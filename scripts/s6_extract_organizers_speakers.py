#!/usr/bin/env python3
"""Sprint 6: Workshop Organizers & Invited Speakers.

Source: https://biosafe-gen-ai.github.io
Raw data: data/raw/s6_organizers_speakers/workshop_organizers_speakers.md

This script:
  1. Creates a workshop event node (anchor for organizer/speaker edges)
  2. Creates new author nodes for organizers/speakers not in graph
  3. Creates new institution/org nodes for new affiliations
  4. Creates organized / invited_speaker edges to workshop
  5. Creates current_affiliation edges for new authors
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')
STAGED_DIR = os.path.join(BASE_DIR, 'data', 'staged')
os.makedirs(STAGED_DIR, exist_ok=True)

with open(GRAPH_FILE) as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']
existing_ids = {n['id'] for n in nodes}
existing_edge_ids = {e['id'] for e in edges}
node_by_id = {n['id']: n for n in nodes}

new_nodes = []
new_edges = []

SOURCE_URL = 'https://biosafe-gen-ai.github.io'

# ── Helper ────────────────────────────────────────────────────────────────────

def add_node(nid, label, ntype, **kwargs):
    if nid not in existing_ids:
        node = {'id': nid, 'label': label, 'type': ntype, 'data_source': SOURCE_URL}
        node.update(kwargs)
        new_nodes.append(node)
        existing_ids.add(nid)
        print(f"+ NODE: {nid} ({label})")
        return True
    else:
        print(f"  SKIP: {nid} already exists")
        return False

def add_edge(eid, source, target, etype, **kwargs):
    if eid not in existing_edge_ids:
        edge = {'id': eid, 'source': source, 'target': target, 'type': etype,
                'data_source': SOURCE_URL, 'confidence': 'HIGH'}
        edge.update(kwargs)
        new_edges.append(edge)
        existing_edge_ids.add(eid)
        src_label = node_by_id.get(source, {}).get('label', source)
        tgt_label = node_by_id.get(target, {}).get('label', target)
        print(f"+ EDGE: {src_label} → {tgt_label} ({etype})")
        return True
    else:
        print(f"  SKIP: edge {eid} already exists")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# 1. WORKSHOP EVENT NODE
# ══════════════════════════════════════════════════════════════════════════════

WORKSHOP_ID = 'event_neurips_biosafe_genai_2025'
add_node(WORKSHOP_ID, 'NeurIPS 2025 BioSafe GenAI Workshop',
         'presentation', subtype='workshop',
         url=SOURCE_URL,
         description='Workshop on Biosecurity Safeguards for Generative AI at NeurIPS 2025')

# ══════════════════════════════════════════════════════════════════════════════
# 2. NEW INSTITUTION / ORG NODES
# ══════════════════════════════════════════════════════════════════════════════

# Institutions that don't exist yet
NEW_INSTITUTIONS = {
    'inst_University_of_Central_Florida': {
        'label': 'University of Central Florida',
        'type': 'institution',
    },
    'inst_Shanghai_Jiao_Tong_University': {
        'label': 'Shanghai Jiao Tong University',
        'type': 'institution',
    },
    'inst_Universite_de_Montreal': {
        'label': 'Université de Montréal',
        'type': 'institution',
    },
    'inst_MBZUAI': {
        'label': 'MBZUAI',
        'type': 'institution',
        'description': 'Mohamed bin Zayed University of Artificial Intelligence',
    },
}

NEW_ORGS = {
    'org_mila': {
        'label': 'Mila',
        'type': 'org',
        'description': 'Quebec AI Institute',
        'url': 'https://mila.quebec',
    },
    'org_chan_zuckerberg_initiative': {
        'label': 'Chan Zuckerberg Initiative',
        'type': 'org',
        'url': 'https://chanzuckerberg.com',
    },
    'org_iris_medicine': {
        'label': 'Iris Medicine',
        'type': 'org',
    },
    'org_kelonia_therapeutics': {
        'label': 'Kelonia Therapeutics',
        'type': 'org',
    },
    'org_nist': {
        'label': 'NIST',
        'type': 'org',
        'description': 'National Institute of Standards and Technology',
        'url': 'https://www.nist.gov',
    },
    'org_nebius': {
        'label': 'Nebius',
        'type': 'org',
        'url': 'https://nebius.com',
    },
    'org_petuum': {
        'label': 'Petuum Inc.',
        'type': 'org',
    },
}

for nid, data in {**NEW_INSTITUTIONS, **NEW_ORGS}.items():
    add_node(nid, data['label'], data['type'],
             **{k: v for k, v in data.items() if k not in ('label', 'type')})

# ══════════════════════════════════════════════════════════════════════════════
# 3. ORGANIZER AUTHOR NODES + EDGES
# ══════════════════════════════════════════════════════════════════════════════

# Organizers: existing author ID or new ID, affiliation ID
ORGANIZERS = [
    # (author_id, label, affiliation_id, is_new)
    ('author_Mengdi_Wang1', 'Mengdi Wang', 'inst_Princeton_University', False),
    ('author_Le_Cong2', 'Le Cong', 'inst_Stanford_University', False),
    ('author_amrit_singh_bedi', 'Amrit Singh Bedi', 'inst_University_of_Central_Florida', True),
    ('author_alvaro_velasquez', 'Alvaro Velasquez', 'org_university_of_colorado', True),
    ('author_ZAIXI_ZHANG2', 'Zaixi Zhang', 'inst_Princeton_University', False),
    ('author_Ruofan_Jin1', 'Ruofan Jin', 'inst_Princeton_University', False),
    ('author_souradip_chakraborty', 'Souradip Chakraborty', 'inst_University_of_Maryland__College_Park', True),
]

STUDENT_ORGANIZERS = [
    ('author_Jigang_Fan2', 'Jigang Fan', 'inst_Peking_University', False),
    ('author_Zhenghong_Zhou2', 'Zhenghong Zhou', 'inst_Shanghai_Jiao_Tong_University', False),
    ('author_avinash_reddy', 'Avinash Reddy', 'inst_University_of_Central_Florida', True),
]

print("\n--- ORGANIZERS ---")
for auth_id, label, aff_id, is_new in ORGANIZERS + STUDENT_ORGANIZERS:
    if is_new:
        add_node(auth_id, label, 'author')
        # Update node_by_id for edge label lookups
        node_by_id[auth_id] = {'id': auth_id, 'label': label, 'type': 'author'}

    # organized edge
    add_edge(f'org_{auth_id}_{WORKSHOP_ID}', auth_id, WORKSHOP_ID, 'organized',
             extraction_method='workshop_website')

    # affiliation edge (only if new author — existing ones already have affiliations)
    if is_new and aff_id in existing_ids:
        add_edge(f'aff_{auth_id}_{aff_id}', auth_id, aff_id, 'current_affiliation',
                 extraction_method='workshop_website')

# ══════════════════════════════════════════════════════════════════════════════
# 4. INVITED SPEAKER AUTHOR NODES + EDGES
# ══════════════════════════════════════════════════════════════════════════════

# Speakers: (author_id, label, primary_affiliation_id, additional_affiliations, is_new)
SPEAKERS = [
    ('author_yoshua_bengio', 'Yoshua Bengio', 'org_mila', ['inst_Universite_de_Montreal'], True),
    ('author_Peter_Henderson1', 'Peter Henderson', 'inst_Princeton_University', [], False),
    ('author_jian_ma', 'Jian Ma', 'inst_Carnegie_Mellon_University', [], True),
    ('author_russ_altman', 'Russ Altman', 'inst_Stanford_University', [], True),
    ('author_eric_xing', 'Eric Xing', 'inst_Carnegie_Mellon_University', ['inst_MBZUAI', 'org_petuum'], True),
    ('author_theofanis_karaletsos', 'Theofanis Karaletsos', 'org_chan_zuckerberg_initiative', [], True),
    ('author_megan_blewett', 'Megan Blewett', 'org_iris_medicine', ['org_kelonia_therapeutics'], True),
    ('author_sheng_lin_gibson', 'Sheng Lin-Gibson', 'org_nist', [], True),
    # Le Cong is already an organizer (author_Le_Cong2) — just add speaker edge
    ('author_Le_Cong2', 'Le Cong', 'inst_Stanford_University', [], False),
    ('author_artem_elmuratov', 'Artem Elmuratov', 'org_nebius', [], True),
]

print("\n--- INVITED SPEAKERS ---")
for auth_id, label, primary_aff, extra_affs, is_new in SPEAKERS:
    if is_new:
        add_node(auth_id, label, 'author')
        node_by_id[auth_id] = {'id': auth_id, 'label': label, 'type': 'author'}

    # invited_speaker edge
    add_edge(f'spk_{auth_id}_{WORKSHOP_ID}', auth_id, WORKSHOP_ID, 'invited_speaker',
             extraction_method='workshop_website')

    # affiliation edges (only for new authors)
    if is_new:
        if primary_aff in existing_ids:
            add_edge(f'aff_{auth_id}_{primary_aff}', auth_id, primary_aff, 'current_affiliation',
                     extraction_method='workshop_website')
        for extra in extra_affs:
            if extra in existing_ids:
                add_edge(f'aff_{auth_id}_{extra}', auth_id, extra, 'current_affiliation',
                         extraction_method='workshop_website')

# ══════════════════════════════════════════════════════════════════════════════
# 5. ADDITIONAL EDGES — Mila part_of Université de Montréal
# ══════════════════════════════════════════════════════════════════════════════

print("\n--- ORG RELATIONSHIPS ---")
add_edge('partof_mila_udem', 'org_mila', 'inst_Universite_de_Montreal', 'part_of',
         extraction_method='general_knowledge')

# NIST → US AISI hierarchy (AISI is part of NIST)
add_edge('partof_us_aisi_nist', 'org_us_aisi', 'org_nist', 'part_of',
         extraction_method='general_knowledge')

# ══════════════════════════════════════════════════════════════════════════════
# MERGE
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n=== SPRINT 6 SUMMARY ===")
print(f"New nodes: {len(new_nodes)}")
print(f"New edges: {len(new_edges)}")

# Save staged files
with open(os.path.join(STAGED_DIR, 's6_nodes.json'), 'w') as f:
    json.dump(new_nodes, f, indent=2)
with open(os.path.join(STAGED_DIR, 's6_edges.json'), 'w') as f:
    json.dump(new_edges, f, indent=2)

nodes.extend(new_nodes)
edges.extend(new_edges)
graph['nodes'] = nodes
graph['edges'] = edges

with open(GRAPH_FILE, 'w') as f:
    json.dump(graph, f, indent=2)

print(f"\nMerged into graph: {len(nodes)} nodes, {len(edges)} edges")
