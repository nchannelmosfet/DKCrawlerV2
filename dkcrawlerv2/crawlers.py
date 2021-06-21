import asyncio
import os
import re
from playwright.async_api import async_playwright
from playwright._impl._api_types import TimeoutError
from dkcrawlerv2.utils import get_file_list, concat_data, set_up_logger
import pandas as pd
from urllib.parse import urljoin


class AllSubCategoryCrawler:
    def __init__(self, url, headless=True):
        self.url = url
        self.headless = headless

    async def scroll_to_bottom(self, page):
        y_offset = 0
        offset_step = 900
        while True:
            y_offset_js = '() => window.pageYOffset;'
            old_y_offset = await page.evaluate(y_offset_js)
            y_offset += offset_step
            await asyncio.sleep(1)
            await page.evaluate(f"window.scrollTo(0, {y_offset});")
            new_y_offset = await page.evaluate(y_offset_js)
            if old_y_offset == new_y_offset:
                break

    async def crawl(self):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(self.url)
            await self.scroll_to_bottom(page)
            subcat_elems = await page.query_selector_all('[data-testid="subcategories-items"]')
            subcat_urls = [await el.get_attribute('href') for el in subcat_elems]
            subcat_urls = [urljoin(self.url, url) for url in subcat_urls]
            return subcat_urls


class AsyncDataCrawler:
    def __init__(self, start_url, base_download_dir, headless=True):
        self.start_url = start_url
        self.base_download_dir = base_download_dir
        self.headless = headless
        self.selectors = {
            'cookie_ok': 'div.cookie-wrapper a.secondary.button',
            'per-page-selector': '[data-testid="per-page-selector"] > div.MuiSelect-root',
            'per-page-100': '[data-testid="per-page-100"]',
            'confirm-per-page-100': '[data-testid="per-page-selector"] > input[value="100"]',
            'in-stock': '[data-testid="filter--2-option-5"]',
            'normally-stocking': '[data-testid="filter--2-option-9"] input[type="checkbox"]',
            'apply-all': '[data-testid="apply-all-button"]',
            'download-popup': '[data-testid="download-table-popup-trigger-button"]',
            'download-btn': '[data-testid="download-table-button"]',
            'cur-page': '[data-testid="pagination-container"] > button[disabled]',
            'next-page': '[data-testid="btn-next-page"]',
            'next-page-alt': '[data-testid="pagination-container"] > button[disabled] + button',
            'next-page-rendered': '[data-testid="pagination-container"] > button[value="{0}"] + button[disabled]',
            'page-nav': '[data-testid="per-page-selector-container"] > div:last-child > span',
            'active-parts': '[data-testid="filter-1989-option-0"]',
            'digikey.com': '[track-data="Choose Your Location – Stay on US Site"] > span',
            'msg_close': 'a.header-shipping-msg-close',
            'btn-first-page': '[data-testid="btn-first-page"]',
            'dkpn-sort-asc': 'button[data-testid="sort--104-asc"] > svg',
            'remove-filters': '[data-testid="filter-box-remove-all"]',
            'dkpn-sorted': '[data-testid="sort--104-asc"][disabled]',
        }

        url_split = start_url.split('/')
        self.subcategory = url_split[-2].replace('-', '_')
        self.product_id = url_split[-1]
        self.download_dir = os.path.join(base_download_dir, f'{self.subcategory}_{self.product_id}')
        os.makedirs(self.download_dir, exist_ok=True)

        self.max_page = 0
        self.downloaded_pages = set()

        self.log_file_path = os.path.join(self.download_dir, f'{self.subcategory}.log')
        self.logger = set_up_logger(self.subcategory, self.log_file_path)

    async def config_page(self, page):
        viewport_size = {'width': 1920, 'height': 1080}
        await page.set_viewport_size(viewport_size)
        self.logger.info(f'Set viewport size to: {viewport_size}')

        await page.click(self.selectors['cookie_ok'])
        await page.click(self.selectors['in-stock'])
        await page.click(self.selectors['apply-all'])
        await page.wait_for_selector(self.selectors['remove-filters'])
        self.logger.info('Select only in-stock items. ')

        await page.click(self.selectors['per-page-selector'])
        await page.click(self.selectors['per-page-100'])
        await page.wait_for_function(
            '''
            () => document.querySelectorAll('[data-testid="data-table-0-row"]').length === 100;
            '''
        )
        self.logger.info('Set page size to 100 item per page. ')

        await page.click(self.selectors['dkpn-sort-asc'])
        await page.wait_for_selector(self.selectors['dkpn-sorted'])
        self.logger.info('Sort items by DK Part# ascending. ')

    async def download(self, page, filename):
        async with page.expect_download() as download_info:
            await page.click(self.selectors['download-popup'])
            await page.click(self.selectors['download-btn'])
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

    async def go_next_page(self, page, cur_page, use_next_page_alt):
        async with page.expect_navigation(wait_until='networkidle'):
            if use_next_page_alt:
                await page.click(self.selectors['next-page-alt'])
                await asyncio.sleep(2.0)
            else:
                await page.click(self.selectors['next-page'])
            await page.wait_for_selector(self.selectors['next-page-rendered'].format(cur_page))

    def combine_data(self):
        in_files = get_file_list(self.download_dir, suffix='.csv')
        out_path = os.path.join(self.download_dir, f'{self.subcategory}_all.xlsx')
        out_path = os.path.realpath(out_path)
        combined_data = concat_data(in_files)
        if any(combined_data['Stock'].astype(str).str.contains('.', regex=False)):
            alert = 'ALERT!\nColumn "Stock" contains decimal numbers.\nColumn misaligned.\nFix data mannually. '
            self.logger.warning(alert)
        combined_data['Stock'] = combined_data['Stock'].astype(str).str.replace(',', '')
        combined_data['Stock'] = pd.to_numeric(combined_data['Stock'], errors='coerce')
        combined_data['Subcategory'] = self.subcategory
        combined_data.to_excel(out_path, index=False)
        self.logger.info(f'{self.subcategory} data combined and saved at: \n{out_path}')

    async def crawl(self):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            await page.goto(self.start_url)
            await self.config_page(page)

            page_nav = await page.text_content(self.selectors['page-nav'])
            self.max_page = int(re.findall(r'/(\d+)|$', page_nav)[0])

            while True:
                use_next_page_alt = False
                cur_page = int(await page.text_content(self.selectors['cur-page']))
                if cur_page not in self.downloaded_pages:
                    self.downloaded_pages.add(cur_page)
                    self.logger.info({'Current Page': cur_page, 'Max Page': self.max_page})
                    filename = f'{self.subcategory}_{cur_page}.csv'
                    await self.download(page, filename)
                else:
                    self.logger.warning(f'Page {cur_page} has already been downloaded. ')
                    use_next_page_alt = True
                    await self.scroll_up_down(page)

                if len(self.downloaded_pages) == self.max_page or cur_page == self.max_page:
                    break

                try:
                    await self.go_next_page(page, cur_page, use_next_page_alt)
                    self.logger.info('Go to next page')
                except TimeoutError:
                    pass

            await context.close()
            await browser.close()
            self.logger.info('Crawl finished, closing browser and browser context. ')
            self.combine_data()
