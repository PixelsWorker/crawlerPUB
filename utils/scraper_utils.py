import json
import os
from typing import List, Set, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
import asyncio

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)
from models.page import Page
from utils.data_utils import is_complete_venue, is_duplicate_venue

def get_browser_config() -> BrowserConfig:
    print("[DEBUG] Initializing browser configuration...")
    return BrowserConfig(
        browser_type="chromium",
        headless=False,
        verbose=True,
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    print("[DEBUG] Setting up LLM extraction strategy...")
    return LLMExtractionStrategy(
        provider="openrouter/deepseek/deepseek-r1:free",
        api_token=os.getenv("OPENROUTER_API_KEY"),
        schema=Page.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Given the following HTML content, extract a JSON array of objects where each object corresponds to one job post. "
            "Each job post is contained in a div with class 'post-outer'. For each post, extract the following fields:\n"
            "  - post_title: the text content of the anchor inside the h1 element with class 'post-title entry-title'.\n"
            "  - post_image_url: the value of the 'src' attribute of the img tag inside the div with class 'post-image-wrap'.\n"
            "  - snippet_summary: the text content of the div with class 'snippet-summary'.\n"
            "  - jump_link: the href attribute of the anchor inside the div with class 'jump-link' (if available; otherwise, use an empty string).\n"
            "Return only a JSON array of objects with these fields."
        ),
        input_format="html",
        verbose=True,
    )

async def extract_next_page_url_with_wait(cleaned_html: str) -> Optional[str]:
    print("[DEBUG] Extracting next page URL...")
    soup = BeautifulSoup(cleaned_html, "html.parser")
    next_link = soup.find("a", class_="blog-pager-older-link")
    if next_link and next_link.has_attr("href"):
        url = next_link["href"].split("#")[0]
        print(f"[DEBUG] Found next page URL: {url}")
        return url
    print("[DEBUG] Next page URL not found immediately, waiting 3 seconds...")
    await asyncio.sleep(3)
    soup = BeautifulSoup(cleaned_html, "html.parser")
    next_link = soup.find("a", class_="blog-pager-older-link")
    if next_link and next_link.has_attr("href"):
        url = next_link["href"].split("#")[0]
        print(f"[DEBUG] Found next page URL after waiting: {url}")
        return url
    print("[DEBUG] No next page URL found after waiting.")
    return None

async def fetch_jump_link_table(jump_url: str) -> List[dict]:
    print(f"[DEBUG] Fetching jump link table from: {jump_url}")
    results = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jump_url)
            response.raise_for_status()
            html = response.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="tablepress")
        if table:
            rows = table.find_all("tr")
            if rows and rows[0].find_all("th"):
                rows = rows[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    jump_name = cells[0].get_text(strip=True)
                    a_tag = cells[1].find("a")
                    jump_url_text = a_tag["href"] if a_tag and a_tag.has_attr("href") else ""
                    results.append({"jump_name": jump_name, "jump_url": jump_url_text})
            print(f"[DEBUG] Extracted {len(results)} entries from jump link table.")
        else:
            print("[DEBUG] No table with class 'tablepress' found on jump link page.")
    except Exception as e:
        print(f"[ERROR] Error fetching or parsing jump link table from {jump_url}: {e}")
    return results

# Global debug list to accumulate debug info for each page.
DEBUG_RECORDS = []

async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_titles: Set[str],
) -> Tuple[List[dict], Optional[str]]:
    url = url.split("#")[0]
    print(f"[DEBUG] Loading main page: {url}")
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )
    if not (result.success and result.extracted_content):
        print(f"[ERROR] Failed to fetch page: {result.error_message}")
        return [], None

    # Save a debug record for this page
    debug_record = {
        "url": url,
        "html_snippet": result.cleaned_html[:1000],
        "extracted_data": result.extracted_content[:1000],
    }
    DEBUG_RECORDS.append(debug_record)

    try:
        extracted_data = json.loads(result.extracted_content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing error: {e}")
        return [], None
    if not extracted_data:
        print("[DEBUG] No items found on the page.")
        return [], None
    print("[DEBUG] Extracted data:", extracted_data)
    complete_items = []
    for item in extracted_data:
        print("[DEBUG] Processing item:", item)
        if item.get("error") is False:
            item.pop("error", None)
        if not is_complete_venue(item, required_keys):
            print("[DEBUG] Item incomplete; skipping.")
            continue
        if is_duplicate_venue(item["post_title"], seen_titles):
            print(f"[DEBUG] Duplicate item '{item['post_title']}' found; skipping.")
            continue
        seen_titles.add(item["post_title"])
        jump_link = item.get("jump_link", "").strip()
        if jump_link:
            jump_link = jump_link.split("#")[0]
            print(f"[DEBUG] Fetching jump link table from: {jump_link}")
            table_data = await fetch_jump_link_table(jump_link)
            item["jump_table"] = table_data
        else:
            item["jump_table"] = []
        complete_items.append(item)
    
    print("[DEBUG] Waiting 5 seconds for dynamic content before extracting next page URL...")
    await asyncio.sleep(5)
    next_page_url = await extract_next_page_url_with_wait(result.cleaned_html)
    if next_page_url:
        print(f"[DEBUG] Next page URL extracted: {next_page_url}")
    else:
        print("[DEBUG] No next page URL found.")
    print(f"[DEBUG] Extracted {len(complete_items)} items from the page.")
    return complete_items, next_page_url
