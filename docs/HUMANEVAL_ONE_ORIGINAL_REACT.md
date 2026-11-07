# A second original HumanEval function: previously incorrect, now test tools

The first genuinely agentic original Inspect ReAct CPU experiment
run 42349665865 scored one passing official HumanEval/0 function
after four actual Python-tool calls and four actual sandbox responses.
The raw transcript shows the model encountered missing-import
NameErrors, added the import, tested the code, and submitted a program
the original independent scorer marked correct. ONE historic function
is only a minimal tool-loop milestone, not AGI or broad software skill.

Our earlier ONE-SHOT frozen Qwen3-1.7B baseline scored 2/3:
HumanEval/0 passed, HumanEval/1 failed, HumanEval/2 passed.
The more informative test is now HumanEval/1, a different original
public function, preserving the exact upstream public prompt, source
test and frozen checkpoint from that recorded 2/3 reference.

Reuse WITHOUT building a new planner or grader:

- Upstream UK AISI Inspect ReAct, Python tool, and default isolated,
  networkless Docker with twenty-second tool timeout.
- Original Inspect Evals 0.27.0 HumanEval public source, unchanged
  verify() functional scorer and original sample ID HumanEval/1.
- Identical Qwen/Qwen3-1.7B checkpoint
  70d244cc86ccca08cf5af4e1e306ecf908b1ad5e.
- Native full JSON --model-config file, preserving the original
  reviewed flat-tool-call chat-template correction as ONE string.
- Six turns, fourteen messages, 256 tokens per model turn,
  one concurrent sample and sandbox, and a hard time ceiling.
- Zero paid model APIs, proprietary Plenum materials, production
  write permission, training, or automatic model promotion.

Before downloading the model, the runner verifies the first
one-shot 2/3 and ReAct 1/1 original independently scored JSON
records and all original raw .eval ZIP SHA256 checksums.

The run compares the earlier 0/1 one-shot outcome with the new
independent ReAct result, reporting real tool calls and tool
responses separately, and archives original errors and all
positive/negative outputs. Any failed task is a valid result:
there is no silent scorer change and no repeated inference to
search for a pass. This is an exploratory post-hoc test on one
known historical public question and cannot show generalization,
autonomous repository repair or AGI.

After this, prioritize original SWE-bench Verified/Terminal-Bench
repo-level tasks and prospective science reproduction using
existing reviewed agent and evaluator software.
