# `demcmc-fip`

This repository contains scripts for estimating the first ionisation potential bias (FIP bias) using [demcmc](https://demcmc.readthedocs.io) to do the differential emission measure (DEM) calculations.
The scripts here are designed to be run on [Myriad](https://www.rc.ucl.ac.uk/docs/Clusters/Myriad/), one of the high performance computing systems at University College London (UCL).
It shouldn't be too hard to adapt them to work elsewhere.

## Ingredients
To start with you'll need
- the original EIS observation as data/header h5 files. [eispac](https://eispac.readthedocs.io) has instructions one how to search for and download these.
- a numpy `.npy` file with fitted intensities and intensity errors across the whole EIS map.
- a `.sav` file with pre-computed contribution functions for each of the observed lines.

The lines in each of these files need to be a number of Fe lines for calculating the DEM, and the S and Si lines for estimating the FIP bias.
Put these three files in the same folder, and make a note of that folder for later.

## Recipe

### Calculating DEMs
Make sure your ingredients are prepared as per the above section.
Then `run_dem.py` runs the DEM calculation. Two things need to be configured at the top of this script:
  - The number of parallel threads used to process the DEM data.
  - The input and output data directories.
Running this script will output progress to a log file in the output directory.
Processing of the DEM for each pixel will happen independently and in parallel.
When a whole row of pixels is processed the DEMs will be output to a netCDF file called `dem_x.nc`, where x is the number that gives the x-pixel of the row that contains DEMs for all y-pixels.
Additional `dem_x_lines.nc` files will be produced, which give information on what lines were used to calculate the DEM.
A '1' value means that line was used to calculate the DEM for that pixel.

#### Running on Myriad
The `submit_demcmc_myriad.sh` script provides a job script to submit the MCMC calculations to [Myriad](https://www.rc.ucl.ac.uk/docs/Clusters/Myriad/).

### Calculating FIP biases
`run_fip.py` runs the FIP esitmation, using the DEMs calculated in the previous step.
The only things that need configuring in this file are the various input/output file path locations.
When you run this a progress bar should pop up in your terminal that shows you how long is left to process all the pixels.
When the script finishes running it will output a file called `fip_map.fits` in the previously specified output directory.

### Plotting the FIP map
`plot_fip.py` plots the generated FIP map, using some nice deafult colormap settings.
