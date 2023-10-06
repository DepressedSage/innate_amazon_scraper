import scrapy
from urllib.parse import urljoin

class AmazonReviewsSpider(scrapy.Spider):
    name = "get_reviews"

    handle_httpstatus_list = [404]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asin_list = kwargs.get('asin_list', [])
        print()
        print()
        print(self.asin_list)
        self.domain = kwargs.get('domain', self.domain)

    def start_requests(self):
        domain = self.domain
        asin_list = self.asin_list.split(",")
        for asin in asin_list:
            amazon_reviews_url = f'https://www.amazon.{domain}/product-reviews/{asin}/'
            print(amazon_reviews_url)
            yield scrapy.Request(
                url=amazon_reviews_url, 
                callback=self.parse_reviews, 
                meta={
                    'asin': asin,
                    'retry_count': 0,
                    'page_num': 1,
                    'domain' : domain,
                    }
                )

    def parse_reviews(self, response):
        asin = response.meta['asin']
        retry_count = response.meta['retry_count']
        page_num = response.meta['page_num']
        status_code = response.status
        prev_url = response.url
        domain = response.meta['domain']

        ref_string = "ref=cm_cr_arp_d_paging_btm_next"
        if status_code == 404:
            if prev_url.split("/")[-1].split("?")[0][:-2] == "ref=cm_cr_arp_d_paging_btm_next":
                ref_string = "ref=cm_cr_getr_d_paging_btm_next"
            elif prev_url.split("/")[-1].split("?")[0][:-2] == "ref=cm_cr_getr_d_paging_btm_next":
                ref_string = "ref=cm_cr_arp_d_paging_btm_next"

        check_next_page = response.css(".a-pagination .a-last>a::attr(href)").get()
        if check_next_page:
            page_num += 1
            next_page_relative_url = f"ref={ref_string}_{page_num}?ie=UTF8&reviewerType=all_reviews&pageNumber={page_num}"
            # next_page_relative_url = f"ref=cm_cr_getr_d_paging_btm_next_{page_num}?ie=UTF8&reviewerType=all_reviews&pageNumber={page_num}"
            retry_count = 0
            next_page = urljoin(f'https://www.amazon.{domain}/product-reviews/{asin}/', next_page_relative_url)
            yield scrapy.Request(
                url=next_page, 
                callback=self.parse_reviews, 
                meta={
                    'asin': asin, 
                    'retry_count': retry_count, 
                    'page_num':page_num,
                    'domain' : domain
                }
            )

        ## Adding this retry_count here so we retry any amazon js rendered review pages
        elif retry_count < 3:
            retry_count = retry_count+1
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_reviews, 
                dont_filter=True,
                meta={
                    'asin': asin, 
                    'retry_count': retry_count, 
                    'page_num':page_num,
                    'domain' : domain
                }
            )

        ## Parse Product Reviews
        review_elements = response.css("#cm_cr-review_list div.review")
        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").get().split()[0],
                    # "rating": review_element.css("i[data-asin='" + asin + "'] span::text").re(r"(\d+\.*\d*) out"),
                    }