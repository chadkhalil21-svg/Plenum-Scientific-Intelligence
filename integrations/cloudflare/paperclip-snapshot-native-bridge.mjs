// Isolated synthetic native archive bridge; no live endpoint or public DB upload.
import assert from "node:assert/strict";
import {randomBytes,randomUUID,createHash} from "node:crypto";
import {readFile,writeFile,mkdtemp,rm,stat} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join,dirname} from "node:path";
import {fileURLToPath} from "node:url";
import {Miniflare} from "miniflare";
import {uploadArchive,downloadArchive} from "./paperclip-snapshot-client.mjs";
assert.equal(process.env.GITHUB_ACTIONS,"true");
assert.equal(process.env.GITHUB_RUN_ATTEMPT,"1");
assert.equal(process.env.PLENUM_SYNTHETIC_NATIVE_SNAPSHOT,"confirmed");
assert.equal(process.argv.length,6);
const [source,dest,company,mission]=process.argv.slice(2);
const info=await stat(source);assert(info.isFile()&&info.size>0&&info.size<255*1024*1024);
const id={company,mission,snapshot:randomUUID(),source_commit:process.env.GITHUB_SHA};
const key=new Uint8Array(randomBytes(32)),secret=randomBytes(32).toString("hex");
const root=dirname(fileURLToPath(import.meta.url)),persist=await mkdtemp(join(tmpdir(),"plenum-native-do-"));
const scope=[id.company,id.mission,id.snapshot,id.source_commit].join("/");
function runtime(){return new Miniflare({modules:true,scriptPath:join(root,"plenum-github-wake-worker.mjs"),compatibilityDate:"2026-07-01",durableObjects:{PLENUM_NATIVE_SNAPSHOT_STORE:{className:"PaperclipSnapshotStore",useSQLite:true}},durableObjectsPersist:persist,bindings:{PLENUM_NATIVE_SNAPSHOT_ENABLED:"true",PLENUM_NATIVE_SNAPSHOT_SCOPE:scope,PLENUM_NATIVE_SNAPSHOT_HMAC_SECRET:secret}});}
const sha=x=>createHash("sha256").update(x).digest("hex");
let mf;
try{
 const raw=new Uint8Array(await readFile(source));mf=runtime();
 const receipt=await uploadArchive(raw,key,id,secret,(url,init)=>mf.dispatchFetch(url,init));
 await mf.dispose();mf=runtime();
 const recovered=await downloadArchive(receipt,key,id,secret,(url,init)=>mf.dispatchFetch(url,init));
 assert.equal(sha(recovered),sha(raw));await writeFile(dest,recovered,{flag:"wx",mode:0o600});
 const proof={schema:"plenum-synthetic-native-encrypted-bridge-v1",...receipt,source_run_id:process.env.GITHUB_RUN_ID,actual_workerd_local:true,sqlite_persistence_across_instances:true,synthetic_data_only:true,live_cloudflare_verified:false,raw_database_uploaded:false,model_calls_replayed:0,provider_calls_replayed:0,paid_inference:false};
 await writeFile(dest+".receipt.json",JSON.stringify(proof),{flag:"wx",mode:0o600});
 console.log(JSON.stringify({schema:proof.schema,archive_sha256:proof.archive_sha256,manifest_sha256:proof.manifest_sha256,actual_workerd_local:true,synthetic_data_only:true,paid_inference:false}));
}finally{if(mf)await mf.dispose();key.fill(0);await rm(persist,{recursive:true,force:true});}
