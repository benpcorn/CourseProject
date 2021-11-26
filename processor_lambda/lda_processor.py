from os import fork
import spacy
from spacy.lang.en import English
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
import gensim
from gensim import corpora
import pickle
import numpy as np

nltk.download('wordnet')
nltk.download('stopwords')
nlp = spacy.load('en_core_web_sm')

parser = English()
en_stop = nltk.corpus.stopwords.words('english')
en_stop.extend(['camera', 'doorbell', 'system', 'connect', 'base', 'station']) #remove product specific words

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

def make_bigrams(texts):
    bigram = gensim.models.Phrases(texts, min_count=5, threshold=100) # higher threshold fewer phrases.
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    return [bigram_mod[doc] for doc in texts]

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

def generate_text_data_from_file(file_name):
    texts = []
    with open(file_name) as f:
        for line in f:
            texts.append(line)
    data_words = list(sent_to_words(texts))
    data_words_nostops = remove_stopwords(data_words)
    data_words_bigrams = make_bigrams(data_words_nostops)
    data_lemmatized = lemmatization(data_words_bigrams, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
    return data_lemmatized

def compute_coherence_values(dictionary, corpus, texts, limit, start=4, step=2):
    coherence_values = []
    model_list = []
    for num_topics in range(start, limit, step):
        model = gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=50, alpha='auto', per_word_topics=True, random_state=100, chunksize=1000)
        model_list.append(model)
        coherencemodel = gensim.models.ldamodel.CoherenceModel(model=model, texts=texts, dictionary=dictionary, coherence='u_mass')
        c = coherencemodel.get_coherence()
        coherence_values.append(c)

    return model_list, coherence_values

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin() 
    return idx

#TODO refactor this into a processor.py file that performs LDA work
texts = generate_text_data_from_file("/Users/benjcorn/Desktop/UIUC/CS410/CourseProject/processor_lambda/B08HRLQ9ZG_small.txt")
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
pickle.dump(corpus, open('corpus.pkl', 'wb'))
dictionary.save('dictionary.gensim')

# NUM_TOPICS = 10
# ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics = NUM_TOPICS, id2word=dictionary, passes=15)
# ldamodel.save('model5.gensim')
# topics = ldamodel.print_topics(num_words=4)
# for topic in topics:
#     print(topic)

model_list, coherence_values = compute_coherence_values(dictionary, corpus, texts, 40)

limit=40; start=4; step=2;
x = list(range(start, limit, step))
for m, cv in zip(x, coherence_values):
    print("Num Topics =", m, " has Coherence Value of", round(cv, 4))
best_score_idx = find_nearest(coherence_values, 0)
best_topic_count = x[best_score_idx]

print("Best Topic Count: ", best_topic_count, " with CV of: ", round(coherence_values[best_score_idx],4))

model_list[best_score_idx].save('model5.gensim')
topics = model_list[best_score_idx].print_topics(num_words=4)
for topic in topics:
    print(topic)
