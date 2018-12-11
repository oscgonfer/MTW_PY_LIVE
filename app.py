#!/usr/bin/python

import re
import datetime

import os
from os import getcwd, pardir
from os.path import join, abspath
from shutil import copyfile
import datetime

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

rootDirectory = abspath(join(getcwd(), pardir))
save_path = join(rootDirectory, 'MPC-MoreThanWords/MTW/bin/data')

# Open topic_list
topic_path = join(getcwd(), 'list_topics.txt')
with open(topic_path, 'r') as topic_file:
	topic_list = topic_file.readlines()
topic_list = [x.strip() for x in topic_list] 		
print ('[Debug] Topic file list')
print ('[Debug]', topic_list)

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

first_day_show = "2018-12-13"
second_day_show = "2018-12-14"

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
from pythonosc import osc_message_builder
from pythonosc import udp_client
PYTHON_PORT = 8000
CPP_PORT = 53000

# Parsing urls
from urllib.parse import urlparse
import urllib.request

class OSCClient(multiprocessing.Process):

	def __init__(self, address='localhost', port=8000, threshold_pressed = 60):

		multiprocessing.Process.__init__(self)
		self.dispatcher = dispatcher.Dispatcher()
		self.address = address
		self.port = port
		self.index_topic = 0
		self.time_last_pressed = 0
		self.time_pressed = 0
		self.threshold_pressed = threshold_pressed


	def run(self):

		# OSC Stuff
		self.dispatcher.map("/filter", self.print_message)
		self.dispatcher.map("/reset", self.reset_status)


		self.server = osc_server.ThreadingOSCUDPServer(
			  (self.address, self.port), self.dispatcher)
		print("[Debug] Serving OSC on {}".format(self.server.server_address))
		self.server.serve_forever()

	def print_message(self, unused_addr, message):
		print (message)

	def reset_status(self, unused_addr, message):
		print ("[Debug] Reset button pressed")
		# Check delta between last time pressed
		self.time_pressed = time.time()
		if self.time_pressed - self.time_last_pressed > self.threshold_pressed:
			print ('[Debug] Accepting button pressed')
			self.time_last_pressed = self.time_pressed

			# Actually do stuff
			twitterListener.start(num_buttons = 16)

			# Check new topic and copy 16 videos
			next_topic = topic_list[self.index_topic]
			self.index_topic += 1
			if self.index_topic > len(topic_list) - 1: self.index_topic = 0
			
			try:
				print ('[Debug] Copying files from', next_topic)
				
				dest = save_path
				source = join(save_path, next_topic)

				for root, dirs, files in os.walk(source):
					for _file in files:
						if _file.endswith(".mp3"):
							filePathSource = join(source, _file)
							filePathDest = join(dest, _file)
							copyfile(filePathSource, filePathDest)
			except:
				print ('[Debug] Failure copying files')
				pass
			
			tweetReset(next_topic)
		else:
			print ('[Debug] Ignoring button pressed, not enough time')

def tweetReset(topic):
	print('[Debug] Post tweet with topic', topic)

	now = datetime.datetime.now().strftime("%Y-%m-%d")
	try:
		if now < first_day_show:
			print ('[Debug] Still testing:', '[Test tweet] Now, let’s talk about: {}'.format(topic))
			twitterAPI.update_status('[Test tweet] Now, let’s talk about: {}'.format(topic))

		elif now == first_day_show:
			print ('[Debug] First day!')

			twitterAPI.update_status('Now, let’s talk about: {}. What are your fears about technology related to {}? Send us a link to a YouTube video or simply your thoughts. #MoreThanWordsLive #codenowness'.format(topic, topic))
		elif now == second_day_show:
			print ('[Debug] Second day!')

			twitterAPI.update_status('Now, let’s talk about: {}. What do you expect technology will one day be able to do regarding {}? Send us a link to a YouTube video or simply your thoughts. #MoreThanWordsLive #codenowness'.format(topic, topic))
	except:
		print('[Debug] Could not post tweet with topic', topic) 
		pass

