# Biosecurity Atlas — Sprint Roadmap

## Goal

Build an interactive network graph mapping the intersection of **biosafety/biosecurity** and **artificial intelligence**: who funds what, who researches what, and how the funding landscape connects to the research community.

## Philosophy

Every sprint produces a **shippable, verified increment**. If Sprint N breaks, Sprints 1 through N-1 stay live. Data from each source is fetched, saved as raw files, validated independently, then merged. No hallucinated edges — every edge must trace to a downloadable source file.

### Anti-hallucination protocol

```
1. FETCH   → save raw file to data/raw/ (CSV, JSON, HTML snapshot)
2. EXTRACT → parse raw file, produce candidate edges with matched_text
3. VALIDATE → run assertions, flag LOW confidence, write to data/staged/
4. HUMAN REVIEW → review flagged items before merge
5. MERGE   → only after review, merge into data/graph_data.json
```

**Rule: if you can't point to a line in a raw file, the edge doesn't exist.**

---

## Graph Architecture

```
DIRECTION 1: Funding Chain (top-down)
─────────────────────────────────────
Funders (Coefficient, NIH, DARPA, IARPA...)
    ↓ funds / contracts
Programs / Focus Areas
    ↓
Recipient organisations / labs
    ↓
Researchers / PIs

DIRECTION 2: Workshop Ecosystem (bottom-up)
───────────────────────────────────────────
NeurIPS 2025 BioSafe GenAI Workshop papers
    ↓ authored
Authors / researchers
    ↓ current_affiliation / past_affiliation
Institutions
    ↕ BRIDGE NODES ↕ (appear in both layers)

DIRECTION 3: Policy & Big Tech (lateral)
────────────────────────────────────────
AI companies ↔ biosecurity eval orgs ↔ policy bodies
    ↓ biosecurity_eval / policy_forum / published_study
Publications & reports

DIRECTION 4: Cross-venue & Key Personnel
─────────────────────────────────────────
Sibling workshop papers (MLGenX, GenAI4Health, AI4Science)
    ↓ authored (shared authors = cross-venue bridges)
Key personnel research footprint (NIH grants, Semantic Scholar pubs)
```

**Rule: no orphan nodes.** Every node must have at least one edge.

---

## Methodology

### Data Collection

The atlas is constructed through 12 iterative sprints, each adding one verified data source. Data sources include public APIs (OpenReview, NSF Awards, NIH RePORTER, UKRI Gateway to Research, Semantic Scholar), public databases (Coefficient/Open Philanthropy grants CSV), and manually curated policy documents (DARPA program announcements, biosecurity evaluation reports).

Each sprint follows the anti-hallucination protocol (above): raw data is fetched, saved, parsed into candidate edges with source references, validated independently, reviewed, and only then merged. No AI-inferred edges are permitted — every connection must trace to a downloadable source file.

### Relevance Criteria

After Sprint 12, a systematic relevance audit was performed across all edges to ensure every connection is genuinely about the intersection of biosafety/biosecurity and AI. Edges were evaluated on two axes:

- **Biosafety/biosecurity axis**: Does this work address biological risk, dual-use potential, pathogen containment, gene drive safety, pandemic preparedness, or governance of biological capabilities?
- **AI/computational axis**: Does this work involve machine learning, language models, computational biology, AI-enabled tools, or automated systems?

Edges that scored on only one axis (e.g., pure CRISPR biology without AI, or pure ML theory without bio) were removed during the audit. Borderline cases (e.g., SARS-CoV-2 genomic surveillance, biocontainment via recoded genomes) were retained with documentation.

The audit removed 11 off-topic Semantic Scholar publications, 6 single-axis NSF grants, and 1 off-topic UKRI grant. It also added 9 missing `biosecurity_eval` edges, 53 `part_of` edges linking presentations to their source workshops, and 2 author nodes for an Epoch AI publication.

### Quality Assurance

A 14-point automated quality check (`scripts/quality_check.py`) runs after every graph modification, testing for dangling references, duplicate IDs, orphan nodes, valid edge/node types, grant amount completeness, and graph connectivity (target: >80%; current: 100%).

### Analysis

Supplementary analysis is available in `analysis_biosecurity_atlas.ipynb`, which generates 14 figures exploring funding concentration, research topics, cross-venue author overlap, geographic distribution, bridge institutions, degree distributions, and audience-specific insights. All figures read directly from `data/graph_data.json` and are reproducible.

## Node Schema

| Type | Key Fields | Count (current) |
|------|-----------|-----------------|
| `funder` | id, label, short, url, description | 8 |
| `program` | id, label, parent→funder, url, subtype (nih_grant/nsf_grant/ukri_grant/wellcome_grant/barda_contract/cepi_grant), year, year_start | 53 |
| `org` | id, label, entity_type, url, country | 178 |
| `institution` | id, label, url, lat, lon, location, country (Sprint 12) | 169 |
| `author` | id, label, url, details | 238 |
| `presentation` | id, label, url, subtype (poster/oral/workshop), year, venue | 57 |
| `publication` | id, label, url, subtype (research_paper/research_report), year, citation_count | 27 |
| `department` | id, label, parent→institution | 8 |

`org.entity_type`: `institution` / `org` / `individual` / `pooled_grant`

## Edge Schema

| Type | Direction | Key Fields | Count (current) |
|------|-----------|-----------|-----------------|
| `funds` | funder/program → org/inst | amount, date_range, grant_title, confidence | 291 |
| `authored` | author → presentation | — | 254 |
| `current_affiliation` | author → institution | — | 221 |
| `past_affiliation` | author → institution | — | 137 |
| `part_of` | department/presentation → institution/workshop | — | 68 |
| `performs_on` | PI → program | — | 31 |
| `biosecurity_eval` | evaluator → publication/report | evidence | 26 |
| `policy_forum` | org → publication | — | 31 |
| `published_study` | author → publication | — | 23 |
| `organized` | author → workshop event | — | 10 |
| `invited_speaker` | author → workshop event | — | 10 |
| `co_authored_with` | author ↔ author (≥3 shared papers) | shared_papers | 11 |
| `contracts` | program → org | amount, confidence [planned] | — |

---

## Sprint 1: Workshop Ecosystem ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Results:**
- 350 nodes, 479 edges
- 38 papers (6 oral, 32 poster), 138 authors, 166 institutions, 8 departments
- Source: OpenReview API (`api2.openreview.net`)

**Scripts:** `extract_data.py` → `build_graph.py` → `generate_html_v3.py`

---

## Sprint 2: Coefficient (prev. Open Philanthropy) — Core Biosecurity ✅ COMPLETE

**Status:** Shipped. Merged into graph.

**Scope:** All grants in Coefficient's public CSV (`op_grants_full.csv`, 2,714 rows) for:
- Focus areas: "Biosecurity & Pandemic Preparedness", "Science Supporting Biosecurity and Pandemic Preparedness"
- All other focus areas: bio-relevance keyword filter (`BIO_REL` regex) applied to grant title + org name
- Excluded focus areas: "Alternatives to Animal Products", "Farm Animal Welfare" (false-positive risk)
- Grant-level blocklist: canine cancer vaccine, reproductive biology, gut microbiome repair, plant protein optimisation, therapeutic food aid, syphilis economic research

**Results (Sprints 2+3 combined, same pipeline):**
- 272 grants, 156 grantee nodes, $543M
- 16 focus-area program nodes
- 21 BRIDGE_MAP entries → 19 active bridge nodes

**Key decisions:**
- `individual` entity type → full grant title as node label (context in title)
- All other entity types → canonical org name as node label; full title stored on edge as `grant_title`
- Alias table: RAND, JHU typo, iGEM ×3, BERI, Biosecure
- Institution keyword check runs BEFORE person regex to prevent false positives on two-word org names

**Scripts:**
```
s2_fetch_op_grants.sh      → data/raw/op_grants_full.csv
s2_extract_op_grants.py    → data/staged/op_edges.json
s2_validate_op.py          → data/staged/op_validation_report.json
s2_merge_op.py             → data/graph_data.json (updated)
quality_check.py           → 14/14 ✅
generate_html_v3.py        → index.html (502 nodes, 767 edges, $543M, 19 bridges)
```

**Known issue:** `grant_title` is stored on every `funds` edge but is not yet surfaced in the detail panel UI. Clicking a node shows funding totals and connected nodes but not individual grant titles. Fix planned: expand `showInfo()` in `generate_html_v3.py` to render grant titles in the funds connection list.

