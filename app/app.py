from flask import Flask, json
from flask import jsonify
from flask import request
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

@app.route("/scrape", methods=['POST'])
def scraper_api():
    if request.method == 'POST':
        payload = request.get_json()
        table.clear_cache()
        Product = Query()
        record = table.search(Product.asin == payload["asin"])
        if len(record) != 0 and "force" not in payload.keys():
            logging.info("Found existing record for: {}, returning results.".format(payload["asin"]))
            return jsonify(record[-1])

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

        if len(record) and "topics" not in record.keys():
            reviews = record['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        elif "topics" in record.keys():
            return jsonify(record)
        else:
            return jsonify({'status': 'failed', 'reason': 'Product reviews not found.'})
