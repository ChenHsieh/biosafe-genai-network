# Biosecurity Atlas — Sprint Roadmap

## Goal

Build an interactive network graph mapping the intersection of **biosafety/biosecurity** and **artificial intelligence**: who funds what, who researches what, and how the funding landscape connects to the research community.

## Philosophy

Every sprint produces a **shippable, verified increment**. If Sprint N breaks, Sprints 1 through N-1 stay live. Data from each source is fetched, saved as raw files, validated independently, then merged. No hallucinated edges — every edge must trace to a downloadable source file.

### Anti-hallucination protocol

Every data pipeline script follows this pattern:

```
1. FETCH → save raw file to data/raw/ (CSV, JSON, HTML snapshot)
2. EXTRACT → parse raw file, produce candidate edges with matched_text
3. VALIDATE → run assertions, flag LOW confidence, write to data/staged/
4. HUMAN REVIEW → export flagged items to review spreadsheet
5. MERGE → only after review, merge into data/graph_data.json
```

**Rule: if you can't point to a line in a raw file, the edge doesn't exist.**

---

## Graph Architecture

The graph has **three directional layers** that overlap at bridge nodes:

```
DIRECTION 1: Funding Chain (top-down)
─────────────────────────────────────
Funders (Coefficient (prev. Open Philanthropy), NIH, DARPA, IARPA...)
    ↓ funds
Programs / Focus Areas
    ↓ contracts
Recipient organizations/lab/group
    ↓ contributions
researchers/PI/PhD/staff
    ↓ outcomes
publications, patents, tools, press, news

DIRECTION 2: Workshop Ecosystem (bottom-up)
──────────────────────────────────────────
NeurIPS 2025 BioSafe GenAI Workshop
    ↓
38 accepted papers (oral + poster)
    ↓ extract author affiliations from OpenReview API
authors / researchers
    ↓ search current and past affiliations with OSINT
Affiliated organizations
    ↓ trace back to funders if possible
funders

DIRECTION 3: Policy & Big Tech (lateral)
────────────────────────────────────────
AI companies (Anthropic, OpenAI, DeepMind, Meta) as orgs
    ↔ evaluates / presented_at / MOU signed / announced
Biosecurity orgs, policy bodies (NIST AISI, UK AISI)
```

    ↕ BRIDGE NODES ↕ between the 3 graphs
          Orgs and persons appear at the overlap between graphs

**Rule: no orphan nodes.** Every node must have at least one edge. If a node has no verifiable connection, skip it.

---

## Node Schema

| Type | Fields | Notes |
|------|--------|-------|
| `funder` | id, label, short, url, description, key_people | Funding agencies |
| `program` | id, label, short, parent (→funder), url, description, year_start, year_end | Focus areas or government programs |
| `media` | id, label, short, url, description, year | Conference/workshop, news, announcement |
| `org` | id, label, short, org_subtype, direction, url, key_people, description | Organizations |
| `publication` | id, title, authors, affiliations, presentation (oral/poster/paper), url, venue, year | Papers |

Org subtypes: `research_institute`, `think_tank`, `company`, `startup`, `government_lab`, `government_agency`

## Edge Schema

| Type | Meaning | Direction |
|------|---------|-----------|
| `funds` | funder → program, or funder/program → org | Dir1 |
| `contracts` | program → org (prime performer) | Dir1 |
| `evaluates` | org ↔ org (red-teaming, benchmarking, T&E) | Dir3 |
| `authored` | author → publication | Dir2 |
| `presented_at` | org → venue, or publication → venue | Dir2 |
| `current_affiliation` | author → org | Dir2 |
| `past_affiliation` | author → org | Dir2 |
| `part_of` | department → institution | Dir2 |

Edge fields: `id, source, target, type, amount (nullable), amount_note, date_range, url, extraction_method, confidence, needs_human_review, review_reason, matched_text`

---

## Sprint 1: Workshop Ecosystem ✅ COMPLETE

**Status:** Shipped. Data verified. Zero orphan nodes, zero broken edges.

