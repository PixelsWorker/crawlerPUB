import csv
import os
from models.page import Page

def is_duplicate_venue(page_title: str, seen_titles: set) -> bool:
    return page_title in seen_titles

def is_complete_venue(page: dict, required_keys: list) -> bool:
    return all(key in page for key in required_keys)

def save_venues_to_csv(pages: list, filename: str):
    if not pages:
        print("No pages to save.")
        return
    file_exists = os.path.isfile(filename)
    fieldnames = Page.model_fields.keys()
    try:
        with open(filename, mode="a" if file_exists else "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(pages)
        print(f"Saved {len(pages)} pages to '{filename}'.")
    except PermissionError as e:
        print(f"PermissionError: {e}. Please ensure the file is not open or change the output path.")

def save_debug_csv(debug_data: list, filename: str):
    """Saves debug records to a CSV file.
    
    Each record is a dictionary with keys: 'url', 'html_snippet', 'extracted_data'.
    """
    if not debug_data:
        print("No debug data to save.")
        return
    fieldnames = ['url', 'html_snippet', 'extracted_data']
    try:
        with open(filename, mode="a" if os.path.isfile(filename) else "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not os.path.isfile(filename):
                writer.writeheader()
            writer.writerows(debug_data)
        print(f"Saved debug data with {len(debug_data)} records to '{filename}'.")
    except PermissionError as e:
        print(f"PermissionError: {e}. Please ensure the file is not open or change the output path.")
