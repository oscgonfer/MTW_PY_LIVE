#!/usr/bin/python

import re
import datetime

import os
from os import getcwd
from os.path import join

import pandas as pd
import time

import pafy
import vlc

from multiprocessing import Process, Queue, current_process, freeze_support
import multiprocessing

with open(join(getcwd(), '.env')) as environment:
	for var in environment:
		key = var.split('=')
		os.environ[key[0]] = re.sub('\n','',key[1])

# Twitter
from tweepy import OAuthHandler 
from tweepy.streaming import StreamListener
from tweepy import Stream
from textblob import TextBlob 

CONSUMER_KEY = os.environ['consumer_key']
CONSUMER_SECRET = os.environ['consumer_secret']
ACCESS_TOKEN = os.environ['access_token']
ACCESS_TOKEN_SECRET = os.environ['access_token_secret']

# Youtube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
DEVELOPER_KEY = os.environ['api_key']

# OSC

# from pythonosc import osc_message_builder
# from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

class OSCClient(multiprocessing.Process):

	def __init__(self, address='localhost', port=8000):

		multiprocessing.Process.__init__(self)
		self.dispatcher = dispatcher.Dispatcher()
		self.address = address
		self.port = port

		# client = udp_client.UDPClient('localhost', 8000)
	def run(self):

		# OSC Stuff
		# self.dispatcher.map("/filter", print)
		self.dispatcher.map("/filter", self.print_message)

		self.server = osc_server.ThreadingOSCUDPServer(
			  (self.address, self.port), self.dispatcher)
		print("Serving on {}".format(self.server.server_address))
		self.server.serve_forever()

	def print_message(self, unused_addr, args):
		print (args)

def pafy_video(video_id):
	url = 'https://www.youtube.com/watch?v={0}'.format(video_id)
	vid = pafy.new(url)
	best = vid.getbest()
	playurl = best.url
	return playurl

class TwitterClient(object): 
	''' 
	Generic Twitter Class for sentiment analysis. 
	'''
	def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret): 
		''' 
		Class constructor or initialization method. 
		'''
		# keys and tokens from the Twitter Dev Console 
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret
  
		# attempt authentication 
		try: 
			# create OAuthHandler object 
			self.auth = OAuthHandler(consumer_key, consumer_secret) 
			# set access token and secret 
			self.auth.set_access_token(access_token, access_token_secret) 
			# create tweepy API object to fetch tweets 
			self.api = tweepy.API(self.auth) 
		except: 
			print("Error: Authentication Failed") 
  
	def clean_tweet(self, tweet): 
		''' 
		Utility function to clean tweet text by removing links, special characters 
		using simple regex statements. 
		'''
		return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split()) 
  
	def get_tweet_sentiment(self, tweet): 
		''' 
		Utility function to classify sentiment of passed tweet 
		using textblob's sentiment method 
		'''
		# create TextBlob object of passed tweet text 
		analysis = TextBlob(self.clean_tweet(tweet)) 
		# set sentiment 
		if analysis.sentiment.polarity > 0: 
			return 'positive'
		elif analysis.sentiment.polarity == 0: 
			return 'neutral'
		else: 
			return 'negative'
  
	def get_tweets(self, query, count): 
		''' 
		Main function to fetch tweets and parse them. 
		'''
		# empty list to store parsed tweets 

		tweets = []

		try: 
			# call twitter api to fetch tweets 
			fetched_tweets = self.api.search(q = query, count = count) 
			# parsing tweets one by one 
			for tweet in fetched_tweets: 

				# empty dictionary to store required params of a tweet 
				parsed_tweet = {} 
  
				# saving text of tweet 
				parsed_tweet['text'] = tweet.text 
				parsed_tweet['date'] = tweet.created_at
				# saving sentiment of tweet 
				parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text) 
				parsed_tweet['clean_text'] = self.clean_tweet(tweet.text)
				
				# appending parsed tweet to tweets list 
				if tweet.retweet_count > 0: 
					# if tweet has retweets, ensure that it is appended only once 
					if parsed_tweet not in tweets: 
						tweets.append(parsed_tweet) 
				else: 
					tweets.append(parsed_tweet) 
  
			# return parsed tweets 
			return tweets 
  
		except tweepy.TweepError as e: 
			# print error (if any) 
			print("Error : " + str(e)) 

class TwitterListener(StreamListener):
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.
	"""
	def on_data(self, data):
		print(data)
		return True

	def on_error(self, status):
		print(status)

class YouTubeClient(object):
	def __init__(self, service_name, api_version, developer_key): 

		self.service_name = service_name
		self.api_version = api_version
		self.developer_key = developer_key

		try: 
			self.youtube = build(self.service_name, self.api_version, developerKey=self.developer_key)
		except:
			print("Error: Build Failed") 

	def youtube_search(self, query, max_results):

		# Call the search.list method to retrieve results matching the specified
		# query term.
		search_response = self.youtube.search().list(
			q=query,
			part='id,snippet',
			maxResults=max_results
		).execute()

		videos = list(tuple())
  
		# Add each result to the appropriate list, and then display the lists of
		# matching videos, channels, and playlists.
		for search_result in search_response.get('items', []):
			if search_result['id']['kind'] == 'youtube#video':
				videos.append((search_result['snippet']['title'],search_result['id']['videoId']))

		return videos

if __name__ == '__main__':

	# creating object of TwitterClient Class 
	# twitterApi = TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET) 
	youtubeApi = YouTubeClient(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, DEVELOPER_KEY)
	
	twitterListener = TwitterListener()
	twitterAuth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	twitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

	workerOSC = OSCClient(address = '127.0.0.1', port = 8000)
	workerOSC.daemon = True
	workerOSC.start()

	stream = Stream(twitterAuth, twitterListener)
	stream.filter(track=['@MTW_LIVE'])

	dataframeTweets = pd.DataFrame()

	while True:

		newTweet = False

		# calling function to get tweets 
		now = datetime.datetime.now()
		print (now.strftime('[%Y-%m-%d %H:%M:%S]'), 'Making new call to API')
		# tweets = twitterApi.get_tweets(query = '@MTW_LIVE', count = 16) 
		tweets = ()
		if tweets:
			list_dates = list()
			list_tweets = list()

			for tweet in tweets:
				list_dates.append(tweet['date'])
				list_tweets.append(re.sub('LIVE ', '', tweet['clean_text']))

			dataframe = pd.DataFrame(list_tweets)
			dataframe.columns = ['Tweets']
			dataframe.index = list_dates
			dataframe.sort_index(inplace = True)

			if dataframeTweets.empty:
				if not dataframe.empty:
					newTweet = True
					print ('We have a new tweet!')
					dataframeTweets = dataframe.copy()
				else: 
					print ('Nothing new!')
			else:
				if dataframe.index[-1] > dataframeTweets.index[-1]:
					newTweet = True
					print ('We have a new tweet!')
					dataframeTweets = dataframe.copy()
				else:
					print ('Nothing new!')

			if newTweet:
				bashCommand = "say -v Trinoids 'tweet received'"
				
				os.system(bashCommand)

				print (dataframe)
				youtubeQuery = dataframe.iloc[-1, :][0]
				print ('Checking for', youtubeQuery)
	
				videos = youtubeApi.youtube_search(query = youtubeQuery, max_results = 16)
	
				if videos:
					print ('This is the first video', videos[0][0])
					playurl = pafy_video(videos[0][1])
					# print ('This is the url', playurl)

		time.sleep(5)