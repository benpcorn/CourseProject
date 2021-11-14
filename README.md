# Amazon Product Review Analysis (Chrome Extension) | Intelligent Browsing

### Group Name
- Vinnie

### Team Members
- Benjamin Corn (bcorn2@illinois.edu) | Team Leader

### Problem

According to research performed by The Medill Spiegel Research Center (SRC) at Northwestern University, about 95% of customers read reviews before making a purchase<sup>[1]</sup> and 82% of customers actively seek out negative reviews when making a purchase decision<sup>[2]</sup>. With reviews playing such a critical role for customers, the method of writing and reading reviews has largely remained the same: reviews consist of a star rating (typically 1-5), review text, and optional media (photos/videos); sorted in a descending order by review date. While the overall star rating (e.g. 4.7 out of 5) and list of reviews is helpful, there is an opportunity to surface additional insights about the product derived from customer reviews to 1) enable customers to make better purchasing decisions in less time and with greater confidence, and 2) enable companies (product managers, designers, engineers, etc) understand what customers really think about their products, and what the top issues and requests are for the product.

### Solution

This project will focus on delivering a solution in two areas:
1. Automatic Topic Grouping: e.g. Screen Resolution, Battery Life, and Scratch Resistance for a mobile phone
2. Sentiment Breakdown by Topic: e.g. 70% positive sentiment for Screen Resolution

The insights above will be automatically delivered directly on the Amazon Product Detail Page (PDP) in the form of an in-line widget powered by a Google Chrome Extension.

### Implementation Approach

#### Review Text Mining
Amazon doesn't have an API to retrieve reviews, so a scraping approach will be taken. Amazon is known to block IPs if they suspect them of scraping, so a client-facing solution executed in the user's browser by the extension is preferred. Puppeteer + Node.js or ScrapingBee will be considered. Scraped review data will be cleaned up and sent to an AWS Lambda to perform the subsequent analysis steps.

#### Review Text Processing
The raw reviews will be tokenized, stopwords removed, lemmatized, and stemmed using the NLTK and gensim libraries through an AWS Lambda function. Finally, we will create a bag of words from the reviews and our corpus.

#### Topic Grouping (Modeling) with LDA
To provide a good user-experience, there is a need to provide our analysis with low latency on the Product Detail Page on Amazon. Depending on the performance of LDA libraries, a tradeoff of accuracy for speed may need to be made. Two of the more popular libraries for LDA using Python are Sklearn and Gensim. Gensim provides more flexibility and the benefit of using GPUs, but GPUs would require a server architecture such as vast.ai or Amazon EC2 vs. using a serverless solution like AWS Lambdas. A technical evaluation between libraries will be completed during the project.

The output of this step will be a set of topics derived from the reviews. 

#### Sentiment Analysis
For each topic, the general sentiment of the reviews will be measured using the NLTK or TextBlob Python library. This will be executed on an AWS Lambda.

#### Chrome Extension
The topics and topic sentiment will be displayed in-line on the Product Detail Page (PDP) on Amazon.com through a Google Chrome Extension. The UI will consist of a summary view and ingress point below the star rating and a larger widget above the "Top reviews" section using the same HTML components and CSS styling that the Amazon site uses for a native experience.

#### Result Caching (Stretch Goal)
Due to the compute resources needed for this solution and the desire to provide a near real-time solution, caching of previous results should be implemented for each product that has been processed through the pipeline. The cache should have a short TTL (e.g., 30-60 days) to ensure the analysis remains accurate and up-to-date. AWS S3 could be used to store the results as JSON.

### Languages
- Extension: HTML, CSS, JavaScript
- Text Mining: Javascript
- Text Processing: Python
- LDA: Python
- Sentiment Analysis: Python

### Measuring Success
- Topic Coherence: I will measure the quality of the topics based on a Topic Coherence measure when determing the # of topics to return based on the review (document) collection.
- User Input: As a stretch goal, I will look to add a user feedback mechanism to the Chrome extension that shows a UI affordance on the product page asking "which of these topics was most useful to you" or "did you find these topics helpful?" with a thumbs up / thumbs down. This data can be stored in a NoSQL DB along with the product ID for future improvements.

### Task Breakdown (LOE Estimates)
- Text Mining: 8 hours
- Text Processing: 2 hours
- LDA: 8 hours (analysis of libraries, implementation, fine tuning parameters, AWS infrastructure)
- Sentiment Anlysis: 4 hours
- Chome Extension: 8 hours (wiring up the various lambdas, integrating the text mining solution, and building the UI)

### References

<sup>[1]</sup> https://spiegel.medill.northwestern.edu/online-reviews/
<sup>[2]</sup> https://www.powerreviews.com/wp-content/uploads/2016/04/PowerofReviews_2016.pdf
