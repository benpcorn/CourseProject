from flask import Flask, json
from flask import jsonify
from flask import request
from flask_cors import CORS
from threading import Thread
from tinydb import TinyDB, Query
import logging
import scraper
import os
import lda_processor

app = Flask(__name__)
db = TinyDB('./db.json')
table = db.table('product_reviews')
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
cors = CORS(app)


@app.route("/scrape", methods=['POST'])
def scraper_api():
    if request.method == 'POST':
        payload = request.get_json()
        logging.info("Received payload: {}".format(payload))

        if "asin" not in payload.keys():
            return jsonify({"state": "failure", "reason": "ASIN not provided."})

        table.clear_cache()
        Product = Query()
        record = table.search(Product.asin == payload["asin"])

        recordCount = len(record)
        containsReview = "reviews" in record[-1].keys() if recordCount > 0 else False
        reviewCount = len(record[-1]["reviews"]) if containsReview else 0
        containsTopics = "topics" in record[-1].keys() if reviewCount > 0 else False
        topicCount = len(record[-1]["topics"]) if containsTopics else 0

        if recordCount: 
            logging.info("Record found for ASIN: {} with doc_id: {}".format(payload["asin"], record[-1].doc_id))
        else:
            logging.info("No records found for ASIN: {}".format(payload["asin"]))

        if recordCount == 0:
            # Start scraping if there is no data for the provided ASIN.
            logging.info("No records found... starting Scrape processor for: {}".format(payload["asin"]))
            thread = Thread(target=scraper.get_reviews_by_asin, args=(payload["asin"],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif recordCount > 0 and reviewCount > 0 and topicCount == 0 and "force" not in payload.keys():
            # Start LDA processor if there is review data, but no topic data.
            logging.info("No topics found for ASIN... starting LDA processor on existing review data for: {}".format(payload["asin"]))
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif recordCount > 0 and reviewCount > 0 and topicCount > 0 and "force" not in payload.keys():
            # Return the DB record for the ASIN when there are reviews and topics.
            logging.info("Found existing record for: {}, returning results.".format(payload["asin"]))
            return jsonify(record[-1])
        else:
            # Force scrape to start.
            logging.info("Force parameter used... starting Scrape processor for: {}".format(payload["asin"]))
            thread = Thread(target=scraper.get_reviews_by_asin, args=(payload["asin"],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})

@app.route("/process", methods=['POST'])
def processor_api():
    if request.method == 'POST':
        payload = request.get_json()

        if "asin" not in payload.keys():
            return jsonify({"state": "failure", "reason": "ASIN not provided."})

        table.clear_cache()
        Product = Query()
        record = table.search(Product.asin == payload["asin"])[-1]

        recordCount = len(record)
        containsReview = "reviews" in record[-1].keys() if recordCount > 0 else False
        reviewCount = len(record[-1]["reviews"]) if containsReview else 0
        containsTopics = "topics" in record[-1].keys() if reviewCount > 0 else False
        topicCount = len(record[-1]["topics"]) if containsTopics else 0

        if recordCount > 0 and reviewCount > 0 and topicCount == 0:
            # Start LDA processor when there are reviews, but no topics.
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif recordCount > 0 and reviewCount > 0 and topicCount > 0 and "force" in payload.keys():
            # Start LDA processor when there are reviews and the force flag exists.
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif recordCount and topicCount > 0:
            # Return topics if they exist
            return jsonify(record)
        else:
            return jsonify({'status': 'failed', 'reason': 'Product reviews not found.'})
