"""Encryption at rest for warehouse connection secrets.

A connection URI is a live external credential (e.g. a Postgres password),
stored in this app's own SQLite file -- a different, larger threat than the
Gemini/Claude keys in .env, which are never entered through the running app.
Fernet symmetric encryption, keyed by Settings.warehouse_encryption_key,
raises the bar on the most likely real leak path: the database file itself
being copied, committed, or read by someone debugging an unrelated issue.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from backend.app.domain.errors import ConfigurationError


def encrypt_secret(plaintext: str, key: str) -> str:
    return _fernet(key).encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str, key: str) -> str:
    try:
        return _fernet(key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        # Only reachable if warehouse_encryption_key changed after data was
        # written -- not a user-facing condition, so this stays a
        # ConfigurationError rather than a new error type.
        raise ConfigurationError(
            "could not decrypt a stored connection secret -- has "
            "warehouse_encryption_key changed since it was saved?"
        ) from exc


def _fernet(key: str) -> Fernet:
    if not key:
        raise ConfigurationError(
            "warehouse_encryption_key is required to store a data source "
            "connection. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise ConfigurationError(
            "warehouse_encryption_key is not a valid Fernet key"
        ) from exc