**Scope:**
- 38 accepted papers (6 oral, 32 poster) from NeurIPS 2025 BioSafe GenAI
- 138 unique authors with OpenReview profiles + OSINT enrichment
- 166 institutions, 8 departments
- 479 edges (authored, current_affiliation, past_affiliation, part_of)

**Data files:**
- `data/raw_data.json` — full author profiles from OpenReview API
- `data/graph_data.json` — assembled graph
- `data/nodes.csv`, `data/edges.csv` — flat exports

**Scripts:** `scripts/extract_data.py`, `scripts/build_graph.py`, `scripts/generate_html_v3.py`

---

## Sprint 2: Coefficient (prev. Open Philanthropy) Funding Layer

**Goal:** Add the largest philanthropic biosecurity funder. Show which workshop-affiliated orgs receive funding and how much. Only grants at the intersection of biosafety/biosecurity and AI.

**Naming:** Open Philanthropy recently rebranded to **Coefficient** (also referred to as "Coefficient Giving"). Use "Coefficient (prev. Open Philanthropy)" as the funder label. The CSV endpoint still uses the openphilanthropy.org domain.

**New node types:**
- `funder`: Coefficient (prev. Open Philanthropy)
- `program`: Each focus area as a separate node (e.g., "Biosecurity and Pandemic Preparedness", "Navigating Transformative AI")

**New edge types:** `funds` (funder → program, program → org)

**Scope:** Keep it tight — only match the curated list of target orgs below. Don't auto-expand to every institution in the workshop. We can merge more later. Only include grants that are at the **intersection of biosafety/biosecurity and AI** (filter by focus area + keyword relevance). Time range: all historical grants to these orgs (no year filter).

**Data source:** Single CSV download.
```bash
curl -L -o data/raw/op_grants_full.csv \
  "https://www.openphilanthropy.org/wp-admin/admin-ajax.php?action=generate_grants"
```

**Target orgs:**
- SecureBio / Nucleic Acid Observatory
- Center for AI Safety / CAIS
- Johns Hopkins Center for Health Security
- MIT Media Lab / Kevin Esvelt / Sculpting Evolution
- Georgetown CSET
- Nuclear Threat Initiative / NTI
- RAND Corporation
- Gryphon Scientific

**Pipeline:**
```
scripts/s2_fetch_op_grants.sh         → data/raw/op_grants_full.csv
scripts/s2_extract_op_grants.py       → data/staged/op_edges.json
scripts/s2_validate_op.py             → data/staged/op_validation_report.json
# Human review of flagged items
scripts/s2_merge_op.py                → data/graph_data.json (updated)
```

**Expected bridge nodes:** SecureBio (7 workshop authors + OP grantee), Center for AI Safety (2 workshop authors + OP grantee), MIT/Kevin Esvelt (workshop organizer + OP grantee)

**Validation assertions:**
1. Every `funds` edge has a non-null `amount`
2. Every `funds` edge has a `url` pointing to the grant page
3. Every `funds` edge source traces to funder or program node
4. Every `funds` edge target exists in node set
5. No duplicate grants (deduplicate by grant URL)
6. Dollar amounts match CSV (± rounding)
7. Bridge nodes correctly detected
8. Every edge traces to a row in `data/raw/op_grants_full.csv`

**Known issues from previous builds:**
- Individual grant pages return HTTP 429. Use the CSV only.
- Georgetown CSET's $55M grant is under "Navigating Transformative AI", not "Biosecurity" — search both focus areas.
- Metabiota and Pirbright may not appear in CSV. Flag for human review, don't invent.
- Previous AI builds fabricated "OP→EcoHealth Alliance $5M" — no such grant exists. Always verify against CSV.

---

## Sprint 3: NIH Federal Funding

**Goal:** Add federal biomedical research grants for university labs with workshop authors. Only biosafety/biosecurity + AI intersection grants.

**Data source:** NIH RePORTER API
```
POST https://api.reporter.nih.gov/v2/projects/search
```

