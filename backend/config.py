"""Backend-only configuration loaded from the project-root .env file."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_geoapify_api_key() -> str:
    """Read the key for backend-only provider requests."""
    return os.getenv("GEOAPIFY_API_KEY", "").strip()


def geoapify_key_is_configured() -> bool:
    """Return configuration status without exposing the API key."""
    return bool(get_geoapify_api_key())
