from dotenv import load_dotenv, find_dotenv
import os
import pandas as pd
import requests
import sys

from IPython.display import display


# Define the lat, long of the location and the year
lat, lon, year = 33.2164, -97.1292, 2020
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

print(info)

# Return all but first 2 lines of csv to get data:
df = pd.read_csv('https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key, attr=attributes), skiprows=2)

# Set the time index in the pandas dataframe:
df = df.set_index(pd.date_range('1/1/{yr}'.format(yr=year), freq=interval+'Min', periods=525600/int(interval)))

# take a look
print('shape:', df.shape)
print(df.head())

print(df.columns.values)

