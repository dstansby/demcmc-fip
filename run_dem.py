from multiprocessing import Pool
from pathlib import Path
import os
import logging
from typing import Tuple


import astropy.units as u
import numpy as np
import pandas as pd
from scipy.io import readsav
import xarray as xr

from demcmc.emission import ContFuncDiscrete, EmissionLine, TempBins
from demcmc.mcmc import predict_dem_emcee

from fiplib import parse_line, dem_output2xr

#################
# Configuration #
#################
# Number of threads to run in parallel.
#
# This should be the same as the number of cores requested from Myriad
n_threads = 18
# Setup input and output data paths
#
# If not running on Myriad, `input_data_path` and `output_data_path`
# can be set to different directories.
#
# The input data path should contain:
#  - `emissivity.sav`: File containing pre-computed emissivity data.
#  - `intensities.npy`: File containing observed intensities and intensity errors.
#
input_data_path = Path(__file__).parent / "data_in"
if 'JOB_ID' in os.environ:
    # Probably running on Myriad
    username = "ucasdst"  # UCL username
    scratch = Path(f"/scratch/scratch/{username}") / str(os.environ["JOB_ID"])
    scratch.mkdir(exist_ok=True)
    output_data_path = scratch
else:
    output_data_path = Path(__file__).parent / "dems"

# Setup logging
logging.basicConfig(
    filename=str(output_data_path / "demcmc.log"),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
)
# install_mp_handler()

# Prevent numpy from trying to multithread calculations
os.environ["OMP_NUM_THREADS"] = "1"
logging.info("Starting run_demcmc.py ...")

# Load contribution function data
logging.info("Loading contribution function data...")

# Load emission line data
logging.info("Loading emission line data...")
fip_lines = np.load((input_data_path / "intensities.npy"), allow_pickle=True).tolist()

cont_func_data = readsav(str(input_data_path / "emissivity.sav"))
cont_func_temps = np.logspace(4, 8, 401) * u.K


def get_cont_funcs(xpix: int, ypix: int):
    """
    Get contribution functions at a given pixel.
    """
    data = cont_func_data["emissivity_array"][xpix, ypix].astype(float)
    lines = cont_func_data["lineid"].astype(str)

    cont_funcs = {}
    for i, line in enumerate(lines):
        cont_funcs[line] = ContFuncDiscrete(
            temps=cont_func_temps,
            values=data[i, :] * u.cm**5 / u.K,
        )

    return cont_funcs


def get_lines(xpix: int, ypix: int):
    """
    Load contribution functions and observed intensities at a given pixel.
    """
    cont_funcs = get_cont_funcs(xpix, ypix)
    lines = []
    for key in fip_lines.keys():
        if "err" in key:
            continue

        line_name = parse_line(key)
        # Only include Iron lines in the DEM estimation
        if "Fe" not in line_name:
            continue
        intensity = fip_lines[key][xpix, ypix]
        error = fip_lines[key + "_err"][xpix, ypix]

        cont_func = cont_funcs[line_name]

        line = EmissionLine(
            cont_func,
            intensity_obs=intensity,
            sigma_intensity_obs=error,
            name=line_name
        )
        lines.append(line)
    return lines


# DEM calculation
def calc_dem(params: Tuple[int, int]):
    """
    Calculate the DEM.

    Parameters
    ----------
    params : tuple[int, int]
        Tuple containing:
            - x coordinate
            - number of y coordinates
    """
    xpix, len_y = params
    temp_bins = TempBins(10 ** np.arange(5.6, 6.8, 0.1) * u.K)

    output_file = output_data_path / f"dem_{xpix}.nc"
    if output_file.exists():
        logging.info(f"Already processed {xpix=}")
        return

    ycoords = np.arange(len_y)
    # List to save coords that were processed
    ycoords_out = []
    dem_results = []
    line_masks = []
    for ypix in ycoords:
        lines = get_lines(xpix, ypix)
        # Save a copy of all the lines available
        all_line_names = [line.name for line in lines]
        # Select only lines with > 0 intensity
        line_mask = [line.intensity_obs > 0 for line in lines]
        lines = [line for line in lines if line.intensity_obs > 0]
        if not len(lines):
            logging.info(f"Skipping pixel ({xpix}, {ypix}), all zero intensities")
            continue

        logging.info(f"Processing ({xpix}, {ypix})")
        dem_result = predict_dem_emcee(
            lines, temp_bins, nwalkers=200, nsteps=400, progress=False
        )

        dem_results.append(dem_output2xr(dem_result))
        ycoords_out.append(ypix)
        line_masks.append(line_mask)

    if len(dem_results):
        # Save DEMs
        ycoords_idx = pd.Index(ycoords_out, name="ypix")
        all_dems = xr.concat(dem_results, ycoords_idx)
        temp_edges = dem_results[0].attrs["Temp bin edges"]
        all_dems.assign_attrs({"Temp bin edges": temp_edges})
        all_dems.to_netcdf(output_file)
        # Save line masks
        line_masks = np.array(line_masks, dtype=bool).T
        line_names_idx = pd.Index(all_line_names, name='line')
        line_masks = xr.DataArray(line_masks, coords=[all_line_names, ycoords_idx])
        line_masks.to_netcdf(output_data_path / f"dem_{xpix}_lines.nc")

if __name__ == "__main__":
    # Get the map shape, and setup the parameters to run for each thread
    map_shape = cont_func_data["emissivity_array"].shape[:2]
    # Each thread runs at a single x pixel, and runs through all y pixels
    params = [(x, map_shape[1]) for x in np.arange(map_shape[0])]

    logging.info(f"Processing {len(params)} rows...")

    with Pool(n_threads) as p:
        p.map(calc_dem, params)

    logging.info("Finished processing pixels!")
