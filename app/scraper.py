import requests
import os
import logging
import math
import proxy as proxy
import lda_processor
from threading import Thread
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
import time

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
    logging.info("Attempting to get soup.")
    try:
        soup = BeautifulSoup(page, 'html.parser')
        logging.info("Soup has been retrieved for page.")
        match option:
            case "raw":
                return soup
            case "pretty":
                return soup.prettify()
    except (AttributeError, TypeError):
        logging.error("Unable to get soup. :/")
        return None,


def get_global_review_count(soup):
    review_div = soup.find(attrs={"data-hook":"cr-filter-info-review-rating-count"})
    if review_div != None:
        review_count = review_div.span
        review_count = review_count.text.strip().split(" ")[0].replace(',', '')
        logging.info("Discovered {} reviews.".format(review_count))
        return int(review_count)
    else:
        logging.error("Page contains no data.")

def get_review_page_count(review_count, reviews_per_page):
    page_count = math.ceil(review_count / reviews_per_page)
    logging.info("Total Review Pages: {}".format(str(page_count)))
    return page_count

def get_reviews_by_asin(asin, method="proxy"):
    logging.info("Starting scrape job for ASIN: {}".format(asin))
    record = {
        'asin': asin,
        'reviews': [],
        'status': 'scrape_started',
        'topics': [],
        'pretty_topics': [],
        'product_title': ''
    }
    table.insert(record)
    review_divs = []
    reviews = []

    try:
        req_url = build_request_url(asin, 1)
        if method == "proxy":
            page = proxy.request_page_with_proxy_2(req_url)

            if page["status_code"] != 200:
                logging.error("{}".format(page["error"]))
            else:
                page = page["html"]
        else:
            page = get_page(req_url)
        soup = get_soup_from_page(page, "raw")

        review_count = get_global_review_count(soup)
        review_page_count = get_review_page_count(review_count, 10)

        for page in range(1, review_page_count + 1):
            if page > 1:
                req_url = build_request_url(asin, page)
                page_content = proxy.request_page_with_proxy_2(req_url)

                if page_content["status_code"] != 200:
                    logging.error("{}".format(page_content["error"]))
                else:
                    page_content = page_content["html"]

                if page_content == None:
                    logging.info("Page {} was NoneType.".format(page))
                    continue

                soup = get_soup_from_page(page_content, "raw")

                if soup == None:
                    logging.info("Soup for page {} was NoneType.".format(page))
                    continue

            reviews_on_page = soup.find_all(attrs={"data-hook":"review-body"})
            review_divs += reviews_on_page

            for div in review_divs:
                reviews.append(div.get_text(strip=True))

            if len(reviews_on_page) < 10:
                logging.info("Reached the last review page.")
                break
            
            #time.sleep(1)

        product_title = soup.title.string.replace("Amazon.com: Customer reviews: ", "")

        #write_reviews_to_file(reviews, asin + ".txt")
        if len(reviews):
            write_reviews_to_db(reviews, asin, product_title)

        return reviews
    except AttributeError:
        if len(reviews):
            write_reviews_to_db(reviews, asin)

def write_reviews_to_file(reviews, file_name):
    logging.info("Writing reviews to file.")
    textfile = open("../sample_reviews/" + file_name, "w")
    for review in reviews:
        textfile.write(review + "\n")
    textfile.close()

def write_reviews_to_db(reviews, asin, product_title = "Error Occurred"):
    logging.info("Writing reviews to DB.")
    record = {
        'asin': asin,
        'reviews': reviews,
        'status': 'scrape_done',
        'topics': [],
        'pretty_topics': [],
        'product_title': product_title
    }
    Product = Query()
    table.update(record, Product.asin == asin)

    logging.info("Product review record written to DB: {}. Starting LDA processor now.".format(record))
    thread = Thread(target=lda_processor.generate_text_data_from_record, args=(reviews,asin,product_title,))
    thread.daemon = True
    thread.start()