---

## Sprint 3: NIH Federal Funding

**Goal:** Add federal biomedical research grants for university labs with workshop authors.

**Data source:** NIH RePORTER API
```
POST https://api.reporter.nih.gov/v2/projects/search
```

**Filter strategy:** Query by institution (those with workshop authors) + biosecurity/AI keyword terms. Do NOT query all NIH grants — far too broad.

**Target institutions** (those with workshop authors):
- Harvard University → `["HARVARD UNIVERSITY"]`
- Stanford University → `["STANFORD UNIVERSITY"]`
- Princeton University → `["PRINCETON UNIVERSITY"]`
- UC Berkeley → `["UNIVERSITY OF CALIFORNIA BERKELEY"]`
- MIT → `["MASSACHUSETTS INSTITUTE OF TECHNOLOGY"]`
- University of Pennsylvania → `["UNIVERSITY OF PENNSYLVANIA"]`

**Known API issues:**
- `org_names` must be a flat list of strings (not `{"any_of": [...]}`)
- Org names must match NIH canonical names exactly
- International institutions (Oxford, Imperial) won't appear in NIH

**Scripts:**
```
scripts/s3_fetch_nih.py         → data/raw/nih_results_{org}.json
scripts/s3_extract_nih.py       → data/staged/nih_edges.json
scripts/s3_validate_nih.py      → data/staged/nih_validation_report.json
scripts/s3_merge_nih.py         → data/graph_data.json (updated)
```

---

## Sprint 4: DARPA / IARPA Programs

**Goal:** Map US government biosecurity programs (DARPA Biological Technologies Office, IARPA) to their performers. Show which workshop-affiliated labs are government contractors.

**Data strategy:**
1. **Primary source — USASpending.gov API**: Federal contract/grant data with amounts, dates, recipient names. Filter by awarding agency (DARPA = `97-6800`, IARPA = `97-0200`) + award description keywords. Clean, machine-readable, authoritative.
   ```
   POST https://api.usaspending.gov/api/v2/search/spending_by_award/
   ```
2. **Secondary source — DARPA program pages**: For performer attribution when USASpending shows aggregate lab names.
   ```
   https://www.darpa.mil/research/programs/{slug}
   ```
3. **Tertiary — press releases / BAA awards**: For individual contracts not in USASpending.

**Programs to include:**

| Program | Agency | Slug / ID | Focus | Known performers |
|---------|--------|-----------|-------|-----------------|
| P3 — Pandemic Prevention Platform | DARPA | `pandemic-prevention-platform` | Rapid antibody countermeasures (60-day response) | AbCellera (~$30M), Vanderbilt U., Duke U. (DHVI), AstraZeneca/MedImmune |
| PREEMPT — PREventing EMerging Pathogenic Threats | DARPA | `preventing-emerging-pathogenic-threats` | Zoonotic reservoir containment | UC Davis ($9.4M), Institut Pasteur, Montana State, Pirbright Institute, Autonomous Therapeutics |
| SAFE GENES | DARPA | `safe-genes` | Safe gene editing | Broad Institute, MIT, Harvard |
| PREPARE — PREemptive Expression of Protective Alleles | DARPA | `preemptive-expression-protective-alleles-response-elements` | Gene-encoded broad-spectrum protection | Multiple universities |
| Fun GCAT — Functional Genomic and Computational Assessment of Threats | **IARPA** | `fun-gcat` | Genomic threat detection | SRI, Harvard, Battelle, Virginia Tech, LLNL, JHU APL |

**Scope filter:** Only performers that are already in the graph (workshop institutions or Coefficient grantees), OR performers at institutions that could plausibly bridge to the workshop community. Do NOT add every DARPA/IARPA performer — that expands scope too broadly.

**Confidence protocol:**
- Performer found in fetched page text or USASpending record → HIGH
- Known from press release but not in fetched data → MEDIUM, flag for review
- Page returned 403/404 → LOW, flag, do not add
- **NEVER add an edge based on AI inference alone**

**Known issues:**
- DARPA URL structure: `/program/X` (old) → `/research/programs/X` (current)
- IARPA returns 403 for automated scraping — use USASpending.gov API instead
- DARPA program pages list performers by name only (no contract amounts) — pair with USASpending for amounts
- P3 note: AbCellera's ~$30M contract announced March 2018; Vanderbilt and Duke amounts not publicly stated
- PREEMPT note: UC Davis award $9.37M confirmed in university press release
- Fun GCAT note: This is IARPA, NOT DARPA — a common misattribution

**Scripts:**
```
scripts/s4_fetch_darpa.py           → data/raw/darpa_{program}.html
scripts/s4_fetch_usaspending.py     → data/raw/usaspending_{agency}.json
scripts/s4_extract_performers.py    → data/staged/darpa_edges.json
scripts/s4_validate_darpa.py        → data/staged/darpa_validation_report.json
scripts/s4_merge_darpa.py           → data/graph_data.json (updated)
```

---

## Sprint 4b: Fix DARPA PI→Program Connections (Hotfix)

**Goal:** Create missing program nodes (SAFE GENES, P3, PREEMPT, PREPARE) and connect 13 DARPA PI author nodes to their programs.

**Status:** Identified during Sprint 5 dry run. 13 PI nodes (George Church, Jennifer Doudna, Harris Wang, etc.) have `current_affiliation` edges only — no connection to their DARPA programs.

**Gap:**
- Missing program nodes: `program_darpa_safe_genes`, `program_darpa_p3`, `program_darpa_preempt`, `program_darpa_prepare`
- Missing edges: PI → program (`pi_of` or `performs_on` edge type)
- Missing edges: program → DARPA funder (`funds` edge, hierarchy)
- Missing edges: program → institution (`funds` edge, from press release performer data)

**Data sources:** Already saved in `data/raw/s4_darpa_iarpa/darpa_programs_performers.json` + news release `.md` files.

---

## Sprint 5: Policy & Big Tech Layer — Biosecurity Evaluations ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Map AI companies' biosecurity evaluation relationships, third-party eval partnerships, and policy forum participation.

**Results:**
- 27 new nodes: 9 publications, 12 authors, 5 orgs, 1 institution
- 47 new edges across 7 types
- Key new edge types: `biosecurity_eval` (10), `policy_forum` (6), `published_study` (1)
- Key new node type: `publication` (9 nodes)
- Added xAI, US AISI, OSTP, Deloitte, Council on Strategic Risks, Epoch AI as org nodes
- 9 publication nodes (RAND studies, SecureBio OSTP RFI, Epoch AI analysis, Anthropic red team blog, NTI forum statement, LAB-Bench paper, OpenAI+Gryphon bio threat study)
- 12 new author nodes (SecureBio team, Gryphon staff, RAND researchers, OpenAI bio safety lead)

**Verified Relationships:**

| Evaluator | Evaluated Lab | Models | Evidence | Confidence |
|---|---|---|---|---|
| SecureBio | Anthropic | Claude 3.7 Sonnet, Claude 4 | SecureBio substack, Epoch AI analysis | HIGH |
| SecureBio | OpenAI | GPT-4.5, o3-mini, o4-mini | SecureBio substack | HIGH |
| SecureBio | Google DeepMind | Gemini 2.5 Pro | SecureBio substack | HIGH |
| SecureBio | xAI | unspecified | SecureBio substack | MEDIUM |
| Gryphon Scientific | OpenAI | GPT-4 | OpenAI blog + VentureBeat | HIGH |
| RAND Corporation | 30+ models | various | RAND publications | HIGH |
| UK AI Safety Institute | Anthropic | Claude 3.5 Sonnet | FedScoop, Epoch AI | HIGH |
| UK AI Safety Institute | OpenAI | o1 | Epoch AI analysis | HIGH |
| FutureHouse | multiple | LAB-Bench | Epoch AI analysis | MEDIUM |

**Data sources:** SecureBio substack, OSTP RFI PDF, Epoch AI biorisk analysis, RAND publications, NTI AIxBio Forum, OpenAI blog, Gryphon Scientific

**Raw data:** `data/raw/s5_policy_bigtech/` (8 files)

**Scripts:**
```
scripts/s5_extract_policy_bigtech.py   → data/staged/s5_nodes.json (27), s5_edges.json (47)
notebooks/s5_policy_bigtech_exploration.ipynb  ← dry run notebook
```

