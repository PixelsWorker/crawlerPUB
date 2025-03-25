import asyncio
from typing import Tuple  # Ensure Tuple is imported
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import START_URLS, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_utils import save_venues_to_csv, save_debug_csv
from utils.scraper_utils import fetch_and_process_page, get_browser_config, get_llm_strategy, DEBUG_RECORDS

load_dotenv()

async def crawl_single_url(start_url: str, max_pages: int = 10) -> list:
    print(f"[INFO] Starting crawl for URL: {start_url}")
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "assamcareer_session"
    all_items = []
    seen_titles = set()
    current_url = start_url.split("#")[0]
    page_count = 0

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while current_url and page_count < max_pages:
            print(f"[INFO] Processing page {page_count + 1}: {current_url}")
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
                print(f"[INFO] No items extracted from {current_url}. Ending crawl for this URL.")
                break
            all_items.extend(items)
            page_count += 1
            if not next_page_url:
                print("[INFO] No further pages found. Ending crawl for this URL.")
                break
            current_url = next_page_url.split("#")[0]
            print(f"[INFO] Next page URL set to: {current_url}")
            await asyncio.sleep(2)
    print(f"[INFO] Completed crawl for URL: {start_url} with {len(all_items)} items.")
    return all_items

async def crawl_multiple_urls():
    all_results = []
    for url in START_URLS:
        results = await crawl_single_url(url)
        all_results.extend(results)
    if all_results:
        save_venues_to_csv(all_results, "assamcareer_items.csv")
        print(f"[INFO] Saved {len(all_results)} items to 'assamcareer_items.csv'.")
    else:
        print("[INFO] No items were found during the crawl.")
    # Save debug information to a separate CSV file.
    save_debug_csv(DEBUG_RECORDS, "assamcareer_debug.csv")

async def main():
    await crawl_multiple_urls()

if __name__ == "__main__":
    asyncio.run(main())
