/**
 * history.js — Analysis history module for LexGuard.
 * Loads past analyses from MongoDB via the backend API.
 * @module history
 */

/**
 * Render the analysis history list.
 * @param {Array<Object>} history - Array of past analysis records.
 * @returns {void}
 */
function renderHistory(history) {
  const list = document.getElementById("history-list");
  if (!history || history.length === 0) {
    list.innerHTML = `<p class="history-empty">📋 No past analyses found. Upload a contract to get started.</p>`;
    return;
  }
  list.innerHTML = "";
  history.forEach(record => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.setAttribute("tabindex", "0");
    item.setAttribute("role", "button");
    item.setAttribute("aria-label", `Analysis: ${record.filename}, Risk Score: ${record.risk_score}`);

    const level = scoreToLevel(record.risk_score || 0);
    const color = RISK_COLORS[level] || "#888";
    const date = record.created_at ? new Date(record.created_at).toLocaleString() : "Unknown date";

    item.innerHTML = `
      <div class="history-score" style="color:${color}">${record.risk_score || 0}</div>
      <div class="history-info">
        <div class="history-filename">${record.filename || "Unknown file"}</div>
        <div class="history-date">${date}</div>
        <div class="history-summary">${(record.summary || "").slice(0, 100)}…</div>
      </div>
      <span class="risk-badge ${level.toLowerCase()}">${level}</span>`;

    list.appendChild(item);
  });
}

/**
 * Load history for the current user's email from the API.
 * @returns {Promise<void>}
 */
async function loadHistory() {
  const email = document.getElementById("user-email").value.trim();
  const errEl = document.getElementById("history-error");
  errEl.style.display = "none";
  const list = document.getElementById("history-list");
  list.innerHTML = "<p style='color:var(--muted);text-align:center;padding:2rem'>Loading history…</p>";

  if (!email) {
    list.innerHTML = `<p class="history-empty">Enter your email address above to view your analysis history.</p>`;
    return;
  }

  try {
    const resp = await fetch(`${API_BASE_URL}/api/history?email=${encodeURIComponent(email)}`, { credentials: "include" });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Failed to load history.");
    renderHistory(data.history || []);
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
    list.innerHTML = "";
  }
}
