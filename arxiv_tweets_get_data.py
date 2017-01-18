
# coding: utf-8

# # Getting the data
# 
# This code connects to a global Twitter stream and listens for tweets that contain keyword 'arxiv'. In every such status, links that lead to an Arxiv paper are identified and paper's arxiv_id and version are extrected from the link. These are than saved in a raw_data.csv file, together with UTC time of the tweet. Data are gathered during 24 hour period.
# 
# TODO:
# Retweets are problematic, they sometimes contain only the link to the original status (both in tweepy.status.retweeted_status.entities['urls'] and tweepy.status.retweeted_status.text). Solution would be to follow the link to the original status. Problem: chains of statuses (although depth 1 may be enough). Too much work.
# 

# In[ ]:

import tweepy
import csv
from datetime import datetime
#from IPython import display

import urllib2 as ul                #to clear up redirections
import re                #for validation of Arxiv urls

import os
if not os.path.isdir('data'):
    os.mkdir('data')


# To acces the Twitter stream, API acces keys are first necessary:
# 
# https://www.digitalocean.com/community/tutorials/how-to-authenticate-a-python-application-with-twitter-using-tweepy-on-ubuntu-14-04

# In[ ]:

#consumer key & consumer secret
TWITTER_APP_KEY=        #Enter consumer key
TWITTER_APP_SECRET=            #Enter consumer secret

#acces token & acces token secret
TWITTER_KEY=       #enter acces token
TWITTER_SECRET=        #enter acces token secret

#authentication
auth = tweepy.OAuthHandler(TWITTER_APP_KEY, TWITTER_APP_SECRET)
auth.set_access_token(TWITTER_KEY, TWITTER_SECRET)

api=tweepy.API(auth)


# In[ ]:

#function that parses url of the paper and returns its id and version 
#Examples of urls of the paper with id 1612.03499 and version 2:
#    https://arxiv.org/abs/1612.03499v2
#    https://arxiv.org/pdf/1612.03499v2.pdf
#    https://arxiv.org/abs/1612.03499?utm_source=dlvr.it&utm_medium=twitter
#
#if url doesn't match, returns False

arxiv_url_re=re.compile(r'https?://arxiv\.org/((abs)|(pdf))/\d{4}\.\d{4,5}(v\d)?')

def id_from_url(url):
    match=arxiv_url_re.search(url) #check if it's a valid arxiv address
    if match:
        arxiv_id=match.group().split('/')[-1]
        try:
            arxiv_id,version=arxiv_id.rsplit('v')
        except ValueError:
            version=0
        return arxiv_id,int(version)
    else:
        return False

datafile=open(os.path.join('data','raw_data.csv'),'a')
csvwriter=csv.writer(datafile)

def add_to_file(arxiv_id,version,created_at):
    csvwriter.writerow(map(str,[arxiv_id,version,created_at]))
    datafile.flush()

#stream listener
class StreamListener(tweepy.StreamListener):
    def __init__(self):
        super( StreamListener, self ).__init__()
        self.num=0            #number of processed statuses
        self.num_added=0      #number of added papers (not every status contains paper)
        self.started_at=datetime.utcnow()
        
    def on_status(self, status):
        if (datetime.utcnow()-self.started_at).days>0:
            print 'Listened for 24 hours, shutting down the listener.'
            datafile.close()
            return False
        
        self.num+=1
        created_at=status.created_at
        
        #display.clear_output()
        print '--------------------------------------------------------------'
        print 'Tweets processed: '+str(self.num)+'        Papers added: '+str(self.num_added)
        print 'Started at UTC: '+str(self.started_at)
        print 'Last paper added:'
        
        #if status is retweeted, consider urls in the original status (because of truncating)
        try:
            if status.retweeted_status:
                status=status.retweeted_status
        except AttributeError:
            pass

        for i in status.entities['urls']:
            exp_url=i['expanded_url']
            #try to see where is the url redirected to
            try:
                response= ul.urlopen(exp_url)
            except:
                url=exp_url
            else:
                url=response.geturl()
            
            #if the url leads to an arxiv paper, add it to the table
            match=id_from_url(url)
            if match:
                arxiv_id,version=match
                
                self.num_added+=1
                print arxiv_id,version,created_at
                
                add_to_file(arxiv_id,version,created_at)
        
    def on_error(self, status_code):
        if status_code == 420:
            print 'twitter limit reached'
            return False


# In[ ]:

at_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=at_listener)
stream.filter(track=['arxiv'])


# In[ ]:



