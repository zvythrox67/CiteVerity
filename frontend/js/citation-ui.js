
function renderCitations(containerId, meta) {
  var box = document.getElementById(containerId);
  var all = window.Citations.makeAllCitations(meta);
  var styles = Object.keys(all);
  var current = styles[0];

  box.innerHTML =
    '<div class="cite-tabs">' +
      styles.map(function (s) {
        return '<button data-style="' + s + '">' + s + "</button>";
      }).join("") +
    '</div>' +
    '<div class="cite-text"></div>' +
    '<button class="cite-copy">Copy citation</button>';

  var textBox = box.querySelector(".cite-text");
  var copyBtn = box.querySelector(".cite-copy");

  function show(style) {
    current = style;
    textBox.innerHTML = all[style].html;
    var buttons = box.querySelectorAll(".cite-tabs button");
    for (var i = 0; i < buttons.length; i++) {
      var b = buttons[i];
      if (b.dataset.style === style) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    }
  }

  var tabButtons = box.querySelectorAll(".cite-tabs button");
  for (var i = 0; i < tabButtons.length; i++) {
    var btn = tabButtons[i];
    btn.addEventListener("click", function () {
      show(this.dataset.style);
    });
  }

  copyBtn.addEventListener("click", function () {
    navigator.clipboard.writeText(all[current].text).then(function () {
      copyBtn.textContent = "Copied!";
      setTimeout(function () {
        copyBtn.textContent = "Copy citation";
      }, 1500);
    }).catch(function () {
      copyBtn.textContent = "Couldn't copy";
      setTimeout(function () {
        copyBtn.textContent = "Copy citation";
      }, 1500);
    });
  });

  show(current);
}

if (typeof window !== "undefined") {
  window.renderCitations = renderCitations;
}