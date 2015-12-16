import mysql.connector
from mysql.connector import errorcode
import re
import string
import collections
import numpy as np
import matplotlib.dates as mdates
from sklearn import tree
import pickle

# this script pulls our twitter data from the DB, processes it into the feature sets used for our decision tree
# and builds the decision tree and then serializes it for later use


# add mysql db info here
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

# list of movies to used in TRAINING set
movieList = ("Bridge of Spies", "Crimson Peak", "Sicario", "Spectre", "Star Wars Episode VII",
             "Steve Jobs", "The Hunger Games: Mockingjay - Part 2", "The Last Witch Hunter",
             "Woodlawn")


releaseDateSQL = ("SELECT releaseDate FROM movies WHERE movieName = '%s'")

boxOfficeSQL = ("SELECT * FROM boxOffice WHERE movie_Name = '%s'")

featureSets = []  # this will store all of the feature sets for training
boxOfficePercentages = []  # this will store all of the class results for training
boxOfficePercentagesRounded = []  # this is used to more closely group similar percentages and improve our classifier
featureSetsTest = []  # this will store a subset of feature sets used for testing our trained classifier
boxOfficePercentagesTest = []  # this will store the matching percentages for those tests
boxOfficePercentagesTestRounded = []
# movie = movieList[5]


# function used to convert our dates to a format that can be used
def bytespdate2num(fmt, encoding='utf-8'):
    strconverter = mdates.strpdate2num(fmt)

    def bytesconverter(b):
        s = b.decode(encoding)
        return strconverter(s)
    return bytesconverter


# TODO: break this giant mess of a loop out into functions

