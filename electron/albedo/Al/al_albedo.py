#! /usr/bin/env python
from os import path, makedirs
import sys
from optparse import *
import socket

# Add the parent and grandparent directory to the path
parent_dir=path.dirname(path.dirname(path.abspath(__file__)))
sys.path.insert(1,parent_dir)
sys.path.insert(1,path.dirname(parent_dir))

import simulation_setup as setup
import albedo_simulation as simulation
import PyFrensie.Data as Data
import PyFrensie.MonteCarlo as MonteCarlo

pyfrensie_path =path.dirname( path.dirname(path.abspath(MonteCarlo.__file__)))

# Set the element
element="Al"; zaid=13000

# Set the cutoff energy
cutoff_energy=1e-4

# Set the bivariate Grid Policy (UNIT_BASE_CORRELATED, CORRELATED, UNIT_BASE)
grid_policy=MonteCarlo.UNIT_BASE_CORRELATED_GRID

# Set the elastic distribution mode ( DECOUPLED, COUPLED, HYBRID )
mode=MonteCarlo.DECOUPLED_DISTRIBUTION

# Set the elastic coupled sampling method
# ( TWO_D_UNION, ONE_D_UNION, MODIFIED_TWO_D_UNION )
method=MonteCarlo.MODIFIED_TWO_D_UNION

## ------- FORWARD OPTIONS ------- ##

# Set the source energy
source_energy=0.256

# Set the bivariate interpolation (LOGLOGLOG, LINLINLIN, LINLINLOG)
interpolation=MonteCarlo.LOGLOGLOG_INTERPOLATION

# Set the data file type (ACE_EPR_FILE, Native_EPR_FILE)
file_type=Data.ElectroatomicDataProperties.Native_EPR_FILE

# Set if a refined grid should be used ( True, False )
use_refined_grid=False

## ------- ADJOINT OPTIONS ------- ##

# Set the nudge past max energy mode ( True, False )
nudge_past_max=True

# Set the electro-ionization sampling mode ( KNOCK_ON, OUTGOING_ENERGY )
ionization=MonteCarlo.KNOCK_ON_SAMPLING

# Set database directory path (for Denali)
if socket.gethostname() == "Denali":
  database_path = "/home/software/mcnpdata/database.xml"
# Set database directory path (for Elbrus)
elif socket.gethostname() == "Elbrus":
  database_path = "/home/software/mcnpdata/database.xml"
else: # Set database directory path (for Cluster)
  database_path = "/home/lkersting/software/mcnp6.2/MCNP_DATA/database.xml"

geometry_path = path.dirname(path.realpath(__file__)) + "/geom.h5m"


def printSimulationName():
  # Set the simulation properties
  properties = setup.setSimulationProperties( 1, 1, interpolation, grid_policy, mode, method )

  # Print the simulation name
  sim_name = simulation.setSimulationName( properties, file_type, element, source_energy, use_refined_grid )

  print sim_name

def printAdjointSimulationName():

  # Set the adjoint simulation properties
  properties = setup.setAdjointSimulationProperties( 1, 1, mode, method )

  sim_name = setAdjointSimulationName( properties, element, grid_policy, ionization, nudge_past_max )

  print sim_name

if __name__ == "__main__":

    # Parse the command line options
    parser = OptionParser()
    parser.add_option("--threads", type="int", dest="threads", default=1,
                      help="the number of threads to use")
    parser.add_option("--log_file", type="string", dest="log_file",
                      help="the file that will be used for logging")
    parser.add_option("--num_particles", type="float", dest="num_particles", default=1e3,
                      help="the number of particles to run")
    parser.add_option("--time", type="float", dest="time", default=1350.0,
                      help="the simultion wall time in minutes")
    parser.add_option("--transport", type="string", dest="transport", default="forward",
                      help="the simultion transport mode (forward/adjoint)")
    options,args = parser.parse_args()

    if options.transport == "forward":
      # Set the simulation properties
      properties = setup.setSimulationProperties( options.num_particles, options.time, interpolation, grid_policy, mode, method )

      # Set the min electron energy
      properties.setMinElectronEnergy( cutoff_energy )

      # Turn certain reactions off
      # properties.setElasticModeOff()
      # properties.setElectroionizationModeOff()
      # properties.setBremsstrahlungModeOff()
      # properties.setAtomicExcitationModeOff()

      # Create the results directory
      directory = setup.getResultsDirectory(file_type, interpolation)
      if not path.exists(directory):
        makedirs(directory)

      # Set the simulation name and title
      sim_name = simulation.setSimulationName( properties, file_type, element, source_energy, use_refined_grid )

      version = 0

      if use_refined_grid:
        version += 1
        # if grid_policy == MonteCarlo.UNIT_BASE_GRID:
        #   version = 1
        # elif grid_policy == MonteCarlo.UNIT_BASE_CORRELATED_GRID:
        #   version = 2
        # elif grid_policy == MonteCarlo.CORRELATED_GRID:
        #   version = 3

      if file_type == Data.ElectroatomicDataProperties.ACE_EPR_FILE:
        version = 14

      # Run the simulation
      simulation.runForwardAlbedoSimulation( sim_name,
                                            database_path,
                                            geometry_path,
                                            properties,
                                            source_energy,
                                            zaid,
                                            file_type,
                                            version,
                                            options.threads,
                                            options.log_file )
    elif options.transport == "adjoint":
      # Set the adjoint simulation properties
      properties = setup.setAdjointSimulationProperties( options.num_particles, options.time, mode, method )

      # Set the min electron energy
      properties.setMinAdjointElectronEnergy( cutoff_energy )

      # Set the max electron energy to be the max source energy
      max_source_energy = 0.256
      properties.setMaxAdjointElectronEnergy( max_source_energy )

      # Set the cutoff weight properties for rouletting
      # properties.setAdjointElectronRouletteThresholdWeight( 1e-8 )
      # properties.setAdjointElectronRouletteSurvivalWeight( 1e-6 )

      # Turn certain reactions off
      # properties.setAdjointElasticModeOff()
      # properties.setAdjointElectroionizationModeOff()
      # properties.setAdjointBremsstrahlungModeOff()
      # properties.setAdjointAtomicExcitationModeOff()

      # Create the results directory
      simulation.createAdjointResultsDirectory()

      # Set the simulation name and title
      sim_name = simulation.setAdjointSimulationName( properties, element, grid_policy, ionization, nudge_past_max )

      if grid_policy == MonteCarlo.UNIT_BASE_CORRELATED_GRID:
        version = 0
      elif grid_policy == MonteCarlo.UNIT_BASE_GRID:
        version = 2

      if not nudge_past_max:
        version += 1

      if ionization == MonteCarlo.OUTGOING_ENERGY_SAMPLING:
        version += 4

      # Run the simulation
      simulation.runAdjointAlbedoSimulation( sim_name,
                                             database_path,
                                             geometry_path,
                                             properties,
                                             cutoff_energy,
                                             max_source_energy,
                                             zaid,
                                             version,
                                             options.threads,
                                             options.log_file )