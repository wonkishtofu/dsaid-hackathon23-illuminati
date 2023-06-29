import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from dotenv import find_dotenv, load_dotenv

# read local .env file and store API keys
_ = load_dotenv(find_dotenv())
PVWATTS_API_KEY  = os.environ['PVWATTS_API_KEY']

"""
3. ESTIMATED OUTPUT (PVWATTS):
Get monthly solar irradiance, DC output, AC output, weather station information
"""

def get_solar_estimate(LAT, LON, azimuth, tilt):
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
    
    assert len(response['errors']) < 1, "Oops! The database could not be accessed. Please try again later."
    
    SYSTEM_MSG = f"Estimates are based on real weather observed at Station No. {response['station_info']['location']}, located {response['station_info']['distance']} m away from queried address."
    
    print(SYSTEM_MSG)
    
    return response['outputs']['ac'], SYSTEM_MSG
