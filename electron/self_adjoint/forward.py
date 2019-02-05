#! /usr/bin/env python
from os import path, makedirs
import sys
import numpy
import datetime
import socket

# Add the parent directory to the path
sys.path.insert(1,path.dirname(path.dirname(path.abspath(__file__))))
import simulation_setup as setup
import PyFrensie.Data as Data
import PyFrensie.Data.Native as Native
import PyFrensie.Geometry.DagMC as DagMC
import PyFrensie.Geometry as Geometry
import PyFrensie.Utility as Utility
import PyFrensie.Utility.MPI as MPI
import PyFrensie.Utility.Prng as Prng
import PyFrensie.Utility.Coordinate as Coordinate
import PyFrensie.Utility.Distribution as Distribution
import PyFrensie.MonteCarlo as MonteCarlo
import PyFrensie.MonteCarlo.Collision as Collision
import PyFrensie.MonteCarlo.ActiveRegion as ActiveRegion
import PyFrensie.MonteCarlo.Event as Event
import PyFrensie.MonteCarlo.Manager as Manager

pyfrensie_path =path.dirname( path.dirname(path.abspath(MonteCarlo.__file__)))

##----------------------------------------------------------------------------##
## ---------------------- GLOBAL SIMULATION VARIABLES ----------------------- ##
##----------------------------------------------------------------------------##

# Set the source energy
energy=0.01

# Set the elastic distribution mode ( DECOUPLED, COUPLED, HYBRID )
mode=MonteCarlo.DECOUPLED_DISTRIBUTION

# Set the elastic coupled sampling method
# ( TWO_D_UNION, ONE_D_UNION, MODIFIED_TWO_D_UNION )
method=MonteCarlo.MODIFIED_TWO_D_UNION

# Set the ionization sampling method
# ( KNOCK_ON_SAMPLING, OUTGOING_ENERGY_SAMPLING )
ionization=MonteCarlo.KNOCK_ON_SAMPLING

# Set the bivariate Grid Policy ( UNIT_BASE_CORRELATED, CORRELATED, UNIT_BASE )
grid_policy=MonteCarlo.UNIT_BASE_CORRELATED_GRID

# Set database directory path (for Denali)
if socket.gethostname() == "Denali":
  database_path = "/home/software/mcnpdata/database.xml"
else: # Set database directory path (for Cluster)
  database_path = "/home/lkersting/software/mcnp6.2/MCNP_DATA/database.xml"

geometry_path = path.dirname(path.realpath(__file__)) + "/geom.h5m"

# Set the bivariate interpolation (LOGLOGLOG, LINLINLIN, LINLINLOG)
interpolation=MonteCarlo.LOGLOGLOG_INTERPOLATION

# Set the data file type (ACE_EPR_FILE, Native_EPR_FILE)
file_type=Data.ElectroatomicDataProperties.Native_EPR_FILE

