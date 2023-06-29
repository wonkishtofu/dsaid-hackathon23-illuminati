"""
HOW TO USE

dependency: websites.csv, /../requirements.txt
Add the links to websites of interest in websites.csv
Run this script to extract website content
Feed the transcript to ChatGPT and ask it to generate a table of Q&A pairs

output: transcript.json
"""

import csv
import json
import os.path
import random
from time import sleep

import pandas as pd
import requests

from bs4 import BeautifulSoup

input_file = 'websites.csv' # file with website URLs
URLs = pd.read_csv(input_file)['URL']

def get_content(soup):
    results = soup.find(class_ = "ogp-askgov-question-list")
    while len(results) > 0:
        pair = results.find("article", class_ = "card ogp-askgov-question-card")
        print(pair)
        print("\n")
        if pair in results:
            results.replace(pair,'')
    print(results)
    questions = elements.find_all("h1")
    parse_text = ""
    for qq in questions:
        parse_text += questions.get_text(strip = True)
    
    parse_text = str(parse_text.encode('ascii', errors = 'ignore'))
    return parse_text
    
save_df = pd.DataFrame(columns = ['URL', 'Title', 'Content'])

for url in URLs:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    
    content = get_content(soup)
    
    print("AskGov, EMA: ")
    print("\n")
    print(content)
    print("\n\n")
    
    data_df = pd.DataFrame([[url, "AskGov, EMA: " + title, content]], columns = ['URL', 'Title', 'Content'])
    save_df = pd.concat([save_df, data_df])
    
with open("askgov_ema_transcript.csv", "w") as file:
    save_df.to_csv(file, index = False)

# improvements:
# 1. scrape in smaller chunks with title, subheader context tags
# 2. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
