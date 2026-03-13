"""
Sprint 15: Global South & International Coverage
Add Africa CDC, SynBio Africa, Brown Pandemic Center; 
link to NTI AIxBio via CEPI partnership and Munich 2025 declaration
"""
import json, os

BASE = "/sessions/eloquent-jolly-knuth/mnt/biosafe-genai-network"

with open(f"{BASE}/data/graph_data.json") as f:
    g = json.load(f)

nodes = g["nodes"]
edges = g["edges"]
node_ids = {n["id"] for n in nodes}
node_by_label = {n["label"].lower(): n["id"] for n in nodes}

max_eid = 0
for e in edges:
    eid = e.get("id", "")
    if eid.startswith("edge_"):
        parts = eid.split("_")
        if len(parts) >= 2:
            try: max_eid = max(max_eid, int(parts[1]))
            except: pass

def new_eid():
    global max_eid
    max_eid += 1
    return f"edge_{max_eid}"

new_nodes = []
new_edges = []
log = []

# ── ORG NODES ────────────────────────────────────────────────────

# 1. Africa CDC
if "org_africa_cdc" not in node_ids:
    new_nodes.append({
        "id": "org_africa_cdc",
        "label": "Africa CDC",
        "type": "org",
        "subtype": "org",
        "url": "https://africacdc.org",
        "country": "ET",  # HQ in Addis Ababa
        "description": "Africa Centres for Disease Control and Prevention; AU agency; spearheads Africa Biosafety and Biosecurity Initiative + Digital Transformation Strategy ('AI for Health in Africa'); Africa Pathogen Genomic Initiative uses AI for outbreak detection. January 2024: Africa Center for Epidemic Resilience in Dakar certified as Center of Excellence in Biosafety and Biosecurity.",
        "details": {"Website": "https://africacdc.org", "Country": "ET", "Founded": 2017, "Source": "news-medical.net Oct 2025; Addis Ababa workshop March 2024"}
    })
    log.append("ADD ORG: Africa CDC")

# 2. SynBio Africa
if "org_synbio_africa" not in node_ids:
    new_nodes.append({
        "id": "org_synbio_africa",
        "label": "SynBio Africa",
        "type": "org",
        "subtype": "org",
        "url": "https://synbioafrica.com",
        "country": "NG",  # Nigeria-based
        "description": "African synthetic biology network; co-sponsor of NTI 2024 Next Generation for Biosecurity Competition; promotes responsible biosafety/biosecurity practices across African SynBio community",
        "details": {"Website": "https://synbioafrica.com", "Country": "NG", "Source": "NTI Next Generation Biosecurity Competition 2024 co-sponsors list"}
    })
    log.append("ADD ORG: SynBio Africa")

# 3. Brown Pandemic Center (Brown University)
if "org_brown_pandemic_center" not in node_ids:
    new_nodes.append({
        "id": "org_brown_pandemic_center",
        "label": "Brown Pandemic Center",
        "type": "org",
        "subtype": "org",
        "url": "https://www.brown.edu/academics/public-health/pandemic-center",
        "country": "US",
        "description": "Brown University School of Public Health Pandemic Center; co-convened Munich Security Conference 2025 Rising Biosecurity Leaders from Global South event with CEPI and NTI; co-signed Biosecurity Rising Leaders' Munich Declaration",
        "details": {"Website": "https://brown.edu", "Country": "US", "Source": "NTI news Feb 2025: CEPI, Brown, NTI partner at Munich Security Conference"}
    })
    log.append("ADD ORG: Brown Pandemic Center")

# 4. iGEM Foundation (already may be in graph from Coefficient grants)
# Check
igem_id = node_by_label.get("igem foundation") or node_by_label.get("igem")
if not igem_id and "org_igem_foundation" not in node_ids:
    new_nodes.append({
        "id": "org_igem_foundation",
        "label": "iGEM Foundation",
        "type": "org",
        "subtype": "org",
        "url": "https://igem.org",
        "country": "US",
        "description": "International Genetically Engineered Machine Foundation; global SynBio community with strong Global South representation; co-sponsor of NTI Next Generation Biosecurity Competition 2024",
        "details": {"Website": "https://igem.org", "Country": "US", "Source": "NTI competition co-sponsors 2024"}
    })
    log.append("ADD ORG: iGEM Foundation")
    igem_id = "org_igem_foundation"

