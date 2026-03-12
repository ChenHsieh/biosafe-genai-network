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

DIRECTION 3: Policy & Big Tech (lateral) [planned]
────────────────────────────────────────
AI companies ↔ biosecurity orgs / policy bodies
```

**Rule: no orphan nodes.** Every node must have at least one edge.

---

## Node Schema

| Type | Key Fields |
|------|-----------|
| `funder` | id, label, short, url, description |
| `program` | id, label, parent→funder, url |
| `org` | id, label, entity_type, url |
| `institution` | id, label, url (from Sprint 1 OpenReview) |
| `author` | id, label, url, details |
| `presentation` | id, label, url |
| `department` | id, label, parent→institution |

`org.entity_type`: `institution` / `org` / `individual` / `pooled_grant`

## Edge Schema

| Type | Direction | Key Fields |
|------|-----------|-----------|
| `funds` | funder/program → org | amount, date_range, grant_title, confidence |
| `authored` | author → presentation | — |
| `current_affiliation` | author → institution | — |
| `past_affiliation` | author → institution | — |
| `part_of` | department → institution | — |
| `contracts` | program → org | amount, confidence [planned] |

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

## Sprint 5: Policy & Big Tech Layer

**Goal:** Map AI companies' biosecurity evaluation relationships.

**Rule: only add edges with a specific, fetchable URL. If URL returns 403 and content cannot be verified from any fetchable source, the edge does not enter the graph.**

| Relationship | Source URL | Expected confidence |
|---|---|---|
| Anthropic → SecureBio | securebio.substack.com | HIGH if fetchable |
| OpenAI → Gryphon Scientific | openai.com press release | MEDIUM (403 expected) |
| OpenAI → LANL | openai.com press release | MEDIUM (403 expected) |
| Anthropic/OpenAI/DeepMind → NTI Bio | nti.org forum page | MEDIUM |
| SecureBio → NIST | nitrd.gov PDF | HIGH if fetchable |

**Scripts:**
```
scripts/s5_fetch_partnerships.py       → data/raw/partnerships_{source}.html
scripts/s5_extract_partnerships.py     → data/staged/partnership_edges.json
scripts/s5_validate_partnerships.py    → data/staged/partnership_validation_report.json
scripts/s5_merge_partnerships.py       → data/graph_data.json (updated)
```

---

## Sprint 6: Workshop Organizers & Invited Speakers

**Organizers:** Mengdi Wang (Princeton), Le Cong (Stanford), Kevin Esvelt (MIT), Zaixi Zhang (Princeton), Ruofan Jin (Princeton), Amrit Singh Bedi (UCF), Alvaro Velasquez (UC Boulder), Souradip Chakraborty (UMD)

**Invited speakers:** Jian Ma (CMU), Yoshua Bengio (Mila), Sheng Lin-Gibson (NIST)

**Source:** Workshop website (`biosafe-gen-ai.github.io`)

---

## Sprint 7: Cross-venue Expansion

Add 2–3 sibling workshops. Only pull papers where ≥1 author is already in the graph.

Candidates: NeurIPS SoLaR, ICLR ML for Drug Discovery, ACL/EMNLP dual-use risk workshops.

---

## Visualization Milestones

| Sprint | Est. nodes | Renderer |
|--------|-----------|----------|
| 1 | 350 | SVG ✅ |
| 2–3 | 502 | SVG ✅ |
| 4–5 | ~600–700 | SVG (current) |
| 6–7 | ~800–1500 | Consider WebGL (force-graph) |

When switching to force-graph (WebGL):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://unpkg.com/force-graph@1.43.5/dist/force-graph.min.js"></script>
```
**NEVER use `cdn.skypack.dev`** — won't expose ForceGraph as a global.
**NEVER call `zoomToFit()` inside `refreshGraph()`** — only once at init.

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
├── index.html                          ← visualization (self-contained, ~570 KB)
├── README.md
├── ROADMAP.md                          ← this file
├── data/
│   ├── graph_data.json                 ← assembled graph (updated each sprint)
│   ├── nodes.csv
│   ├── edges.csv
│   └── raw/
│       ├── openreview_papers.json      ← Sprint 1
│       └── op_grants_full.csv          ← Sprint 2/3
│   └── staged/
│       ├── op_edges.json               ← Sprint 2/3 (272 grants, 288 edges)
│       └── op_validation_report.json
└── scripts/
    ├── extract_data.py                 ← Sprint 1: OpenReview extraction
    ├── build_graph.py                  ← Sprint 1: graph assembly
    ├── generate_html_v3.py             ← visualization generator (all sprints)
    ├── quality_check.py                ← cumulative checks (all sprints)
    ├── s2_fetch_op_grants.sh           ← Sprint 2/3: fetch Coefficient CSV
    ├── s2_extract_op_grants.py         ← Sprint 2/3: extract + classify grants
    ├── s2_validate_op.py               ← Sprint 2/3: validate staged data
    └── s2_merge_op.py                  ← Sprint 2/3: merge into graph
```
