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
Bellow follows a set of instructions for ending up with a FIP map.
