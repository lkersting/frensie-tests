#! /usr/bin/env python
import argparse as ap
import xml.etree.ElementTree as ET
import sys; sys.path.append("../../")
from ElementTree_pretty import prettify
import os.path

# Set up the argument parser
description = "This script allows one to write the est.xml file for FACEMC. "\
              "The input parameter is the source energy."

parser = ap.ArgumentParser(description=description)

energy_msg = "the source energy (in MeV)"
parser.add_argument('-e', help=energy_msg, required=True)

# Parse the user's arguments
user_args = parser.parse_args()
energy = user_args.e

root = ET.Element("ParameterList", name="Simulation Info")


parameter_1 = ET.SubElement(root, "ParameterList", name="Surface Current Estimator 1")

ET.SubElement(parameter_1, "Parameter", name="Id", type="unsigned int", value="1")

ET.SubElement(parameter_1, "Parameter", name="Type", type="string", value="Surface Current")

ET.SubElement(parameter_1, "Parameter", name="Particle Type", type="string", value="Electron")

ET.SubElement(parameter_1, "Parameter", name="Surfaces", type="Array", value="{4, 6}")

sub_list_1 = ET.SubElement(parameter_1, "ParameterList", name="Bins")
ET.SubElement(sub_list_1, "Parameter", name="Cosine Bins", type="Array", value="{-1.0, -0.99, 0.0, 1.0}")


parameter_2 = ET.SubElement(root, "ParameterList", name="Surface Current Estimator 2")

ET.SubElement(parameter_2, "Parameter", name="Id", type="unsigned int", value="2")

ET.SubElement(parameter_2, "Parameter", name="Type", type="string", value="Surface Current")

ET.SubElement(parameter_2, "Parameter", name="Particle Type", type="string", value="Electron")

ET.SubElement(parameter_2, "Parameter", name="Surfaces", type="Array", value="{4, 6}")

sub_list_2 = ET.SubElement(parameter_2, "ParameterList", name="Bins")
ET.SubElement(sub_list_2, "Parameter", name="Cosine Bins", type="Array", value="{-1.0, 0.0, 1.0}")


parameter_3 = ET.SubElement(root, "ParameterList", name="Cell Track Length Flux Estimator")

ET.SubElement(parameter_3, "Parameter", name="Id", type="unsigned int", value="3")

ET.SubElement(parameter_3, "Parameter", name="Type", type="string", value="Cell Track-Length Flux")

ET.SubElement(parameter_3, "Parameter", name="Particle Type", type="string", value="Electron")

ET.SubElement(parameter_3, "Parameter", name="Cells", type="Array", value="{1}")

sub_list_3 = ET.SubElement(parameter_3, "ParameterList", name="Bins")
ET.SubElement(sub_list_3, "Parameter", name="Energy Bins", type="Array", value="{1.5e-5, 99l, " + str(energy)+ "}")

# Set name for source file
name = "est_"+str(energy)+".xml"
i=1
while os.path.isfile(name):
  name = "est_"+str(energy)+"_" +str(i)+".xml"
  i=i+1

prettify(root,name)
print name