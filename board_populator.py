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

rootDirectory = abspath(join(getcwd(), pardir))
# save_path = join(rootDirectory, 'MPC-MoreThanWords/MTW/bin/data')
save_path = '/Users/rebecca/Desktop/Test'

# Env file
with open(join(getcwd(), '.env')) as environment:
	for var in environment:
		key = var.split('=')
		os.environ[key[0]] = re.sub('\n','',key[1])

# Open topic_list
topic_path = join(getcwd(), 'list_topics_good.txt')
with open(topic_path, 'r') as topic_file:
	topic_list = topic_file.readlines()
topic_list = [x.strip() for x in topic_list] 		
print ('[Debug] Topic file list')
print ('[Debug]', topic_list)

# Open topic_list
subtopic_path = join(getcwd(), 'list_subtopics.txt')
with open(subtopic_path, 'r') as subtopic_file:
	subtopic_list = subtopic_file.readlines()
subtopic_list = [x.strip() for x in subtopic_list] 		
print ('[Debug] Subopic file list')
print ('[Debug]', subtopic_list)

# Youtube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import youtube_dl

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
DEVELOPER_KEY = os.environ['api_key']

# Parsing urls
from urllib.parse import urlparse
import urllib.request

def downloadYT(video_url, outname, subfolder):
	subfolder = re.sub(' ', '_',subfolder)
	_save_path = join(save_path, subfolder)

	if not os.path.exists(_save_path):
	    os.makedirs(_save_path)

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
 		'outtmpl': join(_save_path, '%(id)s.%(ext)s'),
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
		original_name = join(_save_path, filename)
		print (original_name)
		target_name = join(_save_path, outname + '.mp3')
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

class BoardGenerator():
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.
	"""
	def __init__(self, num_videos, topics, list_subtopics):
		self.num_videos = num_videos
		self.index_replace = 0	
		self.topics = topics
		self.list_subtopics = list_subtopics

	def run(self):

		for topic in self.topics:
			for subtopic in self.list_subtopics:
				query = topic + ' ' + subtopic
				
				if '#' not in topic:

					print ('[Debug] Checking for', query)
	
					videos = youtubeApi.youtube_search(query = query, 
												max_results = self.num_videos)
					
					if videos:
						for i in range(self.num_videos):
							try:
								replace_name = self.index_replace
								outname = topic +'_'+subtopic +'_'+str(i)
								
								print ('[Debug] This is the video number', i, videos[i][0])
							
								print ('[Debug] Submitting to thread', videos[i][1], 'with name', outname)
	
								url = 'https://www.youtube.com/watch?v={0}'.format(videos[i][1])
								print ('[Debug] Requested url', url)
								
								with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
									executor.submit(downloadYT, url, outname, topic)
	
								self.index_replace += 1
							except:
								pass

		return True

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
	bg = BoardGenerator(2, topic_list, subtopic_list)

	bg.run()
