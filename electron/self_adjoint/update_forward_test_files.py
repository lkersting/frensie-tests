#!/usr/bin/python2.7
##---------------------------------------------------------------------------##
## Adjoint test data updater
##---------------------------------------------------------------------------##


import sys
from os import path, makedirs
import datetime
from optparse import *

# Add the parent directory to the path
sys.path.insert(1, path.dirname(path.dirname(path.abspath(__file__))))
import simulation_setup as setup
from native_endl_to_native_epr import generateData, addToDatabase
import PyFrensie.Utility as Utility
import PyFrensie.Data as Data
import PyFrensie.Data.Native as Native
# import PyFrensie.MonteCarlo as MonteCarlo

# Simple class for color output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Verify the user specified photon and electron limits
def generateNativeFile( db_name,
                        grid_policy = "UnitBaseGrid",
                        refine_grids = "True",
                        version = 0,
                        overwrite = True,
                        log_file = None ):

    endl_file_path = path.dirname(db_name) + "/endldata/endl_native_1.xml"
    output_file_path = path.dirname(db_name) + "/native/epr/epr_native_1_v" + str(version) + ".xml"

    # Check if the endl file exists
    if not path.isfile( endl_file_path ):
        print "The endl directory " + path.dirname( endl_file_path ) + " does not contain the required endl data file", "endl_native_1.xml"
        sys.exit(1)

    # Check if the native directory exists
    if not path.isdir( path.dirname( output_file_path ) ):
        print "The native directory " + path.dirname( output_file_path ) + " does not exist!"
        sys.exit(1)

    # Open the database
    if path.exists( db_name ):
      # Open the database
      database = Data.ScatteringCenterPropertiesDatabase( db_name )
    else:
      print "ERROR: The file", db_name, "doesn't exist!"
      sys.exit(1)

    print "The PyFrensie path is set to: ", path.dirname( path.dirname(path.abspath(Data.__file__)))

    database_save_required = False
    generation_required = True

    # Check if the output file has already been generated
    if path.exists( output_file_path ) and not overwrite:
        generation_required = False

    if generation_required:
        notification_string = "Generating " + output_file_path + " from " + endl_file_path + " ... "

        Utility.logNotification( notification_string )

        if not log_file is None:
            sys.stdout.write(notification_string)
            sys.stdout.flush()

        data_container = \
        generateData( endl_file_path,
                      output_file_path,
                      ace_table_name = None,
                      db_name = None,
                      overwrite = overwrite,
                      notes = "Generated by update_forward_test_files.py",
                      min_photon_energy = 1e-3,
                      max_photon_energy = 20.0,
                      min_electron_energy = 1e-4,
                      max_electron_energy = 20.0,
                      photon_grid_convergence_tol = 1e-3,
                      photon_grid_abs_diff_tol = 1e-80,
                      photon_grid_dist_tol = 1e-18,
                      electron_grid_convergence_tol = 1e-3,
                      electron_grid_abs_diff_tol = 1e-80,
                      electron_grid_dist_tol = 1e-18,
                      occupation_number_eval_tol = 1e-3,
                      subshell_incoherent_eval_tol = 1e-3,
                      photon_threshold_energy_nudge_factor = None,
                      cutoff_angle_cosine = 0.9,
                      num_moment_preserving_angles = 2,
                      tabular_evaluation_tol = 1e-15,
                      electron_secondary_grid_refinement = refine_grids,
                      electron_two_d_interp_policy = "LogLogLog",
                      electron_two_d_grid_policy = grid_policy )

        # Update the database
        database_save_required = \
            addToDatabase( output_file_path,
                           path.dirname( db_name ),
                           database,
                           data_container.getAtomicNumber(),
                           data_container.getAtomicWeight(),
                           True,
                           database_save_required,
                           options.version )

        notification_string = "done."

        Utility.logNotification( notification_string )

        if not log_file is None:
            sys.stdout.write(notification_string + "\n")
            sys.stdout.flush()

    else:
        data_container = Native.ElectronPhotonRelaxationDataContainer( output_file_path )

        # Update the database
        database_save_required = \
            addToDatabase( output_file_path,
                            path.dirname( db_name ),
                            database,
                            data_container.getAtomicNumber(),
                            data_container.getAtomicWeight(),
                            False,
                            database_save_required,
                            options.version )

    # Save the updated database
    if database_save_required:
        database.saveToFile( db_name, True )


if __name__ == "__main__":

    # Parse the command-line arguments
    parser = OptionParser()
    parser.add_option("-d", "--db_name", type="string", dest="db_name", default="database.xml",
                      help="the database file with path")
    parser.add_option("-g", "--grid_policy", type="string", dest="grid_policy", default="UnitBaseGrid",
                      help="the electron two d grid policy")
    parser.add_option("-v", "--version", type="int", dest="version", default=0,
                      help="the data file version number")
    parser.add_option("--refine_electron_secondary_grids", action="store_true", dest="electron_secondary_grid_refinement", default=False,
                      help="Refine the electron secondary grids")

    options,args = parser.parse_args()

    generateNativeFile( options.db_name,
                        options.grid_policy,
                        options.electron_secondary_grid_refinement,
                        options.version )

    print bcolors.BOLD + bcolors.OKGREEN + "H native data updated successfully!\n" + bcolors.ENDC
