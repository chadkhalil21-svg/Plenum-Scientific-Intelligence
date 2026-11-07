// A narrow policy boundary BEFORE calling Microsoft's powerful browser MCP tools.
// Never hand the raw MCP client/tool list to an untrusted model.
export const APPROVED_ORIGINS = Object.freeze(["https://example.com"]);
export const ALLOWED_READ_TOOLS = Object.freeze(["browser_navigate", "browser_snapshot", "browser_close"]);

export function approvedUrl(value) {
  if (typeof value !== "string" || value.length > 900 || /[\u0000-\u001f\u007f]/.test(value)) return false;
  let parsed;
  try { parsed = new URL(value); } catch { return false; }
  return (parsed.protocol === "https:" && parsed.origin === "https://example.com" &&
          !parsed.username && !parsed.password && !parsed.hash && !parsed.search &&
          parsed.port === "" && parsed.pathname === "/");
}

export function validateCall(name, args) {
  if (!ALLOWED_READ_TOOLS.includes(name)) throw new Error("Browser capability not approved for this pilot");
  if (name === "browser_navigate") {
    if (!args || Object.keys(args).sort().join(",") !== "url" || !approvedUrl(args.url))
      throw new Error("Navigation denied: this pilot can visit only https://example.com/");
  } else if (!args || Object.keys(args).length !== 0) {
    throw new Error("Unexpected browser tool arguments");
  }
  return true;
}

export async function readOnlyCall(client, name, args) {
  validateCall(name, args);
  const result = await client.callTool({ name, arguments: args });
  if (result?.isError) throw new Error("Approved browser tool reported an error");
  return result;
}
