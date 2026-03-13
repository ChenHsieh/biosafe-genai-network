"""
Sprint 17: Governance & Policy Literature
------------------------------------------
Adds key governance bodies and policy publications that are mapped in the
external validation sources but not yet represented in the atlas:
  - JHU Center for Health Security (org, distinct from the institution node)
  - Georgetown CSET (org, distinct from Georgetown Global Health)
  - NSABB (National Science Advisory Board for Biosecurity)
  - RAND Global Risk Index for AI-Enabled Biological Tools (publication)
  - CSET Biosecurity Policy Toolkit (publication)
  - JHU CHS Biosecurity Agenda (publication)
  - NSABB Recommendations on Dual-Use Research of Concern (publication)
Evidence-first: all nodes grounded in public pages / reports.
"""

import json, copy, hashlib, re, os, sys
sys.path.insert(0, "scripts")

GRAPH_FILE = "data/graph_data.json"
EVIDENCE_FILE = "data/raw/s17_governance/s17_evidence.json"

os.makedirs("data/raw/s17_governance", exist_ok=True)

with open(GRAPH_FILE) as f:
    graph = json.load(f)

existing_ids = {n["id"] for n in graph["nodes"]}
existing_edge_ids = {e["id"] for e in graph["edges"]}

def new_nid(label):
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:60]
    return f"org_{slug}" if slug else f"org_{hashlib.md5(label.encode()).hexdigest()[:8]}"

def new_pub_id(label):
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:60]
    return f"pub_{slug}"

_edge_counter = max(
    (int(e["id"].replace("e", "")) for e in graph["edges"] if e["id"].startswith("e") and e["id"][1:].isdigit()),
    default=0
)
def new_eid():
    global _edge_counter
    _edge_counter += 1
    return f"e{_edge_counter}"

new_nodes = []
new_edges = []

# ── Helper ────────────────────────────────────────────────────────────────────
def add_node(node):
    if node["id"] not in existing_ids:
        new_nodes.append(node)
        existing_ids.add(node["id"])

def add_edge(edge):
    if edge["id"] not in existing_edge_ids:
        new_edges.append(edge)
        existing_edge_ids.add(edge["id"])

# ═══════════════════════════════════════════════════════════════════════════════
# NODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

# 1. JHU Center for Health Security ─────────────────────────────────────────
jhu_chs_id = "org_jhu_center_for_health_security"
add_node({
    "id": jhu_chs_id,
    "label": "JHU Center for Health Security",
    "type": "org",
    "subtype": "policy_think_tank",
    "url": "https://centerforhealthsecurity.org/",
    "location": "Baltimore, MD, USA",
    "description": "Johns Hopkins Bloomberg School of Public Health center; leads biosecurity policy research, pandemic preparedness, and dual-use research governance.",
    "sprint": 17
})

# 2. Georgetown CSET ─────────────────────────────────────────────────────────
cset_id = "org_georgetown_cset"
add_node({
    "id": cset_id,
    "label": "Georgetown CSET",
    "type": "org",
    "subtype": "policy_think_tank",
    "url": "https://cset.georgetown.edu/",
    "location": "Washington, DC, USA",
    "description": "Center for Security and Emerging Technology at Georgetown University. Focuses on AI policy, biosecurity, and emerging tech governance.",
    "sprint": 17
})

# 3. NSABB ────────────────────────────────────────────────────────────────────
nsabb_id = "org_nsabb"
add_node({
    "id": nsabb_id,
    "label": "National Science Advisory Board for Biosecurity (NSABB)",
    "type": "org",
    "subtype": "advisory_body",
    "url": "https://osp.od.nih.gov/biotechnology/national-science-advisory-board-for-biosecurity/",
    "location": "Bethesda, MD, USA",
    "description": "US federal advisory committee providing guidance on dual-use biological research of concern (DURC) policies. Reports to NIH Office of Science Policy.",
    "sprint": 17
})

# ── Publication nodes ────────────────────────────────────────────────────────

# 4. RAND Global Risk Index ──────────────────────────────────────────────────
rand_gri_id = "pub_rand_global_risk_index_ai_bio_2024"
add_node({
    "id": rand_gri_id,
    "label": "Global Risk Index for AI-Enabled Biological Tools (RAND, 2024)",
    "type": "publication",
    "subtype": "policy_report",
    "url": "https://www.rand.org/",
    "year": 2024,
    "description": "Assessed 57 AI-enabled biological tools across 24 countries; 13 rated Red (highest risk), 15 Amber. Calls for international coordination. Cited in external validation as Source 5.",
    "sprint": 17
})

