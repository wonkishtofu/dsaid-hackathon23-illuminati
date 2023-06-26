# load functions from other scripts
import calendar
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd

from conversions import to_bearing
from demand import get_demand_estimate
from geocode import geocode
from pvwatts import get_solar_estimate
from solarposition import get_optimal_angles, get_suninfo

# SUPPLY
ADDRESS = input("Enter an address in Singapore: ")

LAT, LON = geocode(ADDRESS)
DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) # UTC

exposure_times = get_suninfo(LAT, LON, DT)
azimuth, tilt = get_optimal_angles(exposure_times)

print(f"Optimal azimuth = {np.round(azimuth, 2)} ({to_bearing(azimuth)}) \n\
Optimal tilt = {np.round(tilt, 2)}")

AC_output = get_solar_estimate(LAT, LON, ADDRESS, azimuth, tilt)


# DEMAND
DWELLING = input("Enter dwelling type: ")
if DWELLING == 'Landed Properties':
    roof_area = input("Enter estimated roof area: ")

annual_demand, ytd_demand, hours_elapsed = get_demand_estimate(DT, DWELLING)

print(f"Estimated Annual Energy Consumption by an Average {DWELLING} Dwelling: {np.round(annual_demand, 0)} kWh")

num_panels = 1
if DWELLING == 'Landed Properties':
    num_panels = int(np.floor(float(roof_area)/1.6))
    
annual_supply = num_panels*sum(AC_output)/1000

print(f"Estimated Annual Energy Generation by {num_panels} Standard 250W Solar Panels: {np.round(annual_supply, 0)} kWh (i.e. {np.round(100*annual_supply/annual_demand, 2)}%)")

print(f"Estimated Year-to-date Energy Generation: {np.round(num_panels*sum(AC_output[:hours_elapsed])/1000, 2)} kWh")
