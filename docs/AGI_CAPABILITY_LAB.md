# Plenum AGI Capability Laboratory | Version 1

**Status: experimental benchmark, NOT an AGI system or AGI certification.**

The objective is to measure whether Plenum's open-weight models solve generated
unfamiliar task instances across intellectual areas and how many CPU-seconds
they consume. A green workflow means the evaluation ran correctly; it does
not mean the models passed its tasks.

## Three independently scored capability families

| Family | Tasks | Scoring |
|---|---|---|
| Mathematics | Modular arithmetic and linear equations | Independent exact numerical solutions |
| Quantitative science | Mechanics/work-energy and chemistry/dilution | Independently calculated physical answers |
| Restricted program synthesis | Linear and quadratic integer transforms | A small allowlisted arithmetic DSL tested on 28 extra inputs per task |

Six questions total, two per family, regenerated with a per-run seed. This
small benchmark is inadequate for an AGI classification or a statistically
reliable general-purpose ability score. The questions are synthetic textbook
tasks, not laboratory inventions or discoveries.

The programs are JSON data interpreted with strictly bounded add, multiply,
and square operations. They cannot access filesystem, shell, subprocess,
network, arbitrary Python, dynamic imports or outside tool calls. All 28 hidden program inputs are distinct from one another and from
public input/output examples. The scorer tests the same model program against
those inputs without adding any new instructions. This is
not full unrestricted programming.

## Two reviewed open-weight candidates

1. Qwen3-1.7B, revision 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e.
2. SmolLM2-1.7B-Instruct, revision 31b70e2e869a7173562077fd711b654946d38674.

Each receives exactly the same six tasks but no answer key. Immutable source
revisions must match before inference is accepted. GitHub CPU runners run
the evaluations, not paid model APIs. No automatic self-training, model
promotion, production deployment or generated-code execution occurs.

## Independent evaluation architecture

- Preparation: run offline regression tests, generate question-only manifest
  using GitHub Actions run ID as a seed, upload question data without solutions.
- Models: independent Qwen and SmolLM CPU jobs generate six replies each;
  preserve full source model revision, hashes, and elapsed inference time.
- Audit: a separate job independently regenerates all reference answers.
  Numeric responses are checked for mathematical correctness; arithmetic
  programs run through the strictly limited DSL interpreter on 28 additional
  integer inputs. All errors, refusals and invalid JSON count as failures.
- Ledger: a final job appends the prompts, the two original model outputs,
  numerical results, failure reasons and timing to the permanent public
  research-memory branch without altering previous experiments.

An evaluator, not the model, determines answer correctness.

## How to run from an iPad

GitHub > Plenum-Scientific-Intelligence > Actions >
AGI Capability Laboratory | Independent Generalization Check >
Run workflow.

The feature's initial main-branch merge starts one full experiment. Further
experiments are manually run with a fresh seed from each GitHub Actions run
ID. Pull requests run lightweight unit verification without loading the AI
models.

Local offline preflight:
    python -m plenum_ai.agi_capability_lab prepare --seed 12345 --out reports/tasks.json
    python -m unittest discover -s tests -p 'test_agi_capability_lab.py' -v

Do not submit confidential Plenum patents, private records or credentials to
a public GitHub Actions input or repository.

## What remains necessary for AGI

Measure correct/attempted, schema reliability, domain-level results,
restricted-program generalization, CPU inference time and total model calls.
These values must never be described as a percentage of AGI.

Next evaluations must include genuinely fresh unfamiliar problems,
long-horizon planning, software in a hardened sandbox, research-paper
provenance, real experimental design, evidence-based self-correction,
external human evaluation and independent adversarial benchmarks.

The objective is high verified capability per unit of computation, not the
number of models or workflows installed.
