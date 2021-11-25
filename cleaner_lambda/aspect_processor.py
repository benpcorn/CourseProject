from string import punctuation
from textblob import TextBlob, Word
import nltk
from nltk.corpus import wordnet as wn
import pandas as pd
import spacy

nltk.download('vader_lexicon')
nlp = spacy.load('en_core_web_lg')
en_stop = set(nltk.corpus.stopwords.words('english'))

def load_data(file_name):
    file = open(file_name)
    text_data = []
    with file as f:
        for line in f:
            text_data.append(line)
    return text_data

def clean_sentence(sentence):
    print("Cleaning sentence of length: " + str(len(sentence)))
    sentence = sentence.lower()
    sent = TextBlob(sentence)
    clean = ""
    for sentence in sent.sentences:    
        words = sentence.words
        words = [''.join(c for c in s if c not in punctuation) for s in words]
        words = [s for s in words if s]
        words = [word for word in words if word not in en_stop]
        words = [word for word in words if word not in "arlo ultra 2 spotlight camera".split()]
        clean += " ".join(words)
        clean += ". "
    return clean

def prune(collection):
    print("Pruning collection of length: " + str(len(collection)))
    cleaned = list()
    for phrase in collection.noun_phrases:
        count = 0
        for word in phrase.split():
            if len(word) <= 2 or (not Word(word).definitions):
                count += 1
        if count < len(phrase.split())*0.4:
            cleaned.append(phrase)
    return cleaned

def calc_feature_count(pruned, raw_reviews):
    feature_count = dict()
    for phrase in pruned:
        count = 0
        for word in phrase.split():
            if word not in en_stop:
                count += raw_reviews.words.count(word)
        
        feature_count[phrase] = count
    return feature_count

def count_frequent_features(feature_count):
    frequent_features = list()
    feature_count = {k: v for k, v in sorted(feature_count.items(), key=lambda item: item[1], reverse=True)}
    for feature, count in feature_count.items():
        s = feature.split()
        if len(s) >= 2 and len(s) <= 5:
            frequent_features.append(feature)

    frequent_features = frequent_features[0:9]
    return frequent_features

def nltk_sentiment(sentence):
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    nltk_sentiment = SentimentIntensityAnalyzer()
    score = nltk_sentiment.polarity_scores(sentence)
    return score