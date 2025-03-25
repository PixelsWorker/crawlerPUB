import json
import os
import re
from typing import List, Set, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)

from models.venue import Venue
from utils.data_utils import is_complete_venue, is_duplicate_venue

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="chromium",
        headless=False,
        verbose=True,
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    # Updated instruction to include jump_link field.
    return LLMExtractionStrategy(
        provider="openrouter/deepseek/deepseek-r1:free",  # Use the correct provider string
        api_token=os.getenv("OPENROUTER_API_KEY"),
        schema=Venue.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract all job post objects with the following fields:\n"
            "- post_title: the title from the element with class 'entry-title'\n"
            "- post_image_url: the image URL from the <img> tag inside elements with class 'post-image-wrap'\n"
            "- snippet_summary: a brief summary from the element with class 'snippet-summary'\n"
            "- jump_link: the URL of the jump-link from the element (if available)\n"
            "Return the result as JSON."
        ),
        input_format="html",  # Using HTML input for extraction
        verbose=True,
    )

def extract_next_page_url(cleaned_html: str) -> Optional[str]:
    """
    Extracts the next page URL from the HTML.
    It looks for an element with class "status-msg-body" to check if there are posts.
    If "No posts with label" is found, returns None.
    Otherwise, it searches for an anchor with class "blog-pager-older-link" and returns its href.
    """
    soup = BeautifulSoup(cleaned_html, "html.parser")
    status_elem = soup.find(class_="status-msg-body")
    if status_elem:
        text = status_elem.get_text(strip=True)
        if "No posts with label" in text:
            return None
        elif "Showing posts with label" in text:
            # Proceed to extract the next page URL
            next_link = soup.find("a", class_="blog-pager-older-link")
            if next_link and next_link.has_attr("href"):
                return next_link["href"]
    else:
        # Fallback: try to extract the next page URL even if status-msg-body is not found.
        next_link = soup.find("a", class_="blog-pager-older-link")
        if next_link and next_link.has_attr("href"):
            return next_link["href"]
    return None

async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_titles: Set[str],
) -> Tuple[List[dict], Optional[str]]:
    """
    Fetches and processes a single page given a full URL.
    Returns a tuple: (list of processed items, next page URL or None).
    """
    print(f"Loading page: {url}")

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
        print(f"Error fetching page: {result.error_message}")
        return [], None

    try:
        extracted_data = json.loads(result.extracted_content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return [], None

    if not extracted_data:
        print("No items found on the page.")
        return [], None

    print("Extracted data:", extracted_data)

    complete_items = []
    for item in extracted_data:
        print("Processing item:", item)
        if item.get("error") is False:
            item.pop("error", None)
        if not is_complete_venue(item, required_keys):
            continue
        # Use "post_title" for duplicate checking
        if is_duplicate_venue(item["post_title"], seen_titles):
            print(f"Duplicate item '{item['post_title']}' found. Skipping.")
            continue
        seen_titles.add(item["post_title"])

        # If a jump_link is present, fetch the table data from that page
        jump_link = item.get("jump_link", "").strip()
        if jump_link:
            print(f"Fetching jump link table from: {jump_link}")
            table_data = await fetch_jump_link_table(jump_link)
            item["jump_table"] = table_data
        else:
            item["jump_table"] = []

        complete_items.append(item)

    if not complete_items:
        print("No complete items found on the page.")

    # Now, extract the next page URL from the page's HTML using the new function.
    next_page_url = extract_next_page_url(result.cleaned_html)
    if next_page_url:
        print(f"Next page URL extracted: {next_page_url}")
    else:
        print("No next page URL found.")

    print(f"Extracted {len(complete_items)} items from the page.")
    return complete_items, next_page_url

async def fetch_jump_link_table(jump_url: str) -> List[dict]:
    """
    Fetches the jump_link page and extracts data from the table with class 'tablepress'.
    It extracts:
      - jump_name: from column-1
      - jump_url: from column-2
    Returns a list of dictionaries.
    """
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
            # If the first row is header (contains <th>), skip it.
            if rows and rows[0].find_all("th"):
                rows = rows[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    jump_name = cells[0].get_text(strip=True)
                    a_tag = cells[1].find("a")
                    jump_url_text = a_tag["href"] if a_tag and a_tag.has_attr("href") else ""
                    results.append({"jump_name": jump_name, "jump_url": jump_url_text})
    except Exception as e:
        print(f"Error fetching or parsing jump link table from {jump_url}: {e}")
    return results
