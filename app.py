"""Root-level WSGI shim for deployment platforms that import `app:app`."""

from backend.app import create_app

app = create_app()

