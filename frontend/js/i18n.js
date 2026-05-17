/**
 * i18n.js — Local translation dictionary and language switcher logic.
 */

const translations = {
  en: {
    nav_upload: "Upload",
    nav_analysis: "Analysis",
    nav_chat: "Chat Assistant",
    nav_compare: "Compare Contracts",
    nav_history: "History",
    nav_search: "Legal Search",
    nav_settings: "Settings",
    btn_upgrade: "Upgrade to Pro",
    status_checking: "Checking connection...",
    status_connected: "Backend Connected",
    status_disconnected: "Backend Offline"
  },
  hi: {
    nav_upload: "अपलोड",
    nav_analysis: "विश्लेषण",
    nav_chat: "चैट सहायक",
    nav_compare: "अनुबंध तुलना",
    nav_history: "इतिहास",
    nav_search: "कानूनी खोज",
    nav_settings: "सेटिंग्स",
    btn_upgrade: "प्रो में अपग्रेड करें",
    status_checking: "कनेक्शन की जाँच...",
    status_connected: "बैकएंड कनेक्टेड",
    status_disconnected: "बैकएंड ऑफ़लाइन"
  },
  es: {
    nav_upload: "Subir",
    nav_analysis: "Análisis",
    nav_chat: "Asistente de Chat",
    nav_compare: "Comparar Contratos",
    nav_history: "Historial",
    nav_search: "Búsqueda Legal",
    nav_settings: "Ajustes",
    btn_upgrade: "Actualizar a Pro",
    status_checking: "Comprobando conexión...",
    status_connected: "Backend Conectado",
    status_disconnected: "Backend Desconectado"
  }
};

const langFlags = {
  en: "🇺🇸 EN",
  hi: "🇮🇳 HI",
  es: "🇪🇸 ES"
};

function setLanguage(lang) {
  if (!translations[lang]) return;
  localStorage.setItem("lexguard_lang", lang);
  document.getElementById("current-lang-text").textContent = langFlags[lang];
  
  // Update all elements with data-i18n attribute
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (translations[lang][key]) {
      // If element has icon children, preserve them
      const icon = el.querySelector("svg, i, span.nav-icon, span[aria-hidden]");
      if (icon && el.childNodes.length > 1) {
        // Replace just the text node
        let textNode = Array.from(el.childNodes).find(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim() !== "");
        if(textNode) {
          textNode.textContent = " " + translations[lang][key];
        } else {
          el.appendChild(document.createTextNode(" " + translations[lang][key]));
        }
      } else {
        el.textContent = translations[lang][key];
      }
    }
  });

  // Specifically check for status text update
  const statusEl = document.getElementById("api-status-text");
  const dot = document.getElementById("api-status-dot");
  if(statusEl && dot) {
    if(dot.classList.contains("connected")) {
      statusEl.textContent = translations[lang].status_connected;
    } else if (dot.classList.contains("disconnected")) {
      statusEl.textContent = translations[lang].status_disconnected;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.getElementById("lang-menu-btn");
  const menu = document.getElementById("lang-menu");
  
  if (menuBtn && menu) {
    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.classList.toggle("show");
    });
    
    document.addEventListener("click", () => {
      menu.classList.remove("show");
    });
    
    document.querySelectorAll(".lang-option").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const lang = e.target.getAttribute("data-lang");
        setLanguage(lang);
      });
    });
  }

  // Load saved language
  const saved = localStorage.getItem("lexguard_lang") || "en";
  setLanguage(saved);
});
