/**
 * search.js — Legal precedent search module for LexGuard.
 * @module search
 */

/**
 * Render search result cards with staggered animation.
 * @param {Array<Object>} results - Array of {title, snippet, link} objects.
 * @param {string} source - "google", "fallback", or "cache".
 * @returns {void}
 */
function renderSearchResults(results, source) {
  const container = document.getElementById("search-results");
  container.innerHTML = `<span class="search-source-badge">Source: ${source}</span>`;

  results.forEach((item, i) => {
    const card = document.createElement("div");
    card.className = "search-card";
    card.innerHTML = `
      <p class="search-card-title">${item.title || "Legal Resource"}</p>
      <p class="search-card-snippet">${item.snippet || ""}</p>
      <a class="search-card-link" href="${item.link || "#"}" target="_blank" rel="noopener noreferrer" aria-label="Open: ${item.title}">
        🔗 ${item.link || ""}
      </a>`;
    container.appendChild(card);
    setTimeout(() => card.classList.add("visible"), i * 100);
  });
}

/**
 * Execute a legal precedent search via the backend API.
 * @returns {Promise<void>}
 */
async function runSearch() {
  const query = document.getElementById("search-input").value.trim();
  const errEl = document.getElementById("search-error");
  errEl.style.display = "none";

  if (!query) {
    errEl.textContent = "Please enter a search query.";
    errEl.style.display = "block"; return;
  }

  const btn = document.getElementById("btn-search");
  btn.disabled = true; btn.textContent = "Searching...";

  try {
    const resp = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`, { credentials: "include" });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Search failed.");
    renderSearchResults(data.results || [], data.source || "unknown");
  } catch (err) {
    errEl.textContent = err.message;
    errEl.style.display = "block";
  } finally {
    btn.disabled = false; btn.innerHTML = "🔎 Search";
  }
}

// ---- Event Listeners ----
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-search").addEventListener("click", runSearch);
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") runSearch();
  });
});
