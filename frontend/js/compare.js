/**
 * compare.js — Contract comparison module for LexGuard.
 * @module compare
 */

let fileA = null;
let fileB = null;

function setupMiniDrop(dropId, inputId, nameId, slot) {
  const drop = document.getElementById(dropId);
  const input = document.getElementById(inputId);
  const nameEl = document.getElementById(nameId);

  drop.addEventListener("click", () => input.click());
  input.addEventListener("change", e => {
    if(!e.target.files[0]) return;
    if(slot === "A") fileA = e.target.files[0];
    else fileB = e.target.files[0];
    nameEl.textContent = e.target.files[0].name;
    drop.style.borderColor = "var(--accent-blue)";
    drop.style.background = "rgba(88,166,255,0.05)";
  });
}

function renderComparison(data) {
  const container = document.getElementById("compare-result");
  const comp = data.comparison || {};
  const diffs = comp.differences || [];

  // Update Stats
  document.getElementById("comp-stat-altered").textContent = diffs.length;
  let fav = 0, unfav = 0;
  diffs.forEach(d => {
    if(d.winner === "Contract A") fav++;
    else if(d.winner === "Contract B") unfav++;
  });
  document.getElementById("comp-stat-fav").textContent = fav;
  document.getElementById("comp-stat-unfav").textContent = unfav;
  
  if (unfav > fav) {
    document.getElementById("comp-stat-risk").textContent = "High ⚠";
    document.getElementById("comp-stat-risk").className = "stat-value highlight-red";
  } else if (unfav > 0) {
    document.getElementById("comp-stat-risk").textContent = "Moderate ⚠";
    document.getElementById("comp-stat-risk").className = "stat-value highlight-yellow";
  } else {
    document.getElementById("comp-stat-risk").textContent = "Low ✓";
    document.getElementById("comp-stat-risk").style.color = "var(--risk-safe)";
  }

  const rowsHtml = diffs.map((d, i) => {
    const isUnfavorable = d.winner === "Contract B";
    
    // Naive highlighting for demo - in reality, would use diff-match-patch
    let textA = d.contract_a_text || "";
    let textB = d.contract_b_text || "";
    
    if (textA !== textB) {
      if (textA.length > textB.length) textA = `<span class="diff-del">${textA}</span>`;
      else textB = textB.replace(/(not|three times|3x|unlimited)/gi, '<span class="diff-add">$1</span>');
    }

    return `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem">
      <div class="compare-clause-box">
        <div class="compare-clause-title">${i+1}. ${d.category || 'Clause'}</div>
        <div class="compare-clause-content">${textA}</div>
      </div>
      <div class="compare-clause-box" style="${isUnfavorable ? 'border-color:var(--risk-critical);box-shadow:inset 0 0 10px rgba(255,68,68,0.05)' : ''}">
        <div class="compare-clause-title">
          ${i+1}. ${d.category || 'Clause'}
          ${isUnfavorable ? '<span class="compare-unfavorable">📉 Unfavorable</span>' : ''}
        </div>
        <div class="compare-clause-content">${textB}</div>
      </div>
    </div>
    `;
  }).join("");

  container.innerHTML = `
    <div class="compare-panels" style="margin-top:0">
      <div class="panel-header">
        <div class="panel-filename"><span aria-hidden="true">📄</span> ${fileA ? fileA.name : 'Contract A'}</div>
        <span class="panel-badge">Original</span>
      </div>
      <div class="panel-header">
        <div class="panel-filename"><span aria-hidden="true">📄</span> ${fileB ? fileB.name : 'Contract B'}</div>
        <span class="panel-badge counter">Counter-party</span>
      </div>
    </div>
    <div style="margin-top:1.5rem">
      ${rowsHtml || '<p style="color:var(--text-muted)">No significant differences found.</p>'}
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  setupMiniDrop("mini-drop-a", "compare-file-a", "compare-name-a", "A");
  setupMiniDrop("mini-drop-b", "compare-file-b", "compare-name-b", "B");

  document.getElementById("btn-compare").addEventListener("click", async () => {
    const errEl = document.getElementById("compare-error");
    errEl.style.display = "none";

    if (!fileA || !fileB) {
      errEl.textContent = "Please upload both Contract A and Contract B.";
      errEl.style.display = "block"; return;
    }

    const btn = document.getElementById("btn-compare");
    btn.disabled = true; btn.textContent = "Comparing...";

    const form = new FormData();
    form.append("file_a", fileA);
    form.append("file_b", fileB);

    try {
      const resp = await fetch(`${API_BASE_URL}/api/compare`, { method: "POST", body: form, credentials: "include" });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Comparison failed.");
      renderComparison(data);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = "block";
    } finally {
      btn.disabled = false; btn.innerHTML = "<span aria-hidden='true'>✓</span> Compare";
    }
  });
});
