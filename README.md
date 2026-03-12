# Biosecurity Atlas

Interactive knowledge graph mapping the intersection of **biosafety, biosecurity, and AI** — connecting the NeurIPS 2025 BioSafe GenAI workshop research community to the philanthropic funding landscape.

**[Live Demo](https://chenhsieh.github.io/biosafe-genai-network/)**

---

## What This Is

A multi-layer graph built in verifiable sprints. Each sprint adds one data source, validates it independently, and merges it into the graph only after human review.

### Current State (Sprint 2/3 complete)

| Metric | Count |
|--------|-------|
| Total nodes | 502 |
| Total edges | 767 |
| Bridge nodes (appear in both workshop + funding) | 19 |
| Total funding mapped | $543M |
| Graph connectivity | 90.2% |

### Node breakdown

| Type | Count | Description |
|------|-------|-------------|
| Author | 138 | Workshop paper authors |
| Institution | 166 | Affiliated universities & research orgs |
| Presentation | 38 | Accepted papers (6 oral, 32 poster) |
| Org | 135 | Grantee organisations (funding layer) |
| Program | 16 | Coefficient focus areas |
| Funder | 1 | Coefficient (prev. Open Philanthropy) |
| Department | 8 | Sub-units of institutions |

### Edge breakdown

| Type | Count | Description |
|------|-------|-------------|
| `current_affiliation` | 172 | Author → current institution |
| `past_affiliation` | 136 | Author → former institution |
| `authored` | 163 | Author → paper |
| `funds` | 288 | Funder/program → grantee org |
| `part_of` | 8 | Department → institution |

### Bridge nodes (connect workshop ↔ funding layers)

Harvard, Oxford, Stanford, MIT, JHU, Columbia, Yale, Rutgers, Imperial College London, Broad Institute, SecureBio, RAND Corporation, University of Washington, University of Chicago, University of Georgia, University of Michigan, University of Maryland, Georgia Tech, Icahn School of Medicine at Mount Sinai

---

## Layers

### Layer 1 — Workshop Ecosystem (Sprint 1)

38 accepted papers from [NeurIPS 2025 BioSafe GenAI Workshop](https://openreview.net/group?id=NeurIPS.cc/2025/Workshop/BioSafe_GenAI), with author profiles and institutional affiliations extracted from the OpenReview API.

Key findings:
- **Dominant institutions**: UC Berkeley (9 authors), Princeton (7), SecureBio (7), Oxford (7), Harvard (5), Stanford (5)
- **Most prolific author**: ZAIXI ZHANG (4 papers — DNA jailbreaking, protein red-teaming, watermarking)
- **Governance gap**: Only 7 policy-oriented papers, mostly from a single group

### Layer 2 — Coefficient Funding (Sprints 2 & 3)

Grants from [Coefficient (prev. Open Philanthropy)](https://www.openphilanthropy.org/) selected by bio-relevance keyword filter across all 2,714 grants in their public CSV. 272 grants retained, 11 noise grants excluded via blocklist.

Focus areas captured: Biosecurity & Pandemic Preparedness, Science Supporting Biosecurity, Global Health R&D, Human Health and Wellbeing, GCR Capacity Building, Scientific Research, Transformative Basic Science, Navigating Transformative AI, and 8 others.

Top grantees: Gates Philanthropy Partners ($65M), JHU Center for Health Security ($55M), BlueDot Impact ($32M), Nuclear Threat Initiative ($30M).

---

## Features

- **3 layouts**: Column (grouped by type), Force-directed (clustered), Radial
- **Click-to-select**: Lock selection; connected edges highlighted while panning
- **Detail panel**: Funding totals, neighbor nodes, OpenReview / Scholar / DBLP / LinkedIn links
- **Layers**: Toggle between "All", "Workshop only", "Funding only"
- **Edge-type filters**: Show/hide funds, authored, affiliation edges individually
- **Search**: Find any node by name
- **Simplified mode**: Hide low-connectivity nodes
- **Fully static**: Pre-computed SVG layouts, zero runtime physics

---

## Data Files

| File | Description |
|------|-------------|
| `data/graph_data.json` | Full graph — nodes, edges, metadata |
| `data/nodes.csv` | All nodes with type, degree, URL |
| `data/edges.csv` | All edges with source, target, type, amount |
| `data/raw/openreview_papers.json` | Raw OpenReview API response (Sprint 1) |
| `data/raw/op_grants_full.csv` | Coefficient grants CSV — 2,714 rows (Sprint 2/3) |
| `data/staged/op_edges.json` | Extracted + validated funding edges (pre-merge) |
| `data/staged/op_validation_report.json` | Validation results |

---

## Reproduce

```bash
# Sprint 1: extract workshop data
python scripts/extract_data.py        # → data/raw/openreview_papers.json
python scripts/build_graph.py         # → data/graph_data.json (Sprint 1)

# Sprint 2/3: add Coefficient funding layer
bash scripts/s2_fetch_op_grants.sh    # → data/raw/op_grants_full.csv
python scripts/s2_extract_op_grants.py  # → data/staged/op_edges.json
python scripts/s2_validate_op.py        # → data/staged/op_validation_report.json
# human review of staged data, then:
python scripts/s2_merge_op.py           # → data/graph_data.json (updated)

# Quality check and render
python scripts/quality_check.py
python scripts/generate_html_v3.py    # → index.html (self-contained, ~570 KB)
```

Requires Python 3.8+, stdlib only.

---

## Deploy

Push to GitHub, enable Pages (Settings → Pages → Branch: `main`, folder: `/`).
Live at `https://YOUR_USERNAME.github.io/biosafe-genai-network/`

`index.html` is fully self-contained (all data embedded, no CDN dependencies).

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full sprint plan. Next up: NIH federal grants (Sprint 3), DARPA/IARPA programs (Sprint 4), Policy & Big Tech layer (Sprint 5).

---

## License

Data sourced from [OpenReview](https://openreview.net) (terms of use) and [Coefficient/Open Philanthropy](https://www.openphilanthropy.org/grants/) (public data). Visualization code is MIT licensed.
