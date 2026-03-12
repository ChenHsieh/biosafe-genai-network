#!/usr/bin/env python3
"""Sprint 8: Key Personnel Research Projects & Lab Outputs.

Sources:
  - Semantic Scholar API (publications)
  - NIH RePORTER API (grants)

Adds:
  - Publication nodes for key bio+AI papers (top papers per PI, deduplicated)
  - NIH funder node + grant program nodes
  - has_grant edges (PI → grant)
  - published edges (PI → publication)
  - funds edges (NIH → grants, grants → institutions)
"""

import json, os, re, hashlib
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')
STAGED_DIR = os.path.join(BASE_DIR, 'data', 'staged')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 's8_key_personnel')
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

def add_node(nid, label, ntype, **kwargs):
    if nid not in existing_ids:
        node = {'id': nid, 'label': label, 'type': ntype}
        node.update(kwargs)
        new_nodes.append(node)
        existing_ids.add(nid)
        node_by_id[nid] = node
        return True
    return False

def add_edge(eid, source, target, etype, **kwargs):
    if eid not in existing_edge_ids and source in existing_ids and target in existing_ids:
        edge = {'id': eid, 'source': source, 'target': target, 'type': etype}
        edge.update(kwargs)
        new_edges.append(edge)
        existing_edge_ids.add(eid)
        return True
    return False

def clean_id(s):
    return re.sub(r'[^a-zA-Z0-9_]', '_', s.replace(' ', '_'))[:60]

# ══════════════════════════════════════════════════════════════════════════════
# MAP EXISTING AUTHOR IDS
# ══════════════════════════════════════════════════════════════════════════════

AUTHOR_MAP = {
    'Kevin M. Esvelt': 'author_Kevin_M__Esvelt1',
    'George Church': 'author_george_church',
    'Jennifer Doudna': 'author_jennifer_doudna',
    'Harris Wang': 'author_harris_wang',
    'Le Cong': 'author_Le_Cong2',
    'Yoshua Bengio': 'author_yoshua_bengio',
    'Eugene Shakhnovich': 'author_Eugene_Shakhnovich1',
    'Jonathan Weissman': 'author_jonathan_weissman',
    'Peter Henderson': 'author_Peter_Henderson1',
    'Eric Xing': 'author_eric_xing',
}

# Verify all exist
for name, aid in AUTHOR_MAP.items():
    assert aid in existing_ids, f"{name} ({aid}) not in graph!"

# ══════════════════════════════════════════════════════════════════════════════
# 1. NIH FUNDER NODE
# ══════════════════════════════════════════════════════════════════════════════

NIH_ID = 'funder_nih'
add_node(NIH_ID, 'National Institutes of Health (NIH)', 'funder',
         url='https://www.nih.gov',
         data_source='https://api.reporter.nih.gov')

# ══════════════════════════════════════════════════════════════════════════════
# 2. NIH GRANTS → PROGRAM NODES + EDGES
# ══════════════════════════════════════════════════════════════════════════════

with open(os.path.join(RAW_DIR, 'nih_reporter_results.json')) as f:
    nih_results = json.load(f)

print("=== NIH GRANTS ===")

# Deduplicate grants by project number (same grant appears in multiple fiscal years)
seen_projects = {}
for name, data in nih_results.items():
    for grant in data.get('relevant_grants', []):
        proj_num = grant.get('project_num', '')
        if not proj_num:
            continue
        # Keep the most recent fiscal year version
        if proj_num not in seen_projects or (grant.get('fiscal_year', 0) > seen_projects[proj_num].get('fiscal_year', 0)):
            seen_projects[proj_num] = grant
            seen_projects[proj_num]['_pi_name'] = name

# Aggregate total funding per project across all fiscal years
project_totals = {}
for name, data in nih_results.items():
    for grant in data.get('relevant_grants', []):
        proj_num = grant.get('project_num', '')
        if proj_num:
            project_totals.setdefault(proj_num, 0)
            project_totals[proj_num] += grant.get('award_amount', 0) or 0

print(f"Unique projects: {len(seen_projects)}")

# Institution name → existing node ID mapping
INST_MAP = {
    'MASSACHUSETTS INSTITUTE OF TECHNOLOGY': 'inst_Massachusetts_Institute_of_Technology',
    'UNIVERSITY OF CALIFORNIA BERKELEY': 'inst_University_of_California__Berkeley',
    'UNIVERSITY OF CALIFORNIA, SAN FRANCISCO': 'inst_University_of_California__San_Francisco',
    'COLUMBIA UNIVERSITY HEALTH SCIENCES': 'inst_Columbia_University',
    'STANFORD UNIVERSITY': 'inst_Stanford_University',
    'HARVARD UNIVERSITY': 'inst_Harvard_University',
    'J. DAVID GLADSTONE INSTITUTES': None,
    'WHITEHEAD INSTITUTE FOR BIOMEDICAL RES': None,
}

# Create new institutions we need
NEW_INSTS = {
    'inst_gladstone_institutes': {
        'label': 'Gladstone Institutes',
        'type': 'institution',
        'url': 'https://gladstone.org',
    },
    'inst_whitehead_institute': {
        'label': 'Whitehead Institute',
        'type': 'institution',
        'url': 'https://wi.mit.edu',
    },
}
for nid, data in NEW_INSTS.items():
    add_node(nid, data['label'], data['type'], **{k: v for k, v in data.items() if k not in ('label', 'type')})

