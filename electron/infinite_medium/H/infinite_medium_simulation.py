#! /usr/bin/env python
from os import path, makedirs
import sys
import numpy
import datetime
import socket

# Add the parent directory to the path
sys.path.insert(1,path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
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
## Set up and run the forward simulation
def runForwardDeltaEnergyInfiniteMediumSimulation( sim_name,
                                                   db_path,
                                                   geom_name,
                                                   properties,
                                                   source_energy,
                                                   energy_bins,
                                                   zaid,
                                                   version,
                                                   threads,
                                                   log_file = None ):

    ## Initialize the MPI session
    session = MPI.GlobalMPISession( len(sys.argv), sys.argv )

    # Suppress logging on all procs except for the master (proc=0)
    Utility.removeAllLogs()
    session.initializeLogs( 0, True )

    if not log_file is None:
        session.initializeLogs( log_file, 0, True )

    if session.rank() == 0:
      print "The PyFrensie path is set to: ", pyfrensie_path

    simulation_properties = properties

  ##--------------------------------------------------------------------------##
  ## ---------------------------- MATERIALS SETUP --------------------------- ##
  ##--------------------------------------------------------------------------##

    # Set element name
    element_name="Infinite"

    ## Set up the materials
    database = Data.ScatteringCenterPropertiesDatabase( db_path )

    # Extract the properties for the atom from the database
    atom_properties = database.getAtomProperties( Data.ZAID(zaid) )

    # Set the definition for the atom for this simulation
    scattering_center_definitions = Collision.ScatteringCenterDefinitionDatabase()
    atom_definition = scattering_center_definitions.createDefinition( element_name, Data.ZAID(zaid) )

    file_type = Data.ElectroatomicDataProperties.Native_EPR_FILE

    atom_definition.setElectroatomicDataProperties( atom_properties.getSharedElectroatomicDataProperties( file_type, version ) )

    # Set the definition for material 1
    material_definitions = Collision.MaterialDefinitionDatabase()
    material_definitions.addDefinition( element_name, 1, [element_name], [1.0] )

  ##--------------------------------------------------------------------------##
  ## ---------------------------- GEOMETRY SETUP ---------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the geometry
    model_properties = DagMC.DagMCModelProperties( geom_name )
    model_properties.useFastIdLookup()

    # Load the model
    model = DagMC.DagMCModel( model_properties )

    # Fill the model with the defined material
    filled_model = Collision.FilledGeometryModel( db_path, scattering_center_definitions, material_definitions, simulation_properties, model, True )

  ##--------------------------------------------------------------------------##
  ## ----------------------------- SOURCE SETUP ----------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the source
    particle_distribution = ActiveRegion.StandardParticleDistribution( "isotropic mono-energetic dist" )

    particle_distribution.setEnergy( source_energy )
    particle_distribution.setPosition( 0.0, 0.0, 0.0 )
    particle_distribution.constructDimensionDistributionDependencyTree()

    # The generic distribution will be used to generate electrons
    electron_distribution = [ActiveRegion.StandardElectronSourceComponent( 0, 1.0, model, particle_distribution )]

    # Assign the electron source component to the source
    source = ActiveRegion.StandardParticleSource( [electron_distribution] )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP ------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the event handler
    event_handler = Event.EventHandler( model, simulation_properties )

  ## ------------------------ Surface Flux Estimator ------------------------ ##

    surface_flux_estimator = event_handler.getEstimator( 1 )

    # Set the energy bins
    surface_flux_estimator.setEnergyDiscretization( energy_bins )


  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ----------------------- ##
  ##--------------------------------------------------------------------------##

    # Set the archive type
    archive_type = "xml"

    ## Set up the simulation manager
    factory = Manager.ParticleSimulationManagerFactory( filled_model,
                                                        source,
                                                        event_handler,
                                                        simulation_properties,
                                                        sim_name,
                                                        archive_type,
                                                        threads )

    # Create the simulation manager
    manager = factory.getManager()

    # Allow logging on all procs
    session.restoreOutputStreams()

    ## Run the simulation
    if session.size() == 1:
        manager.runInterruptibleSimulation()
    else:
        manager.runSimulation()

    if session.rank() == 0:

      # Get the plot title
      title = setup.getSimulationPlotTitle( sim_name )

      print "Processing the results:"
      processForwardData( surface_flux_estimator, sim_name, title )

      print "Results will be in ", path.dirname(path.abspath(sim_name))

##---------------------------------------------------------------------------##
## Set up and run the adjoint simulation
def runAdjointDeltaEnergyInfiniteMediumSimulation( sim_name,
                                                   db_path,
                                                   geom_name,
                                                   properties,
                                                   energy_cutoff,
                                                   source_energy,
                                                   source_critical_line,
                                                   energy_bins,
                                                   zaid,
                                                   version,
                                                   threads,
                                                   log_file = None ):

    ## Initialize the MPI session
    session = MPI.GlobalMPISession( len(sys.argv), sys.argv )

    # Suppress logging on all procs except for the master (proc=0)
    Utility.removeAllLogs()
    session.initializeLogs( 0, True )

    if not log_file is None:
        session.initializeLogs( log_file, 0, True )

    if session.rank() == 0:
      print "The PyFrensie path is set to: ", pyfrensie_path

    simulation_properties = properties

  ##--------------------------------------------------------------------------##
  ## ---------------------------- MATERIALS SETUP --------------------------- ##
  ##--------------------------------------------------------------------------##

    # Set element name
    element_name="Infinite"

    ## Set up the materials
    database = Data.ScatteringCenterPropertiesDatabase( db_path )

    # Extract the properties for H from the database
    atom_properties = database.getAtomProperties( Data.ZAID(zaid) )

    # Set the definition for H for this simulation
    scattering_center_definitions = Collision.ScatteringCenterDefinitionDatabase()
    atom_definition = scattering_center_definitions.createDefinition( element_name, Data.ZAID(zaid) )

    file_type = Data.AdjointElectroatomicDataProperties.Native_EPR_FILE

    atom_definition.setAdjointElectroatomicDataProperties( atom_properties.getSharedAdjointElectroatomicDataProperties( file_type, version ) )

    # Set the definition for material 1
    material_definitions = Collision.MaterialDefinitionDatabase()
    material_definitions.addDefinition( element_name, 1, [element_name], [1.0] )

  ##--------------------------------------------------------------------------##
  ## ---------------------------- GEOMETRY SETUP ---------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the geometry
    model_properties = DagMC.DagMCModelProperties( geom_name )
    model_properties.useFastIdLookup()

    # Load the model
    model = DagMC.DagMCModel( model_properties )

    # Fill the model with the defined material
    filled_model = Collision.FilledGeometryModel( db_path, scattering_center_definitions, material_definitions, simulation_properties, model, True )

  ##--------------------------------------------------------------------------##
  ## ----------------------------- SOURCE SETUP ----------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the source
    particle_distribution = ActiveRegion.StandardParticleDistribution( "adjoint isotropic uniform energy dist" )

    uniform_energy = Distribution.UniformDistribution( energy_cutoff, source_energy )
    energy_dimension_dist = ActiveRegion.IndependentEnergyDimensionDistribution( uniform_energy )
    particle_distribution.setDimensionDistribution( energy_dimension_dist )
    particle_distribution.setPosition( 0.0, 0.0, 0.0 )
    particle_distribution.constructDimensionDistributionDependencyTree()

    # The generic distribution will be used to generate electron
    if source_critical_line == None:
      adjoint_electron_distribution = ActiveRegion.StandardAdjointElectronSourceComponent( 0, 1.0, filled_model, particle_distribution )
    else:
      adjoint_electron_distribution = ActiveRegion.StandardAdjointElectronSourceComponent( 0, 1.0, model, particle_distribution, source_critical_line )

    # Assign the electron source component to the source
    source = ActiveRegion.StandardParticleSource( [adjoint_electron_distribution] )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP ------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the event handler
    event_handler = Event.EventHandler( model, simulation_properties )

  ## ------------------------ Surface Flux Estimator ------------------------ ##

    # Setup an adjoint surface flux estimator
    surface_flux_estimator = event_handler.getEstimator( 2 )

    # Create and set the estimator response function
    response_function = ActiveRegion.EnergyParticleResponseFunction( Distribution.DeltaDistribution( source_energy, source_energy - energy_cutoff ) )
    response = ActiveRegion.StandardParticleResponse( response_function )
    surface_flux_estimator.setResponseFunctions( [response] )

    # Set the energy bin discretization
    surface_flux_estimator.setSourceEnergyDiscretization( energy_bins )

  ## -------------------------- Particle Tracker ---------------------------- ##

    # particle_tracker = Event.ParticleTracker( 0, 20 )

    # # Add the particle tracker to the event handler
    # event_handler.addParticleTracker( particle_tracker )

  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ----------------------- ##
  ##--------------------------------------------------------------------------##

    # Set the archive type
    archive_type = "xml"

    ## Set up the simulation manager
    factory = Manager.ParticleSimulationManagerFactory( filled_model,
                                                        source,
                                                        event_handler,
                                                        simulation_properties,
                                                        sim_name,
                                                        archive_type,
                                                        threads )

    # Create the simulation manager
    manager = factory.getManager()

    # Allow logging on all procs
    session.restoreOutputStreams()

    ## Run the simulation
    if session.size() == 1:
        manager.runInterruptibleSimulation()
    else:
        manager.runSimulation()

    if session.rank() == 0:

      # Get the plot title
      title = setup.getAdjointSimulationPlotTitle( sim_name )

      print "Processing the results:"
      processAdjointData( surface_flux_estimator, sim_name, title )

      print "Results will be in ", path.dirname(path.abspath(sim_name))

##---------------------------------------------------------------------------##
## Set up and run the forward simulation
def runForwardUniformEnergyInfiniteMediumSimulation( sim_name,
                                                     db_path,
                                                     geom_name,
                                                     properties,
                                                     min_energy,
                                                     max_energy,
                                                     energy_bins,
                                                     zaid,
                                                     version,
                                                     threads,
                                                     log_file = None ):

    ## Initialize the MPI session
    session = MPI.GlobalMPISession( len(sys.argv), sys.argv )

    # Suppress logging on all procs except for the master (proc=0)
    Utility.removeAllLogs()
    session.initializeLogs( 0, True )

    if not log_file is None:
        session.initializeLogs( log_file, 0, True )

    if session.rank() == 0:
      print "The PyFrensie path is set to: ", pyfrensie_path

    simulation_properties = properties

  ##--------------------------------------------------------------------------##
  ## ---------------------------- MATERIALS SETUP --------------------------- ##
  ##--------------------------------------------------------------------------##

    # Set element name
    element_name="Infinite"

    ## Set up the materials
    database = Data.ScatteringCenterPropertiesDatabase( db_path )

    # Extract the properties for the atom from the database
    atom_properties = database.getAtomProperties( Data.ZAID(zaid) )

    # Set the definition for the atom for this simulation
    scattering_center_definitions = Collision.ScatteringCenterDefinitionDatabase()
    atom_definition = scattering_center_definitions.createDefinition( element_name, Data.ZAID(zaid) )

    file_type = Data.ElectroatomicDataProperties.Native_EPR_FILE

    atom_definition.setElectroatomicDataProperties( atom_properties.getSharedElectroatomicDataProperties( file_type, version ) )

    # Set the definition for material 1
    material_definitions = Collision.MaterialDefinitionDatabase()
    material_definitions.addDefinition( element_name, 1, [element_name], [1.0] )

  ##--------------------------------------------------------------------------##
  ## ---------------------------- GEOMETRY SETUP ---------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the geometry
    model_properties = DagMC.DagMCModelProperties( geom_name )
    model_properties.useFastIdLookup()

    # Load the model
    model = DagMC.DagMCModel( model_properties )

    # Fill the model with the defined material
    filled_model = Collision.FilledGeometryModel( db_path, scattering_center_definitions, material_definitions, simulation_properties, model, True )

  ##--------------------------------------------------------------------------##
  ## ----------------------------- SOURCE SETUP ----------------------------- ##
  ##--------------------------------------------------------------------------##

    # Set up the source
    particle_distribution = ActiveRegion.StandardParticleDistribution( "isotropic uniform source dist" )

    # Set the energy dimension distribution
    uniform_energy = Distribution.UniformDistribution( min_energy, max_energy )
    energy_dimension_dist = ActiveRegion.IndependentEnergyDimensionDistribution( uniform_energy )
    particle_distribution.setDimensionDistribution( energy_dimension_dist )
    particle_distribution.setPosition( 0.0, 0.0, 0.0 )
    particle_distribution.constructDimensionDistributionDependencyTree()

    # Set source components
    source_component = [ActiveRegion.StandardElectronSourceComponent( 0, 1.0, geom_model, particle_distribution )]

    # Assign the electron source component to the source
    source = ActiveRegion.StandardParticleSource( [electron_distribution] )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP ------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the event handler
    event_handler = Event.EventHandler( model, simulation_properties )

  ## ------------------------ Surface Flux Estimator ------------------------ ##

    surface_flux_estimator = event_handler.getEstimator( 1 )

    # Set the energy bins
    surface_flux_estimator.setEnergyDiscretization( energy_bins )


  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ----------------------- ##
  ##--------------------------------------------------------------------------##

    # Set the archive type
    archive_type = "xml"

    ## Set up the simulation manager
    factory = Manager.ParticleSimulationManagerFactory( filled_model,
                                                        source,
                                                        event_handler,
                                                        simulation_properties,
                                                        sim_name,
                                                        archive_type,
                                                        threads )

    # Create the simulation manager
    manager = factory.getManager()

    # Allow logging on all procs
    session.restoreOutputStreams()

    ## Run the simulation
    if session.size() == 1:
        manager.runInterruptibleSimulation()
    else:
        manager.runSimulation()

    if session.rank() == 0:

      # Get the plot title
      title = setup.getSimulationPlotTitle( sim_name )

      print "Processing the results:"
      processForwardData( surface_flux_estimator, sim_name, title )

      print "Results will be in ", path.dirname(path.abspath(sim_name))

##---------------------------------------------------------------------------##
## Set up and run the adjoint simulation
def runAdjointUniformEnergyInfiniteMediumSimulation( sim_name,
                                                     db_path,
                                                     geom_name,
                                                     properties,
                                                     energy_cutoff,
                                                     max_energy,
                                                     energy_bins,
                                                     zaid,
                                                     version,
                                                     threads,
                                                     log_file = None ):

    ## Initialize the MPI session
    session = MPI.GlobalMPISession( len(sys.argv), sys.argv )

    # Suppress logging on all procs except for the master (proc=0)
    Utility.removeAllLogs()
    session.initializeLogs( 0, True )

    if not log_file is None:
        session.initializeLogs( log_file, 0, True )

    if session.rank() == 0:
      print "The PyFrensie path is set to: ", pyfrensie_path

    simulation_properties = properties

  ##--------------------------------------------------------------------------##
  ## ---------------------------- MATERIALS SETUP --------------------------- ##
  ##--------------------------------------------------------------------------##

    # Set element name
    element_name="Infinite"

    ## Set up the materials
    database = Data.ScatteringCenterPropertiesDatabase( db_path )

    # Extract the properties for H from the database
    atom_properties = database.getAtomProperties( Data.ZAID(zaid) )

    # Set the definition for H for this simulation
    scattering_center_definitions = Collision.ScatteringCenterDefinitionDatabase()
    atom_definition = scattering_center_definitions.createDefinition( element_name, Data.ZAID(zaid) )

    file_type = Data.AdjointElectroatomicDataProperties.Native_EPR_FILE

    atom_definition.setAdjointElectroatomicDataProperties( atom_properties.getSharedAdjointElectroatomicDataProperties( file_type, version ) )

    # Set the definition for material 1
    material_definitions = Collision.MaterialDefinitionDatabase()
    material_definitions.addDefinition( element_name, 1, [element_name], [1.0] )

  ##--------------------------------------------------------------------------##
  ## ---------------------------- GEOMETRY SETUP ---------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the geometry
    model_properties = DagMC.DagMCModelProperties( geom_name )
    model_properties.useFastIdLookup()

    # Load the model
    model = DagMC.DagMCModel( model_properties )

    # Fill the model with the defined material
    filled_model = Collision.FilledGeometryModel( db_path, scattering_center_definitions, material_definitions, simulation_properties, model, True )

  ##--------------------------------------------------------------------------##
  ## ----------------------------- SOURCE SETUP ----------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the source
    particle_distribution = ActiveRegion.StandardParticleDistribution( "adjoint isotropic uniform energy dist" )

    uniform_energy = Distribution.UniformDistribution( energy_cutoff, max_energy )
    energy_dimension_dist = ActiveRegion.IndependentEnergyDimensionDistribution( uniform_energy )
    particle_distribution.setDimensionDistribution( energy_dimension_dist )
    particle_distribution.setPosition( 0.0, 0.0, 0.0 )
    particle_distribution.constructDimensionDistributionDependencyTree()

    # Assign the electron source component to the source
    source = ActiveRegion.StandardParticleSource( [adjoint_electron_distribution] )

  ##--------------------------------------------------------------------------##
  ## -------------------------- EVENT HANDLER SETUP ------------------------- ##
  ##--------------------------------------------------------------------------##

    ## Set up the event handler
    event_handler = Event.EventHandler( model, simulation_properties )

  ## ------------------------ Surface Flux Estimator ------------------------ ##

    # Setup an adjoint surface flux estimator
    surface_flux_estimator = event_handler.getEstimator( 2 )

    # Create and set the estimator response function
    response_function = ActiveRegion.EnergyParticleResponseFunction( Distribution.UniformDistribution( energy_cutoff, max_energy, 1.0 ) )
    response = ActiveRegion.StandardParticleResponse( response_function )
    surface_flux_estimator.setResponseFunctions( [response] )

    # Set the energy bin discretization
    surface_flux_estimator.setSourceEnergyDiscretization( energy_bins )

  ## -------------------------- Particle Tracker ---------------------------- ##

    # particle_tracker = Event.ParticleTracker( 0, 20 )

    # # Add the particle tracker to the event handler
    # event_handler.addParticleTracker( particle_tracker )

  ##--------------------------------------------------------------------------##
  ## ----------------------- SIMULATION MANAGER SETUP ----------------------- ##
  ##--------------------------------------------------------------------------##

    # Set the archive type
    archive_type = "xml"

    ## Set up the simulation manager
    factory = Manager.ParticleSimulationManagerFactory( filled_model,
                                                        source,
                                                        event_handler,
                                                        simulation_properties,
                                                        sim_name,
                                                        archive_type,
                                                        threads )

    # Create the simulation manager
    manager = factory.getManager()

    # Allow logging on all procs
    session.restoreOutputStreams()

    ## Run the simulation
    if session.size() == 1:
        manager.runInterruptibleSimulation()
    else:
        manager.runSimulation()

    if session.rank() == 0:

      # Get the plot title
      title = setup.getAdjointSimulationPlotTitle( sim_name )

      print "Processing the results:"
      processAdjointData( surface_flux_estimator, sim_name, title )

      print "Results will be in ", path.dirname(path.abspath(sim_name))

##---------------------------------------------------------------------------##
def restartInfiniteMediumSimulation( rendezvous_file_name,
                                     db_path,
                                     num_particles,
                                     threads,
                                     time,
                                     log_file = None,
                                     num_rendezvous = None ):

    ## Initialize the MPI session
    session = MPI.GlobalMPISession( len(sys.argv), sys.argv )

    # Suppress logging on all procs except for the master (proc=0)
    Utility.removeAllLogs()
    session.initializeLogs( 0, True )

    if session.rank() == 0:
      print "The PyFrensie path is set to: ", pyfrensie_path

    if not log_file is None:
        session.initializeLogs( log_file, 0, True )

    # Set the database path
    Collision.FilledGeometryModel.setDefaultDatabasePath( db_path )

    time_sec = time*60

    if not num_rendevous is None:
        new_simulation_properties = MonteCarlo.SimulationGeneralProperties()
        new_simulation_properties.setNumberOfHistories( int(num_particles) )
        new_simulation_properties.setSimulationWallTime( float(time_sec) )
        new_simulation_properties.setMinNumberOfRendezvous( int(num_rendezvous) )

        factory = Manager.ParticleSimulationManagerFactory( rendezvous_file_name,
                                                            new_simulation_properties,
                                                            threads )
    else:
        factory = Manger.ParticleSimulationManagerFactory( rendezvous_file_name,
                                                           int(num_particles),
                                                           float(time_sec),
                                                           threads )

    manager = factory.getManager()

    manager.initialize()

    # Allow logging on all procs
    session.restoreOutputStreams()

    ## Run the simulation
    if session.size() == 1:
        manager.runInterruptibleSimulation()
    else:
        manager.runSimulation()

    if session.rank() == 0:

      # Get the event handler
      event_handler = manager.getEventHandler()

      # Get the simulation name
      filename = rendezvous.split("_rendezvous_")[0]

      print "Processing the results:"
      if "adjoint" in filename:
        title = setup.getAdjointSimulationPlotTitle( filename )
        estimator = event_handler.getEstimator( 2 )
        processAdjointData( event_handler, filename, title )
      else:
        title = setup.getSimulationPlotTitle( filename )
        estimator = event_handler.getEstimator( 1 )
        processForwardData( event_handler, filename, title )

      print "Results will be in ", path.dirname(filename)

##----------------------------------------------------------------------------##
##--------------------- processAdjointDataFromRendezvous ---------------------##
##----------------------------------------------------------------------------##

# This function pulls data from the rendezvous file
def processAdjointDataFromRendezvous( rendezvous_file, db_path ):

  Collision.FilledGeometryModel.setDefaultDatabasePath( db_path )

  # Load data from file
  manager = Manager.ParticleSimulationManagerFactory( rendezvous_file ).getManager()
  event_handler = manager.getEventHandler()

  # Get the simulation name
  filename = rendezvous.split("_rendezvous_")[0]

  print "Processing the results:"
  if "adjoint" in filename:
    title = setup.getAdjointSimulationPlotTitle( filename )
    estimator = event_handler.getEstimator( 2 )
    processAdjointData( event_handler, filename, title )
  else:
    title = setup.getSimulationPlotTitle( filename )
    estimator = event_handler.getEstimator( 1 )
    processForwardData( event_handler, filename, title )

  print "Results will be in ", path.dirname(filename)

##----------------------------------------------------------------------------##
##---------------------------- processAdjointData ----------------------------##
##----------------------------------------------------------------------------##
def processAdjointData( event_handler, filename, title ):

  # Process surface flux data
  surface_flux = event_handler.getEstimator( 2 )
  ids = surface_flux.getEntityIds()

  for id in ids:
    if id == 1:
      radius = 1
    elif id == 18 or id == 27:
      radius = 2
    elif id == 16 or id == 25:
      radius = 5
    elif id == 23:
      radius = 10
    elif id == 21:
      radius = 20
    elif id == 19:
      radius = 40

    output_file = filename + "_" + str(radius)
    setup.processSurfaceFluxSourceEnergyBinData( surface_flux, id, output_file, title )

##----------------------------------------------------------------------------##
##---------------------------- processForwardData ----------------------------##
##----------------------------------------------------------------------------##
def processForwardData( event_handler, filename, title ):

  # Process surface flux data
  surface_flux = event_handler.getEstimator( 1 )
  ids = surface_flux.getEntityIds()

  for id in ids:
    if id == 1:
      radius = 1
    elif id == 18 or id == 27:
      radius = 2
    elif id == 16 or id == 25:
      radius = 5
    elif id == 23:
      radius = 10
    elif id == 21:
      radius = 20
    elif id == 19:
      radius = 40

    output_file = filename + "_" + str(radius)
    setup.processSurfaceFluxEnergyBinData( surface_flux, id, output_file, title )
