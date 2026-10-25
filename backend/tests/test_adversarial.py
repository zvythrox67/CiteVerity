import io
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import quote

from PIL import Image

from app.fetcher import fetch_page
from app.pipeline import analyze_page


class FakeResp:
    def __init__(self, text="", status=200, json_data=None, content=b"", url=""):
        self.text = text
        self.status_code = status
        self._json = json_data
        self.content = content
        self.url = url

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 30, 30)).save(buf, format="PNG")
    return buf.getvalue()


def ddg_html(results):
    links = "".join('<a class="result__a" href="//duckduckgo.com/l/?uddg=' + quote(u, safe="") + '">' + t + "</a>"
                    for t, u in results)
    return "<html><body>" + links + "</body></html>"


def make_fake_safe_get(site):
    def fake(url, timeout=8, **kwargs):
        params = kwargs.get("params") or {}

        if url in site.get("pages", {}):
            return FakeResp(text=site["pages"][url], url=url)

        if "archive.org/wayback" in url:
            snap = site.get("wayback", {}).get(params.get("url"))
            data = {"archived_snapshots": {"closest": {"timestamp": snap}}} if snap else {"archived_snapshots": {}}
            return FakeResp(json_data=data)

        if "rdap.org/domain/" in url:
            created = site.get("rdap", {}).get(url.rsplit("/", 1)[1])
            if created:
                return FakeResp(json_data={"events": [{"eventAction": "registration", "eventDate": created}]})
            return FakeResp(status=404)

        if url.startswith("https://api.crossref.org/works/"):
            doi = url.split("/works/", 1)[1]
            return FakeResp(json_data={"message": {}}) if doi in site.get("real_dois", set()) else FakeResp(status=404)

        if url.startswith("https://api.crossref.org/works"):
            if "query.title" in params:
                t = params["query.title"].lower()
                real = site.get("real_titles", set())
                best = params["query.title"] if t in real else "An unrelated paper about something else entirely"
                return FakeResp(json_data={"message": {"items": [{"title": [best]}]}})
            if "query.author" in params:
                year = params["filter"].split(",")[0].split(":")[1]
                if (params["query.author"].lower(), year) in site.get("real_authors", set()):
                    return FakeResp(json_data={"message": {"items": [{"author": [{"family": params["query.author"]}]}]}})
                return FakeResp(json_data={"message": {"items": []}})

        if "duckduckgo.com" in url:
            return FakeResp(text=ddg_html(site.get("search", lambda q: [])(params.get("q", ""))))

        if url in site.get("images", {}):
            return FakeResp(content=png_bytes())

        if url in site.get("dead", set()):
            return FakeResp(status=404)

        return FakeResp(text="<html><body>ok</body></html>", url=url)
    return fake


def run_site(site, url):
    fake = make_fake_safe_get(site)
    targets = ["app.utils.safe_get", "app.fetcher.safe_get", "app.detectives.identity.safe_get",
               "app.detectives.source.safe_get", "app.detectives.network.safe_get",
               "app.detectives.mindgames.safe_get", "app.detectives.image.safe_get"]
    patches = [patch(t, fake) for t in targets]
    for p in patches:
        p.start()
    try:
        page = fetch_page(url)
        return analyze_page(page)
    finally:
        for p in patches:
            p.stop()


def reasons(result):
    return " | ".join(p["reason"] for p in result["penalties"])


def rules(result):
    return {p["rule_id"] for p in result["penalties"]}


FILLER = ("The randomized trial enrolled 4,200 adults across 14 sites between 2018 and 2020. "
          "Median follow-up was 24 months and 12.5% of patients had a primary event. "
          "The hazard ratio was 0.74 (95% CI 0.61 to 0.89, p=0.002). ") * 3

PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/12345678/"
PUBMED_HTML = """<html><head>
<meta name="citation_title" content="Efficacy of a new therapy in adults: a randomized trial">
<meta name="citation_author" content="Smith J"><meta name="citation_author" content="Lee S">
<meta name="citation_publication_date" content="2021/03/04">
<meta name="citation_doi" content="10.1056/NEJMoa2034577">
<meta property="og:site_name" content="PubMed">
<title>Efficacy of a new therapy in adults - PubMed</title></head><body>
<h1>Efficacy of a new therapy in adults: a randomized trial</h1>
<a href="/about/">About</a> <a href="/contact/">Contact</a>
<p>""" + FILLER + """ See the full text at
<a href="https://doi.org/10.1056/NEJMoa2034577">doi.org</a> and
<a href="https://www.nejm.org/doi/full/10.1056/NEJMoa2034577">NEJM</a> and
<a href="https://europepmc.org/article/MED/12345678">Europe PMC</a>.
Reference: 10.1056/NEJMoa2034577. </p></body></html>"""

SITE_PUBMED = {
    "pages": {PUBMED_URL: PUBMED_HTML},
    "wayback": {PUBMED_URL: "20210310120000"},
    "rdap": {"nih.gov": "1990-01-01T00:00:00Z"},
    "real_dois": {"10.1056/NEJMoa2034577"},
    "search": lambda q: [("Efficacy of a new therapy", "https://europepmc.org/a"),
                         ("Trial results", "https://www.nejm.org/b")],
}

REUTERS_URL = "https://www.reuters.com/world/europe/central-bank-raises-rates-2026-10-20/"
REUTERS_HTML = """<html><head>
<meta name="author" content="Alex Morgan">
<meta property="article:published_time" content="2026-10-20T09:30:00Z">
<meta property="og:site_name" content="Reuters">
<script type="application/ld+json">{"@type":"NewsArticle","author":{"name":"Alex Morgan"},"datePublished":"2026-10-20"}</script>
<title>Central bank raises rates by 25 basis points</title></head><body>
<h1>Central bank raises rates by 25 basis points</h1>
<a href="/about/">About Reuters</a> <a href="/world/">World</a> <a href="/business/">Business</a>
<p>FRANKFURT, Oct 20 - The central bank raised its key interest rate by 25 basis points to 3.75% on Tuesday,
the third increase this year, as inflation stayed at 4.1% in September. Policymakers said they expect
growth of 0.8% in 2027. Contact: newsroom@example.com. """ + FILLER + """</p>
<figure><img src="https://www.reuters.com/resizer/rates.jpg"><figcaption>The bank headquarters. REUTERS/Staff</figcaption></figure>
</body></html>"""

SITE_REUTERS = {
    "pages": {REUTERS_URL: REUTERS_HTML},
    "rdap": {"reuters.com": "1996-05-01T00:00:00Z"},
    "images": {"https://www.reuters.com/resizer/rates.jpg"},
    "search": lambda q: [("Central bank raises rates", "https://apnews.com/x"),
                         ("Rates rise again", "https://www.bbc.com/y")],
}

CLICK_URL = "https://real-truth-daily.xyz/shocking-cure"
CLICK_HTML = """<html><head><title>SHOCKING cure doctors don't want you to know</title></head><body>
<h1>SHOCKING cure doctors don't want you to know!!!</h1>
<img src="https://real-truth-daily.xyz/cure.jpg">
<p>SHARE THIS before it's deleted!! The shocker they hid from you for years. They don't want you to know
what they are hiding. Everyone knows the system is lying to you. Wake up people. Act now before midnight
because this is your last chance. """ + ("They lie to us every single day and nobody cares about the truth anymore. " * 12) + """</p>
</body></html>"""

