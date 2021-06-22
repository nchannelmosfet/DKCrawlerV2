import asyncio
from playwright.async_api import async_playwright
from playwright._impl._page import Page
from dkcrawlerv2.utils import set_up_logger
from urllib.parse import urljoin
from playwright._impl._api_types import TimeoutError
import random


class VendorSubCategoryCrawler:
    def __init__(self, vendor_url, headless=True, log_file_path=None):
        self.vendor_url = vendor_url
        self.headless = headless
        self.log_file_path = log_file_path
        self.vendor_name = self.vendor_url.split('/')[-1]
        self.logger = set_up_logger(self.vendor_name, self.log_file_path)
        self.subcat_urls = []

    async def crawl(self):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            await page.set_viewport_size({'width': 1920, 'height': 1080})
            await page.goto(self.vendor_url)

            cat_elems = await page.query_selector_all('#product-categories li > a')
            cat_urls = [await el.get_attribute('href') for el in cat_elems]
            cat_urls = [urljoin(self.vendor_url, url) for url in cat_urls]

            subcat_urls = []
            for url in cat_urls:
                subcat_urls += await self.parse_subcat(page, url)
            random.shuffle(subcat_urls)

            await context.close()
            await browser.close()
            return subcat_urls

    async def parse_subcat(self, page: Page, cat_url):
        await page.goto(cat_url)
        cur_url = page.url

        self.logger.info(f'Processing {cur_url}. ')

        await asyncio.sleep(1)
        final_subcat_urls = []
        if 'filter' in cur_url:
            min_qty = await page.text_content('[data-atag="tr-minQty"] > span > div:last-child')
            if min_qty == 'Non-Stock':
                self.logger.info(f'Ignore {cur_url}.')
                self.logger.info(f'All products are non-stock in this subcategory for {self.vendor_name}.')
                return []
            else:
                final_subcat_urls += cur_url.split('?')[0:1]
                self.logger.info(f'Collected {final_subcat_urls}. ')
                return final_subcat_urls
        elif 'products/detail' in cur_url:
            self.logger.info(f'Ignore {cur_url}. ')
            self.logger.info(f"Current URL is a product detail page. ")
            return []
        else:
            subcat_elems = await page.query_selector_all('[data-testid="subcategories-items"]')
            subcat_urls = [urljoin(self.vendor_url, await el.get_attribute('href')) for el in subcat_elems]
            for url in subcat_urls:
                urls = await self.parse_subcat(page, url)
                final_subcat_urls += urls
            return final_subcat_urls
