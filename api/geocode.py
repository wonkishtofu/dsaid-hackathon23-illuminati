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
TOMTOM_API_KEY = os.environ['TOMTOM_API_KEY']

"""
1. GEOCODING API (TOMTOM):
Get (lat, lon) coordinates from input address
Accept only addresses in Singapore
"""

# format input with suffix, ", Singapore" to localize fuzzy match
def formatAddress(s):
    return s.replace(" ", "+") + ",+Singapore"

# geocode address and return LAT, LON, SYSTEM_MSG
def geocode(ADDRESS):
    ADDRESS = formatAddress(ADDRESS)
    response = requests.get(f"https://api.tomtom.com/search/2/geocode/{ADDRESS}.json?storeResult=false&view=Unified&key={TOMTOM_API_KEY}").json()
    
    # address outside Singapore causes AssertionError
    assert response['results'][0]['address']['country'] == "Singapore", "Oops! The address you have queried was not found in Singapore."
    
    LAT = response['results'][0]['position']['lat']
    LON = response['results'][0]['position']['lon']
    
    # address that is too general will just query "Singapore"
    if response['results'][0]['address']['freeformAddress'] == "Singapore":
        SYSTEM_MSG = "The address you are querying is too general. Providing an island-averaged estimate instead."
        print(SYSTEM_MSG)
        
    else:
        SYSTEM_MSG = "The address you are querying is: {}.".format(response['results'][0]['address']['freeformAddress'])
        print(SYSTEM_MSG)
        print(f"""This address has the following coordinates:
    Latitude: {LAT}
    Longitude: {LON}""")
    
    return LAT, LON, SYSTEM_MSG
