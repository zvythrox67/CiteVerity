from datetime import datetime
from io import BytesIO
from urllib.parse import urljoin

import imagehash
from PIL import Image

from .base import Detective
from .identity import find_publish_date
from ..scoring import Penalty
from ..utils import get_soup, safe_get, wayback_first_seen

SKIP_WORDS = ["logo", "icon", "sprite", "avatar", "pixel", "tracking", "banner", "ads"]


def find_images(soup, base_url, limit=3):
    urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src or src.startswith("data:"):
            continue
        full = urljoin(base_url, src)
        if any(w in full.lower() for w in SKIP_WORDS):
            continue
        if full not in urls:
            urls.append(full)
    return urls[:limit]


def fingerprint(img_url):
    r = safe_get(img_url, timeout=8)
    if r is None or r.status_code != 200 or len(r.content) > 5_000_000:
        return None
    try:
        return str(imagehash.phash(Image.open(BytesIO(r.content))))
    except Exception:
        return None


def reverse_image_search(img_url):
    return None


def earliest_seen(img_url):
    from_search = reverse_image_search(img_url)
    if from_search:
        return from_search
    return wayback_first_seen(img_url)


class ImageDetective(Detective):
    name = "Image Matcher"

    def investigate(self, page):
        penalties = []
        soup = get_soup(page.html)
        published = find_publish_date(soup)
        page.extra["images"] = []

        images = find_images(soup, page.url)
        if not images:
            return penalties

        if soup.find("figcaption") is None:
            penalties.append(Penalty("decontext_image", 1, "Images have no caption or credit"))

        for url in images:
            info = {"url": url, "phash": fingerprint(url), "first_seen": None}
            first = earliest_seen(url)
            if first:
                info["first_seen"] = first.strftime("%Y-%m-%d")
                if published and (published - first).days > 730:
                    penalties.append(Penalty("decontext_image", 3,
                        "Image was online by " + info["first_seen"] + ", years before this story (" + published.strftime("%Y-%m-%d") + ")"))
            page.extra["images"].append(info)
        return penalties