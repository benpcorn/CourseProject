# 1 Tasks Completed

This project consists of the following tasks, as outlined in the proposal (see readme.md):

- [x] Text Mining: Done (Python, BeautifulSoup, Proxy service)
- [x] Text Processing: Initial implementation done. Moving to Fine tuning. (NLTK)
- [x] LDA: In Progress: Initial implementation done. Moving to Fine tuning. (Gensim)
- [ ] Sentiment Anlysis: Not Started
- [ ] Chome Extension: Not Started

# 2 Pending Tasks
At this time, I have a functional end-to-end prototype of topic analysis for any given Amazon product, running locally on my machine. The remaining work involves:

1. Creating AWS Lambdas for my text mining and text processing (cleaning + topic modeling).
2. Fine tuning of the text processor to further clean the review data
3. Fine tuning of the LDA model. Namely, implementing an algorithm to determine the ideal number of topics based on Topic Coherence and Perplexity,
4. Sentiment Analysis by Topic.
5. Chrome Extension: create the extension that enables new UI on Amazon.com for an end-user to initiate the analysis with the Lambdas, and the work to show the topics on the website.

# 3 Challenges

1. Blocked: I encountered a problem early on where I was getting blocked by Amazon due to the request volume when scraping reviews. To get around this, I had to utilize a 3P proxy service to avoid blocking. Using the WebScrapingAPI: https://www.webscrapingapi.com/ for the proxy feature (provide URL with params and it returns raw HTML through proxies).
2. Speed: Amazon only shows 10 reviews per page, so products with a lot of reviews are taking a lot of time to scrape. I tried to mitigate this through multi-threading, but it was still pretty slow (~5 minutes for 600 reviews) - turned out 1) I didn't implement it correctly and 2) I/O operations can't be multi-threaded, rather they need to be run on multiple processors. Locally, I can implement multi-processor support to speed this up and will take this up as a new piece of work, if time allows.
3. Topic Quality: The initial set of topics I'm seeing from products aren't great. It's difficult to deduce what the "common topic" is from the topic keywoards returned by Gensim. There is an approach outlined here (https://towardsdatascience.com/%EF%B8%8F-topic-modelling-going-beyond-token-outputs-5b48df212e06) that combines LDA with RAKE. I'm going to try this.
