#!/bin/bash
##---------------------------------------------------------------------------##
## ---------------------------- FACEMC test runner --------------------------##
##---------------------------------------------------------------------------##
## FRENSIE benchmark test: Lockwood energy deposition in Al.
## The dose depth for several ranges and material is calculated by dividing the
## energy deposition by the calorimeter thickness (g/cm^2).
##---------------------------------------------------------------------------##

##---------------------------------------------------------------------------##
## ---------------------------- TEST VARIABLES ------------------------------##
##---------------------------------------------------------------------------##
EXTRA_ARGS=$@

# Set the number of threads
THREADS=160
NODES=10
TASKS=16
# Set the number of histories
HISTORIES=1000000
# Set the max runtime (in minutes, 1 day = 1440 )
TIME=1400

# Set the test energy (0.314, 0.521, 1.033)
energy=0.314

# Set the data file type (ACE Native)
file_types=( Native )

# Set the bivariate interpolation ( LOGLOGLOG LINLINLIN LINLINLOG )
interps=( LOGLOGLOG )

# Set the bivariate Grid Policy ( UNIT_BASE_CORRELATED CORRELATED UNIT_BASE )
grid_policys=( UNIT_BASE_CORRELATED )

# Set the elastic distribution mode ( DECOUPLED COUPLED HYBRID )
modes=( COUPLED )

# Set the elastic coupled sampling method
# ( ONE_D TWO_D MODIFIED_TWO_D )
methods=( MODIFIED_TWO_D )

# Set the test numbers (0.314: 0-11, 0.512: 0-17, 1.033: 0-25)
# test_numbers can be set to indivual test numbers e.g. ( 0 1 2 ) or "all"
test_numbers="all"

##---------------------------------------------------------------------------##
## ------------------------------- COMMANDS ---------------------------------##
##---------------------------------------------------------------------------##

# Set the ranges
if [ ${energy} == 0.314 ]; then
    # ranges for 0.314 MeV source (g/cm2)
    ranges="[ 0.0025, 0.0094, 0.0181, 0.0255, 0.0336, 0.0403, 0.0477, 0.0566, 0.0654, 0.0721, 0.0810, 0.0993 ]"

    if [ ${test_numbers} == "all" ]; then
        # Number of tests for 0.314 MeV
        test_numbers=( 0 1 2 3 4 5 6 7 8 9 10 11 )
    fi

elif [ ${energy} == 0.521 ]; then
    # ranges for 0.521 MeV source (g/cm2)
    ranges="[ 0.0025, 0.0094, 0.0180, 0.0255, 0.0335, 0.0405, 0.0475, 0.0566, 0.0653, 0.0721, 0.0807, 0.0992, 0.1111, 0.1259, 0.1439, 0.1596, 0.1825, 0.2125 ]"

    if [ ${test_numbers} == "all" ]; then
        # Number of tests for 0.314 MeV
        test_numbers=( 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 )
    fi

elif [ ${energy} == 1.033 ]; then
    # ranges for 1.033 MeV source (g/cm2)
    ranges="[ 0.0025, 0.0094, 0.0180, 0.0255, 0.0336, 0.0402, 0.0476, 0.0562, 0.0654, 0.0723, 0.0808, 0.0990, 0.1110, 0.1257, 0.1440, 0.1593, 0.1821, 0.2122, 0.2225, 0.2452, 0.2521, 0.2908, 0.3141, 0.3533, 0.4188, 0.4814 ]"

    if [ ${test_numbers} == "all" ]; then
        # Number of tests for 0.314 MeV
        test_numbers=( 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 )
    fi

else
    echo "Energy $energy MeV is currently not supported!"
fi

calorimeter_thickness=5.050E-03

# Material element
element="Al"; zaid=13000

# Set the element
command=s/atom=.*/atom=Data.${element}_ATOM\;\ element=\"${element}\"\;\ zaid=${zaid}/
sed -i "${command}" lockwood.py

