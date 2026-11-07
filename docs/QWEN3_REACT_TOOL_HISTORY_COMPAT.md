# Genuine ReAct tool call, unscored second-turn failure, and native Qwen3 repair

## What really happened

Original real Inspect ReAct run 42347377474 generated a Python tool call
on the official public HumanEval/0 function and received one real tool
response, a NameError for missing List import. The NEXT model generation
failed before any program was scored:

TypeError: Object of type Undefined is not JSON serializable

The original model transcript exists in GitHub Actions artifact 13563854739
and the exact original evaluation file SHA256 is:
c205cc78bf4cf341a6ea275ffd526ab6b2d24a3e7132bca4e1f68f0c427cce3d

Original sample is UNGRADED; no claim about code passing the tests is valid.
The Python sandbox tool was truly invoked once and returned once, but this
does not demonstrate successful autonomous code repair.

## Precise root cause

Inspect's actual tool call in the original .eval file was a flat dict:
function: "python", arguments: {code: "..."}.

The pinned Qwen3 tokenizer's native Jinja chat template has a branch
that treats a truthy tool_call.function as a nested object and replaces
the whole tool_call with it. The function name STRING becomes the
tool_call, so subsequent .arguments is Jinja Undefined, and the
template's tojson filter fails. The error is a provider/template shape
compatibility problem, not an independent HumanEval incorrect score.

## Reuse existing providers, preserve frozen weights

Inspect officially supports a Hugging Face chat_template override.
A narrow adapter loads the actual immutable model tokenizer, replaces
ONE recognized Jinja branch to accept both Inspect's flat tool shape
and the Qwen/OpenAI nested shape, and refuses template revisions
it cannot recognize. The rest of the ORIGINAL tokenizer template
is retained verbatim; weights are never edited or fine-tuned.

The PR verifies both shapes on the genuine original pretrained tokenizer
using synthetic harmless tool messages, without downloading model
weights or running inference. It independently archives the failed
original .eval and a negative factual report to research-memory.

After all zero-inference checks and archive succeed, a release-gated
single-repeat experiment may test the repaired rendering with one
HumanEval public question, maximum six turns and fourteen messages,
isolated Docker Python, and the official independent functional
scorer. Raw original corrected traces, including new failures, are
preserved separately, without auto-promotion or deployment.

Technical references:
- https://inspect.aisi.org.uk/providers.html#hugging-face
- https://huggingface.co/docs/transformers/chat_templating_writing
- https://github.com/huggingface/trl/issues/4881
- https://github.com/QwenLM/Qwen3/issues/1894

Limits: This is a formatting/serialization repair and an agent
integration test, not evidence of general intelligence, autonomous
programming reliability, proprietary discovery, or AGI.
