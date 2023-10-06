import json
import scrapy
from urllib.parse import urljoin
import re
MAX_PAGES = 5

class AmazonSearchProductSpider(scrapy.Spider):
    name = "amazon_product_search"

    # custom_settings = {
    #     'FEEDS': { f'data/{domain}_%(name)s_%(time)s.csv': { 'format': 'csv',}}
    #     }

    # custom_settings = {
    #     'FEEDS': {}
    #     }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = kwargs.get('keyword_list',self.keyword)
        self.domain = kwargs.get('domain', self.domain)
        self.maximum_pages = kwargs.get('max_pages',self.max_pages)
        # path = f'./data/product_search_{self.domain}_{self.keyword}_%(time)s.csv'
        # print(path)
        # self.custom_settings['FEEDS'] = { f'data/{self.domain}_%(name)s_%(time)s.csv': { 'format': 'csv',}}
        # self.custom_settings['FEEDS'] = { f'./data/product_search_{self.domain}_{self.keyword}_%(time)s.csv': { 'format': 'csv',}}

    def start_requests(self):
        # keyword = ['krill oil']
        keyword = "+".join(self.keyword.split())
        domain = self.domain
        # print(domain)
        amazon_search_url = f'https://www.amazon.{domain}/s?k={keyword}&s=review-rank&page=1'
        # print()
        # print()
        # print(amazon_search_url)
        # print()
        # print()
        yield scrapy.Request(
            url=amazon_search_url, 
            callback=self.discover_product_urls, 
            meta={
                'keyword': keyword,
                'page': 1,
                'domain' : domain
                }
            )

    def discover_product_urls(self, response):
        page = response.meta['page']
        keyword = response.meta['keyword'] 
        domain = response.meta['domain']
        max_pages = int(self.max_pages)

        ## Discover Product URLs
        search_products = response.css("div.s-result-item[data-component-type=s-search-result]")
        for product in search_products:
            relative_url = product.css("h2>a::attr(href)").get()
            product_url = urljoin(f'https://www.amazon.{domain}/', relative_url).split("?")[0]

            asin = relative_url.split("/")[-2]
            page_name = relative_url.split("/")[1]

            yield scrapy.Request(
                url=product_url, 
                callback=self.parse_product_data, 
                meta={
                    'keyword': keyword, 
                    'page': page, 
                    'asin': asin, 
                    'product_url':product_url,
                    'page_name' : page_name,
                    'domain' : domain,
                    }
                )
            
        ## Get All Pages
        if page == 1:
            available_pages = response.xpath(
                '//*[contains(@class, "s-pagination-item")][not(has-class("s-pagination-separator"))]/text()'
            ).getall()

            # print(type(available_pages[-1]))
            last_page = min(int(available_pages[-1]), max_pages)
            for page_num in range(2, int(last_page)):

                amazon_search_url = f'https://www.amazon.{domain}/s?k={keyword}&s=review-rank&page={page_num}'

                yield scrapy.Request(
                    url=amazon_search_url, 
                    callback=self.discover_product_urls, 
                    meta={
                        'keyword': keyword, 
                        'page': page_num,
                        'domain' : domain
                        }
                    )
        

    def parse_product_data(self, response):
        asin = response.meta['asin']
        product_url = response.meta['product_url']
        page_name = response.meta['page_name']

        image_data = json.loads(re.findall(r"colorImages':.*'initial':\s*(\[.+?\])},\n", response.text)[0])
        variant_data = re.findall(r'dimensionValuesDisplayData"\s*:\s* ({.+?}),\n', response.text)
        feature_bullets = [bullet.strip() for bullet in response.css("#feature-bullets li ::text").getall()]
        price = response.css('.a-price span[aria-hidden="true"] ::text').get("")

        if not price:
            price = response.css('.a-price .a-offscreen ::text').get("")

        yield {
            "asin" : asin,
            "product_url" : product_url,
            "page_name" : page_name,
            "title_name": response.css("#productTitle::text").get("").strip(),
            "price": price,
            "stars": response.css("i[data-hook=average-star-rating] ::text").get("").strip(),
            "rating_count": response.css("div[data-hook=total-review-count] ::text").get("").strip(),
            "feature_bullets": feature_bullets,
            "images": image_data,
            "variant_data": variant_data,
        }