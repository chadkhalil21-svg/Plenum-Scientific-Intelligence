// Isolated owner-only transport candidate. Disabled by default on the existing Worker.
// No existing checkpoint grant, route, or private memory permission is widened.
import {verifyPrivateRequest} from "./plenum-private-continuity.mjs";
import {reserveSnapshot,storeChunk,commitSnapshot,readManifest,readChunk} from "./paperclip-snapshot.mjs";
const LIMIT=720*1024, enc=new TextEncoder();
const uuid="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const pathPattern=new RegExp("^/native-snapshots/("+uuid+")/("+uuid+")/("+uuid+")/([0-9a-f]{40})/([0-9a-f]{64})/(reserve|commit|manifest|chunk)(?:/(0|[1-9][0-9]{0,2}))?$");
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,"0")).join("");
const sha=async x=>hex(await crypto.subtle.digest("SHA-256",enc.encode(x)));
function reply(status,data){return Response.json(data,{status,headers:{"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});}
function parse(request){
  const u=new URL(request.url),m=pathPattern.exec(u.pathname);
  if(!m||u.search)return null;
  const [,company,mission,snapshot,source_commit,hash,op,index]=m;
  if((op==="chunk")!==(index!==undefined))return null;
  const method=request.method;
  if(!((method==="GET"&&(op==="manifest"||op==="chunk"))||
       (method==="POST"&&(op==="reserve"||op==="commit"||op==="chunk"))))return null;
  return {id:{company,mission,snapshot,source_commit},hash,op,index:index===undefined?null:Number(index),scope:[company,mission,snapshot,source_commit].join("/")};
}
async function bounded(request){
  if(Number(request.headers.get("content-length")||0)>LIMIT)throw Error("size");
  if(!request.body)return "";
  const reader=request.body.getReader(),parts=[];let n=0;
  try{while(true){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;if(n>LIMIT){void reader.cancel().catch(()=>{});throw Error("size");}parts.push(value);}
    const all=new Uint8Array(n);let off=0;for(const x of parts){all.set(x,off);off+=x.byteLength;}
    return new TextDecoder("utf-8",{fatal:true}).decode(all);
  }finally{reader.releaseLock();}
}
function b64(c){let s="";for(let i=0;i<c.length;i+=8192)s+=String.fromCharCode(...c.subarray(i,i+8192));return btoa(s);}
function unb64(s){
  if(typeof s!=="string"||s.length>700000||!/^[A-Za-z0-9+/]+={0,2}$/.test(s))throw Error("invalid ciphertext");
  const c=Uint8Array.from(atob(s),x=>x.charCodeAt(0));
  if(b64(c)!==s)throw Error("noncanonical ciphertext");return c;
}
function exact(x,keys){return x&&typeof x==="object"&&!Array.isArray(x)&&Object.keys(x).sort().join(",")===keys;}
export async function handleNativeSnapshot(request,env){
  const p=parse(request);if(!p)return reply(404,{error:"route_not_found"});
  const secret=env?.PLENUM_NATIVE_SNAPSHOT_HMAC_SECRET;
  if(env?.PLENUM_PREVIEW_ONLY==="true"||env?.PLENUM_NATIVE_SNAPSHOT_ENABLED!=="true"||
     !env?.PLENUM_NATIVE_SNAPSHOT_STORE||typeof secret!=="string"||secret.length<32||secret.length>512||
     [env.PLENUM_PRIVATE_MEMORY_HMAC_SECRET,env.PLENUM_WEBHOOK_HMAC_SECRET,env.PLENUM_PAPERCLIP_CHECKPOINT_HMAC_SECRET].includes(secret)||
     env.PLENUM_NATIVE_SNAPSHOT_SCOPE!==p.scope)
    return reply(403,{error:"snapshot_scope_unavailable"});
  let raw;try{raw=await bounded(request);}catch{return reply(413,{error:"invalid_or_oversize_body"});}
  if(!await verifyPrivateRequest(request,secret,raw))return reply(403,{error:"unauthorized_or_stale"});
  if(request.method==="GET"&&raw!=="")return reply(400,{error:"invalid_body"});
  try{
    const object=env.PLENUM_NATIVE_SNAPSHOT_STORE.getByName("plenum-native-snapshot-budget-v1");
    return await object.fetch("https://native-snapshot.internal"+new URL(request.url).pathname,{
      method:request.method,...(request.method==="POST"?{body:raw,headers:{"Content-Type":"application/json"}}:{})});
  }catch{return reply(503,{error:"snapshot_storage_unavailable_no_automatic_replay"});}
}
// Only the bound internal Durable Object is intended to call this class.
// The public handler authenticates before obtaining the scoped object.
export class PaperclipSnapshotStore{
  constructor(ctx){this.storage=ctx.storage;}
  async fetch(request){
    const p=parse(request);if(!p)return reply(404,{error:"route_not_found"});
    try{
      if(request.method==="GET"){
        if(p.op==="manifest")return reply(200,await readManifest(this.storage,p.id,p.hash));
        return reply(200,{ciphertext:b64(await readChunk(this.storage,p.id,p.hash,p.index))});
      }
      const raw=await bounded(request),x=JSON.parse(raw);
      if(p.op==="reserve"){
        if(!exact(x,"manifest")||await sha(JSON.stringify(x.manifest))!==p.hash)throw Error("manifest binding");
        return reply(201,await reserveSnapshot(this.storage,p.id,x.manifest));
      }
      if(p.op==="chunk"){
        if(!exact(x,"ciphertext"))throw Error("invalid chunk");
        await storeChunk(this.storage,p.id,p.hash,p.index,unb64(x.ciphertext));return reply(201,{accepted:true});
      }
      if(!exact(x,""))throw Error("invalid commit");
      await commitSnapshot(this.storage,p.id,p.hash);return reply(201,{committed:true});
    }catch{return reply(409,{error:"snapshot_operation_rejected_no_automatic_replay"});}
  }
}
