import os
import subprocess
import pandas as pd
# Define the list of keywords you want to scrape
keyword_list = ['krill oil']
domain_list = ["fr","com"]
max_pages = 5
# Run the Scrapy spider script as a subprocess

# for domain in {'fr'}:
#     for keyword in keyword_list:
#         print(domain)
#         subprocess.run(
#             [
#                 'scrapy', 'crawl', 'amazon_product_search',
#                 '-a',f'keyword={keyword}',
#                 '-a',f'domain={domain}',
#                 '-a',f'max_pages={max_pages}',
#                 '-O',f'{domain}_{keyword}_amazon_product_search_%(time)s.csv'
#             ]
#         )

os.makedirs("./reviews",exist_ok=True)
for domain in ["cn","fr","com"]:
    df = pd.read_csv(f"./{domain}_krill_oil_amazon_product_search_2023-10-06.csv")
    asin_list = list(df['asin'][:20])
    # print(keyword_list)
    for keyword in keyword_list:
        subprocess.run(
            [
                'scrapy', 'crawl', 'get_reviews', 
                '-a', f'asin_list={",".join(asin_list)}',
                '-a',f'domain={domain}',
                '-O',f'./reviews/{domain}_{keyword}_amazon_reviews_%(time)s.csv'
            ]
        )