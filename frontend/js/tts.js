/**
 * tts.js — Text-to-speech module for LexGuard.
 * Primary: Google Cloud TTS via backend. Fallback: Web Speech API.
 * @module tts
 */

/** @type {HTMLAudioElement|null} Current audio element. */
let currentAudio = null;
/** @type {SpeechSynthesisUtterance|null} Current Web Speech utterance. */
let currentUtterance = null;

/**
 * Speak text using Google TTS (backend) or Web Speech API as fallback.
 * @param {string} text - Text to synthesize.
 * @returns {Promise<void>}
 */
async function speakText(text) {
  stopSpeech();
  showTTSPlayer(text);

  try {
    const resp = await fetch(`${API_BASE_URL}/api/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.slice(0, 4500) }),
    });
    const data = await resp.json();

    if (data.audio_base64) {
      playBase64Audio(data.audio_base64);
    } else {
      useWebSpeechAPI(data.fallback_text || text);
    }
  } catch {
    useWebSpeechAPI(text);
  }
}

/**
 * Play a base64-encoded MP3 audio string.
 * @param {string} base64 - Base64 MP3 data from Google TTS.
 * @returns {void}
 */
function playBase64Audio(base64) {
  const src = `data:audio/mp3;base64,${base64}`;
  currentAudio = new Audio(src);
  currentAudio.play();
  currentAudio.onended = hideTTSPlayer;
}

/**
 * Use the browser Web Speech API as a fallback.
 * @param {string} text - Text to speak.
 * @returns {void}
 */
function useWebSpeechAPI(text) {
  if (!("speechSynthesis" in window)) { hideTTSPlayer(); return; }
  currentUtterance = new SpeechSynthesisUtterance(text);
  currentUtterance.rate = 0.9;
  currentUtterance.onend = hideTTSPlayer;
  speechSynthesis.speak(currentUtterance);
}

/** Stop any active speech. @returns {void} */
function stopSpeech() {
  if (currentAudio) { currentAudio.pause(); currentAudio = null; }
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  currentUtterance = null;
  hideTTSPlayer();
}

/**
 * Show the sticky TTS player bar.
 * @param {string} [label="Playing..."] - Label text.
 * @returns {void}
 */
function showTTSPlayer(label = "Playing...") {
  const player = document.getElementById("tts-player");
  document.getElementById("tts-label").textContent = label.slice(0, 60) + "…";
  player.style.display = "flex";
}

/** Hide the TTS player bar. @returns {void} */
function hideTTSPlayer() {
  document.getElementById("tts-player").style.display = "none";
}

// ---- Event Listeners ----
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("tts-stop").addEventListener("click", stopSpeech);
  document.getElementById("tts-pause").addEventListener("click", () => {
    if (currentAudio) {
      currentAudio.paused ? currentAudio.play() : currentAudio.pause();
    } else if ("speechSynthesis" in window) {
      speechSynthesis.paused ? speechSynthesis.resume() : speechSynthesis.pause();
    }
  });
});
