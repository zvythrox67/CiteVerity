const API = "http://127.0.0.1:8000";

document.getElementById("test-btn").addEventListener("click", async function () {
  const output = document.getElementById("output");
  try {
    const res = await fetch(API + "/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: "https://example.com" }),
    });
    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = "couldn't reach backend: " + err;
  }
});