
function createChatWidget(options) {
  var apiBase = options.apiBase;
  var getUrl = options.getUrl;
  var history = [];

  var bubble = document.createElement("button");
  bubble.className = "chat-bubble";
  bubble.textContent = "Ask about this page";

  var panel = document.createElement("div");
  panel.className = "chat-panel hidden";
  panel.innerHTML =
    '<div class="chat-header"><span>CiteVerity Assistant</span><button class="chat-close">x</button></div>' +
    '<div class="chat-messages"></div>' +
    '<div class="chat-input-row">' +
      '<input class="chat-input" type="text" placeholder="Why did it get this score?">' +
      '<button class="chat-send">Send</button>' +
    '</div>';

  document.body.appendChild(bubble);
  document.body.appendChild(panel);

  var messagesBox = panel.querySelector(".chat-messages");
  var input = panel.querySelector(".chat-input");
  var sendBtn = panel.querySelector(".chat-send");

  function addMessage(role, text) {
    var div = document.createElement("div");
    div.className = "chat-msg " + role;
    div.textContent = text;
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return div;
  }

  function send() {
    var question = input.value.trim();
    if (!question) {
      return;
    }

    var url = getUrl();
    if (!url) {
      addMessage("bot", "Analyze a page first, then ask me about it.");
      return;
    }

    input.value = "";
    addMessage("user", question);
    var thinking = addMessage("bot", "Thinking...");
    sendBtn.disabled = true;

    fetch(apiBase + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, question: question, history: history })
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          var detail = result.data.detail || "request failed";
          throw new Error(detail);
        }
        thinking.textContent = result.data.answer;
        history.push({ role: "user", content: question });
        history.push({ role: "assistant", content: result.data.answer });
        sendBtn.disabled = false;
      })
      .catch(function (err) {
        thinking.textContent = "Something went wrong: " + err.message;
        sendBtn.disabled = false;
      });
  }

  bubble.addEventListener("click", function () {
    panel.classList.toggle("hidden");
    if (messagesBox.children.length === 0) {
      addMessage("bot", "Hi! Ask me anything about the page you analyzed, like \"why did it lose points?\"");
    }
  });

  panel.querySelector(".chat-close").addEventListener("click", function () {
    panel.classList.add("hidden");
  });

  sendBtn.addEventListener("click", send);

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      send();
    }
  });
}

if (typeof window !== "undefined") {
  window.createChatWidget = createChatWidget;
}