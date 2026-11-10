"""Bounded adaptive coordinator for the EXISTING owner-controlled Playwright page.

This file deliberately neither opens a browser nor loads credentials nor grants
website permissions. The PRIVATE authenticated owner runtime supplies a restored
page, exact authorized origins, trusted observation/decision/outcome callbacks,
and a per-action consent callback. Page content is untrusted; model suggestions
may never be used as grants. The only executor is the existing browser_actions.
No network endpoint, model provider, vault, or background worker is created here.
"""
from __future__ import annotations

import inspect

from .browser_actions import BrowserStep, execute_steps_on_page, validate_steps
from .engine import safe_url

MAX_ACTIONS = 12
MAX_REPLANS = 2


async def _call(function, *args):
    result = function(*args)
    return await result if inspect.isawaitable(result) else result


def _result(status: str, *, executed: int, replans: int, checks: int) -> dict:
    """Only bounded outcome counters leave this layer, never page content."""
    return {
        "schema": "plenum-owner-browser-adaptive-loop-v1",
        "status": status,
        "executed_steps": executed,
        "safe_locator_replans": replans,
        "trusted_verifier_calls": checks,
        "owner_consent_supplied_by_caller": True,
        "remote_site_or_login_verified_by_this_adapter": False,
        "private_page_text_or_credentials_returned": False,
        "automatic_write_retries": False,
    }


