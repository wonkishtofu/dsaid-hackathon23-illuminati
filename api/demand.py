# load functions from other scripts
import calendar
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd

# read demand data
if '/gui' in os.getcwd():
    os.chdir("../api")
df = pd.read_excel("demand/SES_Public_2022_tidy.xlsx", sheet_name = "T3.5")

def get_demand_estimate(DT, DWELLING):
    # 2021 is the latest compelete year, filter by dwelling type
    demand = df[(df.year == 2021) & (df.dwelling_type == DWELLING)]
    
    # get current month & year
    date = datetime.strptime(DT[:DT.find("T")], "%Y-%m-%d")
    time = datetime.strptime(DT[DT.find("T")+1:-1], "%H:%M:%S")
    month = date.month
    year = date.year
    hours = time.hour

    # compute year to date demand and days elapsed
    ytd = 0
    days_elapsed = 0
    for mm in range(1, month+1):
        ytd += demand[(demand.month == mm) & (demand.Region == 'Overall') & (demand.Description == 'Overall')].iloc[0]['kwh_per_acc']
        days_elapsed += calendar.monthrange(year, month)[1]
    
    annual = 12*demand[(demand.month == 'Annual') & (demand.Region == 'Overall') & (demand.Description == 'Overall')]['kwh_per_acc'].iloc[0]
    
    hours_elapsed = (days_elapsed-1)*24 + hours
    return annual, ytd, hours_elapsed
