# `demcmc-fip`

This repository contains scripts for estimating the first ionisation potential bias (FIP bias) using [demcmc](https://demcmc.readthedocs.io) to do the differential emission measure (DEM) calculations.
The scripts here are designed to be run on [Myriad](https://www.rc.ucl.ac.uk/docs/Clusters/Myriad/), one of the high performance computing systems at University College London (UCL).
It shouldn't be too hard to adapt them to work elsewhere.

## Ingredients
To start with you'll need
- a numpy `.npy` file with fitted intensities and intensity errors across a whole EIS map.
- a `.sav` file with contribution functions for each of the observed lines.

The lines in each of these files need to be a number of Fe lines for calculating the DEM, and the S and Si lines for estimating the FIP bias.
Put both files in the same folder, and make a note of that folder for later.

## Recipe
Make sure your ingredients are prepared as per the above section.
Then `run_dem.py` runs the DEM calculation. Two things need to be configured at the top of this script:
  - The number of parallel threads used to process the DEM data.
  - The input and output data directories.
Running this script will output progress to a log file in the output directory.
Processing of the DEM for each pixel will happen independently and in parallel.
When a pixel is processed the DEM will be output to...
