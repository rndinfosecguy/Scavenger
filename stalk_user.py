#!/usr/bin/python

import tweepy
import time
import os

class MyStreamListener(tweepy.StreamListener):
	def on_status(self, status):
		with open("stalking.txt", "a") as myfile:
			if "RT " not in status.text:
				print status.text
    				myfile.write(status.text + "\n")
				link = status.text.split(" ")
				for l in link:
					if "https://" in l:
						os.system("wget -O dumps/" + str(time.time()) + " " + l)

#Twitter API credentials
consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
try:
	# Get the ID of a twitter user https://tweeterid.com/
	myStream.filter(follow=["<TWITTER-USER-ID-U-WANT-TO-STALK>"])
except:
	pass
