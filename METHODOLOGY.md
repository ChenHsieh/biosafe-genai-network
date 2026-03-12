# Methodology: Biosecurity Atlas Data Sourcing

## Overview

The Biosecurity Atlas maps the network of researchers, institutions, and funders working at the intersection of biosafety and generative AI. Data was collected across four sprints, each adding a new layer to the graph. This document records what was tried, what worked, what didn't, and key insights from the process.

---

## Sprint 1: NeurIPS 2025 BioSafe GenAI Workshop

**Goal:** Build the base graph from workshop papers, authors, and affiliations.

**Data source:** Semantic Scholar API + workshop program page.

**What worked:**
- Semantic Scholar's `/paper/search` endpoint reliably returned paper metadata, author lists, and affiliation strings for all 38 workshop presentations.
- Author deduplication via Semantic Scholar author IDs was straightforward.
- Institution extraction from affiliation strings used a combination of known-institution lookups and heuristic parsing (splitting on commas, matching university/institute keywords).

**What didn't work:**
- Some authors had multiple Semantic Scholar profiles (e.g., name variants). These were manually reconciled via the alias table.
- Affiliation strings are often messy ("Department of X, University of Y, Country") requiring careful parsing to extract the correct institution.
- A few workshop papers were not indexed in Semantic Scholar at query time and had to be added manually from the program page.

**Key insight:** Workshop author networks are surprisingly dense — 90%+ of nodes connect into one giant component even before adding funding data, because many authors share institutional affiliations.

**Output:** 38 papers, 138 authors, 166 institutions, 8 departments. 479 edges (authored, current_affiliation, past_affiliation, part_of).

---

## Sprint 2: Coefficient (Open Philanthropy) Biosecurity Grants

**Goal:** Add philanthropic funding data to show which workshop-affiliated institutions receive biosecurity funding.

**Data source:** Coefficient (formerly Open Philanthropy) grants CSV, publicly available at their website.

**Initial approach — Curated org allowlist:**
- Started with a hand-curated list of ~15 organizations known to be in the biosecurity space.
- Filtered the 2,714-row CSV for grants to those specific orgs.
- This was too narrow — missed hundreds of relevant grants to universities and research institutes.

**What worked:**
- The CSV is clean and well-structured with columns for organization name, grant amount, focus area, and grant description.
- Focus area filtering was highly effective: "Biosecurity & Pandemic Preparedness" and "Scientific Research" focus areas captured the most relevant grants directly.
- A three-tier inclusion logic emerged as the best approach:
  1. **BIO_FOCUS areas** (Biosecurity, Global Health R&D, etc.) → always include
  2. **EXCLUDED_FOCUS areas** (Farm Animal Welfare, Alternatives to Animal Products) → always skip
  3. **Everything else** → apply a `BIO_REL` keyword regex filter on grant name + org name

**What didn't work:**
- The curated org-allowlist approach (Sprint 2 initial) was too narrow and required constant manual updates.
- Keyword-only filtering without focus area pre-filtering produced too many false positives (e.g., "protein" matching food science grants).
- Some grant titles are misleading — "Canine Cancer Vaccine" passed the bio-relevance filter but isn't biosecurity-relevant. A `GRANT_BLOCKLIST` of 7 specific patterns was needed.

**Entity resolution challenges:**
- Organization names in the CSV don't match Semantic Scholar affiliation strings (e.g., "Johns Hopkins Center for Health Security" vs "Johns Hopkins University").
- A `BRIDGE_MAP` of 24 entries was needed to connect Sprint 2 org nodes to Sprint 1 institution nodes.
- Two-word org names like "Open Philanthropy" could false-match person name regexes — required an institution-check-first rule.
- Aliases were needed for typos and variants: "iGEM" (3 variants), "RAND" vs "RAND Corporation", JHU typo.

**Human-in-the-loop review:**
- After the full extraction, all 283 grants were presented grouped by focus area for user review.
- 7 grants were flagged as questionable and excluded after review (Canine Cancer Vaccine, Reproductive Biology, Gut Microbiome Repair, Plant Protein Optimization, Ready-to-Use Therapeutic Food, Project Peanut Butter, Syphilis Vaccine Economic Research).
- This review step was essential — automated filters alone aren't sufficient for this domain.

**Key insight:** The three-tier filter (focus area → exclusion → keyword) strikes the right balance between recall and precision. Pure keyword matching is too noisy; pure allowlisting is too narrow. The human-in-the-loop step catches the remaining edge cases that no automated filter handles well.

**Output:** 272 grants, 135 org nodes, 16 program nodes, 1 funder node. $543M total funding. 19 bridge nodes connecting funding to workshop institutions.

---

## Sprint 3: Expansion and Bridge Map

Sprint 3 was integrated into the Sprint 2 workflow above. The key addition was expanding the `BRIDGE_MAP` from 6 to 24 entries by systematically comparing Sprint 2 grantee organizations against Sprint 1 institutions. Care was taken to avoid false bridges (e.g., University of California campuses are distinct institutions — UC Berkeley ≠ UC Davis ≠ UCSF).

---

## Sprint 4: DARPA / IARPA Government Programs

**Goal:** Map US government biosecurity programs to their performers and connect them to workshop-affiliated labs.

### Data Source 1: USASpending.gov API

**What worked:**
- The API (`/api/v2/search/spending_by_award/`) returns structured award data with recipient names, amounts, descriptions, dates, and award IDs.
- Agency subtier filtering (`Defense Advanced Research Projects Agency`) effectively isolates DARPA awards.
- Combining agency filter + bio-relevant keywords gave 110 awards (59 contracts + 51 grants).
- Award descriptions often contain program names (PROPHECY, ARCADIA, etc.) enabling program classification.

