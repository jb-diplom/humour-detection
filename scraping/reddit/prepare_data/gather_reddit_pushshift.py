"""
Code framework taken from:
    https://www.osrsbox.com/blog/2019/03/18/watercooler-scraping-an-entire-subreddit-2007scape/
    For Usage:
    https://github.com/orionw/rJokesData
"""

import requests
import json
import re
import time
import datetime
import os
from dateutil.relativedelta import relativedelta

PUSHSHIFT_REDDIT_URL = "http://api.pushshift.io/reddit"

def fetchObjects(**kwargs):
    # Default paramaters for API query
    params = {
        "sort_type":"created_utc",
        "sort":"asc",
        "size":500,
        "filter": ("id", "created_utc")
        }

    # Add additional paramters based on function arguments
    for key,value in kwargs.items():
        params[key] = value

    # Print API query paramaters
    print(params)

    # Set the type variable based on function input
    # The type can be "comment" or "submission", default is "comment"
    type_post = "comment"
    if 'type' in kwargs and kwargs['type'].lower() == "submission":
        type_post = "submission"
    
    # Perform an API request
    r = requests.get(PUSHSHIFT_REDDIT_URL + "/" + type_post + "/search/", params=params, timeout=40)

    # Check the status code, if successful, process the data
    if r.status_code == 200:
        response = json.loads(r.text)
        data = response['data']
        sorted_data_by_id = sorted(data, key=lambda x: int(x['id'],36))
        return sorted_data_by_id
    
    else:
        return []

def extract_reddit_data(**kwargs):
    # Speficify the start timestamp, make sure we get everything
#    max_created_utc = int(datetime(datetime.datetime.now() - relativedelta(years=100)).timestamp())
    # num_years_back=10
    # num_days_back=50
    # num_hours_back=24
    # num_mins_back=60
    # num_secs_back=60
    # max_created_utc = int(datetime.datetime.now().timestamp())-int(num_secs_back*num_mins_back*num_hours_back*num_days_back*num_years_back)
    max_id = 0
    max_created_utc= 1559920049 #1559920049

    # Open a file for JSON output
    filename="submissions" + str(max_created_utc) +".json"
    
    file = open(os.path.join(os.path.realpath('../../../data-training/'), "dataSurreal", filename), "w")
    # file = open(os.path.join(os.path.realpath('..'), "dataShowerThoughts", filename), "w")
    # file = open(os.path.join(os.path.realpath('..'), "datasarcasm", filename), "w")

    # While loop for recursive function
    while 1:
        nothing_processed = True
        # Call the recursive function since 01.01.2000 1136070000
        print("After {}".format(max_created_utc))
        objects = fetchObjects(**kwargs,after=max_created_utc)
        
        # Loop the returned data, ordered by date
        for object in objects:
            id = int(object['id'], 36)
            if id > max_id:
                nothing_processed = False
                created_utc = object['created_utc']
                max_id = id
                if created_utc > max_created_utc: max_created_utc = created_utc
                # Output JSON data to the opened file
                print(json.dumps(object, sort_keys=True, ensure_ascii=True), file=file)
        
        # Exit if nothing happened
        if nothing_processed: 
            return
        max_created_utc -= 1

        # Sleep a little before the next recursive function call
        time.sleep(.5)

# Start program by calling function with:
# 1) Subreddit specified
# 2) The type of data required (comment or submission)
# extract_reddit_data(subreddit="jokes",type="submission")
extract_reddit_data(subreddit="sarcasm",type="submission")
# SurrealHumor
# funny
# extract_reddit_data(subreddit="SurrealHumor",type="submission")
# extract_reddit_data(subreddit="Showerthoughts",type="submission")

# extract_reddit_data(subreddit="PoliticalHumor",type="submission")
#extract_reddit_data(subreddit="satire",type="submission")  # <-- very poor quality, obviously referring to memes

# USAGE
# cd to ... \OneDrive\janice\github\rJokes\rJokesData\prepare_data
# Run python gather_reddit_pushshift.py after cd prepare_data to gather the Reddit post ids.
# Run python preprocess.py --update to update the Reddit post IDs with the full post.
# Run python preprocess.py --preprocess to preprocess the Reddit posts into final datasets

# Using different subdirs...
# python preprocess.py --update --subdir_name datasarcasm --file_name_update submissions1559920049.json --output_name_update fulldatasarcasm.json
# python preprocess.py --preprocess --subdir_name datasarcasm --file_name_preprocess fulldatasarcasm.json 

# python preprocess.py --update --subdir_name dataShowerThoughts --file_name_update submissions.json --output_name_update fulldataSHowerThoughts.json
# 571447 od these!!!
