from datetime import datetime, timedelta
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
PVWATTS_API_KEY  = os.environ['PVWATTS_API_KEY']

"""
3. ESTIMATED OUTPUT (PVWATTS):
Get monthly solar irradiance, DC output, AC output, weather station information
"""

def get_solar_estimate(LAT, LON, ADDRESS, azimuth, tilt):
    url = 'https://developer.nrel.gov/api/pvwatts/v6.json'

    # Set the parameters for the request
    parameters = {
        'api_key': PVWATTS_API_KEY,
        'system_capacity': 0.25,  # kW (standard residential size is about 250 W)
        'module_type': 0,  # 0: Standard, 1: Premium, 2: Thin film
        'losses': 15,  # % (default value)
        'array_type': 0,  # 0: Fixed open rack, 1: Fixed roof mount, 2: 1-axis tracking, 3: 1-axis backtracking, 4: 2-axis tracking
        'tilt': tilt,  # degrees
        'azimuth': azimuth,  # degrees
        'lat': LAT,
        'lon': LON,
        'timeframe': 'hourly'
    }

    response = requests.get(url, params = parameters).json()
    
    # create directory to store data (or if it already exists, enter directory)
    path = "queries"
    exists = os.path.exists(path)
    if not exists:
        os.makedirs(path)
    os.chdir(path)
    
    with open(ADDRESS + ".json", "w") as file:
        json.dump(response, file, indent = 4)
                
    print(f"Generated a JSON file containing solar PV output estimates. \n \
Estimates are based on real weather observed at Station No. {response['station_info']['location']}, located {response['station_info']['distance']} m away from your input address.")
    
    return response['outputs']['ac']
