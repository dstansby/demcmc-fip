#!/bin/bash -l

#################
# Configuration #
#################
# Change the next line to set the number of cores. Max
# on Myriad is 36, but much easier to set to a lower
# number (e.g. 18) to avoid a long wait in a the queue
#
#$ -pe smp 16
#
# Set the working directory to somewhere in your scratch space.
# This is a necessary step as compute nodes cannot write to $HOME.
#$ -wd /home/ucasdst/Scratch
#################################
# End of standard configuration #
#################################

# Request wallclock time (format hours:minutes:seconds).
#$ -l h_rt=24:00:0

# Request RAM (must be an integer followed by M, G, or T)
#$ -l mem=2G

# Request TMPDIR space (default is 10 GB - remove if cluster is diskless)
#$ -l tmpfs=10G

# Set the name of the job.
#$ -N demcmc


# Your work should be done in $TMPDIR
cd $TMPDIR

module load "python3/3.9"
virtualenv ./fipenv
source ./fipenv/bin/activate

which python
python -m pip install --upgrade pip
python -m pip install demcmc scipy multiprocessing-logging --upgrade

date
# Set this to the locaiton of the dem script
python /home/ucasdst/demcmc-fip/run_dem.py
