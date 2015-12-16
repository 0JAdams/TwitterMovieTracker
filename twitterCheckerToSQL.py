import SentimentAnalyzer as SA
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import mysql.connector
from mysql.connector import errorcode
import json
import re
import string
import time
from unidecode import unidecode

# This script pulls a stream of relevant tweets from Twitter, runs the sentiment analyzer on it and stores the
# results in our mySQL DB.

# print(SA.check_sentiment("Is anyone going to see the Martian? I am so excited for it. It looks awesome!"))
# print(SA.check_sentiment("I don't understand why people are excited for The Martian. It looks so boring."))


# create mySQL connection.  This needs connection info for the DB being used
try:
    cnx = mysql.connector.connect(user='', password='', host='', database='')
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("something is wrong with the SQL username or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

# these are the keys provided by Twitter to have access to the API.  This must be filled in with your own keys
access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""

cursor = cnx.cursor()

# this is our SQL for adding the tweetID and results into our DB
add_tweet = ("INSERT INTO tweets"
             "(tweetID, movies_movieName, dateTime, result, confidence)"
             "VALUES (%s, %s, %s, %s, %s)")


# Twitter's results just give us back the tweet, but don't tell us which keyword it was found with
# so, we have to use a keyword dictionary to search the tweet and match it back up to the movie
movieKeywordDict = dict()
movieKeywordDict['bridge'] = 'Bridge of Spies'
movieKeywordDict['spies'] = 'Bridge of Spies'
movieKeywordDict['crimson'] = 'Crimson Peak'
movieKeywordDict['peak'] = 'Crimson Peak'
movieKeywordDict['goosebumps'] = 'Goosebumps'
movieKeywordDict['pan'] = 'Pan'
movieKeywordDict['sicario'] = 'Sicario'
movieKeywordDict['star'] = 'Star Wars Episode VII'
movieKeywordDict['wars'] = 'Star Wars Episode VII'
movieKeywordDict['episode'] = 'Star Wars Episode VII'
movieKeywordDict['vii'] = 'Star Wars Episode VII'
movieKeywordDict['force'] = 'Star Wars Episode VII'
movieKeywordDict['awakens'] = 'Star Wars Episode VII'
movieKeywordDict['steve'] = 'Steve Jobs'
movieKeywordDict['jobs'] = 'Steve Jobs'
movieKeywordDict['intern'] = 'The Intern'
movieKeywordDict['last'] = 'The Last Witch Hunter'
movieKeywordDict['witch'] = 'The Last Witch Hunter'
movieKeywordDict['hunter'] = 'The Last Witch Hunter'
movieKeywordDict['martian'] = 'The Martian'
movieKeywordDict['woodlawn'] = 'Woodlawn'
movieKeywordDict['spectre'] = 'Spectre'
movieKeywordDict['trumbo'] = 'Trumbo'
movieKeywordDict['hallow'] = 'The Hallow'
movieKeywordDict['hunger'] = 'The Hunger Games: Mockingjay - Part 2'
movieKeywordDict['mockingjay'] = 'The Hunger Games: Mockingjay - Part 2'
movieKeywordDict['games'] = 'The Hunger Games: Mockingjay - Part 2'



# excludeItems = set(string.puncuation)
regex = re.compile('[%s]' % re.escape(string.punctuation))


class twitter_listener(StreamListener):

    def on_data(self, data):
        all_data = json.loads(data)
        if 'text' in all_data:
            tweet = all_data['text']
            tweet = unidecode(tweet)
            tweetNoPunctuation = regex.sub('', tweet)

            if not all_data['retweeted'] and not tweet.startswith('RT') and 't.co' not in tweet:
                sentiment_value, confidence = SA.check_sentiment(tweetNoPunctuation)
                print(tweet, sentiment_value, confidence)

                found = False
                movie_name = ""
                for word in tweetNoPunctuation.split(" "):  # find which movie this tweet was about
                    if word.lower() in movieKeywordDict.keys():
                        movie_name = movieKeywordDict[word.lower()]
                        # print("------------------Found keyword: ", word, " belongs to movie: ", movie_name)
                        found = True
                        break

                if found:
                    created_at = time.strftime('%Y-%m-%d %H:%M:%S')  # we will just use current time since we are pulling in a live feed and that should be close enough
                    tweet_data = (all_data['id_str'], movie_name, created_at, tweet, sentiment_value.lower(), confidence)
                    try:
                        cursor.execute(add_tweet, tweet_data)
                        cnx.commit()
                    except mysql.connector.Error as err:
                        print("SQL transaction failed")

        return True

    def on_limit(self, track):
        print('Limit hit! Track = %s' % track)
        return True

    def on_error(self, status):
        print(status)

    def on_disconnect(self, notice):
        print(notice)


# create our authorization to connect to Twitter
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# create our stream and tie it to our stream listener code
twitterStream = Stream(auth, twitter_listener())

# give twitter our list of keywords to search for
twitterStream.filter(track=["martian", "crimson peak", "spectre", "trumbo", "the hallow", "the hunger games", "mockingjay part 2", "goosebumps", "sicario", "star wars episode VII", "force awakens", "steve jobs", "intern", "Last Witch Hunter", "woodlawn"], languages=["en"])


cursor.close()
cnx.close()
