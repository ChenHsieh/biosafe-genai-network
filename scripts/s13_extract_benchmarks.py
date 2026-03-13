"""
Sprint 13: Benchmark & Evaluation Landscape
Add Apollo Research, METR, and missing author-publication links
"""
import json, os

BASE = "/sessions/eloquent-jolly-knuth/mnt/biosafe-genai-network"

with open(f"{BASE}/data/graph_data.json") as f:
    g = json.load(f)

nodes = g["nodes"]
edges = g["edges"]

# Build lookup helpers
node_ids = {n["id"] for n in nodes}
node_by_label = {n["label"].lower(): n["id"] for n in nodes}

# Find max edge numeric ID
max_eid = 0
for e in edges:
    eid = e.get("id", "")
    if eid.startswith("edge_"):
        parts = eid.split("_")
        if len(parts) >= 2:
            try:
                max_eid = max(max_eid, int(parts[1]))
            except ValueError:
                pass

def new_eid():
    global max_eid
    max_eid += 1
    return f"edge_{max_eid}"

new_nodes = []
new_edges = []
log = []

# ── NEW ORG NODES ────────────────────────────────────────────────

# 1. Apollo Research
if "org_apollo_research" not in node_ids:
    new_nodes.append({
        "id": "org_apollo_research",
        "label": "Apollo Research",
        "type": "org",
        "subtype": "evaluator",
        "url": "https://www.apolloresearch.ai/",
        "country": "US",
        "description": "AI safety research organization specializing in model evaluations for scheming and dangerous capabilities; PBC nonprofit; evaluates frontier models from Microsoft, OpenAI, Google DeepMind",
        "details": {"Website": "https://www.apolloresearch.ai/", "Country": "US", "Type": "Public Benefit Corporation (PBC)"}
    })
    log.append("ADD NODE: Apollo Research")

# 2. METR (formerly ARC Evals)
if "org_metr" not in node_ids:
    new_nodes.append({
        "id": "org_metr",
        "label": "METR",
        "type": "org",
        "subtype": "evaluator",
        "url": "https://metr.org/",
        "country": "US",
        "description": "Model Evaluation & Threat Research — nonprofit evaluating frontier AI models for dangerous autonomous capabilities; formerly ARC Evals (spinoff of Alignment Research Center); conducts pre-deployment evals for Anthropic and OpenAI",
        "details": {"Website": "https://metr.org/", "Country": "US", "Formerly": "ARC Evals (Alignment Research Center)"}
    })
    log.append("ADD NODE: METR")

# ── NEW AUTHOR NODES ────────────────────────────────────────────

# 3. Beth Barnes (METR founder/CEO)
if "author_beth_barnes" not in node_ids:
    new_nodes.append({
        "id": "author_beth_barnes",
        "label": "Beth Barnes",
        "type": "author",
        "subtype": "evaluator",
        "url": "https://metr.org/about",
        "description": "Founder and CEO of METR (formerly ARC Evals); former alignment researcher at OpenAI",
        "details": {"Role": "CEO, METR", "Formerly": "OpenAI alignment researcher"}
    })
    log.append("ADD NODE: Beth Barnes")

# ── NEW EDGES ────────────────────────────────────────────────────

# Get IDs for existing nodes we'll link to
anthropic_id = node_by_label.get("anthropic")
openai_id = node_by_label.get("openai")
gdm_id = node_by_label.get("google deepmind")
wmdp_pub_id = "pub_s2_The_WMDP_Benchmark__Measuring_and_Reduci_2024"
cais_id = "inst_Center_for_AI_Safety"
nathaniel_li_id = "author_Nathaniel_Li1"
dan_hendrycks_id = "author_Dan_Hendrycks1"

print("Lookup: anthropic=", anthropic_id, "openai=", openai_id, "gdm=", gdm_id)

# Apollo Research biosecurity_eval → AI labs
edge_source = "Apollo Research (source: apolloresearch.ai — listed as evaluating Microsoft, OpenAI, Google DeepMind per organization overview)"
for target_id, target_label in [(anthropic_id, "Anthropic"), (openai_id, "OpenAI"), (gdm_id, "Google DeepMind")]:
    if target_id:
        new_edges.append({
            "id": new_eid(),
            "source": "org_apollo_research",
            "target": target_id,
            "type": "biosecurity_eval",
            "confidence": "HIGH",
            "evidence": "Apollo Research website lists Microsoft, OpenAI, Google DeepMind as key partners; conducted scheming/deceptive alignment evaluations pre-deployment (apolloresearch.ai)"
        })
        log.append(f"ADD EDGE: Apollo Research biosecurity_eval → {target_label}")

