
BASE_URL = "https://www.assamcareer.com"


CSS_SELECTOR = ".widget.Blog .post-outer"

# Required keys for the extracted data.
# Fields:
#   post_title: from elements with class "entry-title"
#   post_image_url: from the <img> tag inside "post-image-wrap"
#   snippet_summary: from elements with class "snippet-summary"
#   jump_link: URL from the jump-link element (if available)
REQUIRED_KEYS = [
    "post_title",
    "post_image_url",
    "snippet_summary",
    "jump_link",
]
