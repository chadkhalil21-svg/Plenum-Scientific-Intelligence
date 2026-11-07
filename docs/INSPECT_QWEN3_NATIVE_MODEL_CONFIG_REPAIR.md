# Inspect ReAct original tool trace and native JSON model arguments

## Observed failures

Original ReAct run 42347377474 made one genuine Python sandbox tool call and
received a NameError. The next generation failed while rendering the frozen
Qwen3 tokenizer chat history; no independent functional score was recorded.
The original negative raw log was archived, never reclassified as a score.

Fix version one correctly rendered both flat Inspect and nested OpenAI tool
shapes using the actual frozen tokenizer, but run 42348424909 failed BEFORE
new model inference because Inspect CLI treated the raw Jinja as invalid YAML.

Fix version two used a JSON-quoted Jinja argument. Run 42348876440
successfully executed one new original model Python tool call, received
one sandbox NameError, and failed on the second turn with the same
unscored Jinja serialization TypeError.

The independently inspected ORIGINAL raw eval reveals the precise root:
Inspect CLI parsed model_args.chat_template as a LIST OF SIX STRINGS.
The original Jinja contains commas, so passing its full source using -M
split it into multiple model args values rather than one string.

Original source model Qwen/Qwen3-1.7B revision:
70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
Original release source commit:
6097cb3684459a3ed8c3f181477f548b5825fb45
Original unscored model trace SHA256:
104c928ca23178962446cf7fd929c7797dcd0618c8e2dfaa585394833b96037d

## The existing upstream solution

UK AISI Inspect has a documented --model-config JSON/YAML file capability.
Reuse it rather than building another agent, tokenizer, or framework:

1. Load the same frozen native Qwen tokenizer, verify the exact minimal
   previously reviewed tool-shape normalization block, with no model call.
2. Save the complete model args as a local JSON FILE with exactly
   model_path, cpu device, do_sample false, enable_thinking false, and
   chat_template containing the original patched Jinja as one STRING.
3. Reparse the JSON with both JSON and PyYAML. Require identical provider
   args and scalar string type, and independently verify actual tokenizer
   rendering of both real Inspect flat and native nested tool-call shapes.
4. Invoke the ORIGINAL Inspect eval with --model hf/local and
   --model-config reports/qwen3-react-model-config.json, never put any
   template contents in -M command-line arguments.
5. Independently archive the new negative original run 42348876440:
   original one tool call, one tool result, no original HumanEval grade.
6. If those checks pass, make only one bounded new CPU agent run with
   the original Inspect ReAct loop, Docker Python tool, one public HumanEval
   question, original independent functional scorer and separately
   recorded model/tool responses. Preserve every outcome, even failures.

Strict bounds: max 6 turns, 14 messages, 256 output tokens/turn,
20 seconds/tool, a networkless disposable Docker environment,
zero paid model API requests, no proprietary patents, model training,
automatic model promotion or production deployment. A template fix
is NOT a demonstration of AGI or autonomous code repair.

References:
- https://inspect.aisi.org.uk/reference/inspect_eval.html
- https://inspect.aisi.org.uk/providers.html
- https://huggingface.co/docs/transformers/chat_templating_writing
