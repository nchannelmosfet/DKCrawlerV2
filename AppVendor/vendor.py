from dkcrawlerv2 import AsyncDataCrawlerRunner, VendorSubCategoryCrawler
from dkcrawlerv2.utils import read_urls
import asyncio
import os


async def main():
    vendor_url = ''
    vendor_url = vendor_url or read_urls('vendor_url.txt')[0]
    vendor_name = vendor_url.split('/')[-1]
    base_download_dir = os.path.join(os.path.dirname(__file__), 'downloads', vendor_name)
    os.makedirs(base_download_dir, exist_ok=True)

    target_vendor_only = True
    in_stock_only = True
    headless = False
    log_file_path = os.path.join(base_download_dir, f'{vendor_name}.log')

    vendor_crawler = VendorSubCategoryCrawler(
        vendor_url,
        log_file_path=log_file_path,
        target_vendor_only=target_vendor_only,
        in_stock_only=in_stock_only,
        headless=headless,
    )
    subcat_urls = await vendor_crawler.crawl()

    crawler_runner = AsyncDataCrawlerRunner(
        subcat_urls, base_download_dir,
        headless=headless, session_name=None,
        in_stock_only=in_stock_only
    )
    await crawler_runner.crawl_all()
    crawler_runner.combine_subcat_data()


if __name__ == '__main__':
    asyncio.run(main())
