import csv
import time
import logging
import datetime
import re
from datetime import tzinfo
import pytz
from pytz import timezone
from dateutil import parser
from twitter import *

logger = logging.getLogger("root")
logging.basicConfig(
    format = "\033[1;36m%(levelname)s: %(filename)s (def %(funcName)s %(lineno)s): \033[1;37m %(message)s",
    level=logging.DEBUG
)

TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""
LOCAL_TIMEZONE = pytz.timezone("US/Eastern")
TWITTER_TIMEZONE = timezone("UTC")

class TwitterHashtagSearch(object):

    # you can really only search back 6 or 7 days
    start_date_for_search = LOCAL_TIMEZONE.localize(datetime.datetime(2015, 3, 2, 8, 0))

    # hashtag to search
    hashtag = "#NICAR15"

    # column names for our csv
    # this will change if you pull in more data
    csv_headers = [
        "hashtag",
        "tweet_utc_date",
        "user_name",
        "user_screen_name",
        "bot_or_not",
        "tweet_text",
        "tweet_url",
        "tweet_id",
        "user_profile_image_url",
        "user_location",
        "source",
        "in_reply_to_screen_name",
        "in_reply_to_status_id",
        "image_link",
        "retweet_count",
        "favorite_count",
        "time_zone",
        "geo_enabled",
        "geography",
        "coordinates",
        "lang",
    ]

    # what we'll name our csv file
    csv_filename = "_%s_tweets.csv" % (hashtag)

    def _init(self, *args, **kwargs):
        """
        start the whole twitter hashtag search a rollin
        """
        # default params for our loop
        max_id = None
        search_is_done = False

        # set our date defaults for comparisons
        start_date_utc = self.start_date_for_search.astimezone(TWITTER_TIMEZONE)

        # open the csv file
        with open(self.csv_filename, "wb") as csv_file:

            csv_output = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)

            # write the header row to the csv file
            csv_output.writerow(self.csv_headers)

            # begin the loop
            while (search_is_done == False):

                # return our tweets
                tweet_results = self.construct_twitter_search(self.hashtag, max_id)

                # for each status
                for tweet in tweet_results["statuses"]:

                    #print tweet

                    # get the UTC time for each
                    tweet_date = parser.parse(tweet["created_at"])

                    # set some timezone information
                    tweet_date = tweet_date.replace(tzinfo=TWITTER_TIMEZONE)

                    # if the tweet falls between our begin and end range
                    if tweet_date >= start_date_utc:

                        # build a new csv row
                        csv_row = self.build_csv_row_from(tweet, tweet_date)

                        # write the new csv row
                        csv_output.writerow(csv_row)

                # if we get through the loop get the new max id, which is in effect paging
                max_id = self.get_max_id(tweet_results)

                # if no max_id
                if max_id == None:

                    # end the loop
                    search_is_done = True

                # otherwise
                else:

                    # get more of them
                    print "Retrieving more tweets since %s" % (max_id)

    def construct_twitter_search(self, hashtag, max_id):
        """
        function to auth with twitter and return tweets
        """
        twitter_object = Twitter(
            auth=OAuth(
                TWITTER_ACCESS_TOKEN,
                TWITTER_ACCESS_TOKEN_SECRET,
                TWITTER_CONSUMER_KEY,
                TWITTER_CONSUMER_SECRET
            )
        )

        tweet_results = twitter_object.search.tweets(
            q=hashtag,
            count=1000,
            result_type="recent",
            include_entities=True,
            max_id=max_id,
            lang="en"
        )
        return tweet_results

    def build_csv_row_from(self, tweet, tweet_date):
        """
        create a csv row from tweet results
        """

        # construct url format
        tweet_url = "https://twitter.com/" + tweet["user"]["screen_name"].encode('ascii', 'ignore') + "/status/" + str(tweet["id"])

        # output some information
        print "%s - %s - %s" % (
            tweet_date,
            tweet["user"]["screen_name"],
            tweet_url,
        )

        has_image = tweet.has_key("media")

        # if there are more
        if has_image == True:
            tweet_image = tweet["media"]["media_url_https"]
        else:
            tweet_image = None

        # build a row of tweet data
        csv_row_data = [
            self.hashtag,
            tweet_date,
            tweet["user"]["name"].encode('ascii', 'ignore'),
            tweet["user"]["screen_name"].encode('ascii', 'ignore'),
            self.check_text_for_bot(tweet["text"].encode('ascii', 'ignore')),
            tweet["text"].encode('ascii', 'ignore'),
            tweet_url.encode('ascii', 'ignore'),
            tweet["id"],
            tweet["user"]["profile_image_url"].encode('ascii', 'ignore'),
            tweet["user"]["location"].encode('ascii', 'ignore'),
            tweet["source"].encode('ascii', 'ignore'),
            tweet["in_reply_to_screen_name"],
            tweet["in_reply_to_status_id_str"],
            tweet_image,
            tweet["retweet_count"],
            tweet["favorite_count"],
            tweet["user"]["time_zone"],
            tweet["user"]["geo_enabled"],
            tweet["geo"],
            tweet["coordinates"],
            tweet["lang"],
        ]

        # return the row
        print csv_row_data
        return csv_row_data

    def check_text_for_bot(self, tweet_text):
        """
        let's see if we can indentify a bot
        """
        bot_check = re.compile("#NICAR15 View here ")
        bot_match = re.search(bot_check, tweet_text)
        try:
            if bot_match:
                is_bot = True
            else:
                is_bot = False
        except:
            is_bot = None
        return is_bot

    def get_max_id(self, results):
        """
        get the max_id of the next twitter search if present
        """
        # see if the metadata has a next_results key
        # value is the idea to pull tweets from
        more_tweets = results["search_metadata"].has_key("next_results")

        # if there are more
        if more_tweets == True:

            # find the max id
            parsed_string = results["search_metadata"]["next_results"].split("&")
            parsed_string = parsed_string[0].split("?max_id=")
            max_id = parsed_string[1]
        else:
            max_id = None

        # return the max id
        return max_id

if __name__ == '__main__':
    task_run = TwitterHashtagSearch()
    task_run._init()
    print "\nTask finished at %s\n" % str(datetime.datetime.now())
