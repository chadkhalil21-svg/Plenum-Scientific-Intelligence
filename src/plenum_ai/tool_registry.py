"""Registry of explicitly approved scientific tools and upstream references.

Only tools marked executable are called. Metadata-only and planned integrations
are never interpreted as permission to install or execute third-party code.
"""
from dataclasses import dataclass, asdict
from importlib.metadata import PackageNotFoundError, version

@dataclass(frozen=True)
class Tool:
    key: str
    origin: str
    purpose: str
    package: str | None
    declared_version: str
    license: str
    stage: str
    status: str
    depends_on: tuple[str, ...] = ()
    limitations: str = ""

TOOLS = {
    "scipy.orbit": Tool("scipy.orbit", "https://github.com/scipy/scipy",
        "Numerical Newtonian orbit fixture", "scipy", ">=1.12,<2", "BSD-3-Clause",
        "parallel", "executable", limitations="Known Earth point-mass test, not a novel spacecraft design"),
    "scipy.thermal": Tool("scipy.thermal", "https://github.com/scipy/scipy",
        "Lumped thermal cooling fixture", "scipy", ">=1.12,<2", "BSD-3-Clause",
        "parallel", "executable", limitations="Constant-rate cooling fixture, not an experimentally validated material"),
    "scipy.kinetics": Tool("scipy.kinetics", "https://github.com/scipy/scipy",
        "Known first-order chemical kinetics fixture", "scipy", ">=1.12,<2", "BSD-3-Clause",
        "parallel", "executable", limitations="Toy closed reaction, not a new reaction mechanism"),
    "scipy.electronics": Tool("scipy.electronics", "https://github.com/scipy/scipy",
        "Ideal RC circuit dynamics fixture", "scipy", ">=1.12,<2", "BSD-3-Clause",
        "parallel", "executable", limitations="Idealized RC circuit, not validated battery electrochemistry"),
    "rdkit.molecule": Tool("rdkit.molecule", "https://github.com/rdkit/rdkit",
        "Known ethanol molecular formula and descriptor check", "rdkit", ">=2025.9,<2027",
        "BSD-3-Clause", "parallel", "executable",
        limitations="No molecular docking, pharmacology or treatment prediction"),
    "openalex.metadata": Tool("openalex.metadata", "https://openalex.org/",
        "Bounded public scholarly metadata retrieval", None, "OpenAlex public API",
        "Metadata subject to service terms", "parallel", "executable",
        limitations="Metadata is not full-text access, citation verification or scientific truth"),
    "federated.metadata": Tool("federated.metadata",
        "https://openalex.org/; https://europepmc.org/; https://www.semanticscholar.org/",
        "Read-only cross-source search across three metadata APIs", None,
        "public provider APIs", "Provider service terms apply",
        "parallel", "executable",
        limitations="Source rate limits, API failure, DOI deduplication; not validated full text"),
    "openmdao.cooling": Tool("openmdao.cooling", "https://github.com/OpenMDAO/OpenMDAO",
        "Optimize a simple cooling-area design constraint", "openmdao", "==3.45.2",
        "Apache-2.0", "dependent", "executable",
        depends_on=("scipy.thermal",),
        limitations="Illustrative linear heat rejection with constant h; not an aircraft engineering validation"),
    "nasa.exoplanets": Tool("nasa.exoplanets",
        "https://exoplanetarchive.ipac.caltech.edu/",
        "Astropy Keplerian consistency check on bounded real NASA catalog records",
        "astropy", ">=7.0,<8", "BSD-3-Clause (Astropy); NASA archive attribution",
        "parallel", "executable",
        limitations="Orbital semimajor axes may be derived from period and mass; NOT independent proof"),
    "pybamm.battery": Tool("pybamm.battery",
        "https://github.com/pybamm-team/PyBaMM",
        "Lithium-ion SPM and SPMe electrochemical discharge simulations",
        "pybamm", "==26.10.1.1", "BSD-3-Clause",
        "isolated_workflow", "install_and_test_separately",
        limitations="Not yet an agent-graph tool; default cell models require empirical validation"),
    "noaa.tides": Tool("noaa.tides",
        "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
        "Precommitted harmonic prediction and 24-hour baseline on held-out NOAA measured hourly water levels",
        "numpy", ">=1.26,<3", "NOAA US government observations, attribution requested",
        "isolated_workflow", "requires_live_measurement_check",
        limitations="Historical 24-hour evaluation only, not approved for maritime safety or flood warnings"),
    "nasa.aviary": Tool("nasa.aviary", "https://github.com/OpenMDAO/Aviary",
        "Aircraft design and mission analysis", "aviary", "not installed",
        "Check version and transitive data licenses", "future", "planned",
        limitations="Aircraft models require configuration, real aircraft inputs and validation"),
    "nasa.gmat": Tool("nasa.gmat", "https://github.com/NASA/GMAT",
        "Spacecraft mission analysis", None, "not installed", "Review upstream",
        "future", "planned", limitations="Large separate simulator, not a Python drop-in"),
    "kdense.skills": Tool("kdense.skills",
        "https://github.com/K-Dense-AI/scientific-agent-skills",
        "Upstream scientific skill documentation", None,
        "source SHA a25cf9ec00e2745d03f8704acf6f6919694ccd9a",
        "MIT collection; review individual skills", "reference", "metadata_only",
        limitations="Instructions are untrusted text; no automatic execution or installation"),
    "arxiv.metadata": Tool("arxiv.metadata", "https://info.arxiv.org/help/api/",
        "Public arXiv bibliographic Atom metadata", None, "public Atom API",
        "Subject to arXiv metadata and rate-limit terms",
        "external_source", "verified_adapter_pending_live_test",
        limitations="Bibliography only, no validated research claims"),
    "osti.metadata": Tool("osti.metadata", "https://www.osti.gov/api/v1/docs",
        "US DOE OSTI-funded research bibliographic metadata", None, "public v1 API",
        "Subject to OSTI metadata service terms", "external_source",
        "verified_adapter_pending_live_test",
        limitations="Bibliography only; source reliability and API availability may vary"),
    "materialsproject.api": Tool("materialsproject.api",
        "https://docs.materialsproject.org/downloading-data/using-the-api/getting-started",
        "Materials structures and computed-property data", None,
        "requires owner-supplied MP_API_KEY", "Review Materials Project use terms",
        "credential_gated", "not_connected",
        limitations="Do not put personal API keys into public GitHub source or artifacts"),
    "lean4.proofs": Tool("lean4.proofs", "https://github.com/leanprover/lean4",
        "Formally machine-check mathematical proofs", None, "not installed",
        "Review upstream and theorem library licenses", "future", "planned",
        limitations="Requires isolated Lean installation and independent proof checking"),
    "diffdock.docking": Tool("diffdock.docking",
        "https://github.com/gcorso/DiffDock",
        "Predict protein-ligand docking poses", None, "not installed",
        "Review upstream source, model weights and dataset license", "future", "planned",
        limitations="Docking predictions are not measured drug safety or efficacy"),
    "openmm.dynamics": Tool("openmm.dynamics",
        "https://github.com/openmm/openmm",
        "Reference CPU harmonic-bond molecular dynamics and future force-fields",
        "openmm", "==8.6.1", "OpenMM BSD-like license; verify other force-field assets",
        "isolated_workflow", "install_and_test_separately",
        limitations="Only a synthetic two-particle fixture; protein force-fields require separate validation"),
    "pyscf.chemistry": Tool("pyscf.chemistry",
        "https://github.com/pyscf/pyscf",
        "Quantum-chemical electronic structure", None, "not installed",
        "Review upstream", "future", "planned",
        limitations="Basis-set, method and convergence choices require review"),
    "pymatgen.materials": Tool("pymatgen.materials",
        "https://github.com/materialsproject/pymatgen",
        "Materials crystal structures and analyses", None, "not installed",
        "Review upstream", "future", "planned",
        limitations="Materials property databases may require separate credentials"),
    "su2.cfd": Tool("su2.cfd", "https://github.com/su2code/SU2",
        "Computational fluid dynamics for aerodynamics", None, "not installed",
        "Review upstream", "future", "planned",
        limitations="Mesh, convergence and turbulence validation required"),
    "tooluniverse.biomed": Tool("tooluniverse.biomed",
        "https://github.com/mims-harvard/ToolUniverse",
        "Curated biomedical research-tool interfaces", None, "not installed",
        "Review individual tools, data restrictions and licenses",
        "future", "planned",
        limitations="Do not provide direct unrestricted commands or private health records"),
    "biomni.biomed": Tool("biomni.biomed",
        "https://github.com/snap-stanford/Biomni",
        "Biomedical scientific-agent platform", None, "not installed",
        "Review platform and tool permissions", "reference", "metadata_only",
        limitations="External data and commands require separate isolation and approval"),
    "karpathy.autoresearch": Tool("karpathy.autoresearch",
        "https://github.com/karpathy/autoresearch",
        "Iterative model-training research", None, "not installed",
        "Review upstream source and training environment", "reference", "metadata_only",
        limitations="Training compute and independent evaluation required"),
    "paperqa.literature": Tool("paperqa.literature",
        "https://github.com/Future-House/paper-qa",
        "LLM-assisted multi-document citation-grounded reading", None, "not installed",
        "Review model backend, document licenses and dependency terms",
        "future", "planned",
        limitations="Requires configured LLM inference, not active in free CPU workflow"),
    "inspectai.eval": Tool("inspectai.eval",
        "https://github.com/UKGovernmentBEIS/inspect_ai",
        "Independent agent reasoning and tool-use evaluation", None, "not installed",
        "Review upstream", "future", "planned",
        limitations="Needs evaluated model and bounded reviewed tasks"),
    "sakana.scientist": Tool("sakana.scientist",
        "https://github.com/SakanaAI/AI-Scientist-v2",
        "Autonomous research architecture reference", None, "not installed",
        "Custom source license: review required", "reference", "metadata_only",
        limitations="Generated-code execution is not permitted in this prototype"),
}

