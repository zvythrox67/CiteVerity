# detectives/network.py - Detective 3: Fact & Rumor Scanner
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

import networkx as nx

from .base import Detective
from .source import link_type
from ..scoring import Penalty
from ..utils import safe_get, get_soup, registered_domain, outbound_links

FACT_CHECKERS = {"snopes.com", "politifact.com", "factcheck.org", "fullfact.org", "leadstories.com"}


def web_search(query, max_results=8):
    r = safe_get("https://html.duckduckgo.com/html/", params={"q": query})
    if r is None or r.status_code != 200:
        return None

    soup = get_soup(r.text)
    results = []
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        if "uddg=" in href:
            href = parse_qs(urlparse(href).query).get("uddg", [""])[0]
        if href.startswith("http"):
            results.append({"title": a.get_text(" ", strip=True), "url": href})
        if len(results) >= max_results:
            break
    return results


def word_overlap(a, b):
    wa = set(re.findall(r"[a-z]{4,}", a.lower()))
    wb = set(re.findall(r"[a-z]{4,}", b.lower()))
    if not wa or not wb:
        return 0
    return len(wa & wb) / min(len(wa), len(wb))


def check_corroboration(page):
    penalties = []
    title = page.extra.get("title", "")
    if not title:
        return penalties
    my_domain = registered_domain(page.url)

    results = web_search('"' + title + '"')
    if results is None:
        page.extra["corroboration"] = "search unavailable"
    else:
        others = {registered_domain(r["url"]) for r in results} - {my_domain, ""}
        page.extra["corroboration"] = str(len(others)) + " other sites found"
        if len(others) == 0:
            penalties.append(Penalty("no_outbound_evidence", 4, "Headline appears nowhere else on the web"))

    opposing = web_search(title + " false OR debunked OR fact check", max_results=6)
    page.extra["opposing_articles"] = []
    if opposing:
        for r in opposing:
            d = registered_domain(r["url"])
            if d == my_domain:
                continue
            if word_overlap(title, r["title"]) < 0.4:
                continue
            page.extra["opposing_articles"].append(r)
            if d in FACT_CHECKERS:
                penalties.append(Penalty("no_outbound_evidence", 3, "A fact-checker (" + d + ") has an article about this claim"))
        page.extra["opposing_articles"] = page.extra["opposing_articles"][:2]
    return penalties


def build_graph(root_url, root_links, linked_pages):
    G = nx.DiGraph()
    root = registered_domain(root_url)
    G.add_node(root)

    for link in root_links:
        d = registered_domain(link)
        if d and d != root:
            G.add_edge(root, d)

    for url, links in linked_pages.items():
        src = registered_domain(url)
        for l in links:
            d = registered_domain(l)
            if d and d != src:
                G.add_edge(src, d)
    return G


def find_loops(G):
    return [c for c in nx.simple_cycles(G) if len(c) >= 2]


def graph_to_json(G, loops, root=None):
    in_loop = set()
    for c in loops:
        in_loop.update(c)
    nodes = []
    for n in G.nodes:
        nodes.append({"id": n, "primary": link_type("https://" + n) == "primary", "in_loop": n in in_loop})
    edges = []
    for a, b in G.edges:
        edges.append({"source": a, "target": b, "in_loop": a in in_loop and b in in_loop})
    return {"root": root, "nodes": nodes, "edges": edges}


def fetch_links_of(url):
    r = safe_get(url, timeout=6)
    if r is None or r.status_code != 200:
        return url, []
    return url, outbound_links(r.text, url)


def check_loops(page):
    penalties = []
    root_links = page.extra.get("links", [])

    to_follow = {}
    for l in root_links:
        d = registered_domain(l)
        if d not in to_follow and link_type(l) == "other":
            to_follow[d] = l
    to_follow = list(to_follow.values())[:5]

    linked_pages = {}
    if to_follow:
        with ThreadPoolExecutor(max_workers=5) as pool:
            for url, links in pool.map(fetch_links_of, to_follow):
                linked_pages[url] = links

    G = build_graph(page.url, root_links, linked_pages)
    loops = find_loops(G)
    page.extra["graph"] = graph_to_json(G, loops, registered_domain(page.url))

    if not loops:
        return penalties

    loop_sites = set()
    for c in loops:
        loop_sites.update(c)
    nice = ", ".join(sorted(loop_sites))
    penalties.append(Penalty("circular_loop", 10, "Sites link to each other in a circle: " + nice))

    has_primary = any(link_type("https://" + s) == "primary" for s in loop_sites)
    if not has_primary:
        penalties.append(Penalty("circular_loop", 6, "No primary/official source anywhere in the loop"))

    root = registered_domain(page.url)
    root_targets = {registered_domain(l) for l in root_links}
    if root_targets <= loop_sites:
        penalties.append(Penalty("circular_loop", 3, "Every source this page links to is inside the loop"))
    return penalties


class NetworkDetective(Detective):
    name = "Fact & Rumor Scanner"

    def investigate(self, page):
        penalties = check_corroboration(page)
        penalties += check_loops(page)
        return penalties