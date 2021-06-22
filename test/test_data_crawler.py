from dkcrawlerv2 import AsyncDataCrawler
import asyncio


async def main():
    start_url = 'https://www.digikey.com/en/products/filter/thermal-heat-pipes-vapor-chambers/977'
    base_download_dir = r'../download'
    crawler = AsyncDataCrawler(start_url, base_download_dir, headless=True)
    await crawler.crawl()


if __name__ == '__main__':
    asyncio.run(main())
