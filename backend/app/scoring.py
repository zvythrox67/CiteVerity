# scoring.py - the point engine for CiteVerity
from dataclasses import dataclass

MAX_SCORE = 100

RULES = {
    "anonymous_author":     {"category": "A: Identity & Transparency",      "max": 25, "label": "Anonymous author"},
    "suspicious_domain":    {"category": "A: Identity & Transparency",      "max": 30, "label": "Suspicious domain"},
    "old_story_repackaged": {"category": "A: Identity & Transparency",      "max": 15, "label": "Old story re-packaging"},
    "no_outbound_evidence": {"category": "B: Evidence & Logic",             "max": 30, "label": "No outbound evidence"},
    "dead_end_trail":       {"category": "B: Evidence & Logic",             "max": 15, "label": "Dead-end evidence trail"},
    "non_falsifiable":      {"category": "B: Evidence & Logic",             "max": 10, "label": "Non-falsifiable rhetoric"},
    "circular_loop":        {"category": "C: Network Manipulation",         "max": 25, "label": "Circular reporting loop"},
    "fake_citations":       {"category": "C: Network Manipulation",         "max": 30, "label": "Unverifiable / fake citations"},
    "emotional_urgency":    {"category": "D: Emotional & Visual Red Flags", "max": 15, "label": "High emotional urgency"},
    "decontext_image":      {"category": "D: Emotional & Visual Red Flags", "max": 20, "label": "Decontextualized image"},
}

TIERS = [
    (85, "High Trust", "green"),
    (50, "Caution / Sketchy", "yellow"),
    (0, "Untrustworthy", "red"),
]


@dataclass
class Penalty:
    rule_id: str
    points: int
    reason: str

    def __post_init__(self):
        if self.rule_id not in RULES:
            raise ValueError("Unknown rule_id: " + self.rule_id)
        if self.points < 0:
            raise ValueError("Penalty points must be 0 or more")


class ScoreReport:
    def __init__(self, score, tier, color, total_penalties, penalties, rule_totals):
        self.score = score
        self.tier = tier
        self.color = color
        self.total_penalties = total_penalties
        self.penalties = penalties
        self.rule_totals = rule_totals

    def to_dict(self):
        return {
            "score": self.score,
            "tier": self.tier,
            "color": self.color,
            "total_penalties": self.total_penalties,
            "penalties": self.penalties,
            "rule_totals": self.rule_totals,
        }


def tier_for(score):
    for minimum, name, color in TIERS:
        if score >= minimum:
            return name, color
    return TIERS[-1][1], TIERS[-1][2]


class PointEngine:
    def __init__(self):
        self._penalties = []

    def add(self, penalty):
        self._penalties.append(penalty)

    def extend(self, penalties):
        for p in penalties:
            self.add(p)

    def compute(self):
        used = {}
        applied = []

        for p in self._penalties:
            rule = RULES[p.rule_id]
            room_left = rule["max"] - used.get(p.rule_id, 0)
            charged = min(p.points, max(0, room_left))
            if charged == 0:
                continue
            used[p.rule_id] = used.get(p.rule_id, 0) + charged
            applied.append({
                "rule_id": p.rule_id,
                "rule": rule["label"],
                "category": rule["category"],
                "points": charged,
                "reason": p.reason,
            })

        total = sum(used.values())
        score = max(0, MAX_SCORE - total)
        tier, color = tier_for(score)
        return ScoreReport(score, tier, color, total, applied, used)