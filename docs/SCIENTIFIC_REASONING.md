# Science reasoning and Qwen3 candidate training (v0.6)

## Independent benchmark
AI2 ARC-Challenge, Allen Institute for AI, CC-BY-SA-4.0. Data: https://huggingface.co/datasets/allenai/ai2_arc
Official test split pinned at revision 210d026faf9955653af8916fad021475a3f00453. Questions are fetched at runtime, not copied into this GitHub repository.
Base model Qwen/Qwen3-0.6B (Apache-2.0), pinned at revision c1899de289a04d12100db370d81485cdf75e47ca.
The benchmark deterministically selects 12 questions and reorders four answer choices using SHA-256. A fixed prompt asks for one answer letter. Next-token logits decide among A/B/C/D; the correct answer is never in the prompt as a label.
**Verified first run 42156895644:** 2/12 correct, 16.7%, versus nominal random guessing expectation of 25%. Twelve publicly available grade-school science questions are NOT a robust AGI, scientific research, or unseen-pretraining evaluation.

## Real but minimal model-weight training
The fine-tune-science command uses PEFT and PyTorch to update Qwen3 LoRA adapter weights, not the base weights, with exactly two predeclared CPU optimizer steps on original, public teaching examples.
The frozen ARC-Challenge test sample is not used for gradient updates or hyperparameter selection. The same eight reserved test questions are evaluated before and after training; a zero or negative difference is a valid outcome. There is no automated rerun to cherry-pick improvement.
Successful training saves adapter_model.safetensors, adapter_config.json and a manifest.json containing the model and dataset revisions, training-example checksum, Git commit, GitHub run ID and SHA-256 hashes.
GitHub Actions retains the candidate checkpoint for 14 days, **not indefinitely**. SHA-256 is an integrity checksum, not an authenticated signature. Candidate weights are never merged or deployed automatically.

## Known limitations and future experiments
ARC is public and could have been included in the foundation model's pretraining. This is a small fixed benchmark, not a blind test.
Two training steps and eight evaluation examples cannot support claims of generalized scientific reasoning improvement, original discovery, AGI or consciousness.
Longer-term work requires more independent questions, several domain-specific benchmarks, a genuinely blind evaluation set, licensing checks, a versioned private artifact registry, and a larger GPU-trained model when justified.

## GitHub actions
Independent Scientific Reasoning Benchmark: public model evaluation only.
Qwen3 Controlled LoRA Candidate Training: small CPU fine-tuning, SHA-256 checkpoint verification and paired evaluation.
No paid AI service is activated. This repository is public; do not include unpublished inventions, credentials, patient records or private research.

## Verified outcomes (2026-11-05)
- First ARC-Challenge evaluation: GitHub run 42156895644, Qwen3-0.6B 2/12 correct, logit letter scoring.
- Actual CPU Qwen3 LoRA training: GitHub run 42157269113, two AdamW gradient steps, 286,720 adapter parameters. Paired external 8-question science score 2/8 before and 2/8 after, **no measurable improvement**.
- Model candidate checkpoint SHA-256: 9d9a3e6105f4f340cfa10ca76584919f2fd8bf2c537c5e04ae1f32f099a173be, stored only in the expiring GitHub artifact; not deployed.
- The evaluation is very small and label-logit scoring may differ substantially from response-generation accuracy. Additional calibration is a priority before future comparisons.