# ── PUBLICATION NODE ─────────────────────────────────────────────

# NTI Global South AI-Biosecurity article (2024) — already referenced in sources
# Link to existing NTI org node
nti_id = node_by_label.get("nuclear threat initiative") or node_by_label.get("nti")
if not nti_id:
    # Check for NTI by searching org nodes
    nti_nodes = [n for n in nodes if 'nti' in n.get('id', '').lower() or 'nuclear threat' in n['label'].lower()]
    if nti_nodes:
        nti_id = nti_nodes[0]['id']

print("NTI ID:", nti_id)

nti_global_south_pub_id = "pub_nti_global_south_ai_biosecurity_2024"
if nti_global_south_pub_id not in node_ids:
    new_nodes.append({
        "id": nti_global_south_pub_id,
        "label": "Exploring AI-Biosecurity Governance in the Global South (NTI, 2024)",
        "type": "publication",
        "subtype": "research_report",
        "url": "https://www.nti.org/risky-business/exploring-ai-biosecurity-governance-in-the-global-south/",
        "year": 2024,
        "description": "NTI analysis finding only 27% of Global South countries have national AI strategies, none of which address biosecurity implications. Identifies governance gap and calls for inclusion of Global South in AI-biosecurity frameworks.",
        "details": {"Source": "NTI Risky Business blog 2024", "Key_finding": "0% of Global South AI strategies address biosecurity"}
    })
    log.append("ADD PUB: NTI Global South AI-Biosecurity 2024")

# Munich Declaration publication node
munich_pub_id = "pub_munich_biosecurity_declaration_2025"
if munich_pub_id not in node_ids:
    new_nodes.append({
        "id": munich_pub_id,
        "label": "Biosecurity Rising Leaders' Munich Declaration (CEPI/Brown/NTI, 2025)",
        "type": "publication",
        "subtype": "research_report",
        "url": "https://www.nti.org/news/cepi-brown-nti-partner-with-rising-leaders-to-take-biological-threats-off-the-table/",
        "year": 2025,
        "description": "Declaration signed at Munich Security Conference Feb 2025 by Global South biosecurity rising leaders; convened by CEPI, Brown University Pandemic Center, and NTI; calls for taking biological threats off the table through Global South leadership.",
        "details": {"Source": "NTI news Feb 2025", "Event": "Munich Security Conference 2025"}
    })
    log.append("ADD PUB: Munich Biosecurity Declaration 2025")

# ── EDGES ────────────────────────────────────────────────────────

# NTI policy_forum → NTI Global South pub (if NTI node exists)
if nti_id:
    new_edges.append({
        "id": new_eid(),
        "source": nti_id,
        "target": nti_global_south_pub_id,
        "type": "policy_forum",
        "evidence": "NTI published this analysis through their Risky Business publication series (nti.org)"
    })
    log.append(f"ADD EDGE: NTI → Global South pub (policy_forum)")
    
    new_edges.append({
        "id": new_eid(),
        "source": nti_id,
        "target": munich_pub_id,
        "type": "policy_forum",
        "evidence": "NTI co-convened Munich Security Conference 2025 event with CEPI and Brown"
    })
    log.append("ADD EDGE: NTI → Munich Declaration pub (policy_forum)")
else:
    log.append("WARN: NTI node not found — skipping NTI edges")

# CEPI → Munich Declaration
cepi_id = "org_cepi"
if cepi_id in node_ids:
    new_edges.append({
        "id": new_eid(),
        "source": cepi_id,
        "target": munich_pub_id,
        "type": "policy_forum",
        "evidence": "CEPI co-convened Munich Security Conference 2025 Biosecurity Rising Leaders event with NTI and Brown"
    })
    log.append("ADD EDGE: CEPI → Munich Declaration (policy_forum)")

