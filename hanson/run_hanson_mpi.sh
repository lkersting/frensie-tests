#!/bin/sh
# This file is named run_facemc_mpi.sh
#SBATCH --partition=pre
#SBATCH --time=1-00:00:00
#SBATCH --nodes=5
#SBATCH --ntasks-per-node=16
#SBATCH --mem-per-cpu=4000

##---------------------------------------------------------------------------##
## ---------------------------- FACEMC test runner --------------------------##
##---------------------------------------------------------------------------##
## Validation runs comparing FRENSIE and MCNP.
## The electron angular distribution for a thin gold foil of .0009658 cm.
## The # of particles per steradian for scattering angle is found by dividing
## the surface current by 2pi * ( \mu_{i} - \mu_{i-1} ) where \mu_{0} is the
## lowest cosine bin (ie: -1). Surface current is needed so DagMC will be used.
## The #/steradians can be changed to #/square degree by multiplying by
## (pi/180)^2.
## FRENSIE will be run with three variations.
## 1. Using ACE data, which should match MCNP almost exactly.
## 2. Using the Native data in analog mode, whcih uses a different interpolation
## scheme than MCNP.
## 3. Using Native data in moment preserving mode, which should give a less
## acurate answer while decreasing run time.

##---------------------------------------------------------------------------##
## ------------------------------- COMMANDS ---------------------------------##
##---------------------------------------------------------------------------##

# Set cross_section.xml directory path.
EXTRA_ARGS=$@
CROSS_SECTION_XML_PATH=/home/ecmartin3/software/mcnpdata/
FRENSIE=/home/lkersting/frensie

INPUT="1"
if [ "$#" -eq 1 ];
then
    # Set the file type (1 = ACE, 2 = Native, 3 = Moment Preserving)
    INPUT="$1"
fi

# Changing variables
THREADS="80"
ELEMENT="Au"
# Number of histories 1e7
HISTORIES="10000000"
# Turn certain reactions on (true/false)
ELASTIC_ON="true"
BREM_ON="true"
IONIZATION_ON="true"
EXCITATION_ON="true"

REACTIONS=" -e ${ELASTIC_ON} -b ${BREM_ON} -i ${IONIZATION_ON} -a ${EXCITATION_ON}"
SIM_PARAMETERS="-n ${HISTORIES} ${REACTIONS}"
ENERGY="15.7"
NAME="ace"

if [ ${INPUT} -eq 1 ]
then
    # Use ACE data
    NAME="ace"
    SIM_PARAMETERS="${SIM_PARAMETERS} -c 1.0"
    python sim_info.py ${SIM_PARAMETERS}
    python mat.py -n ${ELEMENT} -t ${NAME}
    INFO="sim_info_1.0"
    MAT="mat_${ELEMENT}_${NAME}.xml"
    echo "Using ACE data!"
elif [ ${INPUT} -eq 2 ]
then
    # Use Native analog data
    NAME="native"
    SIM_PARAMETERS="${SIM_PARAMETERS} -c 1.0"
    python sim_info.py ${SIM_PARAMETERS}
    python mat.py -n ${ELEMENT} -t ${NAME}
    INFO="sim_info_1.0"
    MAT="mat_${ELEMENT}_${NAME}.xml"
    echo "Using Native analog data!"
elif [ ${INPUT} -eq 3 ]
then
    # Use Native Moment Preserving data
    NAME="moments"
    SIM_PARAMETERS="${SIM_PARAMETERS} -c 0.9"
    python sim_info.py ${SIM_PARAMETERS}
    python mat.py -n ${ELEMENT} -t "native"
    INFO="sim_info_0.9"
    MAT="mat_${ELEMENT}_native.xml"
    echo "Using Native Moment Preserving data!"
else
    # Default to ACE data
    NAME="ace"
    SIM_PARAMETERS="${SIM_PARAMETERS} -c 1.0"
    python sim_info.py ${SIM_PARAMETERS}
    python mat.py -n ${ELEMENT} -t ${NAME}
    INFO="sim_info_1.0"
    MAT="mat_${ELEMENT}_${NAME}.xml"
    echo "Input not valid, ACE data will be used!"
fi

NAME_EXTENTION=""
# Set the sim info xml file name
if [ "${ELASTIC_ON}" = "false" ]
then
    NAME_EXTENTION="_no_elastic"
fi
if [ "${BREM_ON}" = "false" ]
then
    NAME_EXTENTION="${NAME_EXTENTION}_no_brem"
fi
if [ "${IONIZATION_ON}" = "false" ]
then
    NAME_EXTENTION="${NAME_EXTENTION}_no_ionization"
fi
if [ "${EXCITATION_ON}" = "false" ]
then
    NAME_EXTENTION="${NAME_EXTENTION}_no_excitation"
fi
INFO="${INFO}${NAME_EXTENTION}.xml"

# .xml file paths.
EST="est.xml"
SOURCE="source.xml"
GEOM="geom.xml"
RSP="../rsp_fn.xml"
NAME="hanson_${NAME}${NAME_EXTENTION}"

# Make directory for the test results
TODAY=$(date +%Y-%m-%d)
DIR="results/linlog/${TODAY}"
mkdir -p $DIR

echo "Running Facemc Hanson test with ${HISTORIES} particles on ${THREADS} threads:"
RUN="mpiexec -n ${THREADS} ${FRENSIE}/bin/facemc-mpi --sim_info=${INFO} --geom_def=${GEOM} --mat_def=${MAT} --resp_def=${RSP} --est_def=${EST} --src_def=${SOURCE} --cross_sec_dir=${CROSS_SECTION_XML_PATH} --simulation_name=${NAME}"
echo ${RUN}
${RUN} > ${DIR}/${NAME}.txt 2>&1

echo "Removing old xml files:"
rm ${INFO} ${MAT} ElementTree_pretty.pyc

echo "Moving the results:"
# Move file to the test results folder
H5=${NAME}.h5
NEW_NAME="${DIR}/${H5}"
NEW_RUN_INFO="${DIR}/continue_run_${NAME}.xml"

mv ${H5} ${NEW_NAME}
mv continue_run.xml ${NEW_RUN_INFO}

echo "Results will be in ./${DIR}"