import os
import sys
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import FormatStrFormatter
from matplotlib.lines import Line2D

class bcolors:
    HEADER = '\033[95m'
    SIGMA2 = '\033[94m'
    SIGMA1 = '\033[92m'
    SIGMA3 = '\033[93m'
    NO_SIGMA = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def plotInfiniteMediumSimulationSurfaceFlux( forward_data,
                                             adjoint_data,
                                             energy_bins,
                                             output_name,
                                             radius,
                                             element,
                                             top_ylims = None,
                                             bottom_ylims = None,
                                             xlims = None,
                                             legend_pos = None ):

  # Make sure that the forward data is a dictionary
  if not isinstance(forward_data, dict):
      print "The forward data must be a dictionary with keys \"e_bins\", \"mean\" and \"re\""
      sys.exit(1)

  # Make sure that the tadjoint data is a dictionary
  if not isinstance(adjoint_data, dict):
      print "The adjoint data must be a dictionary with keys \"mean\" and \"re\""
      sys.exit(1)

  # Get the forward energy bin boundaries
  energy_bins = np.array(energy_bins)
  # Get the x bin widths
  bin_widths = (energy_bins[1:] - energy_bins[:-1])

  # Get forward data
  # Average the flux to the bin width
  forward_y = np.array(forward_data['mean'])/bin_widths
  # Calculate the error for the bin averaged surface flux
  forward_error = np.array(forward_data['re'])*forward_y

  # Get Adjoint Data
  NORM = 1.0

  # Average the flux to the bin width
  adjoint_y = np.array(adjoint_data['mean'])/bin_widths*NORM
  # Calculate the error for the bin averaged surface flux
  adjoint_error = np.array(adjoint_data['re'])*adjoint_y

  # Plot
  fig = plt.figure(figsize=(10,6))

  # set height ratios for sublots
  gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])

  # the first subplot
  ax0 = plt.subplot(gs[0])

  if element == "Pb":
    atom_name = "Lead"
  elif element == "H":
    atom_name = "Hydrogen"

  mfps = ('%f' % (radius/2.0)).rstrip('0').rstrip('.')

  plot_title = '$\mathrm{0.01\/MeV\/Electron\/Surface\/Flux\/in\/an\/Infinite\/Medium\/of\/' + atom_name + '\/at\/' + str(mfps) +'\/mfps}$'
  x_label = 'Energy (MeV)'
  plt.xlabel(x_label, size=14)
  plt.ylabel('Surface Flux (#/cm$^2$)', size=14)
  plt.title( plot_title, size=16)
  ax=plt.gca()

  if not top_ylims is None:
    plt.ylim(top_ylims[0],top_ylims[1])

  markers = ["--v","-.o",":^","--<","-.>",":+","--x","-.1",":2","--3","-.4",":8","--p","-.P",":*","--h","-.H",":X","--D","-.d"]
  markerssizes = [6,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6]
  marker_color = ['g', 'r', 'c', 'm', 'y', 'k', 'w', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

  linestyles = [(0, ()), (0, (5, 5)), (0, (3, 5, 1, 5)), (0, (1, 1)), (0, (3, 5, 1, 5, 1, 5)), (0, (5, 1)), (0, (3, 1, 1, 1)), (0, (3, 1, 1, 1, 1, 1)), (0, (1, 5)), (0, (5, 10)), (0, (3, 10, 1, 10)), (0, (3, 10, 1, 10, 1, 10))]

  plots = []
  labels = []

  # Plot Adjoint Data

  # Plot histogram of results
  label = "adjoint"
  if not NORM == 1.0:
    label += "*" + str(NORM)
  m, bins, plt1 = plt.hist(energy_bins[:-1], bins=energy_bins, weights=adjoint_y, histtype='step', label=label, color='b', linestyle=linestyles[0], linewidth=1.8 )

  # Plot error bars
  mid = 0.5*(bins[1:] + bins[:-1])
  # plt2 = plt.errorbar(mid, m, yerr=adjoint_error, ecolor='b', fmt=None)

  # plt.errorbar(mid, adjoint_y, yerr=adjoint_error, label="adjoint", fmt="--s", markersize=6, color='b' )

  handle1 = Line2D([], [], c='b', linestyle='--', dashes=linestyles[0][1], linewidth=1.8)
  plots.append( handle1 )
  labels.append("Adjoint")

  # Plot Forward Data

  # Plot histogram of results
  m, bins, plt1 = plt.hist(energy_bins[:-1], bins=energy_bins, weights=forward_y, histtype='step', label="forward", color='g', linestyle=linestyles[1], linewidth=1.8 )

  # Plot error bars
  mid = 0.5*(bins[1:] + bins[:-1])
  # plt2 = plt.errorbar(mid, m, yerr=forward_error, ecolor='g', fmt=None)

  # plt.errorbar(mid, forward_y, yerr=forward_error, label="forward", fmt="--s", markersize=6, color='b' )

  handle1 = Line2D([], [], c='g', linestyle='--', dashes=linestyles[1][1], linewidth=1.8)
  plots.append( handle1 )
  labels.append("Forward")


  plt.legend(loc=legend_pos)
  ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

  markers = ["v","o","^","<",">","+","x","1","2","3","4","8","p","P","*","h","H","X","D","d"]

  # The C/R subplot (with shared x-axis)
  ax1 = plt.subplot(gs[1], sharex = ax0)
  plt.xlabel(x_label, size=14)
  plt.ylabel('Adjoint/Forward', size=14)

  yerr = np.sqrt( ((1.0/forward_y)**2)*(adjoint_error)**2 + ((energy_bins[:-1]/forward_y**2)**2)*(forward_error)**2 )
  y = adjoint_y/forward_y

  if output_name is None:
    output_name = element + "_infinite_medium_" + str(radius)

  output_data_name = output_name + "_3_sigma.txt"

  f = open(output_data_name, 'w')
  f.write( "\n#Energy\tRatio\tUncertainty\n" )

  # calculate % of C/R values within 1,2,3 sigma
  num_in_one_sigma = 0
  num_in_two_sigma = 0
  num_in_three_sigma = 0
  num_below = 0
  num_above = 0

  N=0
  length = len(y)-N
  for i in range(N, len(y)):
    # Print C/R results
    # print energy_bins[i+1], ": ", (1.0-y[i])*100, u"\u00B1", yerr[i]*100, "%"
    # print energy_bins[i+1], ": ", y[i], "\t",forward_y[i]
    if not np.isfinite( y[i] ):
      # print energy_binsx[i+1], ": ", y[i], "\t",forward_y[i], "\t",adjoint_y[i]
      if forward_y[i] == adjoint_y[i]:
        y[i] = 1.0
        yerr[i] = 0.0
      else:
        y[i] = 0
        yerr[i] = 1

    # Calculate number above and below reference
    if y[i] < 1.0:
      num_below += 1
    else:
      num_above += 1

    diff = abs( 1.0 - y[i] )
    # message = '%.4e' % energy_bins[i+1] + ": " + '%.6f' % (y[i]) + u"\u00B1" + '%.6f' % (yerr[i]) + "%"
    message = '%.4e' % energy_bins[i+1] + "\t" + '%.6f' % (y[i]) +"\t"+ '%.6f' % (yerr[i])

    sigma = bcolors.NO_SIGMA
    if diff <= 3*yerr[i]:
        num_in_three_sigma += 1
        sigma = bcolors.SIGMA3
    if diff <= 2*yerr[i]:
        num_in_two_sigma += 1
        sigma = bcolors.SIGMA2
    if diff <= yerr[i]:
        num_in_one_sigma += 1
        sigma = bcolors.SIGMA1

    f.write( message +"\n")
    message = sigma + message + bcolors.ENDC
    # print message

  message = "----------------------------------------------------------------"
  print message
  f.write( message +"\n")
  message = '%.3f' % (float(num_above)/length*100) + "% above reference"
  print "  ", message
  f.write( message +"\n")
  message = '%.3f' % (float(num_below)/length*100) + "% below reference"
  print "  ", message
  f.write( message +"\n")
  message = "----------------------------------------------------------------"
  print message
  f.write( message +"\n")
  message = '%.3f' % (float(num_in_one_sigma)/length*100) + "% C/R within 1 sigma"
  print "  ", bcolors.SIGMA1, message, bcolors.ENDC
  f.write( message +"\n")
  message = "----------------------------------------------------------------"
  print message
  f.write( message +"\n")
  message = '%.3f' % (float(num_in_two_sigma)/length*100) + "% C/R within 2 sigma"
  print "  ", bcolors.SIGMA2, message, bcolors.ENDC
  f.write( message +"\n")
  message = "----------------------------------------------------------------"
  print message
  f.write( message +"\n")
  message = '%.3f' % (float(num_in_three_sigma)/length*100) + "% C/R within 3 sigma"
  print "  ", bcolors.SIGMA3, message, bcolors.ENDC
  f.write( message +"\n")
  f.close()
  # Plot histogram of results
  m, bins, _ = ax1.hist(energy_bins[:-1], bins=energy_bins, weights=y, histtype='step', label="ratio", color='b', linestyle=linestyles[0], linewidth=1.8 )
  # Plot error bars
  mid = 0.5*(bins[1:] + bins[:-1])
  ax1.errorbar(mid, m, yerr=yerr, ecolor='b', fmt=None)

  # make x ticks for first suplot invisible
  plt.setp(ax0.get_xticklabels(), visible=False)

  # remove first tick label for the first subplot
  yticks = ax0.yaxis.get_major_ticks()
  yticks[0].label1.set_visible(False)
  ax0.grid(linestyle=':')
  ax1.grid(linestyle=':')

  output_plot_names = []
  output_plot_names.append( output_name + ".eps" )
  output_plot_names.append( output_name + ".png" )

  if not xlims is None:
    plt.xlim(xlims[0],xlims[1])
  if not bottom_ylims is None:
    plt.ylim(bottom_ylims[0],bottom_ylims[1])

  # remove vertical gap between subplots
  plt.subplots_adjust(hspace=.0)

  print "Plot outputted to: ",output_name
  # Save the figure
  for i in range(0,len(output_plot_names)):
    fig.savefig( output_plot_names[i], bbox_inches='tight', dpi=600)
  plt.draw()
  plt.show()


def plotAllInfiniteMediumSimulationSurfaceFlux( forward_data,
                                                adjoint_data,
                                                energy_bins,
                                                output_name,
                                                radius,
                                                element,
                                                top_ylims = None,
                                                bottom_ylims = None,
                                                xlims = None,
                                                legend_pos = None ):

  linestyles = [(0, ()), (0, (5, 5)), (0, (3, 5, 1, 5)), (0, (1, 1)), (0, (3, 5, 1, 5, 1, 5)), (0, (5, 1)), (0, (3, 1, 1, 1)), (0, (3, 1, 1, 1, 1, 1)), (0, (1, 5)), (0, (5, 10)), (0, (3, 10, 1, 10)), (0, (3, 10, 1, 10, 1, 10))]

  plots = []
  labels = []

  num = len(forward_data)

  # Plot
  fig = plt.figure(figsize=(10,6*num))

  gs = [[] for y in range(num)]
  axes = [[] for y in range(2*num)]


  fig = plt.figure(num=1, figsize=(10,12))

  for i in range(num):
    # We'll use two separate gridspecs to have different margins, hspace, etc
    top = 0.95 -(i*2)/100.0
    bottom = 0.1 -(i*3)/100.0
    gs[i] = gridspec.GridSpec(6, 1, height_ratios=[2, 1, 2, 1, 2, 1], top=top, bottom=bottom, hspace=0)

  y_labels = ['Surface Flux', 'C/R', 'Surface Flux', 'C/R', 'Surface Flux', 'C/R']

  # Set the first plot
  axes[0] = fig.add_subplot(gs[0][0,:])
  axes[0].set_ylabel(y_labels[0], size=14)
  axes[0].grid(linestyle=':')
  # axes[0].set_title('Results for a 0.01 MeV Point Source in a H Sphere', size=16)

  for i in range(1,len(axes)):
    j = i/2
    # Shared axes with C/R
    axes[i] = fig.add_subplot(gs[j][i,:], sharex=axes[i-1])
    # Hide shared x-tick labels
    plt.setp(axes[i-1].get_xticklabels(), visible=False)
    # Set the y labels
    axes[i].set_ylabel(y_labels[i], size=14)

    # remove first tick label for the first subplot
    yticks = axes[i].yaxis.get_major_ticks()
    # yticks[0].label1.set_visible(False)
    axes[i].grid(linestyle=':')

  axes[0].set_title('(a)', size=16)
  axes[2].set_title('(b)', size=16)
  axes[4].set_title('(c)', size=16)

  # place a text box in upper left in axes coords
  axes[0].text(0.45, 0.95, '0.5 mfps', transform=axes[0].transAxes, fontsize=14, verticalalignment='top' )
  axes[2].text(0.45, 0.95, '1.0 mfps', transform=axes[2].transAxes, fontsize=14, verticalalignment='top' )
  axes[4].text(0.45, 0.95, '2.5 mfps', transform=axes[4].transAxes, fontsize=14, verticalalignment='top' )


  # Set the x label
  x_label = 'Energy (MeV)'
  axes[5].set_xlabel(x_label, size=14)

  ax=plt.gca()
  ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

  if element == "Pb":
    atom_name = "Lead"
  elif element == "H":
    atom_name = "Hydrogen"

  # Get the forward energy bin boundaries
  energy_bins = np.array(energy_bins)
  # Get the x bin widths
  bin_widths = (energy_bins[1:] - energy_bins[:-1])

  for i in range(num):
    j = i*2

    # Make sure that the forward data is a dictionary
    if not isinstance(forward_data[i], dict):
        print "The forward data must be a dictionary with keys \"e_bins\", \"mean\" and \"re\""
        sys.exit(1)

    # Make sure that the tadjoint data is a dictionary
    if not isinstance(adjoint_data[i], dict):
        print "The adjoint data must be a dictionary with keys \"mean\" and \"re\""
        sys.exit(1)

    # Get forward data
    # Average the flux to the bin width
    forward_y = np.array(forward_data[i]['mean'])/bin_widths
    # Calculate the error for the bin averaged surface flux
    forward_error = np.array(forward_data[i]['re'])*forward_y

    # Get Adjoint Data
    NORM = 1.0

    # Average the flux to the bin width
    adjoint_y = np.array(adjoint_data[i]['mean'])/bin_widths*NORM
    # Calculate the error for the bin averaged surface flux
    adjoint_error = np.array(adjoint_data[i]['re'])*adjoint_y


    # the first subplot
    mfps = ('%f' % (radius[i]/2.0)).rstrip('0').rstrip('.')

    plot_title = '$\mathrm{0.01\/MeV\/Electron\/Surface\/Flux\/in\/an\/Infinite\/Medium\/of\/' + atom_name + '\/at\/' + str(mfps) +'\/mfps}$'

    if not top_ylims is None:
      axes[j].set_ylim(top_ylims[i][0],top_ylims[i][1])

    # Plot Adjoint Data

    # Plot histogram of results
    label = "adjoint"
    if not NORM == 1.0:
      label += "*" + str(NORM)
    m, bins, plt1 = axes[j].hist(energy_bins[:-1], bins=energy_bins, weights=adjoint_y, histtype='step', label=label, color='b', linestyle=linestyles[0], linewidth=1.8 )

    # Plot error bars
    mid = 0.5*(bins[1:] + bins[:-1])
    # plt2 = plt.errorbar(mid, m, yerr=adjoint_error, ecolor='b', fmt=None)

    # plt.errorbar(mid, adjoint_y, yerr=adjoint_error, label="adjoint", fmt="--s", markersize=6, color='b' )

    handle1 = Line2D([], [], c='b', linestyle='--', dashes=linestyles[0][1], linewidth=1.8)
    plots.append( handle1 )
    labels.append("Adjoint")

    # Plot Forward Data

    # Plot histogram of results
    m, bins, plt1 = axes[j].hist(energy_bins[:-1], bins=energy_bins, weights=forward_y, histtype='step', label="forward", color='g', linestyle=linestyles[1], linewidth=1.8 )

    # Plot error bars
    mid = 0.5*(bins[1:] + bins[:-1])
    # plt2 = plt.errorbar(mid, m, yerr=forward_error, ecolor='g', fmt=None)

    # plt.errorbar(mid, forward_y, yerr=forward_error, label="forward", fmt="--s", markersize=6, color='b' )

    handle1 = Line2D([], [], c='g', linestyle='--', dashes=linestyles[1][1], linewidth=1.8)
    plots.append( handle1 )
    labels.append("Forward")

    # The C/R subplot (with shared x-axis)

    yerr = np.sqrt( ((1.0/forward_y)**2)*(adjoint_error)**2 + ((energy_bins[:-1]/forward_y**2)**2)*(forward_error)**2 )
    y = adjoint_y/forward_y

    if output_name is None:
      output_name = element + "_infinite_medium_" + str(radius)

    output_data_name = output_name + "_3_sigma.txt"

    f = open(output_data_name, 'w')
    f.write( "\n#Energy\tRatio\tUncertainty\n" )

    # calculate % of C/R values within 1,2,3 sigma
    num_in_one_sigma = 0
    num_in_two_sigma = 0
    num_in_three_sigma = 0
    num_below = 0
    num_above = 0

    N=0
    length = len(y)-N
    for k in range(N, len(y)):
      # Print C/R results
      # print energy_bins[k+1], ": ", (1.0-y[k])*100, u"\u00B1", yerr[k]*100, "%"
      # print energy_bins[k+1], ": ", y[k], "\t",forward_y[k]
      if not np.isfinite( y[k] ):
        # print energy_binsx[k+1], ": ", y[k], "\t",forward_y[k], "\t",adjoint_y[k]
        if forward_y[k] == adjoint_y[k]:
          y[k] = 1.0
          yerr[k] = 0.0
        else:
          y[k] = 0
          yerr[k] = 1

      # Calculate number above and below reference
      if y[k] < 1.0:
        num_below += 1
      else:
        num_above += 1

      diff = abs( 1.0 - y[k] )
      # message = '%.4e' % energy_bins[k+1] + ": " + '%.6f' % (y[k]) + u"\u00B1" + '%.6f' % (yerr[k]) + "%"
      message = '%.4e' % energy_bins[k+1] + "\t" + '%.6f' % (y[k]) +"\t"+ '%.6f' % (yerr[k])

      sigma = bcolors.NO_SIGMA
      if diff <= 3*yerr[k]:
          num_in_three_sigma += 1
          sigma = bcolors.SIGMA3
      if diff <= 2*yerr[k]:
          num_in_two_sigma += 1
          sigma = bcolors.SIGMA2
      if diff <= yerr[k]:
          num_in_one_sigma += 1
          sigma = bcolors.SIGMA1

      f.write( message +"\n")
      message = sigma + message + bcolors.ENDC
      # print message

    message = "----------------------------------------------------------------"
    print message
    f.write( message +"\n")
    message = '%.3f' % (float(num_above)/length*100) + "% above reference"
    print "  ", message
    f.write( message +"\n")
    message = '%.3f' % (float(num_below)/length*100) + "% below reference"
    print "  ", message
    f.write( message +"\n")
    message = "----------------------------------------------------------------"
    print message
    f.write( message +"\n")
    message = '%.3f' % (float(num_in_one_sigma)/length*100) + "% C/R within 1 sigma"
    print "  ", bcolors.SIGMA1, message, bcolors.ENDC
    f.write( message +"\n")
    message = "----------------------------------------------------------------"
    print message
    f.write( message +"\n")
    message = '%.3f' % (float(num_in_two_sigma)/length*100) + "% C/R within 2 sigma"
    print "  ", bcolors.SIGMA2, message, bcolors.ENDC
    f.write( message +"\n")
    message = "----------------------------------------------------------------"
    print message
    f.write( message +"\n")
    message = '%.3f' % (float(num_in_three_sigma)/length*100) + "% C/R within 3 sigma"
    print "  ", bcolors.SIGMA3, message, bcolors.ENDC
    f.write( message +"\n")
    f.close()
    # Plot histogram of results
    m, bins, _ = axes[j+1].hist(energy_bins[:-1], bins=energy_bins, weights=y, histtype='step', label="ratio", color='b', linestyle=linestyles[0], linewidth=1.8 )
    # Plot error bars
    mid = 0.5*(bins[1:] + bins[:-1])

    axes[j+1].errorbar(mid, m, yerr=yerr, ecolor='b', fmt=None)

    output_plot_names = []
    output_plot_names.append( output_name + ".eps" )
    output_plot_names.append( output_name + ".png" )

    # remove first tick label for the first subplot
    yticks = axes[j].yaxis.get_major_ticks()
    yticks[0].label1.set_visible(False)

    if not xlims is None:
      plt.xlim(xlims[i][0],xlims[i][1])
    if not bottom_ylims is None:
      axes[j+1].set_ylim(bottom_ylims[i][0],bottom_ylims[i][1])

    axes[j].legend(loc=legend_pos[i])

  print "Plot outputted to: ",output_name
  # Save the figure
  for i in range(0,len(output_plot_names)):
    fig.savefig( output_plot_names[i], bbox_inches='tight', dpi=600)

  plt.show()