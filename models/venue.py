from pydantic import BaseModel

class Venue(BaseModel):
    """
    Represents a job post from www.assamcareer.com.

    Fields:
      post_title: The title of the job post, extracted from elements with class "entry-title".
      post_image_url: The URL of the image, extracted from the <img> tag inside "post-image-wrap".
      snippet_summary: A brief summary, extracted from the element with class "snippet-summary".
      jump_link: The URL of the detail page (jump-link) to follow for additional table data.
      jump_table: A list of dictionaries extracted from the table in the jump-link page.
                  Each dictionary has:
                    - jump_name: the text from column-1.
                    - jump_url: the URL from column-2.
    """
    post_title: str
    post_image_url: str
    snippet_summary: str
    jump_link: str = ""
    jump_table: list = []
