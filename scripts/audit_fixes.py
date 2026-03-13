"""
Biosecurity Atlas — Comprehensive Audit Fixes
===============================================
Implements fixes from AUDIT_REPORT.md:
  Fix 1: Merge 4 duplicate org pairs + 1 near-dupe institution
  Fix 2: Deduplicate 10 NIH grant FY groups (16 redundant nodes)
  Fix 3: Remove 4 off-topic publications (scope creep)
  Fix 4: Change SecureBio type from institution → org
  Fix 5: Update edge schema (authored → published_study for org→pub edges)
"""

import json, re, copy
from collections import defaultdict

GRAPH_FILE = "data/graph_data.json"

with open(GRAPH_FILE) as f:
    graph = json.load(f)

nodes = graph["nodes"]
edges = graph["edges"]
nodes_by_id = {n["id"]: n for n in nodes}

removed_nodes = set()
removed_edges = set()
retargeted_edges = 0
modified_nodes = 0
modified_edges = 0

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 1: MERGE DUPLICATE ORG NODES
# ═══════════════════════════════════════════════════════════════════════════════

# (keep, remove) pairs
ORG_DUPES = [
    ("org_council_on_strategic_risks", "org_council_strategic_risks"),
    ("org_massachusetts_general_hospital", "org_darpa_massachusetts_general_hospital"),
    ("org_university_of_california_davis", "org_darpa_university_of_california_davis"),
    ("org_north_carolina_state_university", "org_darpa_north_carolina_state_university"),
]

for keep_id, remove_id in ORG_DUPES:
    assert keep_id in nodes_by_id, f"Missing keep node: {keep_id}"
    assert remove_id in nodes_by_id, f"Missing remove node: {remove_id}"

    # Retarget all edges from remove_id → keep_id
    for e in edges:
        if e.get("source") == remove_id:
            e["source"] = keep_id
            retargeted_edges += 1
        if e.get("target") == remove_id:
            e["target"] = keep_id
            retargeted_edges += 1

    removed_nodes.add(remove_id)

print(f"Fix 1a: Marked {len(ORG_DUPES)} duplicate org nodes for removal, retargeted {retargeted_edges} edges")

# Near-duplicate UCAS institution
UCAS_KEEP = "inst_University_of_the_Chinese_Academy_of_Sciences"
UCAS_REMOVE = "inst_University_of_Chinese_Academy_of_Sciences"
for e in edges:
    if e.get("source") == UCAS_REMOVE:
        e["source"] = UCAS_KEEP
        retargeted_edges += 1
    if e.get("target") == UCAS_REMOVE:
        e["target"] = UCAS_KEEP
        retargeted_edges += 1
removed_nodes.add(UCAS_REMOVE)
print(f"Fix 1b: Merged UCAS near-duplicate")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 2: DEDUPLICATE NIH GRANT FY INSTANCES
# ═══════════════════════════════════════════════════════════════════════════════

nih_grants = [n for n in nodes if n["type"] == "program" and n.get("subtype") == "nih_grant"]

# Group by base project number
nih_groups = defaultdict(list)
for n in nih_grants:
    m = re.search(r"grant_nih_\d?([A-Z]\d+[A-Z]+\d+)", n["id"])
    if m:
        nih_groups[m.group(1)].append(n)
    else:
        nih_groups[n["id"]].append(n)

nih_nodes_removed = 0
nih_edges_removed = 0

for proj, group in nih_groups.items():
    if len(group) <= 1:
        continue

    # Keep the most recent FY (highest suffix number, first in sorted ID)
    group.sort(key=lambda n: n["id"], reverse=True)
    keep = group[0]
    remove_list = group[1:]

    # Sum amounts from all FYs into the kept node
    total_amount = 0
    for n in group:
        for e in edges:
            if e.get("target") == n["id"] and e["type"] == "funds":
                total_amount += e.get("amount", 0) or 0

    # Retarget edges from removed nodes → kept node
    for rem in remove_list:
        for e in edges:
            if e.get("source") == rem["id"]:
                # Check if keep node already has this edge type to this target
                existing = any(
                    ex.get("source") == keep["id"] and ex.get("target") == e["target"] and ex["type"] == e["type"]
                    for ex in edges
                )
                if existing:
                    removed_edges.add(e["id"])
                    nih_edges_removed += 1
                else:
                    e["source"] = keep["id"]
                    retargeted_edges += 1
            if e.get("target") == rem["id"]:
                existing = any(
                    ex.get("source") == e["source"] and ex.get("target") == keep["id"] and ex["type"] == e["type"]
                    for ex in edges
                )
                if existing:
                    # Duplicate — sum amount into existing edge
                    for ex in edges:
                        if ex.get("source") == e["source"] and ex.get("target") == keep["id"] and ex["type"] == e["type"]:
                            if e["type"] == "funds" and e.get("amount"):
                                ex["amount"] = (ex.get("amount", 0) or 0) + (e.get("amount", 0) or 0)
                            break
                    removed_edges.add(e["id"])
                    nih_edges_removed += 1
                else:
                    e["target"] = keep["id"]
                    retargeted_edges += 1

        removed_nodes.add(rem["id"])
        nih_nodes_removed += 1

