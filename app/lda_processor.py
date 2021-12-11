import spacy
from spacy.lang.en import English
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
import gensim
from gensim.parsing.preprocessing import preprocess_string, strip_punctuation, strip_numeric
from gensim import corpora
import pickle
import numpy as np
from gensim.models import Phrases
from tinydb import TinyDB, Query, where
import logging
import json
import os

db = TinyDB('./db.json')
table = db.table('product_reviews')

nltk.download('wordnet')
nltk.download('stopwords')
nlp = spacy.load('en_core_web_sm')

parser = English()
en_stop = nltk.corpus.stopwords.words('english')

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

def tokenize(text):
    lda_tokens = []
    tokens = parser(text)
    for token in tokens:
        if token.orth_.isspace():
            continue
        else:
            lda_tokens.append(token.lower_)
    return lda_tokens

def get_lemma(word):
    lemma = wn.morphy(word)
    if lemma is None:
        return word
    else:
        return lemma

def get_lemma2(word):
    return WordNetLemmatizer().lemmatize(word)

def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    """https://spacy.io/api/annotation"""
    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent)) 
        texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out

def sent_to_words(sentences):
    for sentence in sentences:
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))

def remove_stopwords(texts):
    cleaned = [[word for word in gensim.utils.simple_preprocess(str(doc)) if word not in en_stop] for doc in texts]
    words = [word for word in cleaned if len(word) >= 4]
    return words

def make_grams(texts):
    bigram = Phrases(texts, min_count=20)
    # trigram = Phrases(bigram[texts], min_count=len(texts)*.05)
    for idx in range(len(texts)):
        for token in bigram[texts[idx]]:
            if '_' in token:
                texts[idx].append(token)
        # for token in trigram[bigram[texts[idx]]]:
        #     if token.count('_') == 2:
        #         texts[idx].append(token)

    return texts

def generate_text_data_from_file(file_name):
    texts = []
    with open(file_name) as f:
        for line in f:
            texts.append(line)
    data_words = list(sent_to_words(texts))
    data_words_nostops = remove_stopwords(data_words)
    data_lemmatized = lemmatization(data_words_nostops, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
    data_grams = make_grams(data_lemmatized)
    return data_grams

def generate_text_data_from_record(texts, asin, product_title):
    table.clear_cache()
    en_stop.extend(gensim.utils.simple_preprocess(str(product_title)))
    data_words = list(sent_to_words(texts))
    data_words_nostops = remove_stopwords(data_words)
    data_lemmatized = lemmatization(data_words_nostops, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
    data_grams = make_grams(data_lemmatized)

    dictionary = corpora.Dictionary(data_grams)
    dictionary.filter_extremes(no_below=.1, no_above=0.60)
    corpus = [dictionary.doc2bow(text) for text in data_grams]
    pickle.dump(corpus, open('corpus.pkl', 'wb'))
    dictionary.save('dictionary.gensim')

    logging.info("Number of unique tokens: {}".format(len(dictionary)))
    logging.info("Number of documents: {}".format(len(corpus)))

    model_list, coherence_values = compute_coherence_values(dictionary, corpus, data_grams, 40)

    limit=40; start=2; step=2;
    x = list(range(start, limit, step))
    for m, cv in zip(x, coherence_values):
        logging.info("Num Topics =", m, " has Coherence Value of", round(cv, 4))
    best_score_idx = find_nearest(coherence_values, 0)
    best_topic_count = x[best_score_idx]

    logging.info("Best Topic Count: {} with CV of: ".format(best_topic_count, round(coherence_values[best_score_idx],4)))

    model_list[best_score_idx].save('model5.gensim')
    topics = model_list[best_score_idx].show_topics(num_words=4)

    pretty_topics = []
    ugly_topics = []
    filters = [lambda x: x.lower(), strip_punctuation, strip_numeric]

    for topic in topics:
        pretty_topics.append(preprocess_string(topic[1], filters))
        ugly_topics.append(topic[1])

    logging.info("Pretty Topics: {}".format(pretty_topics))
    logging.info("Normal Topics: {}".format(topics))
    Product = Query()
    record = table.search(Product.asin == asin)[-1]
    logging.info(record)
    record["pretty_topics"] = pretty_topics
    record["topics"] = ugly_topics
    record["status"] = "Topic Generation Complete"
    logging.info(record)
    table.update(record, Product.asin == asin)

def compute_coherence_values(dictionary, corpus, texts, limit, start=2, step=2):
    coherence_values = []
    model_list = []

    num_topics = 10
    chunksize = 2000
    passes = 20
    iterations = 400
    eval_every = None

    temp = dictionary[0]
    id2word = dictionary.id2token

    for num_topics in range(start, limit, step):
        model = gensim.models.ldamodel.LdaModel(
            corpus=corpus,
            id2word=id2word,
            chunksize=chunksize,
            alpha='auto',
            eta='auto',
            iterations=iterations,
            num_topics=num_topics,
            passes=passes,
            eval_every=eval_every
        )

        model_list.append(model)
        coherencemodel = gensim.models.ldamodel.CoherenceModel(model=model, texts=texts, dictionary=dictionary, coherence='u_mass')
        c = coherencemodel.get_coherence()
        coherence_values.append(c)

    return model_list, coherence_values

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin() 
    return idx
