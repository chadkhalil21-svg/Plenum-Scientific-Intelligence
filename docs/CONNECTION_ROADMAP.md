# Prometheus integration strategy: do not clone everything

**Founder mandate:** reuse proven external engines, APIs and connectors, while
maximizing validated breadth and avoiding duplicated engineering, large bills
or unnecessary access grants.

## Actual status as of 2026-11-07
| Area | Already implemented or verified | Next worthwhile step | Permission/cost |
|---|---|---|---|
| GitHub engineering | Owner repository, Actions, reviewed PRs, public memory ledger | Extend independent benchmarks; protect sensitive environments | Existing access |
| Kaggle GPU | Authenticated API listing via GitHub workflow run #42408852329 | Privately draft trial notebook then owner manually starts 27B inference | GitHub env secret exists; explicit run approval |
| General web/browser | Official Playwright isolated local interaction fixture and public allowlisted read-only browser | Add reviewed Playwright MCP agent adapter, secure session vault and approvals | No browser credentials now |
| Journals/science | OpenAlex, arXiv, Europe PMC, Semantic Scholar, Crossref, OSTI, CAS/China-affiliated works, selected lab feeds and research memory | Improve discovery quality, translation, full-text licenses and prospective verification | Public metadata only |
| Science engines | SciPy, RDKit, OpenMDAO, Aviary, Astropy, PyBaMM, OpenMM, PySCF, Lean, and selected evaluated papers | Connect actual method workflows into one end-to-end research question | Pinned isolated runners |
| Reasoning models | Small Qwen/SmolLM and Inspect AI, broader trials planned | Perform real Kaggle 27B quantified inference with matched independent tasks | Limited free GPU quota |
| Voice | LiveKit agent SDK integration has been trialed | Bind STT/TTS model and hosted realtime transport for a voluntary voice conversation | Runtime/audio provider and consent needed |
| Video/creativity | Public NASA YouTube metadata, Openverse, Met and MusicBrainz; original SVG/MusicXML | Add licensed captions/media processing and visual understanding; no blanket scraping | Rights and keys where required |
| Google Workspace | Connectors for Google Drive and Gmail are available in ChatGPT; not automatically installed inside Prometheus | Add OAuth-backed scopes and audit logs only if required for a concrete task | Separate owner authorization |
| Other provider apps | Render, Resend, Stripe and others are available in ChatGPT but NOT general Prometheus credentials | Install one narrow connector per owner-approved workflow, not entire accounts | No financial or communications permission by default |
| Colab / HF ZeroGPU | Evaluated as optional short-running alternatives | Use only if Kaggle quota/compatibility demands | Separate accounts and usage limits |
| Long-running autonomy | Daily scheduled CI research and research-memory ledger | Durable authenticated coordinator, queues, retries, permissions and test harness | Host selected after verified task |
| Computer control | Playwright proof, local and public modes only | Add MCP-compatible runtime and policy-gated plans | No silent writes or logged-in accounts |

**Avoid immediately connecting every service:** much of the world is accessible
through public APIs. OAuth tokens, paid subscriptions, persistent cloud servers
and overlapping browsers increase attack surface, not intelligence. Add only
connections that have a tested use, rights to data, explicit operational scope,
and rollback.

The ledger remains the authoritative `research-memory/state/AGI_PROGRAM.json`;
this document is an integration map, not a capability certificate.
