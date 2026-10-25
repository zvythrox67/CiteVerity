
var WHEEL_COLORS = { green: "#4a8a4a", yellow: "#8a7a3a", red: "#8a3a3a" };

function scoreColor(score) {
  if (score >= 85) {
    return "green";
  }
  if (score >= 50) {
    return "yellow";
  }
  return "red";
}

function scoreTier(score) {
  if (score >= 85) {
    return "HIGH TRUST";
  }
  if (score >= 50) {
    return "CAUTION";
  }
  return "UNTRUSTWORTHY";
}

function renderWheel(containerId, score) {
  var box = document.getElementById(containerId);
  var R = 80;
  var C = 2 * Math.PI * R;
  var color = WHEEL_COLORS[scoreColor(score)];

  box.innerHTML =
    '<svg class="wheel-svg" viewBox="0 0 200 200" role="img" aria-label="Trust score ' + score + ' percent">' +
      '<circle class="wheel-track" cx="100" cy="100" r="' + R + '"></circle>' +
      '<circle class="wheel-progress" cx="100" cy="100" r="' + R + '" ' +
        'stroke-dasharray="' + C + '" stroke-dashoffset="' + C + '" stroke="#555"></circle>' +
      '<text class="wheel-number" x="100" y="108">0%</text>' +
      '<text class="wheel-tier" x="100" y="132" fill="' + color + '">' + scoreTier(score) + '</text>' +
    '</svg>';

  var progress = box.querySelector(".wheel-progress");
  var number = box.querySelector(".wheel-number");

  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      progress.style.strokeDashoffset = C * (1 - score / 100);
      progress.style.stroke = color;
    });
  });

  var start = performance.now();
  var duration = 1100;

  function tick(now) {
    var t = Math.min(1, (now - start) / duration);
    var eased = 1 - Math.pow(1 - t, 3);
    number.textContent = Math.round(score * eased) + "%";
    if (t < 1) {
      requestAnimationFrame(tick);
    }
  }
  requestAnimationFrame(tick);
}

if (typeof module !== "undefined") {
  module.exports = { scoreColor: scoreColor, scoreTier: scoreTier };
} else {
  window.renderWheel = renderWheel;
  window.scoreColor = scoreColor;
}