---

## Sprint 6: Workshop Organizers & Invited Speakers ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Add workshop organizers and invited speakers as structurally important nodes, creating a central event anchor and connecting key figures who shape the biosafety+AI research agenda.

**Results:**
- 23 new nodes, 38 new edges → 607 nodes, 936 edges total
- Created workshop event anchor: `event_neurips_biosafe_genai_2025`
- 10 organizers (7 main + 3 student) with `organized` edges
- 10 invited speakers with `invited_speaker` edges
- New institutions: UCF, MBZUAI, Université de Montréal
- New orgs: Mila, CZI, NIST, Nebius, Iris Medicine, Kelonia Therapeutics, Petuum
- Structural edges: Mila→UdeM (part_of), US AISI→NIST (part_of)

**Organizers:** Mengdi Wang (Princeton), Le Cong (Stanford), Kevin Esvelt (MIT), Zaixi Zhang (Princeton), Ruofan Jin (Princeton), Amrit Singh Bedi (UCF), Alvaro Velasquez (UC Boulder), Souradip Chakraborty (UMD), Pratyush Maini (CMU), Amin Karbasi (Yale)

**Invited Speakers:** Yoshua Bengio (Mila), Jian Ma (CMU), Sheng Lin-Gibson (NIST), Peter Henderson (Princeton), Le Cong (Stanford), Eric Xing (Petuum/MBZUAI), Eugene Shakhnovich (Harvard), Jason Wei (OpenAI), Tegan Maharaj (Mila), Silvio Micali (Algorand)

**Source:** Workshop website (`biosafe-gen-ai.github.io`)

**Known fix applied:** Removed duplicate `inst_Shanghai_Jiao_Tong_University` (Sprint 6 creation) — pre-existing node was `inst_Shanghai_Jiaotong_University` (Sprint 1).

**Scripts:**
```
scripts/s6_extract_organizers_speakers.py   → data/staged/s6_nodes.json (23), s6_edges.json (38)
```

---

## Sprint 7: Cross-venue Expansion ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Add papers from sibling workshops where ≥1 author already exists in the graph. This surfaces cross-venue research bridges — researchers presenting biosafety+AI work at multiple venues.

**Results:**
- 74 new nodes (15 presentations, 59 new co-authors), 86 new edges → 681 nodes, 1,022 edges total
- 92.6% graph connectivity

**Workshops queried (via OpenReview API):**

| Workshop | Papers Found | Author Overlap |
|---|---|---|
| ICLR 2025 MLGenX (Machine Learning for Genomics Explorations) | 41 | 3 papers |
| NeurIPS 2025 GenAI4Health (Generative AI for Health) | 164 | 8 papers |
| NeurIPS 2025 AI4Science (AI for Science) | 200 | 5 papers |

**Key cross-venue bridges discovered:**
- Jennifer Doudna (CRISPR pioneer) — AI4Science paper on genome editing + AI
- Kevin Esvelt (MIT Media Lab) — AI4Science paper on gene drive modeling
- Multiple Princeton/Stanford authors spanning BioSafe GenAI + MLGenX

**Method:** Queried `api2.openreview.net/notes/search` for each workshop venue ID, extracted all paper titles and author lists, then checked each author against existing graph nodes using lowercase + first-last name fuzzy matching. Papers with ≥1 author overlap were included; all co-authors of qualifying papers were added as new author nodes. Deduplicated 16 raw overlap papers to 15 unique (1 appeared in multiple workshops).

**Note:** Initially planned NeurIPS SoLaR, ICLR ML for Drug Discovery, and ACL/EMNLP workshops, but these either had no OpenReview presence or no author overlap. MLGenX, GenAI4Health, and AI4Science proved far richer.

**Scripts:**
```
scripts/s7_extract_cross_venue.py   → data/staged/s7_nodes.json (74), s7_edges.json (86)
data/raw/s7_cross_venue/mlgenx_papers.json          (41 papers)
data/raw/s7_cross_venue/genai4health_papers.json     (164 papers)
data/raw/s7_cross_venue/ai4science_papers.json       (200 papers)
data/raw/s7_cross_venue/overlap_analysis.json        (16 overlap papers → 15 unique)
```

---

## Sprint 8: Key Personnel Research Projects & Lab Outputs ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Trace the research footprint of key biosafety+AI personnel beyond the workshop — their NIH grants, key publications, and institutional connections. Adds NIH as a 4th funder and surfaces $35M in active federal research funding.

**Results:**
- 44 new nodes, 97 new edges → 725 nodes, 1,119 edges total
- NIH funder node (4th funder after DARPA, IARPA, Coefficient)
- 29 NIH grant program nodes ($35M across 31 unique projects)
- 12 key publications from Semantic Scholar (top-cited bio+AI papers)
- 2 new institutions: Gladstone Institutes, Whitehead Institute (+ part_of MIT edge)
- Total tracked funding: $693M (DARPA $589M + Coefficient $69M + NIH $35M)

**Key personnel scored (weighted: degree + DARPA PI bonus + organizer/speaker bonus):**

| PI | Source | Grants Found | Key Publications |
|---|---|---|---|
| Kevin Esvelt | NIH RePORTER + S2 | 5 grants | 3 papers (gene drive, CRISPR) |
| George Church | NIH RePORTER + S2 | 4 grants | 3 papers (genome writing, DNA storage) |
| Jennifer Doudna | NIH RePORTER + S2 | 8 grants | 3 papers (CRISPR mechanisms) |
| Harris Wang | NIH RePORTER | 6 grants | — (S2 rate-limited) |
| Le Cong | NIH RePORTER + S2 | 2 grants | 3 papers (CRISPR systems) |
| Jonathan Weissman | NIH RePORTER + S2 | 4 grants | — (S2 partial) |
| Yoshua Bengio | S2 only | — | 3 papers (deep learning foundations) |

**Data sources:**

| Source | API | Method |
|---|---|---|
| Semantic Scholar | `api.semanticscholar.org/graph/v1/author/search` | Top-3 papers per PI by citation count, filtered by bio+AI keyword intersection |
| NIH RePORTER | `api.reporter.nih.gov/v2/projects/search` (POST) | Active grants (FY 2023–2026) for 7 DARPA PIs, deduplicated by project number |

**NIH grant deduplication:** Same grant appears across multiple fiscal years. Kept most recent FY metadata, aggregated total funding across all appearances. Institution names mapped via explicit `INST_MAP` (NIH canonical names → existing node IDs).

**Bio+AI keyword filter (Semantic Scholar):** Papers required hits in BOTH keyword sets — `BIO_KW` (biosecurity, CRISPR, gene drive, pathogen, etc.) AND `AI_KW` (machine learning, deep learning, neural network, etc.) — applied to title + abstract.

**Known limitations:**
- Semantic Scholar API rate-limited 4 of 10 targets (Harris Wang, Eugene Shakhnovich, Peter Henderson, Eric Xing). Retried with delays, got partial results.
- George Church returned 0 NIH grants in 2023–2026 window (grants may be under different mechanisms or co-PI names).

**Scripts:**
```
scripts/s8_extract_key_personnel.py   → data/staged/s8_nodes.json (44), s8_edges.json (97)
data/raw/s8_key_personnel/semantic_scholar_results.json   (10 targets)
data/raw/s8_key_personnel/nih_reporter_results.json       (7 PIs, 31 grants)
```

---

## Sprint 9: NSF + International Funding Expansion ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Add NSF and UKRI (UK Research and Innovation) as new funder nodes, mapping federal and international grant funding for key personnel already in the graph.

**Results:**
- 16 new nodes, 37 new edges → 741 nodes, 1,156 edges total
- 2 new funder nodes: NSF and UKRI (funders 5 and 6)
- 14 NSF grant program nodes ($14.3M across 16 awards)
- 2 UKRI grant program nodes (£700K / ~$890K across 2 awards)
- 9 new `performs_on` edges (PI → NSF grant) for 6 matched PIs
- Princeton, CMU, Stanford, Harvard, Columbia, Oxford, Imperial now have NSF/UKRI funding edges
- Total tracked funding: **$720M** (DARPA $589M + Coefficient $69M + NIH $35M + NSF $14M + UKRI $0.9M)