# process all of the data we have for each movie
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

    # Prepare box office numbers to be in same format as other data
    if boxOfficeValuesOnly:  # only process them if they exist
        # Convert movie numbers to collection
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

    ###################################################################################################################
    # convert our daily data into weekly data with the beginning of week 1 being the release date.  week 0 will be the week leading up to that.
    ###################################################################################################################

    # find release date in sentiment data so we know what day of week our weeks start
    foundReleaseDate = False
    week1StartDate = 0
    week1Start = 0
    maxDate = max(dates)
    minDate = min(dates)
    for i, date in enumerate(dates):
        if date == releaseDateFormatted:
            week1StartDate = date
            week1Start = i
            foundReleaseDate = True


    # if found, release date falls in the period we have been watching
    weeks = []
    netSentimentByWeeks = []
    posSentimentByWeeks = []
    negSentimentByWeeks = []
    totalTwitterInterest = []
    netSentHolder = 0
    posSentHolder = 0
    negSentHolder = 0
    totalInterestHolder = 0
    startSpot = week1Start
    startingOn0 = False
    weekCount = 0

    if foundReleaseDate:  # use release date/start spot to break data into weeks
        if week1Start - 7 > 0:  # we need to know if we started tracking twitter at least a full week before release or not for opening weekend prediction
                                # and we don't want to include day 0 because it may have been a partial day's data
            startSpot = week1Start - 7
            startingOn0 = True

        if not startingOn0:
            weekCount = 1

        for i in range(startSpot, len(dates), 7):  # we don't want to include the last day as it may be incomplete
                netSentHolder = 0
                posSentHolder = 0
                negSentHolder = 0
                totalInterestHolder = 0
                if i + 7 <= len(dates):  # make certain our i+j stays in bounds of arrays
                    for j in range(0, 7):
                        netSentHolder += weights[i+j]
                        posSentHolder += posWeights[i+j]
                        negSentHolder += negWeights[i+j]
                        totalInterestHolder += posWeights[i+j] + negWeights[i+j]
                    netSentimentByWeeks.append(netSentHolder)
                    posSentimentByWeeks.append(posSentHolder)
                    negSentimentByWeeks.append(negSentHolder)
                    totalTwitterInterest.append(totalInterestHolder)
                    weeks.append(weekCount)
                    weekCount += 1

    # if not found, release date is either before or after the dates we have data for
    # handle release date is before scenario
    weekGapCount = 0
    sentimentStartDayIndex = 0
    if minDate > releaseDateFormatted:     # figure out our first day that lines up with the beginning of a week, and how many weeks have already occurred
        if (minDate - releaseDateFormatted) % 7 == 0:
            weekGapCount = int((minDate - releaseDateFormatted) / 7)
        else:
            weekGapCount = int(((minDate - releaseDateFormatted) / 7) + 1)  # if our dates start in the middle of a week, our first week will be the full weeks missed, plus one

        for i in range(1, 8):  # we don't want to start with day 0 because it may be a partial day
            if (dates[i] - releaseDateFormatted) % 7 == 0:
                sentimentStartDayIndex = i
                break

        weekCount = weekGapCount + 1
        # group all our data into weeks
        for i in range(sentimentStartDayIndex, len(dates), 7):  # we don't want to include the last day as it may be incomplete
                netSentHolder = 0
                posSentHolder = 0
                negSentHolder = 0
                totalInterestHolder = 0
                if i + 7 <= len(dates):  # make certain our i+j stays in bounds of arrays
                    for j in range(0, 7):
                        netSentHolder += weights[i+j]
                        posSentHolder += posWeights[i+j]
                        negSentHolder += negWeights[i+j]
                        totalInterestHolder += posWeights[i+j] + negWeights[i+j]
                    netSentimentByWeeks.append(netSentHolder)
                    posSentimentByWeeks.append(posSentHolder)
                    negSentimentByWeeks.append(negSentHolder)
                    totalTwitterInterest.append(totalInterestHolder)
                    weeks.append(weekCount)
                    weekCount += 1

    # handle release date is after scenario...  This data can't be used in week-to-week predicting, or release week predicting, so do we care about it?
    # the one case would be if the opening day is exactly 1 day after the end of our dates array. Then we would have a full week to predict with.
    # for now we will just ignore it
    # if maxDate < releaseDateFormatted:

    # group boxOfficeData into matching weeks
    # An alternative to this would be to update the scraper to scrape weekly earnings, but since we already have
    # the daily values, this is an easy solution.
    # since the week count is defined as starting at week 1 with the release date, then we will always start with week 1
    boxOfficeWeeks = []
    boxOfficeEarningsByWeeks = []
    currentWeek = 1
    for i in range(0, len(boxOfficeValue)+1, 7):
        boxOfficeWeekEarnings = 0
        if i+7 <= len(boxOfficeValue) + 1:
            for j in range(0, 7):
                boxOfficeWeekEarnings += boxOfficeValue[i+j]
            boxOfficeEarningsByWeeks.append(boxOfficeWeekEarnings)
            boxOfficeWeeks.append(currentWeek)
            currentWeek += 1

    # Determine our features from this data
    # Features:
    # Total interest/engagement gauged by total count of tweets We already have this one in the totalTwitterInterest object
    # Total interest change, week over week.  This will be classified as, falling, -1, rising, 1, and roughly steady, 0 (only a small change week to week)
    # We will define the roughly steady, or flat, interest as a change of less than 5% from week to week.
    interestChangeByWeek = []
    interestChangeRateByWeek = []
    interestChangeByWeek.append(0)  # we will consider the first weeks as 0 since we have no data before
    interestChangeRateByWeek.append(0)
    interestChangePercentageByWeek = []
    interestChangePercentageByWeek.append(0)
    for i, value in enumerate(totalTwitterInterest[1:]):
        percentageChange = ((totalTwitterInterest[i+1] - totalTwitterInterest[i]) / totalTwitterInterest[i]) * 100
        interestChangePercentageByWeek.append(round(percentageChange, -1))  # round percent to nearest 10
        # interestChangePercentageByWeek.append(round(percentageChange/2, -1)*2)  # round percent to nearest 20
        if (abs(totalTwitterInterest[i+1] - totalTwitterInterest[i]) / totalTwitterInterest[i]) * 100 <= 5:
            interestChangeByWeek.append(0)
            interestChangeRateByWeek.append(0)
        elif totalTwitterInterest[i+1] > totalTwitterInterest[i]:
            interestChangeByWeek.append(1)
            if (abs(totalTwitterInterest[i+1] - totalTwitterInterest[i]) / totalTwitterInterest[i]) * 100 <= 50:
                interestChangeRateByWeek.append(-1)  # -1 for slow
            else:
                interestChangeRateByWeek.append(1)  # 1 for fast
        else:
            interestChangeByWeek.append(-1)
            if (abs(totalTwitterInterest[i+1] - totalTwitterInterest[i]) / totalTwitterInterest[i]) * 100 <= 50:
                interestChangeRateByWeek.append(-1)  # -1 for slow
            else:
                interestChangeRateByWeek.append(1)  # 1 for fast



    # Sentiment, neg -1, pos 1, close to even 0.  We will define close to even as the abs(net) being < 5% of the total number of tweets
    sentimentClassByWeek = []
    for i, week in enumerate(netSentimentByWeeks):
        if ((abs(week) / totalTwitterInterest[i]) * 100) <= 5:
            sentimentClassByWeek.append(0)
        elif week > 0:
            sentimentClassByWeek.append(1)
        else:
            sentimentClassByWeek.append(-1)

    # Sentiment Change: falling, rising, flat  We will define flat as having a change <= 5%
    sentimentChangeByWeek = []
    sentimentChangeByWeek.append(0)
    for i, value in enumerate(netSentimentByWeeks[1:]):  # skip week 0 because it won't have a preceding week to compare to
        if (abs(netSentimentByWeeks[i+1] - netSentimentByWeeks[i]) / netSentimentByWeeks[i]) * 100 <= 5:
            sentimentChangeByWeek.append(0)
        elif netSentimentByWeeks[i+1] > netSentimentByWeeks[i]:
            sentimentChangeByWeek.append(1)
        else:
            sentimentChangeByWeek.append(-1)

    # Box Office Change Percentage:  This is what we want to predict.  How much a movie will fall each week based on these features
    boxOfficeChangePercentageByWeek = []
    boxOfficeChangePercentageByWeek.append(0)  # none for first week
    for i, value in enumerate(boxOfficeEarningsByWeeks[1:]):
        percentageChange = ((boxOfficeEarningsByWeeks[i+1] - boxOfficeEarningsByWeeks[i]) / boxOfficeEarningsByWeeks[i]) * 100
        boxOfficeChangePercentageByWeek.append(percentageChange)

    # Add the features for this movie to the training set array
    # After a movie has been out for a long time it will no longer be tracked because it stops being in many theaters.
    # We need to only add the weeks that we have both twitter data AND box office data
    for i, weekNum in enumerate(weeks):
        if weekNum-1 < len(boxOfficeEarningsByWeeks):
            newSet = [interestChangeByWeek[i], interestChangePercentageByWeek[i], sentimentClassByWeek[i], sentimentChangeByWeek[i]]
            if i == len(weeks) - 1:  # keep the last week of each movie for testing against the classifier
                featureSetsTest.append(newSet)
                boxOfficePercentagesTest.append(boxOfficeChangePercentageByWeek[weekNum-1])
                boxOfficePercentagesTestRounded.append(round(boxOfficeChangePercentageByWeek[weekNum-1], -1))  # round percent to nearest 10
            else:
                featureSets.append(newSet)
                boxOfficePercentages.append(boxOfficeChangePercentageByWeek[weekNum-1])
                boxOfficePercentagesRounded.append(round(boxOfficeChangePercentageByWeek[weekNum-1], -1))  # round percent to nearest 10


    print(featureSets)
    print(boxOfficePercentages)
    print(boxOfficePercentagesRounded)


#############
# End of data preprocessing loop
#############

featureNames = ["Interest Change", "Interest Change Percentage", "Net Sentiment", "Sentiment Change"]
className = ["Box Office Change Percent"]


# use gathered training data to train our classifier

dtclassifier = tree.DecisionTreeClassifier()
dtclassifier = dtclassifier.fit(featureSets, boxOfficePercentagesRounded)

save_classifier = open("pickled_objects/dtclassifier.pickle", "wb")
pickle.dump(dtclassifier, save_classifier)
save_classifier.close()

print("Classifier created and saved as Pickle for future use")
tree.export_graphviz(dtclassifier, out_file='tree.dot',
                     feature_names=featureNames)

for i, test in enumerate(featureSetsTest):
    print("results: ", dtclassifier.predict(test), " Actual: ", boxOfficePercentagesTestRounded[i])

print(dtclassifier.score(featureSetsTest, boxOfficePercentagesTestRounded))


