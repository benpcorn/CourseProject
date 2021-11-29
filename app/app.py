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

        Product = Query()
        records = table.search(Product.asin == payload["asin"] and Product.status == 'done')
        if len(records) != 0:
            logging.info("Found existing record for: {}, returning results.".format(payload["asin"]))
            return jsonify(records[-1])

        thread = Thread(target=scraper.get_reviews_by_asin, args=(payload["asin"],))
        thread.daemon = True
        thread.start()
        return jsonify({'thread_name': str(thread.name),
                        'started': True})

@app.route("/process", methods=['POST'])
def processor_api():
    if request.method == 'POST':
        payload = request.get_json()

        Product = Query()
        records = table.search(Product.asin == payload["asin"] and Product.status == 'done')

        if len(records) != 0:
            reviews = records[-1]['reviews']
            thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,payload["asin"],))
            thread.daemon = True
            thread.start()
            return jsonify({'thread_name': str(thread.name),
                            'started': True})
        else:
            return jsonify({'status': 'failed', 'reason': 'Product reviews not found.'})
