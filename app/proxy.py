from requests.api import request
import config
import requests
import http.client
import os
import logging
from urllib import parse
from random import randint

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

def request_page_with_proxy(request_url):

    params = {
    "api_key": config.proxy_key,
    "url": request_url,
    "device": config.proxy_device,
    "wait_for": config.proxy_timeout_ms,
    "proxy_type": config.proxy_type,
    "render_js": 1
    }

    try:
        encoded_url = "/v1?" + parse.urlencode(params)
        conn = http.client.HTTPSConnection(config.proxy_url)
        response = conn.request("GET", encoded_url)

        res = conn.getresponse()
        data = res.read()
        data = data.decode("utf-8")

        if res.code == 200:
            res = {
                "status_code": res.code,
                "html": data
            }
            return res
        else:
            res = {
                "status_code": res.code,
                "html": None,
                "error": data
            }
            return res

    except http.client.HTTPException as e:
        print("HttpException Occurred", e)

def request_page_with_proxy_2(request_url):

    params = {
    "api_key": "ee65d3434239029e1b92cd86baded97b",
    "url": request_url,
    }

    for _ in range(3):
        try:
            logging.info("Making request: {}".format(_))
            response = requests.get('http://api.scraperapi.com/', params=parse.urlencode(params), verify=False)
            if response.status_code in [200, 404]:
                logging.info("Status of {}".format(response.status_code))
                break
        except requests.exceptions.ConnectionError:
            logging.info("Failure with exception after {} tries.".format(_))
            response = ''
        
    if response.status_code == 200:
        res = {
            "status_code": response.status_code,
            "html": response.text
        }
        return res
    else:
        res = {
            "status_code": response.status_code,
            "html": None,
        }
        return res