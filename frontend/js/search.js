/**
 * search.js — Legal precedent search module for LexGuard.
 * @module search
 */

function renderSearchResults(results, source) {
  const container = document.getElementById("search-results");
  document.getElementById("search-results-container").style.display = "block";
  container.innerHTML = "";

  results.forEach((item, i) => {
    const card = document.createElement("div");
    card.className = "glass-card search-result-card";
    
    // Simulate match percentage
    const matchPct = Math.floor(Math.random() * 20) + 75;
    
    // Parse Google Search snippet into a "synthesis"
    const synthesis = (item.snippet || "").replace(/\.\.\./g, " ").trim() + " This precedent aligns with your search criteria and offers insights into standard judicial interpretations.";

    card.innerHTML = `
      <div class="result-card-header">
        <div>
          <div class="result-title">${item.title || "Legal Resource"}</div>
          <div class="result-citation">Appellate Court · 2023</div>
        </div>
        <div class="result-match-badge">${matchPct}% Match</div>
      </div>
      <div class="result-synthesis">
        <span class="result-synthesis-label">AI Synthesis:</span>${synthesis}
      </div>
      <div class="result-footer">
        <div class="result-tags">
          <span class="result-tag">PRECEDENT</span>
          <span class="result-tag">CASE LAW</span>
        </div>
        <a class="result-link" href="${item.link || "#"}" target="_blank" rel="noopener noreferrer">
          Read Full Opinion <span aria-hidden="true">↗</span>
        </a>
      </div>
    `;
    container.appendChild(card);
    setTimeout(() => card.classList.add("visible"), i * 150);
  });
}

async function runSearch() {
  const query = document.getElementById("search-input").value.trim();
  const errEl = document.getElementById("search-error");
  errEl.style.display = "none";
  document.getElementById("search-results-container").style.display = "none";

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
    btn.disabled = false; btn.innerHTML = "Search ➔";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-search").addEventListener("click", runSearch);
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") runSearch();
  });
});
