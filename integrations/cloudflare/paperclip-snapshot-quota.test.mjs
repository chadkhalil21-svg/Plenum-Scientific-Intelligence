import assert from "node:assert/strict";
import {reserveSnapshot} from "./paperclip-snapshot.mjs";
const store={rows:new Map(),async get(k){return structuredClone(this.rows.get(k));},async put(k,v){this.rows.set(k,structuredClone(v));},async transaction(f){const before=structuredClone(this.rows);try{return await f(this);}catch(e){this.rows=before;throw e;}}};
const id={company:"11111111-1111-4111-8111-111111111111",mission:"22222222-2222-4222-8222-222222222222",snapshot:"33333333-3333-4333-8333-333333333333",source_commit:"a".repeat(40)};
const m=(identity,size)=>({schema:"plenum-native-snapshot-v1",identity,nonce_prefix:"a".repeat(16),size,count:Math.ceil(size/524288),chunks:Array(Math.ceil(size/524288)).fill("b".repeat(64))});
await reserveSnapshot(store,id,m(id,160*1024*1024));
const next={...id,snapshot:"44444444-4444-4444-8444-444444444444"};
await assert.rejects(()=>reserveSnapshot(store,next,m(next,100*1024*1024)),/quota exhausted/);
assert.equal((await store.get("native-snapshot-budget")).count,1);
for(let i=5;i<=7;i++){const x={...id,snapshot:String(i).repeat(8)+"-4444-4444-8444-444444444444"};await reserveSnapshot(store,x,m(x,1));}
await assert.rejects(()=>reserveSnapshot(store,next,m(next,1)),/quota exhausted/);
console.log(JSON.stringify({aggregate_quota_enforced:true,partial_reservations_counted:true,synthetic_data_only:true,paid_inference:false}));
