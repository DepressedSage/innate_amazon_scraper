import scrapy
from urllib.parse import urljoin
DOMAIN = "co.uk"

class AmazonReviewsSpider(scrapy.Spider):
    name = "amazon_get_reviews"

    custom_settings = {
        'FEEDS': { f'data/reviews_{DOMAIN}%(name)s_%(time)s.csv': { 'format': 'csv',}}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asin_list = kwargs.get('asin_list', [])

    def start_requests(self):
        asin_list = ['B01M7SEIA6']
        # for asin in self.asin_list:
        for asin in asin_list:
            amazon_reviews_url = f'https://www.amazon.{DOMAIN}/product-reviews/{asin}/'
            yield scrapy.Request(url=amazon_reviews_url, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': 0})


    def parse_reviews(self, response):
        asin = response.meta['asin']
        retry_count = response.meta['retry_count']

        next_page_relative_url = response.css(".a-pagination .a-last>a::attr(href)").get()
        print()
        print()
        print(next_page_relative_url)
        print()
        print()
        if next_page_relative_url is not None:
            retry_count = 0
            next_page = urljoin(f'https://www.amazon.{DOMAIN}/', next_page_relative_url)
            yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': retry_count})

        ## Adding this retry_count here so we retry any amazon js rendered review pages
        elif retry_count < 3:
            retry_count = retry_count+1
            yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, 'retry_count': retry_count})


        ## Parse Product Reviews
        review_elements = response.css("#cm_cr-review_list div.review")
        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0],
                    }