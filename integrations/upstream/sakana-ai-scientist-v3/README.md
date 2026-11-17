# Sakana AI Scientist v3: fixed scientific evaluator

This opt-in integration preserves the original CPU circle-packing evaluator and
its bundled baseline from the [official repository at the reviewed commit](https://github.com/SakanaAI/AI-Scientist-v3/tree/de1cd267b8922faa31631fb397bbc202bf714d84).
Copyright 2026 Sakana AI. The three upstream Python files are unmodified and
distributed under the adjacent original Apache-2.0 LICENSE. No upstream NOTICE
file was present at this commit. See the [original paper](https://arxiv.org/abs/2610.18933).

The wrapper verifies all three source hashes before copying the reviewed bytes
into a new temporary directory. It accepts no candidate, output path or user
prompt. It passes only the fixed upstream arguments and a minimal child-process
environment, uses one BLAS/OMP thread and imposes a 25-second timeout. It does not
instantiate an agent, download a model, invoke an API, use a GPU or perform an
external account operation. A cleared environment and temporary directory are not
an operating-system security sandbox; never substitute generated or untrusted
programs.

From the original Plenum checkout, verify the source without executing it:

```sh
python integrations/upstream/sakana-ai-scientist-v3/run_fixed_baseline.py --verify-only
```

Only when this exact capability is needed on a host with an existing NumPy
installation, explicitly execute the fixed baseline and receive a JSON receipt:

```sh
python integrations/upstream/sakana-ai-scientist-v3/run_fixed_baseline.py --run
```

No dependency is added to the default runtime; NumPy is already an optional
Plenum numerical dependency. The original evaluation needs no GPU, model or paid
service. The upstream task's example requirements pin NumPy 2.4.2 and SciPy
1.17.1; the previous acceptance used installed NumPy 2.3.5 and SciPy 1.17.0, with
no installs (the three source files only import NumPy).

## Evidence

The existing `baseline_receipt.json` records the original, real one-time
execution in local scratch on November 16, 2026 (ET), before this adapter was
added. It passed Sakana's own evaluator with a score of
0.9597642169962064. It is a baseline result, not a new candidate, new discovery,
or proof of 26 strictly positive radii: two radii were zero and the upstream
validator allows this. It does not establish the full Agentic Scientist
pipeline, autonomous research, or AGI. The adapter's scope is only the exact
reviewed evaluator and the exact fixed baseline.

Do not repeat the baseline for demonstration. The narrow boundary check
`python integrations/upstream/sakana-ai-scientist-v3/test_runner.py` verifies
source hashing, arbitrary-input rejection and fail-closed tampering without
running the original evaluation.
