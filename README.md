# `demcmc-fip`

This repository contains scripts for estimating the first ionisation potential bias (FIP bias) using [demcmc](https://demcmc.readthedocs.io) to do the differential emission measure (DEM) calculations.
The scripts here are designed to be run on [Myriad](https://www.rc.ucl.ac.uk/docs/Clusters/Myriad/), one of the high performance computing systems at University College London (UCL).
It shouldn't be too hard to adapt them to work elsewhere.

## Files

### `run_dem.py`
This script runs the DEM calculation.
There is a confiuration block at the top that should be used to set the number of parallel processes, and the input/output directories.

### `submit_demcmc_myriad.sh`
Submission script to submit `run_dem.py` to run on Myriad.
The location of `run_dem.py` and the required number of cores should be specified at the top of the file.
