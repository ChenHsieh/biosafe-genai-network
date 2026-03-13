"""
Sprint 16: Protein Design Safety Research Mapping
Add David Baker, Institute for Protein Design (UW), EvolutionaryScale org,
and key protein design biosecurity publications
"""
import json

BASE = "/sessions/eloquent-jolly-knuth/mnt/biosafe-genai-network"
with open(f"{BASE}/data/graph_data.json") as f:
    g = json.load(f)

nodes = g["nodes"]
edges = g["edges"]
node_ids = {n["id"] for n in nodes}
node_by_label = {n["label"].lower(): n["id"] for n in nodes}

max_eid = 0
for e in edges:
    eid = e.get("id","")
    if eid.startswith("edge_"):
        parts = eid.split("_")
        if len(parts)>=2:
            try: max_eid = max(max_eid, int(parts[1]))
            except: pass

def new_eid():
    global max_eid
    max_eid += 1
    return f"edge_{max_eid}"

new_nodes = []
new_edges = []
log = []

uw_id = "inst_University_of_Washington"
george_church_id = "author_george_church"

# ── AUTHOR NODES ─────────────────────────────────────────────────

# 1. David Baker (2024 Nobel Prize in Chemistry; UW; co-authored protein design biosecurity Science editorial)
if "author_david_baker" not in node_ids:
    new_nodes.append({
        "id": "author_david_baker",
        "label": "David Baker",
        "type": "author",
        "subtype": "author",
        "url": "https://www.ipd.uw.edu/david-baker/",
        "description": "Director, UW Institute for Protein Design; 2024 Nobel Prize in Chemistry for computational protein design; co-authored 'Protein design meets biosecurity' (Science, Jan 2024) with George Church",
        "details": {
            "Affiliation": "University of Washington — Institute for Protein Design",
            "Nobel": "2024 Chemistry",
            "Source": "ipd.uw.edu; Science ado1671 (2024)"
        }
    })
    log.append("ADD AUTHOR: David Baker")

# ── ORG NODES ────────────────────────────────────────────────────

# 2. EvolutionaryScale (ESM3 / ESM Cambrian protein language models)
if "org_evolutionaryscale" not in node_ids:
    new_nodes.append({
        "id": "org_evolutionaryscale",
        "label": "EvolutionaryScale",
        "type": "org",
        "subtype": "org",
        "url": "https://evolutionaryscale.ai",
        "country": "US",
        "description": "AI company (San Francisco) developing protein language models (ESM3, ESM Cambrian); spun out from Meta FAIR; flagship model ESM3 can generate novel protein sequences with biosecurity implications; company has published responsible AI commitments for protein design",
        "details": {
            "Website": "https://evolutionaryscale.ai",
            "Country": "US",
            "Models": "ESM3, ESM Cambrian",
            "Source": "EvolutionaryScale website + Nature/Science biosecurity protein design literature 2024-2025"
        }
    })
    log.append("ADD ORG: EvolutionaryScale")

# 3. UW Institute for Protein Design (department under UW)
if "org_uw_ipd" not in node_ids:
    new_nodes.append({
        "id": "org_uw_ipd",
        "label": "UW Institute for Protein Design",
        "type": "org",
        "subtype": "org",
        "url": "https://www.ipd.uw.edu",
        "country": "US",
        "description": "University of Washington Institute for Protein Design (IPD); directed by David Baker; convened 2024 summit on responsible AI for protein design; led community agreement signed by scientists from 20 countries; published 'Protein design meets biosecurity' in Science",
        "details": {
            "Website": "https://www.ipd.uw.edu",
            "Country": "US",
            "Source": "ipd.uw.edu — responsible AI commitment 2024; Science ado1671"
        }
    })
    log.append("ADD ORG: UW Institute for Protein Design")

# ── PUBLICATION NODES ────────────────────────────────────────────

# 4. "Protein design meets biosecurity" — Science editorial (Baker & Church, Jan 2024)
pub_baker_church_id = "pub_baker_church_protein_design_biosecurity_2024"
if pub_baker_church_id not in node_ids:
    new_nodes.append({
        "id": pub_baker_church_id,
        "label": "Protein design meets biosecurity (Baker & Church, Science 2024)",
        "type": "publication",
        "subtype": "research_paper",
        "url": "https://www.science.org/doi/10.1126/science.ado1671",
        "year": 2024,
        "description": "Science editorial by David Baker and George Church calling for enhanced screening and universal logging of all synthesized DNA sequences in the age of AI-enabled protein design. Proposes DNA barcode audit trail for designer proteins.",
        "details": {
            "DOI": "10.1126/science.ado1671",
            "Journal": "Science",
            "Date": "January 25, 2024",
            "Source": "bakerlab.org/wp-content/uploads/2024/04/Baker-Church-Protein-design-meets-biosecurity-Science-25-Jan-2024.pdf"
        }
    })
    log.append("ADD PUB: Baker & Church Science 2024")

