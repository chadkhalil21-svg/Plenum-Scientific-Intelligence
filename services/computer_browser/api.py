"""Private authenticated API for an on-demand headless browser worker.

Cloud Run IAM stays ON. This second bearer check is defense in depth, and is
not a replacement for an OAuth2/MCP connector. No live site-changing actions
are available until the owner approval/session-vault service is built.
"""
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .engine import allowed_origins, safe_url, read_public, local_interaction_smoke

app = FastAPI(title="Plenum Computer Browser", docs_url=None, redoc_url=None, openapi_url=None)

def auth(authorization: str | None = Header(default=None)):
    key = os.environ.get("COMPUTER_BROWSER_TOKEN", "")
    candidate = authorization.removeprefix("Bearer ") if authorization else ""
    if (not key or len(key) < 32 or not authorization
            or not authorization.startswith("Bearer ")
            or not hmac.compare_digest(candidate.encode(), key.encode())):
        raise HTTPException(status_code=401, detail="Authenticated service access required")
    return True

class BrowserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=9, max_length=1200)

class PlannedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(min_length=3, max_length=28)
    selector: str | None = Field(default=None, max_length=240)

class BrowserPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=9, max_length=1200)
    actions: list[PlannedAction] = Field(default_factory=list, max_length=20)

@app.get("/health")
@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"service": "plenum-computer-browser", "ready": True,
            "browser_profile_persistence": False, "remote_mutations_enabled": False}

# IAM-only machine smoke route. It intentionally has no application bearer token
# because Cloud Run already authenticates one exact service-level Invoker identity.
# It MUST be disabled on the original owner/IAP service, and may only read a
# fixed public fixture with no site cookies or browser-side writes.
@app.post("/machine/v1/public-read")
async def machine_public_read(task: BrowserRequest):
    if (os.environ.get("MACHINE_IAM_PUBLIC_READ") != "true"
            or os.environ.get("K_SERVICE") != "plenum-computer-browser-machine"
            or os.environ.get("COMPUTER_BROWSER_TOKEN")
            or os.environ.get("BROWSER_SESSION_KEY")
            or os.environ.get("BROWSER_PROFILE_BUCKET")):
        raise HTTPException(status_code=404, detail="Machine public read unavailable")
    if (os.environ.get("BROWSER_ALLOWED_ORIGINS") != "https://example.com"
            or task.url not in ("https://example.com", "https://example.com/")):
        raise HTTPException(status_code=403, detail="Only the public smoke origin is approved")
    try:
        result = await read_public(task.url)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Public smoke destination rejected") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Public machine browser smoke failed") from exc
    return result


@app.post("/v1/plan", dependencies=[Depends(auth)])
async def plan(task: BrowserPlan):
    if not safe_url(task.url):
        raise HTTPException(status_code=403, detail="Origin not granted for this browser service")
    mutations = [a.action for a in task.actions if a.action not in ("read", "snapshot")]
    return {
        "schema": "plenum-browser-plan-v1",
        "approved_public_origin": True,
        "allowed_to_run_now": not bool(mutations),
        "remote_write_actions_require_owner_review": bool(mutations),
        "actions_not_executed": mutations,
        "account_session_available": False,
        "owner_approval_endpoint_available": False,
        "notice": "Remote clicks, fills, logins, uploads and submissions are disabled until a verified private profile vault, scoped owner approvals and network isolation exist."
    }

@app.post("/v1/read", dependencies=[Depends(auth)])
async def read(task: BrowserRequest):
    if not safe_url(task.url):
        raise HTTPException(status_code=403, detail="Origin not granted for this browser service")
    try:
        return await read_public(task.url)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Destination rejected") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Public browser task unavailable") from exc

@app.post("/v1/local-smoke", dependencies=[Depends(auth)])
async def local_smoke():
    return await local_interaction_smoke()

# Owner-facing Google IAP page is separate from the service's internal bearer API.
from .owner_console import mount_owner_console
mount_owner_console(app)

from .private_login import mount_private_login
mount_private_login(app)

# IAP-only encrypted website session status, preview and revocation.
from .owner_saved_session import mount_owner_saved_session
mount_owner_saved_session(app)
