/**
 * analytics.js — Google Analytics 4 event tracking for LexGuard.
 * @module analytics
 */

/**
 * Track a custom GA4 event safely (no-op if gtag unavailable).
 * @param {string} eventName - GA4 event name.
 * @param {Object} [params={}] - Event parameters.
 * @returns {void}
 */
function trackEvent(eventName, params = {}) {
  if (typeof gtag === "function") {
    gtag("event", eventName, params);
  }
}

/**
 * Track a document upload event.
 * @param {string} fileType - File extension (pdf/docx/txt).
 * @param {number} fileSizeBytes - File size in bytes.
 * @returns {void}
 */
function trackDocumentUpload(fileType, fileSizeBytes) {
  trackEvent("document_upload", { file_type: fileType, file_size: fileSizeBytes });
}

/**
 * Track completion of a full contract analysis.
 * @param {number} riskScore - Overall risk score 0-100.
 * @param {number} clauseCount - Number of extracted clauses.
 * @returns {void}
 */
function trackAnalysisComplete(riskScore, clauseCount) {
  trackEvent("analysis_complete", { risk_score: riskScore, clause_count: clauseCount });
}

/**
 * Track when a user clicks on a clause card to expand it.
 * @param {string} clauseCategory - Category of the clause.
 * @param {string} riskLevel - Risk level of the clause.
 * @returns {void}
 */
function trackClauseClicked(clauseCategory, riskLevel) {
  trackEvent("clause_clicked", { category: clauseCategory, risk_level: riskLevel });
}

/**
 * Track when a risk level badge is viewed.
 * @param {string} riskLevel - CRITICAL/HIGH/MEDIUM/LOW/SAFE.
 * @returns {void}
 */
function trackRiskLevelViewed(riskLevel) {
  trackEvent("risk_level_viewed", { risk_level: riskLevel });
}

/**
 * Track when a chat message is sent.
 * @param {number} messageLength - Character count of the message.
 * @returns {void}
 */
function trackChatMessageSent(messageLength) {
  trackEvent("chat_message_sent", { message_length: messageLength });
}

/**
 * Track when a comparison analysis is started.
 * @returns {void}
 */
function trackComparisonStarted() {
  trackEvent("comparison_started");
}

/**
 * Track when a report is downloaded.
 * @param {number} riskScore - Risk score of the downloaded report.
 * @returns {void}
 */
function trackReportDownloaded(riskScore) {
  trackEvent("report_downloaded", { risk_score: riskScore });
}
