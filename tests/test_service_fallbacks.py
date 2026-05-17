"""Additional service tests for fallback and utility behavior."""

from datetime import datetime, timezone, timedelta
import sys
import types

from bson import ObjectId

from backend.services import (
    clause_extractor,
    document_parser,
    gemini_service,
    mongodb_service,
    risk_scorer,
    translate_service,
    tts_service,
)
from backend.utils.constants import DOCX_MAGIC, PDF_MAGIC
from backend.utils.sanitizer import (
    sanitize_chat_message,
    sanitize_dict_strings,
    sanitize_search_query,
)


class _FakeCursor(list):
    def sort(self, key, direction):
        reverse = direction < 0
        return _FakeCursor(sorted(self, key=lambda item: item.get(key), reverse=reverse))

    def limit(self, count):
        return _FakeCursor(self[:count])


class _FakeCollection:
    def __init__(self):
        self.docs = []
        self.indexes = []

    def create_index(self, *args, **kwargs):
        self.indexes.append((args, kwargs))

    def insert_one(self, doc):
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return type("InsertResult", (), {"inserted_id": stored["_id"]})()

    def update_one(self, filter_doc, update_doc, upsert=False):
        for doc in self.docs:
            if doc.get("doc_hash") == filter_doc.get("doc_hash"):
                doc.update(update_doc.get("$set", {}))
                return type("UpdateResult", (), {})()
        if upsert:
            self.docs.append(dict(update_doc.get("$set", {})))
        return type("UpdateResult", (), {})()

    def find_one(self, filter_doc, projection=None):
        for doc in self.docs:
            matches = True
            for key, value in filter_doc.items():
                if key == "_id":
                    matches = str(doc.get("_id")) == str(value)
                else:
                    matches = doc.get(key) == value
                if not matches:
                    break
            if matches:
                result = dict(doc)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                if projection:
                    for key, include in projection.items():
                        if include == 0:
                            result.pop(key, None)
                return result
        return None

    def find(self, filter_doc, projection=None):
        results = []
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in filter_doc.items()):
                result = dict(doc)
                if projection:
                    for key, include in projection.items():
                        if include == 0:
                            result.pop(key, None)
                results.append(result)
        return _FakeCursor(results)


class _FakeDatabase:
    def __init__(self):
        self.collections = {
            "analyses": _FakeCollection(),
            "chat_history": _FakeCollection(),
            "users": _FakeCollection(),
        }

    def __getitem__(self, name):
        return self.collections[name]


class _FakeClient:
    def __init__(self):
        self.admin = type("Admin", (), {"command": staticmethod(lambda *_args, **_kwargs: True)})()
        self.database = _FakeDatabase()

    def __getitem__(self, name):
        return self.database


def test_sanitizer_nested_structures():
    assert sanitize_chat_message("  <b>Hello</b> contract  ") == "Hello contract"
    assert sanitize_search_query("  confidentiality clause  ") == "confidentiality clause"

    payload = {
        "name": "<script>alert(1)</script>Bob",
        "nested": {"note": "<i>safe</i>"},
        "items": ["<u>x</u>", {"deep": "<img src=x onerror=1>"}],
    }
    cleaned = sanitize_dict_strings(payload)
    assert cleaned["name"].startswith("alert") or cleaned["name"] == "Bob"
    assert cleaned["nested"]["note"] == "safe"
    assert cleaned["items"][0] == "x"


