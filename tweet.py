#!/usr/bin/python
import tweepy
import re
import datetime

import os
from os import getcwd
from os.path import join
from shutil import copyfile

import time
import json

# Multiprocessing and threads
from multiprocessing import Process, Queue, current_process, freeze_support
import multiprocessing
import concurrent.futures
import subprocess

# Env file
with open(join(getcwd(), '.env')) as environment:
	for var in environment:
		key = var.split('=')
		os.environ[key[0]] = re.sub('\n','',key[1])

save_path = join(getcwd(), 'vids')

# Open topic_list
topic_path = join(getcwd(), 'list_topics.txt')
with open(topic_path, 'r') as topic_file:
	topic_list = topic_file.readlines()
topic_list = [x.strip() for x in topic_list] 		
print ('[Debug] Topic file list')
print ('[Debug]', topic_list)

# Twitter
from tweepy import OAuthHandler 
from tweepy.streaming import StreamListener
from tweepy import Stream
from textblob import TextBlob

CONSUMER_KEY = os.environ['consumer_key']
CONSUMER_SECRET = os.environ['consumer_secret']
ACCESS_TOKEN = os.environ['access_token']
ACCESS_TOKEN_SECRET = os.environ['access_token_secret']

if __name__ == '__main__':

	twitterAuth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	twitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

	api = tweepy.API(twitterAuth)
	topic = "war"	
	print (api)
	api.update_status('[Test tweet] Now, let’s talk about: {}'.format(topic))
