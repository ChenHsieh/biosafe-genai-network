#!/usr/bin/env python3
"""Sprint 7: Cross-venue Expansion.

Adds papers from sibling workshops where ≥1 author already exists in the graph.
Workshops: ICLR 2025 MLGenX, NeurIPS 2025 GenAI4Health, NeurIPS 2025 AI4Science.

Rule: Only include papers where ≥1 author is already in our graph.
This script adds:
  - New presentation nodes for cross-venue papers
  - New author nodes for co-authors of overlapping papers
  - authored edges
  - current_affiliation edges (from OpenReview profiles where available)
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')
STAGED_DIR = os.path.join(BASE_DIR, 'data', 'staged')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 's7_cross_venue')
os.makedirs(STAGED_DIR, exist_ok=True)

with open(GRAPH_FILE) as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']
existing_ids = {n['id'] for n in nodes}
existing_edge_ids = {e['id'] for e in edges}
node_by_id = {n['id']: n for n in nodes}

# Build author lookup (lowercase)
our_authors = {}
for n in nodes:
    if n['type'] == 'author':
        al = n['label'].lower().strip()
        our_authors[al] = n['id']
        parts = al.split()
        if len(parts) >= 2:
            our_authors[f'{parts[0]} {parts[-1]}'] = n['id']

# Build institution lookup
inst_lookup = {}
for n in nodes:
    if n['type'] in ('institution', 'org'):
        inst_lookup[n['label'].lower()] = n['id']

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

def resolve_author(name):
    """Check if author exists in graph, return ID or None."""
    al = name.lower().strip()
    if al in our_authors:
        return our_authors[al]
    parts = al.split()
    if len(parts) >= 2:
        fl = f'{parts[0]} {parts[-1]}'
        if fl in our_authors:
            return our_authors[fl]
    return None

def make_author_id(name):
    """Create a clean author ID."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name.replace(' ', '_'))
    return f'author_{clean}'

def resolve_institution(name):
    """Try to match institution name to existing node."""
    nl = name.lower().strip()
    if nl in inst_lookup:
        return inst_lookup[nl]
    # Common abbreviations
    for label, nid in inst_lookup.items():
        if nl in label or label in nl:
            return nid
    return None


# ══════════════════════════════════════════════════════════════════════════════
# LOAD OVERLAP DATA
# ══════════════════════════════════════════════════════════════════════════════

with open(os.path.join(RAW_DIR, 'overlap_analysis.json')) as f:
    overlap_data = json.load(f)

# Deduplicate by paper title (some papers appear in multiple workshops)
seen_titles = {}
unique_papers = []
for p in overlap_data:
    title_key = p['title'].lower().strip()
    if title_key not in seen_titles:
        seen_titles[title_key] = p
        unique_papers.append(p)
    else:
        # Merge venue info
        existing = seen_titles[title_key]
        existing['workshop'] += f" + {p['workshop']}"

print(f"Total overlap papers: {len(overlap_data)}")
print(f"Unique papers (after dedup): {len(unique_papers)}")

# ══════════════════════════════════════════════════════════════════════════════
# WORKSHOP VENUE NODES
# ══════════════════════════════════════════════════════════════════════════════

VENUE_NODES = {
    'event_iclr_mlgenx_2025': {
        'label': 'ICLR 2025 MLGenX Workshop',
        'subtype': 'workshop',
        'description': 'Machine Learning for Genomics Explorations, ICLR 2025',
        'url': 'https://iclr.cc/virtual/2025/workshop/23974',
    },
    'event_neurips_genai4health_2025': {
        'label': 'NeurIPS 2025 GenAI4Health Workshop',
        'subtype': 'workshop',
        'description': 'Generative AI for Health, NeurIPS 2025',
    },
    'event_neurips_ai4science_2025': {
        'label': 'NeurIPS 2025 AI4Science Workshop',
        'subtype': 'workshop',
        'description': 'AI for Science, NeurIPS 2025',
    },
}

WORKSHOP_MAP = {
    'mlgenx': 'event_iclr_mlgenx_2025',
    'genai4health': 'event_neurips_genai4health_2025',
    'ai4science': 'event_neurips_ai4science_2025',
}

for vid, vdata in VENUE_NODES.items():
    add_node(vid, vdata['label'], 'presentation', **{k: v for k, v in vdata.items() if k != 'label'})

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS EACH PAPER
# ══════════════════════════════════════════════════════════════════════════════

for paper in unique_papers:
    title = paper['title']
    authors = paper['authors']
    paper_id = paper['paper_id']
    ws = paper['workshop'].split(' + ')[0]  # primary workshop
    venue_id = WORKSHOP_MAP.get(ws, WORKSHOP_MAP.get('genai4health'))

    # Create paper node
    paper_nid = f'paper_{paper_id}'
    openreview_url = f'https://openreview.net/forum?id={paper_id}'

    # Skip if paper already exists (e.g., same paper submitted to BioSafe GenAI too)
    if paper_nid in existing_ids:
        print(f"  SKIP (exists): {title[:60]}")
        continue

    add_node(paper_nid, title, 'presentation',
             subtype='poster',
             url=openreview_url,
             data_source=openreview_url,
             details={'OpenReview': openreview_url})

    print(f"\n+ PAPER: {title[:70]}")
    print(f"  Workshop: {ws}, ID: {paper_id}")

    # Process authors
    for author_name in authors:
        existing_id = resolve_author(author_name)

        if existing_id:
            author_id = existing_id
            print(f"  EXISTING: {author_name} -> {existing_id}")
        else:
            author_id = make_author_id(author_name)
            if add_node(author_id, author_name, 'author',
                       data_source=openreview_url):
                # Register in lookup
                our_authors[author_name.lower().strip()] = author_id
                parts = author_name.lower().split()
                if len(parts) >= 2:
                    our_authors[f'{parts[0]} {parts[-1]}'] = author_id
                print(f"  NEW AUTHOR: {author_name}")
            else:
                print(f"  AUTHOR EXISTS: {author_name}")

        # authored edge
        edge_id = f'authored_{author_id}_{paper_nid}'
        add_edge(edge_id, author_id, paper_nid, 'authored',
                data_source=openreview_url)

    # presented_at edge to workshop venue (cross-venue link)
    # We use 'part_of' to link the paper to the workshop it was presented at
    # Actually, let's just track which workshop it came from via data fields

# ══════════════════════════════════════════════════════════════════════════════
# MERGE
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n=== SPRINT 7 SUMMARY ===")
print(f"New nodes: {len(new_nodes)}")
new_presentations = sum(1 for n in new_nodes if n['type'] == 'presentation')
new_authors = sum(1 for n in new_nodes if n['type'] == 'author')
print(f"  New presentations: {new_presentations}")
print(f"  New authors: {new_authors}")
print(f"New edges: {len(new_edges)}")

# Save staged
with open(os.path.join(STAGED_DIR, 's7_nodes.json'), 'w') as f:
    json.dump(new_nodes, f, indent=2)
with open(os.path.join(STAGED_DIR, 's7_edges.json'), 'w') as f:
    json.dump(new_edges, f, indent=2)

nodes.extend(new_nodes)
edges.extend(new_edges)
graph['nodes'] = nodes
graph['edges'] = edges

with open(GRAPH_FILE, 'w') as f:
    json.dump(graph, f, indent=2)

print(f"\nMerged into graph: {len(nodes)} nodes, {len(edges)} edges")
