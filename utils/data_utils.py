import csv
from models.venue import Venue

def is_duplicate_venue(venue_title: str, seen_titles: set) -> bool:
    return venue_title in seen_titles

def is_complete_venue(venue: dict, required_keys: list) -> bool:
    return all(key in venue for key in required_keys)

def save_venues_to_csv(venues: list, filename: str):
    if not venues:
        print("No venues to save.")
        return

    fieldnames = Venue.model_fields.keys()
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(venues)
        print(f"Saved {len(venues)} venues to '{filename}'.")
    except PermissionError as e:
        print(f"PermissionError: {e}. Check if the file is open or if you have write permission.")
