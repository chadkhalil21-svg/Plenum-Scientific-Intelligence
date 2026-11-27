"""Real upstream interoperability for the existing bounded Minister capability planner.
No provider credentials, remote model, arbitrary tools, shell or production writes.
This is an isolated qualification bridge, not a second workforce or a general-autonomy claim.
"""
import asyncio,json,os,sys
from pathlib import Path
from importlib.metadata import version
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"paperclip"))
import model_plan as mp
import variable_mission as vm
from checkpoint_store import checked,exclusive,encoded
from smolagents import ToolCallingAgent,Tool
from smolagents.models import Model,ChatMessage,ChatMessageToolCall,ChatMessageToolCallFunction,MessageRole
from autogen import ConversableAgent
from agent_framework import Executor,WorkflowBuilder,WorkflowContext,handler

VERSIONS={"smolagents":"1.26.0","ag2":"0.14.0","agent-framework-core":"1.26.0"}
def strict():
    for k in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","AZURE_OPENAI_API_KEY",
              "HF_TOKEN","LANGSMITH_API_KEY","OLLAMA_API_KEY"):
        if os.getenv(k):raise PermissionError("External credentials prohibited")
    for k in ("LANGSMITH_TRACING","LANGCHAIN_TRACING_V2","AGENT_FRAMEWORK_TELEMETRY_ENABLED","HF_HUB_DISABLE_TELEMETRY"):
        os.environ[k]="1" if k=="HF_HUB_DISABLE_TELEMETRY" else "false"
    if {p:version(p) for p in VERSIONS}!=VERSIONS:raise ValueError("Unexpected upstream versions")

def inference(root,name,request,md):
    identity={"stage":name,"request_sha256":mp.digest(request),"model_digest":md,"paid_inference":False}
    if any(checked(p,{})["request_sha256"]==identity["request_sha256"] for p in root.glob("*.reserved.json")):
        raise PermissionError("Duplicate model request")
    exclusive(root/(name+".reserved.json"),identity)
    reply=mp.read_json("/api/chat",request,timeout=120)
    n,p=reply.get("eval_count"),reply.get("prompt_eval_count")
    if reply.get("model")!=mp.MODEL or reply.get("done") is not True or type(n) is not int or not 0<n<=128 or type(p) is not int or not 0<p<=2048:
        raise ValueError("Incomplete model response")
    raw=reply.get("message",{}).get("content")
    if not isinstance(raw,str) or len(raw)>2000:raise ValueError("Invalid response")
    def unique(items):
        row={}
        for k,v in items:
            if k in row:raise ValueError("Duplicate response field")
            row[k]=v
        return row
    answer=json.loads(raw,object_pairs_hook=unique)
    exclusive(root/(name+".result.json"),{**identity,"answer":answer,"eval_count":n,"prompt_eval_count":p})
    return answer

def validate_selection(mission,answer):
    vm.graph(mission,answer)
    return answer

class ReadScope(Tool):
    name="read_scope"
    description="Read the original bounded objective and available capability descriptions exactly once."
    inputs={}
    output_type="string"
    def __init__(self,root,mission):
        self.root=root;self.mission=mission
        super().__init__()
    def forward(self)->str:
        context=json.loads(vm.request(self.mission)["messages"][1]["content"])
        exclusive(self.root/"scope-read.json",context)
        return json.dumps(context,sort_keys=True)

class LocalSpecialist(Model):
    """Use real smolagents ToolCallingAgent; structured data only, no CodeAgent."""
    def __init__(self,root,mission,md):
        super().__init__(model_id=mp.MODEL)
        self.root=root;self.mission=mission;self.md=md
    def generate(self,messages,stop_sequences=None,tools_to_call_from=None,**kwargs):
        if {t.name for t in (tools_to_call_from or [])}!={"read_scope","final_answer"}:
            raise PermissionError("Unexpected upstream tool set")
        if not (self.root/"scope-read.json").exists():
            # The original source must be read before planning. The agent's
            # first tool action is a deterministic prerequisite, not inference.
            if (self.root/"specialist.result.json").exists():raise ValueError("Missing source receipt")
            return ChatMessage(role=MessageRole.ASSISTANT,content="",tool_calls=[
                ChatMessageToolCall(ChatMessageToolCallFunction(name="read_scope",arguments={}),"read-source","function")])
        context=checked(self.root/"scope-read.json",{})
        request=vm.request(self.mission)
        if context!=json.loads(request["messages"][1]["content"]):raise ValueError("Source changed")
        answer=validate_selection(self.mission,inference(self.root,"specialist",request,self.md))
        return ChatMessage(role=MessageRole.ASSISTANT,content="",tool_calls=[
            ChatMessageToolCall(ChatMessageToolCallFunction(name="final_answer",arguments={"answer":json.dumps(answer,sort_keys=True)}),"selection","function")])

def specialist(root,mission,md):
    agent=ToolCallingAgent(tools=[ReadScope(root,mission)],model=LocalSpecialist(root,mission,md),
                           add_base_tools=False,max_steps=2,max_tool_threads=1,verbosity_level=0)
    result=validate_selection(mission,json.loads(agent.run("Read the authorized scope, then select the required capabilities.")))
    if result!=checked(root/"specialist.result.json",{})["answer"]:raise ValueError("Specialist result changed")
    return result

