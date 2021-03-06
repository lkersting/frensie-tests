#! /usr/bin/env python
# Luke Kersting
# This script asks for #/square degree data and run names which it then plots.
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import argparse as ap

# Set up the argument parser
description = "This script asks for #/square degree data and run names which "\
              "which it then plots."

parser = ap.ArgumentParser(description=description)


experimental_msg = "Flag to add the experimental data to the generated plot."
parser.add_argument('-e', help=experimental_msg, action='store_true')

output_msg = "The output file name."
parser.add_argument('-o', help=output_msg, required=False)

parser.add_argument("input_files", nargs='*')

# Parse the user's arguments
user_args = parser.parse_args()
file_paths = user_args.input_files

# Number of files
N = len(file_paths)

# Number of data points in each file
M = 18
data_x = [[0 for x in range(N)] for y in range(M)]
data_y = [[0 for x in range(N)] for y in range(M)]
data_error = [[0 for x in range(N)] for y in range(M)]
names = [0 for x in range(N)]

# Get computational results
for n in range(len(file_paths)):
    question = "Enter the desired plot name to data file (" + file_paths[n] + "): "
    names[n] = raw_input(question)

    with open(file_paths[n]) as input:
        data = zip(*(line.strip().split(' ') for line in input))
        data_name = data[0][0] + data[1][0] + data[2][0]
        data_x[n][0:17] = data[0][1:]
        data_y[n][0:17] = data[1][1:]
        data_error[n][0:17] = data[2][1:]

fig = plt.figure(num=1, figsize=(10,5))
plt.xlabel('Angle (Degree)', size=14)
plt.ylabel('#/Square Degrees', size=14)
plt.title('$\mathrm{15.7\/MeV\/Electron\/Angular\/Distribution\/from\/a\/9.658\/\mu m\/Gold\/Foil}$', size=16)
ax=plt.gca()

plt.xlim(0.0,10.0)
plt.ylim(0.0,0.05)

if user_args.e:
    # Get experimental data
    with open("experimental_results.txt") as input:
        data = zip(*(line.strip().split(' ') for line in input))
        data_name = data[0][0] + data[1][0] + data[2][0]
        exp_x = data[0][1:]
        exp_y = data[1][1:]
        exp_error = data[2][1:]

    x = map(float, exp_x)
    y = map(float, exp_y)
    yerr = map(float, exp_error)
    plt.errorbar(x, y, yerr=yerr, label="Hanson (Exp.)", fmt="s", markersize=5 )


markers = ["v","o","^","<",">","+","x","1","2","3","4","8","p","P","*","h","H","X","D","d"]
markerssizes = [6,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6]
for n in range(N):
    x = map(float, data_x[n])
    y = map(float, data_y[n])
    yerr = map(float, data_error[n])
    plt.errorbar(x, y, yerr=yerr, label=names[n], fmt=markers[n], markersize=markerssizes[n] )
plt.legend(loc=1)
ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
#ax.xaxis.set_major_formatter(FormatStrFormatter('%.4f'))

output = "hanson_results.pdf"
if user_args.o:
    output = user_args.o

print "Plot outputted to: ",output
fig.savefig(output, bbox_inches='tight')
plt.show()