def downloadYT(video_url, outname):

	# Extract url
	try:
		url_parse = urlparse(video_url)
		video_id = url_parse.query
		if '&' in video_id: video_id = video_id[video_id.find('=')+1:video_id.find('&')]
		else: video_id = video_id[video_id.find('=')+1:]
	except:
		print ('[Debug] Error parsing url')
		pass

	print ('[Debug] Downloading', video_url, 'to', outname + '.mp3')

	ydl_opts = {
		'format': 'bestaudio/best',
 		'extractaudio': True,
 		'outtmpl': join(save_path, '%(id)s.%(ext)s'),
		'verbose' : True,
		'forcefilename': True,
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192'
		}],
		'noplaylist': True
	}

	try:
				
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([video_url])

	except:
		print('[Debug] Error downloading YT video')
		pass

	try:
		filename = video_id + '.mp3'
		original_name = join(save_path, filename)
		print (original_name)
		target_name = join(save_path, outname + '.mp3')
		print

		print ('[Debug] Moving file', original_name, 'to', target_name)

		if os.path.isfile(original_name):
			os.rename(original_name, target_name)
			print ('[Debug] File moved')
		else:
			print ('[Debug] File does not exist')

		print ('[Debug] Finished video download')
	except:
		print ('[Debug] Error moving file')

