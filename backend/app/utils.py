import re
import json
import time
from datetime import datetime
from urllib.parse import urljoin

import httpx
import tldextract
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CiteVerity hackathon project)"}
_extract = tldextract.TLDExtract(suffix_list_urls=())

_CACHE = {}
CACHE_TTL = 300


def _cached(key, fn):
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    val = fn()
    _CACHE[key] = (now, val)
    return val


def split_url(url):
    return _extract(url)


def registered_domain(url):
    return _extract(url).registered_domain


def safe_get(url, timeout=8, **kwargs):
    try:
        return httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True, **kwargs)
    except Exception:
        return None


def get_soup(html):
    return BeautifulSoup(html, "lxml")


def html_to_text(html):
    soup = get_soup(html)
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def get_title(soup):
    tag = soup.find("meta", attrs={"property": "og:title"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def outbound_links(html, base_url):
    soup = get_soup(html)
    my_domain = registered_domain(base_url)
    found = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        if not full.startswith("http"):
            continue
        d = registered_domain(full)
        if d and d != my_domain and full not in found:
            found.append(full)
    return found


def get_json_ld(soup):
    results = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                results.append(item)
                for sub in item.get("@graph", []):
                    if isinstance(sub, dict):
                        results.append(sub)
    return results


def wayback_first_seen(url):
    def _do():
        r = safe_get("https://archive.org/wayback/available",
                     params={"url": url, "timestamp": "19960101"})
        if r is None or r.status_code != 200:
            return None
        try:
            snap = r.json()["archived_snapshots"]["closest"]["timestamp"]
            return datetime.strptime(snap[:8], "%Y%m%d")
        except Exception:
            return None
    return _cached(("wayback", url), _do)