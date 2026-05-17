/**
 * analyze.js — Contract analysis rendering for LexGuard.
 * Renders risk gauge, clause cards, negotiation recommendations, and export.
 * @module analyze
 */

/**
 * Animate the SVG risk gauge to the given score.
 * @param {number} score - Overall risk score 0-100.
 * @returns {void}
 */
function animateGauge(score) {
  const fill = document.getElementById("gauge-fill");
  const scoreEl = document.getElementById("gauge-score");
  const levelEl = document.getElementById("gauge-risk-level");
  const circumference = 534;
  const offset = circumference - (score / 100) * circumference;
  const level = scoreToLevel(score);
  const color = RISK_COLORS[level] || "#00d4ff";

  fill.style.stroke = color;
  fill.style.strokeDashoffset = offset;
  levelEl.textContent = level;
  levelEl.style.color = color;

  let current = 0;
  const step = score / 60;
  const timer = setInterval(() => {
    current = Math.min(current + step, score);
    scoreEl.textContent = Math.round(current);
    if (current >= score) clearInterval(timer);
  }, 16);
}

/**
 * Convert a numeric score to a risk level string.
 * @param {number} score - Score 0-100.
 * @returns {string} Risk level.
 */
function scoreToLevel(score) {
  if (score >= 80) return "CRITICAL";
  if (score >= 60) return "HIGH";
  if (score >= 40) return "MEDIUM";
  if (score >= 20) return "LOW";
  return "SAFE";
}

/**
 * Render the risk distribution bar.
 * @param {Object} distribution - {CRITICAL:n, HIGH:n, ...}
 * @returns {void}
 */
function renderDistribution(distribution) {
  const container = document.getElementById("risk-distribution");
  container.innerHTML = "";
  Object.entries(distribution).forEach(([level, count]) => {
    if (count === 0) return;
    const div = document.createElement("div");
    div.className = "risk-dist-item";
    div.style.borderLeft = `3px solid ${RISK_COLORS[level] || "#888"}`;
    div.innerHTML = `<span style="color:${RISK_COLORS[level]}">${level}</span><strong>${count}</strong>`;
    container.appendChild(div);
  });
}

/**
 * Build a single clause card element.
 * @param {Object} clause - Clause data from the API.
 * @param {number} index - Clause index for stagger animation.
 * @returns {HTMLElement} Clause card div element.
 */
function buildClauseCard(clause, index) {
  const card = document.createElement("div");
  const level = (clause.risk_level || "SAFE").toUpperCase();
  card.className = `clause-card glass-card risk-${level}`;
  card.setAttribute("tabindex", "0");
  card.setAttribute("aria-label", `${clause.clause_title || "Clause"} — Risk: ${level}`);

  const redFlagsHtml = (clause.red_flags || []).map(f => `<li>${f}</li>`).join("");
  const simScore = clause.similarity_score != null
    ? `<p class="clause-similarity">📊 ${Math.round(clause.deviation_percent || 0)}% more restrictive than standard — Similarity: ${(clause.similarity_score * 100).toFixed(0)}%</p>`
    : "";

  card.innerHTML = `
    <div class="clause-header">
      <span class="clause-title">${clause.clause_title || "Legal Clause"}</span>
      <span class="risk-badge ${level.toLowerCase()}">${level}</span>
    </div>
    <span class="clause-category">${clause.category || "Other"}</span>
    <p class="clause-original">"${(clause.clause_text || "").slice(0, 250)}${clause.clause_text && clause.clause_text.length > 250 ? "…" : ""}"</p>
    <p class="clause-plain">${clause.plain_explanation || ""}</p>
    ${redFlagsHtml ? `<ul class="clause-red-flags" aria-label="Red flags">${redFlagsHtml}</ul>` : ""}
    ${simScore}
    <div class="clause-actions">
      <button class="btn btn-primary" onclick="speakText(\`${(clause.plain_explanation || "").replace(/`/g,"'")}\`)" aria-label="Listen to plain explanation">🔊 Listen</button>
    </div>`;

  // Lazy-load via IntersectionObserver
  setTimeout(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { card.classList.add("visible"); obs.disconnect(); } });
    }, { threshold: 0.1 });
    obs.observe(card);
  }, index * 80);

  card.addEventListener("click", () => {
    trackClauseClicked(clause.category || "Other", level);
    trackRiskLevelViewed(level);
  });

  return card;
}

