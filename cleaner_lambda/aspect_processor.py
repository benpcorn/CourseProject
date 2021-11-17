import os
from string import punctuation
import re
from textblob import TextBlob, Word
import nltk
from nltk.corpus import wordnet as wn
import pandas as pd
import spacy
nltk.download('vader_lexicon')
nlp = spacy.load('en_core_web_lg')

en_stop = set(nltk.corpus.stopwords.words('english'))

def load_data(file_name):
    file = open("/Users/benjcorn/Desktop/UIUC/CS410/CourseProject/cleaner_lambda/B08HRLQ9ZG_small.txt")
    text_data = []
    with file as f:
        for line in f:
            text_data.append(line)
    return text_data

def clean_sentence(sentence):
    sentence = sentence.lower()
    sent = TextBlob(sentence)
    #sent.correct()
    clean = ""
    for sentence in sent.sentences:    
        words = sentence.words
        words = [''.join(c for c in s if c not in punctuation) for s in words]
        words = [s for s in words if s]
        words = [word for word in words if word not in en_stop]
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

data = load_data("B08HRLQ9ZG_tiny.txt")
result = [clean_sentence(x) for x in data]
reviews = TextBlob(' '.join(result))
pruned = prune(reviews)

feature_count = dict()

for phrase in pruned:
    count = 0
    for word in phrase.split():
        if word not in en_stop:
            count += reviews.words.count(word)
    
    print(phrase + ": " + str(count))
    feature_count[phrase] = count

counts = list(feature_count.values())
features = list(feature_count.keys())
noun_chunks = []
for chunk in nlp(' '.join(pruned)).noun_chunks:
    noun_chunks.append(chunk)
threshold = len(noun_chunks) / 100

frequent_features = list()

for feature, count in feature_count.items():
    s = feature.split()
    if count >= threshold and len(s) >= 2 and len(s) <= 3:
        frequent_features.append(feature)

print(' Features:')
frequent_features=frequent_features[0:11]
frequent_features

def nltk_sentiment(sentence):
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    
    nltk_sentiment = SentimentIntensityAnalyzer()
    score = nltk_sentiment.polarity_scores(sentence)
    return score

nltk_results = [nltk_sentiment(row) for row in frequent_features]
results_df = pd.DataFrame(nltk_results)
text_df = pd.DataFrame(frequent_features)
nltk_df = text_df.join(results_df)

newdf=nltk_df[0]
newdf=pd.DataFrame({'features':nltk_df[0],'pos':nltk_df['pos'],'neg':nltk_df['neg']})
newdf.pos=newdf.pos+0.2
newdf.neg=newdf.neg-0.2
newdf