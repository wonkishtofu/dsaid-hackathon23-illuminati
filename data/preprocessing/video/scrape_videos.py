"""
HOW TO USE

dependency: videos.csv, requirements.txt
Add the links to videos of interest in videos.csv
Run this script to extract video title and the transcript
Feed the transcript to ChatGPT and ask it to generate a table of Q&A pairs

output: transcript.json
"""

import csv
import json
import os.path
import random
import urllib
from collections import defaultdict
from time import sleep
from urllib.parse import parse_qs, urlparse

import lxml
import pandas as pd
from lxml import etree

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

input_file = 'videos.csv' # file with YouTube video URLs
URLs = pd.read_csv(input_file)['URL']


save_df = pd.DataFrame(columns = ['URL', 'Title', 'Content'])

for ii, url in enumerate(URLs):
    url_data = urlparse(url)
    query = parse_qs(url_data.query)
    video_id = query['v'][0]
    
    # finds a transcript in English from the list of available transcripts
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = transcript_list.find_transcript(['en'])
    text = transcript.fetch()
    
    # parses all text from transcript into single chunk of text
    parse_text = ""
    for d in text:
        for value in d['text']:
            parse_text += str(value)
        parse_text += " "
    parse_text = str(parse_text.encode('ascii', errors = 'ignore'))
    
    youtube = etree.HTML(urllib.request.urlopen(url).read())
    title = youtube.xpath("//title")[0].text
    title = str(title.encode('ascii', errors = 'ignore'))
    
    print(title)
    print("\n")
    print(parse_text)
    print("\n\n")
    
    data_df = pd.DataFrame([[url, title, parse_text]], columns = ['URL', 'Title', 'Content'])
    save_df = pd.concat([save_df, data_df])

with open("video_transcript.csv", "w") as file:
    save_df.to_csv(file, index = False)

# improvements:
# 1. scrape metadata, e.g. author, views, likes, tags, comments
# 2. use manually created transcript over auto-generated version
# 3. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
