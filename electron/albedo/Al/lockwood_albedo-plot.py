#! /usr/bin/env python
from os import path
import argparse as ap
import sys

# Add the parent directory to the path
sys.path.insert(1,path.dirname(path.dirname(path.abspath(__file__))))
from albedo_simulation_plot import plotAlbedoSimulationSpectrum

dir=path.dirname(path.abspath(__file__))

if __name__ == "__main__":

    # Set up the argument parser
    description = "This script asks for albedo rendezvous and data files "\
                  "which it then plots against experimental data."

    parser = ap.ArgumentParser(description=description)

    parser.add_argument("-f", "--forward_file", dest="forward_file",
                        help="the forward rendezvous file to load")
    parser.add_argument("-a", "--adjoint_file", dest="adjoint_file",
                      help="the rendezvous file to load")
    parser.add_argument("-o", "--output_name", dest="output_name",
                      help="the plot output name", required=False)
    parser.add_argument("combined_forward_files", nargs='*',
                        help="the combined forward discrete file to load")

    # Parse the user's arguments
    user_args = parser.parse_args()

    forward_filename = dir + "/" + user_args.forward_file
    adjoint_filename = dir + "/" + user_args.adjoint_file

    if user_args.combined_forward_files:
      combined_forward_files = dir + "/" + user_args.combined_forward_files
    else:
      combined_forward_files = None

    top_ylims = [0.0, 0.6]
    bottom_ylims = [0.0, 3.0]
    legend_pos = (0.95,0.95)


    source_angle = 0.0
    exp_base = dir + "/experimental_results/lockwood_"
    exp_file += "0.tsv"
    if "15.0" in forward_filename:
      source_angle = 15.0
      exp_file += "15.tsv"
    if "30.0" in forward_filename:
      source_angle = 30.0
      exp_file += "30.tsv"
    if "45.0" in forward_filename:
      source_angle = 45.0
      exp_file += "45.tsv"
    if "60.0" in forward_filename:
      source_angle = 60.0
      exp_file += "60.tsv"
    if "75.0" in forward_filename:
      source_angle = 75.0
      exp_file += "75.tsv"

    # Plot the spectrum
    plotAlbedoSimulationSpectrum( forward_filename,
                                  adjoint_filename,
                                  exp_file,
                                  combined_forward_files,
                                  source_angle,
                                  "Al",
                                  user_args.output_name,
                                  top_ylims,
                                  bottom_ylims,
                                  None,
                                  legend_pos )