**Key NSF grants:**
- Harris Wang (Columbia) — "Towards Life with a Reduced Protein Alphabet" ($4.2M)
- George Church (Harvard) — "Expanding functions of a 57-codon recoded E. coli genome" ($2.0M)
- Jennifer Doudna (UC Berkeley) — "Mechanism of Acquired Immunity in Bacteria" ($1.5M)
- Eric Xing (CMU) — 4 grants ($2.2M total, ML + bio/health)
- Mengdi Wang (Princeton) — 3 grants ($1.0M total, statistical optimization + single-cell)
- Le Cong (Stanford) — 1 grant ($360K, single-cell barcode statistics)

**Key UKRI grants:**
- Imperial College London — EU Horizon Guarantee antivirus pandemic preparedness platform (£475K)
- University of Oxford — computational synthetic biology for bioproduction (£225K)

**Data sources:** NSF Award Search API (`api.nsf.gov/services/v1/awards.json`), UKRI Gateway to Research API (`gtr.ukri.org/gtr/api/projects`). Amounts embedded in `participantValues.participant[].grantOffer` field. International funding (Wellcome Trust, Gates, ERC) not reliably extractable from public APIs — noted as future work.

**Fix applied:** Dangling UCSF edge fixed (mapped `inst_University_of_California__San_Francisco` → `org_university_of_california_san_francisco`).

**Scripts:**
```
scripts/s9_extract_nsf_international.py   → data/staged/s9_nodes.json (16), s9_edges.json (37)
data/raw/s9_nsf_international/nsf_awards_raw.json          (183 unique awards from keyword search)
data/raw/s9_nsf_international/nsf_pi_inst_awards.json      (82 PI/inst-targeted awards)
data/raw/s9_nsf_international/nsf_selected.json            (16 matched awards)
data/raw/s9_nsf_international/ukri_projects_raw.json       (348 unique UKRI projects)
data/raw/s9_nsf_international/ukri_bio_ai_relevant.json    (75 bio+AI filtered)
data/raw/s9_nsf_international/ukri_selected.json           (2 institution-matched)
```

---

## Sprint 10: Author-Publication Backfill ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Connect 31 authors who entered the graph through DARPA/policy/organizer routes (not via workshop papers) to their key publications. Reduces degree-1 authors and enriches the research footprint of key personnel.

**Results:**
- 11 new publication nodes, 11 new `published_study` edges → 752 nodes, 1,167 edges
- 3 new Esvelt papers: CRISPR gene drive propagation, LLM biosecurity weights, germline sterilization
- 3 new Church papers: swapped genetic code viral defense, multiplexed in situ protein imaging, gastric cancer microenvironment
- 1 new Le Cong paper: APOE loss-of-function variants and longevity
- 3 new Shakhnovich papers: protein folding transition, enzymatic metabolons, co-translational folding
- 1 new Eric Xing paper: heterogeneous multitask learning

**Method:** Queried Semantic Scholar API (`api.semanticscholar.org/graph/v1/author/{id}/papers`) for key personnel. Matched S2 papers against existing publication nodes by normalized title to avoid duplicates. Applied bio+AI keyword filter. Took top-3 by citation count per author.

**Known gaps:**
- Harris Wang: S2 author ID mismatch, no bio papers returned
- Jian Ma: S2 returned wrong researcher (same name, different field)
- Workshop organizers (Bedi, Velasquez, etc.): entered graph via `organized` edges; no presentation or publication linkage needed

**Fix applied:** `author_eugene_shakhnovich` → `author_Eugene_Shakhnovich1` ID mismatch (S8 created node with OpenReview capitalized ID, S10 used lowercase).

**Scripts:**
```
scripts/s10_author_pub_backfill.py   (inline in session)
data/raw/s8_key_personnel/semantic_scholar_retry.json   (retry results for 7 authors)
data/staged/s10_nodes.json   (11 nodes)
data/staged/s10_edges.json   (11 edges)
```

---

## Sprint 11: Graph Densification & Structural Audit ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Audit structural weaknesses, remove duplicate nodes, add co-authorship edges for strong collaboration pairs, and mark bridge nodes correctly.

**Results:**
- Net: -1 node (UC Berkeley dedup), +11 edges (co-authorship) → 751 nodes, 1,178 edges
- Removed duplicate `inst_University_of_California_Berkeley` (deg=4, from Sprint 9 NSF mapping) — merged into canonical `inst_University_of_California__Berkeley` (deg=19)
- 11 new `co_authored_with` edges for author pairs sharing ≥3 workshop presentations
- 26 institution nodes updated with `bridge=True` (appear in both funding and workshop layers)

**Co-authorship pairs discovered (≥3 shared papers):**
- Dianzhuo Wang ↔ Eugene Shakhnovich (4 papers)
- Le Cong ↔ Mengdi Wang ↔ Ruofan Jin ↔ ZAIXI ZHANG (Princeton biosafe core team, 3 papers each)
- Benjamin Liu ↔ Kevin Zhu (3 papers)
- Samira Nedungadi ↔ Seth Donoughe (3 papers)
- Dianzhuo Wang ↔ Marian Huot + Eugene Shakhnovich ↔ Marian Huot (3 papers)

**Structural audit findings:**
- Degree-1 nodes: 318 (44%), mostly institutions/orgs with single funding edge — acceptable
- 136/171 institutions have only affiliation edges (no funding) — expected for workshop-only institutions
- 27 institutions bridge both funding and workshop layers (the most analytically valuable nodes)
- All 32 publication nodes have ≥1 author edge (no orphan publications)

**Scripts:** `quality_check.py` (audit), inline Python for merge and edge creation.

---

## Sprint 12: Geographic / Timeline Layer ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass.

**Goal:** Enrich institution nodes with lat/lon coordinates and country codes; add `year_start`/`year_end` to funding edges; add `year` to program and presentation nodes. Lays the data foundation for a future map view and time slider.

**Results:**
- 70/171 institutions enriched with lat/lon + location + country (curated lookup table)
- 272 `funds` edges enriched with `year_start` (extracted from `date_range` strings)
- 4 org nodes enriched with country codes
- 1 presentation node enriched with year
- **No new nodes/edges** — pure metadata enrichment sprint

**Geographic coverage:**
- US: 45 institutions (Northeast, South, Midwest, West coast, national labs)
- UK: 8 institutions (Oxford, Cambridge, Imperial, UCL, Edinburgh, Manchester, Sanger, Crick)
- Europe: 8 institutions (ETH, EPFL, Heidelberg, Munich, Karolinska, Max Planck, Pasteur)
- Asia: 12 institutions (China, Singapore, Japan, Korea, India)
- Canada: 5 institutions (Toronto, McGill, UdeM, Mila, UBC)
- Middle East: 2 institutions (Hebrew U, Weizmann + MBZUAI)
- Other: 1 (Shahjalal, Bangladesh)

**Future work (not yet implemented):**
- Map view panel in HTML (requires Leaflet.js or similar)
- Time slider filtering edges by `year_start`
- Remaining 101 institutions need geocoding (mostly degree-1 workshop-only nodes)

**Scripts:** Inline Python geo enrichment; coordinates from curated lookup table (no API calls needed).

---

## Visualization Milestones

| Sprint | Nodes | Edges | Funding | Renderer |
|--------|-------|-------|---------|----------|
| 1 | 350 | 479 | — | SVG ✅ |
| 2–3 | 502 | 767 | $543M | SVG ✅ |
| 4–5 | 584 | 852 | $693M | SVG ✅ |
| 6 | 607 | 936 | $693M | SVG ✅ |
| 7 | 681 | 1,022 | $693M | SVG + Canvas 2D ✅ |
| 8 | 725 | 1,119 | $693M | SVG + Canvas 2D ✅ |
| 9–12 | 751 | 1,178 | $720M | SVG + Canvas 2D ✅ |
| Audit | 738 | 1,216 | $703M | SVG + Canvas 2D ✅ |
| Sprint 13 | 741 | 1,225 | $703M | SVG + Canvas 2D ✅ |
| Sprint 14 | 747 | 1,231 | $703M | SVG + Canvas 2D ✅ |
| Sprint 15 | 752 | 1,237 | $703M | SVG + Canvas 2D ✅ |
| Sprint 16 | 757 | 1,244 | $1.22B | SVG + Canvas 2D ✅ |
| Sprint 13 DD | 759 | 1,253 | $1.22B | SVG + Canvas 2D ✅ |
| Sprint 17 | 766 | 1,262 | $1.22B | SVG + Canvas 2D ✅ |
| Sprint 17 DD | 766 | 1,264 | $1.22B | SVG + Canvas 2D ✅ |
| **Comprehensive Audit** | **738** | **1,113** | **$1.22B** | SVG + Canvas 2D ✅ |

