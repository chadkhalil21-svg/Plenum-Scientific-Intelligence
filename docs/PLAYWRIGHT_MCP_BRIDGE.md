# Official Playwright MCP bridge: real protocol test and permission gates

This is the next milestone after Plenum's real isolated Python Playwright
browser proof (run 42409395480). Rather than building another protocol, this
uses the official `@playwright/mcp@0.0.84` alongside the pinned
`@modelcontextprotocol/sdk@1.25.2`. It launches a child MCP server in
**isolated**, **headless** mode, handshakes via stdio, enumerates browser tools,
and calls only `browser_navigate` and `browser_snapshot` on the approved
public `https://example.com/` page. The expected accessibility snapshot
must contain **Example Domain**.

An independent local test rejects unwanted origins, credentials, local/IP
addresses, alternate paths and disallowed browser tools such as clicks,
uploads, JavaScript evaluation and general form submissions. Even though the
underlying official MCP server advertises powerful actions, no untrusted
model receives that raw tool list or its direct transport. Only the
`readOnlyCall` policy function is permitted to dispatch a call in this pilot.

This is **not yet** model-driven website interaction. It neither reads private
accounts nor modifies real sites, grants agent authority, uses an LLM,
exposes an authenticated HTTP server, nor persists browser sessions. A
successful CI demonstration establishes only the official MCP wire protocol,
real navigation and structured accessibility reading.

The Playwright documentation warns that `--allowed-origins` is *not* a
security boundary; we therefore treat this integration only as a fixed public
example and do not grant browsing of user-selected arbitrary sites from it.
Future real web agent operations require network sandboxing, DNS/IP SSRF
protection, content trust boundaries, signed task scopes, human review of
consequential actions and secure isolated browser-profile storage.

## Run

GitHub Actions → **Verify Real Playwright MCP Read-only Integration**.
The workflow runs only with GitHub's read-only source permissions and does not
receive `KAGGLE_API_TOKEN`, payment credentials or any cloud session.

## Relationship to ChatGPT

ChatGPT's **TinyFish** plugin can supply browser capabilities in ordinary chat
only after the user connects it and grants the necessary permissions. It is
not this independent Plenum MCP server.

## Next objective

Connect the guarded tool interface to LangGraph with a real evaluated model
and a *bounded* public question; score on clean unseen tasks before allowing
more tools or automatic browsing. Use Kaggle only for temporary GPU inference
until a durable provider and budget have been selected.
