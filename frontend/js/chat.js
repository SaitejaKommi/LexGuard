/**
 * chat.js — AI chat assistant module for LexGuard.
 * @module chat
 */

let chatDebounceTimer = null;

function appendChatMessage(role, text) {
  const messages = document.getElementById("chat-messages");
  const wrap = document.createElement("div");
  wrap.className = `chat-msg ${role}`;
  
  if (role === "user") {
    wrap.innerHTML = `
      <div class="chat-content-wrap" style="align-items:flex-end">
        <div class="chat-bubble">${text}</div>
      </div>
    `;
  } else {
    wrap.innerHTML = `
      <div class="chat-avatar"><span aria-hidden="true">🛡️</span></div>
      <div class="chat-content-wrap">
        <span class="chat-author">LEXGUARD AI</span>
        <div class="chat-bubble"></div>
      </div>
    `;
  }
  
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return role === "assistant" ? wrap.querySelector(".chat-bubble") : wrap;
}

function showTyping() {
  const messages = document.getElementById("chat-messages");
  const wrap = document.createElement("div");
  wrap.id = "typing-indicator";
  wrap.className = "chat-msg assistant";
  wrap.innerHTML = `
    <div class="chat-avatar"><span aria-hidden="true">🛡️</span></div>
    <div class="chat-content-wrap">
      <span class="chat-author">LEXGUARD AI</span>
      <div class="chat-bubble chat-typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    </div>
  `;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function typewriterEffect(el, text) {
  const words = text.split(" ");
  let i = 0;
  el.textContent = "";
  const timer = setInterval(() => {
    if (i < words.length) {
      el.textContent += (i === 0 ? "" : " ") + words[i++];
      document.getElementById("chat-messages").scrollTop = 99999;
    } else {
      clearInterval(timer);
    }
  }, 30);
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  appendChatMessage("user", message);
  trackChatMessageSent(message.length);
  const typing = showTyping();

  try {
    const resp = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      credentials: "include",
    });
    const data = await resp.json();
    typing.remove();

    if (!resp.ok) {
      const bubble = appendChatMessage("assistant", "");
      bubble.textContent = data.error || "Sorry, I encountered an error. Please try again.";
    } else {
      const bubble = appendChatMessage("assistant", "");
      typewriterEffect(bubble, data.response || "I could not generate a response.");
    }
  } catch (err) {
    typing.remove();
    const bubble = appendChatMessage("assistant", "");
    bubble.textContent = "Network error. Please check your connection and try again.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");

  send.addEventListener("click", () => sendChatMessage());

  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });

  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      input.value = chip.dataset.question || chip.textContent;
      sendChatMessage();
    });
  });
});
