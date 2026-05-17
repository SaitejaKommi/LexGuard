/**
 * upload.js — Drag & drop upload logic for LexGuard.
 * @module upload
 */

/** @type {File|null} Current file selected for upload. */
let currentFile = null;

/** @type {Object|null} Last completed analysis result. */
let lastAnalysisResult = null;

/**
 * Show or hide the progress container and update a specific step.
 * @param {boolean} visible - Whether to show the progress UI.
 * @param {string} [activeStep=""] - Step ID to mark active (e.g. "step-parse").
 * @param {number} [pct=0] - Progress bar percentage 0-100.
 * @param {string} [label=""] - Progress label text.
 * @returns {void}
 */
function setProgress(visible, activeStep = "", pct = 0, label = "") {
  const container = document.getElementById("progress-container");
  const bar = document.getElementById("progress-bar");
  const lbl = document.getElementById("progress-label");
  const wrap = document.getElementById("progress-bar-wrap");
  container.style.display = visible ? "block" : "none";
  if (!visible) return;
  bar.style.width = pct + "%";
  wrap.setAttribute("aria-valuenow", pct);
  lbl.textContent = label;
  document.querySelectorAll(".progress-step").forEach(s => {
    s.classList.remove("active", "complete");
    const steps = ["step-parse","step-extract","step-analyze","step-score","step-done"];
    const activeIdx = steps.indexOf(activeStep);
    const stepIdx = steps.indexOf(s.id);
    if (stepIdx < activeIdx) s.classList.add("complete");
    if (s.id === activeStep) s.classList.add("active");
  });
}

/**
 * Display an error message in the upload error banner.
 * @param {string} message - Error text to display.
 * @returns {void}
 */
function showUploadError(message) {
  const el = document.getElementById("upload-error");
  el.textContent = message;
  el.style.display = "block";
  el.setAttribute("role", "alert");
}

/** Clear the upload error banner. @returns {void} */
function clearUploadError() {
  const el = document.getElementById("upload-error");
  el.textContent = "";
  el.style.display = "none";
}

/**
 * Validate file client-side before upload.
 * @param {File} file - File selected by the user.
 * @returns {{valid: boolean, error: string}} Validation result.
 */
function validateFile(file) {
  const MAX = 10 * 1024 * 1024;
  const allowed = ["pdf", "docx", "txt"];
  const ext = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) return { valid: false, error: `Unsupported file type ".${ext}". Please upload PDF, DOCX, or TXT.` };
  if (file.size > MAX) return { valid: false, error: "File exceeds 10 MB limit." };
  if (file.size === 0) return { valid: false, error: "File is empty." };
  return { valid: true, error: "" };
}

/**
 * Upload and analyze a file, driving the progress UI and routing to analyze.js.
 * @param {File} file - Validated file to upload.
 * @returns {Promise<void>}
 */
async function uploadAndAnalyze(file) {
  clearUploadError();
  const email = document.getElementById("user-email").value.trim();
  const formData = new FormData();
  formData.append("file", file);
  if (email) formData.append("email", email);

  trackDocumentUpload(file.name.split(".").pop(), file.size);
  console.log("[LexGuard] Analysis Step 1: Parsing document...");
  setProgress(true, "step-parse", 10, "Parsing document...");
  switchSection("analysis");
  document.getElementById("analysis-section").setAttribute("aria-busy", "true");

  const steps = [
    { step: "step-extract", pct: 30, label: "Extracting clauses..." },
    { step: "step-analyze", pct: 55, label: "Analyzing with AI..." },
    { step: "step-score", pct: 80, label: "Scoring risks..." },
  ];
  let stepIdx = 0;
  const stepTimer = setInterval(() => {
    if (stepIdx < steps.length) {
      const s = steps[stepIdx++];
      console.log(`[LexGuard] Analysis Step ${stepIdx+1}: ${s.label}`);
      setProgress(true, s.step, s.pct, s.label);
    }
  }, 4000);

  try {
    const resp = await fetch(`${API_BASE_URL}/api/analyze`, { method: "POST", body: formData, credentials: "include" });
    clearInterval(stepTimer);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || `Server error ${resp.status}`);
    }
    const data = await resp.json();
    console.log("[LexGuard] Analysis Complete: Data received.");
    setProgress(true, "step-done", 100, "Analysis complete!");
    setTimeout(() => setProgress(false), 2000);
    lastAnalysisResult = data;
    renderAnalysis(data);
    trackAnalysisComplete(data.overall_risk_score, (data.clauses || []).length);
    document.getElementById("btn-export").style.display = "inline-flex";
  } catch (err) {
    clearInterval(stepTimer);
    setProgress(false);
    console.error("[LexGuard] Analysis Error:", err.message);
    let errorMsg = err.message || "Analysis failed. Please try again.";
    if (errorMsg.includes("Failed to fetch") || errorMsg.includes("NetworkError")) {
      errorMsg = "Backend server is not running. Please start the Flask server.";
    }
    showUploadError(errorMsg);
    switchSection("upload");
  } finally {
    document.getElementById("analysis-section").setAttribute("aria-busy", "false");
  }
}

/**
 * Switch the visible section by data-section name.
 * @param {string} sectionName - Section to show (upload/analysis/chat/...).
 * @returns {void}
 */
function switchSection(sectionName) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active-section"));
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  const target = document.getElementById(`${sectionName}-section`);
  if (target) target.classList.add("active-section");
  const link = document.querySelector(`[data-section="${sectionName}"]`);
  if (link) link.classList.add("active");
}

/** Load a sample contract by filename and trigger analysis. @param {string} name @returns {Promise<void>} */
async function loadSample(name) {
  try {
    const resp = await fetch(`../sample_contracts/${name}.txt`);
    if (!resp.ok) throw new Error("Could not load sample.");
    const text = await resp.text();
    const blob = new Blob([text], { type: "text/plain" });
    const file = new File([blob], `${name}.txt`, { type: "text/plain" });
    await uploadAndAnalyze(file);
  } catch (e) {
    showUploadError("Could not load sample contract.");
  }
}

// ---- Event Listeners ----
document.addEventListener("DOMContentLoaded", () => {
  const zone = document.getElementById("upload-zone");
  const input = document.getElementById("file-input");
  const btn = document.getElementById("upload-btn");

  btn.addEventListener("click", () => input.click());
  zone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") input.click(); });

  input.addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;
    const { valid, error } = validateFile(file);
    if (!valid) { showUploadError(error); return; }
    currentFile = file;
    uploadAndAnalyze(file);
  });

  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault(); zone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const { valid, error } = validateFile(file);
    if (!valid) { showUploadError(error); return; }
    uploadAndAnalyze(file);
  });

  const sampleEmp = document.getElementById("sample-employment");
  if(sampleEmp) sampleEmp.addEventListener("click", () => loadSample("sample_employment"));
  const sampleNda = document.getElementById("sample-nda");
  if(sampleNda) sampleNda.addEventListener("click", () => loadSample("sample_nda"));
  const sampleSub = document.getElementById("sample-subscription");
  if(sampleSub) sampleSub.addEventListener("click", () => loadSample("sample_subscription"));

  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      switchSection(link.dataset.section);
      if (link.dataset.section === "history") loadHistory();
    });
  });

  document.getElementById("btn-export").addEventListener("click", () => {
    if (lastAnalysisResult) exportReport(lastAnalysisResult);
  });
});