MAX_PARALLEL_TOOLS = 5
PARALLEL_TOOLS = frozenset(k for k,v in TOOLS.items()
                           if v.stage == "parallel" and v.status == "executable")

def get_registry():
    tools = []
    for t in TOOLS.values():
        entry = asdict(t)
        entry["depends_on"] = list(t.depends_on)
        if t.package:
            try:
                entry["installed_version"] = version(t.package)
            except PackageNotFoundError:
                entry["installed_version"] = None
        tools.append(entry)
    return {"schema": "plenum-tools-v1", "tools": tools,
            "parallel_limit_per_batch": MAX_PARALLEL_TOOLS,
            "all_external_execution_approved": False}

def approve_request(tool_keys):
    keys = list(tool_keys)
    if not keys or len(keys) > MAX_PARALLEL_TOOLS or len(set(keys)) != len(keys):
        raise ValueError("Choose 1..5 distinct parallel tools")
    if any(key not in PARALLEL_TOOLS for key in keys):
        raise ValueError("Unapproved, dependent, or reference-only scientific tool requested")
    return keys

def route_request(question):
    """Deterministic, auditable keyword router; not an LLM or proof of autonomous reasoning."""
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        raise ValueError("Public question must have 1..600 characters")
    q = question.casefold()
    rules = (
        ("scipy.orbit", ("orbit", "gravity", "spacecraft", "trajectory", "aerospace")),
        ("scipy.thermal", ("heat", "thermal", "cooling", "temperature", "material")),
        ("scipy.kinetics", ("chemical reaction", "kinetic", "catalys", "reaction")),
        ("rdkit.molecule", ("molecule", "molecular", "drug", "protein")),
        ("scipy.electronics", ("circuit", "capacitor", "electronics", "electrical", "battery")),
        ("federated.metadata", ("literature", "scientific paper", "publications", "bibliograph")),
        ("nasa.exoplanets", ("exoplanet", "keplerian", "stellar orbit", "stellar mass")),
    )
    selection = [name for name, keywords in rules if any(k in q for k in keywords)]
    if "optimiz" in q or "design" in q:
        if "scipy.thermal" not in selection:
            selection.insert(0, "scipy.thermal")
    if not selection:
        selection = ["scipy.orbit", "scipy.thermal", "scipy.kinetics", "rdkit.molecule"]
    selection = selection[:MAX_PARALLEL_TOOLS]
    approve_request(selection)
    return {
        "tool_keys": selection,
        "enable_optimization": "scipy.thermal" in selection,
        "routing_method": "deterministic_allowlisted_keywords",
        "model_selected_tools": False,
        "note": "Keyword routing is a conservative prototype, not autonomous scientific planning",
    }