##----------------------------------------------------------------------------##
## ----------------------------- RUN SIMULATION ----------------------------- ##
##----------------------------------------------------------------------------##
def runSimulation( threads, histories, time ):

  ##--------------------------------------------------------------------------##
  ## ------------------------------ MPI Session ----------------------------- ##
  ##--------------------------------------------------------------------------##
  session = MPI.GlobalMPISession( len(sys.argv), sys.argv )
  Utility.removeAllLogs()
  session.initializeLogs( 0, True )

  if session.rank() == 0:
    print "The PyFrensie path is set to: ", pyfrensie_path

  properties = setSimulationProperties( histories, time )

  ##--------------------------------------------------------------------------##
  ## ---------------------------- GEOMETRY SETUP ---------------------------- ##
  ##--------------------------------------------------------------------------##

  # Set element zaid and name
  atom=Data.H_ATOM
  zaid=1000
  element="H"

  # Set geometry path and type
  model_properties = DagMC.DagMCModelProperties( geometry_path )
  model_properties.useFastIdLookup()

  # Set model
  geom_model = DagMC.DagMCModel( model_properties )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP ------------------------- ##
  ##--------------------------------------------------------------------------##

  # Set event handler
  event_handler = Event.EventHandler( properties )

  # Set the energy bins
  bins = list(Utility.doubleArrayFromString( "{ 1e-4, 99l, 8e-3, 149i, 1e-2}" ))

  ## ------------------------ Surface Flux Estimator ------------------------ ##

  # Setup a surface flux estimator
  estimator_id = 1
  surface_ids = [1, 19, 21, 23, 25, 27]
  surface_flux_estimator = Event.WeightMultipliedSurfaceFluxEstimator( estimator_id, 1.0, surface_ids, geom_model )

  # Set the particle type
  surface_flux_estimator.setParticleTypes( [MonteCarlo.ELECTRON] )

  # Set the energy bins
  surface_flux_estimator.setEnergyDiscretization( bins )

  # Add the estimator to the event handler
  event_handler.addEstimator( surface_flux_estimator )

  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ----------------------- ##
  ##--------------------------------------------------------------------------##

  # Initialized database
  database = Data.ScatteringCenterPropertiesDatabase(database_path)
  scattering_center_definition_database = Collision.ScatteringCenterDefinitionDatabase()

  # Set element properties
  element_properties = database.getAtomProperties( atom )

  element_definition = scattering_center_definition_database.createDefinition( element, Data.ZAID(zaid) )


  version = 1
  if file_type == Data.ElectroatomicDataProperties.ACE_EPR_FILE:
    version = 14

  element_definition.setElectroatomicDataProperties(
            element_properties.getSharedElectroatomicDataProperties( file_type, version ) )

  material_definition_database = Collision.MaterialDefinitionDatabase()
  material_definition_database.addDefinition( element, 1, (element,), (1.0,) )

  # Fill model
  model = Collision.FilledGeometryModel( database_path, scattering_center_definition_database, material_definition_database, properties, geom_model, True )

  # Set particle distribution
  particle_distribution = ActiveRegion.StandardParticleDistribution( "source distribution" )

  # Set the energy dimension distribution
  delta_energy = Distribution.DeltaDistribution( energy )
  energy_dimension_dist = ActiveRegion.IndependentEnergyDimensionDistribution( delta_energy )
  particle_distribution.setDimensionDistribution( energy_dimension_dist )

  # Set the spatial dimension distribution
  particle_distribution.setPosition( 0.0, 0.0, 0.0 )

  particle_distribution.constructDimensionDistributionDependencyTree()

  # Set source components
  source_component = [ActiveRegion.StandardElectronSourceComponent( 0, 1.0, geom_model, particle_distribution )]

  # Set source
  source = ActiveRegion.StandardParticleSource( source_component )

  # Set the archive type
  archive_type = "xml"

  name = setSimulationName( properties )
  title = setup.getSimulationPlotTitle( name )

  factory = Manager.ParticleSimulationManagerFactory( model,
                                                      source,
                                                      event_handler,
                                                      properties,
                                                      name,
                                                      archive_type,
                                                      threads )

  manager = factory.getManager()

  Utility.removeAllLogs()
  session.initializeLogs( 0, False )

  manager.runSimulation()

  if session.rank() == 0:

    print "Processing the results:"
    processData( event_handler, name, title )

    print "Results will be in ", path.dirname(name)

##----------------------------------------------------------------------------##
## --------------------- Run Simulation From Rendezvous --------------------- ##
##----------------------------------------------------------------------------##
def runSimulationFromRendezvous( threads, histories, time, rendezvous ):

  ##--------------------------------------------------------------------------##
  ## ------------------------------ MPI Session ----------------------------- ##
  ##--------------------------------------------------------------------------##
  session = MPI.GlobalMPISession( len(sys.argv), sys.argv )
  Utility.removeAllLogs()
  session.initializeLogs( 0, True )

  if session.rank() == 0:
    print "The PyFrensie path is set to: ", pyfrensie_path

  # Set the data path
  Collision.FilledGeometryModel.setDefaultDatabasePath( database_path )

  time_sec = time*60
  factory = Manager.ParticleSimulationManagerFactory( rendezvous, histories, time_sec, threads )

  manager = factory.getManager()

  Utility.removeAllLogs()
  session.initializeLogs( 0, False )

  manager.runSimulation()

  if session.rank() == 0:

    # Get the event handler
    event_handler = manager.getEventHandler()

    # Get the simulation name and title
    properties = manager.getSimulationProperties()

    filename = setSimulationName( properties )
    title = setup.getSimulationPlotTitle( filename )

    filename = rendezvous.split("_rendezvous_")[0]

    print "Processing the results:"
    processData( event_handler, filename, title )

    print "Results will be in ", path.dirname(filename)