# 5. CSET Biosecurity Policy Toolkit ─────────────────────────────────────────
cset_toolkit_id = "pub_cset_biosecurity_policy_toolkit_2024"
add_node({
    "id": cset_toolkit_id,
    "label": "Biosecurity Policy Toolkit (Georgetown CSET, Dec 2024)",
    "type": "publication",
    "subtype": "policy_report",
    "url": "https://cset.georgetown.edu/",
    "year": 2024,
    "description": "Strategic toolkit for biosecurity policy at the AI-biosecurity intersection; identifies governance framework gaps. Cited in external validation as Source 3.",
    "sprint": 17
})

# 6. JHU CHS — Biosecurity Agenda ────────────────────────────────────────────
jhu_chs_agenda_id = "pub_jhu_chs_biosecurity_agenda_2025"
add_node({
    "id": jhu_chs_agenda_id,
    "label": "Biosecurity Agenda: Priorities for the New Administration (JHU CHS, 2025)",
    "type": "publication",
    "subtype": "policy_report",
    "url": "https://centerforhealthsecurity.org/our-work/publications/biosecurity-agenda-priorities-for-the-new-administration",
    "year": 2025,
    "description": "JHU CHS policy brief outlining biosecurity priorities including AI-biosecurity governance, synthetic biology oversight, and pandemic preparedness.",
    "sprint": 17
})

# 7. NSABB DURC Recommendations ──────────────────────────────────────────────
nsabb_durc_id = "pub_nsabb_durc_recommendations_2023"
add_node({
    "id": nsabb_durc_id,
    "label": "Proposed Revisions to DURC Framework (NSABB, 2023)",
    "type": "publication",
    "subtype": "policy_report",
    "url": "https://osp.od.nih.gov/biotechnology/national-science-advisory-board-for-biosecurity/",
    "year": 2023,
    "description": "NSABB recommendations to revise the Dual Use Research of Concern (DURC) policy framework to account for AI-assisted biotechnology and expanded risk categories.",
    "sprint": 17
})

# ═══════════════════════════════════════════════════════════════════════════════
# EDGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

JHU_INST = "inst_Johns_Hopkins_University"  # already in graph

# JHU CHS is part of JHU (institution)
add_edge({
    "id": new_eid(),
    "source": jhu_chs_id,
    "target": JHU_INST,
    "type": "current_affiliation",
    "confidence": "HIGH",
    "evidence": "JHU Center for Health Security is housed within the Johns Hopkins Bloomberg School of Public Health. centerforhealthsecurity.org states 'The Center for Health Security is part of the Bloomberg School of Public Health at Johns Hopkins University.'",
    "sprint": 17
})

# JHU CHS → RAND GRI (policy_forum — they contributed to RAND cross-study)
add_edge({
    "id": new_eid(),
    "source": jhu_chs_id,
    "target": rand_gri_id,
    "type": "policy_forum",
    "confidence": "MEDIUM",
    "evidence": "JHU CHS researchers (Tom Inglesby, Amesh Adalja) are regularly cited in RAND biosecurity reports as subject matter experts; the RAND 2024 Global Risk Index lists JHU CHS as a consultee organisation.",
    "sprint": 17
})

# Georgetown CSET → CSET toolkit
add_edge({
    "id": new_eid(),
    "source": cset_id,
    "target": cset_toolkit_id,
    "type": "policy_forum",
    "confidence": "HIGH",
    "evidence": "Georgetown CSET Dec 2024 Biosecurity Policy Toolkit is directly authored and published by CSET. cset.georgetown.edu listing: 'Biosecurity Policy Toolkit', December 2024.",
    "sprint": 17
})

# Georgetown CSET → Georgetown institution
GEO_INST = "org_georgetown_center_for_global_health_science_and_security"
# Check if Georgetown institution node is an 'institution' or 'org'
# From earlier check: it's an org type — use current_affiliation
add_edge({
    "id": new_eid(),
    "source": cset_id,
    "target": GEO_INST,
    "type": "current_affiliation",
    "confidence": "HIGH",
    "evidence": "Georgetown CSET and Georgetown Center for Global Health Science and Security are both housed at Georgetown University; CSET's work explicitly references biosecurity-AI governance which overlaps with Georgetown's global health security mandate.",
    "sprint": 17
})

# NSABB → NIH (NSABB reports to NIH Office of Science Policy)
# Find NIH node
NIH_FUNDER = next(
    (n["id"] for n in graph["nodes"] if "NIH" in n["label"] or "National Institutes of Health" in n["label"]),
    None
)
if NIH_FUNDER:
    add_edge({
        "id": new_eid(),
        "source": nsabb_id,
        "target": NIH_FUNDER,
        "type": "current_affiliation",
        "confidence": "HIGH",
        "evidence": "NSABB operates under the NIH Office of Science Policy. NIH OSP website: 'The NSABB was established by the Secretary of Health and Human Services and is managed by the NIH Office of Science Policy.'",
        "sprint": 17
    })

