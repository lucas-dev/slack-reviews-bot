#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'libs')

from google.appengine.api import urlfetch
from google.appengine.ext import db
import webapp2
import json
from slacker import Slacker

# base variables
SEARCHMAN_ACCESS_TOKEN = "1fee0affd210f7d...." # YOUR API KEY
SEARCHMAN_BASE_URL = "http://api.searchman.io/v1/{platform}/{store_location}/app/reviews?appId={app_id}&apiKey={token}"

REVIEWS_ANDROID_URL = SEARCHMAN_BASE_URL.format(platform="android", store_location="us", app_id="com.nintendo.zara", token=SEARCHMAN_ACCESS_TOKEN)
REVIEWS_IOS_URL = SEARCHMAN_BASE_URL.format(platform="ios", store_location="us", app_id="1145275343", token=SEARCHMAN_ACCESS_TOKEN)

SLACK_ACCESS_TOKEN = "xoxp-339759810052-339993731490..." # YOUR LEGACY TOKEN

# Model class
class Review(db.Model):
    platform = db.StringProperty()
    rate = db.IntegerProperty()
    title = db.StringProperty()
    description = db.StringProperty(multiline=True)
    author = db.StringProperty()
    date = db.IntegerProperty()


#Controller
class ReviewsHandler(webapp2.RequestHandler):
    slack = Slacker(SLACK_ACCESS_TOKEN)

    def get(self):
        # json data
        reviews_android = self.get_json_data(REVIEWS_ANDROID_URL)
        reviews_ios = self.get_json_data(REVIEWS_IOS_URL)

        for review in reviews_android:
            self.process_data(str(self.get_key_val("id", review)), 
                         "android", 
                         self.get_key_val("rating", review), 
                         self.get_key_val("title", review), 
                         self.get_key_val("body", review), 
                         self.get_key_val("author", review), 
                         self.get_key_val("timestampEpoch", review))

        for review in reviews_ios:
            self.process_data(self.get_key_val("id", review), 
                         "ios", 
                         self.get_key_val("rating", review), 
                         self.get_key_val("title", review), 
                         self.get_key_val("body", review), 
                         self.get_key_val("author", review), 
                         int(self.get_key_val("timestampEpoch", review)))


    def get_key_val(self, key, dict):
        if key in dict:
            return dict[key]
        else:
            return ""


    def process_data(self, key_name, platform, rate, title, description, author, date):
        # create and save entity only if it doesn't exist on the datastore
        review = Review.get_or_insert(key_name)
        if not review.author:
            review.key_name = key_name
            review.platform = platform
            review.rate = rate
            review.title = title
            review.description = description
            review.author = author
            review.date = date

            review.put()

            self.post_to_slack(":robot_face:",
                               "Super Mario Run", 
                               "https://i.imgur.com/TlCWXG2.png",
                               "#reviews",
                               "ReviewBot",
                               review)


    def get_json_data(self, url):
        reviews_response = urlfetch.fetch(url)
        reviews_data = json.loads(reviews_response.content)
        return reviews_data["data"]


    def post_to_slack(self, boticon, appname, appicon, channel, username, review):
        title = ""
        icon = ""
        if (review.platform == "ios"):
            title = "AppStore"
            icon = "https://i.imgur.com/H2PjN7n.png"
        else:
            title = "Android"
            icon = "https://i.imgur.com/iWET221.png"

        stars = ""
        for i in range(5):
            if (i<review.rate):
                stars+="★"
            else:
                stars+="☆"

        msg_body  = json.dumps([
            {
                "color": "#36a64f",
                "author_name": stars,
                "author_icon": appicon,
                "title": review.title,
                "text": review.description,
                "thumb_url": icon,
                "footer": "by %s" % review.author,
                "footer_icon": "https://i.imgur.com/uCzz1ER.png",
                "ts": review.date
            }
        ]);
        ReviewsHandler.slack.chat.post_message(channel, ("%s has a new  %s review" % (appname, title)), icon_emoji=boticon, username=username, as_user=False,attachments=msg_body)




# URLS
app = webapp2.WSGIApplication([('/reviews', ReviewsHandler)],
                              debug=True)

            