#!/usr/bin/env python3
"""
Sprint 2: Merge Coefficient (prev. Open Philanthropy) funding layer into graph_data.json.
Reads data/staged/op_edges.json + data/graph_data.json
Writes updated data/graph_data.json, data/nodes.csv, data/edges.csv

Key logic:
- Funder and program nodes are NEW (added fresh)
- Org nodes are BRIDGED to existing Sprint 1 institution nodes where possible
- New org nodes are created only for orgs not already in the graph
- All funds edges are added
- Degree counts updated for all nodes
"""

import csv
import json
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGED_IN = os.path.join(BASE_DIR, "data", "staged", "op_edges.json")
GRAPH_FILE = os.path.join(BASE_DIR, "data", "graph_data.json")
NODES_CSV = os.path.join(BASE_DIR, "data", "nodes.csv")
EDGES_CSV = os.path.join(BASE_DIR, "data", "edges.csv")

# Mapping from Sprint 2/3 org node IDs → Sprint 1 institution node IDs
# These are the BRIDGE NODES: orgs that appear in both Sprint 1 (workshop) and Sprint 2/3 (funding)
BRIDGE_MAP = {
    # ── Sprint 2 original bridges ──────────────────────────────────────────
    'org_securebio':                                        'inst_SecureBio',
    'org_center_for_ai_safety':                            'inst_Center_for_AI_Safety',
    'org_johns_hopkins_university':                        'inst_Johns_Hopkins_University',
    'org_massachusetts_institute_of_technology':           'inst_Massachusetts_Institute_of_Technology',
    'org_rand_corporation':                                'inst_RAND_Corporation',
    # Johns Hopkins CHS → JHU (specific center within same institution)
    'org_johns_hopkins_center_for_health_security':        'inst_Johns_Hopkins_University',

    # ── Sprint 3 new bridges — universities & institutes ───────────────────
    'org_harvard_university':                              'inst_Harvard_University',
    'org_stanford_university':                             'inst_Stanford_University',
    'org_columbia_university':                             'inst_Columbia_University',
    'org_yale_university':                                 'inst_Yale_University',
    'org_rutgers_university':                              'inst_Rutgers_University',
    'org_imperial_college_london':                         'inst_Imperial_College_London',
    'org_broad_institute':                                 'inst_Broad_Institute',
    'org_university_of_michigan':                          'inst_University_of_Michigan',
    'org_icahn_school_of_medicine_at_mount_sinai':         'inst_Icahn_School_of_Medicine_at_Mount_Sinai',
    'org_university_of_oxford':                            'inst_University_of_Oxford',
    'org_university_of_chicago':                           'inst_University_of_Chicago',
    'org_university_of_georgia':                           'inst_University_of_Georgia',
    # UMD grants go to main College Park campus
    'org_university_of_maryland':                          'inst_University_of_Maryland__College_Park',
    'org_georgia_institute_of_technology':                 'inst_Georgia_Institute_of_Technology',
    'org_university_of_washington':                        'inst_University_of_Washington',
    # UW IPD is housed within University of Washington
    'org_university_of_washington_institute_for_protein_design': 'inst_University_of_Washington',
    # MIT sub-groups — route to parent institution node
    'org_mit_synthetic_neurobiology_group':                'inst_Massachusetts_Institute_of_Technology',
    'org_massachusetts_institute_of_technology_media_lab': 'inst_Massachusetts_Institute_of_Technology',
}

# New orgs not in Sprint 1 (will be added as new nodes)
# Examples: org_nuclear_threat_initiative, org_gryphon_scientific, org_bluedot_impact, etc.

# Org subtypes for new orgs
ORG_SUBTYPES = {
    'org_georgetown_cset': 'think_tank',
    'org_georgetown_university': 'research_institute',
    'org_nuclear_threat_initiative': 'think_tank',
    'org_gryphon_scientific': 'company',
}

ORG_URLS = {
    'org_georgetown_cset': 'https://cset.georgetown.edu/',
    'org_georgetown_university': 'https://www.georgetown.edu/',
    'org_nuclear_threat_initiative': 'https://www.nti.org/',
    'org_gryphon_scientific': 'https://www.gryphonscientific.com/',
}


