# Plenum Universal Discovery, Design and Creativity Network

Engineering status: 2026-11-06. This plan expands the screenshots of
scientific solvers, global knowledge, autonomous research and self-improvement
to art, music, architecture, literature, film, industrial design, invention,
laboratory updates, YouTube and cultural history.

## Scope and what is already working

Plenum is an **evidence-first coordinating architecture**, not a system that
automatically inherits the competence of every repository it catalogs.

| Capability | Current implementation | Honest status |
|---|---|---|
| Scholarly paper search | OpenAlex, Europe PMC, Semantic Scholar, arXiv, DOE OSTI | Real adapters, independent availability; some providers fail/rate-limit |
| Curated major-journal discovery | Crossref journal-ISSN search | 20 journals registered; six rotated per daily run |
| Cross-disciplinary publication discovery | Crossref topic-wide works query | Bounded newest metadata, not all world publications |
| Life-sciences preprints | Official bioRxiv and medRxiv metadata endpoints | Preprints explicitly unreviewed |
| Institutional and publisher news | MIT, NASA, Stanford, NIH, Nature RSS/Atom | Source-by-source, failures preserved |
| Public video | NASA channel Atom feed; arbitrary validated UC channel IDs | Public feeds may return HTTP 403 |
| Official YouTube metadata | Google YouTube Data API v3 optional secret-key adapter | **Not connected until owner sets private YOUTUBE_API_KEY** |
| Original creative work | SVG vector design, MusicXML musical score, JSON idea prompts | CPU Python generator, independent of generative AI model |
| Art/music heritage | Openverse openly-licensed image/audio metadata, The Met v1.1 Open Access catalog, MusicBrainz works | Read-only source metadata; no copies of music/art downloaded |
| Novel interdisciplinary questions | Source-linked speculative design/engineering/art/music cards | Automatically templated, **not invented or scientifically validated by AGI** |
| New-to-Plenum detection | Cross-run comparison of public archived DOI/link fingerprints | Tracks first observed in up to 120 stored snapshots |
| Daily research cadence | GitHub Actions scheduled for 10:37 UTC | GitHub scheduled runs can be delayed or skipped; no user alert service |
| Permanent public evidence | Daily report and first-seen cards on the `research-memory` branch | Stores public titles/links, not full copyrighted articles or video |
| Personal patent-safe knowledge | Separate owner-controlled private data storage | **Not created/deployed by this work** |

### Journal roster currently configured

Nature; Science; PNAS; Cell; Nature Communications; Physical Review Letters;
Nature Physics; Nature Photonics; Nature Materials; Nature Biotechnology;
The Lancet; New England Journal of Medicine; Science Advances;
Journal of the American Chemical Society; ACS Nano;
IEEE Transactions on Pattern Analysis and Machine Intelligence;
ACM Transactions on Graphics; Design Studies; Music Perception;
The Journal of Creative Behavior.

The daily monitor rotates six journals rather than polling all twenty every
day. It also searches the wider Crossref works database by topic. Six-of-twenty
is a deliberate, bounded sampling strategy, **not comprehensive coverage of
every journal, field, publisher or laboratory**.

References: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
https://api.biorxiv.org/details/biorxiv/help
https://www.nasa.gov/rss-feeds/
https://news.mit.edu/rss
https://metmuseum.github.io/
https://api.openverse.org/v1/

### November 9, 2026: invention-first research and ScienceDaily all-fields source

**Founder correction:** NOAA/USGS forecasting is two narrowly controlled tests, *not* Plenum's research domain or invention objective. Maintain broad discovery intake and original cross-disciplinary invention experiments in parallel. The existing daily `discovery-pulse.yml` covers 20 registered journals, rotating six daily, Crossref topic search, bioRxiv/medRxiv and university lab RSS. The original `world_horizon.py` already covers MIT, NIH, NSF, NASA, Nature, arXiv, Harvard, CAS, Chinese-affiliated OpenAlex, public engineering and institutional feeds. **Do not rebuild them.**

