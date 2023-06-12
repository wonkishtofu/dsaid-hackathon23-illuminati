"""
HOW TO USE

dependency: websites.csv, requirements.txt
Add the links to websites of interest in websites.csv
Run this script to extract website content
Feed the transcript to ChatGPT and ask it to generate a table of Q&A pairs

output: transcript.json
"""

import csv
import json
import os.path
import pandas as pd
import random
from time import sleep

input_file = 'websites.csv' # file with website URLs
URLs = pd.read_csv(input_file)['URL']

from urllib.request import urlopen

for url in URLs:
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    
    # extract title
    start_index = html.find("<title>") + len("<title>")
    end_index = end_index = html.find("</title>")
    title = html[start_index:end_index]
    
    print("\n\n\n")
    print(title)
    
    print(html)
