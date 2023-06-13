"""
HOW TO USE

dependency: websites.csv, /../requirements.txt
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

def get_content(soup):
    results = soup.find(id = "internal")
    elements = results.find_all("div", class_="internal-content")
    
    parse_text = ""
    for element in elements:
        parse_text += element.get_text()
        
    return parse_text, elements
    
transcript_dict = {}
for url in URLs:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    
    content, elements = get_content(soup)

    title = elements[0].text.strip()

    transcript_dict[title] = content
    
    print(title)
    print("\n")
    print(content)
    print("\n\n")

with open("ema_website_transcript.json", "w") as file:
    json.dump(transcript_dict, file, indent = 4)
# improvements:
# 1. scrape in smaller chunks with title, subheader context tags
# 2. include embedded URLs in scrape
# 3. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
