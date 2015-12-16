import mysql.connector
from mysql.connector import errorcode
import json
import re
import string
import time
import datetime
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from unidecode import unidecode

# This script pulls all of our results from mySQL and plots them by movie. This includes both the twitter data
# and the box office data


# insert your mySQL db info here
try:
    cnx = mysql.connector.connect(user='', password='', host='', database='')
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("something is wrong with the SQL username or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

cursor = cnx.cursor()

regex = re.compile('[%s]' % re.escape(string.punctuation))  # this will be used to remove punctuation

sql = ("SELECT * FROM tweets WHERE movies_movieName='%s'")

movieList = ("Bridge of Spies", "Crimson Peak", "Goosebumps", "Sicario", "Spectre", "Star Wars Episode VII",
             "Steve Jobs", "The Hunger Games: Mockingjay - Part 2", "The Intern", "The Last Witch Hunter",
             "The Martian", "Trumbo", "Woodlawn")

# movieList = ("The Hunger Games: Mockingjay - Part 2", "Sicario")

releaseDateSQL = ("SELECT releaseDate FROM movies WHERE movieName = '%s'")

boxOfficeSQL = ("SELECT * FROM boxOffice WHERE movie_Name = '%s'")

# movie = movieList[5]

for movie in movieList:
    graphArray = []
    boxOfficeArray = []
    boxOfficeValuesOnly = []  # this will just be used for normalizing
    combinedQuery = sql % movie

    # Get movie sentiment data by day
    cursor.execute(combinedQuery)

    for (tweetID, movies_movieName, dateTime, result, confidence) in cursor:
        rval = 0
        if result == 'neg':
            rval = -1
        elif result == 'pos':
            rval = 1
        graphArrayAppend = "{:%Y-%m-%d}, {}".format(dateTime, rval)
        graphArray.append(graphArrayAppend)
        # print(graphArrayAppend)

    # Get movie box office data by day
    cursor.execute(boxOfficeSQL % movie)

    for (movie_name, date, dollarsearned) in cursor:
        boxOfficeValuesOnly.append((date, int(dollarsearned)))


    # Get movie release date
    cursor.execute(releaseDateSQL % movie)

    releaseDate = cursor.fetchone()  # we only have one releaseDate per movie since the movie is the primary key

    # function used to convert our dates to a format that can be used
    def bytespdate2num(fmt, encoding='utf-8'):
        strconverter = mdates.strpdate2num(fmt)

        def bytesconverter(b):
            s = b.decode(encoding)
            return strconverter(s)
        return bytesconverter

    # Format twitter sentiment data and dates
    datestamp, value = np.loadtxt(graphArray, delimiter=',', unpack=True, converters={0: bytespdate2num('%Y-%m-%d')})

    # Format release date
    if releaseDate[0] is not None:
        releaseDateFormatted = np.loadtxt(releaseDate, unpack=True, converters={0: bytespdate2num('%Y-%m-%d')})

    resultsDict = collections.OrderedDict()
    posResultsDict = collections.OrderedDict()
    negResultsDict = collections.OrderedDict()

    #  break all of the sentiment results into a total bucket, a positive bucket, and a neg bucket.
    for i, v in enumerate(datestamp):
        if v in resultsDict.keys():
            resultsDict[v] += value[i]
        else:
            resultsDict[v] = value[i]

        if v in posResultsDict.keys():
            if value[i] > 0:
                posResultsDict[v] += 1
        else:
            if value[i] > 0:
                posResultsDict[v] = 1

        if v in negResultsDict.keys():
            if value[i] < 0:
                negResultsDict[v] += 1
        else:
            if value[i] < 0:
                negResultsDict[v] = 1

    # prepare box office values
    # Convert movie numbers to collection
    if boxOfficeValuesOnly:  # only process them if they exist
        for v in boxOfficeValuesOnly:
            boxOfficeArrayAppend = "{:%Y-%m-%d}, {}".format(v[0], v[1])
            boxOfficeArray.append(boxOfficeArrayAppend)
        # Format box office date and value
        boxOfficeDate, boxOfficeValue = np.loadtxt(boxOfficeArray, delimiter=',', unpack=True, converters={0: bytespdate2num('%Y-%m-%d')})



    dates = []
    weights = []
    posDates = []
    posWeights = []
    negDates = []
    negWeights = []

    # group sentiment values for plotting
    for key, value in resultsDict.items():
        dates.append(key)
        weights.append(value)

    for key, value in posResultsDict.items():
        posDates.append(key)
        posWeights.append(value)

    for key, value in negResultsDict.items():
        negDates.append(key)
        negWeights.append(value)

    fig = plt.figure(figsize=(15, 5), dpi=100)  # set our dimensions to ~1500x500px
    ax1 = fig.add_subplot(1, 1, 1, axisbg='white')
    ax1.set_xlabel('Date', fontsize=18)
    ax1.set_ylabel('Tweet Count', fontsize=18)
    fig.suptitle(movie, fontsize=22)
    ax1.grid(True)
    ax1.axhline(0, color='black', linewidth=2)
    ax1.plot_date(x=dates[1:-1], y=weights[1:-1], fmt='b-', label='Net Sentiment', linewidth=2)
    ax1.plot_date(x=negDates[1:-1], y=negWeights[1:-1], fmt='r-', label='Negative Tweets', linewidth=2)
    ax1.plot_date(x=posDates[1:-1], y=posWeights[1:-1], fmt='g-', label='Positive Tweets', linewidth=2)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Box Office ($)', fontsize=18)
    if boxOfficeValuesOnly:
        ax2.plot_date(x=boxOfficeDate, y=boxOfficeValue, fmt='k--', label='Box Office Earnings', linewidth=2)
    if releaseDate[0] is not None:
        ax2.axvline(x=releaseDateFormatted, ymin=0, ymax=1, label='Release Date', linewidth=4, color='m')
    x1min, x1max, y1min, y1max = ax1.axis()
    x2min, x2max, y2min, y2max = ax2.axis()
    newy2min = (y1min/y1max)*y2max
    v = [x2min, x2max, newy2min, y2max]
    ax2.axis(v)
    plt.tight_layout(rect=[.01, .01, .99, .95])  # adjust the figure padding
    # plt.show()  # use this to display the graph
    ax1.legend(loc=9)
    ax2.legend(loc=1)
    movieNameNoPunctuation = regex.sub('', movie)  # strip out puncuation so that it doesn't interfere with saving.
    fig.savefig('C:\\Users\\0jona\\Documents\\School\\Intelligent Systems\\plots\\%s_figure.png' % movieNameNoPunctuation)  # save graph to png


cursor.close()
cnx.close()
