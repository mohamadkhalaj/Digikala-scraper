#!/usr/bin/python3
import asyncio
import json
import logging
import os
import sys
from time import perf_counter

import aiohttp


class DigiKalaScraper:
    MAX_RETRIES = 5
    MAX_CONCURRENT_REQUESTS = 15

    def __init__(self):
        self.TOTAL_SUCCESS = 0
        self.logger = logging.getLogger("DigiKalaScraper")

        # Set up console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.category_name = ""

    def parse_url(self, category_url):
        splitted = category_url.split("/")
        category = splitted[4].replace("category-", "")
        and_or_no = "&" if len(splitted[-1]) != 0 else "?"
        self.category_name = category
        return f"https://api.digikala.com/v1/categories/{category}/search/{splitted[-1]}{and_or_no}page="

    async def make_request(self, session, url, semaphore, retries=5):
        async with semaphore:
            while retries > 0:
                try:
                    async with session.get(url, timeout=8) as resp:
                        if resp.status == 200:
                            self.TOTAL_SUCCESS += 1
                            self.logger.info(
                                f"[{self.TOTAL_SUCCESS}] Successful! [200]"
                            )
                            return await resp.json()
                        else:
                            self.logger.warning(
                                f"Request failed with status code {resp.status}. Retrying..."
                            )
                            retries -= 1
                except asyncio.TimeoutError:
                    self.logger.warning("Request timed out. Retrying...")
                    retries -= 1
                except aiohttp.client_exceptions.ClientConnectorError as msg:
                    self.logger.error(msg)
            await asyncio.sleep(0.1)
        self.logger.error("Max retries exceeded. Giving up.")

    def get_products_url(self, pages_data):
        return [
            f"https://api.digikala.com/v1/product/{product['id']}/"
            for page in pages_data
            if page
            and page.get("status", None) == 200
            and len(page.get("data", {}).get("products", []))
            for product in page["data"]["products"]
        ]

    def get_suggestions(self, products):
        base_url = "https://www.digikala.com"
        return {
            base_url
            + product["data"]["product"]["url"]["uri"]: product["data"]["product"].get(
                "suggestion", {"count": 0, "percentage": 0}
            )
            for product in products
            if product and product["data"]["product"].get("url", None)
        }

    async def fetch_data(self, session, url_list, fetch_method):
        semaphore = asyncio.Semaphore(value=self.MAX_CONCURRENT_REQUESTS)
        tasks = [
            fetch_method(session, url, semaphore, self.MAX_RETRIES) for url in url_list
        ]
        return await asyncio.gather(*tasks)

    async def fetch_pages_data(self, session, page_urls):
        return await self.fetch_data(session, page_urls, self.make_request)

    async def fetch_product_data(self, session, product_urls):
        return await self.fetch_data(session, product_urls, self.make_request)

    def get_unique_filename(self, base_filename):
        file_number = 1
        while os.path.isfile(
            filename := f"{base_filename}_files{'_' + str(file_number) if file_number > 1 else ''}.json"
        ):
            file_number += 1
        return filename

    def save_to_file(self, data, filename):
        with open(filename, "w") as output_json_file:
            json.dump(
                sorted(
                    data.items(),
                    key=lambda x: (x[1]["count"], x[1]["percentage"]),
                    reverse=True,
                ),
                output_json_file,
            )

    async def main(self):
        url = sys.argv[1] if len(sys.argv) > 1 else ""  # Your custom url.
        assert url != "", "Url could not be empty."
        url = self.parse_url(url)
        category_filename = self.get_unique_filename(self.category_name)
        page_urls = [url + str(page) for page in range(100)]
        async with aiohttp.ClientSession() as session:
            tic = perf_counter()
            pages_data = await self.fetch_pages_data(session, page_urls)
            product_urls = self.get_products_url(pages_data)

            product_data = await self.fetch_product_data(session, product_urls)
            toc = perf_counter()
            self.logger.info(f"Elapsed time: {toc - tic:.2f}s")
            suggestions = self.get_suggestions(product_data)
            number_of_urls = len(product_urls)
            self.logger.info(f"#Product URLS: {number_of_urls}")
            number_of_products = len(suggestions)
            self.logger.info(f"#Products: {number_of_products}")
            self.logger.info(f"#Lost data: {number_of_urls - number_of_products}")

            self.save_to_file(suggestions, category_filename)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    scraper = DigiKalaScraper()
    asyncio.run(scraper.main())
