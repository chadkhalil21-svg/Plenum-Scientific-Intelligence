// Run only in an authorized private runtime. No stdout secrets or archive data.
import {constants} from "node:fs";
import {lstat,open,link,unlink} from "node:fs/promises";
import {resolve,dirname,join} from "node:path";
import {randomUUID} from "node:crypto";
import {uploadArchive,downloadArchive} from "./paperclip-snapshot-client.mjs";
const MAX=256*1024*1024;
function require(ok){if(!ok)throw Error("Owner snapshot operation rejected");}
async function dir(p){const s=await lstat(p);require(s.isDirectory()&&s.uid===process.getuid()&&(s.mode&0o777)===0o700);}
async function read(p,max){await dir(dirname(p));const f=await open(p,constants.O_RDONLY|constants.O_NOFOLLOW|constants.O_NONBLOCK);try{const s=await f.stat();require(s.isFile()&&s.uid===process.getuid()&&(s.mode&0o777)===0o600&&s.size>0&&s.size<=max);const b=await f.readFile();require(b.length===s.size);return b;}finally{await f.close();}}
async function publish(p,b){await dir(dirname(p));const tmp=join(dirname(p),".snapshot-"+randomUUID());const f=await open(tmp,"wx",0o600);try{await f.writeFile(b);await f.sync();await f.close();await link(tmp,p);}finally{await f.close().catch(()=>{});await unlink(tmp).catch(()=>{});}}
async function absent(p){try{await lstat(p);throw Error("Existing output");}catch(e){if(e.code!=="ENOENT")throw e;}}
async function run(){
 require(process.env.GITHUB_ACTIONS!=="true"&&process.env.PLENUM_PERSISTENT_BOARD==="confirmed"&&process.argv.length===6);
 const [action,g,a,b]=process.argv.slice(2).map((x,i)=>i===0?x:resolve(x));require(["upload","download"].includes(action)&&new Set([g,a,b]).size===3);
 const grant=JSON.parse((await read(g,4096)).toString("utf8"));
 require(Object.keys(grant).sort().join(",")==="identity,key_hex,secret"&&typeof grant.key_hex==="string"&&/^[0-9a-f]{64}$/.test(grant.key_hex)&&typeof grant.secret==="string"&&grant.secret.length>=32&&grant.secret.length<=512);
 const key=new Uint8Array(Buffer.from(grant.key_hex,"hex"));
 await dir(dirname(b));await absent(b);
 // Upload input must be a consistent cold archive supplied by the authorized operator.
 // The private independent receipt must be retained separately from the backup store.
 if(action==="upload"){
  const raw=await read(a,MAX);const receipt=await uploadArchive(new Uint8Array(raw),key,grant.identity,grant.secret,fetch);
  await publish(b,Buffer.from(JSON.stringify(receipt)));console.log(JSON.stringify({action,receipt_written:true,manifest_sha256:receipt.manifest_sha256,paid_inference:false,model_calls_replayed:0,provider_calls_replayed:0}));
 }else{
  const receipt=JSON.parse((await read(a,8192)).toString("utf8"));
  const raw=await downloadArchive(receipt,key,grant.identity,grant.secret,fetch);await publish(b,raw);
  console.log(JSON.stringify({action,archive_restored:true,archive_sha256:receipt.archive_sha256,paid_inference:false,model_calls_replayed:0,provider_calls_replayed:0,native_database_restored:false}));
 }
}
run().catch(()=>{console.error("Owner snapshot operation failed closed; inspect private state without replaying an ambiguous write.");process.exitCode=1;});
