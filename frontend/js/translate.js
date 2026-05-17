/**
 * translate.js — Multilingual UI and content translation for LexGuard.
 * @module translate
 */

/** @type {string} Current active language code. */
let currentLang = "en";

/** @type {Map<string, string>} Client-side translation cache. */
const translationCache = new Map();

/**
 * Apply i18n strings to all elements with data-i18n attribute.
 * @param {string} lang - BCP-47 language code.
 * @returns {void}
 */
function applyStaticTranslations(lang) {
  const strings = (I18N[lang] || I18N["en"]);
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (strings[key]) el.textContent = strings[key];
  });
  document.documentElement.lang = lang;
}

/**
 * Translate a single text string via the backend API with client-side caching.
 * @param {string} text - Source English text.
 * @param {string} targetLang - Target language code.
 * @returns {Promise<string>} Translated text or original on failure.
 */
async function translateText(text, targetLang) {
  if (targetLang === "en" || !text) return text;
  const cacheKey = `${targetLang}::${text.slice(0, 80)}`;
  if (translationCache.has(cacheKey)) return translationCache.get(cacheKey);

  try {
    const resp = await fetch(`${API_BASE_URL}/api/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_lang: targetLang }),
    });
    if (!resp.ok) return text;
    const data = await resp.json();
    const translated = data.translated_text || text;
    translationCache.set(cacheKey, translated);
    return translated;
  } catch {
    return text;
  }
}

/**
 * Translate all clause explanation texts visible on the page.
 * @param {string} lang - Target language code.
 * @returns {Promise<void>}
 */
async function translateClauseContent(lang) {
  const plainEls = document.querySelectorAll(".clause-plain");
  for (const el of plainEls) {
    const original = el.dataset.original || el.textContent;
    el.dataset.original = original;
    el.textContent = await translateText(original, lang);
  }
}

// ---- Event Listener ----
document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("lang-select");
  select.addEventListener("change", async () => {
    currentLang = select.value;
    applyStaticTranslations(currentLang);
    if (currentLang !== "en") {
      await translateClauseContent(currentLang);
    }
  });
});