def test_document_parser_docx_pdf_and_ocr(monkeypatch):
    fake_docx = types.SimpleNamespace()

    class _FakeParagraph:
        def __init__(self, text):
            self.text = text

    class _FakeDocument:
        def __init__(self, _stream):
            self.paragraphs = [_FakeParagraph("DOCX contract text")]

    fake_docx.Document = _FakeDocument
    monkeypatch.setitem(sys.modules, "docx", fake_docx)

    docx_result = document_parser.parse_document(DOCX_MAGIC + b"docx-bytes", "sample.docx")
    assert docx_result["file_type"] == "docx"
    assert "DOCX contract text" in docx_result["text"]

    class _FakePdfPage:
        def __init__(self, text):
            self._text = text

        def get_text(self, _kind):
            return self._text

        def get_pixmap(self, dpi=300):
            return types.SimpleNamespace(width=1, height=1, samples=b"\x00\x00\x00")

    class _FakePdfDoc:
        def __init__(self, pages):
            self.page_count = len(pages)
            self._pages = pages

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __iter__(self):
            return iter(self._pages)

    fake_fitz = types.SimpleNamespace(
        open=lambda stream=None, filetype=None: _FakePdfDoc([_FakePdfPage("PDF contract text"), _FakePdfPage("")])
    )
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)
    monkeypatch.setattr(document_parser, "_ocr_page", lambda _page: "OCR contract text")

    pdf_result = document_parser.parse_document(PDF_MAGIC + b"pdf-bytes", "sample.pdf")
    assert pdf_result["file_type"] == "pdf"
    assert "PDF contract text" in pdf_result["text"]
    assert "OCR contract text" in pdf_result["text"]

    blank_page = _FakePdfPage("")
    assert document_parser._ocr_page(blank_page) == "OCR contract text"


def test_document_parser_text_and_error_branches():
    txt_result = document_parser.parse_document(b"Line one\nLine two", "sample.txt")
    assert txt_result["file_type"] == "txt"
    assert txt_result["page_count"] == 2

    try:
        document_parser.parse_document(PDF_MAGIC + b"bad", "sample.exe")
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)

    try:
        document_parser.parse_document(b"plain", "sample.exe")
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)


def test_translate_service_google_cache_and_fallback(monkeypatch):
    monkeypatch.setattr(translate_service, "_google_translate_api_key", "fake-key")
    monkeypatch.setattr(translate_service, "_mymemory_email", "tester@example.com")

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"translations": [{"translatedText": "हैलो"}]}}

    monkeypatch.setattr(translate_service.requests, "post", lambda *args, **kwargs: _Response())
    first = translate_service.translate_text("Hello", "hi")
    second = translate_service.translate_text("Hello", "hi")
    assert first["translated_text"] == "हैलो"
    assert second["source"] == "cache"

    monkeypatch.setattr(translate_service, "_google_translate_api_key", "")
    class _FallbackResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"responseData": {"translatedText": "Hola"}}

    monkeypatch.setattr(translate_service.requests, "get", lambda *args, **kwargs: _FallbackResponse())
    fallback = translate_service.translate_text("Hello", "es")
    assert fallback["success"] is True
    assert fallback["source"] == "mymemory"

    monkeypatch.setattr(translate_service.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    failed = translate_service.translate_text("Hello", "fr")
    assert failed["success"] is False


def test_tts_service_google_and_fallback(monkeypatch):
    monkeypatch.setattr(tts_service, "_google_tts_api_key", "fake-key")

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"audioContent": "AAAA"}

    monkeypatch.setattr(tts_service.requests, "post", lambda *args, **kwargs: _Response())
    result = tts_service.synthesize_speech("Hello there", "en-US", "en-US-Neural2-D")
    assert result["source"] == "google"
    assert result["audio_base64"] == "AAAA"

    monkeypatch.setattr(tts_service, "_google_tts_api_key", "")
    fallback = tts_service.synthesize_speech("Hello there", "en-US", "en-US-Neural2-D")
    assert fallback["source"] == "web_speech_api"
    assert fallback["success"] is False


