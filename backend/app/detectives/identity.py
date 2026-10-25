# detectives/identity.py - Detective 1: Identity & Date Checker
import re
from datetime import datetime, timezone
from difflib import get_close_matches

from dateutil import parser as dateparser

from .base import Detective
from ..scoring import Penalty
from ..utils import (get_soup, get_json_ld, split_url, registered_domain,
                     safe_get, wayback_first_seen)

BAD_SUFFIXES = {"xyz", "top", "click", "shop", "biz", "buzz", "icu", "loan","win", "bid", "tk", "ml", "ga", "cf", "gq", "work", "rest"}

KNOWN_OUTLETS = ["reuters", "bbc", "nytimes", "washingtonpost", "theguardian", "cnn", "apnews", "npr", "nature", "sciencemag", "nih", "who", "cdc", "wsj", "bloomberg", "forbes", "usatoday", "foxnews", "nbcnews", "cbsnews", "abcnews", "politico", "economist", "aljazeera"]

FAKE_AUTHORS = {"admin", "administrator", "staff", "editor", "webmaster", "guest", "user", "unknown", "anonymous", "news desk", "newsdesk", "team"}

SOCIAL_FORUMS = {"reddit.com", "quora.com", "medium.com", "substack.com", "facebook.com", "twitter.com", "x.com", "tumblr.com", "pinterest.com", "tiktok.com"}

def clean_author(name):
    if not name:
        return None
    name = re.sub(r"^\s*by\s+", "", name.strip(), flags=re.I)
    name = name.strip(" ,|-")
    if len(name) < 3 or len(name) > 80:
        return None
    if name.lower() in FAKE_AUTHORS:
        return None
    return name


def author_from_json(author):
    if isinstance(author, str):
        return author
    if isinstance(author, dict):
        return author.get("name")
    if isinstance(author, list):
        for a in author:
            n = author_from_json(a)
            if n:
                return n
    return None


def find_author(soup):
    for name in ["author", "article:author", "byline", "dc.creator", "parsely-author", "twitter:creator",
                 "citation_author", "citation_authors", "dc.contributor"]:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
        if tag and tag.get("content"):
            got = clean_author(tag["content"].split(";")[0])
            if got:
                return got
    for item in get_json_ld(soup):
        got = clean_author(author_from_json(item.get("author")))
        if got:
            return got
    tag = (soup.find(attrs={"rel": "author"}) or soup.find(attrs={"itemprop": "author"})
           or soup.find(class_=re.compile("byline|author", re.I)))
    if tag:
        got = clean_author(tag.get_text(" ", strip=True))
        if got:
            return got
    return None


def check_author(soup):
    penalties = []
    author = find_author(soup)
    if author is None:
        penalties.append(Penalty("anonymous_author", 30, "No author name found in meta tags, JSON-LD or byline"))
        return author, penalties

    has_bio = soup.find("a", href=re.compile(r"about|author|bio|team|staff", re.I)) is not None
    if not has_bio:
        penalties.append(Penalty("anonymous_author", 1, "No link to an author bio or About page"))
    text = soup.get_text(" ", strip=True).lower()
    if "@" not in text and "contact" not in text:
        penalties.append(Penalty("anonymous_author", 1, "No contact info found on the page"))
    return author, penalties


def check_domain(url):
    penalties = []
    parts = split_url(url)
    suffix = parts.suffix.split(".")[-1]
    label = parts.domain.lower()
    reg_domain = parts.registered_domain.lower()

    
    if reg_domain in SOCIAL_FORUMS:
        penalties.append(Penalty("suspicious_domain", 20, "Domain is a social media site or user-generated forum"))

    if suffix in BAD_SUFFIXES:
        penalties.append(Penalty("suspicious_domain", 10, "Domain ending '." + suffix + "' is heavily used by junk sites"))

    squashed = label.replace("-", "")
    if label not in KNOWN_OUTLETS:
        close = get_close_matches(squashed, KNOWN_OUTLETS, n=1, cutoff=0.85)
        if close:
            penalties.append(Penalty("suspicious_domain", 10, "Domain '" + label + "' looks like '" + close[0] + "' (possible fake)"))
        else:
            for outlet in KNOWN_OUTLETS:
                if len(outlet) >= 4 and squashed.startswith(outlet) and squashed[len(outlet):] in ("news", "daily", "live", "official", "times", "post"):
                    penalties.append(Penalty("suspicious_domain", 10, "Domain '" + label + "' copies the name '" + outlet + "'"))
                    break

    age = domain_age_days(parts.registered_domain)
    if age is not None and age < 180:
        penalties.append(Penalty("suspicious_domain", 5, "Domain was only registered " + str(age) + " days ago"))
    return penalties


def domain_age_days(domain):
    if not domain:
        return None
    r = safe_get("https://rdap.org/domain/" + domain, timeout=6)
    if r is None or r.status_code != 200:
        return None
    try:
        for event in r.json().get("events", []):
            if event.get("eventAction") == "registration":
                made = dateparser.parse(event["eventDate"])
                if made.tzinfo:
                    made = made.astimezone(timezone.utc).replace(tzinfo=None)
                return (datetime.now(timezone.utc).replace(tzinfo=None) - made).days
    except Exception:
        pass
    return None


def to_naive(dt):
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def find_publish_date(soup):
    meta_names = ["article:published_time", "og:article:published_time", "datePublished",
                  "date", "pubdate", "publish-date", "dc.date.issued", "parsely-pub-date",
                  "citation_publication_date", "citation_date", "citation_online_date", "dc.date"]
    candidates = []
    for name in meta_names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            candidates.append(tag["content"])
    for item in get_json_ld(soup):
        if item.get("datePublished"):
            candidates.append(item["datePublished"])
    t = soup.find("time", attrs={"datetime": True})
    if t:
        candidates.append(t["datetime"])

    for c in candidates:
        try:
            return to_naive(dateparser.parse(c))
        except Exception:
            continue
    return None


def year_in_url(url):
    m = re.search(r"/((?:19|20)\d\d)/(\d{1,2})/", url)
    return int(m.group(1)) if m else None


def check_old_story(url, soup):
    penalties = []
    published = find_publish_date(soup)

    if published is None:
        penalties.append(Penalty("old_story_repackaged", 2, "No publish date found in the page code"))
    else:
        url_year = year_in_url(url)
        if url_year and abs(url_year - published.year) >= 1:
            penalties.append(Penalty("old_story_repackaged", 6,
                             "URL says " + str(url_year) + " but page claims " + str(published.year)))

        first_seen = wayback_first_seen(url)
        if first_seen and (published - first_seen).days > 365:
            penalties.append(Penalty("old_story_repackaged", 10,
                             "Wayback Machine has this page from " + first_seen.strftime("%Y-%m-%d")
                             + " but it claims " + published.strftime("%Y-%m-%d")))
    return published, penalties


class IdentityDetective(Detective):
    name = "Identity & Date Checker"

    def investigate(self, page):
        soup = get_soup(page.html)
        penalties = []

        author, p = check_author(soup)
        penalties += p
        page.extra["author"] = author

        penalties += check_domain(page.url)

        published, p = check_old_story(page.url, soup)
        penalties += p
        page.extra["published_date"] = published.strftime("%Y-%m-%d") if published else None

        return penalties