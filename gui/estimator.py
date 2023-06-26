# import scripts to enable API linking
import sys
sys.path.insert(1, '../api/')
from conversions import to_bearing
from geocode import geocode
from solarposition import get_suninfo, get_optimal_angles
from pvwatts import get_solar_estimate
from demand import get_demand_estimate

import calendar
from datetime import datetime
import numpy as np
from nicegui import Client, app, ui
import os
import pandas as pd
import time

def update_field(field, value):
    user_info[f'{field}'] = value

def update_details():
    if user_info['Address'] is not None or user_info['Address'] != '':
        try:
            user.Address = user_info['Address']
            user.LAT, user.LON = geocode(user.Address)
            ui.notify('The estimate was generated!')
        except Exception as e:
            ui.notify(f'{e}')
