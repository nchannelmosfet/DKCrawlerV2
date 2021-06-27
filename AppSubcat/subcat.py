from dkcrawlerv2 import AsyncDataCrawlerRunner
from dkcrawlerv2.utils import read_urls
import asyncio
import os


async def main():
    start_urls = []
    start_urls = start_urls or read_urls('subcat_urls.txt')
    base_download_dir = os.path.join(os.path.dirname(__file__), 'downloads')

    headless = True
    session_name = None
    crawler_runner = AsyncDataCrawlerRunner(
        start_urls, base_download_dir,
        headless=headless, session_name=session_name
    )

    await crawler_runner.crawl_all()
    crawler_runner.combine_subcat_data()


if __name__ == '__main__':
    asyncio.run(main())
