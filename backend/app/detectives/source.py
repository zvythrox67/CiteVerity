# detectives/source.py - Detective 2: Source Tracker
import re
from concurrent.futures import ThreadPoolExecutor

from .base import Detective
from ..scoring import Penalty
from ..utils import split_url, registered_domain, safe_get

PRIMARY_SUFFIX_PARTS = {"gov", "edu", "mil", "int", "ac"}
PRIMARY_DOMAINS = {"doi.org", "nih.gov", "arxiv.org", "who.int", "europa.eu", "un.org",
                   "courtlistener.com", "nature.com", "science.org", "thelancet.com",
                   "nejm.org", "bmj.com", "plos.org"}
SOCIAL_DOMAINS = {"facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com",
                  "reddit.com", "youtube.com", "t.me", "medium.com", "substack.com",
                  "blogspot.com", "wordpress.com"}
AGGREGATORS = {"news.google.com", "flipboard.com", "msn.com", "yahoo.com", "newsbreak.com",
               "google.com", "bing.com"}

ESTABLISHED_OUTLETS = {"reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org", "nytimes.com",
                       "washingtonpost.com", "theguardian.com", "wsj.com", "bloomberg.com",
                       "economist.com", "aljazeera.com", "cnn.com", "usatoday.com", "nbcnews.com",
                       "cbsnews.com"}

VAGUE_PHRASES = ["experts say", "studies show", "scientists say", "research shows",
                 "many people say", "sources say", "they say that"]
UNFALSIFIABLE_PHRASES = ["everyone knows", "it's obvious", "it is obvious", "wake up", "common sense"]


def is_primary(url):
    parts = split_url(url)
    suffix_bits = set(parts.suffix.split("."))
    if suffix_bits & PRIMARY_SUFFIX_PARTS:
        return True
    return parts.registered_domain in PRIMARY_DOMAINS


def link_type(url):
    d = registered_domain(url)
    if is_primary(url):
        return "primary"
    if d in SOCIAL_DOMAINS:
        return "social"
    if d in AGGREGATORS:
        return "aggregator"
    return "other"


def count_hard_data(text):
    numbers = re.findall(r"\b\d[\d,\.]*%?", text)
    years = re.findall(r"\b(?:19|20)\d\d\b", text)
    months = re.findall(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", text, flags=re.I)
    return len(numbers) + len(years) + len(months)


def check_falsifiable(text):
    penalties = []
    words = len(text.split())
    if words < 100:
        return penalties

    lower = text.lower().replace("\u2019", "'")
    hard = count_hard_data(text)

    if hard == 0:
        penalties.append(Penalty("non_falsifiable", 4, "Zero numbers, dates or statistics in the whole text"))
        penalties.append(Penalty("non_falsifiable", 2, "No dates or timeframes given"))
    elif hard < 3:
        penalties.append(Penalty("non_falsifiable", 3, "Almost no numbers or dates (" + str(hard) + " found)"))

    for phrase in UNFALSIFIABLE_PHRASES:
        if phrase in lower:
            penalties.append(Penalty("non_falsifiable", 1, "Unfalsifiable wording: '" + phrase + "'"))
            break

    for phrase in VAGUE_PHRASES:
        if phrase in lower:
            penalties.append(Penalty("no_outbound_evidence", 2, "Vague attribution: '" + phrase + "' (who exactly?)"))
            break
    return penalties


def is_dead(url):
    r = safe_get(url, timeout=4)
    return r is not None and r.status_code in (404, 410)


def check_links(page):
    penalties = []
    links = page.extra.get("links", [])

    if is_primary(page.url):
        page.extra["source_label"] = "Primary Source"
        return penalties

    if len(links) == 0:
        page.extra["source_label"] = "Secondary Source"
        if registered_domain(page.url) in ESTABLISHED_OUTLETS:
            penalties.append(Penalty("no_outbound_evidence", 0, "Established outlet with editorial standards."))
        else:
            penalties.append(Penalty("no_outbound_evidence", 30, "Page has zero outbound links backing up its claims"))
        return penalties

    types = [link_type(l) for l in links]
    primary_count = types.count("primary")

    if primary_count / len(links) >= 0.5:
        page.extra["source_label"] = "Primary Source"
    else:
        page.extra["source_label"] = "Secondary Source"

    page.extra["link_breakdown"] = {t: types.count(t) for t in set(types)}

    if primary_count == 0:
        penalties.append(Penalty("dead_end_trail", 4, "No link to any official or primary source anywhere"))
        if all(t in ("social", "aggregator") for t in types):
            penalties.append(Penalty("dead_end_trail", 2, "Links only go to social media or aggregators"))
        elif "social" in types or "aggregator" in types:
            penalties.append(Penalty("dead_end_trail", 1, "Some links go to social media or aggregators"))

    sample = links[:5]
    with ThreadPoolExecutor(max_workers=5) as pool:
        dead = list(pool.map(is_dead, sample))
    if sum(dead) >= 2:
        penalties.append(Penalty("dead_end_trail", 2, str(sum(dead)) + " of " + str(len(sample)) + " checked links are broken (404)"))
    return penalties


class SourceDetective(Detective):
    name = "Source Tracker"

    def investigate(self, page):
        penalties = check_links(page)
        penalties += check_falsifiable(page.text)
        return penalties