**New explicit, official source (added to both existing public-source registries):** [ScienceDaily all-science RSS](https://www.sciencedaily.com/rss/all.xml) as a **secondary discovery-alert feed**. Its official [RSS catalog](https://www.sciencedaily.com/newsfeeds.htm) states it covers all science and is frequently updated. The daily discovery pulse checks up to 30 feed headlines to avoid missing developments from unrelated fields, maintains strict ScienceDaily link-host boundaries, archives only the short headline, date and original URL, and gives each item `secondary_science_news_not_primary_research` evidence status. A mirrored all-fields `world_horizon` adapter reuses the existing bounded RSS parser and `lab_radar` deduplication. The same story may appear in both; deduplicate by canonical source/DOI and **do not treat two echoes of the same press release as independent reproduction**. Feeds may be unavailable, delayed or incomplete; no claim of exhaustive science monitoring or privileged access.

**Original founder example, with dates and scope clearly separated:** [ScienceDaily (9 Nov 2026)](https://www.sciencedaily.com/releases/2026/11/261105224536.htm) reports an **exciton-polariton supersolid** at room temperature. The underlying [University of Warsaw Faculty of Physics announcement (3 Nov 2026)](https://m.fuw.edu.pl/press-release/news10489.html) cites [Muszyński et al., *Science Advances* 12, eaee4875 (2026), DOI 10.1126/sciadv.aee4875](https://www.science.org/doi/10.1126/sciadv.aee4875), with partners at the Military University of Technology, IBM Research Zurich and CNRS. The observed quantum state uses a liquid-crystal optical microcavity and organic semiconductor, not everyday free light becoming literal bulk solid and liquid. The researchers report brief polariton lifetimes, self-organized spatial fringes, and material compatibility issues limiting sample lifetime to hours. Work at room temperature does **not** establish a functional commercial light computer, sensor, reproducible scalability or a patented Plenum device. Seek source methods and license; don't manufacture numbers or reproduce proprietary details.

**Every credible breakthrough should enter the existing research-to-invention decision path:**

1. **Detect, de-duplicate and date:** source URL, observed news date, university/lab source date, actual research publication date, DOI, version, and geographic/institutional provenance.
2. **Triangulate primary methods:** what did researchers ACTUALLY demonstrate, what was inferred, experimental controls, uncertainties, limitation and contradictory sources; distinguish press releases, preprints, peer-reviewed papers and independently replicated experiments.
3. **Identify the open bottleneck:** lifespan, reproducibility, energy, temperature, scaling, materials, stability, manufacturing, precision, cost, speed, throughput, safety, or tool capability. Ask whether mature science/software/engineering solutions already address it.
4. **Propose constrained invention hypothesis:** articulate the new and **unverified** controllable design variable(s), cause-effect mechanism and measurable advantage relative to a grounded baseline. Do not call this verified novelty, patentability or a working invention.
5. **Choose a minimal falsification test:** published-scope numerical/analytical feasibility first, licensed simulator only when it can actually discriminate proposed mechanisms, then a small experiment if feasible; identify quantitative target, comparator, negative control, materials and independent investigator review.
6. **Preserve evidence and choose next action:** archive only source-linked PUBLIC facts, test plan and negative findings in appropriate public evidence; store confidential Plenum inventive steps, trade secrets, patents, process ideas and results **only privately**. Independently recheck original contribution, patent landscape and rights before external disclosure or claims.

**Example minimal next test (hypothesis only):** For the room-temperature polariton supersolid, the *observed public bottleneck* is reaction of the semiconductor and liquid-crystal medium. A legitimate research question is whether a published, compatible interfacial barrier or an alternative publicly characterized semiconductor changes optical quality, stability and lifetime while preserving coupling and supersolid indicators, under paired matched controls. The actual interface design, optical parameters, fabrication/simulation and quantitative performance must come from authorized primary methods and materials data before any measurement claim. This is **not** a discovered solution, and Plenum's private invention plans should not be committed to this public repository.

### Research evidence classes

1. Journal publication record: article metadata is deposited by a publisher,
   but peer review, retractions, raw data and claims are not independently
   confirmed by Crossref alone.
2. Preprint: explicitly **not peer reviewed**. Clinical implications must not
   be inferred from a preprint.
3. Research institution or journal news: an announcement can report a
   result, but it is not the underlying primary evidence.
4. Video: upload title, link and date only. A video is not an experimental
   record or a licensed transcript.
5. Research idea: generated speculative question, not established mechanism,
   measured performance, freedom-to-operate opinion or verified invention.

Always preserve author, DOI/URL, date and evidence class. The system must
follow citation trails, mark corrections/retractions, identify conflicting
studies and validate new ideas before any promotion.

## Creative studio on iPad

Open **Actions → Plenum Research Control Center → Run workflow** and choose:

- `creative`: search public images/artwork and music work metadata, then
  output editable `geometric_study.svg`, `original_score.musicxml`
  (32 quarter notes) and `interdisciplinary_ideas.json`.
- `discovery`: run the wide research feed, compare with archived records,
  and create a source-grounded interdisciplinary idea JSON.
- `youtube`: fetch public channel metadata, or use official Data API if
  an owner key has been configured.
- `knowledge`: rehydrate approved public research memory and use five
  existing scholarly metadata services.

Alternatively run the individual **Creative Studio and Open Culture
Discovery** or **Daily Journals Labs Preprints and YouTube Discovery**
workflows. Download generated GitHub artifacts before 14-day expiration.

**These creative sketches are original algorithmic works**, not a complete
painting, sound-generation, CAD engineering or sophisticated film editing
system. Opening the MusicXML score in an appropriate notation program
allows editing; the GitHub Actions workflow does not play audio.

## What the expanded screenshot-plus-creative registry includes

Scientific references already inventoried: Lean 4, DiffDock, OpenMM,
PySCF, pymatgen, SU2, PyBaMM, Astropy, NASA OpenMDAO, NASA Aviary, GMAT,
ToolUniverse, K-Dense Scientific Skills, Biomni, Sakana AI Scientist v2,
Karpathy AutoResearch, LangGraph, and evaluation/training frameworks.

Art, design and architecture candidates: Blender, FreeCAD, OpenSCAD,
KiCad, Inkscape, Krita, Godot, p5.js, procedural vector design,
multidisciplinary optimization and CAD assembly verification.

Music and sound candidates: MuseScore, LilyPond, Sonic Pi,
SuperCollider, Magenta, original MusicXML and MusicBrainz/Openverse
metadata. Existing copyrighted compositions may be analyzed or
reproduced only with appropriate permission and applicable law.

Further worthwhile integrations, **not implemented yet**:

- Books, art and music history: Library of Congress, Europeana,
  Smithsonian Open Access, Project Gutenberg and permitted
  Internet Archive materials.
- Physics and spatial datasets: CERN open data, NASA Earthdata,
  ESA Copernicus, USGS, NOAA, astronomic archives and Earth observation.
- Biology and medicine: PubMed/E-utilities, PubChem, clinical-trial
  registries, protein structures, gene/protein knowledge and controlled
  biomedical solvers.
- Industrial engineering: OpenUSD, IFC/BIM, ROS 2, FreeCAD simulations,
  KiCad electrical validation, 3D printing and robotic manufacturing.
- Real-time research: funder awards, conference proceedings, ROR/ORCID
  affiliations, patent filings, standards and corrected/retracted papers.
- Humanities and society: linguistics, economics, legal scholarship,
  social science research, education, history and archival collections.
- Multimodal reasoning: image and diagram interpretation, instrument
  data, original audio composition, film, photonic design and creative
  evaluation. A more capable appropriately licensed model is required.
- Better scientific originality: blind multibenchmark evaluations,
  adversarial review, simulations, independent replication and
  human-controlled candidate training/improvement.

These are future research connectors, not approved external-code
execution or unlicensed dataset collection.

## YouTube connection details

Plenum supports public channels by a NASA alias or a user-provided canonical
`UC...` channel ID at a fixed Google-hosted feed URL. This public feed
sometimes rejects GitHub traffic. A blocked feed is explicitly reported.

For more reliable searching, use the Google-hosted **YouTube Data API v3**.
The official adapter accepts `YOUTUBE_API_KEY` via a private environment
variable and returns only video ID, source, title, publication time and link.
It does not log or persist the key. To activate within GitHub Actions:

1. Create or use a Google Cloud project controlled by the repository owner.
2. Enable YouTube Data API v3 and create a restricted API key.
3. Set repository Actions **secret** `YOUTUBE_API_KEY`.
4. Choose `youtube` from Plenum Research Control Center and supply a
   public query and valid channel ID. Optional daily NASA search uses the
   same configured secret.

These steps need the owner to authorize the Google API project and secret;
the key must never be pasted in the public repository or this document.
Provider quotas and terms apply. Caption enumeration/download is a
separate, usually OAuth-authorized feature; a video description is **not**
a transcript and publicly viewable video is not free content for reuse.

An optional connected YouTube-specialist app in ChatGPT may assist with
creator ideas, video discovery and permitted transcript analysis; its
installation and account connection are independent of the GitHub adapter.

## Daily automation and evidence archive

The public GitHub workflow is scheduled at **10:37 UTC**. It retrieves
bounded scholarly and institutional metadata, creates tentative
interdisciplinary questions, marks failed sources, compares against up
to 120 archived earlier snapshots, and appends a public evidence file to
the `research-memory/evidence/discovery` folder. Each run has its own
immutable filename. Read-only retrieval runs without write privileges;
only the archive job may write and only under the monitored public
research-memory branch.

This is source monitoring, **not** a continuously running AGI, a trained
foundation model, a full-web or full-text crawler, a YouTube transcript
scraper, or an instant push notification to the user's iPad.

The best next step after collecting enough actual data is an independent
model-led review of method quality, citation trails and reproducibility,
not more unverified assertions of breakthroughs.

## Live verification results, November 6, 2026

- Original design, music notation and open-media reference run
  [42169012086](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42169012086)
  **passed**. Original SVG, 32-note MusicXML, and interdisciplinary idea JSON
  created. All four metadata API providers responded; Openverse images
  returned 3 references, MusicBrainz returned 3 music-work references;
  the audio and Met object queries returned zero matching references for
  that specific topic. No media files were downloaded or reproduced.
- Cross-disciplinary scheduled discovery run
  [42170083885](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42170083885)
  **passed both collection and permanent archival**.
  It preserved 35 source-linked journal/preprint/lab/video metadata records,
  archived 8 unverified design/science question cards and compared against
  4 previous public reports. All 35 current links were previously seen,
  so **zero new-to-archive records** were claimed.
  Nature Photonics, Stanford News and public NASA YouTube feed were
  marked unavailable in that run; success does not imply all sources worked.
- The full engineering regression workflow
  [42169911385](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42169911385)
  **passed** after adding structured YouTube API tests and the
  interdisciplinary discovery archive.
- The Google YouTube Data API key is **not configured**; no actual
  owner-authenticated YouTube API connection is asserted. Caption
  extraction, proprietary videos and unrestricted downloads are not enabled.

All source-specific failures remain observable and do not invalidate
the successful independent parts of the research platform. As
additional sources and tools are added, each must be separately tested
and governed by access, license, cost and evidence-quality boundaries.

## November 6 expansion: funded labs, trials and practical 3D design

**Two more read-only research sources:** U.S. National Science Foundation
public award metadata and ClinicalTrials.gov v2 registered-study metadata
are now available through `plenum research-frontiers --query "public topic"
--online` and the iPad control-center `frontiers` option. The scheduled
[Funded Labs and Clinical Research Signals workflow](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/workflows/research-frontiers.yml)
runs daily at 11:05 UTC and saves an immutable source-linked report on the
public `research-memory` branch. The first complete run
[42170871194](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42170871194)
succeeded. It retrieved **3 actual NSF grant records**, while its narrowly
specified clinical query matched **0 trials**. Zero matches is not a provider
outage. Awards and registrations signal *research activity*, not verified
results, medical efficacy or patents.

**Design beyond static images:** OpenSCAD can now generate an editable original
parametric panel file (`.scad`) and export its 3D STL geometry, using
`plenum parametric-design --render`. The isolated
[OpenSCAD CAD workflow](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42171089502)
passed. Dimensions are explicitly bounded; there are no validated material
properties, load paths, fastener engineering, fatigue data or manufacturing
tolerances. No proposed CAD shape should be manufactured as a structural
component without professional review.

**A broader original-ideas space:** Plenum's procedural concept studies now
cover literary art, cinema, poetry, photography, games, choreography,
architecture, sound design, materials, community design, and other existing
creative/scientific intersections. These remain original prompt templates,
not claims of a novel invention, sophisticated trained generative art, or
human-equivalent creative judgment.

**YouTube status:** the official, metadata-only Data API adapter is already
implemented and can search broadly if an authorized Google API key is added
as the `YOUTUBE_API_KEY` GitHub Actions repository secret. The public
channel feed often returns HTTP errors from GitHub runners. Without the key,
there is no verified general YouTube search connection inside Plenum.
Captions, videos, third-party recordings, unlicensed scores, and audio are
not downloaded.

**Broader planned creative engines:** FreeCAD, Blender, music21, LilyPond,
MuseScore, Inkscape, Krita, Godot, p5.js, Sonic Pi, SuperCollider, Magenta,
Wikimedia Commons, the Library of Congress and Smithsonian Open Access
are inventoried for selective, rights-reviewed adapters. Merely being
catalogued does not mean an engine is installed or operational. Future
research directions include digital humanities, economics, engineering
manufacturing, archaeology, ethics, design criticism, patent prior art,
replication and open-data provenance.

## Additional November 6 cultural catalog and real music analysis

The [Library of Congress public JSON API](https://www.loc.gov/apis/json-and-yaml/requests/)
has been added as a fifth cultural discovery adapter for historical books,
photos, maps, film and notated music **metadata**. Its schema and rights
safeguards passed independent tests. The live GitHub request returned a
timeout in [Creative Studio run 42171554503](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42171554503).
Consequently, the **adapter is tested but live Library of Congress access
is not yet confirmed**. No library score, media or photograph was
downloaded. Smithsonian Open Access and other collections remain separately
credentialed or reviewed, not silently activated.

A new optional computational musicology engine,
[music21](https://github.com/cuthbertLab/music21), has now been integrated.
It analyzes the original 32-note, eight-measure Plenum MusicXML study, reports
pitch-class distribution and melodic intervals, and records that originality,
artistic merit and musical composition ability are unproven. The isolated
[music21 live test 42171857399](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42171857399)
passed. It does not play or synthesize any copyrighted score.

The founder control center now includes `music-analysis` alongside
`parametric-design`, `creative`, `frontiers`, `discovery`, `knowledge`,
`science`, `youtube` (public channel feed or owner-authorized official API),
and the existing approved research functions.

### Continuing scientific-source limitations
No single API or feed provides guaranteed real-time coverage of every
laboratory, leading journal, submitted manuscript or discovery. Crossref
metadata can precede or lag a publisher posting; paper indexing and
publication dates are not interchangeable. Lab news is not independent
replication, a registered clinical trial is not efficacy evidence,
and a funded NSF grant is not proof of a completed experiment.

Full journal article text generally requires permission or the relevant
institutional/open-access rights. Automated YouTube-wide video searches
inside the GitHub system require an owner-approved private
`YOUTUBE_API_KEY`; no such key has been installed or exposed. Research
videos may be cited by title and URL, but no private captions, recordings,
lyrics or copyrighted content are downloaded.
