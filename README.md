# [Twitter Movie Sentiment Tracker](http://0jadams.github.io/TwitterMovieTracker/)
## Version 0.0.0.1

**[Check website for more information](http://0jadams.github.io/TwitterMovieTracker/)**


### Files and Descriptions:
* **documentBuilder.py** - This is the first step in training the sentiment classifiers. It uses preclassified tweets and does some of the initial preprocessing of them. 
* **featuresetBuilder.py** - Continues the preprocessing of the training set and outputs a feature set to use for training.
* **SentimentTrainerFromPickles.py** - Uses the above feature set to train all of our different sentiment classifiers.  It then serializes and saves them to be used. 
* **SentimentAnalyzer.py** - Loads the stored sentiment classifiers and outputs the classification and confidence for a given string.
* **twitterCheckerToSQL.py** - Streams tweets from Twitter, processes them, uses the SentimentAnalyzer.py to classify them, and stores the results in an SQL DB.
* **ScrapeBoxOffice.py** - Pulls the release date and daily box office numbers for each movie from the web, and stores them in our SQL DB.
* **plotFromSQL.py** - Pulls all of the twitter results and box office data and plots it and stores those as .png files.
* **decisionTreeClassifierBuilder.py** - Pulls all of the data from the DB for selected movies, converts those into the feature set we are using, and uses that to build a decision tree. The decision tree is saved for future use.
* **boxOfficeDecisionTreeClassifier.py** - Loads the decision tree, pulls data for a given movie from the DB, process its data into the relevant features, and pass those features through the tree to get a week by week prediction of the next weeks box office performance change.

The **pickled_objects** folder holds copies of the classifiers output by the S**entimentTrainerFromPickles.py** script.  Those are loaded by the **SentimentAnalyzer.py** script and used to classify the text.  Those can be used instead of building and retraining everything from scratch, if desired.
