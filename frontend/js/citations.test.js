var assert = require("assert");
var cit = require("./citations.js");
var apa = cit.apa;
var mla = cit.mla;
var chicago = cit.chicago;
var parseName = cit.parseName;
var initials = cit.initials;

var meta = {
  author: "Jane Doe",
  title: "Climate report finds record heat",
  publisher: "Reuters",
  date: "2024-03-05",
  url: "https://www.reuters.com/world/climate-report"
};

var passed = 0;

function test(name, fn) {
  fn();
  passed = passed + 1;
  console.log("PASS", name);
}

test("names", function () {
  assert.deepStrictEqual(parseName("Jane Doe"), { first: "Jane", last: "Doe", org: false });
  assert.deepStrictEqual(parseName("Doe, Jane"), { first: "Jane", last: "Doe", org: false });
  assert.strictEqual(parseName("Dr. Mary Jane Smith").last, "Smith");
  assert.strictEqual(parseName("Reuters").org, true);
  assert.strictEqual(initials("Mary Jane"), "M. J.");
  assert.strictEqual(initials("Jean-Paul"), "J.-P.");
});

test("APA one author", function () {
  assert.strictEqual(apa(meta).text,
    "Doe, J. (2024, March 5). Climate report finds record heat. Reuters. https://www.reuters.com/world/climate-report");
});

test("APA html has italics on title", function () {
  assert.ok(apa(meta).html.indexOf("<i>Climate report finds record heat</i>.") !== -1);
});

test("APA two authors uses ampersand", function () {
  var m = Object.assign({}, meta, { author: "Jane Doe and Sam Lee" });
  assert.ok(apa(m).text.indexOf("Doe, J., & Lee, S. (2024") === 0);
});

test("APA no author puts title first", function () {
  var m = Object.assign({}, meta, { author: null });
  assert.ok(apa(m).text.indexOf("Climate report finds record heat. (2024, March 5).") === 0);
});

test("APA no date -> n.d.", function () {
  assert.ok(apa(Object.assign({}, meta, { date: null })).text.indexOf("(n.d.)") !== -1);
});

test("APA doi becomes link", function () {
  var m = Object.assign({}, meta, { doi: "10.1038/abc123" });
  assert.ok(apa(m).text.indexOf("https://doi.org/10.1038/abc123") !== -1);
});

test("MLA one author", function () {
  assert.strictEqual(mla(meta).text,
    "Doe, Jane. \u201CClimate report finds record heat.\u201D Reuters, 5 Mar. 2024, www.reuters.com/world/climate-report.");
});

test("MLA three authors -> et al", function () {
  var m = Object.assign({}, meta, { author: "Jane Doe; Sam Lee; Al Kim" });
  assert.ok(mla(m).text.indexOf("Doe, Jane, et al.") === 0);
});

test("MLA no date adds accessed", function () {
  assert.ok(mla(Object.assign({}, meta, { date: null })).text.indexOf("Accessed") !== -1);
});

test("Chicago one author", function () {
  assert.strictEqual(chicago(meta).text,
    "Doe, Jane. \u201CClimate report finds record heat.\u201D Reuters. March 5, 2024. https://www.reuters.com/world/climate-report.");
});

test("Chicago three authors", function () {
  var m = Object.assign({}, meta, { author: "Jane Doe, Sam Lee" });
  assert.ok(chicago(m).text.length > 0);
  var m2 = Object.assign({}, meta, { author: "Jane Doe; Sam Lee; Al Kim" });
  assert.ok(chicago(m2).text.indexOf("Doe, Jane, Sam Lee, and Al Kim.") === 0);
});

test("year-only date and missing everything doesn't crash", function () {
  assert.ok(apa({ date: "2019", title: "T", url: "https://x.com" }).text.indexOf("(2019)") !== -1);
  assert.ok(apa({}).text.length >= 0);
  assert.ok(mla({}).text.length >= 0);
  assert.ok(chicago({}).text.length >= 0);
});

test("html escapes angle brackets in titles", function () {
  var m = Object.assign({}, meta, { title: "5 > 3 <script>" });
  assert.ok(apa(m).html.indexOf("<script>") === -1);
});

console.log(passed + " passed");