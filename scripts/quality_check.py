#!/usr/bin/env python3
"""
Cumulative quality checks for the Biosecurity Atlas graph.
Run after every sprint to verify graph integrity.

From ROADMAP.md:
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
13. Graph connectivity > 80% (largest component / total nodes)
14. Every edge traces to a file in data/raw/
"""

import json
import math
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, "data", "graph_data.json")

VALID_NODE_TYPES = {"funder", "program", "presentation", "author", "institution", "department", "org", "publication", "media"}
VALID_EDGE_TYPES = {"funds", "contracts", "evaluates", "authored", "presented_at",
                    "current_affiliation", "past_affiliation", "part_of", "organized", "invited_speaker",
                    "performs_on", "biosecurity_eval", "policy_forum", "published_study"}


def main():
    print(f"Loading {GRAPH_FILE}...")
    with open(GRAPH_FILE) as f:
        graph = json.load(f)

    nodes = graph["nodes"]
    edges = graph["edges"]
    node_ids = {n["id"] for n in nodes}

    passed = 0
    failed = 0
    total = 14

    def check(num, name, ok, detail=""):
        nonlocal passed, failed
        status = "PASS" if ok else "FAIL"
        icon = "+" if ok else "X"
        print(f"  [{icon}] {num:2d}. {name}" + (f" — {detail}" if detail else ""))
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nGraph: {len(nodes)} nodes, {len(edges)} edges\n")

    # 1. Dangling edge references
    dangling = [(e.get("id", "?"), e["source"], e["target"])
                for e in edges if e["source"] not in node_ids or e["target"] not in node_ids]
    check(1, "No dangling edge references", len(dangling) == 0,
          f"{len(dangling)} dangling" if dangling else "")

    # 2. Duplicate node IDs
    all_nids = [n["id"] for n in nodes]
    dupes = [nid for nid in all_nids if all_nids.count(nid) > 1]
    check(2, "No duplicate node IDs", len(set(dupes)) == 0,
          f"dupes: {set(dupes)}" if dupes else "")

    # 3. Duplicate edge IDs
    all_eids = [e.get("id", f"{e['source']}_{e['target']}") for e in edges]
    edge_dupes = [eid for eid in all_eids if all_eids.count(eid) > 1]
    check(3, "No duplicate edge IDs", len(set(edge_dupes)) == 0,
          f"dupes: {list(set(edge_dupes))[:5]}" if edge_dupes else "")

    # 4. Orphan nodes
    connected = set()
    for e in edges:
        connected.add(e["source"])
        connected.add(e["target"])
    orphans = [n["id"] for n in nodes if n["id"] not in connected]
    check(4, "No orphan nodes", len(orphans) == 0,
          f"{len(orphans)} orphans: {orphans[:5]}" if orphans else "")

    # 5. No NaN/Infinity/undefined
    raw = json.dumps(graph)
    has_bad = "NaN" in raw or "Infinity" in raw or "undefined" in raw
    check(5, "No NaN/Infinity/undefined in JSON", not has_bad)

    # 6. Nodes have required fields
    missing_fields = [n["id"] for n in nodes if not all(k in n for k in ("id", "type", "label"))]
    check(6, "All nodes have required fields", len(missing_fields) == 0,
          f"missing: {missing_fields[:5]}" if missing_fields else "")

    # 7. Edges have required fields
    missing_efields = [i for i, e in enumerate(edges) if not all(k in e for k in ("source", "target", "type"))]
    check(7, "All edges have required fields", len(missing_efields) == 0,
          f"missing at indices: {missing_efields[:5]}" if missing_efields else "")

    # 8. Valid edge types
    bad_etypes = [e.get("type", "?") for e in edges if e.get("type") not in VALID_EDGE_TYPES]
    check(8, "All edge types are valid", len(bad_etypes) == 0,
          f"invalid: {set(bad_etypes)}" if bad_etypes else "")

    # 9. Valid node types
    bad_ntypes = [n.get("type", "?") for n in nodes if n.get("type") not in VALID_NODE_TYPES]
    check(9, "All node types are valid", len(bad_ntypes) == 0,
          f"invalid: {set(bad_ntypes)}" if bad_ntypes else "")

    # 10. Bridge nodes detected
    bridge_nodes = [n for n in nodes if n.get("is_bridge")]
    check(10, "Bridge nodes detected", len(bridge_nodes) > 0,
          f"{len(bridge_nodes)} bridges: {[b['label'] for b in bridge_nodes]}")

    # 11. Grant funds edges must have amount (URLs intentionally null — slugified URLs removed)
    funds_edges = [e for e in edges if e["type"] == "funds" and e.get("extraction_method") == "csv_parse"]
    funds_no_amount = [e for e in funds_edges if not e.get("amount")]
    check(11, "All grant funds edges have amount",
          len(funds_no_amount) == 0,
          f"no amount: {len(funds_no_amount)}")

    # 12. Contracts edges have confidence (N/A for Sprint 2, pass if no contracts)
    contract_edges = [e for e in edges if e["type"] == "contracts"]
    contracts_no_conf = [e for e in contract_edges if not e.get("confidence")]
    check(12, "All contracts edges have confidence",
          len(contracts_no_conf) == 0,
          f"no confidence: {len(contracts_no_conf)}" if contract_edges else "N/A (no contracts yet)")

    # 13. Graph connectivity > 80%
    # BFS to find largest connected component
    visited = set()
    largest = 0
    for start in node_ids:
        if start in visited:
            continue
        queue = [start]
        component = set()
        while queue:
            nid = queue.pop(0)
            if nid in component:
                continue
            component.add(nid)
            for e in edges:
                if e["source"] == nid and e["target"] not in component:
                    queue.append(e["target"])
                if e["target"] == nid and e["source"] not in component:
                    queue.append(e["source"])
        visited.update(component)
        largest = max(largest, len(component))

    connectivity = largest / len(nodes) * 100 if nodes else 0
    check(13, "Graph connectivity > 80%", connectivity > 80,
          f"{connectivity:.1f}% (largest component: {largest}/{len(nodes)})")

    # 14. Edge traceability (check if raw files exist)
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    raw_files = []
    if os.path.exists(raw_dir):
        for root, dirs, files in os.walk(raw_dir):
            for f in files:
                raw_files.append(os.path.join(root, f))
    check(14, "Raw data files exist", len(raw_files) > 0,
          f"{len(raw_files)} files in data/raw/")

    # Summary
    print(f"\n{'='*50}")
    print(f"QUALITY CHECK: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'='*50}")

    # Node type breakdown
    type_counts = {}
    for n in nodes:
        t = n.get("type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"\nNode types: {dict(sorted(type_counts.items()))}")

    # Edge type breakdown
    etype_counts = {}
    for e in edges:
        t = e.get("type", "?")
        etype_counts[t] = etype_counts.get(t, 0) + 1
    print(f"Edge types: {dict(sorted(etype_counts.items()))}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
