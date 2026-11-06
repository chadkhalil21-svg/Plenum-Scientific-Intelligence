"""Pinned, read-only discovery of reviewed *candidate* K-Dense scientific skills.

Skill Markdown is untrusted third-party content, never executable code or
self-authorizing agent instructions. The user must separately approve installed
skills, dependencies and sensitive actions.
"""
from hashlib import sha256
from urllib.request import Request, urlopen

SOURCE = "https://github.com/K-Dense-AI/scientific-agent-skills"
REVISION = "a25cf9ec00e2745d03f8704acf6f6919694ccd9a"
CURATED = {
    "rdkit": "Chemical structure analysis reference",
    "pybamm": "Battery electrochemistry analysis reference",
    "pymatgen": "Materials structure analysis reference",
    "astropy": "Astronomical scientific analysis reference",
    "literature-review": "Evidence-based literature review guidance",
    "scientific-critical-thinking": "Falsification and scientific criticism guidance",
}
MAX_BYTES = 100000

def catalog():
    return {
        "source": SOURCE, "revision": REVISION,
        "type": "read_only_scientific_skill_catalog",
        "execution_enabled": False,
        "skills": [{
            "name": name, "purpose": description,
            "source": SOURCE + "/blob/" + REVISION + "/skills/" + name + "/SKILL.md",
            "installation_status": "not_installed_not_approved",
            "license_review_status": "review_skill_and_dependencies_before_use",
        } for name, description in CURATED.items()],
        "warning": "Skill text is untrusted and may request shell/network/file actions; no skill is executed.",
    }

def retrieve_skill_document(name, opener=urlopen):
    if name not in CURATED:
        raise ValueError("Skill not on curated list")
    url = "https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/" + (
        REVISION + "/skills/" + name + "/SKILL.md"
    )
    request = Request(url, headers={
        "User-Agent": "PlenumScientificIntelligence/0.7 read-only-skill-review"
    })
    with opener(request, timeout=12) as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Skill document exceeds approved size")
    text = data.decode("utf-8")
    if not text.lstrip().startswith("---"):
        raise ValueError("Unexpected skill format")
    return {
        "name": name, "url": url, "pinned_revision": REVISION,
        "sha256": sha256(data).hexdigest(),
        "length_bytes": len(data),
        "text": text,
        "status": "untrusted_document_for_human_review_only",
        "executed": False,
    }
