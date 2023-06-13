"""
HOW TO USE

dependency: requirements.txt, all files in ../raw/


"""

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

transcipts = pd.read_json("../website/EMA/MTI_speeches_PQs_scraped.csv")

# Exponential backoff decorator
@retry(wait = wait_random_exponential(min = 10, max = 80), stop = stop_after_attempt(10))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

# Helper function to get returns from gpt
def get_message_completion(messages,
                     model = "gpt-3.5-turbo",
                     temperature = 0,
                     max_tokens = 500,
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

for ii, speech in enumerate(speeches['Content']):
    
    try:
        # Set messages for chatgpt
        messages =  [
        {'role':'system',
         'content':f"""Please refer to the speech provided: {speeches['Content'][ii].strip()}"""},
        {'role':'user',
         'content':f"""Summarise the most relevant lines related to solar energy or solar panels. \
         Make sure to retain key statistics or figures."""},
        ]
        
        # Obtain gpt response
        response = get_message_completion(messages, max_tokens = 500)
        
        # Save to dictionary
        extracts[speeches['Title'][ii]] = response
    except Exception as e:
        print(f"'{speeches['Title'][ii]}' was not summarised. Error message: {e}'")
    # time.sleep(20)

len(extracts)

extracts_df = pd.DataFrame(
    [(k, val) for k, val in extracts.items()],
    columns = ['Title', 'Summary']
)

extracts_df.to_csv("MTI_speeches_PQs_summaries_sample.csv")

