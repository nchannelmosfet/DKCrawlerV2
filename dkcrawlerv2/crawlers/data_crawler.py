import asyncio
from enum import Enum
import os
import re
from playwright.async_api import async_playwright, Page
from playwright._impl._api_types import TimeoutError
from dkcrawlerv2.utils import (
    get_file_list, concat_data, set_up_logger, remove_url_qs,
    get_batches, get_latest_session_index, jsonify, parse_int, retry_on_exception
)
import pandas as pd
import math


class Selector(str, Enum):
    cookie_ok = 'div.cookie-wrapper a.secondary.button',
    per_page_selector = '[data-testid="per-page-selector"] > div'
    per_page_100 = '[data-testid="per-page-100"]'
    in_stock = '[data-testid="filter--2-option-5"]'
    apply_all = '[data-testid="apply-all-button"]'
    download_popup = '[data-testid="download-table-popup-trigger-button"]'
    download_btn = '[data-testid="download-table-button"]'
    cur_page = '[data-testid="pagination-container"] > button[disabled]'
    next_page = '[data-testid="btn-next-page"]'
    next_page_alt = '[data-testid="pagination-container"] > button[disabled] + button'
    next_page_rendered = '[data-testid="pagination-container"] > button[value="{0}"] + button[disabled]'
    page_nav = '[data-testid="per-page-selector-container"]'
    active_parts = '[data-testid="filter-1989-option-0"]'
    mfpn_sort_asc = 'button[data-testid="sort--100-asc"] > svg'
    remove_filters = '[data-testid="filter-box-remove-all"]'
    mfpn_sorted = '[data-testid="sort--100-asc"][disabled]'
    product_count = '[data-testid="product-count"]'
    usa_domain = '''div.domain-suggest__flag[onclick="__footerDomainSelect('com')"]'''
    product_count_remaining = '[data-testid="product-count-remaining"]'


class AsyncDataCrawler:
    def __init__(self, start_url: str, base_download_dir: str, headless=True, in_stock_only=True):
        self.start_url = start_url
        self.base_download_dir = base_download_dir
        self.headless = headless
        self.in_stock_only = in_stock_only
        self.use_next_page_alt = False

        url_split = remove_url_qs(start_url).split('/')
        self.subcategory = url_split[-2].replace('-', '_')
        self.product_id = url_split[-1]
        self.download_dir = os.path.join(base_download_dir, f'{self.subcategory}_{self.product_id}')
        os.makedirs(self.download_dir, exist_ok=True)

        self.max_page = 0
        self.downloaded_pages = set()

        self.log_file_path = os.path.join(self.download_dir, f'{self.subcategory}.log')
        self.logger = set_up_logger(self.subcategory, self.log_file_path)

    async def config_page(self, page: Page):
        viewport_size = {'width': 1920, 'height': 1080}
        await page.set_viewport_size(viewport_size)
        self.logger.info(f'Set viewport size to: {viewport_size}')

        try:
            await page.click(Selector.cookie_ok)
        except TimeoutError:
            pass

        try:
            await page.click(Selector.usa_domain, timeout=5000)
        except TimeoutError:
            pass

        if self.in_stock_only:
            await page.click(Selector.in_stock)
            product_count_remaining = await page.text_content(Selector.product_count_remaining)
            product_count_remaining = parse_int(product_count_remaining)

            if product_count_remaining <= 1:
                await page.click(Selector.in_stock)
            else:
                await page.click(Selector.apply_all)
                await page.wait_for_selector(Selector.remove_filters)
                self.logger.info('Select only in-stock items. ')

        await page.click(Selector.per_page_selector)
        self.logger.info('Clicked page size selector. ')
        await page.click(Selector.per_page_100)
        self.logger.info('Set page size to 100 item per page. ')

        try:
            await page.wait_for_function(
                '''
                function checkRowCount() {
                    let product_count = parseInt(document.querySelector('[data-testid="product-count"]').textContent);
                    let row_count = document.querySelectorAll('[data-testid="data-table-0-row"]').length;
                    if (product_count < 100) {
                        return row_count === product_count;
                    } else {
                        return row_count === 100;
                    }
                }
                '''
            )
        except TimeoutError:
            pass

        await page.click(Selector.mfpn_sort_asc)
        await page.wait_for_selector(Selector.mfpn_sorted)
        self.logger.info('Sort items by MFR Part# ascending. ')

    async def download(self, page: Page, filename: str):
        async with page.expect_download() as download_info:
            await page.click(Selector.download_popup)
            await page.click(Selector.download_btn)
        download = await download_info.value
        file_path = os.path.join(self.download_dir, filename)
        file_path = os.path.realpath(file_path)
        self.logger.info(f'\nDownloaded {file_path}')
        await download.save_as(file_path)

    @staticmethod
    async def scroll_up_down(page):
        pos_offset = 200
        neg_offset = -200
        for offset in [pos_offset, neg_offset]:
            await page.evaluate(f"window.scrollTo(0, {offset});")

    async def go_next_page(self, page: Page, cur_page: int, use_next_page_alt: bool):
        try:
            async with page.expect_navigation(wait_until='networkidle'):
                if use_next_page_alt:
                    await page.click(Selector.next_page_alt)
                    await page.wait_for_timeout(2000)
                else:
                    await page.click(Selector.next_page)
                await page.wait_for_selector(Selector.next_page_rendered.format(cur_page))
            self.logger.info('Go to next page')
        except TimeoutError:
            pass

    def combine_pages(self):
        in_files = get_file_list(self.download_dir, suffix='.csv')
        out_path = os.path.join(self.download_dir, f'{self.subcategory}_all.xlsx')
        out_path = os.path.realpath(out_path)
        combined_df = concat_data(in_files)
        if any(combined_df['Stock'].astype(str).str.contains('.', regex=False)):
            alert = 'ALERT!\nColumn "Stock" contains decimal numbers.\nColumn misaligned.\nFix data mannually. '
            self.logger.warning(alert)
        combined_df['Stock'] = combined_df['Stock'].astype(str).str.replace(',', '')
        combined_df['Stock'] = pd.to_numeric(combined_df['Stock'], errors='coerce')
        combined_df['Subcategory'] = self.subcategory
        combined_df.to_excel(out_path, index=False)
        self.logger.info(f'{self.subcategory} data combined and saved at: \n{out_path}')

    def all_pages_downloaded(self, cur_page: int):
        return len(self.downloaded_pages) == self.max_page or cur_page == self.max_page

    async def crawl(self):
        async with async_playwright() as playwright:
            browser = await playwright.firefox.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            await page.goto(self.start_url)
            await self.config_page(page)

            page_nav = await page.text_content(Selector.page_nav)
            item_count = int(re.findall(r"of (.+)", page_nav)[0].replace(",", ""))
            self.max_page = math.ceil(item_count / 100)
            self.logger.info(f"Calculated {self.max_page} max page")

            while True:
                cur_page = await self.download_page(page=page, logger=self.logger)
                self.logger.info(f"Download succeeded without retry")

                if self.all_pages_downloaded(cur_page):
                    break

                await self.go_next_page(page, cur_page, self.use_next_page_alt)

            await context.close()
            await browser.close()
            self.logger.info('Crawl finished, closing browser and browser context. ')

    @retry_on_exception(attempts=5, delay=10.0)
    async def download_page(self, page: Page, logger):
        self.use_next_page_alt = False
        cur_page = int(await page.text_content(Selector.cur_page, timeout=60 * 1000))
        if cur_page not in self.downloaded_pages:
            logger.info({'Current Page': cur_page, 'Max Page': self.max_page})
            filename = f'{self.subcategory}_{cur_page}.csv'
            await self.download(page, filename)
            self.downloaded_pages.add(cur_page)
        else:
            logger.warning(f'Page {cur_page} has already been downloaded. ')
            self.use_next_page_alt = True
            await self.scroll_up_down(page)
        return cur_page


