"""One-time owner-approved encrypted inventory, no website or credential access."""
import json
import re
import secrets
import time

from .owner_chat_pairing import _owner, _store, _cipher
from .sealed_chat_read import require_enabled, parse_recipient, _seal_document, TTL
from .engine import _origin_syntax

APPROVAL_BLOB = "browser-chat-read/v5/owner-inventory-once.sealed"
SCHEMA = "plenum-sealed-owner-inventory-consent-v1"
ACTION = "inventory-read-v1"


def approve_inventory(owner_id, *, recipient_public_key, now=None):
    """Only invoked by the authenticated owner CSRF-protected approval form."""
    require_enabled()
    owner = _owner(owner_id)
    parse_recipient(recipient_public_key)
    t = int(time.time() if now is None else now)
    record = {"schema": SCHEMA, "owner": owner,
              "recipient_public_key": recipient_public_key, "issued": t,
              "expires": t + TTL, "nonce": secrets.token_hex(16)}
    blob = _store().bucket.blob(APPROVAL_BLOB)
    generation = 0
    if blob.exists():
        blob.reload()
        generation = int(blob.generation)
    blob.upload_from_string(
        _cipher().encrypt(json.dumps(record, separators=(",", ":")).encode()),
        content_type="application/octet-stream", if_generation_match=generation)


def consume_inventory(*, now=None):
    """Only after exact GitHub OIDC verification; consume before metadata read."""
    require_enabled()
    t = int(time.time() if now is None else now)
    blob = _store().bucket.blob(APPROVAL_BLOB)
    try:
        blob.reload()
        generation = int(blob.generation)
        record = json.loads(_cipher().decrypt(
            blob.download_as_bytes(if_generation_match=generation), ttl=TTL))
        if (not isinstance(record, dict)
                or set(record) != {"schema", "owner", "recipient_public_key",
                                   "issued", "expires", "nonce"}
                or record["schema"] != SCHEMA
                or type(record["issued"]) is not int
                or type(record["expires"]) is not int
                or not 0 < record["expires"] - record["issued"] <= TTL
                or record["issued"] > t + 10 or record["expires"] <= t
                or not isinstance(record["nonce"], str)
                or re.fullmatch(r"[0-9a-f]{32}", record["nonce"]) is None):
            raise PermissionError("Malformed inventory consent")
        _owner(record["owner"])
        parse_recipient(record["recipient_public_key"])
        blob.delete(if_generation_match=generation)
        return record
    except Exception as exc:
        raise PermissionError("No unconsumed owner inventory consent") from exc


def seal_inventory(record):
    """Reuse existing metadata reader, whitelist fields, never load saved state."""
    from .owner_saved_session import owner_session_metadata
    require_enabled()
    if record.get("schema") != SCHEMA:
        raise PermissionError("Inventory consent schema required")
    owner = _owner(record["owner"])
    metadata = owner_session_metadata(owner)
    rows = metadata.get("sites")
    if not isinstance(rows, list) or len(rows) > 100:
        raise PermissionError("Unbounded inventory")
    result = []
    for row in rows:
        if (not isinstance(row, dict)
                or set(row) != {"origin", "encrypted_profile_exists",
                                "website_login_verified"}
                or not _origin_syntax(row["origin"])
                or (row["encrypted_profile_exists"] is not None
                    and type(row["encrypted_profile_exists"]) is not bool)
                or row["website_login_verified"] is not False):
            raise PermissionError("Unexpected inventory metadata")
        result.append({"origin": row["origin"],
                       "encrypted_profile_exists": row["encrypted_profile_exists"],
                       "website_login_verified": False})
    document = {"schema": "plenum-owner-session-metadata-v1", "sites": result,
                "owner_authentication_required": True,
                "decrypted_storage_exposed": False,
                "session_exists_does_not_prove_active_login": True}
    return _seal_document(record["recipient_public_key"], document)