async def execute_owner_adaptive_loop(
    page, *,
    authorized_origins,
    observe,
    decide,
    consent,
    verify,
    max_actions: int = 6,
    upload_root=None,
    progress=None,
    confirm_step=None,
    recover_observation=None,
) -> dict:
    """Execute approved steps selected from fresh page observations.

    Callbacks live ONLY in a trusted, authenticated private coordinator:
      observe(page) -> PRIVATE observation, never emitted here;
      decide(observation, feedback) -> one BrowserStep or None;
      consent(step) -> EXACT boolean True only after checking original owner
                       grant, origin, action, target and side-effect policy;
      verify(page) -> EXACT boolean True only after independent final readback;
      confirm_step(page,step) -> optional EXACT boolean that the PRECEDING
                         already-executed action reached its expected state;
      recover_observation(page,feedback) -> optional EXACT boolean requesting
                         another passive observation, never a new website action;
      progress(redacted_event) -> optional owner-only status event.

    Missing locators are safe to reconsider BEFORE consent and BEFORE action.
    An ambiguous locator blocks immediately. Once an action is attempted,
    ANY exception stops the loop without a replay: clicks may have caused
    irreversible effects even if Playwright reported an error. The caller must
    enforce origin-pinned egress, per-site identity, policy, and secret handling.
    """
    if (not isinstance(authorized_origins, (set, frozenset, list, tuple))
            or not authorized_origins
            or not all(isinstance(x, str) for x in authorized_origins)
            or not all(callable(x) for x in (observe, decide, consent, verify))
            or (progress is not None and not callable(progress))
            or (confirm_step is not None and not callable(confirm_step))
            or (recover_observation is not None and not callable(recover_observation))
            or type(max_actions) is not int or not 1 <= max_actions <= MAX_ACTIONS):
        raise ValueError("Trusted owner task callbacks and bounded origins required")
    if not safe_url(page.url, origins=authorized_origins):
        raise PermissionError("Page is outside exact owner-approved origins")
    executed = replans = checks = 0
    feedback = "start"

    async def event(name, number):
        if progress is not None:
            # Do not disclose title, URL, DOM, selector, values or exceptions.
            await _call(progress, {"state": name, "step": number})

    for _attempt in range(max_actions + MAX_REPLANS):
        if not safe_url(page.url, origins=authorized_origins):
            raise PermissionError("Browser left owner-approved origin")
        if executed >= max_actions:
            break
        observation = await _call(observe, page)
        step = await _call(decide, observation, feedback)
        if step is None:
            checks += 1
            verified = await _call(verify, page)
            if type(verified) is not bool:
                raise PermissionError("Trusted outcome verifier must return boolean")
            if verified:
                await event("CALLER_VERIFIED", executed)
                return _result("CALLER_VERIFIED",
                               executed=executed, replans=replans, checks=checks)
            # A missing *observation* may recover without replaying a click.
            # The callback may only wait/inspect the already-authorized page.
            if recover_observation is not None and replans < MAX_REPLANS:
                if not safe_url(page.url, origins=authorized_origins):
                    raise PermissionError("Page left the approved origin")
                refreshed = await _call(recover_observation, page, feedback)
                if type(refreshed) is not bool:
                    raise PermissionError("Trusted passive recovery must return boolean")
                if refreshed:
                    replans += 1
                    feedback = "observation_stale"
                    await event("REOBSERVE_WITHOUT_ACTION", executed)
                    continue
            await event("BLOCKED_NO_NEXT_STEP", executed)
            return _result("BLOCKED_NO_NEXT_STEP",
                           executed=executed, replans=replans, checks=checks)
        validate_steps([step])
        if step.operation != "snapshot":
            # A pre-action missing locator is safe to re-observe and re-plan.
            # Never retry an action after a timeout/uncertain side effect.
            try:
                matches = await page.locator(step.selector).count()
            except Exception:
                await event("BLOCKED_LOCATOR_INSPECTION", executed)
                return _result("BLOCKED_LOCATOR_INSPECTION",
                               executed=executed, replans=replans, checks=checks)
            if matches != 1:
                if matches == 0 and replans < MAX_REPLANS:
                    replans += 1
                    feedback = "locator_missing"
                    await event("REPLAN_NO_ACTION_TAKEN", executed)
                    continue
                await event("BLOCKED_AMBIGUOUS_OR_MISSING_LOCATOR", executed)
                return _result("BLOCKED_AMBIGUOUS_OR_MISSING_LOCATOR",
                               executed=executed, replans=replans, checks=checks)
        # No candidate is executed from model/page instructions alone.
        # The trusted coordinator MUST validate an original owner grant.
        allowed = await _call(consent, step)
        if type(allowed) is not bool or not allowed:
            raise PermissionError("Owner-approved per-action grant missing")
        if not safe_url(page.url, origins=authorized_origins):
            raise PermissionError("Origin changed before approved action")
        await event("ACTION_APPROVED", executed)
        try:
            await execute_steps_on_page(
                page, [step], authorized_origins=authorized_origins,
                upload_root=upload_root,
            )
        except Exception:
            await event("BLOCKED_UNCERTAIN_ACTION_NO_RETRY", executed)
            return _result("BLOCKED_UNCERTAIN_ACTION_NO_RETRY",
                           executed=executed, replans=replans, checks=checks)
        executed += 1
        feedback = "step_complete"
        await event("ACTION_COMPLETE", executed)
        # Never repeat a prior click merely because the website's response
        # is not yet observed. An independent per-step readback is required
        # before the coordinator may choose another action.
        if confirm_step is not None:
            checks += 1
            confirmed = await _call(confirm_step, page, step)
            if type(confirmed) is not bool:
                raise PermissionError("Trusted step confirmation must return boolean")
            if not confirmed:
                await event("BLOCKED_POST_ACTION_UNVERIFIED_NO_RETRY", executed)
                return _result("BLOCKED_POST_ACTION_UNVERIFIED_NO_RETRY",
                               executed=executed, replans=replans, checks=checks)
        checks += 1
        verified = await _call(verify, page)
        if type(verified) is not bool:
            raise PermissionError("Trusted outcome verifier must return boolean")
        if verified:
            await event("CALLER_VERIFIED", executed)
            return _result("CALLER_VERIFIED",
                           executed=executed, replans=replans, checks=checks)
    await event("BLOCKED_ACTION_BUDGET", executed)
    return _result("BLOCKED_ACTION_BUDGET",
                   executed=executed, replans=replans, checks=checks)
