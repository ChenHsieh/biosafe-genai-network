#!/usr/bin/env python3
"""Sprint 5: Extract Policy & Big Tech biosecurity evaluation relationships.

This sprint maps the biosecurity evaluation ecosystem:
  - Which orgs evaluate which AI labs' models
  - Published research papers/reports/blog posts as evidence nodes
  - Key individuals at evaluation organizations
  - Policy forum participation (NTI AIxBio)
  - Government advisory relationships (OSTP, NIST/AISI)

Data sources (all saved in data/raw/s5_policy_bigtech/):
  1. SecureBio team page (securebio.org/team/)
  2. SecureBio OSTP RFI (files.nitrd.gov)
  3. Epoch AI analysis of biorisk evaluations
  4. RAND published studies (rand.org)
  5. OpenAI + Gryphon Scientific study
  6. NTI AIxBio Forum details
  7. Gryphon Scientific / Deloitte acquisition data

Output: data/staged/s5_nodes.json, data/staged/s5_edges.json
"""

import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 's5_policy_bigtech')
STAGED_DIR = os.path.join(BASE_DIR, 'data', 'staged')
GRAPH_FILE = os.path.join(BASE_DIR, 'data', 'graph_data.json')

os.makedirs(STAGED_DIR, exist_ok=True)

# ── Load existing graph for bridge detection ──────────────────────────────
with open(GRAPH_FILE) as f:
    graph = json.load(f)

existing_ids = {n['id'] for n in graph['nodes']}
existing_edge_ids = {e['id'] for e in graph['edges']}
node_by_id = {n['id']: n for n in graph['nodes']}
existing_labels_lower = {}
for n in graph['nodes']:
    existing_labels_lower[n['label'].lower()] = n['id']

nodes = {}  # id -> node dict (new nodes only)
edges = []  # new edges

def add_node(node_id, label, node_type, **kwargs):
    """Add a new node if it doesn't exist in graph or this batch."""
    if node_id in existing_ids or node_id in nodes:
        return node_id
    node = {'id': node_id, 'label': label, 'type': node_type}
    node.update(kwargs)
    nodes[node_id] = node
    return node_id

def add_edge(edge_id, source, target, edge_type, **kwargs):
    """Add a new edge if it doesn't already exist."""
    if edge_id in existing_edge_ids:
        return
    # Check we haven't already added this edge
    for e in edges:
        if e['id'] == edge_id:
            return
    edge = {'id': edge_id, 'source': source, 'target': target, 'type': edge_type}
    edge.update(kwargs)
    edges.append(edge)

def resolve_existing(label):
    """Try to find an existing node by label (case-insensitive)."""
    ll = label.lower()
    if ll in existing_labels_lower:
        return existing_labels_lower[ll]
    # Partial match
    for el, eid in existing_labels_lower.items():
        if ll in el or el in ll:
            return eid
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: NEW ORGANIZATION NODES
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("SECTION 1: Organization Nodes")
print("=" * 60)

# -- xAI (not yet in graph) --
add_node('inst_xAI', 'xAI', 'institution',
         url='https://x.ai',
         description='AI company founded by Elon Musk')
print("+ NODE: inst_xAI (xAI)")

# -- UK AI Safety Institute --
# Check if already exists
uk_aisi_id = resolve_existing('UK AI Safety Institute')
if not uk_aisi_id:
    uk_aisi_id = 'org_uk_aisi'
    add_node(uk_aisi_id, 'UK AI Safety Institute (AISI)', 'org',
             url='https://www.aisi.gov.uk',
             description='UK government AI safety evaluation body',
             entity_type='government')
    print(f"+ NODE: {uk_aisi_id}")
else:
    print(f"  EXISTS: UK AISI → {uk_aisi_id}")

# -- US AISI (in NIST) --
us_aisi_id = resolve_existing('US AI Safety Institute')
if not us_aisi_id:
    us_aisi_id = 'org_us_aisi'
    add_node(us_aisi_id, 'US AI Safety Institute (NIST)', 'org',
             url='https://www.nist.gov/artificial-intelligence/ai-safety-institute',
             description='US government AI safety evaluation body within NIST',
             entity_type='government')
    print(f"+ NODE: {us_aisi_id}")