class TwitterListener(StreamListener):
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.
	"""
	def start(self, num_buttons):
		self.num_buttons = num_buttons
		self.list_replace = range(0,self.num_buttons)
		self.index_replace = 0
		self.index_tweets = 0
	
	def clean_tweet(self, tweet): 
		''' 
		Utility function to clean tweet text by removing links, special characters 
		using simple regex statements. 
		'''
		return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split()) 

	def on_status(self, status):

		# Make funny noise
		bashCommand = "say -v 'Trinoids' 'Tweet received'"
		os.system(bashCommand)

		# calling function to get tweets 
		now = datetime.datetime.now()
		print ('[Debug]', now.strftime('[%Y-%m-%d %H:%M:%S]'), 'Got new tweet')

		# empty dictionary to store required params of a tweet 
		parsed_tweet = {} 
  
		# saving text of tweet 
		parsed_tweet['text'] = status.text 
		parsed_tweet['date'] = status.created_at.isoformat()
		parsed_tweet['author'] = status.user.name

		# saving sentiment of tweet 
		# parsed_tweet['clean_text'] = self.clean_tweet(re.sub('LIVE ', '', status.text))
		
		parsed_tweet['clean_text'] = re.sub('@MTW_LIVE ', '', status.text)

		dict_tweets[str(self.index_tweets)] = dict()
		dict_tweets[str(self.index_tweets)]['text'] = parsed_tweet['text']
		dict_tweets[str(self.index_tweets)]['date'] = parsed_tweet['date']
		dict_tweets[str(self.index_tweets)]['author'] = parsed_tweet['author']
		dict_tweets[str(self.index_tweets)]['clean_text'] = parsed_tweet['clean_text']

		self.index_tweets += 1

		with open(join(getcwd(), 'tweets_list.json'), 'w') as tweet_list_js:
			json.dump(dict_tweets, tweet_list_js)

		# Check what it is
		check_quote = re.findall(r'"([^"]*)"', parsed_tweet['clean_text'])

		replace_name = self.list_replace[self.index_replace]
		outname = 'S'+str(replace_name)

		print ('[Debug]', parsed_tweet['clean_text'], check_quote)

		if check_quote != []:
			# Assume they want a readout
			print ('[Debug] quote requested')
			bashCommand = "say -o " + outname + '.aiff ' + str(check_quote)
			os.system(bashCommand)
			print ('[Debug]', bashCommand)			
			bashCommand = ('lame -m m ' + outname + '.aiff ' + outname + '.mp3')
			os.system(bashCommand)
			print ('[Debug]', bashCommand)
			bashCommand = ('rm ' + outname + '.aiff')
			os.system(bashCommand)
			print ('[Debug]', bashCommand)			
			bashCommand = ('mv ' + outname + '.mp3 ' + join(save_path, outname + '.mp3'))
			os.system(bashCommand)
			print ('[Debug]', bashCommand)

			soundType = 'quote'
		
		else:

			# Parse as url
			check_url = urlparse(parsed_tweet['clean_text'])
			print ('[Debug] ', check_url)

			if check_url.netloc == '':

				youtubeQuery = parsed_tweet['clean_text']
				print ('[Debug] Checking for', youtubeQuery)

				videos = youtubeApi.youtube_search(query = youtubeQuery, 
													max_results = self.num_buttons)

				if videos:
					print ('[Debug] This is the first video', videos[0][0])
					
					print ('[Debug] Submitting to thread', videos[0][1], 'with name', outname)

					url = 'https://www.youtube.com/watch?v={0}'.format(videos[0][1])
					print ('[Debug] Requested url', url)
					
					with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
						executor.submit(downloadYT, url, outname)
			elif check_url.netloc == 'youtu.be' or check_url.netloc == 'www.youtube.com':
				url = parsed_tweet['clean_text']

				with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
					executor.submit(downloadYT, url, outname)
			elif check_url.netloc == 't.co':
				# Checking twitter link
				opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
				request = opener.open(parsed_tweet['clean_text'])

				url = request.url
				print ('[Debug] Requested url', url)

				with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
					executor.submit(downloadYT, url, outname)

			soundType = 'loop'

		## Send New sound to C++
		if soundType == 'quote': message = 1
		elif soundType == 'loop': message = 2
		
		cpp_client.send_message('/sound', [self.index_replace, message])
		print ('[Debug] Send message', '/sound', self.index_replace, message)


		self.index_replace += 1
		if self.index_replace > self.num_buttons -1: self.index_replace = 0

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
			maxResults=max_results,
			type='video',
			videoDuration='short',
			order='viewCount'
		).execute()

		videos = list(tuple())
  
		# Add each result to the appropriate list, and then display the lists of
		# matching videos, channels, and playlists.
		for search_result in search_response.get('items', []):
			if search_result['id']['kind'] == 'youtube#video':
				videos.append((search_result['snippet']['title'],search_result['id']['videoId']))

		return videos

if __name__ == '__main__':

	# YoutubeClient object
	youtubeApi = YouTubeClient(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, DEVELOPER_KEY)
	
	# TwitterListener object 
	twitterListener = TwitterListener()
	twitterListener.start(num_buttons = 16)

	# Twitter
	twitterAuth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	twitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
	twitterAPI = tweepy.API(twitterAuth)

	now = datetime.datetime.now().strftime("%Y-%m-%d")
	if now < first_day_show:
		print ('[Debug] Still testing')
		try:
			twitterAPI.update_status("[Test tweet] Hello everyone! We are testing our installation!")
		except:
			pass
			
	elif now == first_day_show:
		print ('[Debug] First day!')

		twitterAPI.update_status("Today we will talk about technology and it's implications. What are your fears about technology? Send us a link to a YouTube video or simply your thoughts. #MoreThanWordsLive #codenowness")
	elif now == second_day_show:
		print ('[Debug] Second day!')

		twitterAPI.update_status("Today we will talk about technology and it's potential. What do you expect technology will one day be able to do in the future? Send us a link to a YouTube video or simply your thoughts. #MoreThanWordsLive #codenowness")
	

	workerOSC = OSCClient(address = '127.0.0.1', port = PYTHON_PORT)
	workerOSC.daemon = True
	workerOSC.start()

	cpp_client = udp_client.SimpleUDPClient('localhost', CPP_PORT)
	print ('[Debug] OSC Sending on localhost to', CPP_PORT)
	
	stream = Stream(twitterAuth, twitterListener)
	stream.filter(track=['@MTW_LIVE'], async=True)
	print ('[Debug] Listening to @MTW_LIVE')