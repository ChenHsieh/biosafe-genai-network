#!/usr/bin/env python3
"""Sprint 4: Extract DARPA BTO + IARPA Fun GCAT data for graph integration.

Data sources:
  1. USASpending.gov API (JSON) — 21 AI-relevant DARPA BTO awards
  2. IARPA Fun GCAT program page — 11 performers (5 prime + 6 T&E)
  3. DARPA press releases — PI names for SAFE GENES, P3, PREEMPT, PREPARE

Output: data/staged/s4_nodes.json, data/staged/s4_edges.json
"""

import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 's4_darpa_iarpa')
STAGED_DIR = os.path.join(BASE_DIR, 'data', 'staged')
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')

os.makedirs(STAGED_DIR, exist_ok=True)

# ── Load existing graph for bridge detection ──────────────────────────────
with open(GRAPH_FILE) as f:
    graph = json.load(f)

existing_ids = {n['id'] for n in graph['nodes']}
existing_labels_lower = {}
for n in graph['nodes']:
    existing_labels_lower[n['label'].lower()] = n['id']


# ── Recipient → graph node mapping ────────────────────────────────────────
RECIPIENT_MAP = {
    'PRESIDENT AND FELLOWS OF HARVARD COLLEGE': 'inst_Harvard_University',
    'YALE UNIV': 'inst_Yale_University',
    'THE BROAD INSTITUTE, INC': 'inst_Broad_Institute',
    'RUTGERS, THE STATE UNIVERSITY': 'inst_Rutgers_University',
    'UNIVERSITY OF WASHINGTON': 'inst_University_of_Washington',
    'TRUSTEES OF THE UNIVERSITY OF PENNSYLVANIA, THE': 'inst_University_of_Pennsylvania',
    'THE TRUSTEES OF COLUMBIA UNIVERSITY IN THE CITY OF NEW YORK': 'inst_Columbia_University',
    'MASSACHUSETTS INSTITUTE OF TECHNOLOGY': 'inst_Massachusetts_Institute_of_Technology',
    'THE JOHNS HOPKINS UNIVERSITY': 'inst_Johns_Hopkins_University',
    'UNIVERSITY OF MARYLAND, COLLEGE PARK': 'inst_University_of_Maryland__College_Park',
    'THE LELAND STANFORD JUNIOR UNIVERSITY': 'inst_Stanford_University',
    'WILLIAM MARSH RICE UNIVERSITY': 'inst_Rice_University',
    'UNIVERSITY OF TEXAS AT AUSTIN': 'inst_University_of_Texas_at_Austin',
    'CARNEGIE MELLON UNIVERSITY': 'inst_Carnegie_Mellon_University',
    'DUKE UNIVERSITY': 'org_duke_university',
    'UNIVERSITY OF OXFORD': 'inst_University_of_Oxford',
    'UNIVERSITY OF UTAH': 'inst_University_of_Utah',
    'CALIFORNIA INSTITUTE OF TECHNOLOGY': 'inst_California_Institute_of_Technology',
    'THE JOHNS HOPKINS UNIVERSITY APPLIED PHYSICS LABORATORY LLC': 'inst_Johns_Hopkins_University',
    'GEORGIA TECH APPLIED RESEARCH CORP': 'inst_Georgia_Institute_of_Technology',
    'NEW YORK UNIVERSITY': 'inst_New_York_University',
    'UNIVERSITY OF SOUTHERN CALIFORNIA': 'org_university_of_southern_california',
    'REGENTS OF THE UNIVERSITY OF CALIFORNIA, SAN FRANCISCO, THE': 'org_university_of_california_san_francisco',
}

# Fun GCAT performer → graph node mapping
FUNGCAT_MAP = {
    'Harvard University': 'inst_Harvard_University',
    'Johns Hopkins University Applied Physics Laboratory': 'inst_Johns_Hopkins_University',
    'Virginia Tech': None,
    'Battelle Memorial Institute': None,
    'Signature Science': None,
    'SRI International': None,  # will be resolved via fuzzy match to org_darpa_sri_international
    'Lawrence Livermore National Laboratory': 'inst_Lawrence_Livermore_National_Laboratory',
    'Pacific Northwest National Laboratory': 'inst_Pacific_Northwest_National_Laboratory',
    'Los Alamos National Laboratory': None,
    'Department of Homeland Security': None,
    'US Army Medical Research Institute of Infectious Diseases': None,
}