else:
    print(f"  EXISTS: US AISI → {us_aisi_id}")

# -- OSTP --
ostp_id = 'org_ostp'
add_node(ostp_id, 'Office of Science and Technology Policy (OSTP)', 'org',
         url='https://www.whitehouse.gov/ostp/',
         description='White House Office of Science and Technology Policy',
         entity_type='government')
print(f"+ NODE: {ostp_id}")

# -- Deloitte (acquired Gryphon) --
deloitte_id = 'org_deloitte'
add_node(deloitte_id, 'Deloitte', 'org',
         url='https://www.deloitte.com',
         description='Acquired Gryphon Scientific in April 2024',
         entity_type='consulting')
print(f"+ NODE: {deloitte_id}")

# -- Council on Strategic Risks --
csr_id = 'org_council_strategic_risks'
add_node(csr_id, 'Council on Strategic Risks', 'org',
         url='https://councilonstrategicrisks.org',
         description='Biosecurity policy think tank; Christine Parthemore is CEO',
         entity_type='think_tank')
print(f"+ NODE: {csr_id}")

# -- Signature Science (check if already exists from IARPA) --
sig_sci_id = resolve_existing('Signature Science')
if sig_sci_id:
    print(f"  EXISTS: Signature Science → {sig_sci_id}")
