"""Short-lived signed handles for Delta Sharing file downloads (ADR-0015).

The Delta Sharing protocol expects every ``file.url`` in a query
response to be a pre-signed URL the recipient can ``GET`` without the
bearer token — on cloud deployments that is an S3/ABFSS pre-signed
URL. soyuz' tables are ``file://``-backed, so soyuz serves the bytes
itself and this module is the "pre-signing": an HMAC-SHA256 over the
absolute file path, the public file id, and an expiry timestamp,
keyed by a server-side secret. The handle is stateless — no DB row
per download — which matches the cloud pre-signed-URL model exactly:
possession of an unexpired handle *is* the authorisation.

The signature binds the path **and** the file id so a handle for one
file cannot be replayed against another download URL, and the expiry
lives inside the signed payload so it cannot be extended client-side.
Tampering with any byte of the payload invalidates the signature, so
path traversal through a hand-edited handle is structurally
impossible — the path inside a verified handle is exactly the path
the server signed.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path

from soyuz_catalog.exceptions import SharingProtocolError
from soyuz_catalog.settings import get_settings

_EPHEMERAL_KEY: bytes = secrets.token_bytes(32)
"""Per-process fallback signing key.

Used when ``Settings.sharing_signing_key`` is empty. Generated once at
import time so every handle signed by this process verifies for the
process lifetime; a restart invalidates in-flight handles, which is an
acceptable cost for the zero-config single-process default. See the
settings docstring for the multi-replica caveat.
"""


def _signing_key() -> bytes:
    """Resolve the active HMAC key.

    A configured ``sharing_signing_key`` is stretched through SHA-256
    so operators can use any passphrase-like string without weakening
    the HMAC key length; the empty default falls back to the
    per-process random key.

    Returns:
        bytes: 32-byte HMAC key.
    """
    configured = get_settings().sharing_signing_key
    if configured:
        return hashlib.sha256(configured.encode("utf-8")).digest()
    return _EPHEMERAL_KEY


def _sign(payload_b64: str) -> str:
    """Compute the hex HMAC-SHA256 signature of an encoded payload.

    Args:
        payload_b64: The base64url-encoded payload half of a handle.

    Returns:
        str: 64-char lowercase hex signature.
    """
    return hmac.new(_signing_key(), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()


def sign_file_handle(path: Path, file_id: str, expires_at_ms: int) -> str:
    """Build a signed download handle for one parquet file.

    The handle is ``base64url(json({"p", "f", "e"})) + "." + hmac`` —
    the same envelope-then-signature layout as a JWS, minus the
    header, because there is exactly one algorithm and one issuer.

    Args:
        path: Absolute filesystem path of the file to serve. The
            caller has already resolved it under the table root.
        file_id: Public file id the handle is bound to (the path
            segment of the download URL).
        expires_at_ms: Epoch-millisecond expiry baked into the
            signature.

    Returns:
        str: The opaque handle for the ``token`` query parameter.
    """
    payload = json.dumps(
        {"p": str(path), "f": file_id, "e": expires_at_ms},
        separators=(",", ":"),
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=").decode("ascii")
    return f"{payload_b64}.{_sign(payload_b64)}"


def verify_file_handle(token: str, file_id: str) -> Path:
    """Validate a download handle and return the path it authorises.

    Every failure mode — malformed token, bad signature, id mismatch,
    expiry — maps to the same 403 so a probing client learns nothing
    about *which* check failed. The signature is verified before the
    payload is even parsed, so no attacker-controlled bytes reach
    ``json.loads`` unauthenticated.

    Args:
        token: The handle from the ``token`` query parameter.
        file_id: The file id from the URL path, which must match the
            id baked into the signature.

    Returns:
        Path: The absolute path the server signed.

    Raises:
        SharingProtocolError: 403 ``PERMISSION_DENIED`` on any
            validation failure.
    """
    denied = SharingProtocolError(403, "PERMISSION_DENIED", "invalid or expired file token")
    parts = token.rsplit(".", 1)
    if len(parts) != 2:
        raise denied
    payload_b64, signature = parts
    if not hmac.compare_digest(signature, _sign(payload_b64)):
        raise denied
    try:
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise denied from exc
    if not isinstance(payload, dict) or payload.get("f") != file_id:
        raise denied
    expires_at_ms = payload.get("e")
    if not isinstance(expires_at_ms, int) or expires_at_ms < int(time.time() * 1000):
        raise denied
    path = payload.get("p")
    if not isinstance(path, str) or not path:
        raise denied
    return Path(path)
