/**
 * history.js — Analysis history module for LexGuard.
 * @module history
 */

function renderHistory(history) {
  const list = document.getElementById("history-list");
  if (!history || history.length === 0) {
    list.innerHTML = `<p style="text-align:center;color:var(--text-muted);padding:3rem">No past analyses found. Upload a contract to get started.</p>`;
    return;
  }
  
  list.innerHTML = "";
  
  // Group by Today and Yesterday naively
  const now = new Date();
  const today = [];
  const older = [];
  
  history.forEach(r => {
    const d = new Date(r.created_at);
    if(d.toDateString() === now.toDateString()) today.push(r);
    else older.push(r);
  });

  const buildRow = (record) => {
    const level = scoreToLevel(record.risk_score || 0);
    let badgeClass = level.toLowerCase();
    let badgeLabel = level === 'CRITICAL' ? 'High Risk' : (level === 'HIGH' || level === 'MEDIUM' ? 'Moderate Risk' : 'Low Risk');
    let color = 'var(--text-muted)';
    if(badgeClass === 'critical' || badgeClass === 'high') { badgeClass = 'critical'; color = 'var(--risk-critical)'; badgeLabel = 'High Risk ⚠'; }
    else if(badgeClass === 'medium') { badgeClass = 'medium'; color = 'var(--risk-medium)'; badgeLabel = 'Moderate Risk ⓘ'; }
    else { badgeClass = 'safe'; color = 'var(--risk-safe)'; badgeLabel = 'Low Risk ✓'; }

    const timeStr = new Date(record.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const isDoc = (record.filename||'').toLowerCase().includes('doc');

    return `
      <div class="history-row" tabindex="0">
        <div class="history-icon-box ${isDoc?'doc':''}"><span aria-hidden="true">${isDoc?'📝':'📄'}</span></div>
        <div class="history-details">
          <div class="history-filename">${record.filename || "Unknown file"}</div>
          <div class="history-meta">
            <span><span aria-hidden="true">🕒</span> ${timeStr}</span>
            <span class="history-meta-dot">●</span>
            <span>${isDoc?'Agreement':'Contract'}</span>
            <span class="history-meta-dot">●</span>
            <span>Analyzed by: System</span>
          </div>
        </div>
        <div class="history-actions">
          <span class="risk-badge ${badgeClass}" style="color:${color}">${badgeLabel}</span>
          <button class="clause-menu-icon" aria-label="Options">⋮</button>
        </div>
      </div>
    `;
  };

  if (today.length > 0) {
    list.innerHTML += `<div class="history-group-title">TODAY</div><div class="history-list">${today.map(buildRow).join('')}</div>`;
  }
  if (older.length > 0) {
    list.innerHTML += `<div class="history-group-title yesterday" style="margin-top:2rem">YESTERDAY</div><div class="history-list">${older.map(buildRow).join('')}</div>`;
  }
}

async function loadHistory() {
  const email = document.getElementById("user-email").value.trim();
  const errEl = document.getElementById("history-error");
  errEl.style.display = "none";
  const list = document.getElementById("history-list");

  if (!email) {
    list.innerHTML = `<p style="text-align:center;color:var(--text-muted)">User email required.</p>`;
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
