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

ADDRESS = '5 Rhu Cross'

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
        return None
    
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
    
def sgt_friendly(sgt):
    HHMM = datetime.strftime(sgt, '%H:%M')
    return HHMM + " SGT"
    
def get_suninfo(LAT, LON, DT):
    if LAT is None or LON is None:
        return None
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
    f"\n The current time is: {sgt_friendly(utc_to_sgt(current_time))} \n\
    Current Solar Bearing: {to_bearing(current_azimuth)} \n\
    Current Solar Angle: {np.round(current_altitude,2)}° \n\
    Current UV Index: {response['result']['uv']} \n\
    \n\
    Today's Projected Solar Exposure: \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['dawn']))} -- DAWN \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['sunrise']))} -- SUNRISE \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['sunriseEnd']))} -- SUN FULLY RISEN \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['solarNoon']))} -- SOLAR NOON \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['sunsetStart']))} -- SUN STARTS TO SET \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['sunset']))} -- SUNSET \n\
    \t {sgt_friendly(utc_to_sgt(exposure_times['dusk']))} -- DUSK \n\n"
    )
        
        return exposure_times, current_azimuth, current_altitude
    
exposure_times, azimuth, altitude = get_suninfo(LAT, LON, DT)

def get_trajectory(LAT, LON, exposure_times):
    azimuth_times, altitude_times, UVI_times = {}, {}, {}
    for key in exposure_times.keys():
        url = f"https://api.openuv.io/api/v1/uv?lat={LAT}&lng={LON}&alt=15&dt={exposure_times[key]}"
        headers = {
            'x-access-token': OPENUV_API_KEY
        }
        response = requests.get(url, headers = headers).json()
        azimuth_times[key] = np.rad2deg(response['result']['sun_info']['sun_position']['azimuth'])+180
        altitude_times[key] = np.rad2deg(response['result']['sun_info']['sun_position']['altitude'])
        UVI_times[key] = response['result']['uv']
    
    data_df = pd.DataFrame(index = ['Azimuth Angle', 'Altitude Angle', 'UV Index'], data = [azimuth_times, altitude_times, UVI_times])
    print(data_df.T)
    return data_df.T
    
data_df = get_trajectory(LAT, LON, exposure_times)

"""
3. ESTIMATED OUTPUT (PVWATTS): Get monthly solar irradiance (with variance?), DC output, AC output, weather station information,
"""

url = 'https://developer.nrel.gov/api/pvwatts/v6.json'

optimal_tilt = data_df['Altitude Angle']['solarNoon']

# Set the parameters for the request
parameters = {
    'api_key': PVWATTS_API_KEY,
    'system_capacity': 0.25,  # kW (standard residential size is about 250 W)
    'module_type': 0,  # 0: Standard, 1: Premium, 2: Thin film
    'losses': 15,  # % (default value)
    'array_type': 0,  # 0: Fixed open rack, 1: Fixed roof mount, 2: 1-axis tracking, 3: 1-axis backtracking, 4: 2-axis tracking
    'tilt': optimal_tilt,  # degrees
    'azimuth': 180,  # degrees (since Singapore is on the equator)
    'lat': LAT,
    'lon': LON,
    'timeframe': 'hourly',
}

response = requests.get(url, params = parameters).json()
print(response)

print(f"This estimate was based on weather observed at Station No. {response['station_info']['location']} in {response['station_info']['state']} {response['station_info']['country']}, located {response['station_info']['distance']} m away from your input address.")
