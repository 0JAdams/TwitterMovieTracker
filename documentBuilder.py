import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import pickle

# these files are stored tweets, sorted into files by their sentiment
short_pos = open("short_reviews/positive_tweets.txt", "r", encoding="utf-8").read()
short_neg = open("short_reviews/negative_tweets.txt", "r", encoding="utf-8").read()

documents = []
all_words = []


#allowed word types:
allowed_word_types = ["J", "R", "V"]

ps = PorterStemmer()

for review in short_pos.split('\n')[80000:92500]:
    documents.append((review, "pos"))
    words = word_tokenize(review)
    for i, word in enumerate(words):  # we stem the words to reduce the size of the feature set This helps to improve performance
        words[i] = ps.stem(word)
    positive = nltk.pos_tag(words)
    for w in positive:
        if w[1][0] in allowed_word_types:
            all_words.append(w[0].lower())

for review in short_neg.split('\n')[80000:92500]:
    documents.append((review, "neg"))
    words = word_tokenize(review)
    for i, word in enumerate(words):  # we stem the words to reduce the size of the feature set This helps to improve performance
        words[i] = ps.stem(word)
    negative = nltk.pos_tag(words)
    for w in negative:
        if w[1][0] in allowed_word_types:
            all_words.append(w[0].lower())

save_documents = open("pickled_objects/documents25k_stemmed.pickle", "wb")
pickle.dump(documents, save_documents)
save_documents.close()

all_words = nltk.FreqDist(all_words)

word_features = list(all_words.keys())

save_word_features = open("pickled_objects/wordfeatures_all_for25k_stemmed.pickle", "wb")
pickle.dump(word_features, save_word_features)
save_word_features.close()