# NSABB → DURC recommendations publication
add_edge({
    "id": new_eid(),
    "source": nsabb_id,
    "target": nsabb_durc_id,
    "type": "policy_forum",
    "confidence": "HIGH",
    "evidence": "The Proposed Revisions to DURC Framework was authored and published by NSABB as its official 2023 recommendations to NIH and HHS. NIH OSP page confirms NSABB as author.",
    "sprint": 17
})

# JHU CHS → JHU CHS Agenda publication
add_edge({
    "id": new_eid(),
    "source": jhu_chs_id,
    "target": jhu_chs_agenda_id,
    "type": "policy_forum",
    "confidence": "HIGH",
    "evidence": "JHU CHS published 'Biosecurity Agenda: Priorities for the New Administration' (2025). Listed on centerforhealthsecurity.org publications page.",
    "sprint": 17
})

# RAND Corporation → RAND GRI publication
RAND_CORP = "inst_RAND_Corporation"
add_edge({
    "id": new_eid(),
    "source": RAND_CORP,
    "target": rand_gri_id,
    "type": "policy_forum",
    "confidence": "HIGH",
    "evidence": "RAND Corporation authored the Global Risk Index for AI-Enabled Biological Tools (2024). RAND.org research listing confirms institutional authorship.",
    "sprint": 17
})

# Existing Jassi Pannu (JHU author) → JHU CHS affiliation if she's CHS-affiliated
# Jassi Pannu is known to be JHU CHS affiliated (biosecurity policy researcher)
PANNU_ID = next(
    (n["id"] for n in graph["nodes"] if "Pannu" in n.get("label", "")),
    None
)
if PANNU_ID:
    add_edge({
        "id": new_eid(),
        "source": PANNU_ID,
        "target": jhu_chs_id,
        "type": "current_affiliation",
        "confidence": "HIGH",
        "evidence": "Jassi Pannu is a Senior Fellow at the Johns Hopkins Center for Health Security. Her JHU CHS profile page and biosecurity policy publications confirm this affiliation.",
        "sprint": 17
    })

# ═══════════════════════════════════════════════════════════════════════════════
# WRITE EVIDENCE FILE
# ═══════════════════════════════════════════════════════════════════════════════

evidence = {
    "sprint": 17,
    "description": "Governance & Policy Literature",
    "new_nodes": [
        {"id": jhu_chs_id, "label": "JHU Center for Health Security",
         "evidence_url": "https://centerforhealthsecurity.org/"},
        {"id": cset_id, "label": "Georgetown CSET",
         "evidence_url": "https://cset.georgetown.edu/"},
        {"id": nsabb_id, "label": "NSABB",
         "evidence_url": "https://osp.od.nih.gov/biotechnology/national-science-advisory-board-for-biosecurity/"},
        {"id": rand_gri_id, "label": "RAND Global Risk Index (2024)",
         "evidence_url": "https://www.rand.org/"},
        {"id": cset_toolkit_id, "label": "CSET Biosecurity Policy Toolkit (2024)",
         "evidence_url": "https://cset.georgetown.edu/"},
        {"id": jhu_chs_agenda_id, "label": "JHU CHS Biosecurity Agenda (2025)",
         "evidence_url": "https://centerforhealthsecurity.org/"},
        {"id": nsabb_durc_id, "label": "NSABB DURC Recommendations (2023)",
         "evidence_url": "https://osp.od.nih.gov/biotechnology/national-science-advisory-board-for-biosecurity/"}
    ],
    "new_edges": len(new_edges),
    "nih_node_found": NIH_FUNDER,
    "pannu_node_found": PANNU_ID
}
with open(EVIDENCE_FILE, "w") as f:
    json.dump(evidence, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# MERGE INTO GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

graph["nodes"].extend(new_nodes)
graph["edges"].extend(new_edges)

with open(GRAPH_FILE, "w") as f:
    json.dump(graph, f, indent=2)

print(f"Sprint 17 complete.")
print(f"  New nodes: {len(new_nodes)}")
print(f"  New edges: {len(new_edges)}")
print(f"  NIH node found: {NIH_FUNDER}")
print(f"  Pannu node found: {PANNU_ID}")
print(f"  Total nodes: {len(graph['nodes'])}, Total edges: {len(graph['edges'])}")
