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

## Node Schema

| Type | Key Fields | Count (current) |
|------|-----------|-----------------|
| `funder` | id, label, short, url, description | 6 |
| `program` | id, label, parent→funder, url, subtype (nih_grant/nsf_grant/ukri_grant), year, year_start | 75 |
| `org` | id, label, entity_type, url, country | 171 |
| `institution` | id, label, url, lat, lon, location, country (Sprint 12) | 171 |
| `author` | id, label, url, details | 234 |
| `presentation` | id, label, url, subtype (poster/oral/workshop), year | 54 |
| `publication` | id, label, url, subtype (research_paper/research_report), year, citation_count | 32 |
| `department` | id, label, parent→institution | 8 |

`org.entity_type`: `institution` / `org` / `individual` / `pooled_grant`

## Edge Schema

| Type | Direction | Key Fields | Count (current) |
|------|-----------|-----------|-----------------|
| `funds` | funder/program → org/inst | amount, date_range, grant_title, confidence | 400 |
| `authored` | author → presentation | — | 264 |
| `current_affiliation` | author → institution | — | 215 |
| `past_affiliation` | author → institution | — | 137 |
| `part_of` | department/org → institution | — | 11 |
| `performs_on` | PI → program | — | 43 |
| `biosecurity_eval` | org → org (evaluator → evaluated) | — | 10 |
| `policy_forum` | org → publication | — | 6 |
| `published_study` | author/org → publication | — | 13 |
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
scripts/notebooks/s5_policy_bigtech_exploration.ipynb  ← dry run notebook
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

**Dual renderer approach (Sprint 7+):** Rather than replacing SVG with WebGL, we added a Canvas 2D alternative (`index_webgl.html`) alongside the SVG version (`index.html`). Both share the same graph data, layout computation, sidebar, filters, and interaction model. Canvas 2D provides better performance at 700+ nodes via batched edge rendering by type, `ctx.arc()`/`ctx.roundRect()` for nodes, and includes an FPS counter.

**Scripts:** `generate_html_v3.py` → `index.html` (SVG), `generate_webgl.py` → `index_webgl.html` (Canvas 2D)

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
├── index.html                          ← SVG visualization (self-contained, ~784 KB)
├── index_webgl.html                    ← Canvas 2D visualization (self-contained, ~782 KB)
├── README.md
├── ROADMAP.md                          ← this file
├── data/
│   ├── graph_data.json                 ← assembled graph (751 nodes, 1,178 edges)
│   ├── nodes.csv
│   ├── edges.csv
│   ├── raw/
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
│   │   └── s9_nsf_international/       ← Sprint 9: NSF + UKRI grants
│   │       ├── nsf_awards_raw.json             (183 keyword-search awards)
│   │       ├── nsf_pi_inst_awards.json         (82 PI/inst-targeted awards)
│   │       ├── nsf_selected.json               (16 matched awards, $14.3M)
│   │       ├── ukri_projects_raw.json          (348 unique UKRI projects)
│   │       ├── ukri_bio_ai_relevant.json       (75 bio+AI filtered)
│   │       └── ukri_selected.json              (2 institution-matched, £700K)
│   └── staged/
│       ├── op_edges.json               ← Sprint 2/3 (272 grants, 288 edges)
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
│       └── op_validation_report.json
└── scripts/
    ├── extract_data.py                 ← Sprint 1: OpenReview extraction
    ├── build_graph.py                  ← Sprint 1: graph assembly
    ├── generate_html_v3.py             ← SVG visualization generator (all sprints)
    ├── generate_webgl.py               ← Canvas 2D visualization generator (Sprint 7+)
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
    └── notebooks/
        └── s5_policy_bigtech_exploration.ipynb  ← Sprint 5 exploration
```
