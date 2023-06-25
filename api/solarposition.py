from conversions import * # import FUNCTION to convert angle to N/S/E/W bearing
from datetime import datetime, timedelta
from dateutil import tz
from dotenv import load_dotenv, find_dotenv
import json
import numpy as np
import os
import pandas as pd
import requests
import sys
import time

# read local .env file and store API keys
_ = load_dotenv(find_dotenv())
OPENUV_API_KEY = os.environ['OPENUV_API_KEY']

# query solar position on notable dates: perihelion, 2 x solstice, 2 x equinox
notable_dates = ['2023-01-03', '2023-03-21', '2023-06-21', '2023-09-22', '2023-12-22']

"""
2. SUN POSITION API (OPENUV):
Get position of the sun at notable dates and times in the year to compute optimal tilt of solar panel for energy generation
"""

def utc_to_sgt(utc):
    from_zone = tz.tzutc()
    to_zone = tz.gettz('Asia/Singapore')
    utc = utc[:-5].replace("T", " ")
    utc = datetime.strptime(utc, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo = from_zone)
    return utc.astimezone(to_zone)
    
def time_readable(sgt):
    HHMM = datetime.strftime(sgt, '%H:%M')
    return HHMM + " SGT"

def get_suninfo(LAT, LON, DT):
    url = f"https://api.openuv.io/api/v1/uv?lat={LAT}&lng={LON}&alt=15&dt={DT}"
    headers = {'x-access-token': OPENUV_API_KEY}
    response = requests.get(url, headers = headers).json()
    
    # get key times of solar exposure today and print data
    exposure_times = {}
    for key in ['dawn', 'sunrise', 'solarNoon', 'sunset', 'dusk']:
        exposure_times[key] = response['result']['sun_info']['sun_times'][key]
    
    current_time = response['result']['uv_time']
    current_azimuth = np.rad2deg(response['result']['sun_info']['sun_position']['azimuth'])+180
    current_altitude = np.rad2deg(response['result']['sun_info']['sun_position']['altitude'])
    
    print(f"\nThe current time is: {time_readable(utc_to_sgt(current_time))} \n\
Current Solar Bearing: {to_bearing(current_azimuth)} \n\
Current Solar Angle: {np.round(current_altitude,2)}° \n\
\n\
Today's Projected Solar Exposure: \n\
\t {time_readable(utc_to_sgt(exposure_times['dawn']))} -- DAWN \n\
\t {time_readable(utc_to_sgt(exposure_times['sunrise']))} -- SUNRISE \n\
\t {time_readable(utc_to_sgt(exposure_times['solarNoon']))} -- SOLAR NOON \n\
\t {time_readable(utc_to_sgt(exposure_times['sunset']))} -- SUNSET \n\
\t {time_readable(utc_to_sgt(exposure_times['dusk']))} -- DUSK \n\n\
Computing optimal tilt of solar panel ..."
)
    
    # get key solar position on notable dates and high demand times (-1.5 to +5 hours from solar noon)
    azimuth_angles = []
    altitude_angles = []
    
    for date in notable_dates:
        for delta in [4.75, 5.75, 6.75]:
            time = exposure_times['solarNoon'][exposure_times['solarNoon'].find("T")+1:-1]
            time = datetime.strptime(time, "%H:%M:%S.%f")
            time += timedelta(hours = delta)
            
            time = datetime.strftime(time, "T%H:%M:%SZ")
            query = date + time
            
            url = f"https://api.openuv.io/api/v1/uv?lat={LAT}&lng={LON}&alt=15&dt={query}"
            response = requests.get(url, headers = headers).json()
            
            azimuth_angles.append(np.rad2deg(response['result']['sun_info']['sun_position']['azimuth']) + 180)
            altitude_angles.append(np.rad2deg(response['result']['sun_info']['sun_position']['altitude']))

    optimal_azimuth = np.mean(azimuth_angles)
    optimal_altitude = np.mean(altitude_angles)
    
    return optimal_azimuth, optimal_altitude
