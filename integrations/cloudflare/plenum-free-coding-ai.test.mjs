import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import {verifyOriginalGithubOIDC, handleFreeCodingAI} from "./plenum-free-coding-ai.mjs";
import {PublicWakeReplayGuard} from "./plenum-github-wake-worker.mjs";

const REPO="chadkhalil21-svg/Plenum-Scientific-Intelligence";
const enc=x=>Buffer.from(JSON.stringify(x)).toString("base64url");

test("original GitHub OIDC issuer signature audience workflow and main-ref are verified", async()=>{
  const now=Math.floor(Date.now()/1000);
  const pair=await webcrypto.subtle.generateKey({
    name:"RSASSA-PKCS1-v1_5",modulusLength:2048,
    publicExponent:new Uint8Array([1,0,1]),hash:"SHA-256"
  },true,["sign","verify"]);
  const jwk=await webcrypto.subtle.exportKey("jwk",pair.publicKey);
  const header=enc({alg:"RS256",kid:"original-ci-kid"});
  const payload={iss:"https://token.actions.githubusercontent.com",aud:"plenum-original-public-coder",
    repository:REPO,
    repository_owner_id:"251133044",repository_id:"1447724141",
    sub:"repo:chadkhalil21-svg@251133044/Plenum-Scientific-Intelligence@1447724141:ref:refs/heads/main",
    workflow_ref:REPO+"/.github/workflows/business-workforce-runtime.yml@refs/heads/main",
    event_name:"issues",iat:now-1,exp:now+240};
  async function sign(p) {
    const message=header+"."+enc(p);
    const signature=await webcrypto.subtle.sign("RSASSA-PKCS1-v1_5",pair.privateKey,new TextEncoder().encode(message));
    return message+"."+Buffer.from(signature).toString("base64url");
  }
  const fetcher=async()=>Response.json({keys:[{...jwk,kid:"original-ci-kid",alg:"RS256",use:"sig"}]});
  assert.equal(await verifyOriginalGithubOIDC(await sign(payload),{now,fetcher}),true);
  for(const modified of [
    {...payload,aud:"other"},
    {...payload,repository:"untrusted/other"},
    {...payload,sub:"repo:"+REPO+":ref:refs/heads/main"},
    {...payload,repository_id:"999999999"},
    {...payload,repository_owner_id:"999999999"},
    {...payload,workflow_ref:"attacker/repo/.github/workflows/job.yml@refs/heads/main"},
    {...payload,event_name:"pull_request"},
    {...payload,exp:now-1},
  ]) assert.equal(await verifyOriginalGithubOIDC(await sign(modified),{now,fetcher}),false);
  const forged=(await sign(payload)).slice(0,-9)+"forgedabc";
  assert.equal(await verifyOriginalGithubOIDC(forged,{now,fetcher}),false);
});

test("existing free model binding accepts only original signed public issue worker, never writes code",async()=>{
  let calls=0;
  const env={
    PLENUM_FREE_AI_ENABLED:"true",
    AI:{async run(model,args){calls++;assert.equal(model,"@cf/zai-org/glm-4.7-flash");
      assert.equal(args.max_tokens,512);
      return {response:"Read-only reviewed patch proposal",usage:{prompt_tokens:15,completion_tokens:7,total_tokens:22}};
    }},
    PLENUM_REPLAY_GUARD:{getByName:()=>({fetch:async()=>new Response(null,{status:204})})},
  };
  function request(body) {
    return new Request("https://plenum-public-wake.example/ai/v1/chat/completions",{
      method:"POST",headers:{"Authorization":"Bearer "+"z".repeat(450),"Content-Type":"application/json"},
      body:JSON.stringify(body)});
  }
  const task={model:"glm-4.7-flash",messages:[{role:"user",content:"Edit only public copied source"}],max_tokens:512};
  const noAuth=await handleFreeCodingAI(request(task),env);
  assert.equal(noAuth.status,403);assert.equal(calls,0);
  const valid=await handleFreeCodingAI(request(task),env,{verifier:async()=>true});
  assert.equal(valid.status,200);
  const result=await valid.json();assert.equal(result.choices[0].message.content,"Read-only reviewed patch proposal");
  assert.equal(result.usage.total_tokens,22);assert.equal(calls,1);
  const stream=await handleFreeCodingAI(request({...task,stream:true}),env,{verifier:async()=>true});
  assert.equal(stream.status,200);assert.match(await stream.text(),/data: \[DONE\]/);
  assert.equal(calls,2);
  // The live OpenHands/LiteLLM request can send n:null, developer content
  // and assistant tool-call messages without a content property.
  const sdkDefaults={...task,n:null,tools:null,messages:[
    {role:"developer",content:"PUBLIC reviewed code only"},
    {role:"assistant",tool_calls:[{id:"call_1",type:"function",function:{name:"file_editor",arguments:"{}"}}]},
    {role:"tool",content:"File contents inspected",tool_call_id:"call_1"}
  ]};
  const compatible=await handleFreeCodingAI(request(sdkDefaults),env,{verifier:async()=>true});
  assert.equal(compatible.status,200);
  assert.equal(calls,3);
  const multi=await handleFreeCodingAI(request({...task,n:2}),env,{verifier:async()=>true});
  assert.equal(multi.status,400);assert.equal(calls,3);
  const oversizeMessages=await handleFreeCodingAI(request({...task,messages:Array(65).fill({role:"user",content:"a"})}),env,{verifier:async()=>true});
  assert.equal(oversizeMessages.status,400);assert.equal(calls,3);
  const unbound=await handleFreeCodingAI(request(task),{...env,AI:undefined},{verifier:async()=>true});
  assert.equal(unbound.status,503);assert.equal(calls,3);
  const untrusted=await handleFreeCodingAI(request({...task,model:"openai/gpt-paid"}),env,{verifier:async()=>true});
  assert.equal(untrusted.status,400);assert.equal(calls,3);
});

