from dkcrawlerv2 import AllSubCategoryCrawler
import asyncio


async def main():
    url = 'https://www.digikey.com/en/products/'
    crawler = AllSubCategoryCrawler(url, headless=False)
    subcat_urls = await crawler.crawl()
    print(subcat_urls)


if __name__ == '__main__':
    asyncio.run(main())
