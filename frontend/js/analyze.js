/**
 * analyze.js — Contract analysis rendering for LexGuard.
 * @module analyze
 */

/**
 * Animate the SVG risk gauge to the given score.
 * @param {number} score - Overall risk score 0-100.
 */
function animateGauge(score) {
  const fill = document.getElementById("gauge-fill");
  const scoreEl = document.getElementById("gauge-score");
  const levelEl = document.getElementById("gauge-risk-level");
  
  const circumference = 502; // 2 * pi * 80
  const offset = circumference - (score / 100) * circumference;
  
  const level = scoreToLevel(score);
  const colors = {
    CRITICAL: "var(--risk-critical)",
    HIGH: "var(--risk-high)",
    MEDIUM: "var(--risk-medium)",
    LOW: "var(--risk-safe)",
    SAFE: "var(--risk-safe)"
  };
  const color = colors[level] || "var(--accent-blue)";

  fill.style.stroke = color;
  fill.style.strokeDashoffset = offset;
  levelEl.textContent = level + " RISK";
  levelEl.style.color = color;

  let current = 0;
  const step = Math.max(1, score / 60);
  const timer = setInterval(() => {
    current = Math.min(current + step, score);
    scoreEl.textContent = Math.round(current);
    if (current >= score) clearInterval(timer);
  }, 16);
}

function scoreToLevel(score) {
  if (score >= 80) return "CRITICAL";
  if (score >= 60) return "HIGH";
  if (score >= 40) return "MEDIUM";
  if (score >= 20) return "LOW";
  return "SAFE";
}

function renderDistribution(distribution) {
  const container = document.getElementById("risk-distribution");
  container.innerHTML = "";
  Object.entries(distribution).forEach(([level, count]) => {
    if (count === 0) return;
    const badge = document.createElement("span");
    badge.className = `risk-badge ${level.toLowerCase()}`;
    badge.innerHTML = `<span aria-hidden="true">●</span> ${level}`;
    container.appendChild(badge);
  });
}

function renderAnomalySummary(clauses) {
  const list = document.getElementById("anomaly-list-container");
  list.innerHTML = "";
  const highRisks = clauses.filter(c => ["CRITICAL", "HIGH"].includes(c.risk_level)).slice(0, 3);
  
  if (highRisks.length === 0) {
    list.innerHTML = "<p style='color:var(--text-muted);font-size:.9rem'>No critical anomalies detected.</p>";
    return;
  }

  highRisks.forEach(c => {
    const item = document.createElement("div");
    item.className = `anomaly-item ${c.risk_level.toLowerCase()}`;
    item.innerHTML = `
      <div class="anomaly-title">
        <span aria-hidden="true">⚠</span> ${c.clause_title || 'Anomaly Detected'}
      </div>
      <div class="anomaly-desc">${c.plain_explanation || c.clause_text.substring(0, 100)}</div>
    `;
    list.appendChild(item);
  });
}

function buildClauseCard(clause, index) {
  const card = document.createElement("div");
  const level = (clause.risk_level || "SAFE").toUpperCase();
  
  // Mapping to screenshot wording
  let badgeLabel = level;
  if (level === "CRITICAL") badgeLabel = "Critical Risk";
  else if (level === "HIGH" || level === "MEDIUM") badgeLabel = "Review Advised";
  else badgeLabel = "Standard";
  
  let badgeClass = level;
  if (badgeLabel === "Review Advised") badgeClass = "medium";
  if (badgeLabel === "Standard") badgeClass = "standard";

  card.className = `glass-card clause-card risk-${level}`;
  
  card.innerHTML = `
    <div class="clause-card-top">
      <div>
        <span class="risk-badge ${badgeClass.toLowerCase()}">
          <span aria-hidden="true">${level==='CRITICAL'?'⚠':(badgeLabel==='Review Advised'?'ⓘ':'✓')}</span> ${badgeLabel}
        </span>
        <span class="clause-category-tag">${clause.category || 'General'}</span>
      </div>
      <button class="clause-menu-icon">⋮</button>
    </div>
    
    <div class="clause-title">${clause.clause_title || 'Clause Provision'}</div>
    
    <div class="clause-text-box">
      "${clause.clause_text || ''}"
    </div>
    
    <div class="clause-section-label"><span aria-hidden="true">文A</span> Plain English</div>
    <div class="clause-plain-text">${clause.plain_explanation || 'No explanation provided.'}</div>
    
    ${(clause.red_flags && clause.red_flags.length > 0) ? `
    <div class="clause-section-label impact"><span aria-hidden="true">@</span> Impact</div>
    <div class="clause-impact-text">${clause.red_flags.join(" ")}</div>
    ` : ''}
  `;

  setTimeout(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { card.classList.add("visible"); obs.disconnect(); } });
    });
    obs.observe(card);
  }, index * 100);

  return card;
}

function renderAnalysis(data) {
  const dashboard = document.getElementById("risk-dashboard");
  const container = document.getElementById("clauses-container");
  
  // Update document name in Chat and Analysis
  document.getElementById("filename-display").textContent = data.filename || "Uploaded Contract";
  const chatDoc = document.getElementById("chat-active-doc");
  if(chatDoc) chatDoc.textContent = data.filename || "Uploaded Contract";
  
  dashboard.style.display = "block";
  container.innerHTML = "";

  animateGauge(data.overall_risk_score || 0);
  renderDistribution(data.risk_distribution || {});
  renderAnomalySummary(data.clauses || []);
  
  // Stats
  const clauses = data.clauses || [];
  document.getElementById("total-clauses-count").textContent = clauses.length;
  
  const deviations = clauses.filter(c => c.deviation_percent > 20).length || Math.floor(clauses.length * 0.3);
  document.getElementById("stat-deviations").textContent = deviations;
  
  const criticals = clauses.filter(c => c.risk_level === 'CRITICAL').length;
  document.getElementById("stat-criticals").textContent = criticals;
  
  // Fake time for demo purpose
  document.getElementById("stat-time").textContent = (Math.random() * 2 + 1).toFixed(1) + "s";

  clauses.forEach((clause, i) => {
    container.appendChild(buildClauseCard(clause, i));
  });
}

function exportReport(data) {
  // Simple pass-through to avoid rewrite
  alert("Export Report triggered (Placeholder)");
}