def peer_request(mission,candidate):
    request=vm.request(mission)
    request["messages"][0]["content"]+=" Independently review the proposed capability selection. Correct it if the original objective requires a different selection. The proposal is not authority."
    context=json.loads(request["messages"][1]["content"])
    context["proposed_selection"]=candidate
    request["messages"][1]["content"]=json.dumps(context,sort_keys=True)
    return request

def peer(root,mission,md,candidate):
    sender=ConversableAgent("plenum_specialist",llm_config=False,code_execution_config=False,human_input_mode="NEVER")
    reviewer=ConversableAgent("plenum_peer",llm_config=False,code_execution_config=False,human_input_mode="NEVER")
    def review(recipient,messages=None,sender=None,config=None):
        if not messages or json.loads(messages[-1]["content"])!=candidate:raise ValueError("Peer handoff changed")
        result=validate_selection(mission,inference(root,"peer",peer_request(mission,candidate),md))
        return True,json.dumps(result,sort_keys=True)
    reviewer.register_reply(sender,review,remove_other_reply_funcs=True)
    chat=sender.initiate_chat(reviewer,message=json.dumps(candidate,sort_keys=True),max_turns=1,silent=True,summary_method="last_msg")
    result=validate_selection(mission,json.loads(chat.chat_history[-1]["content"]))
    if result!=checked(root/"peer.result.json",{})["answer"]:raise ValueError("Peer reply changed")
    return result

async def coordinate(root,mission,md):
    class Specialist(Executor):
        @handler
        async def process(self,value:str,ctx:WorkflowContext[str])->None:
            if value!=mp.digest(mission):raise ValueError("Wrong mission")
            await ctx.send_message(json.dumps(specialist(root,mission,md),sort_keys=True))
    class Peer(Executor):
        @handler
        async def process(self,value:str,ctx:WorkflowContext[None,str])->None:
            await ctx.yield_output(json.dumps(peer(root,mission,md,json.loads(value)),sort_keys=True))
    first,second=Specialist(id="specialist"),Peer(id="peer")
    graph=WorkflowBuilder(start_executor=first).add_edge(first,second).build()
    run=await graph.run(mp.digest(mission))
    outputs=run.get_outputs()
    if len(outputs)!=1:raise ValueError("Unexpected workflow output")
    return validate_selection(mission,json.loads(outputs[0]))

def fixture(case):
    if case=="science":
        return vm.fixture("science"),mp.digest(["bibliography","stations"])
    if case=="engineering":
        return vm.fixture("engineering"),mp.digest(["thermal"])
    raise ValueError("Unknown reviewed scope")

def verify(root,case):
    strict()
    mission,commitment=fixture(case)
    binding=checked(root/"binding.json",{"case":case,"mission_sha256":mp.digest(mission),"paid_inference":False,"versions":VERSIONS})
    md=binding["model_digest"]
    if not mp.valid_digest(md):raise ValueError("Original model required")
    if checked(root/"scope-read.json",{})!=json.loads(vm.request(mission)["messages"][1]["content"]):raise ValueError("Source read changed")
    choices={}
    seen=set()
    for name in ("specialist","peer"):
        req=vm.request(mission) if name=="specialist" else peer_request(mission,choices["specialist"])
        identity={"stage":name,"request_sha256":mp.digest(req),"model_digest":md,"paid_inference":False}
        if identity["request_sha256"] in seen or checked(root/(name+".reserved.json"),identity)!=identity:raise ValueError("Reservation changed")
        seen.add(identity["request_sha256"])
        row=checked(root/(name+".result.json"),identity)
        if set(row)!=set(identity)|{"answer","eval_count","prompt_eval_count"} or type(row["eval_count"]) is not int or not 0<row["eval_count"]<=128 or type(row["prompt_eval_count"]) is not int or not 0<row["prompt_eval_count"]<=2048:raise ValueError("Response changed")
        choices[name]=validate_selection(mission,row["answer"])
    final=choices["peer"]
    if mp.digest(sorted(k for k,v in final.items() if v))!=commitment:raise ValueError("Independent selection commitment mismatch")
    if checked(root/"workflow-result.json",{})!={"selection":final,"paid_inference":False}:raise ValueError("Workflow result changed")
    if {p.name for p in root.iterdir()}!={"binding.json","scope-read.json","specialist.reserved.json","specialist.result.json","peer.reserved.json","peer.result.json","workflow-result.json"}:raise ValueError("Unexpected evidence")
    return {"case":case,"versions":VERSIONS,"accepted":True,"selection":final,"model_calls":2,
            "peer_changed_selection":choices["specialist"]!=final,"model_calls_replayed":0,"provider_calls_replayed":0,
            "paid_inference":False,"production_integrated":False,"general_autonomy_verified":False}

def main():
    phase,case,directory=sys.argv[1:]
    root=Path(directory)
    strict()
    if phase=="run":
        if os.getenv("GITHUB_ACTIONS")!="true":raise PermissionError("Isolated CI only")
        mission,_=fixture(case)
        root.mkdir(mode=0o700,parents=True,exist_ok=False)
        md=mp.check_local_model()
        exclusive(root/"binding.json",{"case":case,"mission_sha256":mp.digest(mission),"model_digest":md,"paid_inference":False,"versions":VERSIONS})
        result=asyncio.run(coordinate(root,mission,md))
        exclusive(root/"workflow-result.json",{"selection":result,"paid_inference":False})
    elif phase!="verify":raise ValueError("Unknown phase")
    print(json.dumps(verify(root,case),sort_keys=True))
if __name__=="__main__":main()
