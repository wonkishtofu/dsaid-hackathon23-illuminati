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
    article = soup.select('<div class="internal-content">')
    return article[0].get_text().strip()

transcript_dict = {}
for url in URLs:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    
    content = get_article_title(soup)

    title = content.find("h1", class_="banner-header").text.strip()

    transcript_dict[title] = content
    
    print(title)
    print("\n")
    print(content)
    print("\n\n")
    
with open("transcript.json", "w") as file:
    json.dump(transcript_dict, file, indent = 4)
# improvements:
# 1. scrape in smaller chunks with title, subheader context tags
# 2. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
