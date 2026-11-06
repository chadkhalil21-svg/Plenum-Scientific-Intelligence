"""Optional openly licensed local CPU model. No paid API or unrestricted tools."""
from functools import lru_cache

APPROVED_MODEL = "Qwen/Qwen3-0.6B"
APPROVED_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"


@lru_cache(maxsize=1)
def _load_model(model_id):
    if model_id != APPROVED_MODEL:
        raise ValueError("Model not on the explicitly reviewed allowlist")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=APPROVED_REVISION, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=APPROVED_REVISION, trust_remote_code=False, use_safetensors=True
    ).to("cpu").eval()
    return tokenizer, model, torch


def hf_generate(prompt, model_id=APPROVED_MODEL):
    tokenizer, model, torch = _load_model(model_id)
    messages = [{"role": "user", "content": prompt[:3500]}]
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
        enable_thinking=False
    )
    batch = tokenizer(formatted, return_tensors="pt", truncation=True, max_length=1600)
    with torch.inference_mode():
        result = model.generate(
            **batch, max_new_tokens=180, do_sample=False,
            repetition_penalty=1.15, no_repeat_ngram_size=4,
            pad_token_id=tokenizer.eos_token_id
        )
    continuation = result[0][batch["input_ids"].shape[1]:]
    return tokenizer.decode(continuation, skip_special_tokens=True).strip()
