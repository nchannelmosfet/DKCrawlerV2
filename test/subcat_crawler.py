from dkcrawlerv2 import SubCategoryURLCrawler
import asyncio


async def main():
    url = 'https://www.digikey.com/en/products/'
    crawler = SubCategoryURLCrawler(url, headless=False)
    subcat_urls = await crawler.crawl()
    print(subcat_urls)


if __name__ == '__main__':
    asyncio.run(main())