**Target institutions** (only those with workshop authors):
- Harvard University → `["HARVARD UNIVERSITY"]`
- Stanford University → `["STANFORD UNIVERSITY"]`
- Princeton University → `["PRINCETON UNIVERSITY"]`
- UC Berkeley → `["UNIVERSITY OF CALIFORNIA BERKELEY"]`
- MIT → `["MASSACHUSETTS INSTITUTE OF TECHNOLOGY"]`
- University of Pennsylvania → `["UNIVERSITY OF PENNSYLVANIA"]`

**Known API issues:**
- `org_names` MUST be a flat list of strings, NOT `[{"any_of": [...]}]`
- Org names must match NIH canonical names exactly
- Filter by keywords: biosafety, biocontainment, biosecurity, AI safety, generative AI, protein design safety
- International institutions (Oxford) won't appear in NIH

**Pipeline:**
```
scripts/s3_fetch_nih.py               → data/raw/nih_results_{org}.json
scripts/s3_extract_nih.py             → data/staged/nih_edges.json
scripts/s3_validate_nih.py            → data/staged/nih_validation_report.json
scripts/s3_merge_nih.py               → data/graph_data.json (updated)
```

---

## Sprint 4: DARPA/IARPA Programs

**Goal:** Map government biosecurity programs to their performers.

**Programs:**

| Program | Sponsor | URL slug | Known performers |
|---------|---------|----------|------------------|
| SAFE GENES | DARPA | safe-genes | Broad Institute, MIT, Harvard |
| P3 | DARPA | pandemic-prevention-platform | Duke, Vanderbilt, AbCellera |
| PREEMPT | DARPA | preventing-emerging-pathogenic-threats | UNC |
| Fun GCAT | IARPA | iarpa.gov/research-programs/fun-gcat | SRI, Harvard, Battelle, Virginia Tech, LLNL, JHU APL |

**Confidence protocol:**
- Performer name found in fetched page text → HIGH
- Known from literature but not on fetched page → MEDIUM, flag
- Page returned 403/404 → LOW, flag
- **NEVER add an edge based on AI inference alone**

**Known issues:**
- DARPA URL migration: `/program/X` → `/research/programs/X`
- IARPA returns 403 for automated scraping
- Program pages describe programs, not always performers

**Pipeline:**
```
scripts/s4_fetch_darpa.py             → data/raw/darpa_{program}.html
scripts/s4_extract_performers.py      → data/staged/darpa_edges.json
scripts/s4_validate_darpa.py          → data/staged/darpa_validation_report.json
scripts/s4_merge_darpa.py             → data/graph_data.json (updated)
```

---

## Sprint 5: Policy & Big Tech Layer

**Goal:** Map AI companies' biosecurity evaluation relationships. **ONLY add edges with a specific, fetchable URL.**

| Relationship | Source URL | Expected confidence |
|---|---|---|
| Anthropic → SecureBio | securebio.substack.com article | HIGH if fetchable |
| OpenAI → Gryphon Scientific | openai.com press release | MEDIUM (403 expected) |
| OpenAI → LANL | openai.com press release | MEDIUM (403 expected) |
| Anthropic/OpenAI/DeepMind → NTI Bio | nti.org forum page | MEDIUM (403 expected) |
| SecureBio → NIST | nitrd.gov PDF | HIGH if fetchable |

**Rule: if URL returns 403 and content cannot be verified from ANY fetchable source, edge does not enter the graph.**

**Pipeline:**
```
scripts/s5_fetch_partnerships.py      → data/raw/partnerships_{source}.html
scripts/s5_extract_partnerships.py    → data/staged/partnership_edges.json
scripts/s5_validate_partnerships.py   → data/staged/partnership_validation_report.json
scripts/s5_merge_partnerships.py      → data/graph_data.json (updated)
```

---

## Sprint 6: Workshop Organizers & Invited Speakers

**Known organizers:** Mengdi Wang (Princeton), Le Cong (Stanford), Kevin Esvelt (MIT), Zaixi Zhang (Princeton), Ruofan Jin (Princeton), Amrit Singh Bedi (UCF), Alvaro Velasquez (UC Boulder), Souradip Chakraborty (UMD)

**Known invited speakers:** Jian Ma (CMU), Yoshua Bengio (Mila), Sheng Lin-Gibson (NIST)

