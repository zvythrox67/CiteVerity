import pytest

from app.scoring import PointEngine, Penalty, tier_for


def run(*penalties):
    engine = PointEngine()
    engine.extend(list(penalties))
    return engine.compute()


def test_clean_page_scores_100():
    report = PointEngine().compute()
    assert report.score == 100
    assert report.color == "green"


def test_simple_deduction():
    report = run(Penalty("anonymous_author", 15, "No byline"))
    assert report.score == 85
    assert report.tier == "High Trust"


def test_rule_cap_applies():
    report = run(*[Penalty("anonymous_author", 1, "check " + str(i)) for i in range(20)])
    assert report.total_penalties == 15
    assert report.score == 85


def test_score_never_negative():
    report = run(
        Penalty("no_outbound_evidence", 30, "x"), Penalty("fake_citations", 30, "x"),
        Penalty("circular_loop", 25, "x"), Penalty("suspicious_domain", 20, "x"),
        Penalty("decontext_image", 20, "x"), Penalty("anonymous_author", 15, "x"),
    )
    assert report.score == 0
    assert report.color == "red"


@pytest.mark.parametrize("score,color", [(100, "green"), (85, "green"), (84, "yellow"),
                                         (50, "yellow"), (49, "red"), (0, "red")])
def test_tier_boundaries(score, color):
    assert tier_for(score)[1] == color


def test_unknown_rule_is_rejected():
    with pytest.raises(ValueError):
        Penalty("made_up_rule", 5, "x")


def test_report_dict_has_what_the_frontend_needs():
    data = run(Penalty("suspicious_domain", 10, "bad ending")).to_dict()
    assert data["penalties"][0]["category"].startswith("A:")
    assert data["penalties"][0]["rule"] == "Suspicious domain"
    assert data["total_penalties"] == 10