**What didn't work:**
- **Keyword minimum length**: The API rejects keywords shorter than 3 characters, so "P3" couldn't be searched directly.
- **Award type mixing**: The API doesn't allow mixing contracts (A/B/C/D) and grants (02/03/04/05) in one query — must run separate queries.
- **Keyword search is OR-based and global**: Searching for "PREEMPT" without an agency filter returns thousands of unrelated results ("non-preemptible satellite transponder"). Agency filtering is essential.
- **IARPA data is not available**: Intelligence community funding is not in USASpending.gov. IARPA agency filter returned 0 results regardless of keywords. The "functional genomic" keyword search returned NIH awards, not IARPA.
- **Grant descriptions are often generic**: Many DARPA BTO grants say only "THE PURPOSE OF THIS AGREEMENT IS TO FUND RESEARCH SUPPORTING THE DEFENSE ADVANCED RESEARCH PROJECTS AGENCY BIOLOGICAL TECHNOLOGIES OFFICE" without naming the specific program.

**Bio+AI filtering:**
- Of 103 bio-relevant DARPA awards, only 21 (20%) mention AI/ML/computational methods — the rest are pure wet-lab countermeasure work.
- Decision: include only the 21 AI-relevant awards on the graph ($81M), keep the other $391M in raw data for reference.

### Data Source 2: IARPA Program Page (Web Scrape)

**What worked:**
- The IARPA Fun GCAT program page at `iarpa.gov/research-programs/fun-gcat` lists all performers explicitly: 5 prime performers and 6 T&E partners.
- Fun GCAT is directly at the bio+AI intersection (AI-driven DNA threat screening software, 500x computational speedup).
- WebFetch tool successfully extracted the content despite `requests` library getting 403.

**What didn't work:**
- The `requests` Python library received HTTP 403 from iarpa.gov (Cloudflare protection). WebFetch tool bypassed this.

### Data Source 3: DARPA Press Releases

**What worked:**
- DARPA news releases name specific performer teams, PIs, and their institutions — data not available anywhere else.
- Found full rosters for: SAFE GENES (7 teams, $65M), P3 (4 performers), PREEMPT (5 lead teams + ~20 sub-teams), PREPARE (5 teams).
- PI names like Kevin Esvelt, George Church, Jennifer Doudna are high-value nodes that connect the academic biosecurity community to government funding.
- Kevin Esvelt was already in the graph as a workshop author → now also a DARPA SAFE GENES PI, creating a direct bridge.

**What didn't work:**
- DARPA program pages (`darpa.mil/research/programs/...`) describe programs generically but don't name performers. The performer data is only in the news announcements.
- PREPARE program page returned 404 (possibly renamed/removed).
- Press release data lacks funding amounts per team — only aggregate program totals.

### Data Provenance

Every edge in Sprint 4 is tagged with its `extraction_method`:
- `usaspending_api` — 21 edges with dollar amounts and award IDs
- `webpage_scrape` — 11 edges from IARPA Fun GCAT page (amounts classified)
- `news_release` — 14 PI affiliation edges sourced from DARPA news (no amounts, labeled with source URL)
- `hierarchy` — 12 funder→program structural edges

**Key insight:** Government funding data requires triangulating multiple sources. USASpending.gov has amounts but generic descriptions; press releases have performer details but no amounts; program pages have program descriptions but no performers. No single source is sufficient.

**Key insight:** The bio+AI intersection in government funding is narrower than expected. Only 20% of DARPA BTO awards involve computational/AI methods. Most government biosecurity spending goes to wet-lab countermeasures, diagnostics, and vaccine development — important work, but not at the AI intersection this atlas focuses on.

**Output:** 51 new nodes (2 funders, 12 programs, 13 PI authors, 24 orgs), 58 new edges. $81M in DARPA funding captured. 20 bridge edges connecting to existing graph.

---

## Technical Pipeline

```
Raw data (CSV, API JSON, HTML)
  → Extraction scripts (s2_extract_op_grants.py, s4_extract_darpa_iarpa.py)
  → Staged JSON (data/staged/*.json)
  → Merge scripts (s2_merge_op.py or inline merge)
  → graph_data.json
  → Quality check (quality_check.py, 14 checks)
  → HTML generation (generate_html_v3.py, 3 layout algorithms)
  → index.html (interactive visualization)
```

### Quality Checks (14 automated)
1. No dangling edge references
2. No duplicate node IDs
3. No duplicate edge IDs
4. No orphan nodes
5. No NaN/Infinity/undefined in JSON
6. All nodes have required fields
7. All edges have required fields
8. All edge types are valid
9. All node types are valid
10. Bridge nodes detected
11. All grant funds edges have amount
12. All contracts edges have confidence
13. Graph connectivity > 80%
14. Raw data files exist

---

## Data Freshness and Limitations

- **Coefficient CSV**: Snapshot from time of download. New grants added after that date are not captured.
- **USASpending.gov**: Queried 2010–2025 range. Data lags real-time by ~30 days per USASpending documentation.
- **IARPA Fun GCAT**: Program ended September 2022. Performer list is final.
- **DARPA press releases**: Capture point-in-time announcements. Team compositions may have changed over program duration.
- **PI affiliations**: Sourced from press releases at time of award. Some PIs may have moved institutions since.
- **Funding amounts**: Coefficient amounts are grant values; DARPA amounts are total obligated contract/award values (may include options not exercised).

---

## Insights Reserved for Report

Several findings from this process are better suited for the insights report than the methodology document. These include patterns in institutional overlap between philanthropic and government funding, the concentration of biosecurity+AI work at a small number of universities, and the role of specific individuals as bridges between the academic workshop community and government biosecurity programs.
