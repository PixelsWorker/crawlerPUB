from pydantic import BaseModel

class Page(BaseModel):
    """
    Represents a job post (page) from www.assamcareer.com.

    Fields:
      post_title: The title from the element with class "entry-title".
      post_image_url: The image URL from the <img> tag inside elements with class "post-image-wrap".
      snippet_summary: A brief summary from the element with class "snippet-summary".
      jump_link: The URL from the jump-link element (if available).
      jump_table: A list of dictionaries extracted from the jump_link page's table.
                  Each dictionary contains:
                    - jump_name: Text from column‑1.
                    - jump_url: URL from column‑2.
    """
    post_title: str
    post_image_url: str
    snippet_summary: str
    jump_link: str = ""
    jump_table: list = []
