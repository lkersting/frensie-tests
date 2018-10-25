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

##---------------------------------------------------------------------------##
## ---------------------- GLOBAL SIMULATION VARIABLES ---------------------- ##
##---------------------------------------------------------------------------##

# Set the element
atom=Data.Al_ATOM; element="Al"; zaid=13000
# Set the source energy
energy=0.256
# Set the cutoff energy
cutoff_energy = 1e-4

# Set the bivariate interpolation (LOGLOGLOG, LINLINLIN, LINLINLOG)
interpolation=MonteCarlo.LOGLOGLOG_INTERPOLATION

# Set the bivariate Grid Policy (UNIT_BASE_CORRELATED, CORRELATED, UNIT_BASE)
grid_policy=MonteCarlo.UNIT_BASE_CORRELATED_GRID

# Set the elastic distribution mode ( DECOUPLED, COUPLED, HYBRID )
mode=MonteCarlo.COUPLED_DISTRIBUTION

# Set the elastic coupled sampling method
# ( TWO_D_UNION, ONE_D_UNION, MODIFIED_TWO_D_UNION )
method=MonteCarlo.MODIFIED_TWO_D_UNION

# Set the data file type (ACE_EPR_FILE, Native_EPR_FILE)
file_type=Data.ElectroatomicDataProperties.Native_EPR_FILE

# Set database directory path (for Denali)
if socket.gethostname() == "Denali":
  database_path = "/home/software/mcnpdata/database.xml"
# Set database directory path (for Elbrus)
elif socket.gethostname() == "Elbrus":
  database_path = "/home/software/mcnpdata/database.xml"
else: # Set database directory path (for Cluster)
  database_path = "/home/lkersting/software/mcnp6.2/MCNP_DATA/database.xml"

geometry_path = path.dirname(path.realpath(__file__)) + "/" + element + "/geom.h5m"

# Run the simulation
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

  # Set geometry path and type
  model_properties = DagMC.DagMCModelProperties( geometry_path )
  model_properties.useFastIdLookup()

  # Construct model
  geom_model = DagMC.DagMCModel( model_properties )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP -------------------------- ##
  ##--------------------------------------------------------------------------##

  # Set event handler
  event_handler = Event.EventHandler( properties )

  ##----------------------- Surface Current Estimators -----------------------##

  # Setup a surface current estimator
  estimator_id = 1
  surface_ids = [1, 2]
  current_estimator = Event.WeightMultipliedSurfaceCurrentEstimator( estimator_id, 1.0, surface_ids )

  # Set the particle type
  current_estimator.setParticleTypes( [MonteCarlo.ELECTRON] )

  # Set the cosine bins
  cosine_bins = [ -1.0, -0.99, 0.0, 1.0 ]

  current_estimator.setCosineDiscretization( cosine_bins )

  # Add the estimator to the event handler
  event_handler.addEstimator( current_estimator )

  ## ---------------------- Track Length Flux Estimator --------------------- ##

  # Setup a track length flux estimator
  estimator_id = 2
  cell_ids = [1]
  track_flux_estimator = Event.WeightMultipliedCellTrackLengthFluxEstimator( estimator_id, 1.0, cell_ids, geom_model )

  # Set the particle type
  track_flux_estimator.setParticleTypes( [MonteCarlo.ELECTRON] )

  # Set the energy bins
  energy_bins = numpy.logspace(numpy.log10(cutoff_energy), numpy.log10(energy), num=101) #[ cutoff_energy, 99l, energy ]
  track_flux_estimator.setEnergyDiscretization( energy_bins )

  # Add the estimator to the event handler
  event_handler.addEstimator( track_flux_estimator )

  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ------------------------ ##
  ##--------------------------------------------------------------------------##

  # Initialized database
  database = Data.ScatteringCenterPropertiesDatabase(database_path)
  scattering_center_definition_database = Collision.ScatteringCenterDefinitionDatabase()

  # Set element properties
  element_properties = database.getAtomProperties( atom )

  element_definition = scattering_center_definition_database.createDefinition( element, Data.ZAID(zaid) )


  version = 0
  if file_type == Data.ElectroatomicDataProperties.ACE_EPR_FILE:
    version = 14

  element_definition.setElectroatomicDataProperties(
            element_properties.getSharedElectroatomicDataProperties( file_type, version ) )

  material_definition_database = Collision.MaterialDefinitionDatabase()
  material_definition_database.addDefinition( element, 1, (element,), (1.0,) )

  # Get the material ids
  material_ids = geom_model.getMaterialIds()

  # Fill model
  model = Collision.FilledGeometryModel( database_path, scattering_center_definition_database, material_definition_database, properties, geom_model, True )

  # Set particle distribution
  particle_distribution = ActiveRegion.StandardParticleDistribution( "source distribution" )

  # Set the energy dimension distribution
  delta_energy = Distribution.DeltaDistribution( energy )
  energy_dimension_dist = ActiveRegion.IndependentEnergyDimensionDistribution( delta_energy )
  particle_distribution.setDimensionDistribution( energy_dimension_dist )

  # Set the direction dimension distribution
  particle_distribution.setDirection( 0.0, 0.0, 1.0 )

  # Set the spatial dimension distribution
  particle_distribution.setPosition( 0.0, 0.0, -0.1 )

  particle_distribution.constructDimensionDistributionDependencyTree()

  # Set source components
  source_component = [ActiveRegion.StandardElectronSourceComponent( 0, 1.0, geom_model, particle_distribution )]

  # Set source
  source = ActiveRegion.StandardParticleSource( source_component )

  # Set the archive type
  archive_type = "xml"

  # Set the simulation name and title
  name, title = setSimulationName( properties )

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
    processCosineBinData( current_estimator, energy, name, title )

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

  factory = Manager.ParticleSimulationManagerFactory( rendezvous, histories, time, threads )

  manager = factory.getManager()

  Utility.removeAllLogs()
  session.initializeLogs( 0, False )

  manager.runSimulation()

  if session.rank() == 0:

    rendezvous_number = manager.getNumberOfRendezvous()

    components = rendezvous.split("rendezvous_")
    archive_name = components[0] + "rendezvous_"
    archive_name += str( rendezvous_number - 1 )
    archive_name += "."
    archive_name += components[1].split(".")[1]

    print "Processing the results:"
    processData( archive_name )

    print "Results will be in ", path.dirname(archive_name)

