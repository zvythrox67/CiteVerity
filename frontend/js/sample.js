
function P(rule_id, rule, category, points, reason) {
  return { rule_id: rule_id, rule: rule, category: category, points: points, reason: reason };
}

var A = "A: Identity & Transparency";
var B = "B: Evidence & Logic";
var C = "C: Network Manipulation";
var D = "D: Emotional & Visual Red Flags";

var SAMPLES = {
  green: {
    url: "https://journal.example.org/articles/2024/heat-study",
    score: 96,
    tier: "High Trust",
    color: "green",
    total_penalties: 4,
    penalties: [
      P("anonymous_author", "Anonymous author", A, 1, "No contact info found on the page"),
      P("old_story_repackaged", "Old story re-packaging", A, 2, "No publish date found in the page code"),
      P("decontext_image", "Decontextualized image", D, 1, "Images have no caption or credit")
    ],
    author: "Jane Doe",
    published_date: "2024-03-05",
    source_label: "Primary Source",
    link_breakdown: { primary: 7, other: 2 },
    corroboration: "6 other sites found",
    ai_style_score: 0.12,
    citations_found: { author_year: 9, dois: 6, titles: 1 },
    images: [{ url: "x", phash: "abc", first_seen: null }],
    opposing_articles: [],
    detective_errors: [],
    graph: {
      root: "journal.example.org",
      nodes: [
        { id: "journal.example.org", primary: false, in_loop: false },
        { id: "nih.gov", primary: true, in_loop: false },
        { id: "doi.org", primary: true, in_loop: false },
        { id: "nature.com", primary: true, in_loop: false }
      ],
      edges: [
        { source: "journal.example.org", target: "nih.gov", in_loop: false },
        { source: "journal.example.org", target: "doi.org", in_loop: false },
        { source: "journal.example.org", target: "nature.com", in_loop: false }
      ]
    },
    metadata: {
      author: "Jane Doe",
      title: "Record heat across three continents",
      publisher: "Journal of Climate Studies",
      date: "2024-03-05",
      doi: "10.1000/heat2024",
      url: "https://journal.example.org/articles/2024/heat-study"
    }
  },

  yellow: {
    url: "https://dailyscoop.example.com/news/tax-change",
    score: 72,
    tier: "Caution / Sketchy",
    color: "yellow",
    total_penalties: 28,
    penalties: [
      P("anonymous_author", "Anonymous author", A, 15, "No author name found in meta tags, JSON-LD or byline"),
      P("dead_end_trail", "Dead-end evidence trail", B, 4, "No link to any official or primary source anywhere"),
      P("non_falsifiable", "Non-falsifiable rhetoric", B, 3, "Almost no numbers or dates (2 found)"),
      P("old_story_repackaged", "Old story re-packaging", A, 2, "No publish date found in the page code"),
      P("emotional_urgency", "High emotional urgency", D, 4, "Manipulative wording (hidden truth): 'what they won't tell you'")
    ],
    author: null,
    published_date: null,
    source_label: "Secondary Source",
    link_breakdown: { other: 4, social: 2 },
    corroboration: "2 other sites found",
    ai_style_score: 0.41,
    citations_found: { author_year: 0, dois: 0, titles: 0 },
    images: [],
    detective_errors: [],
    opposing_articles: [
      { title: "Fact check: does the new tax rule really work like that?", url: "https://example.org/fact-check" }
    ],
    graph: {
      root: "dailyscoop.example.com",
      nodes: [
        { id: "dailyscoop.example.com", primary: false, in_loop: false },
        { id: "otherblog.net", primary: false, in_loop: false },
        { id: "twitter.com", primary: false, in_loop: false }
      ],
      edges: [
        { source: "dailyscoop.example.com", target: "otherblog.net", in_loop: false },
        { source: "dailyscoop.example.com", target: "twitter.com", in_loop: false }
      ]
    },
    metadata: {
      author: null,
      title: "The tax change they won't explain",
      publisher: "Daily Scoop",
      date: null,
      doi: null,
      url: "https://dailyscoop.example.com/news/tax-change"
    }
  },

  red: {
    url: "https://real-truth-news.xyz/shocking-cure",
    score: 11,
    tier: "Untrustworthy",
    color: "red",
    total_penalties: 89,
    penalties: [
      P("anonymous_author", "Anonymous author", A, 15, "No author name found in meta tags, JSON-LD or byline"),
      P("suspicious_domain", "Suspicious domain", A, 10, "Domain ending '.xyz' is heavily used by junk sites"),
      P("no_outbound_evidence", "No outbound evidence", B, 30, "Page has zero outbound links backing up its claims"),
      P("non_falsifiable", "Non-falsifiable rhetoric", B, 8, "Zero numbers, dates or statistics in the whole text"),
      P("circular_loop", "Circular reporting loop", C, 16, "Sites link to each other in a circle: miracle-health.net, real-truth-news.xyz, wakeup-daily.org"),
      P("emotional_urgency", "High emotional urgency", D, 10, "Manipulative wording (deletion panic): 'before it's deleted'")
    ],
    author: null,
    published_date: "2024-06-01",
    source_label: "Secondary Source",
    link_breakdown: null,
    corroboration: "0 other sites found",
    ai_style_score: 0.83,
    citations_found: { author_year: 2, dois: 1, titles: 1 },
    images: [{ url: "x", phash: "abc", first_seen: "2015-07-02" }],
    opposing_articles: [
      { title: "Debunked: the 'shocking cure' doctors supposedly hid", url: "https://example.org/debunk-1" },
      { title: "No evidence for miracle cure claims", url: "https://example.org/debunk-2" }
    ],
    detective_errors: [{ detective: "Image Matcher", error: "timeout" }],
    graph: {
      root: "real-truth-news.xyz",
      nodes: [
        { id: "real-truth-news.xyz", primary: false, in_loop: true },
        { id: "miracle-health.net", primary: false, in_loop: true },
        { id: "wakeup-daily.org", primary: false, in_loop: true }
      ],
      edges: [
        { source: "real-truth-news.xyz", target: "miracle-health.net", in_loop: true },
        { source: "miracle-health.net", target: "wakeup-daily.org", in_loop: true },
        { source: "wakeup-daily.org", target: "real-truth-news.xyz", in_loop: true }
      ]
    },
    metadata: {
      author: null,
      title: "SHOCKING cure doctors don't want you to know",
      publisher: "Real Truth News",
      date: "2024-06-01",
      doi: null,
      url: "https://real-truth-news.xyz/shocking-cure"
    }
  }
};

if (typeof module !== "undefined") {
  module.exports = { SAMPLES: SAMPLES };
}