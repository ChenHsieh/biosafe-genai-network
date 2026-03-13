# Biosecurity Atlas — Critical Audit Report

*Date: 2026-03-13 | Graph state: 766 nodes, 1,264 edges*

## Executive Summary

The Biosecurity Atlas has grown through 17 sprints from 350 nodes to 766 nodes. While the anti-hallucination protocol and quality checks have prevented fabricated edges, the project has accumulated structural debt in three areas: **duplicate nodes inflating the graph by ~5%**, **scope creep in publications**, and **schema inconsistencies in edge types**. This audit identifies 8 categories of issues and proposes concrete fixes.

## Finding 1: Duplicate Nodes (Critical)

**16 exact-duplicate label groups exist in the graph.** These artificially inflate node counts and fracture edge connectivity.

### 1a. Duplicate org nodes (4 pairs)

| Canonical Node (keep) | Duplicate (remove) | Impact |
|---|---|---|
| `org_council_on_strategic_risks` (deg=6) | `org_council_strategic_risks` (deg=1) | Merge edges |
| `org_massachusetts_general_hospital` (deg=1) | `org_darpa_massachusetts_general_hospital` (deg=1) | Merge edges |
| `org_university_of_california_davis` (deg=2) | `org_darpa_university_of_california_davis` (deg=1) | Merge edges |
| `org_north_carolina_state_university` (deg=1) | `org_darpa_north_carolina_state_university` (deg=1) | Merge edges |

These arose because Sprint 4 (DARPA/IARPA) created `org_darpa_*` prefixed nodes without checking existing Sprint 2/3 grantee nodes.

### 1b. Near-duplicate institution

`inst_University_of_the_Chinese_Academy_of_Sciences` (deg=2) vs `inst_University_of_Chinese_Academy_of_Sciences` (deg=1) — only difference is "the". Merge into former (higher degree).

### 1c. NIH grant fiscal-year duplicates (16 redundant nodes)

The NIH RePORTER extract kept separate nodes for each fiscal year of the same grant project. Example: `grant_nih_5R01AI152209_05`, `_04`, `_03` are all FY instances of R01AI152209. Each has identical PI and institution links.

10 base projects have 26 total FY nodes → should be 10 nodes. **16 redundant program nodes and ~32 redundant edges.**

**Recommendation:** Merge each FY group into the most recent FY node, summing amounts.

## Finding 2: SecureBio Type Inconsistency (Medium)

SecureBio (`inst_SecureBio`) is typed as `institution` but is a biosecurity evaluation organization — not a university, hospital, or research institute. It should be type `org` with subtype `evaluator`. This matters because:

