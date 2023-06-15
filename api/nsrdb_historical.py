import h5pyd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.spatial import cKDTree

YEAR = '2020'
f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{YEAR}.h5", 'r')

extracted_df = pd.DataFrame(columns = list(f))
variables = list(f)
"""
['air_temperature', 'alpha', 'aod', 'asymmetry', 'cld_opd_dcomp', 'cld_reff_dcomp', 'clearsky_dhi', 'clearsky_dni', 'clearsky_ghi', 'cloud_press_acha', 'cloud_type', 'coordinates', 'dew_point', 'dhi', 'dni', 'fill_flag', 'ghi', 'meta', 'ozone', 'relative_humidity', 'solar_zenith_angle', 'ssa', 'surface_albedo', 'surface_pressure', 'time_index', 'total_precipitable_water', 'wind_direction', 'wind_speed']
"""

# Extract datetime index for datasets
time_index = pd.to_datetime(f['time_index'][...].astype(str))

coordinates = pd.DataFrame(f['coordinates'][...])
print(coordinates.head(10))

"""
print(time_index)

meta = pd.DataFrame(f['meta'][...])
print(meta.head())
"""