def test_mongodb_service_crud_and_health(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr(mongodb_service, "_client", fake_client)
    monkeypatch.setattr(mongodb_service, "_db_name", "lexguard")

    mongodb_service.upsert_user("user@example.com")
    analysis_id = mongodb_service.save_analysis(
        user_email="user@example.com",
        filename="contract.txt",
        doc_hash="abc123",
        risk_score=77,
        clauses=[{"risk_level": "HIGH", "risk_score": 77}],
        summary="Summary",
        raw_text_snippet="snippet",
        contract_type="Employment Agreement",
    )

    assert isinstance(analysis_id, str)
    assert mongodb_service.health_check() is True
    assert mongodb_service.compute_doc_hash("hello") == mongodb_service.compute_doc_hash("hello")
    assert mongodb_service.get_analysis_by_hash("abc123")["filename"] == "contract.txt"
    assert mongodb_service.get_user_history("user@example.com")

    existing = mongodb_service.get_analysis_by_hash("abc123")
    assert existing["risk_score"] == 77

    assert mongodb_service.get_analysis_by_id("not-an-id") is None
    assert mongodb_service.get_analysis_by_hash("missing") is None

    mongo_id = ObjectId()
    fake_client.database.collections["analyses"].docs.append(
        {
            "_id": mongo_id,
            "user_email": "user@example.com",
            "filename": "contract.txt",
            "doc_hash": "def456",
            "risk_score": 66,
            "contract_type": "Employment Agreement",
            "clause_count": 1,
            "clauses": [],
            "summary": "Another summary",
            "raw_text_snippet": "snippet",
            "created_at": datetime.now(timezone.utc),
        }
    )
    by_id = mongodb_service.get_analysis_by_id(str(mongo_id))
    assert by_id["filename"] == "contract.txt"

    fake_client.database.collections["chat_history"].docs.extend(
        [
            {
                "session_id": "session-1",
                "role": "user",
                "content": "Hello",
                "created_at": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            {
                "session_id": "session-1",
                "role": "assistant",
                "content": "Hi",
                "created_at": datetime.now(timezone.utc),
            },
        ]
    )
    history = mongodb_service.get_chat_history("session-1")
    assert [message["role"] for message in history] == ["user", "assistant"]
    mongodb_service.save_chat_message("session-1", "assistant", "Follow-up")
    assert len(fake_client.database.collections["chat_history"].docs) == 3

    mongodb_service.upsert_user("user@example.com")
    assert mongodb_service.health_check() is True


def test_clause_extractor_fallback_and_similarity(monkeypatch):
    monkeypatch.setattr(
        clause_extractor.gemini_service,
        "analyze_contract_full",
        lambda text: {
            "overall_score": 60,
            "overall_risk_score": 60,
            "risk_level": "HIGH",
            "contract_type": "Employment Agreement",
            "summary": "Summary",
            "clauses": [
                {"original_text": "Non-compete language", "title": "Non-compete", "risk_level": "HIGH", "risk_score": 75},
                {"original_text": "Indemnification language", "title": "Indemnification", "risk_level": "CRITICAL", "risk_score": 90},
            ],
            "negotiation_priorities": ["Priority"],
            "red_flags": ["Flag"],
        },
    )
    monkeypatch.setattr(clause_extractor.embedding_service, "compute_clause_similarities", lambda clauses: (_ for _ in ()).throw(RuntimeError("no embedder")))
    monkeypatch.setattr(clause_extractor.gemini_service, "generate_negotiation_recommendations", lambda clauses: (_ for _ in ()).throw(RuntimeError("no gemini")))
    result = clause_extractor.run_full_extraction_pipeline("Sample contract text")
    assert result["overall_risk_score"] == 60
    assert result["clauses"][0]["similarity_score"] == 0.5
    assert result["negotiation_recommendations"] == []


def test_gemini_service_local_fallbacks():
    analysis = gemini_service._fallback_analysis(
        "EMPLOYMENT AGREEMENT\n4. NON-COMPETE Employee shall not compete for 2 years."
    )
    assert analysis["overall_score"] > 0
    assert analysis["clauses"]
    assert gemini_service._fallback_glossary("indemnification")["term"] == "indemnification"
    assert "biggest risks" in gemini_service._fallback_chat("non-compete", "", [], "What are the risks?").lower()
    comparison = gemini_service._fallback_compare("A non-compete clause", "A confidentiality clause")
    assert comparison["differences"]
    assert risk_scorer.score_to_level(90) == "CRITICAL"