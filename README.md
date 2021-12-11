# Amazon Review Analyzer

Amazon Review Analyzer (ARA) is a Python based RESTful API (with optional Chrome extension) to scrape, process, and analyze product reviews on Amazon.com to generate common topics your customers are talking about. It scrapes every review, stores them in a lightweight database, and applies an LDA topic model to generate topic keywords.

### Implementation Overview

1. Flask API: ARA runs a lightweight Flask server with two REST API endpoints: `scrape` which scrapes reviews and inserts them to a record in `tinydb` and `process` which runs Gensim's LDA topic modelling on those reviews to generate topics.
2. Chrome Extension: Adds an "Analyze" button to any product page on Amazon.com, and renders the topics in a table on the product page if they exist.

#### Database Model for Product Records

ARA uses a lightweight local Python database implementation `TinyDB` to store and retrieve reviews and topics. When a product is requested for analysis through the `scrape` endpoint, a record in the database is generated with the following fields:

    record = {
        'asin': string - unique identifier of the product on Amazon.com,
        'reviews': array - raw review text, one element per review,
        'status': string - status of the scrape or process job,
        'topics': array - raw topics generated by Gensim LDA with probabilities per word,
        'pretty_topics': 2D array - one array per topic, with each topic word in the sub-array (no probabilities),
        'product_title': string - the title of the product on Amazoin.com
    }

### API Documentation
The Flask API handles two things: scraping and LDA processing. Two Flask "routes" are defined, `/scrape` and `/process` - both are POST requests.

#### Scraper
The scraper endpoint takes an ASIN as a request parameter (required). Every product on Amazon has a unique ASIN, and they can be found in every product page URL or in the product detail information.

For example, the ASIN in `https://www.amazon.com/XLUX-Soil-Moisture-Sensor-Meter/dp/B014MJ8J2U/` is `B014MJ8J2U`.

The `/scrape` route checks the TinyDB database to see if there are any existing records matching the provided ASIN.
1. If there is a matching record with reviews and topics already generated, the database record is returned as JSON. (see example record above)
2. If there is a matching record with reviews, but there are no topics, a new thread is launched that invokes the LDA processor: `lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],)`
3. If there is no existing record for the provided ASIN, a new thread is launched that invokes the scraper: `scraper.get_reviews_by_asin(ASIN)`

If a request is made with the optional parameter `force`, the entire record will be re-built by running the scrape job again. Because new reviews are constantly being added by customers, this enables you to retrieve those new reviews on a regular cadence.

#### Scraper Endpoint Example Requests
POST http://localhost:5000/scrape

    {
        "asin": "B08SC42G8B"
    }
    
To force a re-run of an existing ASIN, include the optional parameter "force" to request body.

    {
        "asin": "B08SC42G8B",
        "force": true
    }
    
#### LDA Processor
The process endpoint takes an ASIN as a request parameter and kicks of an LDA processor job against the product reviews for that ASIN.

The `/process` route checks the TinyDB database to see if there are any existing records matching the provided ASIN.
1. If there is a matching record with topics, the database record is returned as JSON. (see example record above)
2. If there is a matching record, but no topics, a new thread is launched that invokes the LDA processor: `lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],)`
3. If there is no matching record, a JSON object is returned indicating there was no matching ASIN.

If a request is made with the optional parameter `force`, the reviews will be reprocessed to build new topics.

#### LDA Processor Endpoint Example Requests
POST http://localhost:5000/process

    {
        "asin": "B08SC42G8B"
    }
    
Example response

    {
    "asin": "B08SC42G8B",
    "pretty_topics": [
        [
            "ladder",
            "keep",
            "least",
            "problem"
        ]
    ],
    "product_title": "Security Camera Outdoor with Floodlight and Sound Alarm, Imou 4MP QHD Pan/Tilt 2.4G Wi-Fi Camera, IP66 Weatherproof 2K Bullet Camera, Full Color Night Vision IP Camera with 2-Way Talk, Cruiser 4MP",
    "reviews": [
        "Just so everyone knows. When you go to connect the camera. DO NOT USE THE QR CODE IN THE INSTRUCTIONS. That code is for finding the app or something stupid. The instructions do not tell you that you are supposed to scan the code on top of the camera itself. There is absolutely nothing that tells you to that there is a code on the camera itself. So much frustrating time wasted baking in the sun waiting and waiting for search times. I almost returned the camera... Then upon disassembly we noticed the code on top of the camera and tried it in one last desperate effort. Instant connection... So 3 stars for that. Otherwise great camera so far. I love its tracking feature. And it has great night vision."
    ],
    "status": "Topic Generation Complete",
    "topics": [
        "0.002*\"ladder\" + 0.002*\"keep\" + 0.002*\"least\" + 0.002*\"problem\""
    ]
    }
    
    
To force a re-run of an existing ASIN, include the optional parameter "force" to request body.

    {
        "asin": "B08SC42G8B",
        "force": true
    }
    