**Dual renderer approach (Sprint 7+):** Canvas 2D (`index.html`) is the default renderer. SVG is preserved as `index_svg.html` for reference. Both share the same graph data, layout computation, sidebar, filters, and interaction model. Canvas 2D provides better performance at 700+ nodes via batched edge rendering by type, `ctx.arc()`/`ctx.roundRect()` for nodes, and includes an FPS counter.

**Scripts:** `generate_webgl.py` → `index.html` (Canvas 2D, **default**), `generate_html_v3.py` → `index_svg.html` (SVG, reference)

---

---

## Insight Validation — Cross-Check Against External Literature

*Completed: 2026-03-12 | 10 external sources reviewed | See `data/raw/references/external_validation_sources.md`*

### Methodology

Each of the 25 insights (5 audiences × 5 points, generated from multi-angle graph analysis) was cross-checked against 10 external policy reviews and meta-analyses. Insights were classified into three tiers:

- **ROBUST** — directionally confirmed by external sources; holds even with expanded data coverage
- **DATA-LIMITED** — plausible but depends on atlas completeness; should be qualified in communications
- **SAMPLING ARTIFACT** — likely to change significantly when atlas is extended (more workshops, venues, funders)

### Insight Verdict Table

| # | Audience | Insight | Verdict | External Support |
|---|----------|---------|---------|-----------------|
| P1 | Policymakers | Coefficient/OP dominates biosecurity AI funding (~82% of total) | **ROBUST** | OP 2024 report confirms OP = ~60% of all AI safety philanthropy |
| P2 | Policymakers | US institutions dominate researcher network | **ROBUST** | PMC dual-use: 58% US authors, 83% from US/UK/CN/DE |
| P3 | Policymakers | No standardized governance frameworks across funders and researchers | **ROBUST** | JHU CHS, CSET, PMC responsible AI, PMC dual-use all confirm |
| P4 | Policymakers | 2023 funding peak → 2024 drop signals political vulnerability | **DATA-LIMITED** | CSIS confirms NIST FY2026 $325M cut; but only 6 funders tracked |
| P5 | Policymakers | Most researchers siloed — only 5 appear in both workshop and funded programs | **SAMPLING ARTIFACT** | Only 4 NeurIPS workshops; ICLR/ICML/domain venues not included |
| R1 | Researchers | LLM safety dominates workshop submissions (36/53 papers) | **SAMPLING ARTIFACT** | Workshops chosen were ML-native; wet lab / protein design venues excluded |
| R2 | Researchers | Cross-venue collaboration sparse (17 cross-venue authors) | **SAMPLING ARTIFACT** | Same limitation; ICLR, ICML, ASM, ESCMID not covered |
| R3 | Researchers | Five institutions produce ~60% of funded research output | **DATA-LIMITED** | Consistent with general power-law in science; but grantee list from only 6 funders |
| R4 | Researchers | Bridge institutions (Harvard, MIT, Stanford, JHU) at intersection of research and funding | **ROBUST** | Confirmed by NSF, NIH, DARPA data; consistent with CSET/JHU CHS reports |
| R5 | Researchers | Protein design biosecurity dramatically underrepresented relative to risk | **ROBUST** | Science (ado1671), Nature Biotech (2025), EMBO Reports, Singularity Hub all confirm |
| F1 | Funders | Single-funder concentration risk ($540M from OP) | **ROBUST** | OP 2024 report confirms; CSIS confirms government funding volatility compounds risk |
| F2 | Funders | Government vs. private funding ratio ($160M DARPA/NIH/NSF vs. $543M OP) | **ROBUST** | Within atlas scope; consistent with broader AI safety funding landscape |
| F3 | Funders | UK/EU funding minimal vs. US despite similar research output | **DATA-LIMITED** | Atlas covers UKRI only; Wellcome Trust, EU Horizon, BBSRC not tracked |
| F4 | Funders | Startup/VC biosecurity funding not visible | **DATA-LIMITED** | By atlas design (grants only); Convergent Biosciences, Seed Health, etc. missing |
| F5 | Funders | Funding peak in 2023 may signal maturation or political vulnerability | **DATA-LIMITED** | Plausible; CSIS confirms 2025 regulatory cuts, but 6-funder sample limits confidence |
| A1 | AI Safety | Heavy US/UK focus creates global blind spots | **ROBUST** | NTI: 0% of Global South AI strategies address biosecurity; PMC: 83% US/UK/CN/DE |
| A2 | AI Safety | Benchmark fragmentation makes evaluation comparisons difficult | **ROBUST** | WMDP saturating; Epoch AI confirms non-interoperable benchmark landscape |
| A3 | AI Safety | Only 5 researchers bridge research-funding divide | **SAMPLING ARTIFACT** | 4 NeurIPS workshops only; ICLR, ICML, domain venues not included |
| A4 | AI Safety | Evaluator community is small relative to problem scope | **ROBUST** | CSIS: <3% of 370+ models have safeguards; PMC dual-use confirms evaluation gaps |
| A5 | AI Safety | SecureBio/CHS serve as critical bottleneck nodes | **ROBUST** | SecureBio appears in OP grantee lists; JHU CHS cited in NSCEB + AIxBio forums |
| B1 | Practitioners | AI biosecurity evaluations lack standardized methodology | **ROBUST** | JHU CHS, CSET, PMC dual-use, RAND all confirm; UK/US govts have not released standards |
| B2 | Practitioners | Global South absent from atlas despite high pandemic risk | **ROBUST** | NTI analysis: no Global South country AI strategy addresses biosecurity |
| B3 | Practitioners | Atlas captures only 6 funders; landscape is larger | **ROBUST** | By definition; RAND covers 24 countries with 57 tools; Wellcome, Gates, BARDA missing |
| B4 | Practitioners | Eval documents are US/UK focused; international governance thin | **DATA-LIMITED** | Likely true but atlas policy layer is US/UK-sourced; no African CDC, SEARO etc. |
| B5 | Practitioners | Protein design biosecurity = biggest white space in research and funding | **ROBUST** | Science, Nature Biotech, EMBO Reports all call this out; <1% of atlas nodes touch it |

### Summary

- **15 ROBUST** insights — defensible even with expanded data
- **6 DATA-LIMITED** insights — qualify with coverage caveats when communicating
- **4 SAMPLING ARTIFACT** insights — remove from audience-specific materials; address via Sprints 13–15

### Points to Remove or Heavily Qualify

The following insights are **sampling artifacts** and should be dropped from audience-facing materials until the atlas covers more venues:

- *"LLM safety dominates workshop submissions"* — true for 4 NeurIPS ML workshops; not representative of the broader field
- *"Cross-venue collaboration is sparse"* — same limitation; actual collaboration may be much denser across venues not yet tracked
- *"Only 5 researchers bridge research-funding divide"* — a floor, not a ceiling; ICLR/ICML NeurIPS main track alone would multiply this
- *"Most researchers siloed"* — same; the workshop community captured here is a small slice

---

## Sprint 13: Benchmark & Evaluation Landscape ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass. 100% connectivity.

**Results:**
- 3 new nodes: Apollo Research (org), METR (org), Beth Barnes (author)
- 9 new edges: Apollo Research + METR `biosecurity_eval` edges to Anthropic/OpenAI/Google DeepMind; Beth Barnes `current_affiliation` → METR; Nathaniel Li, Dan Hendrycks, Anjali Gopal `published_study` → WMDP paper
- Total: 741 nodes, 1,225 edges

**Raw data:** `data/raw/s13_benchmarks/s13_evidence.json`

---

## Sprint 13: Benchmark & Evaluation Landscape — Original Plan 🔲

**Goal:** Map the AI biosecurity evaluation and benchmark ecosystem. Add major benchmarks, evaluation organizations, and their relationships to address gaps in the evaluator community picture (currently only 12 evaluator nodes).

**Motivation:** ROBUST finding A4 (evaluator community small) and A2 (benchmark fragmentation) need structural support in the graph to be visualizable. CSIS confirms <3% of 370+ models have safeguards — the atlas should reflect the evaluator ecosystem driving this.

