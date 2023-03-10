from pathlib import Path
import logging

import numpy as np
import tqdm

import astropy.units as u
from eispac import read_cube
from scipy.io import readsav
from sunpy.map import Map
import xarray as xr

from demcmc import ContFuncDiscrete, EmissionLine

from fiplib import parse_line, xr2dem_outputs

#################
# Configuration #
#################
# The input data path should contain:
#  - `emissivity.sav`: File containing pre-computed emissivity data.
#  - `intensities.npy`: File containing observed intensities and intensity errors.
#
input_data_path = Path(__file__).parent / "data_in"
input_eis_fname = "eis_20150401_162014.data.h5"
# The DEM data path should contain the .nc files with the DEMs
dem_path = Path(__file__).parent / "dems"
# Path where output array and log will be saved
output_data_path = Path(__file__).parent / "fip_out"

output_data_path.mkdir(exist_ok=True)
fip_lines = np.load(input_data_path / "intensities.npy", allow_pickle=True).tolist()
cont_func_data = readsav(str(input_data_path / "emissivity.sav"))


cont_func_temps = np.logspace(4, 8, 401) * u.K


# Setup logging
logging.basicConfig(
    filename=str(output_data_path / "run_fip.log"),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
)


def get_cont_funcs(xpix: int, ypix: int):
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
    Load all non-Fe lines at a given pixel.
    """
    cont_funcs = get_cont_funcs(xpix, ypix)
    lines = {}
    for key in fip_lines.keys():
        if "err" in key:
            continue

        line_name = parse_line(key)
        # Only load non Fe lines
        if "Fe" in line_name:
            continue
        intensity = fip_lines[key][xpix, ypix]
        error = fip_lines[key + "_err"][xpix, ypix]

        cont_func = cont_funcs[line_name]

        line = EmissionLine(
            cont_func,
            intensity_obs=intensity,
            sigma_intensity_obs=error,
        )
        lines[line_name.split(" ")[0]] = line
    return lines


map_shape = list(fip_lines.values())[0].shape
xys = np.meshgrid(np.arange(map_shape[0]), np.arange(map_shape[1]))
fip_array = np.zeros(map_shape) * np.nan

xs = np.arange(map_shape[0])
for x in tqdm.tqdm(xs, total=len(xs)):
    fname = dem_path / f"dem_{x}.nc"
    if not fname.exists():
        logging.info(f"No DEM file exists for {x=}")
        continue

    da = xr.load_dataarray(fname)
    for y, dem in xr2dem_outputs(da):
        lines = get_lines(x, y)

        # Check that Si and S intensities are > 0
        if not np.all(np.array([line.intensity_obs for line in lines.values()]) > 0):
            logging.info(f"Either S or Si intensity is zero for pixel ({x}, {y})")
            continue

        # Iterate through all the DEM samples, and calculate the FIP bias
        # for each sample
        fips = []
        for sample in dem.iter_binned_dems():
            # Predict Si intensity from DEM
            I_pred = lines["Si"].I_pred(sample)
            if not I_pred > 0:
                continue
            correction = lines["Si"].intensity_obs / I_pred
            fip = lines["S"].I_pred(sample) / lines["S"].intensity_obs
            fips.append(fip * correction)

        if not len(fips):
            logging.info(f"Predicted Si intensities are all zero for pixel ({x}, {y})")
            continue

        # Take the mean of all the sampled FIP biases. Could take another
        # measure here (e.g. the median), or save the whole sample set,
        # or calculate the standard deviation of samples (or something
        # else I haven't thought of!)
        logging.info(f"Saving mean FIP bias for pixel ({x}, {y})")
        fip_array[x, y] = np.mean(fips)

# Save array
np.save(str(output_data_path / "fip_array.npy"), fip_array)

fip_array = np.load(str(output_data_path / "fip_array.npy"))
# Convert bare array to FITS file
cube = read_cube(input_data_path / "eis_20150401_162014.data.h5")
# Use sum_spectra to get the 2D WCS
wcs = cube.sum_spectra().wcs
header = wcs.to_header()
header["DATE-OBS"] = cube.meta["index"]["date_obs"]
fip_map = Map(fip_array, header)

fip_map.save(output_data_path / "fip_map.fits", overwrite=True)
