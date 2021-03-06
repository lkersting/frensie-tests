#! /usr/bin/env python
import argparse as ap
import xml.etree.ElementTree as ET
from ElementTree_pretty import prettify
import os.path

# Set up the argument parser
description = "This script allows one to write the mat.xml file for FACEMC. "\
              "The input parameter is the element, file type and interpolation."

parser = ap.ArgumentParser(description=description)

element_msg = "the elemental symbol (ie: H, He, Al, Pb ). Must be properly capitalized (ie: Al not al or AL)"
parser.add_argument('-n', help=element_msg, required=True)

file_type_msg = "the file type (ace, epr14 or native )"
parser.add_argument('-t', help=file_type_msg, required=True)

file_type_msg = "the 2D electron interpolation ( logloglog, linlinlin or linlinlog)"
parser.add_argument('-i', help=file_type_msg, required=True)


# Parse the user's arguments
user_args = parser.parse_args()
element_symbol = user_args.n
file_type = user_args.t
interp = user_args.i

filename = "{" + element_symbol

if file_type == "ace":
  filename += "}"
elif file_type == "epr14":
  filename += "_v14}"
elif interp == "logloglog":
  filename += "-Native}"
elif interp == "linlinlog":
  filename += "-LinLinLog}"
elif interp == "linlinlin":
  filename += "-LinLinLin}"

root = ET.Element("ParameterList", name="Materials")

parameter_1 = ET.SubElement(root, "ParameterList", name=element_symbol)

ET.SubElement(parameter_1, "Parameter", name="Id", type="unsigned int", value="1")
ET.SubElement(parameter_1, "Parameter", name="Fractions", type="Array", value="{1.0}")
ET.SubElement(parameter_1, "Parameter", name="Isotopes", type="Array(string)", value=filename)

name="mat_"+element_symbol+"_"+file_type+"_"+interp+".xml"
i=1
while os.path.isfile(name):
  name = "mat_"+element_symbol+"_"+file_type+"_"+interp+"_" +str(i)+".xml"
  i=i+1

prettify(root,name)
print name