# Brown Pandemic Center → Munich Declaration
new_edges.append({
    "id": new_eid(),
    "source": "org_brown_pandemic_center",
    "target": munich_pub_id,
    "type": "policy_forum",
    "evidence": "Brown University Pandemic Center co-convened Munich Security Conference 2025 Biosecurity Rising Leaders event"
})
log.append("ADD EDGE: Brown Pandemic Center → Munich Declaration (policy_forum)")

# Africa CDC → NTI Global South pub (Africa CDC is a key subject/stakeholder)
new_edges.append({
    "id": new_eid(),
    "source": "org_africa_cdc",
    "target": nti_global_south_pub_id,
    "type": "policy_forum",
    "evidence": "Africa CDC's biosecurity and AI programs are directly relevant to NTI's Global South AI biosecurity governance analysis; Africa CDC participates in international biosecurity governance frameworks"
})
log.append("ADD EDGE: Africa CDC → NTI Global South pub (policy_forum)")

# SynBio Africa → NTI Global South pub
new_edges.append({
    "id": new_eid(),
    "source": "org_synbio_africa",
    "target": nti_global_south_pub_id,
    "type": "policy_forum",
    "evidence": "SynBio Africa co-sponsored NTI 2024 Next Generation Biosecurity Competition; engaged with same governance community"
})
log.append("ADD EDGE: SynBio Africa → NTI Global South pub (policy_forum)")

# iGEM Foundation connections (if added)
if igem_id and igem_id != node_by_label.get("igem foundation"):
    # New node, needs connection
    # iGEM co-sponsored NTI competition → link to NTI Global South pub
    new_edges.append({
        "id": new_eid(),
        "source": igem_id,
        "target": nti_global_south_pub_id,
        "type": "policy_forum",
        "evidence": "iGEM Foundation co-sponsored NTI 2024 Next Generation Biosecurity Competition focusing on global equity in biosecurity"
    })
    log.append("ADD EDGE: iGEM → NTI Global South pub (policy_forum)")

# ── SAVE EVIDENCE ────────────────────────────────────────────────
evidence = {
    "sprint": 15,
    "date": "2026-03-12",
    "key_finding_confirmed": "NTI 2024: 0% of Global South AI strategies address biosecurity; Munich 2025 Declaration by rising leaders from Global South",
    "sources": [
        {"url": "https://www.nti.org/risky-business/exploring-ai-biosecurity-governance-in-the-global-south/", "evidence": "NTI analysis: 27% of Global South countries have AI strategies, none address biosecurity"},
        {"url": "https://www.nti.org/news/cepi-brown-nti-partner-with-rising-leaders-to-take-biological-threats-off-the-table/", "evidence": "CEPI, Brown, NTI convened Munich Security Conference 2025 Biosecurity Rising Leaders Declaration"},
        {"url": "https://www.news-medical.net/news/20251027/Africa-CDCe28099s-vision-for-AI-driven-primary-health-care-and-self-reliance.aspx", "evidence": "Africa CDC AI for Health strategy + Biosafety and Biosecurity Initiative"},
        {"url": "https://www.nti.org/news/introducing-the-winners-of-the-2024-next-generation-for-biosecurity-competition/", "evidence": "SynBio Africa, iGEM Foundation co-sponsored NTI 2024 competition from 19 countries"}
    ],
    "new_nodes": [n["id"] for n in new_nodes],
    "new_edges": [{"id": e["id"], "source": e["source"], "target": e["target"], "type": e["type"]} for e in new_edges]
}

with open(f"{BASE}/data/raw/s15_global_south/s15_evidence.json", "w") as f:
    json.dump(evidence, f, indent=2)

# ── MERGE ────────────────────────────────────────────────────────
nodes.extend(new_nodes)
edges.extend(new_edges)
g["nodes"] = nodes
g["edges"] = edges
with open(f"{BASE}/data/graph_data.json", "w") as f:
    json.dump(g, f, separators=(",", ":"))

print(f"Sprint 15 complete:")
print(f"  New nodes: {len(new_nodes)}")
print(f"  New edges: {len(new_edges)}")
print(f"  Total nodes: {len(nodes)}")
print(f"  Total edges: {len(edges)}")
for item in log:
    print(" ", item)
