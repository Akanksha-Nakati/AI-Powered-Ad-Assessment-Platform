"""Operational entrypoints.

``python -m backend.app.cli index`` builds or refreshes the vector store, which
is what start.sh calls before booting the API.

``python -m backend.app.cli openapi`` writes openapi.json, from which the
frontend regenerates its TypeScript types.

``python -m backend.app.cli models`` lists the Gemini models the configured key
can actually reach. Provider model IDs get retired without warning -- both of
the ones this project originally shipped with now 404 -- so this is the first
thing to check when the pipeline starts failing with a 404.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from backend.app.config import settings
from backend.app.container import build_container
from backend.app.domain.errors import DomainError


async def _index() -> None:
    container = build_container(settings)
    await container.knowledge.ensure_ready()
    print("Vector store ready.")


def _list_models() -> None:
    from google import genai

    client = genai.Client(api_key=settings.google_api_key)
    configured = {settings.gemini_model, settings.gemini_embedding_model}

    rows: list[tuple[str, str, str]] = []
    for model in client.models.list():
        actions = set(getattr(model, "supported_actions", None) or ())
        if not model.name or not actions & {"generateContent", "embedContent"}:
            continue
        kind = "embed" if "embedContent" in actions else "generate"
        short = model.name.removeprefix("models/")
        marker = "*" if model.name in configured or short in configured else " "
        rows.append((marker, kind, short))

    for marker, kind, name in sorted(rows, key=lambda r: (r[1], r[2])):
        print(f"{marker} {kind:9s} {name}")
    print("\n* = currently configured")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="backend.app.cli")
    parser.add_argument("command", choices=["index", "openapi", "models"])
    parser.add_argument(
        "--out", default="openapi.json", help="output path for the openapi command"
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "index":
            asyncio.run(_index())
        elif args.command == "models":
            _list_models()
        elif args.command == "openapi":
            from backend.app.openapi_export import export

            print(f"Wrote {export(Path(args.out))}")
    except DomainError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
