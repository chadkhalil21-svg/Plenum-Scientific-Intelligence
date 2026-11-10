"""Owner-verified private browser admission: static origin or active encrypted grant.

Use the original Playwright/browser worker. A runtime-granted origin is allowed
ONLY through the existing pinned-IP single-origin CONNECT proxy; it does not
authorize cross-site SSO, general ChatGPT actions, or unrestricted website writes.
"""
from urllib.parse import urlsplit

from .engine import safe_url
from .runtime_site_grants import enabled, normalize_origin, OwnerSiteGrantStore


def owner_live_origin(*, owner_id: str, site: str) -> tuple[str, bool]:
    """Return (canonical_origin, must_use_pinned_proxy), fail closed.

    The caller must already have verified the owner identity. Site registration
    is not an authorization for another owner or a model/GitHub request.
    """
    if not isinstance(owner_id, str) or not owner_id or not isinstance(site, str):
        raise PermissionError("Verified owner and website are required")
    try:
        parsed = urlsplit(site)
        if parsed.port is not None or not parsed.hostname:
            raise PermissionError("Only canonical public HTTPS website origins")
        origin = normalize_origin("https://" + parsed.hostname)
    except (ValueError, TypeError) as exc:
        raise PermissionError("Invalid website address") from exc
    if not safe_url(site, origins={origin}):
        raise PermissionError("Unsafe website URL")
    if safe_url(site):
        return origin, False  # Existing deployment behavior remains unchanged.
    if not enabled():
        raise PermissionError("Private website registration is unavailable")
    if not OwnerSiteGrantStore.from_environment().authorized(
            owner=owner_id, origin=origin):
        raise PermissionError("Website not approved for this owner")
    return origin, True
