```
 _     _______  __  _______  _   _    _    ____  ____
| |   | ____\ \/ / / _____/ | | | |  / \  |  _ \|  _ \
| |   |  _|  \  / | |  ___  | | | | / _ \ | |_) | | | |
| |___| |___ /  \ | | |_| | | |_| |/ ___ \|  _ <| |_| |
|_____|_____/_/\_\ \_______/  \___/_/   \_\_| \_\____/
```

# ⚖ LexGuard — AI-Powered Contract Intelligence Platform

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green?logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen?logo=mongodb)
![Gemini API](https://img.shields.io/badge/Gemini-2.5--flash-purple?logo=google)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)

> **Analyze legal contracts with AI. Identify hidden risks. Make informed decisions before signing.**

LexGuard is a production-grade, full-stack AI contract intelligence platform that parses PDF/DOCX/TXT contracts, extracts and classifies clauses, scores risk levels, explains implications in plain language, and guides users through negotiation — all powered by Google Gemini 2.5 Flash.

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📤 **Smart Upload** | Drag & drop PDF, DOCX, TXT — magic byte validation, 10MB limit |
| 🔍 **Clause Extraction** | Gemini identifies 10-20 key clauses with categories and positions |
| ⚡ **Risk Scoring** | CRITICAL/HIGH/MEDIUM/LOW/SAFE with animated circular gauge |
| 📝 **Plain Language** | Every clause explained as if talking to a friend with zero legal knowledge |
| 💬 **AI Chat** | Ask anything about your contract; Gemini answers with full context |
| ⚖ **Contract Compare** | Upload two contracts; AI shows clause-by-clause winner analysis |
| 🤝 **Negotiation Guide** | Exact alternative language + what to ask the other party |
| 🔎 **Legal Search** | Google Custom Search for precedents + curated fallback |
| 📊 **RAG Similarity** | sentence-transformers compare clauses vs. standard fair language |
| 📋 **History** | MongoDB-stored past analyses; click to reload full results |
| 🌐 **Multilingual** | 6 languages via Google Translate + MyMemory fallback |
| 🔊 **Text-to-Speech** | Google Cloud TTS + Web Speech API fallback per clause |
| 📄 **Export Report** | Downloadable styled HTML report with all findings |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| Backend | Python 3.11, Flask 3.0.3 (factory pattern) |
| Database | MongoDB Atlas (PyMongo), Firebase Firestore (backup) |
| AI Core | Google Gemini 2.5 Flash |
| Document Parsing | PyMuPDF, python-docx, pytesseract |
| Vector Search | sentence-transformers, numpy |
| Translation | Google Cloud Translate + MyMemory fallback |
| TTS | Google Cloud Text-to-Speech + Web Speech API fallback |
| Search | Google Custom Search + static curated fallback |
| Analytics | Google Analytics 4 |
| Fonts | Google Fonts (Inter + Roboto Slab) |
| Deployment | Render (backend), Vercel (frontend) |

---

## 🌐 Google Services Integration

| Service | Purpose | Location | Fallback |
|---------|---------|----------|----------|
| **Gemini 2.5 Flash** | Clause extraction, risk scoring, chat, compare, negotiation, summaries | `services/gemini_service.py` | Error response |
| **Google Custom Search** | Legal precedent lookup | `services/search_service.py`, `routes/search.py` | Static curated results |
| **Google Cloud Translate** | Dynamic content translation (6 languages) | `services/translate_service.py` | MyMemory free API |
| **Google Cloud TTS** | Clause explanation audio | `services/tts_service.py`, `routes/tts.py` | Browser Web Speech API |
| **Google Analytics 4** | 7 custom events tracked | `frontend/js/analytics.js`, `index.html` | Silent no-op |
| **Google Fonts** | Inter + Roboto Slab throughout | `index.html` CSS import | Browser defaults |
| **Firebase Firestore** | Secondary analysis backup | `services/firebase_service.py` | MongoDB-only mode |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   VERCEL (Frontend)                  │
│  index.html → css/styles.css → js/*.js               │
│  Upload | Analyze | Chat | Compare | History | Search│
└───────────────────┬─────────────────────────────────┘
                    │ HTTP (fetch)
┌───────────────────▼─────────────────────────────────┐
│                  RENDER (Backend)                    │
│  Flask create_app() → 8 Blueprints                  │
│  /api/analyze  /api/chat    /api/compare             │
│  /api/search   /api/tts     /api/translate           │
│  /api/history  /api/health                           │
└─┬──────────┬──────────┬──────────┬──────────────────┘
  │          │          │          │
  ▼          ▼          ▼          ▼
Gemini    MongoDB    Google     Firebase
2.5 Flash  Atlas     Cloud      Firestore
          + Redis   (Translate  (Backup)
          Pool       TTS Search)
```

---

## ⚙ Local Setup

### 1. Clone and enter directory
```bash
git clone https://github.com/your-username/lexguard.git
cd lexguard
```

### 2. Create Python virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 5. Run the backend
```bash
python wsgi.py
# Server starts at http://localhost:5000
```

### 6. Open the frontend
Open `frontend/index.html` in your browser, or serve with:
```bash
python -m http.server 5500 --directory frontend
```
Then visit `http://localhost:5500`

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | **Yes** | Google Gemini API key |
| `MONGO_URI` | Recommended | MongoDB Atlas connection string |
| `SECRET_KEY` | Yes | Flask session secret |
| `GOOGLE_TRANSLATE_API_KEY` | Optional | Google Cloud Translate key |
| `GOOGLE_TTS_API_KEY` | Optional | Google Cloud TTS key |
| `GOOGLE_SEARCH_API_KEY` | Optional | Google Custom Search API key |
| `GOOGLE_SEARCH_ENGINE_ID` | Optional | Programmable Search Engine cx ID |
| `GA4_MEASUREMENT_ID` | Optional | Google Analytics 4 Measurement ID |
| `FIREBASE_PROJECT_ID` | Optional | Firebase project ID |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Optional | Firebase service account JSON string |
| `MYMEMORY_EMAIL` | Optional | Email for higher MyMemory quota |
| `CORS_ORIGINS` | Yes (prod) | Comma-separated allowed origins |
| `TESSERACT_CMD` | Optional | Path to tesseract binary for OCR |

---

## 🧪 Running Tests

```bash
# Run full test suite with coverage
python -m pytest tests/ -v --tb=short

# Expected output:
# tests/test_health.py ....                   PASSED
# tests/test_sanitizer.py ..........          PASSED
# tests/test_rate_limiter.py .....            PASSED
# tests/test_risk_scorer.py ..........        PASSED
# tests/test_document_parser.py ........      PASSED
# tests/test_analyze.py .....                 PASSED
# tests/test_chat.py .....                    PASSED
# tests/test_compare.py .....                 PASSED
# tests/test_search.py .....                  PASSED
# Coverage: 75%+
```

---

## 📄 Sample Contracts

| File | Description | Expected Risk |
|------|-------------|---------------|
| `sample_employment.txt` | Employment contract with 5-year IP assignment, 3-year global non-compete, no-severance termination | 3+ CRITICAL clauses |
| `sample_nda.txt` | One-sided NDA with unlimited confidentiality, $1M per-breach damages, no exceptions | 4+ CRITICAL clauses |
| `sample_subscription.txt` | Subscription terms with hidden auto-renewal, unlimited data selling, $1 liability cap | 5+ CRITICAL clauses |

---

## 🤖 AI Reasoning Methodology

LexGuard uses a multi-stage legal reasoning pipeline:

1. **Extraction**: Gemini receives the full contract text with an expert legal analyst persona prompt, identifying 10-20 significant clauses with categories and positions.

2. **Risk Scoring**: Each clause is evaluated independently by Gemini for risk level (CRITICAL/HIGH/MEDIUM/LOW/SAFE), with a numeric score 0-100, plain English explanation, and specific red flags.

3. **RAG Similarity**: sentence-transformers embed each clause and compare against 15 curated standard fair clauses. Clauses deviating >25% from standard language are flagged.

4. **Weighted Aggregation**: Overall risk score weights CRITICAL clauses 4x and HIGH clauses 3x, preventing a single bad clause from being hidden by many safe ones.

5. **Negotiation**: Gemini generates specific alternative contract language, negotiation tips, and feasibility assessments for every HIGH/CRITICAL clause.

---

## 🔒 Security Measures

- All API keys stored in `.env` only — never hardcoded
- Input sanitized via `bleach` + custom validators before any processing
- Magic byte validation for file uploads (not just extension)
- Rate limiting: 20 requests/minute per IP via flask-limiter
- Security headers on all responses: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, CSP
- CORS restricted to configured origins only
- Error responses never expose stack traces
- Files processed in-memory, never written to disk

---

## ♿ Accessibility (WCAG 2.1 AA)

- `<html lang="en">` on root element
- Skip navigation link as first body element
- All images have descriptive `alt` attributes
- All buttons have `aria-label` attributes
- All inputs have associated `<label>` elements
- `aria-live="polite"` on analysis results and chat
- `aria-busy` toggled during loading states
- `role="alert"` on all error messages
- Visible focus indicator: `outline: 3px solid #00d4ff`
- `prefers-reduced-motion` query disabling all animations
- Minimum 4.5:1 contrast ratio maintained
- Full keyboard navigation throughout

---

## 🚀 Deployment

### Backend → Render
1. Connect your GitHub repo to Render
2. Settings auto-loaded from `render.yaml`
3. Add environment variables in Render dashboard
4. Deploy — live at `https://your-app.onrender.com`

### Frontend → Vercel
1. Connect GitHub repo to Vercel
2. Set Output Directory to `frontend`
3. Update `frontend/js/config.js` with your Render URL
4. Deploy — live at `https://your-app.vercel.app`
5. Update `CORS_ORIGINS` in Render with your Vercel URL

---

## 🔮 Future Improvements

- WebSocket streaming for real-time Gemini responses
- PDF annotation overlay showing clause positions
- Chrome extension for analyzing contracts on any website
- Integration with DocuSign API for direct signing flow
- Contract template generator based on risk-free clause library
- Multi-party contract analysis with role-specific risk views
- Legal jurisdiction detection and jurisdiction-specific risk rules

---

## ⚠ Legal Disclaimer

LexGuard is an AI-powered tool for **informational purposes only**. The analysis, risk scores, explanations, and recommendations generated by LexGuard do **not** constitute legal advice. LexGuard is not a law firm and cannot provide legal representation. Always consult a licensed attorney in your jurisdiction before signing any legal agreement. The developers of LexGuard accept no liability for any decisions made based on its output.
