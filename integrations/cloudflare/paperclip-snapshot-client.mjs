// Owner-only encrypted archive transport. No production credentials in CI.
import {createHash,createHmac} from "node:crypto";
import {sealSnapshot,openSnapshot} from "./paperclip-snapshot.mjs";
const HOST="https://plenum-public-wake.chadkhalil21.workers.dev", MAX=256*1024*1024;
const sha=x=>createHash("sha256").update(x).digest("hex");
function check(ok){if(!ok)throw Error("Snapshot transport rejected");}
const validHash=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
function scope(id){
 check(id&&Object.keys(id).sort().join(",")==="company,mission,snapshot,source_commit"&&
 [id.company,id.mission,id.snapshot].every(x=>typeof x==="string"&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x))&&
 typeof id.source_commit==="string"&&/^[0-9a-f]{40}$/.test(id.source_commit));
 return [id.company,id.mission,id.snapshot,id.source_commit].join("/");
}
function exact(x,fields){check(x&&typeof x==="object"&&!Array.isArray(x)&&Object.keys(x).sort().join(",")===fields);}
function client(id,secret,fetcher){
 check(typeof secret==="string"&&secret.length>=32&&secret.length<=512);const prefix="/native-snapshots/"+scope(id)+"/";
 return async (hash,op,method,value,status,limit=720*1024)=>{
  check(validHash(hash));const path=prefix+hash+"/"+op,time=String(Date.now()),raw=value===undefined?"":JSON.stringify(value);
  const signature=createHmac("sha256",secret).update([method,path,time,raw].join("\n")).digest("hex");
  // A rejected or ambiguous write is never retried. Fixed endpoint, no redirects.
  const response=await fetcher(HOST+path,{method,redirect:"error",signal:AbortSignal.timeout(30000),
    headers:{"x-plenum-memory-time":time,"x-plenum-memory-signature":"sha256="+signature,...(method==="POST"?{"Content-Type":"application/json"}:{})},
    ...(method==="POST"?{body:raw}:{})});
  check(response.status===status);
  check(Number(response.headers.get("content-length")||0)<=limit);
  const reader=response.body.getReader(),chunks=[];let count=0;
  try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.length;check(count<=limit);chunks.push(value);}}
  finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
 };
}
// Explicit injectable transport is solely for isolated synthetic tests. The CLI
// below is the owner boundary and does not permit a replacement endpoint.
export async function uploadArchive(raw,key,id,secret,fetcher){
 const b=await sealSnapshot(raw,key,id),h=sha(JSON.stringify(b.manifest)),call=client(id,secret,fetcher);
 const reservation=await call(h,"reserve","POST",{manifest:b.manifest},201);
 exact(reservation,"ciphertext_chunks,manifest_sha256,plaintext_bytes,snapshot");
 check(reservation.snapshot===id.snapshot&&reservation.manifest_sha256===h&&reservation.ciphertext_chunks===b.chunks.length&&reservation.plaintext_bytes===raw.length);
 for(let i=0;i<b.chunks.length;i++){
  const a=await call(h,"chunk/"+i,"POST",{ciphertext:Buffer.from(b.chunks[i]).toString("base64")},201);
  exact(a,"accepted");check(a.accepted===true);
 }
 const c=await call(h,"commit","POST",{},201);exact(c,"committed");check(c.committed===true);
 return {manifest_sha256:h,archive_sha256:sha(raw),size:raw.length,identity:id};
}
export async function downloadArchive(receipt,key,id,secret,fetcher){
 exact(receipt,"archive_sha256,identity,manifest_sha256,size");
 check(scope(receipt.identity)===scope(id)&&validHash(receipt.archive_sha256)&&validHash(receipt.manifest_sha256)&&Number.isSafeInteger(receipt.size)&&receipt.size>0&&receipt.size<=MAX);
 const h=receipt.manifest_sha256,call=client(id,secret,fetcher),m=await call(h,"manifest","GET",undefined,200);
 check(sha(JSON.stringify(m))===h&&m.size===receipt.size&&m.count===Math.ceil(m.size/524288));
 const chunks=[];
 for(let i=0;i<m.count;i++){
  const a=await call(h,"chunk/"+i,"GET",undefined,200);exact(a,"ciphertext");
  check(typeof a.ciphertext==="string"&&a.ciphertext.length<=700000);
  const b=Buffer.from(a.ciphertext,"base64");check(b.toString("base64")===a.ciphertext);chunks.push(new Uint8Array(b));
 }
 const raw=await openSnapshot({manifest:m,chunks},key,id);check(sha(raw)===receipt.archive_sha256&&raw.length===receipt.size);return raw;
}
