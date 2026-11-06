"""Optional Ollama inference running on the user's own computer."""
import json
from urllib.request import Request, urlopen


def local_generate(prompt, model, opener=urlopen):
    if not model or len(model) > 120:
        raise ValueError("Provide a locally installed model name")
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"num_predict": 350}
    }).encode()
    req = Request(
        "http://127.0.0.1:11434/api/generate",
        data=body, headers={"Content-Type": "application/json"}
    )
    with opener(req, timeout=180) as response:
        payload = json.load(response)
    return payload.get("response", "")
