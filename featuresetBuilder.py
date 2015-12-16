from nltk.tokenize import word_tokenize
import pickle

# uses the pickles created by documentBuilder.py to create the training feature set
documents_io = open("pickled_objects/documents25k_stemmed.pickle", "rb")
documents = pickle.load(documents_io)
documents_io.close()

word_features_io = open("pickled_objects/wordfeatures_all_for25k_stemmed.pickle", "rb")
word_features = pickle.load(word_features_io)
word_features_io.close()


def find_features(document):
    words_in_document = word_tokenize(document)
    features = {}
    for w in word_features:
        features[w] = (w in words_in_document)

    return features


featuresets = [(find_features(rev), category) for (rev, category) in documents]

save_featuresets = open("pickled_objects/featuresets25k_stemmed.pickle", "wb")
pickle.dump(featuresets, save_featuresets)
save_featuresets.close()
