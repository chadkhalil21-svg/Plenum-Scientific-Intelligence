"""Match an owner-signed plan to *exactly* the existing Playwright action API.

This is a secure adapter, not an alternate browser/agent framework or a
remote browser endpoint. A trusted owner UI may issue a grant; a separate
private browser worker must enforce network isolation, session binding and
approved origins *before* executing returned BrowserStep values.

The older grant schema includes future actions (navigate/delete/download/
submit) that the existing executor cannot perform. They are intentionally
refused instead of being silently reinterpreted.
"""
from dataclasses import dataclass
from collections.abc import Collection

from .browser_actions import BrowserStep, validate_steps
from .owner_approval import _origin, OwnerApprovalGate


class UnsupportedOwnerAction(PermissionError):
    """Signed plan cannot be executed faithfully by the existing browser."""


@dataclass(frozen=True)
class ApprovedBrowserActionPlan:
    origin: str
    steps: tuple[BrowserStep, ...]


_STEP_FIELDS = {
    "fill": frozenset({"op", "selector", "value"}),
    "select": frozenset({"op", "selector", "value"}),
    "click": frozenset({"op", "selector"}),
    "upload": frozenset({"op", "selector", "file_id"}),
}


def compile_exact_steps(plan: dict, *, allowed_origins: Collection[str]) -> ApprovedBrowserActionPlan:
    """Reject malformed, different-origin or unimplemented operations *first*.

    No site visit or grant consumption occurs here. In particular, do not
    translate submit/delete/navigation/download into a click or another
    operation with different side effects.
    """
    if not isinstance(plan, dict) or set(plan) != {"origin", "operations"}:
        raise UnsupportedOwnerAction("Exact owner action plan is required")
    if (not isinstance(allowed_origins, (frozenset, set, tuple, list))
            or not allowed_origins
            or any(not isinstance(v, str) for v in allowed_origins)):
        raise UnsupportedOwnerAction("Trusted origin allowlist required")
    try:
        origin = _origin(plan["origin"])
    except (ValueError, PermissionError, TypeError) as exc:
        raise UnsupportedOwnerAction("Unsafe website origin") from exc
    if origin not in allowed_origins:
        raise UnsupportedOwnerAction("Owner plan origin not separately authorized")
    operations = plan["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 16:
        raise UnsupportedOwnerAction("Owner action plan must have 1 to 16 steps")
    compiled = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise UnsupportedOwnerAction("Invalid operation")
        kind = operation.get("op")
        expected = _STEP_FIELDS.get(kind) if isinstance(kind, str) else None
        if expected is None or set(operation) != expected:
            raise UnsupportedOwnerAction("Operation unsupported or unexpected fields")
        selector = operation.get("selector")
        if not isinstance(selector, str):
            raise UnsupportedOwnerAction("Selector must be text")
        if kind in ("fill", "select"):
            value = operation.get("value")
            if not isinstance(value, str):
                raise UnsupportedOwnerAction("Form values must be text")
            step = BrowserStep(kind, selector, value)
        elif kind == "upload":
            file_id = operation.get("file_id")
            if not isinstance(file_id, str):
                raise UnsupportedOwnerAction("Preapproved upload identifier required")
            step = BrowserStep(kind, selector, file_id=file_id)
        else:
            step = BrowserStep(kind, selector)
        compiled.append(step)
    try:
        validate_steps(compiled)
    except (ValueError, PermissionError, TypeError) as exc:
        raise UnsupportedOwnerAction("Browser executor rejected plan") from exc
    return ApprovedBrowserActionPlan(origin, tuple(compiled))


def authorize_exact_steps(*, gate: OwnerApprovalGate, token: str,
                          verified_owner_id: str, plan: dict,
                          allowed_origins: Collection[str]) -> ApprovedBrowserActionPlan:
    """Bind an executable plan to the original single-use HMAC/CAS grant.

    All static schema and origin validation occurs BEFORE consuming a grant.
    Calling this function alone does not grant website network permissions.
    The returned result MUST remain inside a trusted private browser worker.
    """
    compiled = compile_exact_steps(plan, allowed_origins=allowed_origins)
    gate.consume(token=token, verified_owner_id=verified_owner_id, plan=plan)
    return compiled
