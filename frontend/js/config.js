/**
 * config.js — LexGuard frontend configuration.
 * @module config
 */

/** @const {string} API_BASE_URL — Backend URL. Replace with your Render URL after deployment. */
const API_BASE_URL = "http://localhost:5000";

/** @const {Object} RISK_COLORS — Hex colors keyed by risk level string. */
const RISK_COLORS = {
  CRITICAL: "#ff3b3b",
  HIGH: "#ff8c00",
  MEDIUM: "#ffd700",
  LOW: "#00d4ff",
  SAFE: "#00e676",
};

/** @const {number} DEBOUNCE_MS — Chat input debounce delay in milliseconds. */
const DEBOUNCE_MS = 300;

/** @const {number} ANALYSIS_CACHE_TTL_MS — Client-side analysis cache TTL in ms (10 min). */
const ANALYSIS_CACHE_TTL_MS = 10 * 60 * 1000;

/** @const {Object} I18N — UI string translations keyed by language code then i18n key. */
const I18N = {
  en: {
    hero_title: "Contract Intelligence Platform",
    hero_subtitle: "AI-powered risk analysis · Plain language explanations · Negotiation guidance",
    upload_heading: "Upload Contract",
    upload_drag: "Drag & Drop your contract here",
    upload_hint: "PDF, DOCX, or TXT · Max 10 MB",
    sample_contracts: "Try Sample Contracts",
    analysis_heading: "Contract Analysis",
    summary_title: "Analysis Summary",
    negotiation_title: "Negotiation Recommendations",
    chat_heading: "AI Legal Assistant",
    chat_welcome: "Upload a contract to start asking questions about it.",
    compare_heading: "Compare Contracts",
    history_heading: "Analysis History",
    search_heading: "Legal Precedent Search",
  },
  hi: {
    hero_title: "अनुबंध बुद्धिमत्ता प्लेटफ़ॉर्म",
    hero_subtitle: "AI-संचालित जोखिम विश्लेषण · सरल भाषा में स्पष्टीकरण",
    upload_heading: "अनुबंध अपलोड करें",
    upload_drag: "यहाँ अपना अनुबंध खींचें और छोड़ें",
    upload_hint: "PDF, DOCX, या TXT · अधिकतम 10 MB",
    sample_contracts: "नमूना अनुबंध आज़माएं",
    analysis_heading: "अनुबंध विश्लेषण",
    summary_title: "विश्लेषण सारांश",
    negotiation_title: "वार्ता अनुशंसाएं",
    chat_heading: "AI कानूनी सहायक",
    chat_welcome: "प्रश्न पूछने के लिए एक अनुबंध अपलोड करें।",
    compare_heading: "अनुबंध की तुलना करें",
    history_heading: "विश्लेषण इतिहास",
    search_heading: "कानूनी मिसाल खोज",
  },
  es: {
    hero_title: "Plataforma de Inteligencia Contractual",
    hero_subtitle: "Análisis de riesgo con IA · Explicaciones en lenguaje sencillo",
    upload_heading: "Subir Contrato",
    upload_drag: "Arrastra y suelta tu contrato aquí",
    upload_hint: "PDF, DOCX o TXT · Máx 10 MB",
    sample_contracts: "Prueba Contratos de Muestra",
    analysis_heading: "Análisis de Contrato",
    summary_title: "Resumen del Análisis",
    negotiation_title: "Recomendaciones de Negociación",
    chat_heading: "Asistente Legal IA",
    chat_welcome: "Sube un contrato para empezar a hacer preguntas.",
    compare_heading: "Comparar Contratos",
    history_heading: "Historial de Análisis",
    search_heading: "Búsqueda de Precedentes Legales",
  },
  fr: {
    hero_title: "Plateforme d'Intelligence Contractuelle",
    upload_heading: "Télécharger le Contrat",
    analysis_heading: "Analyse du Contrat",
    chat_heading: "Assistant Juridique IA",
    compare_heading: "Comparer les Contrats",
    history_heading: "Historique d'Analyse",
    search_heading: "Recherche de Précédents Juridiques",
  },
  ar: {
    hero_title: "منصة ذكاء العقود",
    upload_heading: "رفع العقد",
    analysis_heading: "تحليل العقد",
    chat_heading: "المساعد القانوني بالذكاء الاصطناعي",
    compare_heading: "مقارنة العقود",
    history_heading: "سجل التحليل",
    search_heading: "البحث في السوابق القانونية",
  },
  te: {
    hero_title: "కాంట్రాక్ట్ ఇంటెలిజెన్స్ ప్లాట్‌ఫారమ్",
    upload_heading: "కాంట్రాక్ట్ అప్‌లోడ్ చేయండి",
    analysis_heading: "కాంట్రాక్ట్ విశ్లేషణ",
    chat_heading: "AI చట్టపరమైన సహాయకుడు",
  },
};

/**
 * Ping backend health endpoint and update UI.
 */
async function checkBackendHealth() {
  const dot = document.getElementById("api-status-dot");
  const text = document.getElementById("api-status-text");
  if (!dot || !text) return;
  
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: "GET" });
    if (res.ok) {
      dot.className = "status-dot connected";
      if (typeof translations !== "undefined" && typeof localStorage !== "undefined") {
        const lang = localStorage.getItem("lexguard_lang") || "en";
        text.textContent = (translations[lang] && translations[lang].status_connected) ? translations[lang].status_connected : "Backend Connected";
      } else {
        text.textContent = "Backend Connected";
      }
    } else {
      throw new Error("Not OK");
    }
  } catch (e) {
    dot.className = "status-dot disconnected";
    if (typeof translations !== "undefined" && typeof localStorage !== "undefined") {
      const lang = localStorage.getItem("lexguard_lang") || "en";
      text.textContent = (translations[lang] && translations[lang].status_disconnected) ? translations[lang].status_disconnected : "Backend Offline";
    } else {
      text.textContent = "Backend Offline";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  // Check every 30s
  setInterval(checkBackendHealth, 30000);
});
