from app.chatbot import (tokenize, split_into_chunks, pick_chunks, build_messages,
                         report_to_text, MAX_HISTORY)
from app.fetcher import find_doi, find_publisher
from app.utils import get_soup


def test_tokenize_drops_stopwords():
    assert tokenize("What is the capital of France?") == ["capital", "france"]


def test_chunks_cover_text_and_overlap():
    text = " ".join("w" + str(i) for i in range(400))
    chunks = split_into_chunks(text, size=150, overlap=30)
    assert len(chunks) >= 3
    assert chunks[0].split()[0] == "w0"
    assert "w399" in chunks[-1]
    assert chunks[0].split()[-1] in chunks[1].split()


def test_pick_chunks_finds_the_right_part():
    filler = " ".join(["filler"] * 200)
    text = filler + " The study enrolled 4200 patients in Norway and found a 12 percent drop. " + filler
    best = pick_chunks(text, "How many patients were in the study?", k=1)
    assert "4200" in best[0]


def test_pick_chunks_falls_back_to_start():
    text = " ".join("word" + str(i) for i in range(500))
    best = pick_chunks(text, "summarize please", k=2)
    assert best[0].startswith("word0")


def test_pick_chunks_empty_page():
    assert pick_chunks("", "anything") == []


def test_prompt_is_grounded_and_has_report():
    report = {"score": 62, "tier": "Caution", "penalties": [{"points": 15, "reason": "No author"}]}
    msgs = build_messages(["some excerpt"], "why this score?", [], report_to_text(report))
    assert msgs[0]["role"] == "system"
    assert "ONLY" in msgs[0]["content"]
    assert "some excerpt" in msgs[0]["content"]
    assert "No author" in msgs[0]["content"]
    assert msgs[-1] == {"role": "user", "content": "why this score?"}


def test_history_is_trimmed_and_cleaned():
    history = [{"role": "user", "content": "q" + str(i)} for i in range(20)]
    history.append({"role": "system", "content": "hack"})
    msgs = build_messages(["x"], "now", history)
    assert len(msgs) == 2 + MAX_HISTORY
    assert all(m["content"] != "hack" for m in msgs)
    assert msgs[-1]["content"] == "now"


def test_history_short_is_kept():
    history = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    msgs = build_messages(["x"], "now", history)
    assert len(msgs) == 1 + 2 + 1


def test_find_doi_from_meta():
    soup = get_soup('<meta name="citation_doi" content="doi:10.1038/s41586-020-2649-2">')
    assert find_doi(soup, "") == "10.1038/s41586-020-2649-2"


def test_find_doi_from_text():
    assert find_doi(get_soup("<p></p>"), "see https://doi.org/10.1000/xyz123.") == "10.1000/xyz123"


def test_publisher_prefers_site_name():
    soup = get_soup('<meta property="og:site_name" content="Reuters">')
    assert find_publisher(soup, "https://www.reuters.com/a") == "Reuters"


def test_publisher_falls_back_to_domain():
    assert find_publisher(get_soup("<p></p>"), "https://www.example.com/a") == "example.com"