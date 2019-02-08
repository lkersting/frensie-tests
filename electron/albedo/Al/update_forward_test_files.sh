#!/bin/bash
##---------------------------------------------------------------------------##
## Al Albedo test data updater
##---------------------------------------------------------------------------##

# Sbatch variables
partition=pre
time=1-00:00:00
ntasks=1
cpus=1

##---------------------------------------------------------------------------##
## ------------------------------- COMMANDS ---------------------------------##
##---------------------------------------------------------------------------##

database='/home/lkersting/software/mcnp6.2/MCNP_DATA/database.xml'
if [ ! -f "${database}" ]; then
  database='/home/software/mcnpdata/database.xml'
fi

sbatch_command="sbatch --partition=${partition} --time=${time} --ntasks=${ntasks} --cpus-per-task=${cpus}"
# sbatch_command=bash
if ! type "sbatch" > /dev/null; then
  sbatch_command=bash
fi

if [ -f "${database}" ]; then

    # Update Al data version 0
    python_command="python ../../update_forward_test_files.py --db_name="${database}" -z 13 -g 'UnitBaseCorrelatedGrid' -v 0"
    printf "#!/bin/bash\n${python_command}" > update_Al_0_temp.sh
    ${sbatch_command} update_Al_0_temp.sh
    if [ ! $? -eq 0 ]; then
        printf "\nAl native data version 0 FAILED to update!\n"
        rm update_Al_0_temp.sh
        exit 1
    fi
    rm update_Al_0_temp.sh

    # Update Al data version 1
    python_command="python ../../update_forward_test_files.py --db_name="${database}" -z 13 -g 'UnitBaseGrid' -v 1 --refine_electron_secondary_grids"
    printf "#!/bin/bash\n${python_command}" > update_Al_1_temp.sh
    ${sbatch_command} update_Al_1_temp.sh
    if [ ! $? -eq 0 ]; then
        printf "\nAl native data version 1 FAILED to update!\n"
        rm update_Al_1_temp.sh
        exit 1
    fi
    rm update_Al_1_temp.sh

    # Update Al data version 2
    python_command="python ../../update_forward_test_files.py --db_name="${database}" -z 13 -g 'UnitBaseCorrelatedGrid' -v 2 --refine_electron_secondary_grids"
    printf "#!/bin/bash\n${python_command}" > update_Al_2_temp.sh
    ${sbatch_command} update_Al_2_temp.sh
    if [ ! $? -eq 0 ]; then
        printf "\nAl native data version 2 FAILED to update!\n"
        rm update_Al_2_temp.sh
        exit 1
    fi
    rm update_Al_2_temp.sh

    # Update Al data version 3
    python_command="python ../../update_forward_test_files.py --db_name="${database}" -z 13 -g 'CorrelatedGrid' -v 3 --refine_electron_secondary_grids"
    printf "#!/bin/bash\n${python_command}" > update_Al_3_temp.sh
    ${sbatch_command} update_Al_3_temp.sh
    if [ ! $? -eq 0 ]; then
        printf "\nAl native data version 3 FAILED to update!\n"
        rm update_Al_3_temp.sh
        exit 1
    fi
    rm update_Al_3_temp.sh

else
    printf "\nERROR: Invalid database file: ${database}\n"
fi