print(f"Fix 2: Marked {nih_nodes_removed} redundant NIH FY nodes for removal, {nih_edges_removed} redundant edges")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 3: REMOVE OFF-TOPIC PUBLICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

OFF_TOPIC_PUBS = [
    "pub_s2_Benchmarking_Graph_Neural_Networks_2023",          # Pure ML
    "pub_s2_Automated_Detection_of_Anatomical_Landma_2023",    # Colonoscopy imaging
    "pub_s2_Brain_wide_silencing_of_prion_protein_by_2024",    # Gene therapy, no AI
    "pub_s2_Assessing_the_safety_of_new_germicidal_f_2023",    # UVC safety, no AI
]

for pub_id in OFF_TOPIC_PUBS:
    if pub_id in nodes_by_id:
        removed_nodes.add(pub_id)
        # Remove all edges connected to this node
        for e in edges:
            if e.get("source") == pub_id or e.get("target") == pub_id:
                removed_edges.add(e["id"])

print(f"Fix 3: Marked {len(OFF_TOPIC_PUBS)} off-topic publications for removal")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 4: SECUREBIO TYPE → org
# ═══════════════════════════════════════════════════════════════════════════════

securebio = nodes_by_id.get("inst_SecureBio")
if securebio and securebio["type"] == "institution":
    securebio["type"] = "org"
    securebio["subtype"] = "evaluator"
    modified_nodes += 1
    print(f"Fix 4: Changed SecureBio type institution → org (evaluator)")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 5: FIX 'authored' EDGES FROM org/institution → publication
# ═══════════════════════════════════════════════════════════════════════════════
# These should be 'policy_forum' or 'published_study', not 'authored'
# 'authored' is for author → presentation

for e in edges:
    if e["type"] != "authored":
        continue
    src = nodes_by_id.get(e.get("source"))
    tgt = nodes_by_id.get(e.get("target"))
    if not src or not tgt:
        continue
    if src["type"] in ("institution", "org") and tgt["type"] == "publication":
        e["type"] = "policy_forum"
        modified_edges += 1

print(f"Fix 5: Changed {modified_edges} 'authored' edges (org/inst→pub) to 'policy_forum'")

# ═══════════════════════════════════════════════════════════════════════════════
# APPLY REMOVALS
# ═══════════════════════════════════════════════════════════════════════════════

# Remove marked edges first (before removing nodes)
graph["edges"] = [e for e in edges if e["id"] not in removed_edges]

# Remove duplicate edges that now point to same source+target+type
seen_edge_sigs = set()
deduped_edges = []
for e in graph["edges"]:
    sig = (e.get("source"), e.get("target"), e["type"])
    if sig in seen_edge_sigs and e["type"] in ("funds", "performs_on", "current_affiliation", "past_affiliation"):
        # Sum amounts for funds edges
        for kept in deduped_edges:
            if (kept.get("source"), kept.get("target"), kept["type"]) == sig:
                if e["type"] == "funds":
                    kept["amount"] = (kept.get("amount", 0) or 0) + (e.get("amount", 0) or 0)
                break
        continue
    seen_edge_sigs.add(sig)
    deduped_edges.append(e)

deduped_count = len(graph["edges"]) - len(deduped_edges)
graph["edges"] = deduped_edges

# Remove marked nodes
graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in removed_nodes]

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════

with open(GRAPH_FILE, "w") as f:
    json.dump(graph, f, indent=2)

print(f"\n{'='*50}")
print(f"AUDIT FIXES APPLIED")
print(f"{'='*50}")
print(f"Nodes removed: {len(removed_nodes)}")
print(f"Edges removed (explicit): {len(removed_edges)}")
print(f"Edges deduplicated: {deduped_count}")
print(f"Edges retargeted: {retargeted_edges}")
print(f"Nodes modified: {modified_nodes}")
print(f"Edges type-changed: {modified_edges}")
print(f"Final: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