# Set the calorimeter thickness
command=s/calorimeter_thickness=.*/calorimeter_thickness=${calorimeter_thickness}/
sed -i "${command}" lockwood.py

# Set the ranges
command=s/ranges=.*/ranges=${ranges}/
sed -i "${command}" lockwood.py

# Set the energy
command=s/energy=.*/energy=${energy}/
sed -i "${command}" lockwood.py

# Set the number of threads
command=s/THREADS=.*/THREADS=${THREADS}/
sed -i "${command}" lockwood.sh
command=s/NODES=.*/NODES=${NODES}/
sed -i "${command}" lockwood.sh
command=s/TASKS=.*/TASKS=${TASKS}/
sed -i "${command}" lockwood.sh
command=s/TIME=.*/TIME=${TIME}/
sed -i "${command}" lockwood.sh
command=s/HISTORIES=.*/HISTORIES=${HISTORIES}/
sed -i "${command}" lockwood.sh


for file_type in "${file_types[@]}"
do
  # Set the file type
  command=s/file_type=Data.ElectroatomicDataProperties.*/file_type=Data.ElectroatomicDataProperties.${file_type}_EPR_FILE/
  sed -i "${command}" lockwood.py
  echo "Setting file type to ${file_type}"

  if [ "${file_type}" = "Native" ]; then

    for interp in "${interps[@]}"
    do
      # Set the interp
      command=s/interpolation=MonteCarlo.*/interpolation=MonteCarlo.${interp}_INTERPOLATION/
      sed -i "${command}" lockwood.py
      echo "  Setting interpolation to ${interp}"

      for grid_policy in "${grid_policys[@]}"
      do
        if [ "${interp}" == "LINLINLOG" ] && [ "${grid_policy}" == "CORRELATED" ]; then
          echo "    The interp (${interp}) and grid policy (${grid_policy}) combo will be skipped."
        else

          # Set 2D grid policy
          command=s/grid_policy=MonteCarlo.*/grid_policy=MonteCarlo.${grid_policy}_GRID/
          sed -i "${command}" lockwood.py
          echo "    Setting grid policy to ${grid_policy}"

          for mode in "${modes[@]}"
          do
            # Set the elastic distribution mode
            command=s/mode=MonteCarlo.*/mode=MonteCarlo.${mode}_DISTRIBUTION/
            sed -i "${command}" lockwood.py
            echo "      Setting elastic mode to ${mode}"

            if [ "${mode}" == "COUPLED" ]; then

              for method in "${methods[@]}"
              do
                # Set the elastic coupled sampling method
                command=s/method=MonteCarlo.*/method=MonteCarlo.${method}_UNION/
                sed -i "${command}" lockwood.py
                echo "        Setting elastic coupled sampling method to ${method}"

                # loop through test numbers and run mpi script
                for test_number in "${test_numbers[@]}"
                do
                    # Change the test number
                    command=s/test_number=.*/test_number=\"$test_number\"/
                    sed -i "${command}" lockwood.py

                    echo -e "          Running Lockwood ${energy} Test Number $test_number!\n"
                    sbatch lockwood.sh
                done
              done
            else
              # loop through test numbers and run mpi script
              for test_number in "${test_numbers[@]}"
              do
                  # Change the test number
                  command=s/test_number=.*/test_number=\"$test_number\"/
                  sed -i "${command}" lockwood.py

                  echo -e "        Running Lockwood ${energy} Test Number $test_number!\n"
                  sbatch lockwood.sh
              done
            fi
          done
        fi
      done
    done
  else
    # loop through test numbers and run mpi script
    for test_number in "${test_numbers[@]}"
    do
        # Change the test number
        command=s/test_number=.*/test_number=\"$test_number\"/
        sed -i "${command}" lockwood.py

        echo -e "  Running Lockwood ${energy} Test Number $test_number!\n"
        sbatch lockwood.sh
    done
  fi

done