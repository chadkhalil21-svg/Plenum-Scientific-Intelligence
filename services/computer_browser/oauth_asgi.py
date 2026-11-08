"""Isolated ASGI entrypoint for the owner-bound MCP facade only.

This is NOT the IAP owner-browser app or the IAM machine Playwright worker.
Missing OAuth configuration prevents process startup, and no browser account
session is loaded here. Cloud Run's ingress to this process must be isolated
in its own service and protected at the application layer via OAuth.
"""
from starlette.responses import JSONResponse
from starlette.routing import Route
from .mcp_resource_server import create_private_browser_mcp

server = create_private_browser_mcp()
app = server.streamable_http_app()


async def health(request):
    """No user data; confirms only that strict OAuth config parsed at startup."""
    return JSONResponse(
        {"service": "plenum-computer-browser-oauth-facade",
         "configured": True,
         "private_accounts_enabled": False,
         "remote_website_writes_enabled": False},
        headers={"Cache-Control": "no-store"},
    )


app.router.routes.append(Route("/health", endpoint=health, methods=["GET"]))
