"""Generate original, reviewable program starters without deploying any code.

The foundry builds *small working starter applications*, not an AGI that can
invent arbitrary software. Arbitrary AI-generated code must enter a separate,
permission-restricted review pipeline with human approval and test isolation.
"""
from pathlib import Path
from hashlib import sha256
import json
import re

KINDS = ("research_cli", "data_validator", "geometry_designer")
TOPIC = re.compile(r"^[A-Za-z0-9 ,._()/-]{3,120}$")


def _scaffold(kind, topic):
    t = json.dumps(topic)
    if kind == "research_cli":
        return (
            '"""Original research metadata organizer (starter, no live provider)."""\n'
            'import argparse\nimport json\n'
            'from datetime import datetime, timezone\n'
            'def organize(title, sources):\n'
            '    if not isinstance(title, str) or not title.strip():\n'
            '        raise ValueError("Research question required")\n'
            '    if not isinstance(sources, list):\n'
            '        raise TypeError("Sources must be a list")\n'
            '    return {"question": title, "sources": sources, '
            '"citations_independently_verified": False}\n'
            'def main():\n'
            '    p=argparse.ArgumentParser()\n'
            f'    p.add_argument("--question", default={t})\n'
            '    args=p.parse_args()\n'
            '    print(json.dumps(organize(args.question, []), indent=2))\n'
            'if __name__=="__main__": main()\n'
        )
    if kind == "data_validator":
        return (
            '"""Original local scientific JSON validation starter."""\n'
            'import argparse\nimport json\nfrom pathlib import Path\n'
            'def validate(records):\n'
            '    if not isinstance(records, list):\n'
            '        raise TypeError("Expected a JSON list")\n'
            '    valid=[]\n'
            '    for row in records:\n'
            '        if not isinstance(row,dict):\n'
            '            continue\n'
            '        if isinstance(row.get("value"),(int,float)) and '
            'not isinstance(row.get("value"),bool):\n'
            '            valid.append(row)\n'
            '    return {"valid_rows": len(valid), "total_rows": len(records),'
            '"measurement_truth_verified": False}\n'
            'def main():\n'
            '    p=argparse.ArgumentParser()\n'
            '    p.add_argument("file",type=Path)\n'
            '    args=p.parse_args()\n'
            '    print(json.dumps(validate(json.loads(args.file.read_text())),indent=2))\n'
            'if __name__=="__main__":main()\n'
        )
    if kind == "geometry_designer":
        return (
            '"""Original deterministic SVG procedural study, not licensed artwork."""\n'
            'import argparse\nfrom pathlib import Path\nfrom html import escape\n'
            'def drawing(label):\n'
            '    if not isinstance(label,str) or len(label)>100:\n'
            '        raise ValueError("Invalid drawing topic")\n'
            '    circles="".join(f\'<circle cx="{x}" cy="100" r="{r}" '
            'fill="none" stroke="#2771a3" stroke-width="4"/>\' '
            'for x,r in [(100,60),(130,50),(160,40)])\n'
            '    return \'<svg xmlns="http://www.w3.org/2000/svg" '
            'width="320" height="240"><title>\'+escape(label)+'
            '\'</title>\'+circles+\'</svg>\'\n'
            'def main():\n'
            '    p=argparse.ArgumentParser()\n'
            f'    p.add_argument("--title",default={t})\n'
            '    p.add_argument("--out",type=Path,default=Path("drawing.svg"))\n'
            '    args=p.parse_args()\n'
            '    args.out.write_text(drawing(args.title),encoding="utf-8")\n'
            'if __name__=="__main__":main()\n'
        )
    raise ValueError("Unapproved starter kind")


def generate_program(kind, topic, out_dir):
    if kind not in KINDS:
        raise ValueError("Unknown reviewed program kind")
    if not isinstance(topic, str) or not TOPIC.fullmatch(topic.strip()):
        raise ValueError("Use a bounded public, non-executable program title")
    path = Path(out_dir)
    if path.exists():
        if path.is_symlink() or any(path.iterdir()):
            raise FileExistsError("Refuse to overwrite existing program files")
    path.mkdir(parents=True, exist_ok=True)
    program = _scaffold(kind,topic.strip())
    # Parse without executing any candidate code; catches invalid syntax.
    compile(program,"main.py","exec")
    (path/"main.py").write_text(program,encoding="utf-8")
    test = (
        "import importlib.util, unittest\n"
        "spec=importlib.util.spec_from_file_location('candidate','main.py')\n"
        "module=importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "class CandidateTests(unittest.TestCase):\n"
        + (
            "    def test_research_source_honesty(self):\n"
            "        self.assertFalse(module.organize('public research',[])['citations_independently_verified'])\n"
            if kind=="research_cli" else
            "    def test_numeric_records(self):\n"
            "        self.assertEqual(module.validate([{'value':1},{}])['valid_rows'],1)\n"
            if kind=="data_validator" else
            "    def test_original_svg(self):\n"
            "        self.assertIn('<svg',module.drawing('Original art'))\n"
        ) +
        "if __name__=='__main__':unittest.main()\n"
    )
    compile(test,"test_generated.py","exec")
    (path/"test_generated.py").write_text(test,encoding="utf-8")
    (path/"README.md").write_text(
        f"# {topic}\n\nOriginal starter program of kind \`{kind}\`.\n\n"
        "Run: \`python main.py --help\`\n\n"
        "Verify: \`python -m unittest discover -s . -p 'test_generated.py' -v\`\n\n"
        "Review source and licenses before publishing, networking, deployment or patent use.\n",
        encoding="utf-8")
    manifest={
        "schema":"plenum-reviewable-program-v1","kind":kind,
        "public_topic":topic.strip(),"file_count":3,
        "main_sha256":sha256(program.encode()).hexdigest(),
        "synthesis_method":"reviewed deterministic template, not autonomous generative AGI",
        "generated_program_has_not_been_deployed":True,
        "external_code_execution_approved":False,
        "model_weights_self_modified":False,
        "human_code_review_required":True,
    }
    (path/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest
