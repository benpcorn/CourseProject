import sys
import aspect_processor as ap
from textblob import TextBlob, Word
import nltk
from nltk.corpus import wordnet as wn
import pandas as pd

data = ap.load_data("/Users/benjcorn/Desktop/UIUC/CS410/CourseProject/cleaner_lambda/B08HRLQ9ZG_tiny.txt")
result = [ap.clean_sentence(x) for x in data]
reviews = TextBlob(' '.join(result))
pruned = ap.prune(reviews)

feature_count = ap.calc_feature_count(pruned, reviews)

counts = list(feature_count.values())
features = list(feature_count.keys())
threshold = len(reviews.noun_phrases)/100

frequent_features = ap.count_frequent_features(feature_count)
print(frequent_features)

nltk_results = [ap.nltk_sentiment(row) for row in frequent_features]
results_df = pd.DataFrame(nltk_results)
text_df = pd.DataFrame(frequent_features)
nltk_df = text_df.join(results_df)

newdf=nltk_df[0]
newdf=pd.DataFrame({'features':nltk_df[0],'pos':nltk_df['pos'],'neg':nltk_df['neg']})
newdf.pos=newdf.pos+0.2
newdf.neg=newdf.neg-0.2
print(newdf.head())