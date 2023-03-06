from multiprocessing import Pool
from pathlib import Path
import os
import logging
from typing import Tuple

from multiprocessing_logging import install_mp_handler

import astropy.units as u
import numpy as np
from scipy.io import readsav

from demcmc.emission import ContFuncDiscrete, EmissionLine, TempBins
from demcmc.mcmc import predict_dem_emcee

from .lib import parse_line

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
username = "ucasdst"  # UCL username
scratch = Path(f"/scratch/scratch/{username}") / str(os.environ["JOB_ID"])
scratch.mkdir(exist_ok=True)
output_data_path = scratch


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
        if "Fe" not in line_name:
            continue
        intensity = fip_lines[key][xpix, ypix]
        error = fip_lines[key + "_err"][xpix, ypix]

        cont_func = cont_funcs[line_name]

        line = EmissionLine(
            cont_func,
            intensity_obs=intensity,
            sigma_intensity_obs=error,
        )
        lines.append(line)
    return lines


# DEM calculation
def calc_dem(params: Tuple[int, int]) -> int:
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

    for ypix in np.arange(len_y):
        lines = get_lines(xpix, ypix)
        if not np.all(np.array([line.intensity_obs for line in lines]) > 0):
            logging.info(f"Skipping ({xpix}, {ypix})")
            return 0
        logging.info(f"Processing pixel {xpix}, {ypix}")
        dem_result = predict_dem_emcee(
            lines, temp_bins, nwalkers=200, nsteps=400, progress=False
        )

    dem_result.save(output_data_path / f"dem_{xpix}_{ypix}.nc")
    return 1


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        filename=str(output_data_path / "demcmc.log"),
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
    )
    install_mp_handler()

    # Prevent numpy from trying to multithread calculations
    os.environ["OMP_NUM_THREADS"] = "1"
    logging.info("Starting run_demcmc.py ...")

    # Load contribution function data
    logging.info("Loading contribution function data...")
    cont_func_data = readsav(str(input_data_path / "emissivity.sav"))
    cont_func_temps = np.logspace(4, 8, 401) * u.K

    # Load emission line data
    logging.info("Loading emission line data...")
    fip_lines = np.load(
        (input_data_path / "intensities.npy"), allow_pickle=True
    ).tolist()

    # Get the map shape, and setup the parameters to run for each thread
    map_shape = cont_func_data["emissivity_array"].shape[:2]
    x, y = np.meshgrid(np.arange(map_shape[0]), np.arange(map_shape[1]))
    xs, ys = x.ravel(), y.ravel()
    xys = [(x, y, i, len(xs)) for i, (x, y) in enumerate(zip(xs, ys))]

    # Each thread runs at a single x pixel, and runs through all y pixels
    params = [(x, map_shape[1]) for x in np.arange(map_shape[0])]

    logging.info(f"Processing {len(xys)} pixels...")

    with Pool(n_threads) as p:
        p.map(calc_dem, params)

    logging.info("Finished processing pixels!")
