from pydantic import BaseModel

class Venue(BaseModel):
    post_title: str
    post_image_url: str
    snippet_summary: str
    jump_link: str = ""
    jump_table: list = []
