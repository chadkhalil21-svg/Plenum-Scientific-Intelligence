import assert from "node:assert/strict";
import {randomBytes,createHash,createHmac} from "node:crypto";
import {sealSnapshot,openSnapshot} from "./paperclip-snapshot.mjs";
import {handleNativeSnapshot,PaperclipSnapshotStore} from "./paperclip-snapshot-transport.mjs";
class Storage{
  constructor(){this.rows=new Map();}
  async get(k){return structuredClone(this.rows.get(k));}
  async put(k,v){this.rows.set(k,structuredClone(v));}
  async transaction(f){const before=structuredClone(this.rows);try{return await f(this);}catch(e){this.rows=before;throw e;}}
}
const id={company:"11111111-1111-4111-8111-111111111111",mission:"22222222-2222-4222-8222-222222222222",snapshot:"33333333-3333-4333-8333-333333333333",source_commit:"b".repeat(40)};
const scope=Object.values(id).join("/"),data=new Uint8Array(randomBytes(650000)),key=new Uint8Array(randomBytes(32));
const secret=randomBytes(32).toString("hex"),bundle=await sealSnapshot(data,key,id);
const hash=createHash("sha256").update(JSON.stringify(bundle.manifest)).digest("hex"),prefix="/native-snapshots/"+scope+"/"+hash;
const objects=new Map();let accesses=0;
const env={PLENUM_NATIVE_SNAPSHOT_ENABLED:"true",PLENUM_NATIVE_SNAPSHOT_SCOPE:scope,PLENUM_NATIVE_SNAPSHOT_HMAC_SECRET:secret,
  PLENUM_NATIVE_SNAPSHOT_STORE:{getByName(n){accesses++;if(!objects.has(n))objects.set(n,new PaperclipSnapshotStore({storage:new Storage()}));return {fetch:(url,init)=>objects.get(n).fetch(new Request(url,init))};}}};
function request(op,method="GET",value,opts={}){
  const raw=value===undefined?"":JSON.stringify(value),path=opts.path??prefix+"/"+op,time=String(opts.time??Date.now());
  const sig=createHmac("sha256",opts.secret??secret).update([method,path,time,raw].join("\n")).digest("hex");
  return new Request("https://example.invalid"+path,{method,headers:{"x-plenum-memory-time":time,"x-plenum-memory-signature":"sha256="+sig},...(method==="POST"?{body:raw}:{})});
}
const call=(op,method,value,opts)=>handleNativeSnapshot(request(op,method,value,opts),env);
assert.equal((await handleNativeSnapshot(request("manifest"),{...env,PLENUM_PREVIEW_ONLY:"true"})).status,403);
assert.equal((await handleNativeSnapshot(request("manifest"),{...env,PLENUM_PRIVATE_MEMORY_HMAC_SECRET:secret})).status,403);
assert.equal((await call("manifest","GET",undefined,{secret:randomBytes(32).toString("hex")})).status,403);
assert.equal((await call("manifest","GET",undefined,{time:Date.now()-300000})).status,403);
assert.equal((await call("manifest","GET",undefined,{path:prefix.replace(id.mission,id.company)+"/manifest"})).status,403);
assert.equal(accesses,0);
assert.equal((await call("reserve","POST",{manifest:bundle.manifest})).status,201);
assert.equal((await call("reserve","POST",{manifest:bundle.manifest})).status,409);
assert.equal((await call("commit","POST",{})).status,409);
assert.equal((await call("manifest")).status,409);
assert.equal((await call("chunk/1","POST",{ciphertext:Buffer.from(bundle.chunks[1]).toString("base64")})).status,409);
const first={ciphertext:Buffer.from(bundle.chunks[0]).toString("base64")};
assert.equal((await call("chunk/0","POST",first)).status,201);
assert.equal((await call("chunk/0","POST",first)).status,409);
assert.equal((await call("chunk/1","POST",{ciphertext:Buffer.from(bundle.chunks[1]).toString("base64")})).status,201);
assert.equal((await call("commit","POST",{})).status,201);
assert.equal((await call("commit","POST",{})).status,409);
const m=await (await call("manifest")).json(),chunks=[];
for(let i=0;i<m.count;i++){const response=await call("chunk/"+i);assert.equal(response.status,200);chunks.push(new Uint8Array(Buffer.from((await response.json()).ciphertext,"base64")));}
assert.deepEqual(await openSnapshot({manifest:m,chunks},key,id),data);
console.log(JSON.stringify({synthetic_data_only:true,storage_emulator_only:true,authenticated_transport_roundtrip:true,live_cloudflare_verified:false,actual_native_database_restored:false,paid_inference:false,model_calls_replayed:0,provider_calls_replayed:0}));