- It's the 4th highest-degree node in the graph (deg=30)
- It has `authored` edges to publications (orgs can author; institutions typically don't)
- The node schema says `institution` is for entities with "lat, lon, location, country" — SecureBio has none

## Finding 3: Edge Type Direction Violations (89 total)

### 3a. Schema-valid but schema-undocumented (71)

- **71 `funds` edges from funder → program:** This is the Coefficient cascade pattern (Coefficient → focus area programs → grantees). The schema says `funds: funder/program → org/inst`, but the funder→program hierarchy uses the same edge type. This is a **design decision, not a bug**, but the schema should document it.

### 3b. Actual mismatches (18)

- **8 `current_affiliation` edges targeting `department` nodes:** Authors affiliated with departments (e.g., "AGI Safety and Alignment Team" at DeepMind). The schema says `current_affiliation: author → institution/org`. The target type `department` is not listed. These should either target the parent institution or `department` should be added to the allowed target types.

- **9 `authored` edges where source is `institution` or `org`:** These are institutional-authorship edges (e.g., "RAND Corporation → RAND publication", "SecureBio → SecureBio RFI Response"). The schema says `authored: author → presentation`. These should use `published_study` or `policy_forum` instead, or the schema should be updated.

- **1 `funds` edge where target is `author`:** An individual grantee classified as an author.

## Finding 4: Scope Creep in Publications (Medium)

4 publications fail the dual-axis (bio AND AI) relevance test that the Sprint 12 audit established as the standard:

| Publication | Problem | Linked Author |
|---|---|---|
| Benchmarking Graph Neural Networks | Pure ML, no bio connection | Yoshua Bengio |
| Automated Detection of Anatomical Landmarks During Colonoscopy | Medical imaging, not biosecurity | Yoshua Bengio |
| Brain-wide silencing of prion protein by AAV | Gene therapy, no AI | Jonathan Weissman |
| Assessing the safety of new germicidal far-UVC technologies | UVC safety, no AI | Kevin Esvelt |

These were added in Sprint 10 as "key personnel publications" to reduce degree-1 author nodes. However, the Sprint 12 audit removed 11 similar off-topic publications. These 4 were missed.

**Recommendation:** Remove these 4 publications and their edges. The linked authors have other connections (Bengio deg=19, Esvelt deg=18, Weissman deg=7) and won't become orphans.

## Finding 5: 40% Degree-1 Nodes

310 of 766 nodes (40.5%) have exactly one edge. Breakdown:

- 124 org nodes (mostly OP grantees with a single funds edge)
- 104 institution nodes (workshop-only affiliations)
- 59 author nodes (cross-venue co-authors added in Sprint 7)
- 18 publication nodes (single-author-link pubs)
- 4 funder nodes (Wellcome, BARDA, IARPA, UKRI with minimal connections)
- 1 program node

**Assessment:** This is partly unavoidable (many grantees genuinely have only one grant in scope), but it signals the graph is wide and shallow. The 59 degree-1 authors from Sprint 7 cross-venue expansion added breadth without depth — they have one `authored` edge and no affiliation, publication, or funding links.

## Finding 6: IARPA Funding = $0

All 11 IARPA Fun GCAT grants show $0 amounts. The USASpending API returned data but contract amounts were classified or not reported. The graph currently shows IARPA as a funder with a program and 11 performers but $0 total funding — which is misleading.

**Recommendation:** Add a note field or set a reasonable estimate from public sources (Fun GCAT was a ~$20M program based on press releases).

## Finding 7: Funding Double-Count Risk

The `$1.22B tracked funding` headline number includes the Wellcome Trust's £200M (~$260M) aggregate figure, which covers all Wellcome→Oxford funding, not just biosecurity+AI. This inflates the total. Similarly, the Coefficient $543M includes grants in focus areas like "Global Health R&D" and "GiveWell-Recommended Charities" that are not primarily biosecurity+AI.

**Recommendation:** Report two funding totals: "core biosecurity+AI funding" (Coefficient Biosecurity & Pandemic Preparedness + DARPA bio programs + NIH bio grants + targeted evaluator funding) vs. "expanded scope" (everything in the graph).

## Finding 8: Missing s10 Script

The Sprint 10 script (`s10_author_pub_backfill.py`) is listed in the ROADMAP as "(inline in session)" — it was never saved to the `scripts/` directory. All other sprints have their extraction scripts preserved.

## Summary of Recommended Fixes

| Fix | Severity | Nodes removed | Edges affected |
|---|---|---|---|
| Merge 4 duplicate org pairs | Critical | -4 | ~4 retargeted |
| Merge UCAS near-duplicate | Critical | -1 | ~1 retargeted |
| Deduplicate 10 NIH grant groups | Critical | -16 | ~32 removed |
| Remove 4 off-topic publications | Medium | -4 | -4 removed |
| Fix SecureBio type → org | Medium | 0 | 0 |
| Update edge schema documentation | Low | 0 | 0 |

**Estimated post-fix graph: ~741 nodes, ~1,224 edges** — a cleaner, more accurate graph that better represents the actual biosecurity+AI landscape without inflated counts.
