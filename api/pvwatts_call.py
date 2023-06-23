ADDRESS = '5 Rhu Cross'

from conversions import * # import FUNCTION to convert angle to N/S/E/W bearing
from datetime import datetime
from dateutil import tz
from dotenv import load_dotenv, find_dotenv
from flask import jsonify, make_response
import json
import numpy as np
import os
import pandas as pd
import requests
import sys
import time

"""
1. GEOCODING API (TOMTOM): Get (lat, lon) coordinates from input address
"""
_ = load_dotenv(find_dotenv()) # read local .env file
TOMTOM_API_KEY = os.environ['TOMTOM_API_KEY']
OPENUV_API_KEY = os.environ['OPENUV_API_KEY']
PVWATTS_API_KEY  = os.environ['PVWATTS_API_KEY']

def formatAddress(s):
    if "Singapore" in s:
        return s.replace(" ", "+")
    else:
        return s.replace(" ", "+") + ",+Singapore"
        # need to add suffix Singapore to localize fuzzy-match search

def geocode(ADDRESS):
    response = requests.get(f"https://api.tomtom.com/search/2/geocode/{ADDRESS}.json?storeResult=false&view=Unified&key={TOMTOM_API_KEY}").json()
    
    if response['results'][0]['address']['country'] != "Singapore":
        print("Oops! The address you have queried was not found in Singapore.")
        return None, None
    
    else:
        print("The address you are querying is: {}".format(response['results'][0]['address']['freeformAddress']))
        
        LAT = response['results'][0]['position']['lat']
        LON = response['results'][0]['position']['lon']
        print(f"""This address has the following coordinates:
        Latitude: {LAT}
        Longitude: {LON}""")
        
        return LAT, LON

LAT, LON = geocode(formatAddress(ADDRESS))
DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) # UTC

"""
2. REAL-TIME SOLAR API (OPENUV): Get real time data on solar position and projected duration of sunlight today
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
    if LAT is None or LON is None:
        return None, None, None
    else:
        url = f"https://api.openuv.io/api/v1/uv?lat={LAT}&lng={LON}&alt=15&dt={DT}"
        headers = {
            'x-access-token': OPENUV_API_KEY
        }
        response = requests.get(url, headers = headers).json()

        exposure_times = {}
        for key in ['dawn', 'sunrise', 'sunriseEnd', 'solarNoon', 'sunsetStart', 'sunset', 'dusk']:
            exposure_times[key] = response['result']['sun_info']['sun_times'][key]
        
        current_time = response['result']['uv_time']
        current_azimuth = np.rad2deg(response['result']['sun_info']['sun_position']['azimuth'])+180
        current_altitude = np.rad2deg(response['result']['sun_info']['sun_position']['altitude'])
        
        print(
    f"\n The current time is: {time_readable(utc_to_sgt(current_time))} \n\
    Current Solar Bearing: {to_bearing(current_azimuth)} \n\
    Current Solar Angle: {np.round(current_altitude,2)}° \n\
    Current UV Index: {response['result']['uv']} \n\
    \n\
    Today's Projected Solar Exposure: \n\
    \t {time_readable(utc_to_sgt(exposure_times['dawn']))} -- DAWN \n\
    \t {time_readable(utc_to_sgt(exposure_times['sunrise']))} -- SUNRISE \n\
    \t {time_readable(utc_to_sgt(exposure_times['solarNoon']))} -- SOLAR NOON \n\
    \t {time_readable(utc_to_sgt(exposure_times['sunset']))} -- SUNSET \n\
    \t {time_readable(utc_to_sgt(exposure_times['dusk']))} -- DUSK \n\n"
    )
        
        return exposure_times, current_azimuth, current_altitude
    
exposure_times, azimuth, altitude = get_suninfo(LAT, LON, DT)


# FULL RANGE OF SOLAR TRAJECTORY IN SINGAPORE
#
#                           |  azimuth  |  altitude  |       day       |  time  |
# -------------------------------------------------------------------------------
# 2023-03-20T22:38:00.000Z  |    90.05  |   -0.15    | vernal equinox  |  dawn  | SW
# 2023-03-21T05:06:00.000Z  |   127.86  |    1.53    | vernal equinox  |  noon  |
# 2023-03-21T11:35:00.000Z  |   269.95  |   -0.09    | vernal equinox  |  dusk  |
# -------------------------------------------------------------------------------
# 2023-06-20T22:38:00.000Z  |    66.55  |   -0.11    | summer solstice |  dawn  | NW
# 2023-06-21T05:06:00.000Z  |     0.66  |    1.18    | summer solstice |  noon  |
# 2023-06-21T11:35:00.000Z  |   293.45  |   -0.10    | summer solstice |  dusk  |
# -------------------------------------------------------------------------------
# 2023-09-22T22:38:00.000Z  |    89.47  |   -0.09    | autumn equinox  |  dawn  | NW
# 2023-09-23T05:06:00.000Z  |   243.03  |    1.53    | autumn equinox  |  noon  |
# 2023-09-23T11:35:00.000Z  |   270.53  |   -0.16    | autumn equinox  |  dusk  |
# -------------------------------------------------------------------------------
# 2023-12-21T22:38:00.000Z  |   113.54  |   -0.11    | winter solstice |  dawn  | SW
# 2023-12-22T05:06:00.000Z  |   181.55  |    1.14    | winter solstice |  noon  |
# 2023-12-22T11:35:00.000Z  |   246.46  |   -0.14    | winter solstice |  dusk  |
#

def get_optimal_angles():
    

"""
3. ESTIMATED OUTPUT (PVWATTS): Get monthly solar irradiance (with variance?), DC output, AC output, weather station information,
"""

url = 'https://developer.nrel.gov/api/pvwatts/v6.json'

# Set the parameters for the request
parameters = {
    'api_key': PVWATTS_API_KEY,
    'system_capacity': 0.25,  # kW (standard residential size is about 250 W)
    'module_type': 0,  # 0: Standard, 1: Premium, 2: Thin film
    'losses': 15,  # % (default value)
    'array_type': 0,  # 0: Fixed open rack, 1: Fixed roof mount, 2: 1-axis tracking, 3: 1-axis backtracking, 4: 2-axis tracking
    'tilt': 15,  # degrees
    'azimuth': 180,  # degrees (since Singapore is on the equator)
    'lat': LAT,
    'lon': LON,
    'timeframe': 'hourly'
}

response = requests.get(url, params = parameters).json()

with open("pvwatts_response.json", "w") as file:
    json.dump(response, file, indent = 4)

print(f"Generated a JSON file containing solar PV output estimates. \
This estimate was based on weather observed at Station No. {response['station_info']['location']} in {response['station_info']['state']} {response['station_info']['country']}, located {response['station_info']['distance']} m away from your input address.")
