"""
HOW TO USE

dependency: ../raw/demand/*.xls (demand data compiled over the last 365 days, downloaded from EMA's website)
Generates a 30-minutely energy demand estimate using a given day in the last year
Computes upper and lower bounds based on the 30-minutely range across all days in the last year
"""

import csv
from os import listdir
from os.path import isfile, join
import pandas as pd
import random
import xrld

# navigate to directory with demand data
current_path = os.getcwd()
raw_path = os.chdir('../data/raw/demand')

allfiles = [f for f in listdir(raw_path) if isfile(f)]
print(allfiles)

"""
def get_demand_estimate(date):
    for file in allfiles:
        mindate = file[]
    
    df_sheet_index = pd.read_excel('sample.xlsx', sheet_name=1)

print(df_sheet_index)

df = pd.read_excel('sample.xlsx')

# change working directory to save GPT outputs
processed_path = os.chdir('../processed/')
"""
