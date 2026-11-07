"""Command-line interface. No paid services or unrestricted AI tool use."""
import argparse
import json
from pathlib import Path
from .evolve import default_benchmarks, evaluate_evolution
from .literature import search_papers
from .physics import circular_orbit_speed
from .research import make_report
from .mission import run_mission
from .memory import make_record, verify, save
from .audit import independent_audit
import os


def save_json(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(target)


def main():
    parser = argparse.ArgumentParser(prog="plenum")
    commands = parser.add_subparsers(dest="action", required=True)
    efficient = commands.add_parser("efficient-research",
        help="Low-cost deterministic preflight; approved fixed fixtures only, no AI calls")
    efficient.add_argument("--query", required=True)
    efficient.add_argument("--dry-run", action="store_true")
    efficient.add_argument("--out", default="reports/efficient_research.json")
    research = commands.add_parser("research")
    research.add_argument("--query", required=True)
    research.add_argument("--out", default="reports/research.json")
    research.add_argument("--model", help="Locally running Ollama model; optional")
    improve = commands.add_parser("improve")
    improve.add_argument("--out", default="reports/improvement.json")
    physics = commands.add_parser("physics")
    physics.add_argument("--radius-m", required=True, type=float)
    mission = commands.add_parser("mission")
    mission.add_argument("--query", required=True)
    mission.add_argument("--out", default="reports/mission.json")
    mission.add_argument("--simulation", choices=["heat", "orbit", "none"], default="heat")
    mission.add_argument("--offline", action="store_true", help="Use clearly labeled offline fixture")
    mission.add_argument("--model", help="Optional locally running Ollama model")
    mission.add_argument("--hf-model", action="store_true", help="Optional reviewed tiny CPU model")
    mission.add_argument("--memory-dir", help="Public archived research metadata")
    memory = commands.add_parser("memory-record")
    memory.add_argument("--mission", required=True)
    memory.add_argument("--improvement", required=True)
    memory.add_argument("--out", default="reports/memory_entry.json")
    ingest = commands.add_parser("memory-ingest")
    ingest.add_argument("--file", required=True)
    ingest.add_argument("--dir", required=True)
    lab = commands.add_parser("lab")
    lab.add_argument("--query", required=True)
    lab.add_argument("--domains", default="mechanics,chemistry,materials,electronics,molecules")
    lab.add_argument("--out", default="reports/scientific_lab.json")
    lab.add_argument("--method", choices=["RK45","DOP853","Radau"], default="RK45")
    methods = commands.add_parser("solver-benchmark")
    methods.add_argument("--out", default="reports/solver_benchmark.json")
    team = commands.add_parser("investigate")
    team.add_argument("--query", required=True)
    team.add_argument("--domains", default="mechanics,chemistry,materials,electronics,molecules")
    team.add_argument("--out", default="reports/investigation.json")
    team.add_argument("--offline", action="store_true")
    team.add_argument("--memory-dir")
    team.add_argument("--model", help="Existing local Ollama model")
    team.add_argument("--hf-model", action="store_true")
    training = commands.add_parser("train-models")
    training.add_argument("--tasks", default="botany,chemistry,handwriting,gravity",
                          help="Comma-separated allowlisted scientific ML benchmarks")
    training.add_argument("--out", default="reports/model_training.json")
    qa = commands.add_parser("eval-science")
    qa.add_argument("--count", type=int, default=12)
    qa.add_argument("--out", default="reports/science_reasoning.json")
    tune = commands.add_parser("fine-tune-science")
    tune.add_argument("--out", default="reports/qwen3_finetune.json")
    tune.add_argument("--checkpoint-dir", default="candidates/qwen3-science-v1")
    registry = commands.add_parser("tool-registry")
    registry.add_argument("--out", default="reports/tool_registry.json")
    multi = commands.add_parser("parallel-research")
    multi.add_argument("--query", required=True)
    multi.add_argument("--tools", default="scipy.orbit,scipy.thermal,scipy.kinetics,rdkit.molecule")
    multi.add_argument("--online", action="store_true", help="Allow read-only research metadata retrieval")
    multi.add_argument("--auto", action="store_true", help="Route public question to approved tools using deterministic keywords")
    multi.add_argument("--no-optimization", action="store_true")
    multi.add_argument("--out", default="reports/parallel_research.json")
    skills = commands.add_parser("scientific-skills")
    skills.add_argument("--inspect", help="Allowlisted K-Dense skill name for pinned read-only review")
    skills.add_argument("--out", default="reports/scientific_skills.json")
    federation = commands.add_parser("federated-literature")
    federation.add_argument("--query", required=True)
    federation.add_argument("--online", action="store_true")
    federation.add_argument("--global-sources", action="store_true", help="Also query public arXiv and DOE OSTI metadata")
    federation.add_argument("--out", default="reports/federated_literature.json")
    nasa = commands.add_parser("nasa-exoplanets")
    nasa.add_argument("--out", default="reports/nasa_exoplanet_consistency.json")
    battery = commands.add_parser("battery-simulation")
    battery.add_argument("--minutes", type=int, default=10)
    battery.add_argument("--out", default="reports/battery_simulation.json")
    tides = commands.add_parser("empirical-tides")
    tides.add_argument("--out", default="reports/noaa_measured_tides.json")
    seasons = commands.add_parser("empirical-tides-seasons")
    seasons.add_argument("--out", default="reports/noaa_seasonal_validation.json")
    hypothesis = commands.add_parser("propose-hypotheses")
    hypothesis.add_argument("--out", default="reports/ai_hypothesis_proposals.json")
    evaluate = commands.add_parser("audit-hypotheses")
    evaluate.add_argument("--proposal", required=True)
    evaluate.add_argument("--out", default="reports/ai_hypothesis_audit.json")
    evidence_proposals = commands.add_parser("propose-evidence-gated")
    evidence_proposals.add_argument("--out", default="reports/gated_hypotheses.json")
    evidence_audit = commands.add_parser("audit-evidence-gated")
    evidence_audit.add_argument("--proposal", required=True)
    evidence_audit.add_argument("--out", default="reports/gated_audit.json")
    durable = commands.add_parser("durable-research")
    durable.add_argument("--query", required=True)
    durable.add_argument("--db", default="reports/research_checkpoints.sqlite")
    durable.add_argument("--thread-id", required=True)
    durable.add_argument("--tools", default="scipy.orbit,scipy.thermal")
    durable.add_argument("--out", default="reports/durable_research.json")
    recover = commands.add_parser("durable-state")
    recover.add_argument("--db", required=True)
    recover.add_argument("--thread-id", required=True)
    recover.add_argument("--out", default="reports/recovered_graph.json")
    index = commands.add_parser("index-literature")
    index.add_argument("--query", required=True)
    index.add_argument("--db", default="reports/research_index.sqlite")
    index.add_argument("--online", action="store_true")
    index.add_argument("--global-sources", action="store_true", help="Add arXiv and DOE OSTI metadata search")
    index.add_argument("--out", default="reports/knowledge_ingest.json")
    fulltext = commands.add_parser("index-open-article")
    fulltext.add_argument("--pmcid", required=True)
    fulltext.add_argument("--db", default="reports/research_index.sqlite")
    fulltext.add_argument("--out", default="reports/oa_ingest.json")
    search_index = commands.add_parser("search-knowledge")
    search_index.add_argument("--query", required=True)
    search_index.add_argument("--db", default="reports/research_index.sqlite")
    search_index.add_argument("--out", default="reports/knowledge_search.json")
    memory_index = commands.add_parser("import-public-memory")
    memory_index.add_argument("--dir", required=True)
    memory_index.add_argument("--db", default="reports/research_index.sqlite")
    memory_index.add_argument("--out", default="reports/memory_index.json")
    ecosystem = commands.add_parser("scientific-ecosystem")
    ecosystem.add_argument("--out", default="reports/scientific_ecosystem.json")
    openmm = commands.add_parser("openmm-reference")
    openmm.add_argument("--steps", type=int, default=100)
    openmm.add_argument("--out", default="reports/openmm_reference.json")
    discovery = commands.add_parser("discovery-pulse")
    discovery.add_argument("--topic", default="scientific discovery")
    discovery.add_argument("--out", default="reports/discovery_pulse.json")
    artist = commands.add_parser("creative-sources")
    artist.add_argument("--query", required=True)
    artist.add_argument("--out", default="reports/creative_sources.json")
    studio = commands.add_parser("creative-studio")
    studio.add_argument("--topic", required=True)
    studio.add_argument("--seed", type=int, default=1701)
    studio.add_argument("--dir", default="reports/creative_studio")
    studio.add_argument("--out", default="reports/creative_studio_manifest.json")
    videos = commands.add_parser("youtube-updates")
    videos.add_argument("--channel", default="nasa")
    videos.add_argument("--query", default="scientific lectures")
    videos.add_argument("--out", default="reports/youtube_updates.json")
    delta = commands.add_parser("compare-discovery")
    delta.add_argument("--report", required=True)
    delta.add_argument("--history", required=True)
    delta.add_argument("--out", default="reports/discovery_delta.json")
    ideas = commands.add_parser("invention-ideas")
    ideas.add_argument("--report", required=True)
    ideas.add_argument("--out", default="reports/serendipity.json")
    frontiers = commands.add_parser("research-frontiers")
    frontiers.add_argument("--query", required=True)
    frontiers.add_argument("--online", action="store_true")
    frontiers.add_argument("--out", default="reports/research_frontiers.json")
    design = commands.add_parser("parametric-design")
    design.add_argument("--width",type=float,default=180)
    design.add_argument("--height",type=float,default=110)
    design.add_argument("--thickness",type=float,default=6)
    design.add_argument("--hole-diameter",type=float,default=5)
    design.add_argument("--render",action="store_true")
    design.add_argument("--dir",default="reports/parametric_cad")
    design.add_argument("--out",default="reports/cad_manifest.json")
    music = commands.add_parser("music-analysis")
    music.add_argument("--topic",default="procedural light and sound")
    music.add_argument("--seed",type=int,default=1701)
    music.add_argument("--out",default="reports/music_analysis.json")
    horizon = commands.add_parser("world-horizon")
    horizon.add_argument("--topic", required=True)
    horizon.add_argument("--category", default="all",
                         choices=["all","universities","defense","foreign_affairs",
                                  "business","environment","news","journals",
                                  "software","discoveries","art","music","design",
                                  "health","funding","artificial_intelligence","physics"])
    horizon.add_argument("--online", action="store_true")
    horizon.add_argument("--out", default="reports/world_horizon.json")
    horizon_registry = commands.add_parser("horizon-catalog")
    horizon_registry.add_argument("--out", default="reports/horizon_catalog.json")
    build = commands.add_parser("build-program")
    build.add_argument("--kind", choices=["research_cli","data_validator","geometry_designer"], default="research_cli")
    build.add_argument("--topic", required=True)
    build.add_argument("--dir", default="reports/generated_program")
    build.add_argument("--out", default="reports/program_manifest.json")
    universal = commands.add_parser("universal-brief")
    universal.add_argument("--topic", required=True)
    universal.add_argument("--online", action="store_true")
    universal.add_argument("--limit", type=int, default=8)
    universal.add_argument("--out", default="reports/universal_brief.json")
    args = parser.parse_args()
    if args.action == "efficient-research":
        from .efficient_execution import execute
        report = execute(args.query, dry_run=args.dry_run)
        save_json(args.out, report)
        print("Efficient public research:", report["status"],
              "approved fixed tools:", report["approved_tool_count"],
              "model calls:", report["estimated_model_calls"])
        return
    if args.action == "research":
        papers = search_papers(args.query)
        report = make_report(args.query, papers, model=args.model)
        print("Research inventory:", save_json(args.out, report), "papers:", len(papers))
    elif args.action == "improve":
        benchmarks = default_benchmarks()
        evaluation = evaluate_evolution(benchmarks)
        evaluation["independent_audit"] = independent_audit(benchmarks, evaluation)
        print("Improvement proposal:", save_json(args.out, evaluation),
              "accepted:", evaluation["accepted_for_proposal"])
    elif args.action == "mission":
        if args.model and args.hf_model:
            parser.error("Choose either local Ollama or Hugging Face model")
        if args.hf_model:
            from .hf_model import hf_generate, APPROVED_MODEL
            generator = hf_generate
            model = APPROVED_MODEL
        else:
            generator = None
            model = args.model
        report = run_mission(args.query, simulation=args.simulation,
                             offline=args.offline, model=model,
                             memory_dir=args.memory_dir,
                             generator=generator)
        print("Mission:", save_json(args.out, report),
              "benchmark:", report["numeric_benchmark_verified"],
              "model:", report["model_inference_executed"])
    elif args.action == "memory-record":
        mission_report = json.loads(Path(args.mission).read_text(encoding="utf-8"))
        improvement = json.loads(Path(args.improvement).read_text(encoding="utf-8"))
        record = make_record(mission_report, improvement,
                             os.getenv("GITHUB_RUN_ID", ""),
                             os.getenv("GITHUB_SHA", ""))
        verify(record)
        print("Validated memory record:", save_json(args.out, record), "ID:", record["id"])
    elif args.action == "memory-ingest":
        record = json.loads(Path(args.file).read_text(encoding="utf-8"))
        name, created = save(record, args.dir)
        print("Stored checksum-verified memory:", name, "new:", created)
    elif args.action == "lab":
        from .lab import run_lab
        domains = [x.strip() for x in args.domains.split(",")]
        result = run_lab(args.query, domains=domains, method=args.method)
        print("Scientific lab:", save_json(args.out,result),
              "passed:", result["known_model_checks_passed"])
    elif args.action == "solver-benchmark":
        from .lab import benchmark_methods
        result = benchmark_methods()
        print("Numerical solver benchmark:", save_json(args.out,result))
    elif args.action == "investigate":
        if args.model and args.hf_model:
            parser.error("Choose either Ollama or Qwen3")
        from .investigate import investigate
        if args.hf_model:
            from .hf_model import hf_generate, APPROVED_MODEL
            name, generator = APPROVED_MODEL, hf_generate
        else:
            name, generator = args.model, None
        report = investigate(args.query, domains=[s.strip() for s in args.domains.split(",")],
                             offline=args.offline, model=name, generator=generator,
                             memory_dir=args.memory_dir)
        print("Research team:", save_json(args.out, report),
              "verified known tools:", report["workflow_verified_as_known_tool_demonstration"],
              "new discovery:", report["hypotheses_verified"])
    elif args.action == "train-models":
        from .trainlab import run_training_lab
        tasks = [task.strip() for task in args.tasks.split(",")]
        report = run_training_lab(tasks)
        print("Trained scientific ML models:", save_json(args.out, report),
              "holdout improvements:", report["candidate_beats_dummy_in_all_tasks"],
              "production deployed:", report["deployment_authorized"])
    elif args.action == "eval-science":
        from .science_eval import run_external_evaluation
        report = run_external_evaluation(count=args.count, out=args.out)
        print("External science evaluation:", report["correct"], "/", report["total"],
              "data revision:", report["source"]["revision"],
              "model revision:", report["model_revision"])
    elif args.action == "fine-tune-science":
        from .fine_tune import run_fine_tuning
        report = run_fine_tuning(output_dir=args.checkpoint_dir, report_file=args.out)
        print("LoRA candidate training:", report["training_steps"],
              "optimizer steps; baseline:", report["baseline"]["correct"],
              "/", report["baseline"]["total"],
              "candidate:", report["candidate"]["correct"],
              "/", report["candidate"]["total"],
              "automatically deployed:", report["automatic_model_promotion"])
    elif args.action == "tool-registry":
        from .tool_registry import get_registry
        report = get_registry()
        print("Scientific tool registry:", save_json(args.out, report),
              "catalogued tools:", len(report["tools"]))
    elif args.action == "parallel-research":
        from .parallel_research import run_network
        if args.auto:
            from .tool_registry import route_request
            routing = route_request(args.query)
            tool_keys = routing["tool_keys"]
            optimization = routing["enable_optimization"] and not args.no_optimization
        else:
            routing = {"routing_method": "explicit_user_selected_tools"}
            tool_keys = [key.strip() for key in args.tools.split(",")]
            optimization = not args.no_optimization
        report = run_network(
            args.query, tool_keys=tool_keys,
            offline=not args.online, optimize=optimization,
        )
        report["routing"] = routing
        print("Parallel scientific research:", save_json(args.out, report),
              "workers:", report["parallel_tool_count"],
              "known-model checks passed:", report["known_model_integration_passed"])
    elif args.action == "scientific-skills":
        from .skill_catalog import catalog, retrieve_skill_document
        report = retrieve_skill_document(args.inspect) if args.inspect else catalog()
        print("Read-only K-Dense skill index:", save_json(args.out,report))
    elif args.action == "federated-literature":
        from .federated_sources import search_federated
        from .global_sources import global_literature
        report=(global_literature(args.query,offline=not args.online) if args.global_sources
                else search_federated(args.query,offline=not args.online))
        print("Federated public literature search:",save_json(args.out,report),
              "records:",len(report["records"]))
    elif args.action == "nasa-exoplanets":
        from .nasa_exoplanets import run_nasa_catalog_consistency
        report = run_nasa_catalog_consistency()
        print("NASA catalog comparison:", save_json(args.out, report),
              "planets:", report["observations_evaluated"],
              "within ten percent:", report["fraction_within_ten_percent"],
              "independent proof:", report["independent_empirical_validation"])
    elif args.action == "battery-simulation":
        from .battery_model import simulate_discharge
        report=simulate_discharge(minutes=args.minutes)
        print("PyBaMM electrochemical models:",
              save_json(args.out, report),
              "simulations:", len(report["models"]),
              "experimental validation:", report["experimentally_validated"])
    elif args.action == "empirical-tides":
        from .noaa_empirical import run_empirical_forecast
        report = run_empirical_forecast()
        print("NOAA measured water-level forecast:", save_json(args.out, report),
              "all-station hypothesis supported:", report["hypothesis_supported_at_both_stations"],
              "independent observed target:", report["is_independent_future_observation_holdout"])
    elif args.action == "empirical-tides-seasons":
        from .noaa_seasons import run_seasonal_validation
        report=run_seasonal_validation()
        print("NOAA multi-season measured holdouts:",
              save_json(args.out,report),
              "station-days:",report["number_of_station_day_tests"],
              "harmonic wins:",report["wins"],
              "aggregate hypothesis:",report["hypothesis_supported"])
    elif args.action == "propose-hypotheses":
        from .autonomous_hypothesis import make_proposals, qwen_choose, save_report
        result = make_proposals(qwen_choose)
        print("Constrained Qwen3 proposal manifest:", save_report(args.out, result),
              "blind proposed hypotheses:", len(result["proposals"]))
    elif args.action == "audit-hypotheses":
        from .autonomous_hypothesis import audit_proposals, save_report
        report = json.loads(Path(args.proposal).read_text(encoding="utf-8"))
        verdict = audit_proposals(report)
        print("Independent scientific evaluation:", save_report(args.out, verdict),
              "wins:", verdict["won_against_persistence"],
              "/", verdict["trials"])
    elif args.action == "propose-evidence-gated":
        from .evidence_gate import propose_gated
        from .autonomous_hypothesis import save_report
        result = propose_gated()
        print("Evidence-gated model proposals:", save_report(args.out,result),
              "decisions:",len(result["proposals"]))
    elif args.action == "audit-evidence-gated":
        from .evidence_gate import independent_audit as audit_gated_evidence
        from .autonomous_hypothesis import save_report
        proposals=json.loads(Path(args.proposal).read_text(encoding="utf-8"))
        result=audit_gated_evidence(proposals)
        print("Independent evidence-gated audit:",save_report(args.out,result),
              "guard wins:",result["guard_wins_against_persistence"],"/",result["trials"])
    elif args.action == "durable-research":
        from .durable_graph import run_persistent
        report=run_persistent(args.query, args.db, args.thread_id,
                              tool_keys=[t.strip() for t in args.tools.split(",")],
                              offline=True, optimize=("scipy.thermal" in args.tools))
        print("Persistent scientific graph:", save_json(args.out,report),
              "status:",report["status"])
    elif args.action == "durable-state":
        from .durable_graph import inspect_persistent
        report=inspect_persistent(args.db, args.thread_id)
        print("Recovered previous research:",save_json(args.out,report))
    elif args.action == "index-literature":
        from .federated_sources import search_federated
        from .global_sources import global_literature
        from .knowledge_index import index_federated
        search=(global_literature(args.query, offline=not args.online) if args.global_sources
                else search_federated(args.query, offline=not args.online))
        report=index_federated(args.db, search)
        report["provider_status"]=[{"provider":p["provider"],"status":p["status"]}
                                   for p in search["providers"]]
        print("Searchable bibliography:",save_json(args.out,report))
    elif args.action == "index-open-article":
        from .open_access import index_open_article
        report=index_open_article(args.db, args.pmcid)
        print("Licensed open-access paper indexed:",save_json(args.out,report))
    elif args.action == "search-knowledge":
        from .knowledge_index import search_index as local_search
        report=local_search(args.db, args.query)
        print("Citation-ready local library:",save_json(args.out,report),
              "records:",len(report["results"]))
    elif args.action == "import-public-memory":
        from .knowledge_index import import_verified_memory
        report = import_verified_memory(args.db, args.dir)
        print("Restored public research memory:",save_json(args.out,report),
              "references:",report["valid_paper_references_indexed"])
    elif args.action == "scientific-ecosystem":
        from .tool_registry import get_registry
        result=get_registry()
        result["published_api_keys_exposed"]=False
        print("Audited scientific tool ecosystem:", save_json(args.out,result),
              "entries:",len(result["tools"]))
    elif args.action == "openmm-reference":
        from .openmm_engine import reference_diatomic
        report=reference_diatomic(args.steps)
        print("OpenMM molecular-dynamics integration:",save_json(args.out,report),
              "energy drift:",report["relative_total_energy_drift"],
              "real molecular validation:",report["protein_dynamics_validated"])
    elif args.action == "discovery-pulse":
        from .discovery_watch import research_pulse
        report = research_pulse(args.topic)
        print("Journal/preprint/lab/video discovery:",
              save_json(args.out, report),"records:",report["distinct_records"],
              "unavailable:",report["sources_unavailable"])
    elif args.action == "creative-sources":
        from .creative_sources import creative_discovery
        report = creative_discovery(args.query)
        print("Art and music source metadata:",save_json(args.out,report),
              "providers:",report["source_count"])
    elif args.action == "creative-studio":
        from .creative_studio import write_studies
        report = write_studies(args.topic,args.seed,args.dir)
        print("Original art, music notation and ideas:",save_json(args.out,report))
    elif args.action == "youtube-updates":
        from .discovery_watch import youtube_url,parse_youtube,_read,YOUTUBE_CHANNELS
        if os.getenv("YOUTUBE_API_KEY"):
            from .youtube_api import from_environment
            channel_id=YOUTUBE_CHANNELS.get(args.channel,args.channel)
            report=from_environment(args.query,channel=channel_id)
            report["status"]="retrieved_metadata"
        else:
            try:
                videos=parse_youtube(_read(youtube_url(args.channel)))
                report={"channel":args.channel,"videos":videos,
                        "status":"retrieved_metadata",
                        "service":"public_youtube_atom_feed"}
            except Exception as exc:
                report={"channel":args.channel,"videos":[],
                        "status":"unavailable",
                        "error_type":type(exc).__name__,
                        "service":"public_youtube_atom_feed",
                        "next_step":"Configure private YOUTUBE_API_KEY secret for official API search"}
        report["transcripts_scraped"]=False
        report["videos_downloaded"]=False
        report["metadata_only"]=True
        print("YouTube public listing status:",save_json(args.out,report),
              "status:",report["status"],"videos:",len(report["videos"]))
    elif args.action == "compare-discovery":
        from .discovery_delta import compare_discovery
        snapshot=json.loads(Path(args.report).read_text(encoding="utf-8"))
        result=compare_discovery(snapshot,args.history)
        print("New public sources since prior archive:",save_json(args.out,result),
              "first-seen:",result["new_to_this_archive"])
    elif args.action == "invention-ideas":
        from .serendipity import hypotheses_from_sources
        report=json.loads(Path(args.report).read_text(encoding="utf-8"))
        output=hypotheses_from_sources(report)
        print("Speculative research-linked creative ideas:",
              save_json(args.out,output),"ideas:",output["idea_count"])
    elif args.action == "research-frontiers":
        from .research_frontiers import scan_frontiers
        result=scan_frontiers(args.query,online=args.online)
        print("Research funding and clinical-trial signals:",save_json(args.out,result),
              "records:",len(result["records"]),
              "verified breakthrough:",result["laboratory_breakthrough_confirmed"])
    elif args.action == "parametric-design":
        from .cad_studio import create_design
        report=create_design(args.dir,args.width,args.height,args.thickness,
                             args.hole_diameter,render=args.render)
        print("Parametric original design:",save_json(args.out,report),
              "mesh exported:",report["mesh_export_verified"])
    elif args.action == "music-analysis":
        from .music_analysis import analyze_original_music
        report=analyze_original_music(args.topic,args.seed)
        print("Original score music21 study:",save_json(args.out,report),
              "notes:",report["note_count"],
              "artistic novelty verified:",report["artistic_quality_or_originality_verified"])
    elif args.action == "world-horizon":
        from .world_horizon import scan_horizon
        report=scan_horizon(args.topic,category=args.category,online=args.online)
        print("Public research and world-intelligence horizon:",
              save_json(args.out,report), "sources checked:",
              report.get("providers_attempted",0),
              "actual returned items:",len(report["records"]))
    elif args.action == "horizon-catalog":
        from .world_horizon import source_catalog
        result=source_catalog()
        print("Public-source catalog:",save_json(args.out,result),
              "sources:",len(result["providers"]))
    elif args.action == "build-program":
        from .program_foundry import generate_program
        report=generate_program(args.kind,args.topic,args.dir)
        print("Original review-required program:",save_json(args.out,report),
              "files generated:",report["file_count"],
              "deployed:",not report["generated_program_has_not_been_deployed"])
    elif args.action == "universal-brief":
        from .universal_brief import build_universal_brief
        result=build_universal_brief(args.topic,online=args.online,limit=args.limit)
        print("Worldwide interdisciplinary research brief:",
              save_json(args.out,result),
              "source items:",result["cross_domain_ideas"]["source_record_count"],
              "reviewable idea questions:",result["cross_domain_ideas"]["concept_count"])
    elif args.action == "physics":
        print(json.dumps({
            "radius_m": args.radius_m,
            "circular_orbit_speed_m_s": circular_orbit_speed(args.radius_m),
        }))


if __name__ == "__main__":
    main()