def main():
    print("Loading graph...")
    with open(GRAPH_FILE) as f:
        graph = json.load(f)

    print("Loading staged Sprint 2 data...")
    with open(STAGED_IN) as f:
        staged = json.load(f)

    existing_nodes = {n['id']: n for n in graph['nodes']}
    # Sprint 1 edges may not have 'id' — generate deterministic IDs
    for i, e in enumerate(graph['edges']):
        if 'id' not in e:
            e['id'] = f"{e['type']}_{e['source']}_{e['target']}"
    existing_edges = {e['id']: e for e in graph['edges']}

    s2_nodes = {n['id']: n for n in staged['nodes']}
    s2_edges = staged['edges']

    added_nodes = 0
    added_edges = 0
    bridged_nodes = 0

    # 1. Add funder node (always new)
    funder = s2_nodes.get('funder_coefficient')
    if funder and funder['id'] not in existing_nodes:
        existing_nodes[funder['id']] = funder
        added_nodes += 1
        print(f"  + Funder: {funder['label']}")

    # 2. Add program nodes (always new)
    for nid, node in s2_nodes.items():
        if node['type'] == 'program' and nid not in existing_nodes:
            existing_nodes[nid] = node
            added_nodes += 1
            print(f"  + Program: {node['label']}")

    # 3. Handle org nodes (bridge or create new)
    for nid, node in s2_nodes.items():
        if node['type'] != 'org':
            continue

        if nid in BRIDGE_MAP:
            # This org already exists in Sprint 1 — bridge it
            s1_id = BRIDGE_MAP[nid]
            if s1_id in existing_nodes:
                # Mark existing node as bridge
                existing_nodes[s1_id]['is_bridge'] = True
                existing_nodes[s1_id]['bridge_from'] = existing_nodes[s1_id].get('bridge_from', [])
                if 'sprint2_funding' not in existing_nodes[s1_id]['bridge_from']:
                    existing_nodes[s1_id]['bridge_from'].append('sprint2_funding')
                bridged_nodes += 1
                print(f"  ↔ Bridge: {node['label']} → {existing_nodes[s1_id]['label']} ({s1_id})")
            else:
                # Sprint 1 node somehow missing — add as new
                node['id'] = nid
                if nid in ORG_SUBTYPES:
                    node['org_subtype'] = ORG_SUBTYPES[nid]
                if nid in ORG_URLS:
                    node['url'] = ORG_URLS[nid]
                existing_nodes[nid] = node
                added_nodes += 1
                print(f"  + New (bridge target missing): {node['label']}")
        else:
            # New org — add it
            if nid in ORG_SUBTYPES:
                node['org_subtype'] = ORG_SUBTYPES[nid]
            if nid in ORG_URLS:
                node['url'] = ORG_URLS[nid]
            if nid not in existing_nodes:
                existing_nodes[nid] = node
                added_nodes += 1
                print(f"  + New org: {node['label']}")

    # 4. Add all edges, remapping bridge node targets
    for e in s2_edges:
        # Remap source and target through bridge map
        if e['source'] in BRIDGE_MAP and BRIDGE_MAP[e['source']] in existing_nodes:
            e['source'] = BRIDGE_MAP[e['source']]
        if e['target'] in BRIDGE_MAP and BRIDGE_MAP[e['target']] in existing_nodes:
            e['target'] = BRIDGE_MAP[e['target']]

        # Verify both endpoints exist
        if e['source'] not in existing_nodes:
            print(f"  ! Skipping edge {e['id']}: source {e['source']} not found")
            continue
        if e['target'] not in existing_nodes:
            print(f"  ! Skipping edge {e['id']}: target {e['target']} not found")
            continue

        if e['id'] not in existing_edges:
            existing_edges[e['id']] = e
            added_edges += 1

    # 5. Recompute degrees
    degree = {}
    for e in existing_edges.values():
        degree[e['source']] = degree.get(e['source'], 0) + 1
        degree[e['target']] = degree.get(e['target'], 0) + 1
    for nid, node in existing_nodes.items():
        node['degree'] = degree.get(nid, 0)

    # 6. Rebuild graph
    graph['nodes'] = list(existing_nodes.values())
    graph['edges'] = list(existing_edges.values())
    graph['sprint2_merged_at'] = datetime.now().isoformat()

    # 7. Write updated graph
    with open(GRAPH_FILE, 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"\nUpdated {GRAPH_FILE}")

    # 8. Write updated CSVs
    # Nodes CSV
    node_fields = ['id', 'type', 'label', 'degree', 'url', 'is_bridge', 'org_subtype']
    with open(NODES_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=node_fields, extrasaction='ignore')
        writer.writeheader()
        for n in sorted(graph['nodes'], key=lambda x: x.get('degree', 0), reverse=True):
            writer.writerow(n)
    print(f"Updated {NODES_CSV}")

    # Edges CSV
    edge_fields = ['id', 'source', 'target', 'type', 'amount', 'amount_note', 'date_range',
                   'url', 'confidence', 'needs_human_review', 'matched_text']
    with open(EDGES_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=edge_fields, extrasaction='ignore')
        writer.writeheader()
        for e in graph['edges']:
            writer.writerow(e)
    print(f"Updated {EDGES_CSV}")

    # 9. Summary
    print(f"\n{'='*60}")
    print(f"MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"  Added nodes: {added_nodes}")
    print(f"  Bridged nodes: {bridged_nodes}")
    print(f"  Added edges: {added_edges}")
    print(f"  Total nodes: {len(graph['nodes'])}")
    print(f"  Total edges: {len(graph['edges'])}")

    # Node type breakdown
    type_counts = {}
    for n in graph['nodes']:
        t = n.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"\n  Node types:")
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    # Edge type breakdown
    etype_counts = {}
    for e in graph['edges']:
        t = e.get('type', 'unknown')
        etype_counts[t] = etype_counts.get(t, 0) + 1
    print(f"\n  Edge types:")
    for t, c in sorted(etype_counts.items()):
        print(f"    {t}: {c}")

    # Bridge node summary
    bridges = [n for n in graph['nodes'] if n.get('is_bridge')]
    if bridges:
        print(f"\n  Bridge nodes ({len(bridges)}):")
        for b in bridges:
            print(f"    {b['label']} (degree={b['degree']})")


if __name__ == "__main__":
    main()
