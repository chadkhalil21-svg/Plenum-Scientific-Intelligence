"""Scientific numerical fixtures using SciPy and RDKit. No novel discoveries claimed."""
from math import exp, pi, sqrt
from scipy.integrate import solve_ivp

DOMAINS = ("mechanics", "chemistry", "materials", "electronics", "molecules")


def solve(domain, method="RK45"):
    if domain not in DOMAINS:
        raise ValueError("Unknown or unapproved scientific domain")
    if method not in ("RK45", "DOP853", "Radau"):
        raise ValueError("Numerical method not allowlisted")
    if domain == "molecules":
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        mol = Chem.MolFromSmiles("CCO")
        formula = rdMolDescriptors.CalcMolFormula(mol)
        weight = float(Descriptors.MolWt(mol))
        return {"domain": domain, "library": "RDKit",
                "formula": formula, "molecular_weight_g_mol": weight,
                "verified_fixture": formula == "C2H6O" and abs(weight - 46.069) < .05,
                "limitation": "Ethanol descriptors only; not a drug, toxicity, docking, or cure prediction"}
    if domain == "mechanics":
        mu, radius = 6.67430e-11 * 5.9722e24, 6771000.0
        speed = sqrt(mu / radius)
        duration = 2*pi*radius/speed
        def rhs(t, y):
            x, z, vx, vz = y
            r = sqrt(x*x + z*z)
            return (vx, vz, -mu*x/r**3, -mu*z/r**3)
        initial = [radius, 0., 0., speed]
        reference = radius
    elif domain == "chemistry":
        duration, initial, reference = 10., [1., 0.], exp(-3.5)
        def rhs(t, y):
            return (-.35*y[0], .35*y[0])
    elif domain == "materials":
        duration, initial, reference = 30., [360.], 300. + 60*exp(-3.6)
        def rhs(t, y):
            return (-.12*(y[0]-300.),)
    else:
        duration, initial, reference = 5., [5.], 5*exp(-5)
        def rhs(t, y):
            return (-y[0],)
    sol = solve_ivp(rhs, (0., duration), initial, method=method,
                    rtol=1e-10, atol=1e-12, max_step=duration/20)
    if not sol.success:
        raise RuntimeError("Scientific solver failed")
    actual = sqrt(sol.y[0,-1]**2 + sol.y[1,-1]**2) if domain == "mechanics" else float(sol.y[0,-1])
    error = abs(actual-reference)/max(abs(reference),1e-12)
    invariant_error = (abs(float(sol.y[0,-1]+sol.y[1,-1])-1)
                       if domain == "chemistry" else 0.)
    if domain == "mechanics":
        x,z,vx,vz = map(float, sol.y[:,-1])
        energy = (vx*vx+vz*vz)/2 - mu/sqrt(x*x+z*z)
        invariant_error = abs((energy+mu/(2*radius))/(mu/(2*radius)))
    passed = error < 2e-6 and invariant_error < 2e-6
    return {"domain": domain, "library": "SciPy solve_ivp", "method": method,
            "observed": float(actual), "analytical_reference": float(reference),
            "relative_error": float(error), "invariant_error": float(invariant_error),
            "solver_function_evaluations": int(sol.nfev),
            "verified_fixture": passed,
            "limitation": "Known simplified equations, not experimental validation or scientific discovery"}


def run_lab(question, domains=None, method="RK45"):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        raise ValueError("Research question must have 1 to 600 characters")
    if domains is None:
        q = question.lower()
        rules = {"mechanics": ("orbit","gravity","space"), "chemistry": ("chemical","reaction"),
                 "materials": ("heat","material","thermal"), "electronics": ("battery","circuit"),
                 "molecules": ("drug","molecule","protein")}
        domains = [k for k, tags in rules.items() if any(t in q for t in tags)]
        domains = domains[:3] or ["mechanics","chemistry","materials"]
    if not domains or len(domains)>5 or len(set(domains))!=len(domains):
        raise ValueError("Select 1 to 5 distinct tool domains")
    result = [solve(d, method) for d in domains]
    return {"question": question, "specialists": list(domains),
            "agent_roles": ["planner", "simulation specialists", "analytical verifier", "skeptical reviewer"],
            "results": result,
            "known_model_checks_passed": all(r["verified_fixture"] for r in result),
            "scientific_discovery_verified": False, "self_modified": False,
            "limitations": "These known-equation fixtures do not test the question's speculative hypotheses."}


def benchmark_methods():
    methods = ("RK45","DOP853","Radau")
    results=[]
    for method in methods:
        solved=[solve(d,method) for d in DOMAINS[:4]]
        results.append({"method": method,
                        "all_passed": all(x["verified_fixture"] for x in solved),
                        "calls": sum(x["solver_function_evaluations"] for x in solved),
                        "worst_error": max(x["relative_error"] for x in solved)})
    winners=[x for x in results if x["all_passed"]]
    return {"methods": results,
            "least_calls_in_known_fixtures": min(winners,key=lambda x:x["calls"])["method"] if winners else None,
            "candidate_deployed": False, "scientific_discovery_verified": False,
            "caveat": "Algorithm benchmarking on known fixtures is not AI self-improvement."}
