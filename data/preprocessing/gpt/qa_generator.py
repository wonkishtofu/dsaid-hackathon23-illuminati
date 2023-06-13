"""
HOW TO USE

dependency: requirements.txt, all scraped raw data files in ../../raw/

"""

import csv
from dotenv import load_dotenv, find_dotenv
import json
import openai
import os
import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff (to overcome rate limit)
import time

_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key  = os.environ['OPENAI_API_KEY']

current_path = os.getcwd()
raw_path = os.chdir('../../raw/')

raw_data = {}
for filename in os.listdir(raw_path):
    name, file_extension = os.path.splitext(filename)
    # read CSV raw data files
    if '.csv' in file_extension:
        input_df = pd.read_csv(name + file_extension)
        
        # extract (title, content) pair and save in raw_data
        for ii, title in enumerate(input_df['Title']):
            raw_data[title] = input_df['Content'][ii]
            
        print("Successfully read file: {}".format(name + file_extension))
        
    # read JSON raw data files
    elif '.json' in file_extension:
        with open(name + file_extension, 'r') as f:
            data = json.load(f)
        
        # extract (key, value) pair and save in raw_data
        for key, value in data.items():
            raw_data[key] = value
            
        print("Successfully read file: {}".format(name + file_extension))
    else:
        print("Did not read file: {}".format(name + file_extension))
        
# Exponential backoff decorator
@retry(wait = wait_random_exponential(min = 10, max = 80), stop = stop_after_attempt(10))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

# Helper function to get returns from gpt
def get_message_completion(messages,
                     model = "gpt-3.5-turbo",
                     temperature = 0,
                     max_tokens = 1000,
                     num_pairings = 100
                    ):

    response = completion_with_backoff(
        model = model,
        messages = messages,
        temperature = temperature, # this is the degree of randomness of the model's output
        max_tokens = max_tokens, # the maximum number of tokens the model can ouptut
    )
    return response.choices[0].message.content

extracts = {}

for title, content in raw_data.items():
    
    try:
        # Set messages for chatgpt
        messages =  [
        {'role':'system',
         'content':f"""Please refer to the content provided: {content.strip()}"""},
        {'role':'user',
         'content':f"""Summarise the most relevant lines related to solar energy or solar panels. \
         Make sure to retain key statistics or figures."""},
        ]
        
        # Obtain gpt response
        response = get_message_completion(messages, max_tokens = 500)
        
        # Save to dictionary
        extracts[title] = response
        
    except Exception as e:
        print(f"'{title}' was not summarised. Error message: {e}'")
    
    # time.sleep(20)

print(len(extracts))

extracts_df = pd.DataFrame(
    [(k, val) for k, val in extracts.items()],
    columns = ['Title', 'Summary']
)

extracts_df.to_csv("raw_data_summaries_sample.csv")

qna = {}
num_qna = 25 # Set number of Q&As

for t, s in extracts.items():
    
    try:
        # Set messages for ChatGPT
        messages =  [
        {'role':'system',
         'content':f"""Please refer to the content provided: {s.strip()}"""},
        {'role':'user',
         'content':f"""# Create a JSON of {num_qna} pairs of questions and answers based on this summary. \
         The key value pairs should be the question and answer."""},
        ]
        
        # Obtain gpt response
        response = get_message_completion(messages, max_tokens = 1000)
        
        # Convert response to JSON and then dictionary
        qna_dict = dict(json.loads(response))
        
        # Create list of tuples based on q&a pairings and save to dictionary
        qna[t] = [(qna_dict[k]['question'], qna_dict[k]['answer']) for k in qna_dict.keys()]
        
    except Exception as e:
        print(f"Did not generate Q&As for'{t}'. Error message: {e}'")
    
    # time.sleep(20)
    
print(len(qna))

# Create df and save to csv
qna_df = pd.DataFrame(qna)
qna_melt = pd.melt(qna_df, value_vars = [k for k in qna.keys()], var_name = "Title")
qna_melt['Questions'], qna_melt['answers'] = zip(*qna_melt['value'])
qna_melt = qna_melt.drop('value', axis = 1)

qna_melt.to_csv("raw_data_qna_sample.csv")
