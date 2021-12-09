import requests
import os
import logging
import math
import proxy as proxy
import lda_processor
from threading import Thread
from numpy import random
from time import sleep
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query

from requests.api import head

db = TinyDB('./db.json')
table = db.table('product_reviews')
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

def build_request_url(asin, page_number):
    request_url = "https://www.amazon.com/dp/product-reviews/" + asin + "/ref=cm_cr_getr_d_paging_btm_next_{}?pageNumber={}&reviewerType=all_reviews".format(page_number, page_number)
    logging.info("Built Request URL: {}".format(request_url))
    return request_url


def get_page(request_url):
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    page = requests.get(request_url, headers = headers)
    if page.status_code != 200:
        logging.error("Error retrieving {} with status code: {}".format(request_url, page.status_code))
        return None
    else:
        logging.info("get_page successful for {}".format(request_url))
        return page

def get_soup_from_page(page, option = "raw"):
    try:
        soup = BeautifulSoup(page, 'html.parser')
        logging.info("Soup has been retrieved for page.")
        match option:
            case "raw":
                return soup
            case "pretty":
                return soup.prettify()
    except AttributeError:
        logging.error("No content for page.")
        return None


def get_global_review_count(soup):
    review_div = soup.find(attrs={"data-hook":"cr-filter-info-review-rating-count"})
    if review_div != None:
        review_count = review_div.span
        review_count = review_count.text.strip().split(" ")[0].replace(',', '')
        logging.info("Discovered " + str(review_count) + " reviews.")
        return int(review_count)
    else:
        logging.error("Page contains no data.")

def get_review_page_count(review_count, reviews_per_page):
    page_count = math.ceil(review_count / reviews_per_page)
    logging.info("Total Review Pages: {}".format(str(page_count)))
    return page_count

def get_reviews_by_asin(asin, method="proxy"):
    logging.info("Starting scrape job for ASIN: ".format(asin))
    record = {
        'asin': asin,
        'reviews': [],
        'status': 'Scraping Started',
        'topics': [],
        'pretty_topics': []
    }
    table.insert(record)
    req_url = build_request_url(asin, 1)
    if method == "proxy":
        page = proxy.request_page_with_proxy(req_url)["html"]
    else:
        page = get_page(req_url)
    soup = get_soup_from_page(page, "raw")
    review_count = get_global_review_count(soup)
    review_page_count = get_review_page_count(review_count, 10)
    review_divs = []
    reviews = []

    for page in range(1, review_page_count + 1):
        if page > 1:
            req_url = build_request_url(asin, page)
            page = proxy.request_page_with_proxy(req_url)["html"]
            if page == None:
                break 
            soup = get_soup_from_page(page, "raw")
        reviews_on_page = soup.find_all(attrs={"data-hook":"review-body"})
        review_divs += reviews_on_page

        if len(reviews_on_page) < 10:
            break

    for div in review_divs:
        reviews.append(div.get_text(strip=True))

    write_reviews_to_file(reviews, asin + ".txt")
    write_reviews_to_db(reviews, asin)

    return reviews

def write_reviews_to_file(reviews, file_name):
    logging.info("Writing reviews to file.")
    textfile = open("../sample_reviews/" + file_name, "w")
    for review in reviews:
        textfile.write(review + "\n")
    textfile.close()

def write_reviews_to_db(reviews, asin):
    logging.info("Writing reviews to DB.")
    record = {
        'asin': asin,
        'reviews': reviews,
        'status': 'Scraping Done',
        'topics': [],
        'pretty_topics': []
    }
    Product = Query()
    table.update(record, Product.asin == asin)

    logging.info("Reviews written to DB record. Starting LDA processor now.")
    thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,asin,))
    thread.daemon = True
    thread.start()