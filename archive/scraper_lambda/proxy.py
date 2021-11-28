from requests.api import request
import config
import requests
import http.client
from urllib import parse

def request_page_with_proxy(request_url):

    params = {
    "api_key": config.proxy_key,
    "url": request_url,
    "device": config.proxy_device,
    "country": config.proxy_country,
    "wait_for": config.proxy_timeout_ms,
    "proxy_type": config.proxy_type,
    "url": request_url
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
                "html": None
            }
            return res

    except http.client.HTTPException as e:
        print("HttpException Occurred", e)


