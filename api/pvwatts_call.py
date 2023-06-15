from dotenv import load_dotenv, find_dotenv
from flask import jsonify, make_response
import json
import os
import pandas as pd
import requests
import sys
import time

"""
WORKFLOW:

1. GEOCODING API (TOMTOM): Get (lat, lon) coordinates from input address

2. REAL-TIME WEATHER & SOLAR API (OPENUV): Get real time solar data on


"""
_ = load_dotenv(find_dotenv()) # read local .env file
TOMTOM_API_KEY = os.environ['TOMTOM_API_KEY']
OPENUV_API_KEY = os.environ['OPENUV_API_KEY']
NSRDV_API_KEY  = os.environ['NSRDB_API_KEY']

ADDRESS = '12 Cove Grove'

def formatAddress(s):
    if "Singapore" in s:
        return s.replace(" ", "+")
    else:
        return s.replace(" ", "+") + ",+Singapore"

def geocode(ADDRESS):
    response = requests.get(f"https://api.tomtom.com/search/2/geocode/{ADDRESS}.json?storeResult=false&view=Unified&key={TOMTOM_API_KEY}").json()
    
    print("The address you are querying is: {}".format(response['results'][0]['address']['freeformAddress']))
    
    LAT = response['results'][0]['position']['lat']
    LON = response['results'][0]['position']['lon']
    print(f"""This address has the following coordinates:
    latitude: {LAT}
    longitude: {LON}""")
    
    return LAT, LON

LAT, LON = geocode(formatAddress(ADDRESS))
DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
print(DT)
"""
response = requests.get(f"https://api.openuv.io/api/v1/uv?lat={LAT}&lng={LON}&alt={0}&dt={DT}", headers = {'Authorization': f'access_token {OPENUV_API_KEY}'})

print(response)
"""


response = requests.get(f"https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({LON}+{LAT})&api_key={NSRDV_API_KEY}")

print(response)
# Define the lat, long of the location and the year
year = 33.2164, -97.1292, 2020
_ = load_dotenv(find_dotenv()) # read local .env file
api_key  = os.environ['NSRDB_API_KEY']
attributes = 'ghi,dhi,dni,wind_speed,air_temperature,solar_zenith_angle'
leap_year = 'false'
interval = '30'
utc = 'false'
your_name = 'Arushi+Sinha'
reason_for_use = 'alpha+testing'
your_affiliation = 'gov.sg'
your_email = 'arushi@dsaid.gov.sg'
mailing_list = 'false'

# Declare url string
url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key, attr=attributes)
# Return just the first 2 lines to get metadata:
info = pd.read_csv(url, nrows = 1)
# See metadata for specified properties, e.g., timezone and elevation
timezone, elevation = info['Local Time Zone'], info['Elevation']

print(info.T)

# Return all but first 2 lines of csv to get data:
df = pd.read_csv('https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key, attr=attributes), skiprows=2)

# Set the time index in the pandas dataframe:
df = df.set_index(pd.date_range('1/1/{yr}'.format(yr=year), freq=interval+'Min', periods=525600/int(interval)))

# take a look
print('shape:', df.shape)
print(df.head())

print(df.columns.values)

