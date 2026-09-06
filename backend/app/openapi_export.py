"""Dump the OpenAPI schema to a file.

The frontend's TypeScript types are generated from this, so the API contract
has exactly one definition. Run via ``python -m backend.app.cli openapi``.
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import Settings
from backend.app.main import create_app


def export(destination: Path) -> Path:
    # Placeholder credentials: building the schema only needs the routes, and
    # requiring real keys to regenerate types would be a poor developer
    # experience (and would break CI).
    app = create_app(
        Settings(google_api_key="schema-export", anthropic_api_key="schema-export")
    )
    destination.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    return destination
