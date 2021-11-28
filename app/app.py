from flask import Flask
from flask import jsonify
from flask import request
from threading import Thread
import scraper

app = Flask(__name__)

@app.route("/scrape", methods=['GET', 'POST'])
def scraper_api():

    if request.method == 'POST':
        payload = request.get_json()
        thread = Thread(target=scraper.get_reviews_by_asin, args=(payload["asin"],))
        thread.daemon = True
        thread.start()
        return jsonify({'thread_name': str(thread.name),
                        'started': True})
    else:
        return 'get request'
