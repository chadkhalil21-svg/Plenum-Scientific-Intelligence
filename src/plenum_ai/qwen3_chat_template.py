"""Patch exactly one reviewed Qwen3 chat-template compatibility branch.

Original Inspect ReAct sample stored a flat function-name string plus args.
Qwen3 template expected a nested function map and raised Jinja Undefined.
Use the existing tokenizer and Inspect's chat_template model argument. Do
not change checkpoint weights, prompts, graders or raw evidence.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from .inspect_cross_domain import permitted_report
from .inspect_paired_qwen import MODEL,REVISION

SCHEMA="plenum-qwen3-chat-template-compat-v1"
BLOCK=re.compile(
    r"\{%-\s*if tool_call\.function\s*%\}\s*"
    r"\{%-\s*set tool_call = tool_call\.function\s*%\}\s*"
    r"\{%-\s*endif\s*%\}"
)
PATCH="""{%- if tool_call.function is string %}
{%- set tool_call = {'name': tool_call.function, 'arguments': tool_call.arguments} %}
{%- elif tool_call.function is mapping %}
{%- set tool_call = tool_call.function %}
{%- endif %}"""


def patch_template(original):
    if not isinstance(original,str) or not 100<len(original)<20000:
        raise ValueError("Original Qwen3 template missing or oversized")
    if any(v not in original for v in
           ("<tool_call>","tool_call.arguments","tool_call.name")):
        raise ValueError("Unrecognized original model tool template")
    revised,count=BLOCK.subn(lambda _: PATCH,original)
    if count!=1 or revised==original:
        raise ValueError("Original Qwen3 tool-history patch did not match exactly once")
    return revised


def validate_tokenizer(tokenizer_directory):
    from transformers import AutoTokenizer

    path=Path(tokenizer_directory)
    if not path.is_dir():
        raise ValueError("Frozen local tokenizer snapshot missing")
    tokenizer=AutoTokenizer.from_pretrained(str(path),local_files_only=True)
    origin=tokenizer.chat_template
    revised=patch_template(origin)
    tools=[{"type":"function","function":{
        "name":"python","description":"Execute isolated Python",
        "parameters":{"type":"object","properties":{"code":{"type":"string"}},
                      "required":["code"]}}}]
    tool_shapes=[
        {"type":"function","function":"python","arguments":{"code":"print(2+2)"}},
        {"type":"function","function":{"name":"python","arguments":{"code":"print(2+2)"}}},
    ]
    for shape in tool_shapes:
        conversation=[
            {"role":"system","content":"sandbox only"},
            {"role":"user","content":"try code"},
            {"role":"assistant","content":"","tool_calls":[shape]},
            {"role":"tool","content":"4","name":"python"},
        ]
        rendered=tokenizer.apply_chat_template(
            conversation,tokenize=False,chat_template=revised,
            tools=tools,add_generation_prompt=True,enable_thinking=False)
        if any(required not in rendered for required in
               ("<tool_call>","python","print(2+2)","<tool_response>","4")):
            raise ValueError("Original Qwen model tool call or response lost")
    return ({
        "schema":SCHEMA,"model":MODEL,"model_revision":REVISION,
        "original_template_sha256":sha256(origin.encode()).hexdigest(),
        "patched_template_sha256":sha256(revised.encode()).hexdigest(),
        "original_flat_inspect_tools_render":True,
        "original_nested_tools_render":True,
        "tokenizer_render_verified":True,
        "model_weights_modified":False,"local_model_calls":0,
        "paid_api_calls":0,"AGI_demonstrated":False,
    },revised)


def plan():
    return {
        "schema":SCHEMA,"model":MODEL,"model_revision":REVISION,
        "tokenizer_render_verified":False,
        "model_weights_modified":False,"local_model_calls":0,
        "paid_api_calls":0,"AGI_demonstrated":False,
        "limitations":"Template render compatibility is not autonomous reasoning or AGI.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--model-path")
    parser.add_argument("--template-out")
    parser.add_argument("--out",default="reports/qwen3-template-check.json")
    args=parser.parse_args()
    out=permitted_report(args.out)
    if args.model_path:
        if args.template_out!="reports/qwen3-react-template.jinja":
            raise ValueError("Only reviewed temporary template path supported")
        report,rendered=validate_tokenizer(args.model_path)
        p=Path(args.template_out)
        if p.is_symlink():
            raise ValueError("Disallow output symlinks")
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(rendered,encoding="utf-8")
    else:
        report=plan()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("Qwen3 original tool-history template render:",
          report["tokenizer_render_verified"],"model calls",report["local_model_calls"])


if __name__=="__main__":
    main()
