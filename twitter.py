#!/usr/bin/python

import re 
import tweepy 
from tweepy import OAuthHandler 
from textblob import TextBlob 
import argparse

import os
from os import getcwd
from os.path import join

import pandas as pd
import time
  
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


with open(join(getcwd(), '.env')) as environment:
  for var in environment:
    key = var.split('=')
    os.environ[key[0]] = re.sub('\n','',key[1])

# Put codes into vars
consumer_key = os.environ['consumer_key']
consumer_secret = os.environ['consumer_secret']
access_token = os.environ['access_token']
access_token_secret = os.environ['access_token_secret']

if __name__ == '__main__':

    # parser = argparse.ArgumentParser()
    # parser.add_argument('--q', help='Search term', default='Google')
    # parser.add_argument('--max-results', help='Max results', default=1)
    # args = parser.parse_args()

    # creating object of TwitterClient Class 
    api = TwitterClient(consumer_key, consumer_secret, access_token, access_token_secret) 

    while True:

        # calling function to get tweets 
        print ('Making new call to API')
        tweets = api.get_tweets(query = '@MTW_LIVE', count = 16) 
    
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

            print (dataframe)
            print ('Checking for', (dataframe.iloc[-1, :][0]))

            time.sleep(5)