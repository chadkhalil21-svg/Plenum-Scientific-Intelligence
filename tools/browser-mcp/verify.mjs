/* Actual MCP stdio round-trip through official pinned Microsoft Playwright package.
 * Only a deterministic allowlisted public page. No accounts, private data or
 * model-directed arbitrary tool calls. This is NOT an LLM-driven browser agent.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { approvedUrl, readOnlyCall } from "./policy.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const url = process.argv[2] || "https://example.com/";
if (!approvedUrl(url)) throw new Error("Only https://example.com/ approved for this pilot");
const serverCli = path.join(here, "node_modules", "@playwright", "mcp", "cli.js");
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [serverCli, "--headless", "--isolated", "--block-service-workers",
         "--no-webmcp", "--idle-timeout=180000"],
  env: {
    PATH: process.env.PATH || "",
    HOME: process.env.HOME || "",
    TMPDIR: process.env.TMPDIR || "",
    CI: "true",
  },
  stderr: "pipe",
});
const client = new Client(
  { name: "plenum-readonly-browser-mcp-check", version: "0.1.0" },
  { capabilities: {} }
);
let connected = false;
try {
  await client.connect(transport);
  connected = true;
  const catalog = await client.listTools();
  const available = new Set((catalog.tools || []).map(t => t.name));
  if (!available.has("browser_navigate") || !available.has("browser_snapshot"))
    throw new Error("Official Playwright MCP lacks the required browser read tools");
  const navigated = await readOnlyCall(client, "browser_navigate", { url });
  const snapshot = await readOnlyCall(client, "browser_snapshot", {});
  const texts = [...(navigated.content || []), ...(snapshot.content || [])]
    .filter(x => x.type === "text").map(x => x.text || "").join("\n");
  if (!texts.includes("Example Domain") || !texts.includes("https://example.com/"))
    throw new Error("No independently observed public page accessibility result");
  if (available.has("browser_close"))
    await readOnlyCall(client, "browser_close", {});
  process.stdout.write(JSON.stringify({
    schema: "plenum-playwright-mcp-public-readonly-v1",
    upstream: "@playwright/mcp", upstream_version: "0.0.84",
    mcp_protocol_roundtrip_succeeded: true,
    public_page: "https://example.com/",
    accessibility_snapshot_has_example_domain: true,
    untrusted_page_content_executed_as_instructions: false,
    model_planned_browser_action: false,
    site_mutation_performed: false,
    authenticated_browser_session_used: false,
    AGI_demonstrated: false,
  }, null, 2) + "\n");
} finally {
  if (connected) {
    try { await client.close(); } catch { /* original failure preserved */ }
  }
}