**Data Sources:**

| Source | Type | Target |
|--------|------|--------|
| WMDP paper (arxiv 2403.03218) | Research paper | Add as publication; link to existing SecureBio/author nodes |
| VCT (Virology Capabilities Test) | Research paper | New publication node + evaluator author nodes |
| LAB-Bench (FutureHouse) | Already in graph | Add `benchmark` subtype; add `evaluates` edges to AI labs |
| BioWeapons Eval (RAND, 2024) | Report | Link to existing RAND org node |
| Epoch AI biorisk analysis | Already in graph | Verify subtype + add missing `biosecurity_eval` edges |
| Apollo Research | Org | New org node + evaluates edges to Anthropic/OpenAI |
| METR | Org | New org node |
| ARC Evals | Org | New org node (now METR); deduplicate if needed |

**New Edge Types Needed:**
- `evaluates`: evaluator org/author → AI org (for org-level, not publication-level relationships)
- Consider adding `benchmark_subtype` field to `publication` nodes

**Anti-hallucination:** All connections must trace to a published paper, blog post, or press release naming the evaluator and the model evaluated.

**Expected output:** +15–20 nodes, +20–30 edges

**Scripts:**
```
scripts/s13_extract_benchmarks.py    → data/staged/s13_nodes.json, s13_edges.json
data/raw/s13_benchmarks/             ← Raw paper abstracts + org pages
```

---

## Sprint 14: Funding Completeness — Wellcome, BARDA, CEPI ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass. 100% connectivity.

**Results:**
- 6 new nodes: Wellcome Trust (funder), BARDA (funder), CEPI (org), Wellcome Oxford programme (program), CEPI Oxford Vaccines (program), BARDA Medical Countermeasures (program)
- 6 new edges: funder → program → institution links for Wellcome→Oxford and CEPI→Oxford; BARDA → JHU
- Total: 747 nodes, 1,231 edges
- Funding: Wellcome added ~$260M (£200M Oxford aggregate); BARDA and CEPI amounts not publicly stated for specific grants

**Limitation:** Wellcome and BARDA do not expose individual grant records via public API. Funder nodes added with known aggregate funding; program-institution links only where total amounts are publicly stated in verified sources.

**Raw data:** `data/raw/s14_funding/s14_evidence.json`

---

## Sprint 14: Funding Completeness — Original Plan 🔲

**Goal:** Add major funders missing from the atlas — Wellcome Trust, Gates Foundation (bio-AI relevant grants), and US BARDA — to reduce the data-limited nature of F3, F4, F5 insights and give a more complete picture of the funding landscape.

**Motivation:** DATA-LIMITED findings F3 (UK/EU funding underrepresented) and F2 (government vs. private ratio) require Wellcome and BARDA data to be defensible. OP = $543M looks like 82% of total only because major funders are absent.

**Data Sources:**

| Funder | API / Source | Target Filter |
|--------|-------------|---------------|
| Wellcome Trust | `api.wellcome.org/grants` or Figshare open grants | Bio+AI keywords; UK institutions already in graph |
| Gates Foundation | Figshare open data (grantee name, amount, year) | Pandemic preparedness + AI/computational biology |
| BARDA (US) | USASpending.gov API (awarding_agency_code `75-2700`) | Biosecurity + pandemic countermeasures; map to existing institutions |
| Founders Pledge Health Security | Public commitment data | Link to existing funder nodes or create new |

**Scope filter:** Only grants to institutions already in the atlas, OR grants to major grantees whose work directly overlaps existing nodes.

**Expected output:** +2–3 funder nodes, +30–60 new program nodes, $500M–$1B additional tracked funding

**Scripts:**
```
scripts/s14_fetch_wellcome.py        → data/raw/s14_funding/wellcome_grants.json
scripts/s14_fetch_gates.py           → data/raw/s14_funding/gates_grants.json
scripts/s14_fetch_barda.py           → data/raw/s14_funding/barda_grants.json
scripts/s14_extract_funding.py       → data/staged/s14_nodes.json, s14_edges.json
```

---

## Sprint 15: Global South & International Coverage ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass. 100% connectivity.

**Results:**
- 5 new nodes: Africa CDC (org, Ethiopia), SynBio Africa (org, Nigeria), Brown Pandemic Center (org, US), NTI Global South AI-Biosecurity 2024 (publication), Munich Biosecurity Declaration 2025 (publication)
- 6 new edges: NTI, CEPI, Brown Pandemic Center `policy_forum` → Munich Declaration; Africa CDC, SynBio Africa `policy_forum` → NTI Global South pub
- Total: 752 nodes, 1,237 edges

**Key insight confirmed:** Africa CDC has a formal Biosafety and Biosecurity Initiative + AI for Health strategy; SynBio Africa and iGEM co-sponsored 2024 NTI competition from 19 countries; Munich 2025 Declaration represents first formal Global South biosecurity leadership commitment.

**Raw data:** `data/raw/s15_global_south/s15_evidence.json`

---

## Sprint 15: Global South — Original Plan 🔲

**Goal:** Address the ROBUST finding B2 / A1 (Global South absent) by adding relevant international organizations, funders, and researchers from underrepresented regions.

**Motivation:** NTI confirms 0% of Global South AI strategies address biosecurity. Adding at least placeholder nodes for key international biosecurity bodies makes the gap visible in the graph rather than invisible.

**Data Sources:**

| Source | Target |
|--------|--------|
| Africa CDC biosecurity programs | Org node + publications |
| WHO SEARO / AFRO AI health initiatives | Org nodes |
| NTI AIxBio Global South report | Publication node + link to existing NTI org |
| CEPI (Coalition for Epidemic Preparedness) | Org node + funding edges to existing institutions (Oxford, LSHTM, etc.) |
| IAVI | Org node + link to existing Coefficient grants |
| Rift Valley Institute / Africa-focused biosecurity NGOs | Org nodes |
| CSET/NTI authors from Global South | Author nodes if named in sourced documents |

**Key constraint:** No invented edges. If a Global South org has no traceable connection to existing atlas nodes, add it as an isolated node only if it has a `self-connection` (node exists with correct metadata). Orphan nodes will need at least one publication link.

**Expected output:** +10–15 org nodes, +5–10 edges; primarily structural/visibility improvement

**Scripts:**
```
scripts/s15_extract_global_south.py   → data/staged/s15_nodes.json, s15_edges.json
data/raw/s15_global_south/            ← NTI report snapshot, Africa CDC page, CEPI data
```

---

## Sprint 16: Protein Design Safety Research Mapping ✅ COMPLETE

**Status:** Shipped. 14/14 quality checks pass. 100% connectivity.

**Results:**
- 5 new nodes: David Baker (author, 2024 Nobel Chemistry), EvolutionaryScale (org), UW Institute for Protein Design (org), "Protein design meets biosecurity" Science 2024 (publication), EMBO Reports protein design security 2024 (publication)
- 7 new edges: David Baker `current_affiliation` → UW; UW IPD `part_of` → UW; David Baker + George Church `published_study` → Science paper; Gryphon Scientific + UW IPD + EvolutionaryScale `policy_forum` → publications
- Total: 757 nodes, 1,244 edges

**Key insight confirmed:** Protein design safety is now a visible cluster in the graph. Baker & Church Science 2024 editorial, EMBO Reports security challenge paper, and EvolutionaryScale are all now connected to the existing DARPA (George Church) and policy evaluation layer.

**Raw data:** `data/raw/s16_protein_design/s16_evidence.json`

---

## Sprint 16: Protein Design — Original Plan 🔲

**Goal:** Add the protein design safety research cluster — the biggest white space identified in analysis (insights R5, B5, confirmed ROBUST by multiple external sources). This is the area of highest biosecurity risk with lowest current atlas coverage.

**Motivation:** Science, Nature Biotechnology, EMBO Reports, and Singularity Hub all confirm AI-assisted protein design is the frontier biosecurity risk. Current atlas has <5 nodes touching this topic. Baker & Church proposals (2024), nucleic acid screening work, and EvolutionaryScale ESM models safety evaluations are all missing.

**Data Sources:**

