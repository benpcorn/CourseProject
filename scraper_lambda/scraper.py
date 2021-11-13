import requests
import logging
import math
from bs4 import BeautifulSoup

# 10 reviews per page
# URL structure contains https://www.amazon.com/dp/product-reviews/B08SG2MS3V/&reviewerType=all_reviews&pageNumber=6 
# Important URL components "dp", "product-reviews", {ASIN i.e., B08SG2MS3V}, pageNumber=N

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
    soup = BeautifulSoup(page.content, 'html.parser')
    match option:
        case "raw":
            return soup
        case "pretty":
            return soup.prettify()


def get_global_review_count(soup):
    review_div = soup.find(attrs={"data-hook":"cr-filter-info-review-rating-count"})
    review_count = review_div.span
    review_count = review_count.text.strip().split(" ")[0].replace(',', '')
    return int(review_count)

def get_review_page_count(review_count, reviews_per_page):
    return math.ceil(review_count / reviews_per_page)

## Testing ##
asin = "B08SG2MS3V"
page_number = 1

req_url = build_request_url(asin, page_number)
page = get_page(req_url)
soup = get_soup_from_page(page, "raw")
review_count = get_global_review_count(soup)
review_page_count = get_review_page_count(review_count, 10)

print(review_page_count)