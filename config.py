# config.py

# List of starting URLs to crawl.
START_URLS = [
    "https://www.assamcareer.com/search/label/Admission",
    "https://www.assamcareer.com/search/label/Admission?updated-max=2024-07-20T22:07:00%2B05:30&max-results=20&start=20&by-date=false",
    "https://www.assamcareer.com/search/label/Admission?updated-max=2024-05-07T20:55:00%2B05:30&max-results=20&start=40&by-date=false",
    "https://www.assamcareer.com/search/label/Admission?updated-max=2021-08-03T21:39:00%2B05:30&max-results=20&start=60&by-date=false",
    "https://www.assamcareer.com/search/label/Admission?updated-max=2020-06-27T20:48:00%2B05:30&max-results=20&start=74&by-date=false",
]

# CSS selector to target each post container.
CSS_SELECTOR = ".post-outer"

# Required keys that the extraction must return.
REQUIRED_KEYS = [
    "post_title",
    "post_image_url",
    "snippet_summary",
    "jump_link",
]
