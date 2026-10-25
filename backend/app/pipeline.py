from concurrent.futures import ThreadPoolExecutor

from .scoring import PointEngine
from .detectives.base import PageData
from .detectives.identity import IdentityDetective
from .detectives.source import SourceDetective
from .detectives.network import NetworkDetective
from .detectives.mindgames import MindGamesDetective
from .detectives.image import ImageDetective

DETECTIVES = [
    IdentityDetective(),
    SourceDetective(),
    NetworkDetective(),
    MindGamesDetective(),
    ImageDetective(),
]


def run_detective(args):
    d, page = args
    local = PageData(url=page.url, html=page.html, text=page.text, extra=dict(page.extra))
    try:
        penalties = d.investigate(local)
        delta = {k: v for k, v in local.extra.items() if page.extra.get(k) != v}
        return d.name, penalties, delta, None
    except Exception as e:
        return d.name, [], {}, str(e)


def merge_extra(target, deltas):
    for d in deltas:
        for k, v in d.items():
            if v is None and k in target:
                continue
            target[k] = v


def analyze_page(page):
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(run_detective, [(d, page) for d in DETECTIVES]))

    engine = PointEngine()
    errors = []
    deltas = []
    for name, penalties, delta, error in results:
        engine.extend(penalties)
        deltas.append(delta)
        if error:
            errors.append({"detective": name, "error": error})

    merge_extra(page.extra, deltas)
    report = engine.compute().to_dict()
    extra = page.extra
    return {
        "url": page.url,
        **report,
        "metadata": {
            "author": extra.get("author"),
            "title": extra.get("title"),
            "publisher": extra.get("publisher"),
            "date": extra.get("published_date"),
            "doi": extra.get("doi"),
            "url": page.url,
        },
        "author": extra.get("author"),
        "published_date": extra.get("published_date"),
        "source_label": extra.get("source_label"),
        "link_breakdown": extra.get("link_breakdown"),
        "corroboration": extra.get("corroboration"),
        "opposing_articles": extra.get("opposing_articles", []),
        "ai_style_score": extra.get("ai_style_score"),
        "citations_found": extra.get("citations_found"),
        "images": extra.get("images", []),
        "graph": extra.get("graph"),
        "detective_errors": errors,
    }