# 5. "EMBO Reports: Security challenges by AI-assisted protein design" (2024) — already noted in external validation
pub_embo_protein_id = "pub_embo_protein_design_security_2024"
if pub_embo_protein_id not in node_ids:
    new_nodes.append({
        "id": pub_embo_protein_id,
        "label": "Security challenges by AI-assisted protein design (EMBO Reports, 2024)",
        "type": "publication",
        "subtype": "research_paper",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11094011/",
        "year": 2024,
        "description": "EMBO Reports review demonstrating that AI protein design tools can generate variants retaining toxicity while evading current biosecurity screening databases (nucleic acid synthesis provider tools). Calls for updated screening infrastructure.",
        "details": {
            "Journal": "EMBO Reports",
            "PMC": "PMC11094011",
            "Key_finding": "AI-designed proteins evade database-matching biosecurity screens"
        }
    })
    log.append("ADD PUB: EMBO Reports protein design security 2024")

# ── EDGES ────────────────────────────────────────────────────────

# David Baker → current_affiliation → UW
new_edges.append({
    "id": new_eid(),
    "source": "author_david_baker",
    "target": uw_id,
    "type": "current_affiliation",
})
log.append("ADD EDGE: David Baker → UW (current_affiliation)")

# David Baker → UW IPD (part_of as institute director — use part_of org structure)
new_edges.append({
    "id": new_eid(),
    "source": "org_uw_ipd",
    "target": uw_id,
    "type": "part_of",
})
log.append("ADD EDGE: UW IPD → UW (part_of)")

# David Baker → published_study → Baker & Church Science paper
new_edges.append({
    "id": new_eid(),
    "source": "author_david_baker",
    "target": pub_baker_church_id,
    "type": "published_study",
    "note": "Lead author of Science editorial 'Protein design meets biosecurity' (ado1671, Jan 2024)"
})
log.append("ADD EDGE: David Baker → Baker/Church Science paper (published_study)")

# George Church → published_study → Baker & Church Science paper
existing_pubs = {(e['source'],e['target']) for e in edges if e['type']=='published_study'}
if (george_church_id, pub_baker_church_id) not in existing_pubs:
    new_edges.append({
        "id": new_eid(),
        "source": george_church_id,
        "target": pub_baker_church_id,
        "type": "published_study",
        "note": "Co-author of Science editorial 'Protein design meets biosecurity' (ado1671, Jan 2024)"
    })
    log.append("ADD EDGE: George Church → Baker/Church Science paper (published_study)")

# EMBO paper — link to org_gryphon_scientific (they do nucleic acid screening evals)
gryphon_id = node_by_label.get("gryphon scientific")
if gryphon_id:
    new_edges.append({
        "id": new_eid(),
        "source": gryphon_id,
        "target": pub_embo_protein_id,
        "type": "policy_forum",
        "evidence": "Gryphon Scientific's biosecurity work on nucleic acid screening is directly relevant to and cited in the protein design security literature"
    })
    log.append("ADD EDGE: Gryphon Scientific → EMBO protein design pub (policy_forum)")

# UW IPD → Baker/Church Science pub (institutional output)
new_edges.append({
    "id": new_eid(),
    "source": "org_uw_ipd",
    "target": pub_baker_church_id,
    "type": "policy_forum",
    "evidence": "Baker & Church editorial published as an output of IPD's responsible AI protein design work (IPD press release Jan 2024, ipd.uw.edu)"
})
log.append("ADD EDGE: UW IPD → Baker/Church Science pub (policy_forum)")

# EvolutionaryScale → Baker/Church paper (they are a key subject of the biosecurity call)
new_edges.append({
    "id": new_eid(),
    "source": "org_evolutionaryscale",
    "target": pub_baker_church_id,
    "type": "policy_forum",
    "evidence": "EvolutionaryScale ESM models are among the generative protein design tools whose biosecurity implications Baker & Church address in their Science editorial"
})
log.append("ADD EDGE: EvolutionaryScale → Baker/Church pub (policy_forum)")

# ── SAVE EVIDENCE ────────────────────────────────────────────────
evidence = {
    "sprint": 16,
    "date": "2026-03-12",
    "sources": [
        {"url": "https://www.science.org/doi/10.1126/science.ado1671", "evidence": "Baker & Church Science editorial Jan 2024: calls for DNA logging of AI-designed sequences"},
        {"url": "https://www.ipd.uw.edu/2024/01/david-baker-and-george-church-call-for-enhanced-controls-on-dna-synthesis/", "evidence": "IPD press release confirming Baker & Church authorship and calls for DNA synthesis controls"},
        {"url": "https://www.ipd.uw.edu/2024/03/our-commitment-to-responsible-ai-development/", "evidence": "IPD community agreement on responsible AI for protein design; 20+ countries signed"},
        {"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11094011/", "evidence": "EMBO Reports: AI protein design tools evade database-matching biosecurity screens"},
        {"url": "https://evolutionaryscale.ai", "evidence": "EvolutionaryScale: ESM3 / ESM Cambrian protein language models with biosecurity implications"}
    ]
}
with open(f"{BASE}/data/raw/s16_protein_design/s16_evidence.json", "w") as f:
    json.dump(evidence, f, indent=2)

# ── MERGE ────────────────────────────────────────────────────────
nodes.extend(new_nodes)
edges.extend(new_edges)
g["nodes"] = nodes
g["edges"] = edges
with open(f"{BASE}/data/graph_data.json", "w") as f:
    json.dump(g, f, separators=(",",":"))

print(f"Sprint 16 complete:")
print(f"  New nodes: {len(new_nodes)}")
print(f"  New edges: {len(new_edges)}")
print(f"  Total nodes: {len(nodes)}")
print(f"  Total edges: {len(edges)}")
for item in log:
    print(" ", item)