##----------------------------------------------------------------------------##
## ------------------------- SIMULATION PROPERTIES -------------------------- ##
##----------------------------------------------------------------------------##
def setSimulationProperties( histories, time ):

  properties = setup.setSimulationProperties( histories, time, interpolation, grid_policy, mode, method )


  ## -------------------------- ELECTRON PROPERTIES ------------------------- ##

  # Set the ionization sampling method
  properties.setElectroionizationSamplingMode( ionization )

  # Turn off Atomic Relaxation
  properties.setAtomicRelaxationModeOff( MonteCarlo.ELECTRON )

  # Turn certain reactions off
  # properties.setElasticModeOff()
  # properties.setElectroionizationModeOff()
  # properties.setBremsstrahlungModeOff()
  # properties.setAtomicExcitationModeOff()

  return properties

##----------------------------------------------------------------------------##
## ------------------------ Create Results Directory ------------------------ ##
##----------------------------------------------------------------------------##
def createResultsDirectory():

  date = str(datetime.datetime.today()).split()[0]
  directory = "results/forward/" + date

  if not path.exists(directory):
    makedirs(directory)

  return directory

##----------------------------------------------------------------------------##
## -------------------------- setSimulationName ------------------------------##
##----------------------------------------------------------------------------##
# Define a function for naming an electron simulation
def setSimulationName( properties ):
  extension = setup.setSimulationNameExtention( properties, file_type )
  name = "forward_" + str(energy) + extension

  date = str(datetime.datetime.today()).split()[0]
  directory = "results/forward/" + date

  output = directory + "/" + name

  return output

##----------------------------------------------------------------------------##
## -------------------------- getSimulationName ------------------------------##
##----------------------------------------------------------------------------##
# Define a function for naming an electron simulation
def getSimulationName():

  properties = setSimulationProperties( 1, 1.0 )

  name = setSimulationName( properties )
  title = setup.getSimulationPlotTitle( name )

  return name

##----------------------------------------------------------------------------##
##------------------------ processDataFromRendezvous -------------------------##
##----------------------------------------------------------------------------##

# This function pulls data from the rendezvous file
def processDataFromRendezvous( rendezvous_file ):

  Collision.FilledGeometryModel.setDefaultDatabasePath( database_path )

  # Load data from file
  manager = Manager.ParticleSimulationManagerFactory( rendezvous_file ).getManager()
  event_handler = manager.getEventHandler()

  # Get the simulation name and title
  properties = manager.getSimulationProperties()

  if "epr14" not in rendezvous_file:
    file_type = Data.ElectroatomicDataProperties.Native_EPR_FILE
  else:
    file_type = Data.ElectroatomicDataProperties.ACE_EPR_FILE

  filename = setSimulationName( properties )
  title = setup.getSimulationPlotTitle( filename )

  print "Processing the results:"
  processData( event_handler, filename, title )

  print "Results will be in ", path.dirname(filename)

##----------------------------------------------------------------------------##
##------------------------------- processData --------------------------------##
##----------------------------------------------------------------------------##
def processData( event_handler, filename, title ):

  # Process surface flux data
  surface_flux = event_handler.getEstimator( 1 )

  file1 = filename + "_1"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 1, file1, title )

  file2 = filename + "_2"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 27, file2, title )

  file3 = filename + "_5"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 25, file3, title )

  file4 = filename + "_10"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 23, file4, title )

  file5 = filename + "_20"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 21, file5, title )

  file6 = filename + "_40"
  setup.processSurfaceFluxEnergyBinData( surface_flux, 19, file6, title )