| Source | Target |
|--------|--------|
| Science ado1671 "Protein design meets biosecurity" (2024) | Publication node + link to author nodes |
| Nature Biotech "Built-in biosecurity safeguards for generative AI" (2025) | Publication node |
| EMBO Reports "Security challenges by AI-assisted protein design" (2024) | Publication node |
| EvolutionaryScale (ESM3 / ESM Cambrian) | Org node + author nodes (Baker Lab, Rives) |
| David Baker (UW Institute for Protein Design) | Author node (if not already in graph) + institution |
| Gryphon Scientific nucleic acid screening work | Link to existing org_gryphon_scientific |
| Synthesis.ai / Profluent | Org nodes (commercial protein design; dual-use concern) |

**Expected output:** +10–15 nodes, +15–20 edges; creates a visible "protein design safety" cluster in graph

**Scripts:**
```
scripts/s16_extract_protein_design.py   → data/staged/s16_nodes.json, s16_edges.json
data/raw/s16_protein_design/            ← Science/EMBO/NatBiotech abstracts, EvolutionaryScale page
```

---

## Sprint 17: Governance & Policy Literature Mapping ✅ COMPLETE

*Completed: 2026-03-13 | 7 nodes, 9 edges added | See `data/raw/s17_governance/s17_evidence.json`*

**Goal:** Add the governance and policy organization layer — JHU CHS, Georgetown CSET, RAND Global Risk Index publication, NSABB — so the atlas visually connects the funding and research communities to the policy evaluation community.

**Motivation:** ROBUST insights B1, B3, B4 and the JHU/CSET/NTI external sources are not yet in the graph. Adding these as properly sourced nodes makes the governance gap visible and connects evaluators to policymakers.

**Added nodes (+7):**

| Node | Type | Key Connection |
|------|------|---------------|
| JHU Center for Health Security | org (policy_think_tank) | current_affiliation → JHU; Jassi Pannu author link |
| Georgetown CSET | org (policy_think_tank) | current_affiliation → Georgetown Global Health org |
| NSABB | org (advisory_body) | current_affiliation → NIH |
| RAND Global Risk Index (2024) | publication | policy_forum ← RAND Corporation, JHU CHS |
| CSET Biosecurity Policy Toolkit (2024) | publication | policy_forum ← Georgetown CSET |
| JHU CHS Biosecurity Agenda (2025) | publication | policy_forum ← JHU CHS |
| NSABB DURC Recommendations (2023) | publication | policy_forum ← NSABB |

**Added edges (+9):** JHU CHS → JHU inst, JHU CHS → RAND GRI pub, CSET → CSET toolkit pub, CSET → Georgetown Health org, NSABB → NIH, NSABB → DURC pub, JHU CHS → CHS Agenda pub, RAND Corp → RAND GRI pub, Jassi Pannu → JHU CHS

**Post-sprint graph:** 766 nodes, 1,262 edges | $1.22B tracked | 14/14 quality checks | 100% connectivity

### Sprint 17 Due Diligence ✅ COMPLETE

*Completed: 2026-03-13 | 3 fixes applied | 2 new edges added*

**Audit findings and fixes:**

| Fix | Severity | Description |
|-----|----------|-------------|
| Fix 1 | 🔴 CRITICAL | 9 OP funds edges ($55.3M) were targeting `inst_Johns_Hopkins_University` but grant titles say "Johns Hopkins Center for Health Security". Retargeted all 9 to `org_jhu_center_for_health_security`. JHU CHS now correctly shows deg=13 with $55.3M funding; JHU institution retains 5 edges ($6.5M for APL contracts + BARDA) |
| Fix 2 | 🟡 MEDIUM | RAND GRI publication had no individual author links. Added `published_study` edges for Christopher A. Mouton and Caleb Lucas (both already in graph as RAND authors of the related bio-attack-redteam pub) |
| Fix 3 | 🟢 LOW | CSET → Georgetown Global Health edge had type `current_affiliation` (reserved for author→institution). Changed to `part_of` to reflect that both are research centers housed within Georgetown University |

**Post-DD graph:** 766 nodes, 1,264 edges | $1.22B | 14/14 quality checks | 100% connectivity

**Script:** `scripts/s17_dd_fixes.py`

**Data sources:**
- JHU CHS: centerforhealthsecurity.org (Jassi Pannu profile, publications page)
- Georgetown CSET: cset.georgetown.edu (Biosecurity Policy Toolkit, Dec 2024)
- RAND: rand.org (Global Risk Index for AI-Enabled Biological Tools, 2024)
- NSABB: osp.od.nih.gov/biotechnology (DURC recommendations, 2023)

**Scripts:**
```
scripts/s17_extract_governance.py   → data/graph_data.json (direct merge)
data/raw/s17_governance/            ← s17_evidence.json (7 node records)
```

---

## Comprehensive Audit ✅ COMPLETE

*Completed: 2026-03-13 | 27 nodes removed, 151 edges removed/deduplicated | See `AUDIT_REPORT.md`*

**Motivation:** After 17 sprints the graph grew from 350 to 766 nodes, accumulating structural debt: duplicate nodes from inconsistent naming across sprints, NIH grant fiscal-year inflation, off-topic publications that slipped past the dual-axis relevance test, and schema inconsistencies.

**Findings (8 categories):**

1. **Duplicate nodes (Critical):** 4 exact-duplicate org pairs (DARPA sprint prefix collision), 1 near-duplicate institution ("the" vs no "the" in UCAS name), 18 NIH grant FY instances that should be 8 base projects
2. **SecureBio type inconsistency:** Typed as `institution` but is an evaluation org — changed to `org` (subtype `evaluator`)
3. **Edge type violations:** 9 `authored` edges from org/institution sources changed to `policy_forum`; 8 `current_affiliation` edges targeting departments documented
4. **Scope creep:** 4 publications fail the dual-axis (bio AND AI) relevance test — removed
5. **40% degree-1 nodes:** 310/766 nodes had exactly one edge; partly unavoidable but noted
6. **IARPA $0 funding:** 11 Fun GCAT grants show $0 (classified amounts) — documented
7. **Funding double-count risk:** $1.22B includes broad Wellcome/Coefficient figures — documented
8. **Missing s10 script:** Sprint 10 script was inline-only — documented

**Fixes applied:**

| Fix | Nodes Removed | Edges Affected |
|-----|--------------|----------------|
| Merge 5 duplicate org pairs (incl. UC Berkeley) | -5 | ~5 retargeted |
| Merge UCAS near-duplicate | -1 | ~1 retargeted |
| Deduplicate 18 NIH grant FY instances | -18 | ~46 removed + summed amounts |
| Remove 4 off-topic publications | -4 | -4 removed |
| SecureBio type → org (evaluator) | 0 | 0 |
| 9 authored edges → policy_forum | 0 | 9 type-changed |
| Edge deduplication (post-merge) | 0 | 95 deduplicated |

**Post-audit graph:** 738 nodes, 1,113 edges | $1.22B tracked | 14/14 quality checks | 100% connectivity

**Scripts:** `scripts/audit_fixes.py` (all fixes), plus inline RM1HG009490 final dedup

---

## UI Improvements Backlog

- [ ] **Grant titles in detail panel**: `grant_title` is stored on every `funds` edge but not shown in the UI. When a node is selected and its funding connections are listed, show the grant title alongside the amount. Fix: modify `showInfo()` in `generate_html_v3.py` — replace `nn.label + amtStr` with `(e.grant_title || nn.label) + amtStr` for `funds` edges.
- [ ] **Edge click**: clicking a funds edge should open a mini-panel with grant title, date, focus area, amount, and confidence
- [ ] **URL enrichment**: add verified homepage URLs to major grantee org nodes

---

## Quality Checks (run after every sprint)

Automated by `scripts/quality_check.py`:

1. No dangling edge references
2. No duplicate node IDs
3. No duplicate edge IDs
4. No orphan nodes
5. No NaN/Infinity/undefined in JSON
6. All nodes have required fields
7. All edges have required fields
8. All edge types are valid enum values
9. All node types are valid enum values
10. Bridge nodes detected and marked
11. All `funds` edges have amount
12. All `contracts` edges have confidence score
13. Graph connectivity > 80%
14. Raw data files exist in `data/raw/`

---

## Known Hallucination Patterns

Previous AI-assisted builds produced ~9% false edge rate, ~11% wrong amounts:

