#!/bin/bash
####  PBS preamble

#PBS -m bea
#PBS -j oe

#PBS -l nodes=1:ppn=12,pmem=2gb
#PBS -V

#PBS -A hbmayes_fluxod
#PBS -q fluxod

#PBS -l walltime={walltime}:00:00
#PBS -N {job_name}
####  End PBS preamble
####  Commands follow this line

# print this file listing the computers that were used
if [ -e "$PBS_NODEFILE" ] ; then
    echo "Running on"
    uniq -c $PBS_NODEFILE
fi

# changes to the directory that the program is run from, and prints it out
if [ -d "$PBS_O_WORKDIR" ] ; then
    cd $PBS_O_WORKDIR
fi

namd2 +p 12 {output_name}.inp >& {output_name}.log