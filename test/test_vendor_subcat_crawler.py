from dkcrawlerv2 import VendorSubCategoryCrawler
import asyncio


async def main():
    url = 'https://www.digikey.com/en/supplier-centers/assmann-wsw-components'
    crawler = VendorSubCategoryCrawler(url, headless=True, log_file_path='awsw.log')
    subcat_urls = await crawler.crawl()
    print(subcat_urls)
    print(f'Extract {len(subcat_urls)} URLs for vendor assmann-wsw-components. ')


if __name__ == '__main__':
    asyncio.run(main())
