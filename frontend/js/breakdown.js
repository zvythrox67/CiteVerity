
var CATEGORIES = {
  A: { name: "Identity & Transparency", question: "Who made this, and is the site real?" },
  B: { name: "Evidence & Logic", question: "Does it back up its claims?" },
  C: { name: "Network Manipulation", question: "Are sources just quoting each other?" },
  D: { name: "Emotional & Visual Red Flags", question: "Is it trying to manipulate you?" }
};

function categoryKey(category) {
  var c = category || "?";
  return c.trim().charAt(0).toUpperCase();
}

function groupByCategory(penalties) {
  var groups = {};
  var keys = ["A", "B", "C", "D"];
  for (var i = 0; i < keys.length; i++) {
    var k = keys[i];
    groups[k] = {
      key: k,
      name: CATEGORIES[k].name,
      question: CATEGORIES[k].question,
      total: 0,
      items: []
    };
  }
  var list = penalties || [];
  for (var j = 0; j < list.length; j++) {
    var p = list[j];
    var key = categoryKey(p.category);
    if (!groups[key]) {
      continue;
    }
    groups[key].total = groups[key].total + p.points;
    groups[key].items.push(p);
  }
  return groups;
}

function severity(total) {
  if (total === 0) {
    return "clear";
  }
  if (total <= 10) {
    return "minor";
  }
  return "major";
}

function el(tag, className, text) {
  var n = document.createElement(tag);
  if (className) {
    n.className = className;
  }
  if (text !== undefined && text !== null) {
    n.textContent = text;
  }
  return n;
}

function renderBreakdown(containerId, penalties) {
  var box = document.getElementById(containerId);
  var groups = groupByCategory(penalties);
  var active = "ALL";
  var keys = ["A", "B", "C", "D"];

  function draw() {
    box.innerHTML = "";

    var tabs = el("div", "tabs");

    var allBtn = el("button", "tab", "All (" + (penalties || []).length + ")");
    allBtn.type = "button";
    if (active === "ALL") {
      allBtn.className = "tab active";
    }
    allBtn.addEventListener("click", function () {
      active = "ALL";
      draw();
    });
    tabs.appendChild(allBtn);

    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var btn = el("button", "tab", k + ": " + groups[k].name);
      btn.type = "button";
      if (active === k) {
        btn.className = "tab active";
      }
      makeTabButton(btn, k);
      tabs.appendChild(btn);
    }
    box.appendChild(tabs);

    for (var g = 0; g < keys.length; g++) {
      var kk = keys[g];
      if (active !== "ALL" && active !== kk) {
        continue;
      }
      box.appendChild(makeCard(kk, groups[kk]));
    }
  }

  function makeTabButton(btn, key) {
    btn.addEventListener("click", function () {
      active = key;
      draw();
    });
  }

  function makeCard(k, group) {
    var card = el("div", "cat-card " + severity(group.total));

    var head = el("div", "cat-head");
    var left = el("div");
    left.appendChild(el("div", "cat-title", k + ": " + group.name));
    left.appendChild(el("div", "cat-question", group.question));
    head.appendChild(left);

    var totalText = "Clear";
    if (group.total > 0) {
      totalText = "-" + group.total + " pts";
    }
    head.appendChild(el("div", "cat-total", totalText));
    card.appendChild(head);

    if (group.items.length === 0) {
      card.appendChild(el("p", "all-clear", "No problems found here."));
    } else {
      var ul = el("ul", "deductions");
      for (var n = 0; n < group.items.length; n++) {
        var p = group.items[n];
        var li = el("li");
        li.appendChild(el("span", "pts", "-" + p.points));
        var text = el("div");
        text.appendChild(el("span", "rule-name", p.rule || p.rule_id));
        text.appendChild(el("div", "reason", p.reason));
        li.appendChild(text);
        ul.appendChild(li);
      }
      card.appendChild(ul);
    }
    return card;
  }

  draw();
}

function aiStyleText(score) {
  if (score === null || score === undefined) {
    return "Not enough text to tell";
  }
  var pct = Math.round(score * 100);
  return pct + "% uniform (rough guess, not part of the score)";
}

function citationsText(found) {
  if (!found) {
    return "None checked";
  }
  var total = (found.author_year || 0) + (found.dois || 0) + (found.titles || 0);
  if (total === 0) {
    return "None found in the text";
  }
  return total + " found (DOIs: " + (found.dois || 0) +
    ", titles: " + (found.titles || 0) +
    ", author-year: " + (found.author_year || 0) + ")";
}

function linkBreakdownText(b) {
  if (!b) {
    return null;
  }
  var parts = [];
  for (var key in b) {
    if (b.hasOwnProperty(key)) {
      parts.push(b[key] + " " + key);
    }
  }
  return parts.join(", ");
}

function renderSummary(containerId, data) {
  var box = document.getElementById(containerId);
  box.innerHTML = "";

  var pill = el("span", "tier-pill " + data.color, data.tier);
  box.appendChild(pill);

  var subText = "";
  if (data.total_penalties === 0) {
    subText = "No points were taken off.";
  } else {
    subText = data.total_penalties + " points were taken off from 100.";
  }
  var sub = el("p", "muted", subText);
  sub.style.margin = "0 0 12px";
  box.appendChild(sub);

  var source = data.source_label || "Unknown";
  var lb = linkBreakdownText(data.link_breakdown);
  if (lb) {
    source = source + " (links: " + lb + ")";
  }

  var rows = [
    ["Author", data.author || "Not found"],
    ["Published", data.published_date || "Not found"],
    ["Source type", source],
    ["Also reported by", data.corroboration || "Not checked"],
    ["Citations", citationsText(data.citations_found)],
    ["AI-style writing", aiStyleText(data.ai_style_score)],
    ["Images checked", String((data.images || []).length)]
  ];

  var dl = el("dl", "facts");
  for (var i = 0; i < rows.length; i++) {
    dl.appendChild(el("dt", null, rows[i][0]));
    dl.appendChild(el("dd", null, rows[i][1]));
  }
  box.appendChild(dl);

  if (data.detective_errors && data.detective_errors.length > 0) {
    var names = [];
    for (var e = 0; e < data.detective_errors.length; e++) {
      names.push(data.detective_errors[e].detective);
    }
    var warning = el("div", "warn-box",
      "Heads up: " + names.join(", ") + " couldn't finish, so this score might be missing some checks.");
    box.appendChild(warning);
  }
}

function safeHref(url) {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  return null;
}

function renderOpposing(containerId, articles) {
  var box = document.getElementById(containerId);
  box.innerHTML = "";

  if (!articles || articles.length === 0) {
    box.appendChild(el("p", "muted", "No opposing or fact-check articles found."));
    return;
  }

  var ul = el("ul", "opp-list");
  for (var i = 0; i < articles.length; i++) {
    var a = articles[i];
    var li = el("li");
    var href = safeHref(a.url);
    if (href) {
      var link = el("a", null, a.title || a.url);
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      li.appendChild(link);
    } else {
      li.textContent = a.title || "(untitled)";
    }
    ul.appendChild(li);
  }
  box.appendChild(ul);
}

if (typeof module !== "undefined") {
  module.exports = {
    groupByCategory: groupByCategory,
    categoryKey: categoryKey,
    severity: severity,
    aiStyleText: aiStyleText,
    citationsText: citationsText,
    linkBreakdownText: linkBreakdownText,
    safeHref: safeHref
  };
} else {
  window.renderBreakdown = renderBreakdown;
  window.renderSummary = renderSummary;
  window.renderOpposing = renderOpposing;
}