INST_MAP['J. DAVID GLADSTONE INSTITUTES'] = 'inst_gladstone_institutes'
INST_MAP['WHITEHEAD INSTITUTE FOR BIOMEDICAL RES'] = 'inst_whitehead_institute'

for proj_num, grant in seen_projects.items():
    pi_name = grant['_pi_name']
    pi_id = AUTHOR_MAP.get(pi_name)
    if not pi_id:
        continue

    title = grant.get('project_title', 'Unknown Project')
    total_amount = project_totals.get(proj_num, 0)
    org_name = grant.get('organization', {}).get('org_name', '')
    inst_id = INST_MAP.get(org_name)

    # Create grant/program node
    grant_id = f'grant_nih_{clean_id(proj_num)}'
    add_node(grant_id, title.strip(), 'program',
             subtype='nih_grant',
             data_source='https://api.reporter.nih.gov',
             description=f'NIH {proj_num} | {org_name}',
             details={'NIH RePORTER': f'https://reporter.nih.gov/project-details/{proj_num.replace(" ", "")}'})

    print(f"  + GRANT: {title[:60]} (${total_amount:,.0f})")

    # NIH → grant funds edge
    add_edge(f'funds_nih_{clean_id(proj_num)}', NIH_ID, grant_id, 'funds',
             amount=total_amount,
             data_source='https://api.reporter.nih.gov',
             confidence='HIGH')

    # PI → grant performs_on edge
    add_edge(f'performs_{pi_id}_{grant_id}', pi_id, grant_id, 'performs_on',
             data_source='https://api.reporter.nih.gov',
             confidence='HIGH')

    # grant → institution funds edge
    if inst_id and inst_id in existing_ids:
        add_edge(f'funds_{grant_id}_{inst_id}', grant_id, inst_id, 'funds',
                 amount=total_amount,
                 data_source='https://api.reporter.nih.gov',
                 confidence='HIGH')

# ══════════════════════════════════════════════════════════════════════════════
# 3. KEY PUBLICATIONS → PUBLICATION NODES + EDGES
# ══════════════════════════════════════════════════════════════════════════════

with open(os.path.join(RAW_DIR, 'semantic_scholar_results.json')) as f:
    s2_results = json.load(f)

print("\n=== KEY PUBLICATIONS ===")

# Select top papers per PI (max 3 per person, highest citation count)
seen_paper_titles = set()

for name, data in s2_results.items():
    pi_id = AUTHOR_MAP.get(name)
    if not pi_id:
        continue

    papers = data.get('s2_papers', [])
    if not papers:
        continue

    # Sort by citations, take top 3
    papers.sort(key=lambda p: -(p.get('citationCount', 0) or 0))
    top_papers = papers[:3]

    for paper in top_papers:
        title = paper.get('title', '')
        if not title or title.lower() in seen_paper_titles:
            continue
        seen_paper_titles.add(title.lower())

        year = paper.get('year', '')
        cites = paper.get('citationCount', 0)
        venue = paper.get('venue', '')

        # Create publication node
        s2_id = paper.get('paperId', '')
        pub_id = f'pub_s2_{clean_id(title[:40])}_{year}'

        add_node(pub_id, title, 'publication',
                 subtype='research_paper',
                 data_source=f'https://api.semanticscholar.org/graph/v1/paper/{s2_id}',
                 description=f'{venue} ({year}) | {cites} citations',
                 details={'Semantic Scholar': f'https://www.semanticscholar.org/paper/{s2_id}'})

        print(f"  + PUB [{year}]: {title[:60]} ({cites} cites)")

        # PI → publication published_study edge
        add_edge(f'pub_{pi_id}_{pub_id}', pi_id, pub_id, 'published_study',
                 data_source='https://api.semanticscholar.org',
                 confidence='HIGH')

# ══════════════════════════════════════════════════════════════════════════════
# 4. WHITEHEAD → MIT RELATIONSHIP
# ══════════════════════════════════════════════════════════════════════════════

print("\n--- ORG RELATIONSHIPS ---")
add_edge('partof_whitehead_mit', 'inst_whitehead_institute', 'inst_Massachusetts_Institute_of_Technology', 'part_of',
         data_source='general_knowledge', confidence='HIGH')

# ══════════════════════════════════════════════════════════════════════════════
# MERGE
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n=== SPRINT 8 SUMMARY ===")
new_types = Counter(n['type'] for n in new_nodes)
new_etypes = Counter(e['type'] for e in new_edges)
print(f"New nodes: {len(new_nodes)} {dict(new_types)}")
print(f"New edges: {len(new_edges)} {dict(new_etypes)}")

total_nih_funding = sum(e.get('amount', 0) or 0 for e in new_edges if e.get('type') == 'funds')
print(f"New NIH funding tracked: ${total_nih_funding:,.0f}")

with open(os.path.join(STAGED_DIR, 's8_nodes.json'), 'w') as f:
    json.dump(new_nodes, f, indent=2)
with open(os.path.join(STAGED_DIR, 's8_edges.json'), 'w') as f:
    json.dump(new_edges, f, indent=2)

nodes.extend(new_nodes)
edges.extend(new_edges)
graph['nodes'] = nodes
graph['edges'] = edges

with open(GRAPH_FILE, 'w') as f:
    json.dump(graph, f, indent=2)

print(f"\nMerged into graph: {len(nodes)} nodes, {len(edges)} edges")
