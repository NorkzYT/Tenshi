import os
from urllib.parse import urlparse


def filename_for_index(src_url: str, idx: int) -> str:
    """
    Given an image URL and a zero‑based index, return
    a filename like '000.jpg', '001.png', etc.
    """
    ext = os.path.splitext(urlparse(src_url).path)[1] or ".jpg"
    return f"{idx:03d}{ext}"
