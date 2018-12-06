from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from os.path import join
from os import getcwd
import os
import re

with open(join(getcwd(), '.env')) as environment:
    for var in environment:
        key = var.split('=')
        os.environ[key[0]] = re.sub('\n','',key[1])

CONSUMER_KEY = os.environ['consumer_key']
CONSUMER_SECRET = os.environ['consumer_secret']
ACCESS_TOKEN = os.environ['access_token']
ACCESS_TOKEN_SECRET = os.environ['access_token_secret']

class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_data(self, data):
        print(data)
        return True

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    stream = Stream(auth, l)
    stream.filter(track=['@MTW_LIVE'])