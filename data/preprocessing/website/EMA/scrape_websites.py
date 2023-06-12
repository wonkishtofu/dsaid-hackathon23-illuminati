"""
HOW TO USE

dependency: websites.csv, requirements.txt
Add the links to websites of interest in websites.csv
Run this script to extract website content
Feed the transcript to ChatGPT and ask it to generate a table of Q&A pairs

output: transcript.json
"""

from bs4 import BeautifulSoup
import csv
import json
import os.path
import pandas as pd
import random
import requests
from time import sleep

input_file = 'websites.csv' # file with website URLs
URLs = pd.read_csv(input_file)['URL']

transcript_dict = {}
for url in URLs:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
        
    # <div class="internal-content">
    results = soup.find(id = "internal")
    elements = results.find_all("div", class_="internal-content")

    parse_text = ""
    for element in elements:
        title = element.find("h1", class_="banner-header").text.strip()
        parse_text += element.text.strip() + " "

    transcript_dict[title] = parse_text
    
    print(title)
    print("\n")
    print(parse_text)
    print("\n\n")
    
with open("transcript.json", "w") as file:
    json.dump(transcript_dict, file, indent = 4)
# improvements:
# 1. scrape in smaller chunks with title, subheader context tags
# 2. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
