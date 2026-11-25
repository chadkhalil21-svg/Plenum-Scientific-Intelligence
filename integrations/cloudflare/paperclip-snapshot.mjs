// Candidate storage core only: no public route, no deployment or credential handling.
// Call only after a separately authorized private-runtime boundary.
const CHUNK=512*1024, MAX=256*1024*1024;
const TOTAL_BUDGET=256*1024*1024, MAX_SNAPSHOTS=4;
const enc=new TextEncoder();
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,"0")).join("");
const sha=async b=>hex(await crypto.subtle.digest("SHA-256",b));
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const digest=/^[0-9a-f]{64}$/;
function require(ok,msg){if(!ok)throw Error(msg);}
function identity(x){
  require(x&&Object.keys(x).sort().join(",")==="company,mission,snapshot,source_commit"&&
    [x.company,x.mission,x.snapshot].every(v=>typeof v==="string"&&uuid.test(v))&&
    typeof x.source_commit==="string"&&/^[0-9a-f]{40}$/.test(x.source_commit),"invalid identity");
  return {company:x.company,mission:x.mission,snapshot:x.snapshot,source_commit:x.source_commit};
}
function bytes(x){require(x instanceof Uint8Array,"bytes required");return x;}
function aad(id,i,count,size){return enc.encode(JSON.stringify({schema:"plenum-native-snapshot-v1",...id,i,count,size}));}
async function key(raw){require(bytes(raw).length===32,"AES-256 key required");return crypto.subtle.importKey("raw",raw,"AES-GCM",false,["encrypt","decrypt"]);}
function nonce(prefix,i){const n=new Uint8Array(12);n.set(prefix);new DataView(n.buffer).setUint32(8,i);return n;}
function prefixBytes(s){require(typeof s==="string"&&/^[0-9a-f]{16}$/.test(s),"invalid nonce prefix");return Uint8Array.from(s.match(/../g),v=>parseInt(v,16));}
function manifest(m,id){
  require(m&&Object.keys(m).sort().join(",")==="chunks,count,identity,nonce_prefix,schema,size"&&m.schema==="plenum-native-snapshot-v1"&&
    JSON.stringify(identity(m.identity))===JSON.stringify(id),"manifest scope mismatch");
  require(Number.isSafeInteger(m.size)&&m.size>0&&m.size<=MAX&&m.count===Math.ceil(m.size/CHUNK)&&
    Array.isArray(m.chunks)&&m.chunks.length===m.count&&m.chunks.every(x=>typeof x==="string"&&digest.test(x)),"invalid manifest");
  prefixBytes(m.nonce_prefix);return m;
}
function slot(id){return "native-snapshot:"+id.company+":"+id.mission+":"+id.snapshot+":";}
export async function sealSnapshot(raw,rawKey,input){
  const id=identity(input),data=bytes(raw);
  require(data.length>0&&data.length<=MAX,"snapshot size out of bounds");
  const k=await key(rawKey),count=Math.ceil(data.length/CHUNK),prefix=crypto.getRandomValues(new Uint8Array(8));
  const chunks=[],hashes=[];
  for(let i=0;i<count;i++){
    const c=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv:nonce(prefix,i),additionalData:aad(id,i,count,data.length),tagLength:128},k,data.subarray(i*CHUNK,(i+1)*CHUNK)));
    chunks.push(c);hashes.push(await sha(c));
  }
  return {manifest:{schema:"plenum-native-snapshot-v1",identity:id,nonce_prefix:hex(prefix),size:data.length,count,chunks:hashes},chunks};
}
export async function openSnapshot(bundle,rawKey,input){
  const id=identity(input),m=manifest(bundle.manifest,id),k=await key(rawKey),prefix=prefixBytes(m.nonce_prefix);
  require(Array.isArray(bundle.chunks)&&bundle.chunks.length===m.count,"incomplete snapshot");
  const output=new Uint8Array(m.size);
  for(let i=0;i<m.count;i++){
    const c=bytes(bundle.chunks[i]),size=Math.min(CHUNK,m.size-i*CHUNK);
    require(c.length===size+16&&await sha(c)===m.chunks[i],"ciphertext mismatch");
    const p=new Uint8Array(await crypto.subtle.decrypt({name:"AES-GCM",iv:nonce(prefix,i),additionalData:aad(id,i,m.count,m.size),tagLength:128},k,c));
    require(p.length===size,"plaintext length mismatch");output.set(p,i*CHUNK);
  }
  return output;
}
// Bounded independent requests: one reservation, sequential immutable chunks,
// and a final commit marker. Call only from an authorized private transport.
export async function reserveSnapshot(storage,input,value){
  const id=identity(input),m=manifest(value,id),p=slot(id);
  const h=await sha(enc.encode(JSON.stringify(m)));
  await storage.transaction(async tx=>{
    require(await tx.get(p+"reserved")===undefined&&await tx.get(p+"manifest")===undefined,"snapshot already reserved");
    // All scopes share one dedicated object; reserve conservatively before data writes.
    const budget=await tx.get("native-snapshot-budget")??{bytes:0,count:0};
    require(Number.isSafeInteger(budget.bytes)&&budget.bytes>=0&&Number.isSafeInteger(budget.count)&&budget.count>=0,"invalid quota ledger");
    const charge=m.size+m.count*16+65536;
    require(budget.bytes+charge<=TOTAL_BUDGET&&budget.count<MAX_SNAPSHOTS,"snapshot quota exhausted");
    await tx.put("native-snapshot-budget",{bytes:budget.bytes+charge,count:budget.count+1});
    await tx.put(p+"reserved",{manifest:m,hash:h,next:0});
  });
  return {snapshot:id.snapshot,manifest_sha256:h,ciphertext_chunks:m.count,plaintext_bytes:m.size};
}
function expectedHash(h){require(typeof h==="string"&&digest.test(h),"independent manifest digest required");}
export async function storeChunk(storage,input,h,i,raw){
  const id=identity(input),p=slot(id),c=bytes(raw);
  expectedHash(h);
  require(Number.isSafeInteger(i)&&i>=0&&i<MAX/CHUNK&&c.length<=CHUNK+16,"invalid chunk");
  const ch=await sha(c);
  await storage.transaction(async tx=>{
    const row=await tx.get(p+"reserved");
    require(row&&row.hash===h,"snapshot reservation mismatch");
    const m=manifest(row.manifest,id);
    require(await tx.get(p+"manifest")===undefined,"snapshot already committed");
    require(i===row.next&&i<m.count,"nonsequential or replayed chunk");
    require(c.length===Math.min(CHUNK,m.size-i*CHUNK)+16&&ch===m.chunks[i],"ciphertext mismatch");
    require(await tx.get(p+"chunk:"+i)===undefined,"chunk already exists");
    await tx.put(p+"chunk:"+i,c);
    await tx.put(p+"reserved",{manifest:m,hash:h,next:i+1});
  });
}
export async function commitSnapshot(storage,input,h){
  const id=identity(input),p=slot(id);expectedHash(h);
  await storage.transaction(async tx=>{
    const row=await tx.get(p+"reserved");
    require(row&&row.hash===h,"snapshot reservation mismatch");
    const m=manifest(row.manifest,id);
    require(await tx.get(p+"manifest")===undefined,"snapshot already committed");
    require(row.next===m.count,"incomplete snapshot");
    await tx.put(p+"manifest",m);
  });
}
export async function readManifest(storage,input,h){
  const id=identity(input),p=slot(id);expectedHash(h);
  const m=manifest(await storage.get(p+"manifest"),id);
  require(await sha(enc.encode(JSON.stringify(m)))===h,"manifest digest mismatch");
  return m;
}
export async function readChunk(storage,input,h,i){
  const id=identity(input),p=slot(id),m=await readManifest(storage,id,h);
  require(Number.isSafeInteger(i)&&i>=0&&i<m.count,"invalid chunk index");
  const c=bytes(await storage.get(p+"chunk:"+i));
  require(c.length===Math.min(CHUNK,m.size-i*CHUNK)+16&&await sha(c)===m.chunks[i],"ciphertext mismatch");
  return c;
}
// Client/emulator convenience; use staged operations individually in a Worker.
// This wrapper must not run with a large bundle inside a Worker memory budget.
export async function storeSnapshot(storage,bundle,input){
  const id=identity(input),m=manifest(bundle.manifest,id);
  require(Array.isArray(bundle.chunks)&&bundle.chunks.length===m.count,"incomplete snapshot");
  for(let i=0;i<m.count;i++){
    const c=bytes(bundle.chunks[i]);
    require(c.length===Math.min(CHUNK,m.size-i*CHUNK)+16&&await sha(c)===m.chunks[i],"ciphertext mismatch");
  }
  const receipt=await reserveSnapshot(storage,id,m);
  for(let i=0;i<m.count;i++)await storeChunk(storage,id,receipt.manifest_sha256,i,bundle.chunks[i]);
  await commitSnapshot(storage,id,receipt.manifest_sha256);
  return receipt;
}
export async function loadSnapshot(storage,input,h){
  const id=identity(input),m=await readManifest(storage,id,h),chunks=[];
  for(let i=0;i<m.count;i++)chunks.push(await readChunk(storage,id,h,i));
  return {manifest:m,chunks};
}