# PI → institution mapping (from press releases)
# source_type: "news_release" means sourced from DARPA news, not contract data
PI_DATA = [
    # SAFE GENES — source: https://www.darpa.mil/news-events/2017-07-19
    {"name": "Amit Choudhary", "institution": "Broad Institute", "inst_id": "inst_Broad_Institute",
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    {"name": "George Church", "institution": "Harvard Medical School", "inst_id": "inst_Harvard_University",
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    {"name": "Keith Joung", "institution": "Massachusetts General Hospital", "inst_id": None,
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    {"name": "Kevin Esvelt", "institution": "Massachusetts Institute of Technology", "inst_id": "inst_Massachusetts_Institute_of_Technology",
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release",
     "existing_author_id": "author_Kevin_M__Esvelt1"},
    {"name": "John Godwin", "institution": "North Carolina State University", "inst_id": None,
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    {"name": "Jennifer Doudna", "institution": "University of California, Berkeley", "inst_id": None,
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    {"name": "Omar Akbari", "institution": "University of California, Riverside", "inst_id": None,
     "program": "SAFE GENES", "source": "DARPA news 2017-07-19", "source_type": "news_release"},
    # PREEMPT — source: https://www.darpa.mil/news/2019/medical-preparedness
    {"name": "Ariel Weinberger", "institution": "Autonomous Therapeutics, Inc.", "inst_id": None,
     "program": "PREEMPT", "source": "DARPA news 2019", "source_type": "news_release"},
    {"name": "Peter Barry", "institution": "University of California, Davis", "inst_id": None,
     "program": "PREEMPT", "source": "DARPA news 2019", "source_type": "news_release"},
    {"name": "Carla Saleh", "institution": "Institut Pasteur", "inst_id": None,
     "program": "PREEMPT", "source": "DARPA news 2019", "source_type": "news_release"},
    {"name": "Raina Plowright", "institution": "Montana State University", "inst_id": None,
     "program": "PREEMPT", "source": "DARPA news 2019", "source_type": "news_release"},
    {"name": "Luke Alphey", "institution": "The Pirbright Institute", "inst_id": None,
     "program": "PREEMPT", "source": "DARPA news 2019", "source_type": "news_release"},
    # PREPARE — source: https://www.darpa.mil/news/2021/defend-chemical-biolgical-threats
    {"name": "Harris Wang", "institution": "Columbia University", "inst_id": "inst_Columbia_University",
     "program": "PREPARE", "source": "DARPA news 2021", "source_type": "news_release"},
    {"name": "Jonathan Weissman", "institution": "University of California, San Francisco", "inst_id": "org_university_of_california_san_francisco",
     "program": "PREPARE", "source": "DARPA news 2021", "source_type": "news_release"},
]


# ── Bio-relevance + AI filters ───────────────────────────────────────────
BIO_REL = re.compile(
    r'biolog|biosecur|biosafety|pandemic|pathogen|genomic|sequenc|'
    r'protein|antiviral|vaccine|virol|antibod|countermeasure|'
    r'gene edit|gene drive|CRISPR|infectious|epidemic|'
    r'zoonotic|biosurveillance|biodefense|biothreats|'
    r'PREEMPT|SAFE GENES|PREPARE|pandemic prevention|'
    r'PROPHECY|SIGMA\+|biological threat|virus|'
    r'diagnostic|bioengineering|molecular biology|'
    r'reef|coral', re.I
)
FALSE_POS = re.compile(
    r'LORELEI|(?:ADAPTIVE )?RADAR|ELECTRONIC WARFARE|'
    r'SATELLITE|TRANSPONDER|OPTICAL|LASER|INFRARED|'
    r'CHEMICAL AGENT DETECTOR|MINE DETECTION', re.I
)
AI_KW = re.compile(
    r'artificial intelligence|machine learning|deep learning|neural network|'
    r'computational|algorithm|model.*predict|predict.*model|'
    r'data.driven|\bAI\b|\bML\b|NLP|natural language|'
    r'automated|autonomous|robot|'
    r'living foundries|synthetic biology|synergistic discovery|'
    r'PROPHECY|predictive|evolution.*platform|'
    r'screening.*software|sequence.*assess|'
    r'LEAP|evaluation.*AI', re.I
)

# ── Program identification from descriptions ──────────────────────────────
PROGRAM_PATTERNS = {
    'PROPHECY': re.compile(r'PROPHECY|predictive.*viral.*evolution|virus.*host.*picoreactor', re.I),
    'LIVING FOUNDRIES': re.compile(r'LIVING FOUNDRIES|ATCG', re.I),
    'BIOLOGICAL CONTROL': re.compile(r'BIOLOGICAL CONTROL PROGRAM', re.I),
    'BRICS': re.compile(r'BRICS', re.I),
    'L2M': re.compile(r'L2M|LIFELONG LEARNING MACHINE', re.I),
    'SIGMA+': re.compile(r'SIGMA\+', re.I),
    'LEAP': re.compile(r'LEAP.*BIOSECURITY|LABORATORY EVALUATION.*AI', re.I),
    'RADIOBIO': re.compile(r'RADIOBIO', re.I),
    'BIO TELEPORTER': re.compile(r'BIOLOGICAL TELEPORTER', re.I),
    'ARCADIA': re.compile(r'ARCADIA', re.I),
    'TRIAGE CHALLENGE': re.compile(r'TRIAGE CHALLENGE|DTC PROGRAM', re.I),
    'BTO BAA': re.compile(r'OFFICE.WIDE BAA.*BIOLOGICAL TECHNOLOGIES', re.I),
}


def identify_program(desc):
    for name, pat in PROGRAM_PATTERNS.items():
        if pat.search(desc):
            return name
    return 'DARPA BTO (unclassified program)'


def make_id(prefix, name):
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')[:60]
    return f"{prefix}_{slug}"


# ══════════════════════════════════════════════════════════════════════════
# EXTRACTION
# ══════════════════════════════════════════════════════════════════════════
nodes = {}  # id -> node dict
edges = []  # edge dicts

# ── 1. Funder + Program hierarchy ─────────────────────────────────────────
nodes['funder_darpa'] = {
    'id': 'funder_darpa', 'label': 'DARPA',
    'type': 'funder', 'subtype': 'government',
    'description': 'Defense Advanced Research Projects Agency — US DoD',
    'url': 'https://www.darpa.mil',
}
nodes['funder_iarpa'] = {
    'id': 'funder_iarpa', 'label': 'IARPA',
    'type': 'funder', 'subtype': 'government',
    'description': 'Intelligence Advanced Research Projects Activity — ODNI',
    'url': 'https://www.iarpa.gov',
}
# DARPA BTO programs (only ones with AI-relevant awards)
darpa_programs = {
    'PROPHECY': {'desc': 'Pathogen prediction and viral evolution modeling', 'url': None},
    'LIVING FOUNDRIES': {'desc': 'Engineering biology — design-build-test cycle automation', 'url': None},
    'BIOLOGICAL CONTROL': {'desc': 'Predictive closed-loop control of biological systems', 'url': None},
    'BRICS': {'desc': 'Biologically Robust Interfaces in Complex Settings — synthetic biology', 'url': None},
    'L2M': {'desc': 'Lifelong Learning Machines — bio-inspired ML', 'url': None},
    'SIGMA+': {'desc': 'Biological threat detection systems', 'url': None},
    'LEAP': {'desc': 'Laboratory Evaluation of AI-Developed Protocols for Biosecurity', 'url': None},
    'ARCADIA': {'desc': 'Autonomous biological systems research', 'url': None},
    'TRIAGE CHALLENGE': {'desc': 'DARPA Triage Challenge — automated medical triage', 'url': None},
    'BIO TELEPORTER': {'desc': 'Digital-to-biological conversion systems', 'url': None},
    'BTO BAA': {'desc': 'DARPA Biological Technologies Office open BAA awards', 'url': None},
}

for prog_name, info in darpa_programs.items():
    pid = make_id('program_darpa', prog_name)
    nodes[pid] = {
        'id': pid, 'label': f'DARPA {prog_name}',
        'type': 'program', 'subtype': 'darpa_bto',
        'description': info['desc'],
    }
    edges.append({
        'id': f'funds_darpa_{pid}', 'source': 'funder_darpa', 'target': pid,
        'type': 'funds', 'grant_title': None, 'amount': None,
        'extraction_method': 'hierarchy',
    })

# IARPA Fun GCAT
nodes['program_iarpa_fungcat'] = {
    'id': 'program_iarpa_fungcat',
    'label': 'IARPA Fun GCAT',
    'type': 'program', 'subtype': 'iarpa',
    'description': 'Functional Genomic and Computational Assessment of Threats — AI-driven DNA sequence threat screening (2017–2022)',
    'url': 'https://www.iarpa.gov/research-programs/fun-gcat',
    'details': {'BAA': 'IARPA-BAA-16-08'},
}
edges.append({
    'id': 'funds_iarpa_fungcat', 'source': 'funder_iarpa', 'target': 'program_iarpa_fungcat',
    'type': 'funds', 'grant_title': None, 'amount': None,
    'extraction_method': 'hierarchy',
})


# ── 2. DARPA BTO Awards from USASpending.gov ──────────────────────────────
with open(os.path.join(RAW_DIR, 'darpa_bto_all_contracts.json')) as f:
    contracts = json.load(f).get('results', [])
with open(os.path.join(RAW_DIR, 'darpa_bto_all_grants.json')) as f:
    grants = json.load(f).get('results', [])

all_awards = contracts + grants
bio_ai_awards = []
for a in all_awards:
    desc = a.get('Description', '') or ''
    rname = a.get('Recipient Name', '') or ''
    if FALSE_POS.search(desc):
        continue
    if BIO_REL.search(f"{desc} {rname}") and AI_KW.search(desc):
        bio_ai_awards.append(a)

print(f"DARPA BTO: {len(all_awards)} total → {len(bio_ai_awards)} bio+AI relevant")

darpa_fund_count = 0
for a in bio_ai_awards:
    rname = (a.get('Recipient Name') or '').strip()
    desc = (a.get('Description') or '')
    amt = a.get('Award Amount', 0) or 0
    award_id = a.get('Award ID', '')
    prog_name = identify_program(desc)
    prog_id = make_id('program_darpa', prog_name)

    # Ensure program node exists (for unclassified)
    if prog_id not in nodes:
        nodes[prog_id] = {
            'id': prog_id, 'label': f'DARPA {prog_name}',
            'type': 'program', 'subtype': 'darpa_bto',
            'description': '',
        }
        edges.append({
            'id': f'funds_darpa_{prog_id}', 'source': 'funder_darpa', 'target': prog_id,
            'type': 'funds', 'grant_title': None, 'amount': None,
            'extraction_method': 'hierarchy',
        })

    # Resolve recipient to graph node
    target_id = RECIPIENT_MAP.get(rname)
    if target_id and target_id not in existing_ids:
        target_id = None  # mapped but not in graph

    if not target_id:
        # Try fuzzy match
        for label_lower, nid in existing_labels_lower.items():
            if rname.lower().rstrip(',') in label_lower or label_lower in rname.lower():
                target_id = nid
                break

    if not target_id:
        # Create new org node
        target_id = make_id('org_darpa', rname)
        # Clean up label — title case for ALL CAPS, preserve mixed case
        label = rname.title() if rname.isupper() else rname
        # Fix known acronyms mangled by .title()
        label = label.replace('Sri International', 'SRI International')
        label = label.replace('Llc', 'LLC').replace('Inc.', 'Inc.')
        if target_id not in nodes:
            nodes[target_id] = {
                'id': target_id, 'label': label,
                'type': 'org', 'subtype': 'darpa_performer',
            }

    # Create funds edge: program → recipient
    grant_title = f"{rname.title() if rname.isupper() else rname} — {prog_name} ({award_id})"
    edge_id = f"funds_darpa_{award_id}_{darpa_fund_count}"
    edges.append({
        'id': edge_id, 'source': prog_id, 'target': target_id,
        'type': 'funds',
        'amount': int(amt) if amt else None,
        'grant_title': grant_title,
        'extraction_method': 'usaspending_api',
        'data_source': 'USASpending.gov',
        'award_id': award_id,
        'start_date': a.get('Start Date'),
        'end_date': a.get('End Date'),
    })
    darpa_fund_count += 1

print(f"  Created {darpa_fund_count} DARPA fund edges")


# ── 3. IARPA Fun GCAT performers ─────────────────────────────────────────
with open(os.path.join(RAW_DIR, 'iarpa_fungcat_extracted.json')) as f:
    fungcat = json.load(f)

fungcat_count = 0
for p in fungcat['prime_performers'] + fungcat['test_eval_partners']:
    pname = p['name']
    role = p['role']

    target_id = FUNGCAT_MAP.get(pname)
    if target_id and target_id not in existing_ids:
        target_id = None

    if not target_id:
        # Fuzzy match against existing graph
        for label_lower, nid in existing_labels_lower.items():
            if pname.lower() in label_lower or label_lower in pname.lower():
                target_id = nid
                break

    if not target_id:
        # Also check nodes created during this extraction (e.g. DARPA pass)
        for nid, n in nodes.items():
            if pname.lower() in n['label'].lower() or n['label'].lower() in pname.lower():
                target_id = nid
                break

    if not target_id:
        target_id = make_id('org_iarpa', pname)
        if target_id not in nodes:
            nodes[target_id] = {
                'id': target_id, 'label': pname,
                'type': 'org', 'subtype': f'iarpa_{role}',
            }

    edge_id = f"funds_iarpa_fungcat_{fungcat_count}"
    edges.append({
        'id': edge_id,
        'source': 'program_iarpa_fungcat',
        'target': target_id,
        'type': 'funds',
        'amount': None,  # classified
        'grant_title': f"{pname} — Fun GCAT ({role.replace('_', ' ')})",
        'extraction_method': 'webpage_scrape',
        'data_source': 'https://www.iarpa.gov/research-programs/fun-gcat',
    })
    fungcat_count += 1

print(f"  Created {fungcat_count} Fun GCAT performer edges")


# ── 4. PI names from DARPA press releases ─────────────────────────────────
pi_count = 0
pi_affil_count = 0
for pi in PI_DATA:
    pi_name = pi['name']
    inst_id = pi.get('inst_id')
    existing_id = pi.get('existing_author_id')
    program = pi['program']
    source = pi['source']

    # Use existing author node if available (e.g., Kevin Esvelt)
    if existing_id and existing_id in existing_ids:
        author_id = existing_id
    else:
        author_id = make_id('author', pi_name)
        if author_id not in nodes:
            nodes[author_id] = {
                'id': author_id,
                'label': pi_name,
                'type': 'author',
                'subtype': 'darpa_pi',
                'description': f'PI for DARPA {program}',
                'details': {
                    'source': source,
                    'source_type': pi['source_type'],
                    'program': program,
                },
            }
            pi_count += 1

    # Affiliation edge: PI → institution
    if inst_id and inst_id in existing_ids:
        affil_target = inst_id
    elif inst_id and inst_id in [n for n in nodes]:
        affil_target = inst_id
    else:
        # Institution not in graph — create org node if needed
        inst_name = pi['institution']
        affil_target = make_id('org_darpa', inst_name)
        if affil_target not in nodes and affil_target not in existing_ids:
            nodes[affil_target] = {
                'id': affil_target, 'label': inst_name,
                'type': 'org', 'subtype': 'darpa_institution',
            }

    affil_edge_id = f"affil_darpa_pi_{make_id('', pi_name)}"
    edges.append({
        'id': affil_edge_id,
        'source': author_id,
        'target': affil_target,
        'type': 'current_affiliation',
        'extraction_method': 'news_release',
        'data_source': source,
    })
    pi_affil_count += 1

print(f"  Created {pi_count} new PI author nodes, {pi_affil_count} affiliation edges")


# ── 5. Save staged data ──────────────────────────────────────────────────
new_nodes = [v for v in nodes.values()]
with open(os.path.join(STAGED_DIR, 's4_nodes.json'), 'w') as f:
    json.dump(new_nodes, f, indent=2)
with open(os.path.join(STAGED_DIR, 's4_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2)

# ── Summary ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"SPRINT 4 EXTRACTION SUMMARY")
print(f"{'='*60}")

type_counts = defaultdict(int)
for n in new_nodes:
    type_counts[n['type']] += 1

print(f"\nNew nodes ({len(new_nodes)}):")
for t, c in sorted(type_counts.items()):
    print(f"  {t:<15} {c}")

edge_types = defaultdict(int)
for e in edges:
    src = e.get('extraction_method', '?')
    edge_types[src] += 1

print(f"\nEdges ({len(edges)}):")
for t, c in sorted(edge_types.items()):
    print(f"  {t:<25} {c}")

# Count bridges
bridge_count = 0
for e in edges:
    if e['target'] in existing_ids or e['source'] in existing_ids:
        bridge_count += 1
print(f"\nBridge edges (connect to existing graph): {bridge_count}")

total_funding = sum(e.get('amount', 0) or 0 for e in edges)
print(f"Total funding captured: ${total_funding:,.0f}")
print(f"\nStaged to: {STAGED_DIR}/s4_*.json")
