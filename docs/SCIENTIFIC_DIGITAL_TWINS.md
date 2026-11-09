# Plenum Prometheus: Digital twins across physical, biological and engineered sciences

**Founder directive (November 8, 2026):** Scientific intelligence must reason about, simulate, predict and test the real world across **all disciplines**, including the living world. Always adopt the best maintained upstream solver for a *specific problem* rather than constructing a universal homegrown simulator. This inventory is source-reviewed **candidate software**, not a claim of installed or operational twins. Main policy: [LEDGER](LEDGER.md).

## Credibility levels (do not blur)

- **Reference model**: validated numerical execution against an equation or fixed synthetic fixture. Already established for several Plenum solvers.
- **Observation-linked model / shadow**: measured data ingested and compared with or sequentially assimilated into a defined virtual state. The June 2025 NOAA retrospective pilot **ran against actual NOAA data** ([run #42557644772](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42557644772)) at this *historical replay level only*.
- **Research digital twin**: real counterpart, repeatable verified data synchronization at a stated cadence, quality flags, uncertainty estimates, recalibration process and independently demonstrated prospective predictive value against strong competing forecasts. **Not yet achieved**.
- **Operational digital twin**: deployed measurement and prediction pipeline with monitoring, realistic interventions, validated limits, access controls, incident response and ongoing validation for its actual use. **Not achieved**.
- **Action-conditioned causal world model / AGI**: an additional independent research question. A frozen simulator, twin, or pretrained JEPA representation alone does not establish causal comprehension, AGI or ASI.

NIST foundational definitions, essential elements and VVUQ: https://www.nist.gov/digital-twins/definitions-and-state-art , https://www.nist.gov/digital-twins/essential-elements , https://www.nist.gov/publications/credibility-consideration-digital-twins-manufacturing .

## Domain-specific upstream shortlist and appropriate real-world evidence

| Domain | Established reusable engine / source | Observations necessary for a true twin | Adoption decision |
|---|---|---|---|
| Coastal oceans, tides, flood exposure | **Existing** NOAA CO-OPS and Plenum harmonics; future NOAA operational model/forecast products, open hydrodynamic engines only after benchmark | Actual gauge heights, atmospheric forcing, QC, spatial validation and strong NOAA forecast baseline | **First** low-cost historical shadow pilot; no new engine |
| Forage, grasses, crop yield, plant ecophysiology | **PCSE** with LINGRA grassland, WOFOST crop and LINTUL; alternative **BioCro** plant physiology | Weather, soil water, nutrients, irrigation/harvest management and independently sampled biomass/leaf area | **Second science trial candidate**, especially LINGRA with actual grassland field measurements; review license and dataset match |
| Plant form, roots, light interception | **OpenAlea** PlantGL/L-Py/MTG functional-structural plant frameworks | Phenotyping images, root traits, spatial light/soil conditions and time-series measurements | Use only for a morphology question absent in PCSE |
| Agricultural production and ecosystem flux | **APSIM Next Gen** or **DSSAT** crop and soil models | Soil layers, field management, yield, climate, emissions | Alternatives after source/model-specific licenses checked; do not install both by default |
| Molecular mechanisms and proteins | Existing **OpenMM**, **RDKit**, **PySCF**; candidate DiffDock for separate docking experiment | Assay binding, kinetics, structures and experimental replicates | Reuse existing molecular solvers; binding prediction is not efficacy |
| Cell metabolism, biochemistry, microbiomes | **COBRApy** (metabolic flux), **COPASI** or **Tellurium/libRoadRunner** (SBML reaction networks) | Metabolomics, biomass, enzyme rate measurements, interventions and species/culture validation | One mechanistic target at a time; no unverified clinical or biochemical claim |
| Multi-cell tissues and biomedical physiology | **PhysiCell** for cellular interactions, other organ-specific specialist models as needed | Time-lapse microscopy, histology, lineage and treatment response | Candidate only; clinical validation/privacy separate |
| Aerodynamics, aerospace | Existing NASA **Aviary/OpenMDAO**; choose **SU2** or **OpenFOAM** only for CFD question | Wind tunnel, pressure distributions, forces, flight measurements | Use existing verified aircraft sample; no false flight certification |
| Robotics and embodied learning | **MuJoCo** first, **Isaac Lab** only for GPU-scale sensor/robotics | Robot trajectories, joint torques, visual observations and intervention data | Conditional upstream, not installed |
| Buildings, infrastructure, construction | DOE **EnergyPlus** for whole-building thermo-energy, specialist structural solvers for stress | Sensors for temperature, energy, humidity, load/strain and maintenance | Upstream-first once actual measured asset selected |
| Energy storage and grids | Existing **PyBaMM**; **pandapower** for power networks | Cell cycles, temperatures, capacity fade, current/voltage and grid metering | Separate measured battery and network experiments |
| Photonics and electromagnetic systems | **Meep** FDTD (GPL) and existing specialized numerical tools | Wavelength-calibrated optical spectra, radiometry, physical device measurements | Review suitability and license before any design simulation |
| Climate, hydrology, earth systems | Existing NOAA/USGS prospective studies, open data, scientifically maintained model packages | Real river flow, coastal levels, satellite, soil/weather observations | Extend evidence-led independent forecast trials, not another weather model |
| Medicine, human physiology, epidemiology | Existing biomedical tools plus validated open clinical/epidemiological models as suited | Appropriate ethically sourced, consented biological/clinical observations | Future, private governance and independent validation required |
| Industrial/manufacturing optimization | Existing OpenMDAO, other validated process simulation/scheduling upstream | Production line timing, metered resource use, machine faults | After a measured industrial dataset/acceptance case |

**Primary verified reference sources for biology and plant science:**
- PCSE incl. grassland LINGRA: https://pcse.readthedocs.io/en/latest/ and https://pcse.readthedocs.io/en/latest/code.html ; source https://github.com/ajwdewit/pcse ; package license **EUPL-1.2** (review legal obligations before distribution).
- BioCro plant growth/physiology: https://github.com/biocro/biocro ; R package **MIT**, C++ core **LGPL >=3**.
- APSIM: https://github.com/APSIMInitiative/ApsimX ; DSSAT: https://dssat.net/ ; review the actual license and redistribution terms for every model/data source.
- OpenAlea plant form: https://openalea.readthedocs.io/en/latest/packages/modelling.html .
- Metabolic flux COBRApy: https://github.com/opencobra/cobrapy and https://cobrapy.readthedocs.io/en/latest/ ; solver and GPL obligations must be checked.
- Biochemical networks COPASI: https://copasi.org/ ; Tellurium/libRoadRunner: https://tellurium.readthedocs.io/en/latest/ .
- Multicellular biology PhysiCell: https://github.com/MathCancer/PhysiCell .
- Buildings EnergyPlus: https://energyplus.readthedocs.io/en/latest/ ; photonics Meep: https://meep.readthedocs.io/en/master/ .

## Not-yet-discussed capabilities that matter more than more software

1. **Data assimilation, uncertainty quantification and sensor quality**: measurements must update a model without letting the answer leak backward into forecasts. Quantify uncertainty, reject stale/invalid data, detect domain shifts.
2. **Causal intervention and experimental design**: compare *what if I act?* against what the physical counterpart does under separately evaluated interventions, not merely correlated readings.
3. **Cross-scale biology**: molecular reaction, cell, tissue, whole-organism, crop canopy, soil microbiome and ecosystem operate at different spatial/temporal scales; there is no magic single model. Connect via documented units, boundaries and measured interfaces only.
4. **Standards and provenance**: SBML for biological reaction models, consent/licensing for data, UTC/time-base and physical units, raw checksums, versioned models, strong independent baselines and calibrated instrument uncertainty.
5. **Active learning and prospective validation**: choose measurements/experiments based on information gain, freeze predictions before tests, archive null results and verify across laboratories/sensors.
6. **Physical-world sensing / robotics / laboratory interfaces**: useful for future autonomous science, but physical actuation requires separately bounded authorization, hardware safety and third-party verification.
7. **Error-detection and model governance**: reproducibility, auditability, simulation validity, monitoring and graceful degradation matter before deploying any twin for real decisions.

## Immediate sequence

1. Finish the existing **NOAA historical sensor-replay shadow pilot** (reuse one verified harmonic engine, actual public NOAA observations, two baselines, immutable report). *Code/CI result governs status; this document alone proves nothing.*
2. Do not disturb the pre-registered Nov 12–13 NOAA/USGS prospective studies. Observe actual outcomes before updating model decisions.
3. Next biology pilot: evaluate **one existing PCSE LINGRA grassland experiment** with a publicly licensed grassland dataset and a naïve phenology/biomass baseline. Its upstream includes experimental grassland collections; verify relevance and license. Avoid claiming transfer to any specific tropical forage genotype without field measurements.
4. Extend to aircraft, robotics, buildings, infrastructure, cellular and energy twins **one independently evidenced physical counterpart at a time**. Use the best upstream model per domain and private IP only in private approved storage.

**Current boundary:** No PCSE/BioCro/COBRApy/PhysiCell/Meep/EnergyPlus installation, validated biological twin, private data ingestion, paid compute, autonomous physical control or new scientific discovery has been executed by adding this inventory.

