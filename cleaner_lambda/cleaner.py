import spacy
from spacy.lang.en import English
import nltk
import pandas as pd
import os

nltk.download('wordnet')
nltk.download('stopwords')
nlp = spacy.load('en_core_web_lg')

parser = English()
en_stop = set(nltk.corpus.stopwords.words('english'))

def get_aspects(text):
    doc=nlp(text)
    doc=[i.text for i in doc if i.text not in en_stop and (i.pos_=="NOUN" or i.pos_=="ADJECTIVE")]
    doc=list(map(lambda i: i.lower(),doc))
    doc=pd.Series(doc)
    doc=doc.value_counts().head().index.tolist()
    return doc

def load_data(file_name):
    file = open(os.path.join("../sample_reviews/", file_name))
    data = file.read()
    file.close()
    return data

# Driver
nlp.max_length = 1500000
text = load_data("B08HRLQ9ZG_small.txt")
aspects = get_aspects(text)
print(aspects)