1. **Fabricated funding** — e.g., "OP→EcoHealth Alliance $5M" (no such grant). Always verify against CSV/API.
2. **Invented programs** — e.g., "DARPA BioAutoMATED" (MIT Lincoln Lab tool, not a DARPA program).
3. **Conflated amounts** — attributing total funding from all sources to a single funder.
4. **Misattributed sponsors** — e.g., "DARPA Fun GCAT" (it's **IARPA**, not DARPA).
5. **Assumed partnerships** — e.g., "Meta FAIR ↔ SecureBio collaboration" (SecureBio evaluated Meta's models, no formal partnership).

---

## File Structure

```
biosecurity-atlas/
├── index.html                          ← Canvas 2D visualization (self-contained, default)
├── index_svg.html                      ← SVG visualization (self-contained, reference)
├── index_d3.html                       ← D3 force-directed visualization
├── README.md
├── ROADMAP.md                          ← this file
├── AUDIT_REPORT.md                     ← comprehensive audit findings (8 categories)
├── METHODOLOGY.md
├── assets/
├── figures/                            ← Generated analysis figures (PNG)
├── notebooks/                          ← All Jupyter notebooks (canonical location)
│   ├── analysis_biosecurity_atlas.ipynb    ← Multi-angle analysis (14+ figures)
│   ├── op_grants_audit.ipynb               ← Open Philanthropy grants audit
│   ├── s4_darpa_iarpa_exploration.ipynb    ← Sprint 4 DARPA/IARPA dry run
│   └── s5_policy_bigtech_exploration.ipynb ← Sprint 5 Policy & Big Tech dry run
├── data/
│   ├── graph_data.json                 ← assembled graph (738 nodes, 1,113 edges)
│   ├── nodes.csv
│   ├── edges.csv
│   ├── raw/
│   │   ├── references/                 ← External validation sources (Sprint 12+)
│   │   │   └── external_validation_sources.md   (10 policy sources, insight verdicts)
│   │   ├── s1_neurips_workshop/        ← Sprint 1: OpenReview papers + PDFs
│   │   ├── s2s3_coefficient_funding/   ← Sprint 2/3: Coefficient grants CSV
│   │   ├── s4_darpa_iarpa/             ← Sprint 4: USASpending JSON, DARPA/IARPA pages, news releases
│   │   ├── s5_policy_bigtech/          ← Sprint 5: SecureBio, RAND, NTI publications & evals
│   │   ├── s6_organizers_speakers/     ← Sprint 6: Workshop website data
│   │   ├── s7_cross_venue/             ← Sprint 7: OpenReview data from 3 sibling workshops
│   │   │   ├── mlgenx_papers.json          (41 papers)
│   │   │   ├── genai4health_papers.json     (164 papers)
│   │   │   ├── ai4science_papers.json       (200 papers)
│   │   │   └── overlap_analysis.json        (16 overlap papers → 15 unique)
│   │   ├── s8_key_personnel/           ← Sprint 8: Semantic Scholar + NIH RePORTER
│   │   │   ├── semantic_scholar_results.json   (10 targets)
│   │   │   ├── semantic_scholar_retry.json     (7 additional targets)
│   │   │   └── nih_reporter_results.json       (7 PIs, 31 grants)
│   │   ├── s9_nsf_international/       ← Sprint 9: NSF + UKRI grants
│   │   │   ├── nsf_awards_raw.json             (183 keyword-search awards)
│   │   │   ├── nsf_pi_inst_awards.json         (82 PI/inst-targeted awards)
│   │   │   ├── nsf_selected.json               (16 matched awards, $14.3M)
│   │   │   ├── ukri_projects_raw.json          (348 unique UKRI projects)
│   │   │   ├── ukri_bio_ai_relevant.json       (75 bio+AI filtered)
│   │   │   └── ukri_selected.json              (2 institution-matched, £700K)
│   │   ├── s13_benchmarks/             ← Sprint 13: Eval benchmark landscape
│   │   │   └── s13_evidence.json               (Apollo, METR, VCT, WMDP evidence)
│   │   ├── s14_funding/                ← Sprint 14: Funding completeness
│   │   │   └── s14_evidence.json               (Wellcome, BARDA, CEPI evidence)
│   │   ├── s15_global_south/           ← Sprint 15: Global South coverage
│   │   │   └── s15_evidence.json               (Africa CDC, SynBio Africa, NTI evidence)
│   │   ├── s16_protein_design/         ← Sprint 16: Protein design safety research
│   │   │   └── s16_evidence.json               (Baker, EvolutionaryScale, EMBO evidence)
│   │   └── s17_governance/             ← Sprint 17: Governance & Policy Literature
│   │       └── s17_evidence.json               (JHU CHS, CSET, NSABB, RAND GRI evidence)
│   └── staged/
│       ├── op_edges.json               ← Sprint 2/3 (272 grants, 288 edges)
│       ├── op_validation_report.json
│       ├── s4_nodes.json               ← Sprint 4 (51 nodes)
│       ├── s4_edges.json               ← Sprint 4 (58 edges)
│       ├── s5_nodes.json               ← Sprint 5 (27 nodes)
│       ├── s5_edges.json               ← Sprint 5 (47 edges)
│       ├── s6_nodes.json               ← Sprint 6 (23 nodes)
│       ├── s6_edges.json               ← Sprint 6 (38 edges)
│       ├── s7_nodes.json               ← Sprint 7 (74 nodes)
│       ├── s7_edges.json               ← Sprint 7 (86 edges)
│       ├── s8_nodes.json               ← Sprint 8 (44 nodes)
│       ├── s8_edges.json               ← Sprint 8 (97 edges)
│       ├── s9_nodes.json               ← Sprint 9 (16 nodes)
│       ├── s9_edges.json               ← Sprint 9 (37 edges)
│       ├── s10_nodes.json              ← Sprint 10 (11 nodes)
│       ├── s10_edges.json              ← Sprint 10 (11 edges)
│       ├── s13_dd_nodes.json           ← Sprint 13 DD (2 nodes: VCT pub, METR task suite pub)
│       └── s13_dd_edges.json           ← Sprint 13 DD (9 edges: author links, RAND policy_forum, Beth Barnes)
└── scripts/
    ├── extract_data.py                 ← Sprint 1: OpenReview extraction
    ├── build_graph.py                  ← Sprint 1: graph assembly
    ├── generate_webgl.py               ← Canvas 2D visualization generator → index.html (default)
    ├── generate_html_v3.py             ← SVG visualization generator → index_svg.html (reference)
    ├── quality_check.py                ← cumulative checks (all sprints, 14 checks)
    ├── s2_fetch_op_grants.sh           ← Sprint 2/3: fetch Coefficient CSV
    ├── s2_extract_op_grants.py         ← Sprint 2/3: extract + classify grants
    ├── s2_validate_op.py               ← Sprint 2/3: validate staged data
    ├── s2_merge_op.py                  ← Sprint 2/3: merge into graph
    ├── s4_extract_darpa_iarpa.py       ← Sprint 4: DARPA/IARPA extraction
    ├── s4b_fix_darpa_programs.py       ← Sprint 4b: DARPA program nodes hotfix
    ├── s5_extract_policy_bigtech.py    ← Sprint 5: Policy & Big Tech extraction
    ├── s6_extract_organizers_speakers.py ← Sprint 6: Organizers & speakers extraction
    ├── s7_extract_cross_venue.py       ← Sprint 7: Cross-venue overlap extraction
    ├── s8_extract_key_personnel.py     ← Sprint 8: NIH grants + Semantic Scholar pubs
    ├── s9_extract_nsf_international.py ← Sprint 9: NSF + UKRI funding extraction
    ├── s13_extract_benchmarks.py       ← Sprint 13: Eval benchmark landscape
    ├── s13_dd_fixes.py                 ← Sprint 13 DD: VCT pub, evidence backfill, RAND/Beth Barnes fixes
    ├── s14_extract_funding.py          ← Sprint 14: Wellcome, BARDA, CEPI funding
    ├── s15_extract_global_south.py     ← Sprint 15: Africa CDC, SynBio Africa, NTI
    ├── s16_extract_protein_design.py   ← Sprint 16: Baker, EvolutionaryScale, protein design safety
    ├── s17_extract_governance.py       ← Sprint 17: JHU CHS, Georgetown CSET, NSABB, RAND GRI
    ├── s17_dd_fixes.py                 ← Sprint 17 DD: JHU CHS $55M funding retarget, RAND GRI authors, CSET edge fix
    └── audit_fixes.py                  ← Comprehensive audit: dedup orgs/NIH FY grants, remove off-topic pubs, fix types
```
