from dkcrawlerv2 import AllSubCategoryCrawler
import asyncio


async def main():
    url = 'https://www.digikey.com/en/products/'
    crawler = AllSubCategoryCrawler(url, headless=False, log_file_path='subcat_urls.log')
    subcat_urls = await crawler.crawl()
    print(f'Extract {len(subcat_urls)} subcategory URLs. ')


if __name__ == '__main__':
    asyncio.run(main())
