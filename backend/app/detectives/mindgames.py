# detectives/mindgames.py - Detective 4: Mind-Games & AI Catcher
import re
import statistics
from difflib import SequenceMatcher

from .base import Detective
from ..scoring import Penalty
from ..utils import safe_get

CLICKBAIT = [
    ("deletion panic", 4, ["before it's deleted", "before it gets deleted", "before they delete",
                           "before it's taken down", "before it's banned", "before it's too late",
                           "before they ban"]),
    ("hidden truth", 4, ["they don't want you to know", "what they won't tell you", "the secret they",
                         "they hid from you", "what they're hiding", "what they are hiding",
                         "the truth they", "shocker"]),
    ("fear framing", 2, ["they are lying to you", "wake up", "your life is in danger", "you are being lied to"]),
    ("countdown pressure", 2, ["act now", "before midnight", "limited time", "last chance", "hours left"]),
    ("share urgency", 1, ["share this", "send this to everyone", "spread the word", "forward this", "share before"]),
]


def check_clickbait(text):
    penalties = []
    lower = text.lower().replace("\u2019", "'")

    for name, points, phrases in CLICKBAIT:
        for phrase in phrases:
            if phrase in lower:
                penalties.append(Penalty("emotional_urgency", points, "Manipulative wording (" + name + "): '" + phrase + "'"))
                break

    words = text.split()
    caps = [w for w in words if len(w) >= 4 and w.isupper() and w.isalpha()]
    if (len(words) > 0 and len(caps) / len(words) > 0.05) or text.count("!!") >= 2:
        penalties.append(Penalty("emotional_urgency", 2, "ALL CAPS or too many exclamation marks"))
    return penalties


def ai_style_score(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 2]
    if len(lengths) < 10:
        return None
    mean = statistics.mean(lengths)
    cv = statistics.pstdev(lengths) / mean
    score = (0.6 - cv) / 0.3
    return round(max(0.0, min(1.0, score)), 2)


AUTHOR_YEAR = re.compile(r"\(([A-Z][A-Za-z\-']+)(?: et al\.?| (?:&|and) [A-Z][A-Za-z\-']+)?,? ((?:19|20)\d\d)\)")
DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
QUOTED_TITLE = re.compile(r"(?:titled|entitled|study|paper|book|article)\s+[\u201c\"]([^\u201d\"]{15,200})[\u201d\"]", re.I)

CROSSREF = "https://api.crossref.org/works"


def find_citations(text):
    dois = [d.rstrip(".,;)") for d in DOI.findall(text)]
    return {
        "author_year": AUTHOR_YEAR.findall(text),
        "dois": list(dict.fromkeys(dois)),
        "titles": QUOTED_TITLE.findall(text),
    }


def doi_exists(doi):
    r = safe_get(CROSSREF + "/" + doi, timeout=8)
    if r is None:
        return None
    if r.status_code == 404:
        return False
    return r.status_code == 200


def title_exists(title):
    r = safe_get(CROSSREF, params={"query.title": title, "rows": 1}, timeout=8)
    if r is None or r.status_code != 200:
        return None
    try:
        items = r.json()["message"]["items"]
        if not items or not items[0].get("title"):
            return False
        best = items[0]["title"][0]
        return SequenceMatcher(None, title.lower(), best.lower()).ratio() >= 0.7
    except Exception:
        return None


def author_published_in(surname, year):
    r = safe_get(CROSSREF, params={"query.author": surname,
                                   "filter": "from-pub-date:" + year + ",until-pub-date:" + year,
                                   "rows": 10}, timeout=8)
    if r is None or r.status_code != 200:
        return None
    try:
        for item in r.json()["message"]["items"]:
            for a in item.get("author", []):
                if a.get("family", "").lower() == surname.lower():
                    return True
        return False
    except Exception:
        return None


def check_citations(page):
    penalties = []
    text = page.text + " " + " ".join(page.extra.get("links", []))
    found = find_citations(text)
    page.extra["citations_found"] = {k: len(v) for k, v in found.items()}

    for title in found["titles"][:5]:
        if title_exists(title) is False:
            penalties.append(Penalty("fake_citations", 8, "Cited work '" + title[:60] + "' not found in Crossref"))

    for doi in found["dois"][:5]:
        if doi_exists(doi) is False:
            penalties.append(Penalty("fake_citations", 4, "DOI " + doi + " returns no record"))

    for surname, year in list(dict.fromkeys(found["author_year"]))[:5]:
        if author_published_in(surname, year) is False:
            penalties.append(Penalty("fake_citations", 3, "No author named '" + surname + "' published anything in " + year))
    return penalties


class MindGamesDetective(Detective):
    name = "Mind-Games & AI Catcher"

    def investigate(self, page):
        penalties = check_clickbait(page.text)
        page.extra["ai_style_score"] = ai_style_score(page.text)
        penalties += check_citations(page)
        return penalties