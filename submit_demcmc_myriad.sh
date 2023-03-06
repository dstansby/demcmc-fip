#!/bin/bash -l

# Change this to point to the location of the DEM script
DEM_SCRIPT = "/home/ucasdst/fip/run_dem.py"
# Change the next line to set the number of cores. Max
# on Myriad is 36, but much easier to set to a lower
# number (e.g. 18) to avoid a long wait in a the queue
#
#$ -pe smp 16

# Request wallclock time (format hours:minutes:seconds).
#$ -l h_rt=12:00:0

# Request RAM (must be an integer followed by M, G, or T)
#$ -l mem=2G

# Request TMPDIR space (default is 10 GB - remove if cluster is diskless)
#$ -l tmpfs=10G

# Set the name of the job.
#$ -N demcmc

# Set the working directory to somewhere in your scratch space.
# This is a necessary step as compute nodes cannot write to $HOME.
#$ -wd /home/$(whoami)/Scratch


# Your work should be done in $TMPDIR
cd $TMPDIR

module load "python3/3.9"
virtualenv ./fipenv
source ./fipenv/bin/activate

which python
python -m pip install --upgrade pip
python -m pip install /home/ucasdst/fip/demcmc
python -m pip install scipy multiprocessing-logging

date
python $DEM_SCRIPT
