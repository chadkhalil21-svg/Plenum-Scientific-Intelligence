# Offline CMBAgent successor numeric claim grounding

Isolated reuse of the original, unmodified MIT-licensed `cmbagent_lg/researcher/grounding.py` from CMBAgents/cmbagent commit [bde10cb482357675fc747f8436895b1ed79b12b0](https://github.com/CMBAgents/cmbagent/tree/bde10cb482357675fc747f8436895b1ed79b12b0) (2026-11-16). The upstream module and LICENSE file retain their exact Git blobs 9d00e525d422d61eb3a2f3ede209847eb9edeaf4 and fc4ecf8b298d50c62310688515d5f2e0071c30e4 respectively. Source SHA256: 757beed7f7a2d48fa308804e17f5bfdf78f628e93afd065d30dcf51a60bf6ef9.

The successor package is `cmbagent_lg`, not the older `cmbagent` dependency of Denario. This is an independently usable deterministic component, not a Denario installation or implementation of the model-driven research chains. Standard library only; no package download, credentials, network, model or provider required.

From repository root, select one **public** JSON evidence artifact under `evidence/` and one or more atomic numeric statements:

    python integrations/upstream/cmbagent-lg-20261116/audit_claims.py --artifact evidence/fermilink/2026-11-17-tls/receipt.json --claim 'The original output contained 1000 rows.'

The adapter stages only the selected bounded file (256 KB maximum, no symlinks), emits coverage, source digest and the upstream grounded numeric tokens with their labels/line references. It does not mutate the source or execute text as code. At most 12 claims, 512 characters each. When coverage is incomplete, an absence is not exhaustive. Never equate an exact or approximate token match with semantic proof, causality, or scientific validity. Even labels may collide (the original receipt's Pe_min and Pe_max both equal 0.0001).

Original accepted public receipt audited once at Plenum main a2417a3dfb04db401979afc14ca11427a5136be1, not a new simulation. Full output: `evidence/cmbagent-lg/2026-11-17-fermilink/claim-grounding.json`. Three supported numeric claims matched; the explicitly counterfactual control 0.432198765 was absent; coverage 2471/2471 bytes. No paid calls, no AGI/discovery claim.

Denario v1.0.1 (GPLv3, pinned f6cc751603f2caed7524cc22b31652243c7b7c97) depends on legacy `cmbagent>=0.0.1post63`, while this official successor has a distinct distribution and a model factory configured only for Google, OpenAI and Anthropic by model name. Neither this adapter nor the current upstream model-factory source establishes an operational no-cost local Denario analysis backend.
