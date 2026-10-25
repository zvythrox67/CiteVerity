
var MONTHS = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"];
var MLA_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July",
                  "Aug.", "Sept.", "Oct.", "Nov.", "Dec."];

// ---------- names ----------

function splitAuthors(raw) {
  if (!raw) {
    return [];
  }
  var parts = raw.split(/\s*(?:;|&|\band\b)\s*/i);
  var out = [];
  for (var i = 0; i < parts.length; i++) {
    var p = parts[i].trim();
    if (p) {
      out.push(p);
    }
  }
  return out;
}

function parseName(full) {
  var name = full.replace(/^(dr|prof|mr|mrs|ms)\.?\s+/i, "").trim();

  if (name.indexOf(",") !== -1) {
    var pieces = name.split(",");
    var last = pieces[0].trim();
    var first = "";
    if (pieces.length > 1) {
      first = pieces[1].trim();
    }
    return { first: first, last: last, org: false };
  }

  var words = name.split(/\s+/);
  if (words.length === 1) {
    return { first: "", last: name, org: true };
  }
  var firstName = words.slice(0, words.length - 1).join(" ");
  var lastName = words[words.length - 1];
  return { first: firstName, last: lastName, org: false };
}

function initials(first) {
  var parts = first.split(/\s+/);
  var out = [];
  for (var i = 0; i < parts.length; i++) {
    var p = parts[i];
    if (!p) {
      continue;
    }
    var sub = p.split("-");
    var subOut = [];
    for (var j = 0; j < sub.length; j++) {
      if (sub[j]) {
        subOut.push(sub[j][0].toUpperCase() + ".");
      }
    }
    out.push(subOut.join("-"));
  }
  return out.join(" ");
}

// ---------- dates ----------

function parseDate(d) {
  if (!d) {
    return null;
  }
  var m = String(d).match(/^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?/);
  if (!m) {
    return null;
  }
  var month = null;
  if (m[2]) {
    month = parseInt(m[2], 10);
  }
  var day = null;
  if (m[3]) {
    day = parseInt(m[3], 10);
  }
  return { y: m[1], m: month, d: day };
}

function todayParts() {
  var t = new Date();
  return { y: String(t.getFullYear()), m: t.getMonth() + 1, d: t.getDate() };
}

// ---------- helpers ----------

function endWithPeriod(s) {
  if (/[.?!]$/.test(s)) {
    return s;
  }
  return s + ".";
}

