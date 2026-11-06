# Plenum v0.8: Battery Electrochemical Modeling

## Working scientific solver
**PyBaMM 26.10.1.1**, BSD-licensed electrochemical battery modeling software.

This project now runs actual PyBaMM **Single Particle Model (SPM)** and
**Single Particle Model with Electrolyte (SPMe)** default lithium-ion simulations
for a fixed 10-minute constant-current discharge interval.

Published upstream docs:
https://docs.pybamm.org/en/pybamm-v26.10.1.1/source/examples/notebooks/models/SPM.html

## Verified results (GitHub run 42160642565)

| Model | Initial voltage | Final voltage | Voltage drop | Saved points |
|---|---:|---:|---:|---:|
| SPM | 3.780081 V | 3.710364 V | 0.069716 V | 42 |
| SPMe | 3.770813 V | 3.691442 V | 0.079372 V | 50 |

The output is numerically bounded and both computed discharge profiles end
at lower voltages than they began.

**These are model predictions, not measured cell data.** The repository does
not yet reproduce or evaluate Plenum's unpublished solid-state battery design.
Model agreement is not independent proof of cell properties.

## Next experimental research
1. Select actual battery chemistries and parameter sets with documented
   measurement provenance.
2. Use appropriately licensed public independent discharge-curve datasets.
3. Fix parameters and training data before examining reserved measurements.
4. Compare predictions with empirical voltage, temperature, degradation,
   cycling and safety data, reporting uncertainty and model limitations.
5. Require expert review before any claim about energy density, lifespan,
   fast charging, thermal safety or manufacturability.

## Reproduce
```sh
python -m pip install -e ".[battery]"
plenum battery-simulation --minutes 10 --out reports/battery_simulation.json
```

Run `PyBaMM Battery Electrochemistry Demonstration` from the GitHub Actions
tab to reproduce on public CPU runners without a paid model API. The report
artifact is retained for 14 days.
