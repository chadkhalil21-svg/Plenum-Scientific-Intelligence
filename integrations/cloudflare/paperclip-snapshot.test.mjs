import assert from "node:assert/strict";
import {randomBytes} from "node:crypto";
import {sealSnapshot,openSnapshot,storeSnapshot,loadSnapshot,reserveSnapshot,storeChunk,commitSnapshot,readManifest,readChunk} from "./paperclip-snapshot.mjs";
const id={company:"11111111-1111-4111-8111-111111111111",mission:"22222222-2222-4222-8222-222222222222",snapshot:"33333333-3333-4333-8333-333333333333",source_commit:"a".repeat(40)};
const data=new Uint8Array(randomBytes(1200000)),key=new Uint8Array(randomBytes(32));
class Storage {
  constructor(rows=new Map()){this.rows=rows;}
  async get(k){return structuredClone(this.rows.get(k));}
  async put(k,v){this.rows.set(k,structuredClone(v));}
  async transaction(f){const before=structuredClone(this.rows);try{return await f(this);}catch(e){this.rows=before;throw e;}}
}
const storage=new Storage();
const bundle=await sealSnapshot(data,key,id);
const receipt=await storeSnapshot(storage,bundle,id);
assert.equal(receipt.ciphertext_chunks,3);
const fresh=new Storage(structuredClone(storage.rows));
const loaded=await loadSnapshot(fresh,id,receipt.manifest_sha256);
assert.deepEqual(await openSnapshot(loaded,key,id),data);
await assert.rejects(()=>storeSnapshot(storage,bundle,id),/already reserved/);
await assert.rejects(()=>openSnapshot(loaded,new Uint8Array(randomBytes(32)),id));
await assert.rejects(()=>openSnapshot(loaded,key,{...id,mission:id.company}),/scope/);
await assert.rejects(()=>loadSnapshot(fresh,id,"0".repeat(64)),/digest/);
const tampered=structuredClone(loaded);tampered.chunks[0][0]^=1;
await assert.rejects(()=>openSnapshot(tampered,key,id),/ciphertext/);
const reordered=structuredClone(loaded);[reordered.chunks[0],reordered.chunks[1]]=[reordered.chunks[1],reordered.chunks[0]];
await assert.rejects(()=>openSnapshot(reordered,key,id),/ciphertext/);
const incomplete=structuredClone(loaded);incomplete.chunks.pop();
await assert.rejects(()=>openSnapshot(incomplete,key,id),/incomplete/);
const broken=new Storage();let writes=0;
broken.put=async function(k,v){if(++writes===3)throw Error("simulated interruption");this.rows.set(k,structuredClone(v));};
await assert.rejects(()=>storeSnapshot(broken,bundle,id),/interruption/);
await assert.rejects(()=>loadSnapshot(broken,id,receipt.manifest_sha256),/manifest/);
await assert.rejects(()=>storeSnapshot(broken,bundle,id),/already reserved/);
await assert.rejects(()=>sealSnapshot(new Uint8Array(),key,id),/bounds/);
const staged=new Storage();
const ticket=await reserveSnapshot(staged,id,bundle.manifest);
await assert.rejects(()=>commitSnapshot(staged,id,ticket.manifest_sha256),/incomplete/);
await assert.rejects(()=>storeChunk(staged,id,ticket.manifest_sha256,1,bundle.chunks[1]),/nonsequential/);
await storeChunk(staged,id,ticket.manifest_sha256,0,bundle.chunks[0]);
await assert.rejects(()=>storeChunk(staged,id,ticket.manifest_sha256,0,bundle.chunks[0]),/replayed/);
await assert.rejects(()=>readManifest(staged,id,ticket.manifest_sha256),/manifest/);
for(let i=1;i<bundle.chunks.length;i++)await storeChunk(staged,id,ticket.manifest_sha256,i,bundle.chunks[i]);
await commitSnapshot(staged,id,ticket.manifest_sha256);
await assert.rejects(()=>commitSnapshot(staged,id,ticket.manifest_sha256),/committed/);
assert.deepEqual(await readChunk(staged,id,ticket.manifest_sha256,2),bundle.chunks[2]);
assert.deepEqual(await openSnapshot(await loadSnapshot(staged,id,ticket.manifest_sha256),key,id),data);
console.log(JSON.stringify({synthetic_data_only:true,storage_emulator_only:true,actual_native_database_restored:false,live_cloudflare_verified:false,paid_inference:false,model_calls_replayed:0,provider_calls_replayed:0,roundtrip:true,negative_cases:16}));
