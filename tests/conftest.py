import os

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Provide safe defaults so settings import works without a real .env."""
    monkeypatch.setenv("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", "test-groq"))
    monkeypatch.setenv("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "test-gemini"))
    monkeypatch.setenv(
        "ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "test-anthropic")
    )
