import requests
import logging
import math
from numpy import random
from time import sleep
from bs4 import BeautifulSoup

def build_request_url(asin, page_number):
    return "https://www.amazon.com/dp/product-reviews/" + asin + "/&reviewerType=all_reviews&pageNumber=" + str(page_number)


def get_page(request_url):
    page = requests.get(request_url)
    if page.status_code != 200:
        return None
        logging.error("Error retrieving " + request_url + " with status code: " + page.status_code)
    else:
        return page

def get_soup_from_page(page, option = "raw"):
    try:
        soup = BeautifulSoup(page.content, 'html.parser')
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
    review_count = review_div.span
    review_count = review_count.text.strip().split(" ")[0].replace(',', '')
    return int(review_count)

def get_review_page_count(review_count, reviews_per_page):
    return math.ceil(review_count / reviews_per_page)

def get_reviews_by_asin(asin):
    req_url = build_request_url(asin, 1)
    page = get_page(req_url)
    soup = get_soup_from_page(page, "raw")
    review_count = get_global_review_count(soup)
    review_page_count = get_review_page_count(review_count, 10)
    review_divs = []
    reviews = []

    for page in range(1, review_page_count + 1):
        if page > 1:
            req_url = build_request_url(asin, page)
            page = get_page(req_url)
            soup = get_soup_from_page(page, "raw")
        reviews_on_page = soup.find_all(attrs={"data-hook":"review-body"})
        review_divs += reviews_on_page

        if len(reviews_on_page) < 10:
            break

        sleep(random.uniform(2, 4))

    for div in review_divs:
        reviews.append(div.get_text(strip=True))

    return reviews

def write_reviews_to_file(reviews, file_name):
    textfile = open("../sample_reviews/" + file_name, "w")
    for review in reviews:
        textfile.write(review + "\n")
    textfile.close()

#TODO Create a driver.py file that acts as a console/driver of the program for testing purposes.
asin = "B08HRLQ9ZG"
reviews = get_reviews_by_asin(asin)
write_reviews_to_file(reviews, asin + ".txt")