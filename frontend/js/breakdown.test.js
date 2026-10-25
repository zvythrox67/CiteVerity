var assert = require("assert");
var wheel = require("./wheel.js");
var scoreColor = wheel.scoreColor;
var scoreTier = wheel.scoreTier;
var bd = require("./breakdown.js");
var groupByCategory = bd.groupByCategory;
var categoryKey = bd.categoryKey;
var severity = bd.severity;
var citationsText = bd.citationsText;
var safeHref = bd.safeHref;
var aiStyleText = bd.aiStyleText;
var SAMPLES = require("./sample.js").SAMPLES;

var passed = 0;

function test(name, fn) {
  fn();
  passed = passed + 1;
  console.log("PASS", name);
}

test("wheel colors match backend tiers", function () {
  var cases = [[100, "green"], [85, "green"], [84, "yellow"], [50, "yellow"], [49, "red"], [0, "red"]];
  for (var i = 0; i < cases.length; i++) {
    var s = cases[i][0];
    var c = cases[i][1];
    assert.strictEqual(scoreColor(s), c, "score " + s);
  }
  assert.strictEqual(scoreTier(90), "HIGH TRUST");
  assert.strictEqual(scoreTier(10), "UNTRUSTWORTHY");
});

test("category key", function () {
  assert.strictEqual(categoryKey("B: Evidence & Logic"), "B");
  assert.strictEqual(categoryKey(undefined), "?");
});

test("grouping adds up points per category", function () {
  var g = groupByCategory([
    { category: "A: Identity & Transparency", points: 15 },
    { category: "A: Identity & Transparency", points: 2 },
    { category: "D: Emotional & Visual Red Flags", points: 4 }
  ]);
  assert.strictEqual(g.A.total, 17);
  assert.strictEqual(g.A.items.length, 2);
  assert.strictEqual(g.B.total, 0);
  assert.strictEqual(g.D.total, 4);
});

test("grouping handles empty / unknown", function () {
  assert.strictEqual(groupByCategory(null).A.total, 0);
  assert.strictEqual(groupByCategory([{ category: "Z: ???", points: 5 }]).A.total, 0);
});

test("severity", function () {
  assert.strictEqual(severity(0), "clear");
  assert.strictEqual(severity(10), "minor");
  assert.strictEqual(severity(11), "major");
});

test("sample data is consistent with the scoring formula", function () {
  var names = Object.keys(SAMPLES);
  for (var i = 0; i < names.length; i++) {
    var s = SAMPLES[names[i]];
    var sum = 0;
    for (var j = 0; j < s.penalties.length; j++) {
      sum = sum + s.penalties[j].points;
    }
    assert.strictEqual(sum, s.total_penalties, s.url + " penalties sum");
    assert.strictEqual(Math.max(0, 100 - sum), s.score, s.url + " score");
    assert.strictEqual(scoreColor(s.score), s.color, s.url + " color");
  }
});

test("sample rule caps respected", function () {
  var caps = {
    anonymous_author: 15,
    suspicious_domain: 20,
    old_story_repackaged: 15,
    no_outbound_evidence: 30,
    dead_end_trail: 15,
    non_falsifiable: 10,
    circular_loop: 25,
    fake_citations: 30,
    emotional_urgency: 15,
    decontext_image: 20
  };
  var names = Object.keys(SAMPLES);
  for (var i = 0; i < names.length; i++) {
    var s = SAMPLES[names[i]];
    var used = {};
    for (var j = 0; j < s.penalties.length; j++) {
      var p = s.penalties[j];
      if (!used[p.rule_id]) {
        used[p.rule_id] = 0;
      }
      used[p.rule_id] = used[p.rule_id] + p.points;
    }
    var ruleIds = Object.keys(used);
    for (var k = 0; k < ruleIds.length; k++) {
      var r = ruleIds[k];
      assert.ok(used[r] <= caps[r], r);
    }
  }
});

test("safeHref blocks javascript: links", function () {
  assert.strictEqual(safeHref("javascript:alert(1)"), null);
  assert.strictEqual(safeHref("https://example.org/a"), "https://example.org/a");
});

test("text helpers", function () {
  var c = citationsText({ author_year: 1, dois: 2, titles: 0 });
  assert.ok(c.indexOf("3 found") === 0);
  assert.strictEqual(citationsText({ author_year: 0, dois: 0, titles: 0 }), "None found in the text");
  assert.ok(aiStyleText(0.5).indexOf("50%") === 0);
  assert.ok(aiStyleText(null).indexOf("Not enough") !== -1);
});

console.log(passed + " passed");