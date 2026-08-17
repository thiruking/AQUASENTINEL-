"""Writes the public backend URL into the static Vercel build."""
import json
import os
from pathlib import Path

api_url = os.environ.get("AQUASENTINEL_API_URL", "").strip().rstrip("/")
Path("runtime-config.js").write_text(
    "// Generated at build time. Do not store secrets here.\n"
    f"window.AQUASENTINEL_API_URL = {json.dumps(api_url)};\n",
    encoding="utf-8",
)