function link(meta) {
  if (meta.doi) {
    return "https://doi.org/" + meta.doi.replace(/^https?:\/\/(dx\.)?doi\.org\//, "");
  }
  return meta.url || "";
}

function toText(s) {
  return s.replace(/\*/g, "");
}

function toHtml(s) {
  var safe = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return safe.replace(/\*(.+?)\*/g, "<i>$1</i>");
}

function pack(s) {
  var clean = s.replace(/\s+/g, " ").trim();
  return { text: toText(clean), html: toHtml(clean) };
}

// ---------- APA 7 ----------

function apa(meta) {
  var authors = [];
  var rawAuthors = splitAuthors(meta.author);
  for (var i = 0; i < rawAuthors.length; i++) {
    authors.push(parseName(rawAuthors[i]));
  }

  var who = "";
  if (authors.length === 1) {
    var a = authors[0];
    if (a.org) {
      who = a.last;
    } else {
      who = a.last + ", " + initials(a.first);
    }
  } else if (authors.length > 1 && authors.length <= 20) {
    var names = [];
    for (var j = 0; j < authors.length; j++) {
      var au = authors[j];
      if (au.org) {
        names.push(au.last);
      } else {
        names.push(au.last + ", " + initials(au.first));
      }
    }
    var before = names.slice(0, names.length - 1).join(", ");
    who = before + ", & " + names[names.length - 1];
  } else if (authors.length > 20) {
    var first19 = [];
    for (var k = 0; k < 19; k++) {
      var au2 = authors[k];
      if (au2.org) {
        first19.push(au2.last);
      } else {
        first19.push(au2.last + ", " + initials(au2.first));
      }
    }
    var lastAu = authors[authors.length - 1];
    var lastStr = lastAu.org ? lastAu.last : lastAu.last + ", " + initials(lastAu.first);
    who = first19.join(", ") + ", ... " + lastStr;
  }

  var dt = parseDate(meta.date);
  var when = "n.d.";
  if (dt) {
    when = dt.y;
    if (dt.m) {
      when += ", " + MONTHS[dt.m - 1];
      if (dt.d) {
        when += " " + dt.d;
      }
    }
  }

  var title = "";
  if (meta.title) {
    title = "*" + meta.title + "*";
    if (!/[.?!]$/.test(meta.title)) {
      title += ".";
    }
  }

  var publisher = "";
  if (meta.publisher) {
    var sameAsAuthor = authors.length > 0 && authors[0].last === meta.publisher;
    if (!sameAsAuthor) {
      publisher = endWithPeriod(meta.publisher);
    }
  }

  var out;
  if (who) {
    out = endWithPeriod(who) + " (" + when + "). " + title;
  } else {
    out = title + " (" + when + ").";
  }
  out += " " + publisher + " " + link(meta);
  return pack(out);
}

// ---------- MLA 9 ----------

function mla(meta) {
  var authors = [];
  var rawAuthors = splitAuthors(meta.author);
  for (var i = 0; i < rawAuthors.length; i++) {
    authors.push(parseName(rawAuthors[i]));
  }

  var who = "";
  if (authors.length === 1) {
    var a = authors[0];
    if (a.org) {
      who = a.last;
    } else {
      who = a.last + ", " + a.first;
    }
  } else if (authors.length === 2) {
    var a1 = authors[0];
    var a2 = authors[1];
    who = a1.last + ", " + a1.first + ", and " + a2.first + " " + a2.last;
  } else if (authors.length >= 3) {
    who = authors[0].last + ", " + authors[0].first + ", et al";
  }

  var dt = parseDate(meta.date);
  var when = "";
  if (dt) {
    if (dt.d) {
      when += dt.d + " ";
    }
    if (dt.m) {
      when += MLA_MONTHS[dt.m - 1] + " ";
    }
    when += dt.y;
  }

  var parts = [];
  if (who) {
    parts.push(endWithPeriod(who));
  }
  if (meta.title) {
    parts.push("\u201C" + endWithPeriod(meta.title) + "\u201D");
  }

  var tail = [];
  if (meta.publisher) {
    tail.push("*" + meta.publisher + "*");
  }
  if (when) {
    tail.push(when);
  }
  var l = link(meta);
  if (l) {
    tail.push(l.replace(/^https?:\/\//, ""));
  }
  if (tail.length) {
    parts.push(endWithPeriod(tail.join(", ")));
  }

  if (!when) {
    var t = todayParts();
    parts.push("Accessed " + t.d + " " + MLA_MONTHS[t.m - 1] + " " + t.y + ".");
  }
  return pack(parts.join(" "));
}

// ---------- Chicago (bibliography style) ----------

function chicago(meta) {
  var authors = [];
  var rawAuthors = splitAuthors(meta.author);
  for (var i = 0; i < rawAuthors.length; i++) {
    authors.push(parseName(rawAuthors[i]));
  }

  var who = "";
  if (authors.length === 1) {
    var a = authors[0];
    if (a.org) {
      who = a.last;
    } else {
      who = a.last + ", " + a.first;
    }
  } else if (authors.length >= 2) {
    var shown = authors;
    if (authors.length > 10) {
      shown = authors.slice(0, 7);
    }
    var first = shown[0].last + ", " + shown[0].first;
    var rest = [];
    for (var j = 1; j < shown.length; j++) {
      var au = shown[j];
      if (au.org) {
        rest.push(au.last);
      } else {
        rest.push(au.first + " " + au.last);
      }
    }
    if (authors.length > 10) {
      who = first + ", " + rest.join(", ") + ", et al";
    } else if (rest.length === 1) {
      who = first + ", and " + rest[0];
    } else {
      var before = rest.slice(0, rest.length - 1).join(", ");
      who = first + ", " + before + ", and " + rest[rest.length - 1];
    }
  }

  var dt = parseDate(meta.date);
  var when = "n.d.";
  if (dt) {
    when = "";
    if (dt.m) {
      when += MONTHS[dt.m - 1] + " ";
    }
    if (dt.d) {
      when += dt.d + ", ";
    }
    when += dt.y;
  }

  var parts = [];
  if (who) {
    parts.push(endWithPeriod(who));
  }
  if (meta.title) {
    parts.push("\u201C" + endWithPeriod(meta.title) + "\u201D");
  }
  if (meta.publisher) {
    parts.push(endWithPeriod(meta.publisher));
  }
  parts.push(endWithPeriod(when));
  var l = link(meta);
  if (l) {
    parts.push(l + ".");
  }
  return pack(parts.join(" "));
}

function makeAllCitations(meta) {
  return { APA: apa(meta), MLA: mla(meta), Chicago: chicago(meta) };
}

if (typeof module !== "undefined") {
  module.exports = {
    apa: apa,
    mla: mla,
    chicago: chicago,
    makeAllCitations: makeAllCitations,
    parseName: parseName,
    initials: initials,
    parseDate: parseDate
  };
} else {
  window.Citations = {
    apa: apa,
    mla: mla,
    chicago: chicago,
    makeAllCitations: makeAllCitations
  };
}