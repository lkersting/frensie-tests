#!/bin/bash
##---------------------------------------------------------------------------##
## FACEMC test runner
##---------------------------------------------------------------------------##
## Validation runs comparing FRENSIE and MCNP.
## The electron albedo is found for a semi-infinite aluminum slab. Since the
## electron albedo requires a surface current, DagMC will be used and not Root.
## FRENSIE will be run with four variations.
## 1. Using the Native data in analog mode, which uses a different interpolation
## scheme than MCNP.
## 2. Using Native data in moment preserving mode, which should give a less
## acurate answer while decreasing run time.
## 3. Using ACE (EPR14) data, which should match MCNP6.2 almost exactly.
## 4. Using ACE (EPR12) data, which should match MCNP6.1 almost exactly.
##---------------------------------------------------------------------------##

# Set cross_section.xml directory path.
EXTRA_ARGS=$@
CROSS_SECTION_XML_PATH=/home/software/mcnp6.2/MCNP_DATA
#CROSS_SECTION_XML_PATH=/home/lkersting/mcnpdata/
FRENSIE=/home/lkersting/frensie

THREADS="12"
if [ "$#" -eq 1 ]; then
    # Set the number of threads used
    THREADS="$1"
fi

# Changing variables
ENERGY=".015"
ELEMENT="Al"
# Number of histories
HISTORIES="10"
# Turn certain reactions on (true/false)
ELASTIC_ON="true"
BREM_ON="true"
IONIZATION_ON="true"
EXCITATION_ON="true"
# Two D Interp Policy (logloglog, linlinlin, linlinlog)
INTERP="logloglog"
# Two D Sampling Policy (1 = unit-base correlated, 2 = correlated, 3 = unit-base)
SAMPLE=1
# Elastic distribution ( Decoupled, Coupled, Hybrid )
DISTRIBUTION="Coupled"
# Elastic coupled sampling method ( 2D, 1D, 2DM )
COUPLED_SAMPLING="2DM"

NAME="native"

ELASTIC="-d ${DISTRIBUTION} -c ${COUPLED_SAMPLING}"
REACTIONS=" -t ${ELASTIC_ON} -b ${BREM_ON} -i ${IONIZATION_ON} -a ${EXCITATION_ON}"
SIM_PARAMETERS="-e ${ENERGY} -n ${HISTORIES} -l ${INTERP} -s ${SAMPLE} ${REACTIONS} ${ELASTIC}"
ENERGY_EV=$(echo $ENERGY*1000000 |bc)
ENERGY_EV=${ENERGY_EV%.*}

echo -n "Enter the desired data type (1 = Native, 2 = ACE EPR14, 3 = ACE EPR12) > "
read INPUT
if [ ${INPUT} -eq 2 ]; then
    # Use ACE EPR14 data
    NAME="epr14"
    echo "Using ACE EPR14 data!"
elif [ ${INPUT} -eq 3 ]; then
    # Use ACE EPR12 data
    NAME="ace"
    echo "Using ACE EPR12 data!"
elif [ ${DISTRIBUTION} = "Hybrid" ]; then
    # Use Native moment preserving data
    NAME="moments"
    echo "Using Native Moment Preserving data!"
else
    # Use Native analog data
    echo "Using Native analog data!"
fi

NAME_EXTENTION=""
NAME_REACTION=""
# Set the sim info xml file name
if [ "${ELASTIC_ON}" = "false" ]; then
    NAME_REACTION="${NAME_REACTION}_no_elastic"
elif [ ${DISTRIBUTION} = "Coupled" ]; then
    NAME_EXTENTION="${NAME_EXTENTION}_${COUPLED_SAMPLING}"
fi
if [ "${BREM_ON}" = "false" ]; then
    NAME_REACTION="${NAME_REACTION}_no_brem"
fi
if [ "${IONIZATION_ON}" = "false" ]; then
    NAME_REACTION="${NAME_REACTION}_no_ionization"
fi
if [ "${EXCITATION_ON}" = "false" ]; then
    NAME_REACTION="${NAME_REACTION}_no_excitation"
fi

# .xml file paths.
INFO=$(python ../../sim_info.py ${SIM_PARAMETERS} 2>&1)
MAT=$(python ../../mat.py -n ${ELEMENT} -t ${NAME} -i ${INTERP} 2>&1)
EST=$(python ../est.py -e ${ENERGY} 2>&1)
SOURCE=$(python source.py -e ${ENERGY} 2>&1)
GEOM="geom.xml"
RSP="../rsp_fn.xml"

# Make directory for the test results
TODAY=$(date +%Y-%m-%d)

if [ ${NAME} = "ace" -o ${NAME} = "epr14" ]; then
    DIR="results/testrun/${NAME}"
    NAME="al_${NAME}_${ENERGY_EV}${NAME_REACTION}"
else
    DIR="results/testrun/${INTERP}"

    if [ ${SAMPLE} = 1 ]
    then
        echo "unit_correlated"
        SAMPLE_NAME="unit_correlated"
    elif [ ${SAMPLE} = 2 ]
    then
        echo "correlated"
        SAMPLE_NAME="correlated"
    elif [ ${SAMPLE} = 3 ]
    then
        echo "unit_base"
        SAMPLE_NAME="unit_base"
    fi
    echo $SAMPLE_NAME

    NAME="al_${NAME}_${ENERGY_EV}_${INTERP}_${SAMPLE_NAME}${NAME_EXTENTION}${NAME_REACTION}"
fi

mkdir -p $DIR

echo "Running Facemc Albedo test with ${HISTORIES} particles on ${THREADS} threads:"
RUN="${FRENSIE}/bin/facemc --sim_info=${INFO} --geom_def=${GEOM} --mat_def=${MAT} --resp_def=$RSP --est_def=$EST --src_def=$SOURCE --cross_sec_dir=$CROSS_SECTION_XML_PATH --simulation_name=$NAME --threads=${THREADS}"
echo ${RUN}

# gdb --args ${RUN}
${RUN}

echo "Removing old xml files:"
rm ${INFO} ${EST} ${SOURCE} ${MAT} ../../ElementTree_pretty.pyc

echo "Processing the results:"
H5=${NAME}.h5
NEW_NAME="${DIR}/${H5}"
NEW_RUN_INFO="${DIR}/continue_run_${NAME}.xml"
mv ${H5} ${NEW_NAME}
mv continue_run.xml ${NEW_RUN_INFO}

cd ${DIR}

bash ../../../../data_processor.sh ${ENERGY} ${NAME}
echo "Results will be in ./${DIR}"