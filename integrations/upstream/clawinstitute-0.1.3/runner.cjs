'use strict';
// Explicitly invoked, finite coordination operation; inputs are research text only.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { once } = require('node:events');

const pin = '0.1.3';
const roles = ['research', 'verification'];
const hash = s => crypto.createHash('sha256').update(s).digest('hex');
function text(input, key, max) {
  const s = input[key];
  if (typeof s !== 'string' || !s.trim() || s.includes('\0') || s.length > max) throw new Error(`Invalid ${key}`);
  return s.trim();
}
async function main() {
  if (process.argv.length !== 3 || process.argv[2] !== '--run') throw new Error('Explicit --run required; provide research JSON on stdin');
  if (Number(process.versions.node.split('.')[0]) < 22 || require('clawinstitute/package.json').version !== pin) throw new Error('Unsupported Node or package version');
  const chunks = [];
  let bytes = 0;
  for await (const chunk of process.stdin) {
    bytes += chunk.length;
    if (bytes > 24000) throw new Error('Input exceeds 24 KB');
    chunks.push(chunk);
  }
  const input = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  if (!input || Array.isArray(input) || Object.keys(input).sort().join(',') !== 'critique,proposal,revision,title') throw new Error('Expected title, proposal, critique, revision');
  const title = text(input, 'title', 200), proposal = text(input, 'proposal', 6000);
  const critique = text(input, 'critique', 6000), revision = text(input, 'revision', 6000);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'plenum-claw-'));
  const token = 'claw_' + crypto.randomBytes(32).toString('hex');
  // Prevent accidental use of inherited credentials or non-local data services.
  for (const key of Object.keys(process.env)) if (key.startsWith('CLAWINSTITUTE_') || key === 'DATABASE_URL') delete process.env[key];
  Object.assign(process.env, { CLAWINSTITUTE_DB_DIR: path.join(dir, 'db'), CLAWINSTITUTE_HOME: dir,
    CLAWINSTITUTE_TOKEN: token, CLAWINSTITUTE_AUTH_REQUIRED: '1', CLAWINSTITUTE_ALLOW_EPHEMERAL: '1',
    CLAWINSTITUTE_CHECKPOINT_MS: '0', CLAWINSTITUTE_SKIP_FRONTEND: '1', NODE_ENV: 'production' });
  let server, db;
  try {
    db = require('clawinstitute/src/db/client.js');
    await require('clawinstitute/src/db/migrate.js').runMigrations();
    assert.equal(db.mode(), 'pglite');
    const app = require('clawinstitute/src/app.js');
    server = http.createServer((req, res) => {
      if (req.headers.authorization !== `Bearer ${token}`) { res.writeHead(401); return res.end(); }
      app(req, res);
    });
    server.listen(0, '127.0.0.1');
    await once(server, 'listening');
    assert.equal(server.address().address, '127.0.0.1');
    const url = `http://127.0.0.1:${server.address().port}/api/v1`;
    const rejected = await fetch(url + '/workshops', { signal: AbortSignal.timeout(5000) });
    assert.equal(rejected.status, 401);
    async function request(method, route, role, body, version) {
      const response = await fetch(url + route, { method, redirect: 'error', signal: AbortSignal.timeout(5000),
        headers: { authorization: `Bearer ${token}`, 'x-agent-name': role, 'content-type': 'application/json',
          ...(version === undefined ? {} : { 'if-match': String(version) }) },
        ...(body === undefined ? {} : {body: JSON.stringify(body)}) });
      if (!response.ok) throw new Error(`${method} ${route.split('/')[1]} HTTP ${response.status}`);
      return response.json();
    }
    for (const role of roles) await request('POST', '/agents/register', role, {name: role, description: 'Local attributed research role; not an autonomous agent'});
    const workshop = 'plenum-research-review';
    await request('POST', '/workshops', roles[0], { name: workshop, display_name: title });
    const { post } = await request('POST', '/posts', roles[0], {workshop, title, content: proposal});
    await request('POST', `/posts/${post.id}/comments`, roles[1], { content: critique });
    const { comments } = await request('GET', `/posts/${post.id}/comments`, roles[0]);
    assert.equal(comments.length, 1); assert.equal(comments[0].content, critique);
    assert.equal(comments[0].author_name, roles[1]);
    const ws = await request('POST', '/workspaces', roles[0], { title, workshop, visibility: 'public' });
    const file = `/workspaces/${ws.id}/files/research-review.md`;
    await request('PUT', file, roles[0], {content: proposal});
    await request('PUT', file, roles[1], {content: revision}, 1);
    const current = await request('GET', file, roles[0]);
    const original = await request('GET', file + '?version=1', roles[0]);
    assert.equal(current.version, 2); assert.equal(current.content, revision);
    assert.equal(current.updatedBy, roles[1]); assert.equal(original.content, proposal);
    console.log(JSON.stringify({ package: 'clawinstitute', version: pin, db: 'pglite', listen: '127.0.0.1',
      unauthorized_http_status: rejected.status, role_attribution: roles, workshop: workshop,
      comments: comments.length, file_version: current.version, proposal_sha256: hash(proposal),
      critique_sha256: hash(critique), revision_sha256: hash(revision), scope: 'coordination only; supplied text; no model or agents executed' }));
  } finally {
    if (server) await new Promise(resolve => { server.close(resolve); server.closeAllConnections(); });
    if (db) await db.close();
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
// A hard stop bounds the local invocation, including stdin and DB setup.
const guard = setTimeout(() => { console.error('Coordination deadline exceeded'); process.exit(1); }, 45000);
main().catch(e => { console.error(e.message); process.exitCode = 1; }).finally(() => clearTimeout(guard));
