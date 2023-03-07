import numpy as np
import xarray as xr

from demcmc.units import u_temp
from demcmc import DEMOutput


def parse_line(line: str) -> str:
    line = line.replace("_int", "")
    line_split = line.split("_")
    line_split[0] = line_split[0].capitalize()
    line_split[1] = line_split[1].upper()

    line_str = f"{line_split[0]} {line_split[1]} {line_split[2]}.{line_split[3]}"
    return line_str


def dem_output2xr(dem_out: DEMOutput) -> xr.DataArray:
    temp_centers = dem_out.temp_bins.bin_centers
    temp_edges = dem_out.temp_bins.edges

    samplers = np.arange(dem_out.samples.shape[0])
    coords = {"Sampler": samplers, "Temp bin center": temp_centers.to_value(u_temp)}

    da = xr.DataArray(
        data=dem_out.samples,
        coords=coords,
        attrs={"Temp bin edges": temp_edges.to_value(u_temp)},
    )
    return da