##---------------------------------------------------------------------------##
## ------------------------- SIMULATION PROPERTIES ------------------------- ##
##---------------------------------------------------------------------------##
def setSimulationProperties( histories, time ):

  properties = setup.setSimulationProperties( histories, time, interpolation, grid_policy, mode, method )


  ## -------------------------- ELECTRON PROPERTIES ------------------------- ##

  # Set the min electron energy
  properties.setMinElectronEnergy( cutoff_energy )

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

  directory = setup.getResultsDirectory(file_type, interpolation)

  directory = element + "/" + directory

  if not path.exists(directory):
    makedirs(directory)

  print directory
  return directory

##---------------------------------------------------------------------------##
## -------------------------- setSimulationName -----------------------------##
##---------------------------------------------------------------------------##
# Define a function for naming an electron simulation
def setSimulationName( properties ):
  extension, title = setup.setSimulationNameExtention( properties, file_type )
  name = "albedo_" + element + "_" + str(energy) + extension
  output = element + "/" + setup.getResultsDirectory(file_type, interpolation) + "/" + name

  return (output, title)

##---------------------------------------------------------------------------##
## -------------------------- getSimulationName -----------------------------##
##---------------------------------------------------------------------------##
# Define a function for naming an electron simulation
def getSimulationName():

  properties = setSimulationProperties( 1, 1.0 )

  name, title = setSimulationName( properties )

  return name

##----------------------------------------------------------------------------##
##------------------------------- processData --------------------------------##
##----------------------------------------------------------------------------##

# This function pulls data from the rendezvous file
def processData( rendezvous_file ):

  Collision.FilledGeometryModel.setDefaultDatabasePath( path.dirname(database_path) )

  # Load data from file
  manager = Manager.ParticleSimulationManagerFactory( rendezvous_file ).getManager()
  event_handler = manager.getEventHandler()

  # Get the estimator data
  estimator_1 = event_handler.getEstimator( 1 )
  cosine_bins = estimator_1.getCosineDiscretization()

  # Get the simulation name and title
  properties = manager.getSimulationProperties()

  if "epr14" not in rendezvous_file:
    file_type = Data.ElectroatomicDataProperties.Native_EPR_FILE
  else:
    file_type = Data.ElectroatomicDataProperties.ACE_EPR_FILE

  filename, title = setSimulationName( properties )

  print "Processing the results:"
  processCosineBinData( estimator_1, cosine_bins, filename, title )

  print "Results will be in ", path.dirname(filename)

##----------------------------------------------------------------------------##
##--------------------------- processCosineBinData ---------------------------##
##----------------------------------------------------------------------------##

# This function pulls cosine estimator data outputs it to a separate file.
def processCosineBinData( estimator, energy, filename, title ):

  ids = list(estimator.getEntityIds() )
  if not 2 in ids:
    print "ERROR: estimator does not contain entity 2!"
    raise ValueError(message)

  today = datetime.date.today()

  # Read the data file for surface tallies
  name = filename+"_albedo.txt"
  out_file = open(name, 'w')

  # Get the current and relative error
  processed_data = estimator.getEntityBinProcessedData( 2 )
  current = processed_data['mean']
  current_rel_error = processed_data['re']
  cosine_bins = estimator.getCosineDiscretization()

  print current
  print cosine_bins
  # Write title to file
  out_file.write( "# " + title +"\n")
  # Write data header to file
  header = "# Energy (MeV)\tAlbedo\tError\t"+str(today)+"\n"
  out_file.write(header)

  # Write data to file
  output = '%.6e' % energy + "\t" + \
           '%.16e' % current[-1] + "\t" + \
           '%.16e' % current_rel_error[-1] + "\n"
  out_file.write( output )
  out_file.close()
