#!/usr/bin/env python3
"""Sprint 4b: Fix missing DARPA program nodes and PI→program connections.

Gap identified during Sprint 5 dry run:
  - 4 DARPA programs (SAFE GENES, P3, PREEMPT, PREPARE) have PIs in graph
    but NO program nodes exist
  - 13 PI author nodes have current_affiliation only, no program connection
  - Kevin Esvelt (author_Kevin_M__Esvelt1) is a SAFE GENES PI but only
    connected to workshop paper + MIT affiliation

This script:
  1. Creates 4 program nodes
  2. Creates DARPA → program hierarchy edges
  3. Creates PI → program (performs_on) edges
  4. Creates program → institution (funds) edges for performer institutions
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')

with open(GRAPH_FILE) as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']
existing_ids = {n['id'] for n in nodes}
existing_edge_ids = {e['id'] for e in edges}
node_by_id = {n['id']: n for n in nodes}

new_nodes = []
new_edges = []

# ── Program definitions ──────────────────────────────────────────────────────

PROGRAMS = {
    'program_darpa_safe_genes': {
        'label': 'DARPA SAFE GENES',
        'full_name': 'Safe Genes',
        'url': 'https://www.darpa.mil/research/programs/safe-genes',
        'description': 'Gene editing safety tools — $65M over 4 years (2017–2021)',
        'source_url': 'https://www.darpa.mil/news-events/2017-07-19',
    },
    'program_darpa_p3': {
        'label': 'DARPA P3',
        'full_name': 'Pandemic Prevention Platform',
        'url': 'https://www.darpa.mil/research/programs/pandemic-prevention-platform',
        'description': 'Rapid antibody countermeasures — 60-day pandemic response (2018–2022)',
        'source_url': 'https://www.darpa.mil/news/2018/halt-outbreaks',
    },
    'program_darpa_preempt': {
        'label': 'DARPA PREEMPT',
        'full_name': 'PREventing EMerging Pathogenic Threats',
        'url': 'https://www.darpa.mil/research/programs/preventing-emerging-pathogenic-threats',
        'description': 'Zoonotic reservoir containment — 3.5 years (2019–2022)',
        'source_url': 'https://www.darpa.mil/news/2019/medical-preparedness',
    },
    'program_darpa_prepare': {
        'label': 'DARPA PREPARE',
        'full_name': 'PReemptive Expression of Protective Alleles and Response Elements',
        'url': 'https://www.darpa.mil/research/programs/preemptive-expression-protective-alleles-response-elements',
        'description': 'Gene-encoded broad-spectrum protection (2019–2023)',
        'source_url': 'https://www.darpa.mil/news/2019/dose-inner-strength',
    },
}

# ── PI → program mapping ─────────────────────────────────────────────────────
# Maps existing PI node IDs to their program node ID

PI_PROGRAM_MAP = {
    # SAFE GENES PIs
    'author_amit_choudhary': 'program_darpa_safe_genes',
    'author_george_church': 'program_darpa_safe_genes',
    'author_keith_joung': 'program_darpa_safe_genes',
    'author_Kevin_M__Esvelt1': 'program_darpa_safe_genes',  # Existing workshop author
    'author_john_godwin': 'program_darpa_safe_genes',
    'author_jennifer_doudna': 'program_darpa_safe_genes',
    'author_omar_akbari': 'program_darpa_safe_genes',
    # PREEMPT PIs
    'author_ariel_weinberger': 'program_darpa_preempt',
    'author_peter_barry': 'program_darpa_preempt',
    'author_carla_saleh': 'program_darpa_preempt',
    'author_raina_plowright': 'program_darpa_preempt',
    'author_luke_alphey': 'program_darpa_preempt',
    # PREPARE PIs
    'author_harris_wang': 'program_darpa_prepare',
    'author_jonathan_weissman': 'program_darpa_prepare',
}

# ── Performer institution → program mapping ──────────────────────────────────
# Maps existing institution node IDs to program node IDs (for funds edges)

PERFORMER_INSTITUTION_MAP = {
    # SAFE GENES performers
    'program_darpa_safe_genes': [
        'inst_Broad_Institute',
        'inst_Harvard_University',
        'inst_Massachusetts_Institute_of_Technology',
    ],
    # P3 performers
    'program_darpa_p3': [
        'org_duke_university',
    ],
    # PREEMPT performers
    'program_darpa_preempt': [
        'inst_Johns_Hopkins_University',  # Montana State sub-team
    ],
    # PREPARE performers
    'program_darpa_prepare': [
        'inst_Columbia_University',
        'org_university_of_california_san_francisco',
        'inst_Georgia_Institute_of_Technology',
    ],
}

# ── Create program nodes ─────────────────────────────────────────────────────

for prog_id, prog_data in PROGRAMS.items():
    if prog_id not in existing_ids:
        node = {
            'id': prog_id,
            'label': prog_data['label'],
            'type': 'program',
            'full_name': prog_data['full_name'],
            'url': prog_data['url'],
            'description': prog_data['description'],
            'data_source': prog_data['source_url'],
        }
        new_nodes.append(node)
        print(f"+ NODE: {prog_id} ({prog_data['label']})")
    else:
        print(f"  SKIP: {prog_id} already exists")

# ── Create DARPA → program hierarchy edges ───────────────────────────────────

DARPA_FUNDER_ID = 'funder_darpa'
assert DARPA_FUNDER_ID in existing_ids, "DARPA funder node not found!"

for prog_id in PROGRAMS:
    edge_id = f"hier_darpa_{prog_id.replace('program_darpa_', '')}"
    if edge_id not in existing_edge_ids:
        edge = {
            'id': edge_id,
            'source': DARPA_FUNDER_ID,
            'target': prog_id,
            'type': 'funds',
            'extraction_method': 'news_release',
            'data_source': PROGRAMS[prog_id]['source_url'],
            'confidence': 'HIGH',
        }
        new_edges.append(edge)
        print(f"+ EDGE: DARPA → {PROGRAMS[prog_id]['label']}")

# ── Create PI → program edges ────────────────────────────────────────────────

for pi_id, prog_id in PI_PROGRAM_MAP.items():
    if pi_id not in existing_ids:
        print(f"  WARN: PI node {pi_id} not found in graph, skipping")
        continue
    edge_id = f"performs_{pi_id}_{prog_id.replace('program_darpa_', '')}"
    if edge_id not in existing_edge_ids:
        edge = {
            'id': edge_id,
            'source': pi_id,
            'target': prog_id,
            'type': 'performs_on',
            'extraction_method': 'news_release',
            'data_source': PROGRAMS[prog_id].get('source_url', ''),
            'confidence': 'HIGH',
        }
        new_edges.append(edge)
        pi_label = node_by_id[pi_id]['label']
        print(f"+ EDGE: {pi_label} → {PROGRAMS[prog_id]['label']} (performs_on)")

# ── Create program → institution (funds) edges ──────────────────────────────

for prog_id, inst_ids in PERFORMER_INSTITUTION_MAP.items():
    for inst_id in inst_ids:
        if inst_id not in existing_ids:
            print(f"  WARN: Institution {inst_id} not found, skipping")
            continue
        edge_id = f"perf_{prog_id.replace('program_darpa_', '')}_{inst_id}"
        if edge_id not in existing_edge_ids:
            inst_label = node_by_id[inst_id]['label']
            edge = {
                'id': edge_id,
                'source': prog_id,
                'target': inst_id,
                'type': 'funds',
                'extraction_method': 'news_release',
                'data_source': PROGRAMS[prog_id].get('source_url', ''),
                'confidence': 'HIGH',
            }
            new_edges.append(edge)
            print(f"+ EDGE: {PROGRAMS[prog_id]['label']} → {inst_label} (funds)")

# ── Merge ────────────────────────────────────────────────────────────────────

print(f"\n=== SPRINT 4b SUMMARY ===")
print(f"New nodes: {len(new_nodes)}")
print(f"New edges: {len(new_edges)}")

nodes.extend(new_nodes)
edges.extend(new_edges)

graph['nodes'] = nodes
graph['edges'] = edges

with open(GRAPH_FILE, 'w') as f:
    json.dump(graph, f, indent=2)

print(f"\nMerged into graph: {len(nodes)} nodes, {len(edges)} edges")
