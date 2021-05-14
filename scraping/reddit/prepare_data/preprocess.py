import re
import requests
import json
import praw
import datetime
import os
from multiprocessing import Pool
import time
import csv

import argparse
import numpy as np
import pandas as pd
import random
import nltk
from sklearn.model_selection import train_test_split
import seaborn as sns
import matplotlib.pyplot as plt

# app registered here: https://www.reddit.com/prefs/apps
reddit = praw.Reddit(client_id='-BplwOVm5bmrIg',
                     client_secret='17QDThZomWC-iEVk1OjkF8Ql1peO2g',
                     user_agent="humour research")

random.seed(42)
np.random.seed(42)

def processExistingPost(doc):
    """ A helper function to gather data from the Reddit API based on post ID """
    # create a post object
    post = reddit.submission(doc['id'])
    # fetch the updated post from reddit
    post._fetch()
    return post


def read_and_update_ids(file_name: str = "submissions.json", output_name: str = "fullrjokes.json"):
    """
    Gathers the data in the data/{file_name} file and grabs the fields we want to keep, along with the updated
    upvote count and stores them in data/{output_name}.

    If you want to include other meta-data from the reddit API, you can add it to `KEEP_KEYS` list

    Args:
        file_name: the name of the file in the `data` folder that contains the Reddit post IDs
        output_name: the name of the file to output the gathered posts to, in the `data` folder
    """
    print("Reading and update jokes for each id...")
    # PYDEVD_WARN_EVALUATION_TIMEOUT = 10
    KEEP_KEYS = ["id", "selftext", "title", "downs", "ups", "score", "name", "created_utc"]
    # KEEP_KEYS = ["selftext","ups", "score"]
    with open(os.path.join(os.path.realpath('..'), args.subdir_name, file_name), "r") as f:
        for line in f:
            line = json.loads(line)
            for retry in range(3):
                try:
                    # print (line)
                    updated_doc = processExistingPost(line)
                except Exception as e:
                    print("On retry number", retry)
                    time.sleep(5)
                    continue
                break
            consalidated_dict = {your_key: updated_doc.__dict__[your_key] for your_key in KEEP_KEYS}
            with open(os.path.join(os.path.realpath('..'), args.subdir_name, output_name), "a") as fout:
                fout.write(json.dumps(consalidated_dict, default=str) + "\n")
                print("wrote out id={}".format(updated_doc))


def phrase_in_doc(phrase, updated_doc):
    """ A helper function to see if the phrase is in the document body (title) or punchline (selftext) """
    return phrase in updated_doc["title"] or phrase in updated_doc["selftext"]

def get1toNscore(old_scores, upper_bounds, n=5):
#   recalculate scores into 1,2,.., n
    new_scores = []
    for i, val in enumerate(old_scores) :
        score = 1
        while (val >= upper_bounds[score-1] and score !=n):
            score += 1
        new_scores.append(score)
    return new_scores

