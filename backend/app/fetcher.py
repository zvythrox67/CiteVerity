import re

from .detectives.base import PageData
from .utils import (safe_get, html_to_text, outbound_links, get_soup, get_title,
                    get_json_ld, registered_domain)

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")


def find_doi(soup, text):
    for name in ["citation_doi", "dc.identifier", "prism.doi", "doi"]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            m = DOI_RE.search(tag["content"])
            if m:
                return m.group(0).rstrip(".,;)")
    m = DOI_RE.search(text)
    return m.group(0).rstrip(".,;)") if m else None


def find_publisher(soup, url):
    tag = soup.find("meta", attrs={"property": "og:site_name"})
    if tag and tag.get("content"):
        return tag["content"].strip()

    for name in ["citation_publisher", "citation_journal_title"]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()

    for item in get_json_ld(soup):
        pub = item.get("publisher")
        if isinstance(pub, dict) and pub.get("name"):
            return pub["name"]
        if isinstance(pub, str) and pub:
            return pub

    return registered_domain(url)


def fetch_page(url):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    r = safe_get(url, timeout=12)
    if r is None:
        raise Exception("could not connect to that site")
    if r.status_code >= 400:
        raise Exception("site returned status " + str(r.status_code))

    soup = get_soup(r.text)
    page = PageData(url=str(r.url), html=r.text, text=html_to_text(r.text))
    page.extra["title"] = get_title(soup)
    page.extra["links"] = outbound_links(r.text, page.url)
    page.extra["publisher"] = find_publisher(soup, page.url)
    page.extra["doi"] = find_doi(soup, page.text)
    return page