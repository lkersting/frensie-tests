#!/bin/bash
##---------------------------------------------------------------------------##
## ---------------------------- FACEMC test runner --------------------------##
##---------------------------------------------------------------------------##
## FRENSIE verification test: Self Adjoint test.
## The adjoint surface flux in source energy bins at the delta forward source
## energy
##---------------------------------------------------------------------------##

##---------------------------------------------------------------------------##
## ---------------------------- TEST VARIABLES ------------------------------##
##---------------------------------------------------------------------------##
EXTRA_ARGS=$@

# Set the number of mpi processes and openMP threads
# NOTE: OpenMP threads should be a factor of 16 for univ and 20 for univ2
# NOTE: the max OpenMP threads should be <= 6
MPI_PROCESSES=40
OPEN_MP_THREADS=4

# Set the number of histories
HISTORIES=1000000
# Set the max runtime (in minutes, 1 day = 1440 )
TIME=1350

# Set the scripts that will be edited ( 'forward.sh' 'adjoint.sh' )
scripts=( 'forward.sh' 'adjoint.sh' )

# Set the elastic distribution mode ( DECOUPLED COUPLED HYBRID )
modes=( COUPLED )

# Set the elastic coupled sampling method
# ( ONE_D TWO_D MODIFIED_TWO_D )
methods=( MODIFIED_TWO_D )

# Turn individual physics options off ( ELASTIC IONIZATION )
reactions_off=( )

##---------------------------------------------------------------------------##
## ------------------------------- COMMANDS ---------------------------------##
##---------------------------------------------------------------------------##

# Set the number of threads
command1="s/\#SBATCH[[:space:]]--ntasks=.*/\#SBATCH --ntasks=${MPI_PROCESSES}/"
command2="s/\#SBATCH[[:space:]]--cpus-per-task=.*/\#SBATCH --cpus-per-task=${OPEN_MP_THREADS}/"

# Set the wall time and number of histories
command3=s/TIME=.*/TIME=${TIME}/
command4=s/HISTORIES=.*/HISTORIES=${HISTORIES}/

for script in ${scripts[@]}
do
  sed -i "${command1}" ${script}
  sed -i "${command2}" ${script}
  sed -i "${command3}" ${script}
  sed -i "${command4}" ${script}
done

for mode in "${modes[@]}"
do
  # Set the elastic distribution mode
  command=s/MODE=.*/MODE=${mode}/
  for script in ${scripts[@]}; do
    sed -i "${command}" ${script}
  done
  echo "Setting elastic mode to ${mode}"

  if [ "${mode}" == "COUPLED" ]; then

    for method in "${methods[@]}"
    do
      # Set the elastic coupled sampling method
      command=s/METHOD=.*/METHOD=${method}/
      for script in ${scripts[@]}; do
        sed -i "${command}" ${script}
      done
      echo "  Setting elastic coupled sampling method to ${method}"

      for reaction in "${reactions_off[@]}"
      do
        # Set the reaction off
        command=s/${reaction}=.*/${reaction}=\'off\'/
        for script in "${scripts[@]}"; do
          sed -i "${command}" ${script}
        done
        echo "    Turning the ${reaction} reaction off"

        for script in "${scripts[@]}"; do
          sbatch ${script}
        done

        # Set the reaction on
        command=s/${reaction}=.*/${reaction}=\'\'/
        for script in ${scripts[@]}; do
          sed -i "${command}" ${script}
        done

      done

      if [ "${reactions_off}" == "" ]; then
          for script in "${scripts[@]}"; do
            sbatch ${script}
          done
      fi

    done
  else
    for script in "${scripts[@]}"; do
      sbatch ${script}
    done

    if [ "${reactions_off}" == "" ]; then
      for script in "${scripts[@]}"; do
        sbatch ${script}
      done
    fi

  fi
done