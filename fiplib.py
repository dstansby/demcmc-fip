from typing import Tuple, Generator

import numpy as np
import xarray as xr

from demcmc.units import u_temp, u_dem
from demcmc import DEMOutput, TempBins


def parse_line(line: str) -> str:
    line = line.replace("_int", "")
    line_split = line.split("_")
    line_split[0] = line_split[0].capitalize()
    line_split[1] = line_split[1].upper()

    line_str = f"{line_split[0]} {line_split[1]} {line_split[2]}.{line_split[3]}"
    return line_str


def dem_output2xr(dem_out: DEMOutput) -> xr.DataArray:
    """
    Convert the output of a DEM calculation into a DataArray
    """
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


def xr2dem_outputs(da: xr.DataArray) -> Generator[Tuple[int, DEMOutput], None, None]:
    """
    Convert a loaded DataArray with a row of data to a set of DEMOutput objects,
    one for each pixel.
    """
    for ypix in da.coords["ypix"].values:
        dem_data = da.sel(ypix=ypix)
        output = DEMOutput()
        output._temp_bins = TempBins(dem_data.attrs["Temp bin edges"] * u_temp)
        output._samples = dem_data.data * u_dem
        yield ypix, output
