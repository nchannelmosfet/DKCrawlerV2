import asyncio
import os
import re
import logging
from playwright.async_api import async_playwright
from playwright._impl._api_types import TimeoutError


class AsyncCrawler:
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
        self.create_log_file()
        self.logger = self.set_up_logger()

    def create_log_file(self):
        with open(self.log_file_path, 'w+') as f:
            f.write('')

    def set_up_logger(self):
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s',
            "%Y-%m-%d %H:%M:%S"
        )
        logger = logging.getLogger(self.subcategory)
        if len(logger.handlers) > 0:
            logger.handlers.clear()
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

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

    async def go_next_page(self, page, use_next_page_alt):
        async with page.expect_navigation(wait_until='networkidle'):
            if use_next_page_alt:
                await page.click(self.selectors['next-page-alt'])
                await asyncio.sleep(2.0)
            else:
                await page.click(self.selectors['next-page'])

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
                    filename = f'{self.subcategory}{cur_page}.csv'
                    await self.download(page, filename)
                else:
                    self.logger.warning(f'Page {cur_page} has already been downloaded. ')
                    use_next_page_alt = True
                    await self.scroll_up_down(page)
                    await asyncio.sleep(3.0)

                if len(self.downloaded_pages) == self.max_page or cur_page == self.max_page:
                    break

                try:
                    await self.go_next_page(page, use_next_page_alt)
                    self.logger.info('Go to next page')
                except TimeoutError:
                    pass

            await context.close()
            await browser.close()
            self.logger.info('Crawl finished, closing browser and browser context. ')


async def main():
    start_url = 'https://www.digikey.com/en/products/filter/thermal-heat-sinks/219'
    base_download_dir = r'../download'
    crawler = AsyncCrawler(start_url, base_download_dir, headless=True)
    await crawler.crawl()


if __name__ == '__main__':
    asyncio.run(main())
