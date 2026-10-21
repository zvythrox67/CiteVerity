
RULES = {
    "anonymous_author":     {"category": "A: Identity", "max": 15},
    "suspicious_domain":    {"category": "A: Identity", "max": 20},
    "old_story":            {"category": "A: Identity", "max": 15},
    "no_outbound_evidence": {"category": "B: Evidence", "max": 30},
    "dead_end_trail":       {"category": "B: Evidence", "max": 15},
    "non_falsifiable":      {"category": "B: Evidence", "max": 10},
    "circular_loop":        {"category": "C: Network",  "max": 25},
    "fake_citations":       {"category": "C: Network",  "max": 30},
    "emotional_urgency":    {"category": "D: Emotional", "max": 15},
    "bad_image":            {"category": "D: Emotional", "max": 20},
}


def make_penalty(rule, points, reason):
    if rule not in RULES:
        raise ValueError("unknown rule: " + rule)
    return {"rule": rule, "points": points, "reason": reason}


def get_tier(score):
    if score >= 85:
        return "High Trust", "green"
    elif score >= 50:
        return "Caution / Sketchy", "yellow"
    else:
        return "Untrustworthy", "red"


def calculate_score(penalties):
    used = {}
    details = []

    for p in penalties:
        rule = p["rule"]
        already = used.get(rule, 0)
        room_left = RULES[rule]["max"] - already
        taken = min(p["points"], room_left)
        if taken <= 0:
            continue
        used[rule] = already + taken
        details.append({
            "rule": rule,
            "category": RULES[rule]["category"],
            "points": taken,
            "reason": p["reason"],
        })

    total = sum(used.values())
    score = max(0, 100 - total)
    tier, color = get_tier(score)

    return {
        "score": score,
        "tier": tier,
        "color": color,
        "total_penalties": total,
        "details": details,
    }