test("existing replay guard atomically bounds native AI budget per UTC day",async()=>{
  const storage=new Map();
  const guard=new PublicWakeReplayGuard({storage:{transaction:async fn=>fn({
    get:async key=>storage.get(key),put:async(k,v)=>storage.set(k,v)
  })}});
  const day=new Date().toISOString().slice(0,10);
  const req=()=>new Request("https://replay-guard.internal/claim-ai",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({day,reserve:200,maximum:4000})});
  for(let n=0;n<20;n++)assert.equal((await guard.fetch(req())).status,204);
  assert.equal((await guard.fetch(req())).status,429);
  assert.equal(storage.get("free-original-ai:"+day),4000);
  const wrong=()=>new Request("https://replay-guard.internal/claim-ai",{
    method:"POST",body:JSON.stringify({day,reserve:0,maximum:4000})});
  assert.equal((await guard.fetch(wrong())).status,429);
});


test("native incomplete or inconsistent cloud completions never become successful stops or partial tool calls",async()=>{
  let response;
  let calls=0;
  const env={PLENUM_FREE_AI_ENABLED:"true",AI:{async run(){calls++;return response;}},
    PLENUM_REPLAY_GUARD:{getByName:()=>({fetch:async()=>new Response(null,{status:204})})}};
  const tool={id:"call_1",function:{name:"file_editor",arguments:"{}"}};
  const invoke=stream=>handleFreeCodingAI(new Request("https://example.invalid/ai/v1/chat/completions",{
    method:"POST",headers:{"Authorization":"Bearer "+"z".repeat(450),"Content-Type":"application/json"},
    body:JSON.stringify({model:"glm-4.7-flash",messages:[{role:"user",content:"Public task"}],stream})}),env,{verifier:async()=>true});
  for (const invalid of [
    {choices:[{finish_reason:"length",message:{content:"partial"}}]},
    {finish_reason:"content_filter",response:"partial"},
    {choices:[{finish_reason:"tool_calls",message:{content:"missing tools"}}]},
    {choices:[{finish_reason:"stop",message:{tool_calls:[tool]}}]},
    {finish_reason:"unrecognized",response:"partial"},
    {tool_calls:Array(9).fill(tool)},
  ]) {
    response=invalid;
    for(const stream of [false,true]) {
      const rejected=await invoke(stream);
      assert.equal(rejected.status,502);
      assert.equal((await rejected.json()).error.message,"free_model_unavailable_or_invalid_result");
    }
  }
  assert.equal(calls,12);
  response={choices:[{finish_reason:"tool_calls",message:{tool_calls:[tool]}}]};
  const valid=await invoke(false);
  assert.equal(valid.status,200);
  assert.equal((await valid.json()).choices[0].finish_reason,"tool_calls");
  response={choices:[{finish_reason:"stop",message:{content:"complete"}}]};
  const stopped=await invoke(true);
  assert.equal(stopped.status,200);
  assert.match(await stopped.text(),/"finish_reason":"stop"/);
});
