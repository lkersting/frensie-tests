#!/bin/bash
##---------------------------------------------------------------------------##
## FACEMC test result data processor
##---------------------------------------------------------------------------##

EXTRA_ARGS=$@
TESTING_DIR="/home/lkersting/frensie/frensie-tests"

if [ "$#" -ne 1 ]; then
    echo "The input file is required. $# arguments provided!"
    echo "run:  ./data_processor.sh <file_name minus .h5>"
else
    # Set file name
    FILE=$1

    H5="${FILE}.h5"

    if [ -f $H5 ]; then
        output="${FILE}_transmission.txt"
        # Extract the surface current data for transmission
        ${TESTING_DIR}/edump.py -f $H5 -e 1 -i 48 -b Cosine > ${output}
        # convert to #/sqaure degrees
        spectrum="${FILE}_spectrum.txt"
        python ../../../convert_to_square_degrees.py -f ${output} -o ${spectrum}
        # Plot the spectrum results
        plot="${FILE}.pdf"
        echo "${FILE}" | python ../../../plot_results.py -o ${plot} ${spectrum}

        output="${FILE}_reflection.txt"
        # Extract the surface current data for reflection
        ${TESTING_DIR}/edump.py -f $H5 -e 2 -i 46 -b Cosine > ${output}

        output="${FILE}_cell_flux.txt"
        # Extract the surface current data
        ${TESTING_DIR}/edump.py -f $H5 -e 3 -i total -b Energy > ${output}
    else
       echo "File $H5 does not exist."
    fi
fi


