import asyncio
from playwright.async_api import async_playwright
from dkcrawlerv2.utils import set_up_logger
from urllib.parse import urljoin


class SubCategoryURLCrawler:
    def __init__(self, url, headless=True, log_file_path=None):
        self.url = url
        self.headless = headless
        self.log_file_path = log_file_path
        self.logger = set_up_logger(self.__class__.__name__, self.log_file_path)

    async def scroll_to_bottom(self, page):
        y_offset = 0
        offset_step = 900
        scroll_times = 0
        while True:
            y_offset_js = '() => window.pageYOffset;'
            old_y_offset = await page.evaluate(y_offset_js)
            y_offset += offset_step
            await asyncio.sleep(1)
            await page.evaluate(f"window.scrollTo(0, {y_offset});")
            scroll_times += 1
            self.logger.info(f'Scroll down by {offset_step} pixels. Scrolled {scroll_times} times. ')
            new_y_offset = await page.evaluate(y_offset_js)
            if old_y_offset == new_y_offset:
                self.logger.info('Reached bottom of page. ')
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
            subcat_urls_out = '\n'.join(subcat_urls)
            self.logger.info(f'Extracted subcategory URLs: \n{subcat_urls_out}')
            return subcat_urls