def read_filter_and_preprocess(file_name: str = "fullrjokes.json", output_name: str = "preprocessed.csv"):
    """
    Gathers the data in the data/{file_name} file, preprocesses it to exclude deleted/pic/video/removed/empty
    posts and stores them in data/{output_name}.

    It also creates the split for the log-upvote regression problem and stores them in `data/{train|dev|test}.tsv`

    Args:
        file_name: the name of the file in the `data` folder that contains the Reddit posts
        output_name: the name of the file to output the gathered preprocessed files to
    """
    START_OF_2020 = 1577836801 # GMT time, 1/1/2020
    list_of_jokes = []
    skipped_deleted = 0
    skipped_removed = 0
    skipped_format = 0
    TEXT_COLS = ["body", "punchline", "joke"]
    print("Reading and preprocessing all jokes")
    with open(os.path.join(os.path.realpath('..'), args.subdir_name, file_name), "r") as f:
        for index, line in enumerate(f):
            # print("Nest Line is:", line)
            updated_doc = json.loads(line)
            if (updated_doc["title"] == "" and updated_doc["selftext"] == "") or len(updated_doc["title"])+len(updated_doc["selftext"]) <40:
            # if (updated_doc["title"] == "" and updated_doc["selftext"] == ""):
                skipped_format += 1
                continue
            if phrase_in_doc("[deleted]", updated_doc):
                skipped_deleted += 1
                continue
            if phrase_in_doc("[removed]", updated_doc):
                skipped_removed += 1
                continue
            if pd.isnull(updated_doc["score"]) or type(updated_doc["score"]) == str and updated_doc["score"] == "":
                skipped_format += 1
                continue
            if phrase_in_doc("[pic]", updated_doc) or phrase_in_doc("VIDEO", updated_doc):
                skipped_format += 1
                continue

            joke = updated_doc["title"] + " " + updated_doc["selftext"]
            if int(updated_doc["score"]) > 10 :
                list_of_jokes.append({"joke": joke, "body": updated_doc["selftext"], 
                                    "punchline": updated_doc["title"], "score": updated_doc["score"], "date": updated_doc["created_utc"]})
                        
    df = pd.DataFrame(list_of_jokes)

    # get rid of newlines
    df["joke"] = df["joke"].replace(r'\n',' ',regex=True)
    df["joke"] = df["joke"].replace(r'\t',' ',regex=True)
    df["joke"] = df["joke"].replace(r'\r',' ',regex=True)
    assert df["joke"].isnull().any() == False, "there were NaNs in the joke columns, ERROR"
    assert df["score"].isnull().any() == False, "there were NaNs in the score columns, ERROR"
    df = df.dropna()  # drop all jokes that have something funny
    print("Writing df with shape", df.shape, "to file path", os.path.join(os.path.realpath('..'), args.subdir_name, output_name))
    print("SKIPPED: {} were removed, {} deleted, {} format".format(skipped_removed, skipped_deleted, skipped_format))
    df.to_csv(os.path.join(os.path.realpath('..'), args.subdir_name, output_name), index=None, encoding="UTF-8")

    sortedscores=np.sort(df["score"])
    chunk_lst=np.array_split(sortedscores,args.num_degrees)
    # get first and last score of each sub array
    upper_bounds=[]
    for chunk in chunk_lst:
        upper_bounds.append(max(chunk))
    # upper_bounds=[max(chunk_lst[0]),max(chunk_lst[1]), max(chunk_lst[2]), max(chunk_lst[3]), max(chunk_lst[4])]

    df["score"] = get1toNscore(df["score"],upper_bounds,n=args.num_degrees) # set values according to overall hierarchical position
    # df["score"] = np.log(df["score"]) / 2  # use a log scale, make 0's 0 still
    df = df.replace([np.inf, -np.inf], np.nan)
    df["score"] = df["score"].fillna(0).astype(int)
    print("Values are between\n", df["score"].value_counts())
    print("For log prediction task, {} unique jokes\n".format(df.shape))
    df = df[["score", "joke"]]

    file_in='../../../TwitterScraper/snscrape/python-wrapper/serious_tweets.tsv'
    serious = pd.read_csv(file_in, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\', header=None, names=['score', 'joke'], encoding="UTF-8")
    serious = serious.replace([np.inf, -np.inf], np.nan)
    serious = serious.dropna()

    assert serious["joke"].isnull().any() == False, "there were NaNs in the joke columns, ERROR"
    # print ("Testing for 0's")
    # for i, val in enumerate(serious["score"]):
    #     if val !=0 : print (i)
    assert serious["score"].isin([0]).all() == True, "all scores have to be 0"

    # add on proportional number of serious texts before shuffling (same number of serious texts as in each level of the funnies)
    # df =pd.concat([df, serious[:min(int(len(df)/args.num_degrees),len(serious))]], join="inner") 
    df =pd.concat([df, serious[:min(int(len(df)),len(serious))]], join="inner") 
    df['joke']=df['joke'].str.lower()
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    # uncomment following to have as many serious texts as all the funnies put together
    # df =pd.concat([df, serious[:min(len(df),len(serious))]], join="inner") 
    
    train, dev = train_test_split(df, test_size=0.1, random_state=42)
    dev, test = train_test_split(dev, test_size=0.5, random_state=42)
    print("writing train, dev, and test with shapes", train.shape, dev.shape, test.shape)
    suffix="_Oto" + str(args.num_degrees)
    train.to_csv(os.path.join("..", args.subdir_name, "train"+suffix+".tsv"), sep="\t", quoting=csv.QUOTE_NONE, escapechar='\\', index=None, header=['sentence','label'], encoding="UTF-8")
    dev.to_csv(os.path.join("..", args.subdir_name, "dev"+suffix+".tsv"),  sep="\t", quoting=csv.QUOTE_NONE, escapechar='\\', index=None, header=['sentence','label'], encoding="UTF-8")
    test.to_csv(os.path.join("..", args.subdir_name, "test"+suffix+".tsv"),  sep="\t", quoting=csv.QUOTE_NONE, escapechar='\\', index=None, header=['sentence','label'], encoding="UTF-8")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", default=False, help="updates the ids for all files in the given file_path")
    parser.add_argument("--preprocess", action="store_true", default=False, help="preprocesses the given id for all docs in the given file_path")
    parser.add_argument("--file_name_update", type=str, default="submissions.json", help="updates the ids for all files in the given file_name")
    parser.add_argument("--output_name_update", type=str, default="fullrjokes.json", help="updates the ids for all files in the given output_name")
    parser.add_argument("--file_name_preprocess", type=str, default="fullrjokes.json", help="preprocesses for all files in the given file_name")
    parser.add_argument("--output_name_preprocess", type=str, default="preprocessed.csv", help="preprocesses for all files in the given output_name")
    parser.add_argument("--subdir_name", type=str, default="data", help="defines where to get and save data files relative to pwd")
    parser.add_argument("--num_degrees", type=int, default=5, help="defines number of degrees of humour to differentiate")
    args = parser.parse_args()

    if args.update:
        read_and_update_ids(file_name=args.file_name_update, output_name=args.output_name_update)
    if args.preprocess:
        read_filter_and_preprocess(file_name=args.file_name_preprocess, output_name=args.output_name_preprocess)
    if not args.update and not args.preprocess:
        raise Exception("Did not give a command to execute...")
    
#%%    
# os.chdir("D:\\Janice/github/rJokes/rJokesData/data")
# read_and_update_ids(file_name="submissions.json", output_name="fullrjokes.json")

# Using different subdirs...
# python preprocess.py --update --subdir_name datasarcasm --file_name_update submissions1559920049.json --output_name_update fulldatasarcasm.json
# python preprocess.py --preprocess --subdir_name datasarcasm --file_name_preprocess fulldatasarcasm.json 

# python preprocess.py --update --subdir_name dataShowerThoughts --file_name_update submissions.json --output_name_update fulldataSHowerThoughts.json


# %%
