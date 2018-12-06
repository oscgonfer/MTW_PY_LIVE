#!/usr/bin/python

save_path = '/Users/macoscar/Documents/04_Projects/03_ArtWork/MTW/TECHNICAL/FABRA_LIVEMEDIA/vids'

import re
import datetime

import os
from os import getcwd
from os.path import join

import time

from multiprocessing import Process, Queue, current_process, freeze_support
import multiprocessing
# input_queue = Queue()
# output_queue = Queue()

import concurrent.futures
import subprocess

# Env file
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

list_tweets = list()

# Youtube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import youtube_dl

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
DEVELOPER_KEY = os.environ['api_key']

# OSC
from pythonosc import dispatcher
from pythonosc import osc_server

class OSCClient(multiprocessing.Process):

	def __init__(self, address='localhost', port=8000):

		multiprocessing.Process.__init__(self)
		self.dispatcher = dispatcher.Dispatcher()
		self.address = address
		self.port = port

	def run(self):

		# OSC Stuff
		# self.dispatcher.map("/filter", print)
		self.dispatcher.map("/filter", self.print_message)

		self.server = osc_server.ThreadingOSCUDPServer(
			  (self.address, self.port), self.dispatcher)
		print("Serving OSC on {}".format(self.server.server_address))
		self.server.serve_forever()

	def print_message(self, unused_addr, args):
		print (args)

def downloadYT(video_id, outname):

	url = 'https://www.youtube.com/watch?v={0}'.format(video_id)
	outtmpl = join(save_path, str(outname) + '.mp3')

	print ('[Debug] Downloading', url, 'to', outtmpl)

	ydl_opts = {
		'format': 'bestaudio/best',
		'outtmpl' : outtmpl,
		'verbose' : True,
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192'
		}],
	}
				
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download([url])


class TwitterListener(StreamListener):
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.
	"""
	def start(self, num_buttons):
		self.num_buttons = num_buttons
		self.list_replace = range(0,self.num_buttons-1)
		self.index_replace = 0
	
	def clean_tweet(self, tweet): 
		''' 
		Utility function to clean tweet text by removing links, special characters 
		using simple regex statements. 
		'''
		return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split()) 

	def on_status(self, status):

		# Make funny noise
		bashCommand = "say -v Trinoids 'tweet received'"
		os.system(bashCommand)

		# calling function to get tweets 
		now = datetime.datetime.now()
		print (now.strftime('[%Y-%m-%d %H:%M:%S]'), 'Got new tweet')

		# empty dictionary to store required params of a tweet 
		parsed_tweet = {} 
  
		# saving text of tweet 
		parsed_tweet['text'] = status.text 
		parsed_tweet['date'] = status.created_at

		# saving sentiment of tweet 
		parsed_tweet['clean_text'] = self.clean_tweet(re.sub('LIVE ', '', status.text))

		list_tweets.append(parsed_tweet)
		
		youtubeQuery = parsed_tweet['clean_text']
		print ('Checking for', youtubeQuery)

		videos = youtubeApi.youtube_search(query = youtubeQuery, max_results = self.num_buttons)

		if videos:
			print ('This is the first video', videos[0][0])
			replace_name = self.list_replace[self.index_replace]
			outname = 'S'+str(replace_name)

			print ('Submitting to thread', videos[0][1], 'with name', outname)

			with concurrent.futures.ThreadPoolExecutor(max_workers = 1) as executor:
				executor.submit(downloadYT, videos[0][1], outname)
			# self.processDL.map(downloadYT, [videos[0][1], outname])

			# input_queue.put([videos[0][1], outname])
			
			self.index_replace += 1
			# print (playurl)
			# downloadYouTube(playurl, '/Users/macoscar/Documents/04_Projects/03_ArtWork/MTW/TECHNICAL/FABRA_LIVEMEDIA/vids')

			# print ('This is the url', playurl)
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

	
	# twitterApi = TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET) 
	# YoutubeClient object
	youtubeApi = YouTubeClient(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, DEVELOPER_KEY)
	
	# TwitterListener object 
	twitterListener = TwitterListener()
	twitterListener.start(num_buttons = 16)
	twitterAuth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	twitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

	workerOSC = OSCClient(address = '127.0.0.1', port = 8000)
	workerOSC.daemon = True
	workerOSC.start()

	stream = Stream(twitterAuth, twitterListener)
	stream.filter(track=['@MTW_LIVE'], async=True)
	print ('Listening to @MTW_LIVE')