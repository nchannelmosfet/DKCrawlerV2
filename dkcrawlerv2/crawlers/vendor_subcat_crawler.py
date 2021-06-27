import asyncio
import re
from playwright.async_api import async_playwright
from playwright._impl._page import Page
from dkcrawlerv2.utils import set_up_logger, jsonify, remove_url_qs
from urllib.parse import urljoin
import random


class VendorSubCategoryCrawler:
    def __init__(self, vendor_url, headless=True, log_file_path=None, target_vendor_only=True, in_stock_only=True):
        self.vendor_url = vendor_url
        self.headless = headless
        self.log_file_path = log_file_path
        self.target_vendor_only = target_vendor_only
        self.in_stock_only = in_stock_only

        self.vendor_name = self.vendor_url.split('/')[-1]
        self.logger = set_up_logger(self.vendor_name, self.log_file_path)
        self.subcat_url_info = []
        self.selectors = {
            'cookie_ok': 'div.cookie-wrapper a.secondary.button',
            'in-stock': '[data-testid="filter--2-option-5"]',
            'apply-all': '[data-testid="apply-all-button"]',
            'remove-filters': '[data-testid="filter-box-remove-all"]',
            'product-count': '[data-testid="product-count"]',
        }

    async def crawl(self):
        self.subcat_url_info = []
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
            self.subcat_url_info = sorted(self.subcat_url_info, key=lambda item: item['product_count'], reverse=True)
            sorted_subcat_urls = [item['url'] for item in self.subcat_url_info]
            return sorted_subcat_urls

    async def parse_subcat(self, page: Page, cat_url):
        await page.goto(cat_url)
        cur_url = page.url

        processing_msg = {
            'url': cur_url,
            'action': 'processing'
        }
        self.logger.info(jsonify(processing_msg))

        await asyncio.sleep(1)
        final_subcat_urls = []
        if 'filter' in cur_url:
            min_qty = await page.text_content('[data-atag="tr-minQty"] > span > div:last-child')
            if min_qty == 'Non-Stock' and self.in_stock_only:
                ignored_msg = {
                    'url': cur_url,
                    'action': 'ignored',
                    'reason': f'All products are non-stock in this subcategory for {self.vendor_name}.'
                }
                self.logger.info(jsonify(ignored_msg))
                return []
            else:
                if not self.target_vendor_only:
                    # remove query string to select all vendors for the subcategory
                    cur_url = remove_url_qs(cur_url)
                    await page.goto(cur_url)

                await page.click(self.selectors['in-stock'])
                await page.click(self.selectors['apply-all'])
                await page.wait_for_selector(self.selectors['remove-filters'])
                self.logger.info('Select only in-stock items. ')

                product_count = await page.text_content(self.selectors['product-count'])
                product_count = int(re.sub(r'\D', '', product_count))
                url_info = {'url': cur_url, 'product_count': product_count}
                self.subcat_url_info.append(url_info)
                self.logger.info(f'Collected {jsonify(url_info)}')
                return final_subcat_urls

        elif 'products/detail' in cur_url:
            ignored_msg = {
                'url': cur_url,
                'action': 'ignored',
                'reason': f"Current URL is a product detail page. "
            }
            self.logger.info(jsonify(ignored_msg))
            return []
        else:
            subcat_elems = await page.query_selector_all('[data-testid="subcategories-items"]')
            subcat_urls = [urljoin(self.vendor_url, await el.get_attribute('href'))
                           for el in subcat_elems]

            further_processing_msg = {
                'url': cur_url,
                'action': 'Further processing of sub urls. ',
                'sub_urls': subcat_urls,
            }
            self.logger.info(jsonify(further_processing_msg))
            for url in subcat_urls:
                urls = await self.parse_subcat(page, url)
                final_subcat_urls += urls
            return final_subcat_urls
