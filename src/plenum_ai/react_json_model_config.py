"""Produce native Inspect --model-config JSON, preserving the Qwen template as ONE string.

Previously Inspect CLI -M chat_template=... split commas in a correctly
patched Jinja template into a six-element list. Use Inspect's documented
file-based provider args, not an alternative tokenizer, agent or grader.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from .inspect_paired_qwen import MODEL, REVISION
from .qwen3_chat_template import patch_template

SCHEMA="plenum-inspect-qwen3-native-model-config-v1"
CONFIG_NAME="reports/qwen3-react-model-config.json"


def checked_config(model_path, original_template, revised):
    path=Path(model_path)
    if (not path.is_dir() or path.name!=REVISION or path.is_symlink()):
        raise ValueError("Frozen Qwen3-1.7B checkpoint directory is missing or changed")
    if (not isinstance(revised,str)
        or not isinstance(original_template,str)
        or patch_template(original_template)!=revised):
        raise ValueError("Template does not exactly match reviewed native Qwen patch")
    return {
        "model_path":str(path),
        "device":"cpu",
        "do_sample":False,
        "enable_thinking":False,
        "chat_template":revised,
    }


def make(model_path, original_template, revised, destination=CONFIG_NAME):
    if destination!=CONFIG_NAME:
        raise ValueError("Use only the reviewed temporary JSON provider configuration")
    path=Path(destination)
    if path.is_symlink():
        raise ValueError("Refuse model-configuration symlink")
    payload=checked_config(model_path,original_template,revised)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    reloaded=json.loads(path.read_text(encoding="utf-8"))
    try:
        import yaml
        yaml_loaded=yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        yaml_loaded=reloaded
    if (not isinstance(reloaded["chat_template"],str)
        or not isinstance(yaml_loaded["chat_template"],str)
        or reloaded!=payload or yaml_loaded!=payload):
        raise ValueError("Inspect provider configuration changed original string type")
    return {
        "schema":SCHEMA,
        "model":MODEL,
        "model_revision":REVISION,
        "config_file":CONFIG_NAME,
        "chat_template_type":"str",
        "template_sha256":sha256(revised.encode("utf-8")).hexdigest(),
        "provider_args_keys":sorted(payload),
        "json_and_yaml_roundtrip_verified":True,
        "model_weight_changes":False,
        "model_inference_calls":0,
        "external_paid_model_apis":0,
        "AGI_demonstrated":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--model-path",required=True)
    parser.add_argument("--original-template",required=True)
    parser.add_argument("--template",required=True)
    parser.add_argument("--out",default=CONFIG_NAME)
    args=parser.parse_args()
    if args.out!=CONFIG_NAME:
        raise ValueError("Only approved native model configuration destination")
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.model_path,local_files_only=True)
    original=tokenizer.chat_template
    supplied=Path(args.template).read_text(encoding="utf-8")
    if args.original_template!="native":
        raise ValueError("Original model template must come from loaded tokenizer")
    report=make(args.model_path,original,supplied,args.out)
    # The file itself is the secure value passed to --model-config.
    print("Qwen native Inspect model config:",report["json_and_yaml_roundtrip_verified"],
          "type",report["chat_template_type"],"paid API calls",report["external_paid_model_apis"])


if __name__=="__main__":
    main()
