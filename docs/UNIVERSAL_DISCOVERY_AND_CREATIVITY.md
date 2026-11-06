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
