import nltk
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.naive_bayes import MultinomialNB, GaussianNB, BernoulliNB
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import SVC, LinearSVC, NuSVC
import random
import pickle

# this script will open our feature set created by featuresetBuilder.py and use that to train all of our classifiers
# the classifiers will each be serialized and saved for use later

featuresets_io = open("pickled_objects/featuresets25k_stemmed.pickle", "rb")
featuresets = pickle.load(featuresets_io)
featuresets_io.close()

random.shuffle(featuresets)
random.shuffle(featuresets)
random.shuffle(featuresets)

# positive data example:
training_set = featuresets[:24000]
testing_set = featuresets[24000:]

# posterior = prior occurrences * likelihood / evidence

# Original Naive Bayes algorithm:
NB_classifier = nltk.NaiveBayesClassifier.train(training_set)
NB_classifier.show_most_informative_features(25)

save_naive_bayes_classifier = open("pickled_objects/naive_bayes_stemmed_25k.pickle", "wb")
pickle.dump(NB_classifier, save_naive_bayes_classifier)
save_naive_bayes_classifier.close()
print("Original Naive Bayes algo accuracy percent: %", (nltk.classify.accuracy(NB_classifier, testing_set))*100)

# Multinomial Naive Bayes algorithm:
MNB_classifier = SklearnClassifier(MultinomialNB())
MNB_classifier.train(training_set)

save_MNB_classifier = open("pickled_objects/MNB_stemmed_25k.pickle", "wb")
pickle.dump(MNB_classifier, save_MNB_classifier)
save_MNB_classifier.close()
print("MNB algo accuracy percent: %", (nltk.classify.accuracy(MNB_classifier, testing_set))*100)

# Bernoulli Naive Bayes algorithm:
BNB_classifier = SklearnClassifier(BernoulliNB())
BNB_classifier.train(training_set)

save_BNB_classifier = open("pickled_objects/BNB_stemmed_25k.pickle", "wb")
pickle.dump(BNB_classifier, save_BNB_classifier)
save_BNB_classifier.close()
print("BNB algo accuracy percent: %", (nltk.classify.accuracy(BNB_classifier, testing_set))*100)

# Logistic Regression algorithm:
LG_classifier = SklearnClassifier(LogisticRegression())
LG_classifier.train(training_set)

save_LG_classifier = open("pickled_objects/LG_stemmed_25k.pickle", "wb")
pickle.dump(LG_classifier, save_LG_classifier)
save_LG_classifier.close()
print("LG algo accuracy percent: %", (nltk.classify.accuracy(LG_classifier, testing_set))*100)

# SGD_algorithm:
SGD_classifier = SklearnClassifier(SGDClassifier())
SGD_classifier.train(training_set)

save_SGD_classifier = open("pickled_objects/SGD_stemmed_25k.pickle", "wb")
pickle.dump(SGD_classifier, save_SGD_classifier)
save_SGD_classifier.close()
print("SGD algo accuracy percent: %", (nltk.classify.accuracy(SGD_classifier, testing_set))*100)

# Linear SVC algorithm:
LSVC_classifier = SklearnClassifier(LinearSVC())
LSVC_classifier.train(training_set)

save_LSVC_classifier = open("pickled_objects/LSVC_stemmed_25k.pickle", "wb")
pickle.dump(LSVC_classifier, save_LSVC_classifier)
save_LSVC_classifier.close()
print("LSVC algo accuracy percent: %", (nltk.classify.accuracy(LSVC_classifier, testing_set))*100)

# Nu SVC algorithm:
NSVC_classifier = SklearnClassifier(NuSVC())
NSVC_classifier.train(training_set)

save_NSVC_classifier = open("pickled_objects/NSVC_stemmed_25k.pickle", "wb")
pickle.dump(NSVC_classifier, save_NSVC_classifier)
save_NSVC_classifier.close()
print("NSVC algo accuracy percent: %", (nltk.classify.accuracy(NSVC_classifier, testing_set))*100)

# SVC algorithm:
SVC_classifier = SklearnClassifier(SVC())
SVC_classifier.train(training_set)

save_SVC_classifier = open("pickled_objects/SVC_stemmed_25k.pickle", "wb")
pickle.dump(SVC_classifier, save_SVC_classifier)
save_SVC_classifier.close()
print("SVC algo accuracy percent: %", (nltk.classify.accuracy(SVC_classifier, testing_set))*100)

