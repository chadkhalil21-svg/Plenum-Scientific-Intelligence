"""Private encrypted browser profile storage in Google Cloud Storage.

This is server-side infrastructure, not a web login endpoint. It must only
be called by trusted back-end code after verifying a user's identity and
authorization for one exact HTTPS origin. NEVER return encrypted or decrypted
browser storage states through model-visible or GitHub tools.
"""
import hashlib
import os
from urllib.parse import urlsplit

from .engine import _origin_syntax
from .session_crypto import PrivateSessionVault


class BrowserProfileStore:
    """Cloud Storage bucket with application-side Fernet encryption and CAS."""

    def __init__(self, *, bucket_name, fernet_key, client=None):
        if not isinstance(bucket_name,str) or not 3 <= len(bucket_name) <= 222:
            raise ValueError("Missing private browser bucket")
        if any(x in bucket_name for x in ("/","\\","?","#")):
            raise ValueError("Invalid browser bucket")
        if not isinstance(fernet_key,(str,bytes)) or not fernet_key:
            raise ValueError("Encryption key required")
        if client is None:
            from google.cloud import storage
            client=storage.Client()
        self.bucket=client.bucket(bucket_name)
        self.vault=PrivateSessionVault(
            fernet_key if isinstance(fernet_key,bytes) else fernet_key.encode()
        )
        self._bucket_verified=False

    def _require_private_bucket(self):
        """Refuse to store credentials in a bucket without explicit privacy controls."""
        if self._bucket_verified:
            return
        self.bucket.reload()
        iam=self.bucket.iam_configuration
        if (getattr(iam,"public_access_prevention",None)!="enforced" or
                getattr(iam,"uniform_bucket_level_access_enabled",False) is not True):
            raise PermissionError("Browser profiles require enforced private bucket access")
        self._bucket_verified=True

    @classmethod
    def from_environment(cls):
        bucket=os.environ.get("BROWSER_PROFILE_BUCKET","")
        key=os.environ.get("BROWSER_SESSION_KEY","")
        if not bucket or not key:
            raise RuntimeError("Private profile storage is not configured")
        return cls(bucket_name=bucket, fernet_key=key)

    @staticmethod
    def _path(owner, origin):
        # Owner identity is provided by the authenticated server, never page text.
        if not isinstance(owner,str) or not 1 <= len(owner) <= 80 or "/" in owner:
            raise PermissionError("Invalid owner identity")
        if not _origin_syntax(origin):
            raise PermissionError("Profile must be bound to one public HTTPS origin")
        o=hashlib.sha256(owner.encode()).hexdigest()
        site=hashlib.sha256(origin.encode()).hexdigest()
        return f"browser-profiles/v1/{o}/{site}.sealed"

    def _blob(self,owner,origin):
        path=self._path(owner,origin)
        self._require_private_bucket()
        return self.bucket.blob(path)

    def save_new(self, *, owner, origin, state, ttl_seconds=3600):
        """Create only. Browser context is never serialized without encryption."""
        blob=self._blob(owner,origin)
        sealed=self.vault.encrypt(state,owner,origin,ttl_seconds=ttl_seconds)
        blob.upload_from_string(sealed,content_type="application/octet-stream",
                                if_generation_match=0)
        return {"stored":True,"new_session":True,"storage_state_returned":False}

    def replace_if_current(self, *, owner, origin, state, expected_generation,
                           ttl_seconds=3600):
        """Optimistic update prevents concurrent login sessions overwriting."""
        if not isinstance(expected_generation,int) or expected_generation<1:
            raise ValueError("Expected storage object generation required")
        blob=self._blob(owner,origin)
        sealed=self.vault.encrypt(state,owner,origin,ttl_seconds=ttl_seconds)
        blob.upload_from_string(sealed,content_type="application/octet-stream",
                                if_generation_match=expected_generation)
        return {"stored":True,"new_session":False,"storage_state_returned":False}

    def load_for_trusted_worker(self, *, owner, origin):
        """ONLY for trusted server-internal Playwright context construction."""
        blob=self._blob(owner,origin)
        blob.reload()
        generation=int(blob.generation)
        sealed=blob.download_as_bytes(if_generation_match=generation)
        state=self.vault.decrypt(sealed,owner,origin)
        return state,generation

    def current_generation(self, *, owner, origin):
        """Metadata-only revision for safe replacement of expired sessions."""
        blob=self._blob(owner,origin)
        if not blob.exists():
            return None
        blob.reload()
        return int(blob.generation)

    def revoke(self, *, owner, origin, expected_generation):
        """Delete only when an independently authorized owner requests logout."""
        if not isinstance(expected_generation,int) or expected_generation<1:
            raise ValueError("Owner-confirmed current generation required")
        blob=self._blob(owner,origin)
        blob.delete(if_generation_match=expected_generation)
        return {"revoked":True}

    def status(self, *, owner, origin):
        """No cookies, tokens, site data, or encrypted blobs returned."""
        blob=self._blob(owner,origin)
        exists=blob.exists()
        return {"profile_exists":bool(exists),
                "note":"Existence does not guarantee a still-valid website login"}
