import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scoring import calculate_score, make_penalty, get_tier


def test_clean_page():
    result = calculate_score([])
    assert result["score"] == 100
    assert result["color"] == "green"


def test_one_penalty():
    result = calculate_score([make_penalty("anonymous_author", 15, "no author")])
    assert result["score"] == 85


def test_rule_cap():
    penalties = [make_penalty("anonymous_author", 1, "check") for i in range(20)]
    assert calculate_score(penalties)["total_penalties"] == 15


def test_never_below_zero():
    penalties = [
        make_penalty("no_outbound_evidence", 30, "x"),
        make_penalty("fake_citations", 30, "x"),
        make_penalty("circular_loop", 25, "x"),
        make_penalty("suspicious_domain", 20, "x"),
        make_penalty("bad_image", 20, "x"),
        make_penalty("anonymous_author", 15, "x"),
    ]
    assert calculate_score(penalties)["score"] == 0


def test_tiers():
    assert get_tier(85)[1] == "green"
    assert get_tier(84)[1] == "yellow"
    assert get_tier(50)[1] == "yellow"
    assert get_tier(49)[1] == "red"