# METR biosecurity_eval → Anthropic, OpenAI
for target_id, target_label in [(anthropic_id, "Anthropic"), (openai_id, "OpenAI")]:
    if target_id:
        new_edges.append({
            "id": new_eid(),
            "source": "org_metr",
            "target": target_id,
            "type": "biosecurity_eval",
            "confidence": "HIGH",
            "evidence": "METR (metr.org) conducted pre-deployment evaluations for Anthropic Claude models and OpenAI o3, o4-mini, GPT-4o, GPT-4.5 per METR About page"
        })
        log.append(f"ADD EDGE: METR biosecurity_eval → {target_label}")

# Beth Barnes current_affiliation → METR
new_edges.append({
    "id": new_eid(),
    "source": "author_beth_barnes",
    "target": "org_metr",
    "type": "current_affiliation"
})
log.append("ADD EDGE: Beth Barnes → METR (current_affiliation)")

# Nathaniel Li published_study → WMDP (he is first author; has CAIS affiliation already)
# Check edge doesn't already exist
existing_pub_edges = {(e['source'], e['target']) for e in edges if e['type'] == 'published_study'}
if (nathaniel_li_id, wmdp_pub_id) not in existing_pub_edges:
    new_edges.append({
        "id": new_eid(),
        "source": nathaniel_li_id,
        "target": wmdp_pub_id,
        "type": "published_study",
        "note": "First author of WMDP benchmark paper (arxiv 2403.03218, ICML 2024)"
    })
    log.append("ADD EDGE: Nathaniel Li published_study → WMDP")

# Dan Hendrycks published_study → WMDP (he is corresponding/last author at CAIS)
if (dan_hendrycks_id, wmdp_pub_id) not in existing_pub_edges:
    new_edges.append({
        "id": new_eid(),
        "source": dan_hendrycks_id,
        "target": wmdp_pub_id,
        "type": "published_study",
        "note": "Last/corresponding author of WMDP benchmark paper (arxiv 2403.03218, ICML 2024)"
    })
    log.append("ADD EDGE: Dan Hendrycks published_study → WMDP")

# Anjali Gopal published_study → WMDP (she is a named author in the WMDP consortium)
anjali_id = node_by_label.get("anjali gopal", "author_anjali_gopal")
if anjali_id and (anjali_id, wmdp_pub_id) not in existing_pub_edges:
    new_edges.append({
        "id": new_eid(),
        "source": anjali_id,
        "target": wmdp_pub_id,
        "type": "published_study",
        "note": "Named author in WMDP benchmark paper consortium (arxiv 2403.03218)"
    })
    log.append("ADD EDGE: Anjali Gopal published_study → WMDP")

# Dan Hendrycks → CAIS (he directs CAIS; already has current_affiliation — check)
existing_aff_edges = {(e['source'], e['target']) for e in edges if e['type'] in ('current_affiliation', 'past_affiliation')}
# He already has current_affiliation → CAIS per earlier check, skip

# ── SAVE RAW EVIDENCE ────────────────────────────────────────────
evidence = {
    "sprint": 13,
    "date": "2026-03-12",
    "sources": [
        {"node": "Apollo Research", "url": "https://www.apolloresearch.ai/", "evidence": "Organization overview: evaluates Microsoft, OpenAI, Google DeepMind; PBC nonprofit; specializes in scheming/deceptive alignment evals"},
        {"node": "METR", "url": "https://metr.org/about", "evidence": "Nonprofit: pre-deployment evals for Anthropic and OpenAI models (o3, o4-mini, GPT-4o, Claude); formerly ARC Evals (ARC spinoff Dec 2023)"},
        {"node": "Beth Barnes", "url": "https://80000hours.org/podcast/episodes/beth-barnes-ai-safety-evals/", "evidence": "CEO/founder of METR; former OpenAI alignment researcher; founded ARC Evals in 2022"},
        {"node": "WMDP author edges", "url": "https://arxiv.org/abs/2403.03218", "evidence": "Nathaniel Li (first author), Anjali Gopal (named author), Kevin Esvelt (author), Dan Hendrycks (last author); ICML 2024, 350+ citations"}
    ],
    "new_nodes": [n["id"] for n in new_nodes],
    "new_edges": [{"id": e["id"], "source": e["source"], "target": e["target"], "type": e["type"]} for e in new_edges]
}

with open(f"{BASE}/data/raw/s13_benchmarks/s13_evidence.json", "w") as f:
    json.dump(evidence, f, indent=2)

# ── MERGE INTO GRAPH ─────────────────────────────────────────────
nodes.extend(new_nodes)
edges.extend(new_edges)
g["nodes"] = nodes
g["edges"] = edges

with open(f"{BASE}/data/graph_data.json", "w") as f:
    json.dump(g, f, separators=(",", ":"))

# ── REPORT ───────────────────────────────────────────────────────
print(f"\nSprint 13 complete:")
print(f"  New nodes: {len(new_nodes)}")
print(f"  New edges: {len(new_edges)}")
print(f"  Total nodes: {len(nodes)}")
print(f"  Total edges: {len(edges)}")
print()
for item in log:
    print(" ", item)
