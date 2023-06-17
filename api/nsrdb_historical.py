from datetime import datetime
import h5json
import h5pyd
import h5py
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import time

"""
for YEAR in range(2000,2023):
    YEAR = str(YEAR)
    f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{YEAR}.h5", 'r')
    print(f) # <HDF5 file "nsrdb_2020.h5" (mode r)>
    
    print("Keys:")
    for key in f.keys():
        print("\t" + key)
"""
YEAR = '2020'
f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{YEAR}.h5", 'r')
print(f)

variables = f.keys()
"""
variables = ['air_temperature', 'alpha', 'aod', 'asymmetry', 'cld_opd_dcomp', 'cld_reff_dcomp', 'clearsky_dhi', 'clearsky_dni', 'clearsky_ghi', 'cloud_press_acha', 'cloud_type', 'coordinates', 'dew_point', 'dhi', 'dni', 'fill_flag', 'ghi', 'meta', 'ozone', 'relative_humidity', 'solar_zenith_angle', 'ssa', 'surface_albedo', 'surface_pressure', 'time_index', 'total_precipitable_water', 'wind_direction', 'wind_speed']
"""

# Extract datetime index for datasets
meta = pd.DataFrame(f['meta'][...])
print(meta.head(10))
coordinates = pd.Dataframe(f['coordinates'][...])
print(coordinates.head(10))
time_index = pd.to_datetime(f['time_index'][...].astype(str))
print(time_index.head(10))

# Data sets are stored in a 2D array of TIME X LOCATION
data = f['solar_zenith_angle']
print(data.shape)
print(data.dtype)
print(data.chunks) #  chunk by week
print(data.attrs['psm_scale_factor']) # convert values back to float using the 'psm_scale_factor'

""" TEST 1: Overall trend over a historical time period """
print("\n executing test 1 \n")
# Slice by month
MONTH = datetime.now().month

time_index = pd.to_datetime(f['time_index'][...].astype(str))
idx = time_index.month == MONTH
print(idx)
print(f['solar_zenith_angle'][idx[0]])
print(np.mean(f['solar_zenith_angle'][idx[0]]))

""" TEST 2: Variance of this day in history """
print("\n executing test 2 \n")
# Slice by date
# YEAR = datetime.today().year
# f = h5pyd.File(f"/nrel/nsrdb/v3/nsrdb_{YEAR}.h5", 'r')

CURR_DATE = YEAR + "-" + datetime.today().strftime('%m-%d')

time_index = pd.to_datetime(f['time_index'][...].astype(str))
idx = np.where(CURR_DATE in time_index)
print(idx)
print(f['solar_zenith_angle'][idx[0][0]])


""" TEST 3: Spatial variance at a given time """
print("\n executing test 3 \n")
print(dict(f['coordinates'].attrs))
coords = f['coordinates'][...]

data = f['solar_zenith_angle']
dataset = data[idx[0][0],::10] # extract every 10th location at a given time
df = pd.DataFrame() # Combine data with coordinates in a DataFrame
df['longitude'] = coords[::10, 1]
df['latitude'] = coords[::10, 0]
df['solar_zenith_angle'] = dataset / data.attrs['psm_scale_factor'] # unscale dataset
print(df.shape)

df.plot.scatter(x = 'longitude', y = 'latitude', c = 'solar_zenith_angle',
                colormap = 'YlOrRd',
                title = str(time_index[idx[0][0]]))
plt.show()

""" TEST 4: All of Singapore """
print("\n executing test 4 \n")
# Full resolution subset of Singapore
meta = pd.DataFrame(f['meta'][...])
SG = meta.loc[meta['country'] == b'Singapore'] # Note .h5 saves strings as bit-strings
print(SG.head(10))

# Extract coordinates (lat, lon)
print(dict(f['coordinates'].attrs))
coords = f['coordinates'][...]
