"""
Sprint 9: NSF + International Funding Expansion
Adds NSF funder + 16 grants, UKRI funder + 2 grants.
Sources:
  data/raw/s9_nsf_international/nsf_selected.json
  data/raw/s9_nsf_international/ukri_selected.json
"""
import json, re, uuid

with open('data/graph_data.json') as f:
    g = json.load(f)
existing_ids = {n['id'] for n in g['nodes']}

with open('data/raw/s9_nsf_international/nsf_selected.json') as f:
    nsf_awards = json.load(f)
with open('data/raw/s9_nsf_international/ukri_selected.json') as f:
    ukri_awards = json.load(f)

nodes, edges = [], []
seen_nodes = set(existing_ids)

def add_node(n):
    if n['id'] not in seen_nodes:
        nodes.append(n)
        seen_nodes.add(n['id'])

def add_edge(e):
    edges.append(e)

# ── Funder nodes ──────────────────────────────────────────────────────────────
add_node({
    "id": "funder_nsf",
    "type": "funder",
    "label": "National Science Foundation",
    "short": "NSF",
    "url": "https://www.nsf.gov",
    "description": "US federal agency funding fundamental research in science and engineering",
    "bridge": False
})

add_node({
    "id": "funder_ukri",
    "type": "funder",
    "label": "UK Research and Innovation",
    "short": "UKRI",
    "url": "https://www.ukri.org",
    "description": "UK public body funding research and innovation across all disciplines",
    "bridge": False
})

# ── NSF grants ────────────────────────────────────────────────────────────────
# Only keep grants where PI is in graph OR institution is in graph
# Filter out clearly non-relevant awards (check title manually)
EXCLUDED_NSF_TITLES = {
    "CNS Core: Small: Toward Globally-Optimal Resource Distribution",  # networking, not bio
    "Collaborative Research: Safe Reinforcement Learning Guaranteed by Bayesian",  # RL not bio
    "ML Basis for Intelligence Augmentation:Toward Personalized Modeling",  # general ML
    "III: Small: Multiple Device Collaborative Learning",  # distributed ML
    "III: Small: Trustworthy and Explainable AI for Neurodegenerat",  # neurodegen, not bio
    "MRI: Track #1: Development of a System for Ultra-Low Tempera",  # lab equipment
}

# Additional institution mapping for NSF awards
NSF_AWARDEE_TO_INST = {
    'columbia university': 'inst_Columbia_University',
    'harvard university': 'inst_Harvard_University',
    'university of california-berkeley': 'inst_University_of_California_Berkeley',
    'princeton university': 'inst_Princeton_University',
    'carnegie mellon university': 'inst_Carnegie_Mellon_University',
    'university of california-san francisco': 'inst_University_of_California__San_Francisco',
    'university of texas at austin': 'inst_University_of_Texas_at_Austin',
    'stanford university': 'inst_Stanford_University',
}

for award in nsf_awards:
    title = award.get('title','')
    # Skip excluded
    if any(title.startswith(excl[:40]) for excl in EXCLUDED_NSF_TITLES):
        continue

    awardee = (award.get('awardeeName') or '').lower()
    pi_name  = f"{award.get('piFirstName','')} {award.get('piLastName','')}".strip()
    pi_id    = award.get('_pi_id')
    inst_id  = award.get('_inst_id') or NSF_AWARDEE_TO_INST.get(awardee)
    amt      = award.get('_amt', 0)

    if not inst_id:
        continue

    # Sanitise grant node ID
    safe_title = re.sub(r'[^a-z0-9]+', '_', title.lower())[:50].strip('_')
    nsf_num    = award.get('id','')
    grant_id   = f"program_nsf_{nsf_num}"

    add_node({
        "id": grant_id,
        "type": "program",
        "subtype": "nsf_grant",
        "label": title,
        "short": f"NSF {nsf_num}",
        "url": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={nsf_num}",
        "description": f"NSF award to {award.get('awardeeName','')} (PI: {pi_name})",
        "amount": amt,
        "date_range": f"{award.get('start','')}–{award.get('end','')}",
        "bridge": False
    })

    # NSF → grant
    add_edge({
        "id": f"edge_funds_nsf_{nsf_num}",
        "type": "funds",
        "source": "funder_nsf",
        "target": grant_id,
        "amount": amt,
        "grant_title": title,
        "date_range": f"{award.get('start','')}–{award.get('end','')}",
        "confidence": "HIGH"
    })

    # grant → institution
    add_edge({
        "id": f"edge_funds_nsf_{nsf_num}_to_inst",
        "type": "funds",
        "source": grant_id,
        "target": inst_id,
        "amount": amt,
        "grant_title": title,
        "confidence": "HIGH"
    })

    # PI performs_on grant
    if pi_id:
        add_edge({
            "id": f"edge_performs_nsf_{nsf_num}_{pi_id}",
            "type": "performs_on",
            "source": pi_id,
            "target": grant_id,
            "confidence": "HIGH"
        })

print(f"NSF grants processed: checking UKRI next...")

# ── UKRI grants ───────────────────────────────────────────────────────────────
for award in ukri_awards:
    ukri_id = award.get('ukri_id','')
    title   = award.get('title','')
    inst_id = award.get('inst_id')
    amt_gbp = award.get('amount_gbp', 0)
    amt_usd = award.get('amount_usd', 0)
    funder  = award.get('leadFunder','')

    if not inst_id or not amt_gbp:
        continue

    grant_id = f"program_ukri_{re.sub(r'[^a-z0-9]+','_', ukri_id.lower())[:20]}"
    
    add_node({
        "id": grant_id,
        "type": "program",
        "subtype": "ukri_grant",
        "label": title,
        "short": f"UKRI/{funder}",
        "url": f"https://gtr.ukri.org/projects?ref={ukri_id}",
        "description": f"UKRI {funder} award to {award.get('org_name','')}",
        "amount": amt_usd,
        "amount_gbp": amt_gbp,
        "date_range": f"{award.get('start','')}–{award.get('end','')}",
        "bridge": False
    })

    add_edge({
        "id": f"edge_funds_ukri_{ukri_id[:12]}",
        "type": "funds",
        "source": "funder_ukri",
        "target": grant_id,
        "amount": amt_usd,
        "grant_title": title,
        "confidence": "HIGH"
    })

    add_edge({
        "id": f"edge_funds_ukri_{ukri_id[:12]}_to_inst",
        "type": "funds",
        "source": grant_id,
        "target": inst_id,
        "amount": amt_usd,
        "grant_title": title,
        "confidence": "HIGH"
    })

# ── Save staged ───────────────────────────────────────────────────────────────
with open('data/staged/s9_nodes.json', 'w') as f:
    json.dump(nodes, f, indent=2)
with open('data/staged/s9_edges.json', 'w') as f:
    json.dump(edges, f, indent=2)

print(f"Staged: {len(nodes)} nodes, {len(edges)} edges")

# ── Merge into graph ──────────────────────────────────────────────────────────
g['nodes'].extend(nodes)
g['edges'].extend(edges)

# Deduplicate edges by id
seen_eids = {}
deduped_edges = []
for e in g['edges']:
    eid = e.get('id','')
    if eid not in seen_eids:
        seen_eids[eid] = True
        deduped_edges.append(e)
g['edges'] = deduped_edges

with open('data/graph_data.json', 'w') as f:
    json.dump(g, f, indent=2)

print(f"Graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges")

# Quick node type breakdown
from collections import Counter
nt = Counter(n['type'] for n in g['nodes'])
et = Counter(e['type'] for e in g['edges'])
print("\nNode types:", dict(nt))
print("Edge types:", dict(et))
