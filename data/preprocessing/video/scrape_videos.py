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
import pandas as pd
import random
from time import sleep

input_file = 'videos.csv' # file with YouTube video URLs
URLs = pd.read_csv(input_file)['URL']

from collections import defaultdict
import lxml
from lxml import etree
import urllib
from urllib.parse import urlparse
from urllib.parse import parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

transcript_dict = {}

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
        
    youtube = etree.HTML(urllib.request.urlopen(url).read())
    title = youtube.xpath("//title")[0].text
    
    print(title)
    print("\n")
    print(parse_text)
    print("\n\n")
    
    transcript_dict[title] = parse_text

with open("transcript.json", "w") as file:
    json.dump(transcript_dict, file, indent = 4)
# improvements:
# 1. scrape metadata, e.g. author, views, likes, tags, comments
# 2. use manually created transcript over auto-generated version
# 3. unstructured language processing, e.g. https://realpython.com/natural-language-processing-spacy-python/
