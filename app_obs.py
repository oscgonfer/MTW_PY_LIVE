#!/Users/macoscar/anaconda2/envs/python3v/bin/python3

import re
import datetime

import os
from os import getcwd, pardir
from os.path import join, abspath
from shutil import copyfile
import datetime

import time
import json

# Env file
with open(join(getcwd(), '.env')) as environment:
	for var in environment:
		key = var.split('=')
		os.environ[key[0]] = re.sub('\n','',key[1])

rootDirectory = abspath(join(getcwd(), pardir))
save_path_json = join(rootDirectory, 'MPC-MoreThanWords/TWITTER_FEED/bin/data')
print ('[Debug]', save_path_json)

# Twitter
import tweepy
from tweepy import OAuthHandler 
from tweepy.streaming import StreamListener
from tweepy import Stream
from textblob import TextBlob

CONSUMER_KEY = os.environ['consumer_key']
CONSUMER_SECRET = os.environ['consumer_secret']
ACCESS_TOKEN = os.environ['access_token']
ACCESS_TOKEN_SECRET = os.environ['access_token_secret']

dict_tweets = dict()

# Parsing urls
from urllib.parse import urlparse
import urllib.request

class TwitterListener(StreamListener):
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.
	"""
	def start(self):
		self.index_replace = 0
		self.index_tweets = 0
	
	def clean_tweet(self, tweet): 
		''' 
		Utility function to clean tweet text by removing links, special characters 
		using simple regex statements. 
		'''
		return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split()) 

	def on_status(self, status):
		
		try:	
			full_tweet = status.extended_tweet
		except:
			full_tweet = status
		
		# Make funny noise
		# bashCommand = "say -v 'Trinoids' 'Tweet received'"
		# os.system(bashCommand)

		# calling function to get tweets 
		now = datetime.datetime.now()
		print ('[Debug]', now.strftime('[%Y-%m-%d %H:%M:%S]'), 'Got new tweet')

		# empty dictionary to store required params of a tweet 
		parsed_tweet = {} 
  
		# saving text of tweet 
		try:		
			parsed_tweet['text'] = full_tweet['full_text'] 
		except:
			parsed_tweet['text'] = status.text

		parsed_tweet['date'] = status.created_at.isoformat()
		parsed_tweet['author'] = status.user.name
		parsed_tweet['handle'] = status.user.screen_name

		# Clean text
		parsed_tweet['clean_text'] = re.sub('@MTW_LIVE ', '', parsed_tweet['text'])
		parsed_tweet['clean_text'] = re.sub('\n', '', parsed_tweet['clean_text'])
		# Change quote weird character for actual unicode
		parsed_tweet['clean_text'] = re.sub('\u201c', '"', parsed_tweet['clean_text'])
		parsed_tweet['clean_text'] = re.sub('\u201d', '"', parsed_tweet['clean_text'])

		dict_tweets[str(self.index_tweets)] = dict()
		dict_tweets[str(self.index_tweets)]['text'] = parsed_tweet['text']
		dict_tweets[str(self.index_tweets)]['date'] = parsed_tweet['date']
		dict_tweets[str(self.index_tweets)]['author'] = parsed_tweet['author']
		dict_tweets[str(self.index_tweets)]['clean_text'] = parsed_tweet['clean_text']
		dict_tweets[str(self.index_tweets)]['handle'] = parsed_tweet['handle']
		
		self.index_tweets += 1

		# Save tweets list
		with open(join(save_path_json, 'tweets_list.json'), 'w') as tweet_list_js:
			json.dump(dict_tweets, tweet_list_js)
			print ('[Debug] Saving json file')

		print ('[Debug] Tweet author', parsed_tweet['author'])

		return True

	def on_error(self, status):
		print(status)

if __name__ == '__main__':
	
	# TwitterListener object 
	twitterListener = TwitterListener()
	twitterListener.start()

	# Twitter
	twitterAuth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	twitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
	twitterAPI = tweepy.API(twitterAuth)

	stream = Stream(twitterAuth, twitterListener, tweet_mode= 'extended')
	stream.filter(track=['@MTW_LIVE'], async=True)
	print ('[Debug] Listening to @MTW_LIVE')