SITE_CLICK = {
    "pages": {CLICK_URL: CLICK_HTML},
    "rdap": {"real-truth-daily.xyz": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%dT00:00:00Z")},
    "images": {"https://real-truth-daily.xyz/cure.jpg"},
    "wayback": {"https://real-truth-daily.xyz/cure.jpg": "20150702000000"},
    "search": lambda q: [("something", "https://real-truth-daily.xyz/other")],
}

AI_URL = "https://insights-journal-online.com/ai-nutrition-breakthrough"
AI_SENTENCE = "The findings highlight the importance of a balanced approach to nutrition and long-term health outcomes. "
AI_HTML = """<html><head><meta name="author" content="Michael Harrison">
<meta property="article:published_time" content="2026-10-01T08:00:00Z">
<title>Breakthrough in nutrition science</title></head><body>
<h1>Breakthrough in nutrition science</h1>
<p>""" + (AI_SENTENCE * 14) + """
According to the study \u201cNeural Pathways of Dietary Adaptation in Mammalian Cohorts\u201d researchers found a lasting effect.
A second paper titled \u201cQuantum Metabolic Signatures in Human Longevity Trials\u201d confirmed it
(Johnson, 2023) and (Whitfield et al., 2022). See doi 10.9999/fake.2023.0042 and 10.8888/invented.77.</p>
</body></html>"""

SITE_AI = {
    "pages": {AI_URL: AI_HTML},
    "rdap": {"insights-journal-online.com": (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%dT00:00:00Z")},
    "real_dois": set(), "real_titles": set(), "real_authors": set(),
    "search": lambda q: [("Breakthrough in nutrition science", "https://insights-journal-online.com/x")],
}


def test_1_pubmed_paper_scores_high_green():
    r = run_site(SITE_PUBMED, PUBMED_URL)
    print("pubmed", r["score"], [(p["points"], p["reason"]) for p in r["penalties"]])
    assert r["color"] == "green" and r["score"] >= 85
    assert r["author"] == "Smith J"
    assert r["source_label"] == "Primary Source"
    assert r["metadata"]["doi"] == "10.1056/NEJMoa2034577"
    assert "anonymous_author" not in {p["rule_id"] for p in r["penalties"] if p["points"] >= 15}


def test_2_reuters_article_is_green_or_high_yellow():
    r = run_site(SITE_REUTERS, REUTERS_URL)
    print("reuters", r["score"], [(p["points"], p["reason"]) for p in r["penalties"]])
    assert r["score"] >= 80
    assert "established outlet" in reasons(r)


def test_3_clickbait_blog_is_red():
    r = run_site(SITE_CLICK, CLICK_URL)
    print("clickbait", r["score"], [(p["points"], p["reason"]) for p in r["penalties"]])
    assert r["color"] == "red" and r["score"] <= 40
    assert {"anonymous_author", "suspicious_domain", "no_outbound_evidence", "emotional_urgency"} <= rules(r)


def test_4_ai_page_with_fake_citations_is_deep_red():
    r = run_site(SITE_AI, AI_URL)
    print("ai page", r["score"], [(p["points"], p["reason"]) for p in r["penalties"]])
    assert r["color"] == "red" and r["score"] < 40
    assert "fake_citations" in rules(r)
    fake = [p for p in r["penalties"] if p["rule_id"] == "fake_citations"]
    assert sum(p["points"] for p in fake) == 30
    assert r["ai_style_score"] is not None and r["ai_style_score"] > 0.8


def test_scores_are_ordered_like_the_plan_says():
    scores = [run_site(SITE_PUBMED, PUBMED_URL)["score"], run_site(SITE_REUTERS, REUTERS_URL)["score"],
              run_site(SITE_CLICK, CLICK_URL)["score"], run_site(SITE_AI, AI_URL)["score"]]
    assert scores[0] >= scores[1] > scores[2]
    assert scores[1] > scores[3]


def test_the_math_balances_for_all_four():
    for site, url in [(SITE_PUBMED, PUBMED_URL), (SITE_REUTERS, REUTERS_URL), (SITE_CLICK, CLICK_URL), (SITE_AI, AI_URL)]:
        r = run_site(site, url)
        assert r["score"] == max(0, 100 - r["total_penalties"])
        assert sum(p["points"] for p in r["penalties"]) == r["total_penalties"]
        assert sum(r["rule_totals"].values()) == r["total_penalties"]
        assert 0 <= r["score"] <= 100


def test_response_has_everything_the_frontend_reads():
    r = run_site(SITE_CLICK, CLICK_URL)
    for key in ["url", "score", "tier", "color", "total_penalties", "penalties", "author", "published_date",
                "source_label", "corroboration", "opposing_articles", "ai_style_score", "citations_found",
                "images", "graph", "metadata", "detective_errors"]:
        assert key in r, key
    for p in r["penalties"]:
        for key in ["rule_id", "rule", "category", "points", "reason"]:
            assert key in p, key
    assert r["penalties"][0]["category"][:1] in "ABCD"
    assert r["detective_errors"] == []