else:
    sig_sci_id = 'org_signature_science'
    add_node(sig_sci_id, 'Signature Science', 'org',
             description='Co-developed virology evaluation tasks with SecureBio',
             entity_type='research')
    print(f"+ NODE: {sig_sci_id}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: PUBLICATION / EVIDENCE NODES
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 2: Publication & Evidence Nodes")
print("=" * 60)

PUBLICATIONS = [
    {
        'id': 'pub_openai_bio_early_warning_2024',
        'label': 'Building an early warning system for LLM-aided biological threat creation',
        'type': 'publication',
        'subtype': 'blog_post',
        'url': 'https://openai.com/index/building-an-early-warning-system-for-llm-aided-biological-threat-creation/',
        'date': '2024-01-31',
        'authors_orgs': ['OpenAI', 'Gryphon Scientific'],
        'description': 'OpenAI + Gryphon study: 100 participants, GPT-4 bio threat eval. Found models "at most mildly useful".',
    },
    {
        'id': 'pub_rand_bio_attack_redteam_2024',
        'label': 'The Operational Risks of AI in Large-Scale Biological Attacks (RAND RRA2977-2)',
        'type': 'publication',
        'subtype': 'research_report',
        'url': 'https://www.rand.org/pubs/research_reports/RRA2977-2.html',
        'date': '2024-01-25',
        'authors_orgs': ['RAND Corporation'],
        'description': 'Red-team study: no significant difference in bio attack plan viability with/without LLMs.',
    },
    {
        'id': 'pub_rand_automated_grading_2025',
        'label': 'Automated Grading for Evaluating Dual-Use Bio Capabilities of LLMs (RAND RRA3124-1)',
        'type': 'publication',
        'subtype': 'research_report',
        'url': 'https://www.rand.org/pubs/research_reports/RRA3124-1.html',
        'date': '2025',
        'authors_orgs': ['RAND Corporation'],
        'description': 'Proof-of-concept automated grader for LLM bio capabilities across 30+ models.',
    },
    {
        'id': 'pub_securebio_ostp_rfi_2025',
        'label': 'SecureBio RFI Response: AI Action Plan (OSTP)',
        'type': 'publication',
        'subtype': 'policy_submission',
        'url': 'https://files.nitrd.gov/90-fr-9088/SecureBio-AI-RFI-2025.pdf',
        'date': '2025-03-15',
        'authors_orgs': ['SecureBio'],
        'description': 'SecureBio submission to OSTP: AI models now exceed human experts in bioweapon-relevant guidance.',
    },
    {
        'id': 'pub_securebio_biorisk_eval_overview',
        'label': "SecureBio's AI Team: An Overview of Our Biorisk Evaluations",
        'type': 'publication',
        'subtype': 'blog_post',
        'url': 'https://securebio.substack.com/p/securebios-ai-team-an-overview-of',
        'date': '2025',
        'authors_orgs': ['SecureBio'],
        'description': 'Overview of SecureBio eval portfolio: Anthropic, OpenAI, DeepMind, xAI models evaluated.',
    },
    {
        'id': 'pub_epoch_biorisk_eval_analysis',
        'label': 'Do the biorisk evaluations of AI labs actually measure bioweapon risk? (Epoch AI)',
        'type': 'publication',
        'subtype': 'analysis',
        'url': 'https://epoch.ai/gradient-updates/do-the-biorisk-evaluations-of-ai-labs-actually-measure-the-risk-of-developing-bioweapons',
        'date': '2025',
        'authors_orgs': ['Epoch AI'],
        'description': 'Comprehensive analysis of all AI lab biorisk evaluations. Maps evaluator landscape.',
    },
    {
        'id': 'pub_anthropic_frontier_red_team',
        'label': 'Progress from our Frontier Red Team (Anthropic)',
        'type': 'publication',
        'subtype': 'blog_post',
        'url': 'https://www.anthropic.com/news/strategic-warning-for-ai-risk-progress-and-insights-from-our-frontier-red-team',
        'date': '2025',
        'authors_orgs': ['Anthropic'],
        'description': 'Anthropic frontier red team: ~15 researchers. Claude now exceeds expert virologists on VCT.',
    },
    {
        'id': 'pub_nti_aixbio_forum_statement',
        'label': 'AIxBio Global Forum High-Level Statement on Biosecurity Risks',
        'type': 'publication',
        'subtype': 'policy_statement',
        'url': 'https://www.nti.org/about/programs-projects/project/aixbio-global-forum/',
        'date': '2024',
        'authors_orgs': ['Nuclear Threat Initiative'],
        'description': 'NTI convened 25+ high-level participants including Anthropic, Google DeepMind representatives.',
    },
    {
        'id': 'pub_futurehouse_lab_bench',
        'label': 'LAB-Bench: Measuring Capabilities of Language Models for Biology Research',
        'type': 'publication',
        'subtype': 'benchmark_paper',
        'url': 'https://arxiv.org/abs/2407.10362',
        'date': '2024-07',
        'authors_orgs': ['FutureHouse'],
        'description': '2,457 questions across 8 categories. Used by multiple AI labs for biorisk evaluation.',
    },
]

for pub in PUBLICATIONS:
    pub_id = pub['id']
    if pub_id not in existing_ids:
        node = {k: v for k, v in pub.items() if k != 'authors_orgs'}
        add_node(pub_id, pub['label'], pub['type'],
                 **{k: v for k, v in pub.items() if k not in ('id', 'label', 'type', 'authors_orgs')})
        print(f"+ NODE: {pub_id[:50]}...")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: KEY INDIVIDUAL NODES
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 3: Key Individual Nodes")
print("=" * 60)

INDIVIDUALS = [
    # SecureBio leadership
    {'id': 'author_ben_mueller', 'label': 'Ben Mueller', 'org': 'inst_SecureBio',
     'role': 'Executive Director', 'source': 'securebio.org/team/'},
    {'id': 'author_seth_donoughe', 'label': 'Seth Donoughe', 'org': 'inst_SecureBio',
     'role': 'Director of AI', 'source': 'securebio.org/team/'},
    {'id': 'author_jasper_gotting', 'label': 'Jasper Götting', 'org': 'inst_SecureBio',
     'role': 'Head of Research, AI', 'source': 'securebio.org/team/'},
    {'id': 'author_jeff_kaufman', 'label': 'Jeff Kaufman', 'org': 'inst_SecureBio',
     'role': 'Director of Detection', 'source': 'securebio.org/team/'},
    {'id': 'author_coleman_breen', 'label': 'Coleman Breen', 'org': 'inst_SecureBio',
     'role': 'Senior AI Policy Researcher', 'source': 'securebio.org/team/'},
    {'id': 'author_anjali_gopal', 'label': 'Anjali Gopal', 'org': 'inst_SecureBio',
     'role': 'Research Scientist & AI Project Co-Lead (past)', 'source': 'securebio.org/team/'},

    # Gryphon Scientific leadership
    {'id': 'author_rocco_casagrande', 'label': 'Rocco Casagrande', 'org': 'org_gryphon_scientific',
     'role': 'Founder and Executive Chairman', 'source': 'gryphon_deloitte_acquisition.md'},
    {'id': 'author_froggi_jackson', 'label': 'Shawn S. "Froggi" Jackson', 'org': 'org_gryphon_scientific',
     'role': 'Co-author on OpenAI bio threat study', 'source': 'gryphon_deloitte_acquisition.md'},
    {'id': 'author_daniel_greene', 'label': 'Daniel Greene', 'org': 'org_gryphon_scientific',
     'role': 'Senior Analyst', 'source': 'gryphon_deloitte_acquisition.md'},
    {'id': 'author_mark_kazmierczak', 'label': 'Mark Kazmierczak', 'org': 'org_gryphon_scientific',
     'role': 'Director of Biosafety, Biosecurity and Emerging Technologies', 'source': 'gryphon_deloitte_acquisition.md'},

    # RAND authors
    {'id': 'author_christopher_mouton', 'label': 'Christopher A. Mouton', 'org': 'inst_RAND_Corporation',
     'role': 'Lead author, RAND bio attack red-team study', 'source': 'rand.org'},
    {'id': 'author_caleb_lucas', 'label': 'Caleb Lucas', 'org': 'inst_RAND_Corporation',
     'role': 'Co-author, RAND bio attack red-team study', 'source': 'rand.org'},

    # OpenAI bio eval authors
    {'id': 'author_tejal_patwardhan', 'label': 'Tejal Patwardhan', 'org': 'inst_OpenAI',
     'role': 'Lead author, OpenAI bio threat early warning study', 'source': 'openai.com'},

    # NTI | bio leadership
    {'id': 'author_christine_parthemore', 'label': 'Christine Parthemore', 'org': 'org_council_strategic_risks',
     'role': 'CEO, Council on Strategic Risks; SecureBio Board', 'source': 'securebio.org/team/'},

    # Epoch AI
    {'id': 'org_epoch_ai', 'label': 'Epoch AI', 'org': None,
     'role': None, 'source': 'epoch.ai', 'is_org': True},
]

for ind in INDIVIDUALS:
    ind_id = ind['id']
    if ind.get('is_org'):
        add_node(ind_id, ind['label'], 'org',
                 url=f"https://{ind['source']}",
                 description='AI research institute tracking AI capabilities and safety evaluations')
        print(f"+ NODE (org): {ind_id}")
    else:
        # Check if person already exists
        existing = resolve_existing(ind['label'])
        if existing:
            print(f"  EXISTS: {ind['label']} → {existing}")
            continue
        add_node(ind_id, ind['label'], 'author',
                 subtype='evaluator',
                 description=ind['role'],
                 details={'source': ind['source']})
        print(f"+ NODE: {ind_id} ({ind['label']} @ {ind.get('org', 'N/A')})")

        # Add affiliation edge
        if ind['org']:
            org_target = ind['org']
            if org_target in existing_ids or org_target in nodes:
                edge_id = f"affil_s5_{ind_id}"
                add_edge(edge_id, ind_id, org_target, 'current_affiliation',
                         extraction_method='webpage_scrape',
                         data_source=ind['source'])
                print(f"  + EDGE: {ind['label']} → {org_target} (affiliation)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: BIOSECURITY EVALUATION EDGES
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 4: Biosecurity Evaluation Edges")
print("=" * 60)

# SecureBio evaluated these labs
SECUREBIO_EVALS = [
    {'lab': 'inst_Anthropic', 'models': 'Claude 3.7 Sonnet, Claude 4', 'confidence': 'HIGH',
     'source': 'securebio.substack.com', 'evidence_node': 'pub_securebio_biorisk_eval_overview'},
    {'lab': 'inst_OpenAI', 'models': 'GPT-4.5, o3-mini, o4-mini', 'confidence': 'HIGH',
     'source': 'securebio.substack.com', 'evidence_node': 'pub_securebio_biorisk_eval_overview'},
    {'lab': 'inst_Google_DeepMind', 'models': 'Gemini 2.5 Pro', 'confidence': 'HIGH',
     'source': 'securebio.substack.com', 'evidence_node': 'pub_securebio_biorisk_eval_overview'},
    {'lab': 'inst_xAI', 'models': 'unspecified', 'confidence': 'MEDIUM',
     'source': 'securebio.substack.com', 'evidence_node': 'pub_securebio_biorisk_eval_overview'},
]

for eval_item in SECUREBIO_EVALS:
    lab_id = eval_item['lab']
    edge_id = f"eval_securebio_{lab_id}"
    lab_label = node_by_id.get(lab_id, {}).get('label', '') or nodes.get(lab_id, {}).get('label', lab_id)
    add_edge(edge_id, 'inst_SecureBio', lab_id, 'biosecurity_eval',
             models_evaluated=eval_item['models'],
             confidence=eval_item['confidence'],
             extraction_method='blog_post',
             data_source=eval_item['source'],
             evidence_node=eval_item['evidence_node'])
    print(f"+ EDGE: SecureBio → {lab_label} (biosecurity_eval, {eval_item['confidence']})")

# Gryphon Scientific evaluated OpenAI
add_edge('eval_gryphon_openai', 'org_gryphon_scientific', 'inst_OpenAI', 'biosecurity_eval',
         models_evaluated='GPT-4',
         confidence='HIGH',
         extraction_method='blog_post',
         data_source='openai.com',
         evidence_node='pub_openai_bio_early_warning_2024')
print("+ EDGE: Gryphon Scientific → OpenAI (biosecurity_eval, HIGH)")

# UK AISI evaluated Anthropic and OpenAI
add_edge('eval_uk_aisi_anthropic', uk_aisi_id, 'inst_Anthropic', 'biosecurity_eval',
         models_evaluated='Claude 3.5 Sonnet',
         confidence='HIGH',
         extraction_method='news_article',
         data_source='fedscoop.com',
         evidence_node='pub_epoch_biorisk_eval_analysis')
print("+ EDGE: UK AISI → Anthropic (biosecurity_eval, HIGH)")

add_edge('eval_uk_aisi_openai', uk_aisi_id, 'inst_OpenAI', 'biosecurity_eval',
         models_evaluated='o1',
         confidence='HIGH',
         extraction_method='news_article',
         data_source='epoch.ai',
         evidence_node='pub_epoch_biorisk_eval_analysis')
print("+ EDGE: UK AISI → OpenAI (biosecurity_eval, HIGH)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: PUBLICATION → ORGANIZATION EDGES (authored)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 5: Publication → Organization Edges")
print("=" * 60)

PUB_AUTHOR_MAP = [
    # OpenAI + Gryphon bio study
    ('pub_openai_bio_early_warning_2024', 'inst_OpenAI'),
    ('pub_openai_bio_early_warning_2024', 'org_gryphon_scientific'),
    ('pub_openai_bio_early_warning_2024', 'author_tejal_patwardhan'),
    ('pub_openai_bio_early_warning_2024', 'author_rocco_casagrande'),
    ('pub_openai_bio_early_warning_2024', 'author_froggi_jackson'),
    # RAND studies
    ('pub_rand_bio_attack_redteam_2024', 'inst_RAND_Corporation'),
    ('pub_rand_bio_attack_redteam_2024', 'author_christopher_mouton'),
    ('pub_rand_bio_attack_redteam_2024', 'author_caleb_lucas'),
    ('pub_rand_automated_grading_2025', 'inst_RAND_Corporation'),
    # SecureBio publications
    ('pub_securebio_ostp_rfi_2025', 'inst_SecureBio'),
    ('pub_securebio_biorisk_eval_overview', 'inst_SecureBio'),
    # Anthropic publication
    ('pub_anthropic_frontier_red_team', 'inst_Anthropic'),
    # NTI
    ('pub_nti_aixbio_forum_statement', 'org_nuclear_threat_initiative'),
    # Epoch AI
    ('pub_epoch_biorisk_eval_analysis', 'org_epoch_ai'),
    # FutureHouse
    ('pub_futurehouse_lab_bench', 'org_futurehouse'),
]

# Resolve FutureHouse
fh_id = resolve_existing('FutureHouse')
if not fh_id:
    fh_id = 'org_futurehouse'
    add_node(fh_id, 'FutureHouse', 'org',
             url='https://www.futurehouse.org',
             description='AI research org; created LAB-Bench biology benchmark')
    print(f"+ NODE: {fh_id}")
else:
    print(f"  EXISTS: FutureHouse → {fh_id}")

for pub_id, author_id in PUB_AUTHOR_MAP:
    # Adjust FutureHouse reference
    if author_id == 'org_futurehouse':
        author_id = fh_id

    # Check both exist
    source_exists = pub_id in existing_ids or pub_id in nodes
    target_exists = author_id in existing_ids or author_id in nodes
    if not source_exists:
        print(f"  WARN: pub {pub_id} not found")
        continue
    if not target_exists:
        print(f"  WARN: author/org {author_id} not found")
        continue

    edge_id = f"authored_s5_{pub_id}_{author_id}"
    # Use 'authored' type — author → publication direction
    # But for orgs, it's more like "published_by"
    add_edge(edge_id, author_id, pub_id, 'authored',
             extraction_method='webpage_scrape',
             data_source='s5_evidence')
    author_label = node_by_id.get(author_id, {}).get('label', '') or nodes.get(author_id, {}).get('label', author_id)
    pub_label_short = (node_by_id.get(pub_id, {}).get('label', '') or nodes.get(pub_id, {}).get('label', pub_id))[:50]
    print(f"+ EDGE: {author_label} → {pub_label_short}... (authored)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: POLICY FORUM EDGES
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 6: Policy Forum Edges")
print("=" * 60)

# NTI AIxBio Forum participants
NTI_FORUM_PARTICIPANTS = [
    'inst_Anthropic',
    'inst_Google_DeepMind',
    'inst_RAND_Corporation',
]

nti_id = 'org_nuclear_threat_initiative'
for participant_id in NTI_FORUM_PARTICIPANTS:
    edge_id = f"forum_nti_{participant_id}"
    p_label = node_by_id.get(participant_id, {}).get('label', participant_id)
    add_edge(edge_id, nti_id, participant_id, 'policy_forum',
             activity='AIxBio Global Forum',
             confidence='MEDIUM',
             extraction_method='webpage_scrape',
             data_source='nti.org',
             evidence_node='pub_nti_aixbio_forum_statement')
    print(f"+ EDGE: NTI → {p_label} (policy_forum)")

# SecureBio → OSTP (policy submission)
add_edge('policy_securebio_ostp', 'inst_SecureBio', ostp_id, 'policy_forum',
         activity='RFI Response: AI Action Plan',
         confidence='HIGH',
         extraction_method='pdf_parse',
         data_source='files.nitrd.gov',
         evidence_node='pub_securebio_ostp_rfi_2025')
print("+ EDGE: SecureBio → OSTP (policy_forum)")

# SecureBio recommends empowering US AISI
add_edge('policy_securebio_us_aisi', 'inst_SecureBio', us_aisi_id, 'policy_forum',
         activity='Recommends empowering US AISI for AI evaluation',
         confidence='HIGH',
         extraction_method='pdf_parse',
         data_source='files.nitrd.gov',
         evidence_node='pub_securebio_ostp_rfi_2025')
print(f"+ EDGE: SecureBio → US AISI (policy_forum)")

# NTI + RAND co-organized Paris summit
add_edge('collab_nti_rand_paris', nti_id, 'inst_RAND_Corporation', 'policy_forum',
         activity='Co-organized AIxBio session at Paris AI Action Summit (Feb 2025)',
         confidence='HIGH',
         extraction_method='webpage_scrape',
         data_source='nti.org')
print("+ EDGE: NTI → RAND (policy_forum, Paris AI Summit)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: ORGANIZATIONAL RELATIONSHIP EDGES
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 7: Organizational Relationships")
print("=" * 60)

# Deloitte acquired Gryphon Scientific
add_edge('acquired_deloitte_gryphon', deloitte_id, 'org_gryphon_scientific', 'funds',
         description='Deloitte acquired Gryphon Scientific assets (April 2024)',
         confidence='HIGH',
         extraction_method='news_article',
         data_source='prnewswire.com')
print("+ EDGE: Deloitte → Gryphon Scientific (acquisition)")

# Christine Parthemore: SecureBio board + Council on Strategic Risks CEO
add_edge('board_parthemore_securebio', 'author_christine_parthemore', 'inst_SecureBio', 'current_affiliation',
         description='Board of Directors',
         extraction_method='webpage_scrape',
         data_source='securebio.org/team/')
print("+ EDGE: Christine Parthemore → SecureBio (board)")

# SecureBio co-developed virology tasks with Signature Science and Deloitte
add_edge('collab_securebio_sigsci', 'inst_SecureBio', sig_sci_id, 'biosecurity_eval',
         description='Co-developed long-form virology evaluation tasks',
         confidence='HIGH',
         extraction_method='blog_post',
         data_source='securebio.substack.com')
print(f"+ EDGE: SecureBio → Signature Science (co-developed eval tasks)")

add_edge('collab_securebio_deloitte', 'inst_SecureBio', deloitte_id, 'biosecurity_eval',
         description='Co-developed long-form virology evaluation tasks for Claude 4',
         confidence='HIGH',
         extraction_method='blog_post',
         data_source='securebio.substack.com')
print(f"+ EDGE: SecureBio → Deloitte (co-developed eval tasks)")

# Kevin Esvelt → SecureBio (he's listed as past member / founder)
esvelt_id = 'author_Kevin_M__Esvelt1'
if esvelt_id in existing_ids:
    add_edge('affil_esvelt_securebio_past', esvelt_id, 'inst_SecureBio', 'past_affiliation',
             description='Founder / Past Member',
             extraction_method='webpage_scrape',
             data_source='securebio.org/team/')
    print(f"+ EDGE: Kevin Esvelt → SecureBio (past_affiliation)")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8: PUBLISHED STUDY EDGES (RAND)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 8: Published Study Edges")
print("=" * 60)

# RAND studied multiple LLMs (published_study to the labs whose models they tested)
add_edge('study_rand_openai', 'inst_RAND_Corporation', 'inst_OpenAI', 'published_study',
         description='Tested OpenAI models in bio attack red-team study',
         confidence='HIGH',
         extraction_method='publication',
         data_source='rand.org',
         evidence_node='pub_rand_bio_attack_redteam_2024')
print("+ EDGE: RAND → OpenAI (published_study)")

# FutureHouse LAB-Bench used by multiple labs
add_edge('study_futurehouse_benchmark', fh_id, 'inst_Anthropic', 'biosecurity_eval',
         description='LAB-Bench benchmark used in Anthropic biorisk evaluation',
         confidence='MEDIUM',
         extraction_method='publication',
         data_source='epoch.ai',
         evidence_node='pub_futurehouse_lab_bench')
print("+ EDGE: FutureHouse → Anthropic (biosecurity_eval via LAB-Bench)")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SPRINT 5 EXTRACTION SUMMARY")
print("=" * 60)

new_nodes_list = list(nodes.values())
print(f"New nodes: {len(new_nodes_list)}")
for ntype, count in sorted(defaultdict(int, {n['type']: sum(1 for nn in new_nodes_list if nn['type'] == n['type']) for n in new_nodes_list}).items()):
    print(f"  {ntype}: {count}")

print(f"New edges: {len(edges)}")
edge_type_counts = defaultdict(int)
for e in edges:
    edge_type_counts[e['type']] += 1
for etype, count in sorted(edge_type_counts.items()):
    print(f"  {etype}: {count}")

# Save staged files
with open(os.path.join(STAGED_DIR, 's5_nodes.json'), 'w') as f:
    json.dump(new_nodes_list, f, indent=2)

with open(os.path.join(STAGED_DIR, 's5_edges.json'), 'w') as f:
    json.dump(edges, f, indent=2)

print(f"\nSaved to data/staged/s5_nodes.json ({len(new_nodes_list)} nodes)")
print(f"Saved to data/staged/s5_edges.json ({len(edges)} edges)")

# ── MERGE ────────────────────────────────────────────────────────────────────
print("\n--- MERGING INTO GRAPH ---")

graph['nodes'].extend(new_nodes_list)
graph['edges'].extend(edges)

with open(GRAPH_FILE, 'w') as f:
    json.dump(graph, f, indent=2)

total_nodes = len(graph['nodes'])
total_edges = len(graph['edges'])
print(f"Merged: {total_nodes} nodes, {total_edges} edges")
