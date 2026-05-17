/**
 * compare.js — Contract comparison module for LexGuard.
 * @module compare
 */

/** @type {File|null} Contract A file. */
let fileA = null;
/** @type {File|null} Contract B file. */
let fileB = null;

/**
 * Set up a mini drop zone for comparison upload.
 * @param {string} dropId - ID of the drop zone element.
 * @param {string} inputId - ID of the hidden file input.
 * @param {string} nameId - ID of the filename display span.
 * @param {"A"|"B"} slot - Which contract slot this is.
 * @returns {void}
 */
function setupMiniDrop(dropId, inputId, nameId, slot) {
  const drop = document.getElementById(dropId);
  const input = document.getElementById(inputId);
  const nameEl = document.getElementById(nameId);

  drop.addEventListener("click", () => input.click());
  drop.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") input.click(); });
  drop.addEventListener("dragover", e => { e.preventDefault(); drop.classList.add("dragover"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("dragover"));
  drop.addEventListener("drop", e => {
    e.preventDefault(); drop.classList.remove("dragover");
    handleCompareFile(e.dataTransfer.files[0], slot, nameEl);
  });
  input.addEventListener("change", e => handleCompareFile(e.target.files[0], slot, nameEl));
}

/**
 * Store a file in the appropriate slot and update the UI.
 * @param {File} file - Selected file.
 * @param {"A"|"B"} slot - Which contract slot.
 * @param {HTMLElement} nameEl - Element to display the filename.
 * @returns {void}
 */
function handleCompareFile(file, slot, nameEl) {
  if (!file) return;
  if (slot === "A") fileA = file;
  else fileB = file;
  nameEl.textContent = file.name;
}

/**
 * Render the comparison results table.
 * @param {Object} data - API response from /api/compare.
 * @returns {void}
 */
function renderComparison(data) {
  const container = document.getElementById("compare-result");
  const comp = data.comparison || {};
  const diffs = comp.differences || [];

  const rowsHtml = diffs.map(d => `
    <tr>
      <td>${d.category || ""}</td>
      <td>${d.contract_a_text || "—"}</td>
      <td>${d.contract_b_text || "—"}</td>
      <td>${d.analysis || ""}</td>
      <td>${d.winner && d.winner !== "Tie" ? `<span class="winner-badge">${d.winner}</span>` : "Tie"}</td>
    </tr>`).join("");

  container.innerHTML = `
    <div class="glass-card" style="margin-bottom:1rem">
      <p><strong>📋 Summary:</strong> ${comp.summary || ""}</p>
      <p style="margin-top:.75rem"><strong>✅ Recommendation:</strong> ${comp.recommendation || ""}</p>
    </div>
    ${diffs.length > 0 ? `
    <table class="compare-table" aria-label="Contract comparison table">
      <thead><tr><th>Category</th><th>Contract A</th><th>Contract B</th><th>Analysis</th><th>Better</th></tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>` : "<p style='color:var(--muted)'>No significant differences found.</p>"}`;
}

// ---- Event Listeners ----
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

    trackComparisonStarted();
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
      btn.disabled = false; btn.innerHTML = "⚖ Compare Contracts";
    }
  });
});