### Scraper Implementation (scraper.py)
The `scraper` module takes an ASIN, scrapes all the Amazon.com reviews, and creates a database record. This module can be used as a standalone tool for scraping reviews for any product on Amazon.com. Please note, this does not work for products in other marketplaces such as Amazon.co.uk, Amazon.de, etc., however could be easily extended to support those regions. There are three primary components to the scraper:

1. Proxy: Amazon blocks any client making requests that appear to be automated, so a proxy service is utilized to retrieve the HTML of the page. The proxy used is https://www.webscrapingapi.com/
2. BeautifulSoup: Once the raw HTML is returned by the proxy, BeautifulSoup is used to extract the reviews from the page.

#### get_reviews_by_asin
This method takes an ASIN (e.g., B014MJ8J2U) and a page retrieval method (proxy or local). Proxy is used by default. The method makes a call to `build_request_url` that generates the correct URL on Amazon.com for product reviews (e.g., https://www.amazon.com/XLUX-Soil-Moisture-Sensor-Meter/product-reviews/B014MJ8J2U/ref=cm_cr_arp_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber=2). There are (3) components to the URL: the ASIN, the `paging_btm_next_{x}`, and the `pageNumber={x}`. The method takes in the ASIN and the page number to generate the correct URL used when requesting HTML from the proxy.

Amazon displays up to 10 reviews per page, so the number of pages must also be calculated by scraping the total number of reviews by 10. `get_global_review_count` and `get_review_page_count` are both invoked to generate these numbers. The total reviews is located on every Amazon product review page (e.g., "3,775 global reviews").

The scraper then iterates over every page, building a new request URL each time, and parsing the reviews using BeautifulSoup to extract the review DOM elements with `soup.find_all(attrs={"data-hook":"review-body"})`.

Once complete, the reviews are written to the TinyDB database record: `write_reviews_to_db(reviews, asin, product_title)`. There is an additional method `write_reviews_to_file(reviews, file_name)` available to write the reviews to a text file.

### LDA Processor Implementation (lda_processor.py)
The LDA processor takes a set of reviews (documents), and generates a set of topics. The processor module has methods for processing from a TinyDB record and a local text file.

Processor steps include:
1. Retrieving a set of reviews from a DB record or local text file
2. Creating a dictionary of words by tozenizing every review: `list(sent_to_words(texts))` and the bag-of-words corpus
3. Removing stop words: `remove_stopwords(data_words)`
4. Lemmatizing: `lemmatization(data_words_nostops, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])`
5. Creating bigrams: `make_grams(data_lemmatized)`
6. Running Gensim LDA against the dictionary, corpus, and reviews with a variable number of topics ranging from 2 to 40: `compute_coherence_values(dictionary, corpus, data_grams, 40)`
7. Picking the best topic model based on the coherence scores calculated by Gensim's CoherenceModel

Additional details for the steps above:

#### Retrieve Set of Reviews

`generate_text_data_from_record(texts, asin, product_title)` takes an array of texts (reviews), an ASIN (string), and product title (string).

#### Create Dictionary
Gensim's `simple_preprocess` is run against every review to tokenize. `deacc=True` removes any accents in the words.

#### Remove Stop Words and Corpus
`remove_stopwords(data_words)` removes any stop words (e.g., the, if, of) based on the English corpus of stopwords from NLTK. The corpus is extended with the words from the product title, as better topic results were generally seen after doing so (`en_stop.extend(gensim.utils.simple_preprocess(str(product_title)))`)

#### Lemmatizing
`lemmatization(data_words_nostops, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])` lemmatizes (i.e., assigns base forms to tokens using rules based on part-of-speech tags, or lookup tables) using Spacy.io's `en_core_web_sm`.

#### Creating Bigrams
`make_bigrams(texts)` uses Gensim's `Phrases` module to generate bigram's - by doing so, improved topic results were generally seen. An example bigram would be 'social media', or 'battery life'. The min_count parameter is set to 20, only including the bigram is it is seen at least 20 times in the set. This parameter can be adjusted to improve performance, however 20 is used as a default. Additionally, there is commented out code for generating trigrams. This was a recommended approach found in several tutorials, but the results were varied across different products and ommitted due to low overall topic quality.

#### Running Gensim LDA
`compute_coherence_values(dictionary, corpus, texts, limit, start=2, step=2)` runs Gensim LDA to generate topics. The method generates topic models with N # of topics from 2 to 40, in steps of 2 (i.e., 2,4,6,...,40). Additionally, the coherence value using "U Mass" as the measure (e.g., success / accuracy metric) is computed for each model using Gensim's Coherence Model method. The models and coherence values are returned.

#### Model Selection
The coherence value **closest to 0** is selected using the `find_nearest` method, which simply calculates the value closest to zero and returns the index in the array. `generate_text_data_from_record` chooses the topic model with that index, and generates a 2D array called `pretty_topics` that is more readable than the standard Gensim output. Each element is a topic with each sub-array element being a word from that topic. The implementation only returns the first (4) words, based on probability value in descending order.

A TinyDB record is updated with the raw topic output from Gensim (`topics`) and the formatted topics (`pretty_topics`) and the `status` field of the record is updated.

Raw Topic Example: 

    'topics': ['0.002*"ladder" + 0.002*"keep" + 0.002*"least" + 0.002*"problem"', '0.002*"ladder" + 0.002*"keep" + 0.002*"least" + 0.002*"problem"',        '0.002*"ladder" + 0.002*"keep" + 0.002*"least" + 0.002*"problem"', '0.002*"ladder" + 0.002*"keep" + 0.002*"least" + 0.002*"problem"', '0.002*"ladder" + 0.002*"keep" + 0.002*"least" + 0.002*"problem"', '0.049*"work" + 0.024*"well" + 0.024*"light" + 0.024*"great"', '0.030*"use" + 0.030*"app" + 0.030*"work" + 0.030*"cam"', '0.025*"cam" + 0.022*"recording" + 0.022*"record" + 0.013*"video"', '0.027*"even" + 0.027*"experience" + 0.014*"resolve" + 0.014*"sorry"', '0.040*"work" + 0.040*"good" + 0.030*"time" + 0.020*"well"']
    
Pretty Topic Example:
    
    'pretty_topics': [['ladder', 'keep', 'least', 'problem'], ['ladder', 'keep', 'least', 'problem'], ['ladder', 'keep', 'least', 'problem'], ['ladder', 'keep', 'least', 'problem'], ['ladder', 'keep', 'least', 'problem'], ['work', 'well', 'light', 'great'], ['use', 'app', 'work', 'cam'], ['cam', 'recording', 'record', 'video'], ['even', 'experience', 'resolve', 'sorry'], ['work', 'good', 'time', 'well']]****
    
#### General Comments
The topic quality varies greatly based on the particular product and review dataset size. Products with a greater number of reviews (e.g., N >= 100) seemed to provide decent results, while products with a low number of reviews (e.g., N <= 100) simply did not provide enough data to generate quality topics. Additionally, Amazon.com targets the English and Spanish speaking customer segment, but this LDA processor only handles English reviews. Processing to remove non-English reviews could be implemented to further increase accuracy. Lastly, the speed for processing topics is quite fast for most products (<30s), however products with a large number of reviews such as the Amazon Alexa Show device can take some time (~5-8 minutes). The scraping jobs for these products with large reviews is the long pole, taking up to 30 minutes or more.

### Google Chrome Extension Implementation (inject.js)
Extensionizr was used to create boilerplate Google Chrome extension code, however most of it was not utilized in this MVP project iteration. The boilerplate code enables a fast way to add a settings menu to the extension, which will be handy when enabling customers to set hyperparameters used in the scraping and processing jobs such as max number of pages/reviews to scrape, max number of topics, number of words per topics, and other parameters used with Gensim LDA.

The extension is handled in `inject.js`. The original intent was to make the extension feel like a native part of the Amazon page, so a new DOM element is created that matches the styling of an existing Amazon DOM element. Because the Amazon page uses lazy loading, a check is done on an interval `var readyStateCheckInterval = setInterval(function()` until the DOM element ID that is copied, is found on the page: `if (document.getElementById('cm_cr_dp_d_write_review'))`. Once found, the element is cloned `reviewDiv.cloneNode(true);` and the title and subtext are modified to look like this:

![alt text](https://user-images.githubusercontent.com/73569064/145688835-d976edb3-4e4f-435f-bd46-0029ee35101e.png)

A request is made to the Flask `/scrape` endpoint by passing in the ASIN from the product page `const retrieveAnalysis = async ASIN => {` on page load. If reviews and topics already exist, they are rendered in a table. Otherwise a scrape job is kicked off automatically, and then a subsequent processor job is run. After some time, refreshing the page will render the topics in a table (see image above as example).

Selecting the "Analyze" button will fire the `const forceAnalysis = async ASIN => {` method with the `force` request parameter, forcing the scraper to generate new review results.

The limitation of this extension is that the current state of the jobs are not displayed. The scope and complexity of this work was not possible to pull in given the timeframe of the project, but calling this out as a painpoint in the current experience.

### How to Install

1. This deployment requires Python 3.10+. It is recommend to use Conda (Anaconda / Miniconda) to save yourself frustration when managing multiple Python versions and libraries. You can quickly install Miniconda with their installers for MacOS and Windows: https://docs.conda.io/en/latest/miniconda.html (hint: use .pkg on MacOS for faster install).
2. Clone this repository to your machine.

#### Python Project
    conda create --name env-name python=3.10
    conda activate env-name
    pip install .
    
#### Extension
1. From Google Chrome, chrome://extensions/
2. Click "Load unpacked"
3. Select the extension folder

### How to Run the Flask API
From the app folder, run the following command to start Flask on localhost:5000

Option 1:
    ./run.sh
    
Option 2:
    FLASK_APP=app.py FLASK_ENV=development flask run

### How to Generate Results

Option 1: Use the `/scrape' endpoint and an ASIN of your choosing.
Option 2: Use the Chrome extension to kick off the requests.
