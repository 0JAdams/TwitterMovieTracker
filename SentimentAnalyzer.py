import pickle
from nltk.classify import ClassifierI
from nltk.stem import PorterStemmer
from statistics import mode
from nltk.tokenize import word_tokenize


# This script is uses our trained sentiment classifiers to classify a string of text
# it is called by our twitterCheckerToSQL.py script

# todo combine classify and confidence methods so we aren't duplicating work
class VoteClassifier(ClassifierI):
    def __init__(self, *classifiers):
        self._classifiers = classifiers

    def classify(self, features):
        votes = []
        for c in self._classifiers:
            v = c.classify(features)
            votes.append(v)
        result = mode(votes)
        return result.lower()

    def confidence(self, features):
        votes = []
        for c in self._classifiers:
            v = c.classify(features)
            votes.append(v)

        choice_votes = votes.count(mode(votes))
        conf = choice_votes / len(votes)
        return conf


word_features_io = open("pickled_objects/wordfeatures_all_for25k_stemmed.pickle", "rb")
word_features = pickle.load(word_features_io)
word_features_io.close()

ps = PorterStemmer()

def find_features(document):
    words = word_tokenize(document)
    features = {}
    for i, word in enumerate(words):  # we stem the words to reduce the size of the feature set This is supposed to improve performance
        words[i] = ps.stem(word)
    for w in word_features:
        features[w] = (w in words)

    return features

# load the classifiers that we are going to use

NB_open = open("pickled_objects/naive_bayes_stemmed_25k.pickle", "rb")
NB_classifier = pickle.load(NB_open)
NB_open.close()

MNB_open = open("pickled_objects/MNB_stemmed_25k.pickle", "rb")
MNB_classifier = pickle.load(MNB_open)
MNB_open.close()

BNB_open = open("pickled_objects/BNB_stemmed_25k.pickle", "rb")
BNB_classifier = pickle.load(BNB_open)
BNB_open.close()

LG_open = open("pickled_objects/LG_stemmed_25k.pickle", "rb")
LG_classifier = pickle.load(LG_open)
LG_open.close()

SGD_open = open("pickled_objects/SGD_stemmed_25k.pickle", "rb")
SGD_classifier = pickle.load(SGD_open)
SGD_open.close()

LSVC_open = open("pickled_objects/LSVC_stemmed_25k.pickle", "rb")
LSVC_classifier = pickle.load(LSVC_open)
LSVC_open.close()

NSVC_open = open("pickled_objects/NSVC_stemmed_25k.pickle", "rb")
NSVC_classifier = pickle.load(NSVC_open)
NSVC_open.close()

# SVC_open = open("pickled_objects/SVC_stemmed_25k.pickle", "rb")
# SVC_classifier = pickle.load(SVC_open)
# SVC_open.close()

voted_classifier = VoteClassifier(NB_classifier, MNB_classifier, BNB_classifier, LG_classifier, SGD_classifier,
                                  LSVC_classifier, NSVC_classifier)


def check_sentiment(text):
    text_features = find_features(text)
    return voted_classifier.classify(text_features), voted_classifier.confidence(text_features)