class AsyncDataCrawlerRunner:
    def __init__(self, start_urls, base_download_dir, headless=True, in_stock_only=True, session_name=None):
        self.start_urls = start_urls
        self.base_download_dir = base_download_dir
        self.headless = headless
        self.in_stock_only = in_stock_only
        self.max_concurrency = 3

        session_index = get_latest_session_index(self.base_download_dir) + 1
        self.session_name = session_name or f'session{session_index}'
        self.download_dir = os.path.realpath(
            os.path.join(self.base_download_dir, self.session_name)
        )
        os.makedirs(self.download_dir, exist_ok=True)

        log_file_path = os.path.join(self.download_dir, f'{self.session_name}.log')
        self.logger = set_up_logger(self.session_name, log_file_path)

        params = {
            'start_urls': self.start_urls,
            'download_dir': self.download_dir,
            'headless': self.headless,
            'max_concurrency': self.max_concurrency,
        }
        pretty_params = jsonify(params)
        self.logger.info(
            f'CrawlerRunner initialized with params:\n{pretty_params}'
        )

    async def create_crawl_job(self, url: str):
        crawler = AsyncDataCrawler(url, self.download_dir, self.headless, self.in_stock_only)
        self.logger.info(f'Created crawl job for URL: {url}')
        try:
            await crawler.crawl()
        except TimeoutError as ex:
            error_msg = {
                'url': url,
                'error': 'Timeout exceeded.',
                'msg': 'Retry crawling with AppSubCat'
            }
            self.logger.error(jsonify(error_msg))
            self.logger.error("==========Full Error Message==========")
            self.logger.error(ex)
            self.logger.error("======================================")
        crawler.combine_pages()

    async def crawl_all(self):
        tasks = [self.create_crawl_job(url) for url in self.start_urls]
        for task_batch in get_batches(tasks, batch_size=self.max_concurrency):
            await asyncio.gather(*task_batch)

    def combine_subcat_data(self):
        in_files = get_file_list(self.download_dir, suffix='all.xlsx')
        out_path = os.path.join(self.download_dir, 'combine.xlsx')
        df = concat_data(in_files)
        df.to_excel(out_path)
        self.logger.info(
            f'Combined common-column data of all subcategories. \n'
            f'Exported combined data to {out_path}'
        )
