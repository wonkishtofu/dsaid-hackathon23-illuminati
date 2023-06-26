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
azimuth, tilt = get_optimal_angles(LAT, LON, exposure_times)

print(f"Optimal azimuth = {np.round(azimuth, 2)} ({to_bearing(azimuth)}) \n\
Optimal tilt = {np.round(tilt, 2)}")

AC_output = get_solar_estimate(LAT, LON, azimuth, tilt)


# DEMANDs
DWELLING = input("\nEnter dwelling type: ")

if DWELLING == 'Landed Property':
    # get roof area for landed property
    roof_area = input("\nEnter estimated roof area (m²): ")
    annual_demand, ytd_demand, hours_elapsed = get_demand_estimate(DT, 'Landed Properties')
    num_panels = int(np.floor(float(roof_area)/1.6))
else:
    # assume one panel for apartment/condo/etc
    annual_demand, ytd_demand, hours_elapsed = get_demand_estimate(DT, DWELLING)
    num_panels = 1

if num_panels > 1:
    suffix = "s"
else:
    suffix = ""
    
print(f"\nEstimated Annual Energy Consumption by an Average {DWELLING} Dwelling: {np.round(annual_demand, 0)} kWh")

annual_supply = num_panels*sum(AC_output)/1000

print(f"\nEstimated Annual Energy Generation by {num_panels} Standard 250W Solar Panel{suffix}: \
{np.round(annual_supply, 0)} kWh \
(i.e. {np.round(100*annual_supply/annual_demand, 2)}%)")

print(f"Estimated Year-to-date Energy Generation: \
{np.round(num_panels*sum(AC_output[:hours_elapsed])/1000, 2)} kWh \
(estimated to the hour)")
