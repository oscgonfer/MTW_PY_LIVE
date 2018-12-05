#!/usr/bin/python

# This sample executes a search request for the specified search term.
# Sample usage:
#   python search.py --q=surfing --max-results=10
# NOTE: To use the sample, you must provide a developer key obtained
#       in the Google APIs Console. Search for "REPLACE_ME" in this code
#       to find the correct place to provide that key..

import argparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pafy
import vlc


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import os
from os import getcwd
from os.path import join

with open(join(getcwd(), '.env')) as environment:
  for var in environment:
    key = var.split('=')
    os.environ[key[0]] = key[1]

DEVELOPER_KEY = os.environ['api_key']

def pafy_video(_video_id):
  url = 'https://www.youtube.com/watch?v={0}'.format(_video_id)
  vid = pafy.new(url)
  best = vid.getbest()
  playurl = best.url
  return playurl

def play_video (_playurl):
  Instance = vlc.Instance()
  player = Instance.media_player_new()
  Media = Instance.media_new(_playurl)
  Media.get_mrl()
  player.set_media(Media)
  # orig = shutup()
  player.play()
  # talk(orig)

def youtube_search(options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(
    q=options.q + 'sound effect',
    part='id,snippet',
    maxResults=options.max_results,
    type='channel'
  ).execute()

  videos = list(tuple())
  # channels = []
  # playlists = []

  # Add each result to the appropriate list, and then display the lists of
  # matching videos, channels, and playlists.
  for search_result in search_response.get('items', []):
    if search_result['id']['kind'] == 'youtube#video':
      videos.append((search_result['snippet']['title'],
                                 search_result['id']['videoId']))
    # elif search_result['id']['kind'] == 'youtube#channel':
    #   channels.append('%s (%s)' % (search_result['snippet']['title'],
    #                                search_result['id']['channelId']))
    # elif search_result['id']['kind'] == 'youtube#playlist':
    #   playlists.append('%s (%s)' % (search_result['snippet']['title'],
    #                                 search_result['id']['playlistId']))

  # print ('Videos:\n', '\n'.join(videos), '\n')
  # print ('Channels:\n', '\n'.join(channels), '\n')
  # print ('Playlists:\n', '\n'.join(playlists), '\n')
  return videos

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--q', help='Search term', default='Google')
  parser.add_argument('--max-results', help='Max results', default=25)
  args = parser.parse_args()

  videos = youtube_search(args)
  if videos:
    print ('Playing the first video')
    print (videos[0][0])
    playurl = pafy_video(videos[0][1])
    print (playurl)
    play_video(playurl)
    while True:
      a = 0
