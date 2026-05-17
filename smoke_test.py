import requests, json

BASE = 'http://localhost:5000/api'

def test(name, r):
    print(f"\n=== {name} === [{r.status_code}]")
    try:
        print(json.dumps(r.json(), indent=2)[:600])
    except Exception:
        print(r.text[:300])

# 1. Health check
test("HEALTH", requests.get(f'{BASE}/health'))

# 2. History (no email)
test("HISTORY no-email", requests.get(f'{BASE}/history'))

# 3. History with email
test("HISTORY with-email", requests.get(f'{BASE}/history?email=demo@lexguard.ai'))

# 4. Search
test("SEARCH", requests.get(f'{BASE}/search?q=non-compete+clause'))

# 5. Translate to Hindi
test("TRANSLATE->HI", requests.post(f'{BASE}/translate', json={'text': 'This contract is for employment.', 'target_lang': 'hi'}))

# 6. TTS
test("TTS", requests.post(f'{BASE}/tts', json={'text': 'Hello legal world', 'language_code': 'en-US'}))

# 7. Glossary (requires Gemini)
test("GLOSSARY indemnification", requests.post(f'{BASE}/glossary', json={'term': 'indemnification'}))

# 8. Negotiate with no clauses
test("NEGOTIATE empty", requests.post(f'{BASE}/negotiate', json={'clauses': []}))

# 9. Negotiate with sample clauses
sample_clauses = [{"title": "Non-compete", "risk_level": "CRITICAL", "original_text": "Employee shall not work in any related industry for 5 years worldwide.", "category": "Non-Compete"}]
test("NEGOTIATE with-clauses", requests.post(f'{BASE}/negotiate', json={'clauses': sample_clauses}))

# 10. Analyze with sample contract
with open('sample_contracts/sample_employment.txt', 'rb') as f:
    test("ANALYZE employment.txt", requests.post(f'{BASE}/analyze', files={'file': ('sample_employment.txt', f, 'text/plain')}, data={'email': 'demo@lexguard.ai'}))
