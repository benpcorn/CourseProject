import spacy
from spacy.lang.en import English
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
import gensim
from gensim import corpora
import pickle
import numpy as np
from gensim.models import Phrases

nltk.download('wordnet')
nltk.download('stopwords')
nlp = spacy.load('en_core_web_sm')

parser = English()
en_stop = nltk.corpus.stopwords.words('english')
en_stop.extend(['camera', 'doorbell', 'system', 'connect', 'base', 'station', 'arlo', 'ring', 'like', 'say']) #remove product specific words

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
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))  # deacc=True removes punctuations

def remove_stopwords(texts):
    cleaned = [[word for word in gensim.utils.simple_preprocess(str(doc)) if word not in en_stop] for doc in texts]
    words = [word for word in cleaned if len(word) >= 4]
    return words

def make_grams(texts):
    dictionary = corpora.Dictionary(texts)
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

# texts = generate_text_data_from_file("/Users/benjcorn/Desktop/UIUC/CS410/CourseProject/app/B08HRLQ9ZG_small.txt")
# dictionary = corpora.Dictionary(texts)
# dictionary.filter_extremes(no_below=.1, no_above=0.60)
# corpus = [dictionary.doc2bow(text) for text in texts]
# pickle.dump(corpus, open('corpus.pkl', 'wb'))
# dictionary.save('dictionary.gensim')

# print('Number of unique tokens: %d' % len(dictionary))
# print('Number of documents: %d' % len(corpus))

# model_list, coherence_values = compute_coherence_values(dictionary, corpus, texts, 40)

# limit=40; start=2; step=2;
# x = list(range(start, limit, step))
# for m, cv in zip(x, coherence_values):
#     print("Num Topics =", m, " has Coherence Value of", round(cv, 4))
# best_score_idx = find_nearest(coherence_values, 0)
# best_topic_count = x[best_score_idx]

# print("Best Topic Count: ", best_topic_count, " with CV of: ", round(coherence_values[best_score_idx],4))

# model_list[best_score_idx].save('model5.gensim')
# topics = model_list[best_score_idx].print_topics(num_words=4)
# for topic in topics:
#     print(topic)