/**
 * Render negotiation recommendations.
 * @param {Array} recs - Array of recommendation objects.
 * @returns {void}
 */
function renderNegotiations(recs) {
  const section = document.getElementById("negotiation-section");
  const list = document.getElementById("negotiation-list");
  if (!recs || recs.length === 0) { section.style.display = "none"; return; }
  section.style.display = "block";
  list.innerHTML = "";
  recs.forEach(rec => {
    const div = document.createElement("div");
    div.className = "neg-item";
    div.innerHTML = `
      <p class="neg-original">Original: "${(rec.original_clause || "").slice(0, 120)}…"</p>
      <div class="neg-alt"><strong>Proposed language:</strong><br>${rec.alternative_language || ""}</div>
      <p><strong>What to ask:</strong> ${rec.what_to_ask || ""}</p>
      <p class="neg-tip">💡 ${rec.negotiation_tip || ""}</p>
      <p style="font-size:.78rem;color:var(--muted);margin-top:.4rem">Reasonable request: ${rec.reasonable_ask ? "✅ Yes" : "⚠️ May face pushback"}</p>`;
    list.appendChild(div);
  });
}

/**
 * Main render function — called after API response arrives.
 * @param {Object} data - Full analysis API response.
 * @returns {void}
 */
function renderAnalysis(data) {
  const dashboard = document.getElementById("risk-dashboard");
  const container = document.getElementById("clauses-container");
  dashboard.style.display = "block";
  container.innerHTML = "";

  animateGauge(data.overall_risk_score || 0);
  renderDistribution(data.risk_distribution || {});
  document.getElementById("summary-text").textContent = data.summary || "";
  document.getElementById("total-clauses-count").textContent = `${(data.clauses || []).length} clauses analyzed`;
  document.getElementById("filename-display").textContent = data.filename || "";

  (data.clauses || []).forEach((clause, i) => {
    container.appendChild(buildClauseCard(clause, i));
  });

  renderNegotiations(data.negotiation_recommendations || []);
}

/**
 * Generate and download an HTML analysis report.
 * @param {Object} data - Full analysis result object.
 * @returns {void}
 */
function exportReport(data) {
  const clauses = (data.clauses || []).map(c => `
    <div style="margin-bottom:1.5rem;padding:1rem;border:1px solid #ddd;border-radius:8px;border-top:4px solid ${RISK_COLORS[c.risk_level]||'#888'}">
      <h3 style="margin-bottom:.5rem">${c.clause_title || "Clause"} <span style="font-size:.8rem;padding:.2rem .6rem;background:${RISK_COLORS[c.risk_level]||'#888'};border-radius:4px;color:#fff">${c.risk_level}</span></h3>
      <p style="font-style:italic;color:#666;font-size:.85rem">"${(c.clause_text||"").slice(0,200)}…"</p>
      <p style="margin-top:.5rem">${c.plain_explanation||""}</p>
    </div>`).join("");

  const html = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>LexGuard Report — ${data.filename||""}</title>
  <style>body{font-family:Georgia,serif;max-width:800px;margin:2rem auto;padding:0 1rem;color:#222}
  h1{color:#0a0e27}h2{color:#0066cc;margin-top:2rem}.score{font-size:3rem;font-weight:700;color:${RISK_COLORS[scoreToLevel(data.overall_risk_score)]||"#333"}}
  .disclaimer{font-size:.8rem;color:#888;border-top:1px solid #eee;margin-top:2rem;padding-top:1rem}</style></head>
  <body><h1>⚖ LexGuard Contract Analysis Report</h1>
  <p><strong>File:</strong> ${data.filename||""} &nbsp;|&nbsp; <strong>Analyzed:</strong> ${new Date().toLocaleString()}</p>
  <h2>Overall Risk Score</h2><p class="score">${data.overall_risk_score||0}/100</p>
  <p>${data.summary||""}</p>
  <h2>Clause Analysis (${(data.clauses||[]).length} clauses)</h2>${clauses}
  <p class="disclaimer">⚠ This report is generated by AI and is for informational purposes only. It does not constitute legal advice. Consult a licensed attorney before signing any legal agreement.</p>
  </body></html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `LexGuard_Report_${Date.now()}.html`;
  a.click(); URL.revokeObjectURL(url);
  trackReportDownloaded(data.overall_risk_score || 0);
}
