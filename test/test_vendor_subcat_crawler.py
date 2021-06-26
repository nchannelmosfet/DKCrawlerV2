from dkcrawlerv2 import VendorSubCategoryCrawler
import asyncio


async def main():
    vendor_url = 'https://www.digikey.com/en/supplier-centers/assmann-wsw-components'
    vendor_name = vendor_url.split('/')[-1]
    crawler = VendorSubCategoryCrawler(vendor_url, headless=True, log_file_path='test_vendor.log')
    subcat_urls = await crawler.crawl()
    print(crawler.subcat_url_info)
    print(subcat_urls)
    print(f'Extract {len(subcat_urls)} URLs for vendor {vendor_name}. ')


if __name__ == '__main__':
    asyncio.run(main())