**Source:** Workshop website (biosafe-gen-ai.github.io)

---

## Sprint 7: Cross-venue Expansion

Add 2-3 sibling workshops. Only pull papers where ≥1 author is already in the graph.

**Candidates:** NeurIPS SoLaR, ICLR ML for Drug Discovery, ACL/EMNLP dual-use risk workshops.

---

## Visualization Milestones

| Sprint | Est. nodes | Renderer |
|--------|-----------|----------|
| 1 | ~350 | SVG (current) |
| 2-3 | ~400-500 | SVG (current) |
| 4-5 | ~500-600 | SVG or force-graph WebGL |
| 6-7 | ~800-1500 | force-graph WebGL |

When switching to force-graph (WebGL):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://unpkg.com/force-graph@1.43.5/dist/force-graph.min.js"></script>
```
**NEVER use cdn.skypack.dev** — won't expose ForceGraph as a global.
**NEVER call zoomToFit() inside refreshGraph()** — only once at init.

---

## Quality Checks (run after every sprint)

1. No dangling edge references (source/target not in node set)
2. No duplicate node IDs
3. No duplicate edge IDs
4. No orphan nodes (nodes with zero edges)
5. No NaN/Infinity/undefined in JSON
6. All nodes have required fields (id, type, label)
7. All edges have required fields (source, target, type)
8. All edge types are valid enum values
9. All node types are valid enum values
10. Bridge nodes properly detected and marked
11. All `funds` edges have amount + source URL
12. All `contracts` edges have confidence score
13. Graph connectivity > 80%
14. **Every edge traces to a file in data/raw/**

---

## Known Hallucination Patterns (from previous builds)

Previous AI-assisted builds produced ~9% false edge rate, ~11% wrong amounts:

1. **Fabricated funding** — e.g., "OP→EcoHealth Alliance $5M" (no such grant). Always verify against CSV/API.
2. **Invented programs** — e.g., "DARPA BioAutoMATED" (MIT Lincoln Lab tool, not a DARPA program), "DARPA SHIELD" (supply chains, not biosecurity).
3. **Conflated amounts** — attributing total funding from all sources to a single funder. Use per-grant amounts only.
4. **Misattributed sponsors** — e.g., "DARPA Fun GCAT" (it's IARPA, not DARPA).
5. **Assumed partnerships** — e.g., "Meta FAIR ↔ SecureBio collaboration" (SecureBio evaluated Meta's models, but no formal partnership).

---

## File Structure

```
biosecurity-atlas/
├── index.html                          ← visualization (self-contained)
├── README.md
├── ROADMAP.md                          ← this file
├── LICENSE
├── .nojekyll
├── .gitignore
├── .gitguardian.yaml
├── assets/
│   └── preview.svg
├── data/
│   ├── graph_data.json                 ← assembled graph (updated each sprint)
│   ├── nodes.csv
│   ├── edges.csv
│   ├── raw/                            ← untouched source files (committed)
│   │   ├── openreview_papers.json      ← Sprint 1
│   │   ├── op_grants_full.csv          ← Sprint 2
│   │   ├── nih_results_*.json          ← Sprint 3
│   │   ├── darpa_*.html                ← Sprint 4
│   │   └── partnerships_*.html         ← Sprint 5
│   └── staged/                         ← extracted + validated, pre-merge
│       ├── op_edges.json               ← Sprint 2
│       ├── nih_edges.json              ← Sprint 3
│       ├── darpa_edges.json            ← Sprint 4
│       └── partnership_edges.json      ← Sprint 5
├── scripts/
│   ├── extract_data.py                 ← Sprint 1
│   ├── build_graph.py                  ← Sprint 1
│   ├── generate_html_v3.py             ← visualization generator
│   ├── s2_fetch_op_grants.sh           ← Sprint 2
│   ├── s2_extract_op_grants.py         ← Sprint 2
│   ├── s2_validate_op.py              ← Sprint 2
│   ├── s2_merge_op.py                  ← Sprint 2
│   └── quality_check.py               ← cumulative checks
└── SOCIAL_MEDIA_COPY.md
```
