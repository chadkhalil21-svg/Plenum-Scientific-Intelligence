// Candidate storage core only: no public route, no deployment or credential handling.
// Call only after a separately authorized private-runtime boundary.
const CHUNK=512*1024, MAX=256*1024*1024;
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
// Durable Object storage API; reserve once, no retry or overwrite after ambiguity.
// Each ciphertext value is below 512 KiB + 16 bytes; commit marker last.
export async function storeSnapshot(storage,bundle,input){
  const id=identity(input),m=manifest(bundle.manifest,id),p=slot(id);
  require(Array.isArray(bundle.chunks)&&bundle.chunks.length===m.count,"incomplete snapshot");
  for(let i=0;i<m.count;i++){
    const c=bytes(bundle.chunks[i]);
    require(c.length===Math.min(CHUNK,m.size-i*CHUNK)+16&&await sha(c)===m.chunks[i],"ciphertext mismatch");
  }
  await storage.transaction(async tx=>{
    require(await tx.get(p+"reserved")===undefined&&await tx.get(p+"manifest")===undefined,"snapshot already reserved");
    await tx.put(p+"reserved",true);
  });
  for(let i=0;i<m.count;i++)await storage.put(p+"chunk:"+i,bundle.chunks[i]);
  await storage.put(p+"manifest",m);
  return {snapshot:id.snapshot,manifest_sha256:await sha(enc.encode(JSON.stringify(m))),ciphertext_chunks:m.count,plaintext_bytes:m.size};
}
export async function loadSnapshot(storage,input,expectedManifestHash){
  const id=identity(input),p=slot(id);
  require(typeof expectedManifestHash==="string"&&digest.test(expectedManifestHash),"independent manifest digest required");
  require(await storage.get(p+"reserved")===true,"snapshot not reserved");
  const m=manifest(await storage.get(p+"manifest"),id);
  require(await sha(enc.encode(JSON.stringify(m)))===expectedManifestHash,"manifest digest mismatch");
  const chunks=[];
  for(let i=0;i<m.count;i++){
    const c=bytes(await storage.get(p+"chunk:"+i));
    require(c.length===Math.min(CHUNK,m.size-i*CHUNK)+16&&await sha(c)===m.chunks[i],"ciphertext mismatch");
    chunks.push(c);
  }
  return {manifest:m,chunks};
}
