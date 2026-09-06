"""Content-addressed local blob store -- implements the BlobStore port.

Files are named by the sha256 of their contents and sharded two levels deep, so
uploading the same creative twice costs one copy and no directory ends up with
tens of thousands of entries. Swapping this for S3 is a new class satisfying the
same port; nothing upstream changes.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

#: Written alongside each blob so the media type survives a restart.
_MEDIA_TYPE_SUFFIX = ".type"


def digest_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path_for(self, digest: str) -> Path:
        return self._root / digest[:2] / digest[2:4] / digest

    async def put(self, data: bytes, media_type: str) -> str:
        digest = digest_of(data)
        await asyncio.to_thread(self._write, digest, data, media_type)
        return digest

    def _write(self, digest: str, data: bytes, media_type: str) -> None:
        path = self._path_for(digest)
        if path.exists():
            return  # Same content, same bytes. Nothing to do.
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp name and rename, so a crash mid-write cannot leave a
        # truncated file sitting at a digest that claims to be complete.
        tmp = path.with_suffix(".partial")
        tmp.write_bytes(data)
        tmp.replace(path)
        path.with_suffix(_MEDIA_TYPE_SUFFIX).write_text(media_type)

    async def get(self, digest: str) -> bytes | None:
        return await asyncio.to_thread(self._read, digest)

    def _read(self, digest: str) -> bytes | None:
        path = self._path_for(digest)
        return path.read_bytes() if path.exists() else None

    async def media_type_of(self, digest: str) -> str | None:
        path = self._path_for(digest).with_suffix(_MEDIA_TYPE_SUFFIX)
        return await asyncio.to_thread(
            lambda: path.read_text() if path.exists() else None
        )
