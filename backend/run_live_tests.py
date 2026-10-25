import json
import sys
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000"

LIVE_TESTS = [
    {"name": "1. PubMed paper",            "url": "PASTE A PUBMED ARTICLE LINK HERE",  "min": 85, "max": 100},
    {"name": "2. Reuters news article",    "url": "PASTE A REUTERS ARTICLE LINK HERE", "min": 75, "max": 100},
    {"name": "3. Clickbait blog",          "url": "PASTE A CLICKBAIT BLOG LINK HERE",  "min": 0,  "max": 60},
    {"name": "4. AI page, fake citations", "url": "PASTE AN AI-GENERATED PAGE HERE",   "min": 0,  "max": 39},
]


def call_api(url):
    body = json.dumps({"url": url}).encode()
    req = urllib.request.Request(API + "/analyze", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read())


def run_one(test):
    print("=" * 70)
    print(test["name"])
    print(test["url"])

    try:
        data = call_api(test["url"])
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read() or b"{}").get("detail", e.reason)
        print("  ERROR from backend:", detail)
        return False
    except urllib.error.URLError:
        print("  ERROR: can't reach the backend at", API, "- is uvicorn running?")
        return False

    ok = test["min"] <= data["score"] <= test["max"]
    print("  score:", str(data["score"]) + "%", "(" + data["color"] + ")",
          "expected", str(test["min"]) + "-" + str(test["max"]),
          "->", "PASS" if ok else "FAIL")
    print("  author:", data.get("author"), "| published:", data.get("published_date"),
          "| source:", data.get("source_label"), "| also reported by:", data.get("corroboration"))

    print("  points taken off:")
    for p in sorted(data["penalties"], key=lambda p: -p["points"]):
        print("    -%-3d %s  (%s)" % (p["points"], p["reason"], p["rule"]))
    if not data["penalties"]:
        print("    (none)")

    for err in data.get("detective_errors", []):
        print("  !! detective crashed:", err["detective"], "-", err["error"])
    return ok


def main():
    tests = [t for t in LIVE_TESTS if not t["url"].startswith("PASTE")]
    skipped = len(LIVE_TESTS) - len(tests)
    if not tests:
        print("Paste real links into LIVE_TESTS at the top of this file first.")
        sys.exit(1)

    results = [run_one(t) for t in tests]

    print("=" * 70)
    print(sum(results), "of", len(tests), "passed" + (" (" + str(skipped) + " skipped, no link pasted)" if skipped else ""))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()