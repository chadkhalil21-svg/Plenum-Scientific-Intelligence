import assert from "node:assert/strict";
import {randomBytes,createHash,createHmac} from "node:crypto";
import {mkdtemp,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join,dirname} from "node:path";
import {fileURLToPath} from "node:url";
import {Miniflare} from "miniflare";
import {sealSnapshot,openSnapshot} from "./paperclip-snapshot.mjs";
const root=dirname(fileURLToPath(import.meta.url)),persist=await mkdtemp(join(tmpdir(),"plenum-do-"));
const id={company:"11111111-1111-4111-8111-111111111111",mission:"22222222-2222-4222-8222-222222222222",snapshot:"33333333-3333-4333-8333-333333333333",source_commit:"c".repeat(40)};
const scope=Object.values(id).join("/"),data=new Uint8Array(randomBytes(650000)),key=new Uint8Array(randomBytes(32)),secret=randomBytes(32).toString("hex");
const bundle=await sealSnapshot(data,key,id),hash=createHash("sha256").update(JSON.stringify(bundle.manifest)).digest("hex"),prefix="/native-snapshots/"+scope+"/"+hash;
function runtime(enabled){return new Miniflare({modules:true,scriptPath:join(root,"plenum-github-wake-worker.mjs"),compatibilityDate:"2026-07-01",durableObjects:{PLENUM_NATIVE_SNAPSHOT_STORE:{className:"PaperclipSnapshotStore",useSQLite:true}},durableObjectsPersist:persist,bindings:{PLENUM_NATIVE_SNAPSHOT_ENABLED:enabled?"true":"false",PLENUM_NATIVE_SNAPSHOT_SCOPE:scope,PLENUM_NATIVE_SNAPSHOT_HMAC_SECRET:secret}});}
function call(mf,op,method="GET",value,override){
 const raw=value===undefined?"":JSON.stringify(value),path=override??prefix+"/"+op,time=String(Date.now());
 const sig=createHmac("sha256",secret).update([method,path,time,raw].join("\n")).digest("hex");
 return mf.dispatchFetch("http://localhost"+path,{method,headers:{"x-plenum-memory-time":time,"x-plenum-memory-signature":"sha256="+sig},...(method==="POST"?{body:raw}:{})});
}
let mf;
try{
 mf=runtime(false);assert.equal((await call(mf,"manifest")).status,403);await mf.dispose();mf=runtime(true);
 assert.equal((await call(mf,"manifest","GET",undefined,prefix.replace(id.mission,id.company)+"/manifest")).status,403);
 assert.equal((await call(mf,"reserve","POST",{manifest:bundle.manifest})).status,201);
 assert.equal((await call(mf,"commit","POST",{})).status,409);
 for(let i=0;i<bundle.chunks.length;i++){
  const body={ciphertext:Buffer.from(bundle.chunks[i]).toString("base64")};
  assert.equal((await call(mf,"chunk/"+i,"POST",body)).status,201);
  assert.equal((await call(mf,"chunk/"+i,"POST",body)).status,409);
 }
 assert.equal((await call(mf,"commit","POST",{})).status,201);
 await mf.dispose();mf=runtime(true);
 const mr=await call(mf,"manifest");assert.equal(mr.status,200);const m=await mr.json(),chunks=[];
 for(let i=0;i<m.count;i++){const c=await call(mf,"chunk/"+i);assert.equal(c.status,200);chunks.push(new Uint8Array(Buffer.from((await c.json()).ciphertext,"base64")));}
 assert.deepEqual(await openSnapshot({manifest:m,chunks},key,id),data);
 assert.equal((await call(mf,"reserve","POST",{manifest:bundle.manifest})).status,409);
 console.log(JSON.stringify({synthetic_data_only:true,actual_workerd_local:true,sqlite_persistence_across_instances:true,live_cloudflare_verified:false,native_database_restored:false,paid_inference:false,model_calls_replayed:0,provider_calls_replayed:0}));
}finally{if(mf)await mf.dispose();await rm(persist,{recursive:true,force:true});}
