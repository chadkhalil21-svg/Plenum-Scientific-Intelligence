"""Optional pinned open-weight local CPU model. No paid API or arbitrary code tools."""
from functools import lru_cache

APPROVED_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"


@lru_cache(maxsize=1)
def _load_model(model_id):
    if model_id != APPROVED_MODEL:
        raise ValueError("Model not on the explicitly reviewed allowlist")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, trust_remote_code=False, use_safetensors=True
    ).to("cpu").eval()
    return tokenizer, model, torch


def hf_generate(prompt, model_id=APPROVED_MODEL):
    tokenizer, model, torch = _load_model(model_id)
    messages = [{"role": "user", "content": prompt[:3000]}]
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    batch = tokenizer(formatted, return_tensors="pt", truncation=True, max_length=1300)
    with torch.inference_mode():
        result = model.generate(
            **batch, max_new_tokens=80, do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    continuation = result[0][batch["input_ids"].shape[1]:]
    return tokenizer.decode(continuation, skip_special_tokens=True)
