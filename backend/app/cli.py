"""Operational entrypoints.

``python -m backend.app.cli index`` builds or refreshes the vector store, which
is what start.sh calls before booting the API. Replaces the old
backend/setup_vectorstore.py.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

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
    parser.add_argument("command", choices=["index"])
    args = parser.parse_args(argv)

    try:
        if args.command == "index":
            asyncio.run(_index())
    except DomainError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
