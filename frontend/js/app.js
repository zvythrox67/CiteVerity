// connects the input box, the backend, and the display pieces

const API = "http://127.0.0.1:8000";
let currentUrl = "";

const LOADING_MESSAGES = [
  "Reading the page...",
  "Checking the author and domain...",
  "Tracing the links...",
  "Looking for circular reporting...",
  "Verifying citations...",
  "Scanning the images...",
];

const form = document.getElementById("analyze-form");
const input = document.getElementById("url-input");
const button = document.getElementById("analyze-btn");
const label = button.querySelector(".btn-label");
const statusEl = document.getElementById("status");
const results = document.getElementById("results");

createChatWidget({ apiBase: API, getUrl: () => currentUrl });

document.getElementById("open-chat-btn").addEventListener("click", () => {
  const bubble = document.querySelector(".chat-bubble");
  const panel = document.querySelector(".chat-panel");
  if (panel.classList.contains("hidden")) bubble.click();
});


function showResults(data, urlForChat) {
  currentUrl = urlForChat;
  results.hidden = false;

  renderWheel("wheel", data.score);
  renderSummary("summary", data);
  renderBreakdown("breakdown", data.penalties);
  renderOpposing("opposing", data.opposing_articles);
  renderCitations("cite-box", data.metadata || {});

  if (typeof d3 !== "undefined") {
    renderGraph("graph-box", data.graph);
  } else {
    document.getElementById("graph-box").innerHTML =
      '<p class="graph-empty">Couldn\'t load the graph library (are you offline?).</p>';
  }

  results.scrollIntoView({ behavior: "smooth", block: "start" });
}


let loadingTimer = null;

function startLoading() {
  button.disabled = true;
  input.disabled = true;
  button.classList.add("loading");
  label.textContent = "Analyzing...";
  statusEl.className = "";

  let i = 0;
  statusEl.textContent = LOADING_MESSAGES[0];
  loadingTimer = setInterval(() => {
    i = (i + 1) % LOADING_MESSAGES.length;
    statusEl.textContent = LOADING_MESSAGES[i];
  }, 1600);
}

function stopLoading() {
  clearInterval(loadingTimer);
  button.disabled = false;
  input.disabled = false;
  button.classList.remove("loading");
  label.textContent = "Analyze Source";
}


async function analyze(url) {
  startLoading();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);

  try {
    const res = await fetch(API + "/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url }),
      signal: controller.signal,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "the server returned an error");

    statusEl.textContent = "Done.";
    showResults(data, data.url);
  } catch (err) {
    statusEl.className = "error";
    if (err.name === "AbortError") {
      statusEl.textContent = "That took too long. Try again or try a different link.";
    } else if (err instanceof TypeError) {
      statusEl.textContent = "Can't reach the backend. Is it running on " + API + "? (You can still try a sample.)";
    } else {
      statusEl.textContent = err.message;
    }
  } finally {
    clearTimeout(timeout);
    stopLoading();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const url = input.value.trim();
  if (!url) {
    statusEl.className = "error";
    statusEl.textContent = "Paste a link first.";
    return;
  }
  analyze(url);
});

document.querySelectorAll(".sample-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    statusEl.className = "";
    statusEl.textContent = "Showing a sample result (not a real analysis).";
    showResults(SAMPLES[btn.dataset.sample], "");
  });
});