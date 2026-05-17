/**
 * chat.js — AI chat assistant module for LexGuard.
 * Debounced input, typewriter effect, suggested question chips.
 * @module chat
 */

/** @type {ReturnType<typeof setTimeout>} Debounce timer handle. */
let chatDebounceTimer = null;

/**
 * Append a message bubble to the chat window.
 * @param {string} role - "user" or "assistant".
 * @param {string} text - Message text content.
 * @returns {HTMLElement} The bubble element (for typewriter targeting).
 */
function appendChatMessage(role, text) {
  const messages = document.getElementById("chat-messages");
  const wrap = document.createElement("div");
  wrap.className = `chat-msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

/**
 * Show the typing indicator animation.
 * @returns {HTMLElement} The typing indicator element (remove to clear).
 */
function showTyping() {
  const messages = document.getElementById("chat-messages");
  const wrap = document.createElement("div");
  wrap.id = "typing-indicator";
  wrap.className = "chat-msg assistant";
  wrap.innerHTML = `<div class="chat-bubble chat-typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

/**
 * Animate text appearing word-by-word in a target element.
 * @param {HTMLElement} el - Element to write into.
 * @param {string} text - Full text to reveal.
 * @returns {void}
 */
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

/**
 * Send the current chat input to the API and render the response.
 * @returns {Promise<void>}
 */
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
      appendChatMessage("assistant", data.error || "Sorry, I encountered an error. Please try again.");
    } else {
      const bubble = appendChatMessage("assistant", "");
      typewriterEffect(bubble, data.response || "I could not generate a response.");
    }
  } catch (err) {
    typing.remove();
    appendChatMessage("assistant", "Network error. Please check your connection and try again.");
  }
}

// ---- Event Listeners ----
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");

  send.addEventListener("click", () => sendChatMessage());

  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });

  // Debounced input handler (for future suggestions)
  input.addEventListener("input", () => {
    clearTimeout(chatDebounceTimer);
    chatDebounceTimer = setTimeout(() => {}, DEBOUNCE_MS);
  });

  // Suggested question chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      input.value = chip.dataset.question || chip.textContent;
      sendChatMessage();
    });
  });
});
