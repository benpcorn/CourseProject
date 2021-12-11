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
        table.clear_cache()
        Product = Query()
        record = table.search(Product.asin == payload["asin"])
        if len(record) > 0: 
            logging.info("Record: {}".format(record[-1].doc_id))
        if len(record) != 0 and "force" not in payload.keys():
            # Return the existing data we have
            logging.info("Found existing record for: {}, returning results.".format(payload["asin"]))
            return jsonify(record[-1])
        elif len(record) != 0 and len(record[-1]["topics"]) == 0 and "force" not in payload.keys():
            # Kick off LDA processing
            logging.info("Starting LDA processor on existing review data for: {}".format(payload["asin"]))
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        else:
            # Kick off scraping
            logging.info("Starting Scrape processor for: {}".format(payload["asin"]))
            thread = Thread(target=scraper.get_reviews_by_asin, args=(payload["asin"],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})

@app.route("/process", methods=['POST'])
def processor_api():
    if request.method == 'POST':
        payload = request.get_json()
        table.clear_cache()
        Product = Query()
        record = table.search(Product.asin == payload["asin"])[-1]

        if len(record) and len(record["topics"]) == 0:
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif len(record) and len(record["topics"]) > 0 and "force" in payload.keys():
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],record['product_title'],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif len(record) and len(record["topics"]) > 0:
            return jsonify(record)
        else:
            return jsonify({'status': 'failed', 'reason': 'Product reviews not found.'})
