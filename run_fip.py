from pathlib import Path

import numpy as np
import tqdm

import astropy.units as u
from scipy.io import readsav

from demcmc import DEMOutput, ContFuncDiscrete, EmissionLine

from fiplib import parse_line

cont_func_data = readsav("../data/test_emissivity_13lines_demcmc.sav")
cont_func_temps = np.logspace(4, 8, 401) * u.K


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


fip_lines = np.load("../data/FIP_lines_new.npy", allow_pickle=True).tolist()


def get_lines(xpix: int, ypix: int):
    cont_funcs = get_cont_funcs(xpix, ypix)
    lines = {}
    for key in fip_lines.keys():
        if "err" in key:
            continue

        line_name = parse_line(key)
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

xs, ys = xys[0].ravel(), xys[1].ravel()
for x, y in tqdm.tqdm(zip(xs, ys), total=len(xs)):
    fname = Path(f"~/Downloads/dems/dem_{x}_{y}.nc").expanduser()
    if not fname.exists():
        continue
    if np.isfinite(fip_array[x, y]):
        continue
    dem = DEMOutput.load(fname)
    lines = get_lines(x, y)
    if not np.all(np.array([l.intensity_obs for l in lines.values()]) > 0):
        continue

    fips = []
    for sample in dem.iter_binned_dems():
        I_pred = lines["Si"].I_pred(sample)
        if not I_pred > 0:
            continue
        correction = lines["Si"].intensity_obs / I_pred
        fip = lines["S"].I_pred(sample) / lines["S"].intensity_obs
        fips.append(fip * correction)

    if not len(fips):
        continue

    fip_array[x, y] = np.mean(fips)

np.save("fip_array.npy", fip_array)
