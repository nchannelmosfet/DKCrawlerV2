from dkcrawlerv2 import AsyncDataCrawler, AsyncDataCrawlerRunner
import asyncio


async def main():
    # start_urls = 'https://www.digikey.com/en/products/filter/thermal-heat-pipes-vapor-chambers/977'
    # base_download_dir = r'../download'
    # crawler = AsyncDataCrawler(start_url, base_download_dir, headless=True)
    # await crawler.crawl()

    start_urls = [
        'https://www.digikey.com/en/products/filter/thermal-thermoelectric-peltier-modules/222',
        'https://www.digikey.com/en/products/filter/thermal-heat-pipes-vapor-chambers/977',
        'https://www.digikey.com/en/products/filter/thermal-flexible-heaters/1005',
        'https://www.digikey.com/en/products/filter/fans-finger-guards-filters-sleeves/221',
        'https://www.digikey.com/en/products/filter/fans-accessories/223',
        'https://www.digikey.com/en/products/filter/rack-thermal-management/602'
    ]
    base_download_dir = r'../download'
    crawler_runner = AsyncDataCrawlerRunner(start_urls, base_download_dir, headless=False)
    await crawler_runner.crawl()


if __name__ == '__main__':
    asyncio.run(main())
