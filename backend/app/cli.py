"""Operational entrypoints.

``python -m backend.app.cli index`` builds or refreshes the vector store, which
is what start.sh calls before booting the API.

``python -m backend.app.cli openapi`` writes openapi.json, from which the
frontend regenerates its TypeScript types.
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


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="backend.app.cli")
    parser.add_argument("command", choices=["index", "openapi"])
    parser.add_argument(
        "--out", default="openapi.json", help="output path for the openapi command"
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "index":
            asyncio.run(_index())
        elif args.command == "openapi":
            from backend.app.openapi_export import export

            print(f"Wrote {export(Path(args.out))}")
    except DomainError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
