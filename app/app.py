from flask import Flask
from flask import jsonify
from threading import Thread
#from tasks import threaded_task

app = Flask(__name__)

@app.route("/scrape", methods=['GET', 'POST'])
def scraper_api():
    thread = Thread(target=test_func)
    thread.daemon = True
    thread.start()
    return jsonify({'thread_name': str(thread.name),
                    'started': True})

def test_func():
    return 5+5