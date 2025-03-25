import asyncio
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_utils import save_venues_to_csv
from utils.scraper_utils import fetch_and_process_page, get_browser_config, get_llm_strategy

load_dotenv()

async def crawl_items():
    """
    Crawl pages from AssamCareer.com by following the "blog-pager-older-link" until no new page is found
    or until 10 pages have been crawled.
    It checks for a status message in "status-msg-body" to decide if new pages are available.
    """
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "assamcareer_session"

    all_items = []
    seen_titles = set()
    current_url = BASE_URL  
    page_count = 0  

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while current_url and page_count < 10:
            print(f"Processing page {page_count + 1}: {current_url}")
            items, next_page_url = await fetch_and_process_page(
                crawler,
                current_url,
                CSS_SELECTOR,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_titles,
            )
            if not items:
                print(f"No items extracted from {current_url}. Ending crawl.")
                break
            all_items.extend(items)
            page_count += 1  
            if not next_page_url:
                print("No further pages found. Ending crawl.")
                break
            current_url = next_page_url
            await asyncio.sleep(2)  

    if all_items:
        save_venues_to_csv(all_items, "assamcareer_items.csv")
        print(f"Saved {len(all_items)} items to 'assamcareer_items.csv'.")
    else:
        print("No items were found during the crawl.")

    llm_strategy.show_usage()

async def main():
    await crawl_items()

if __name__ == "__main__":
    asyncio.run(main())
