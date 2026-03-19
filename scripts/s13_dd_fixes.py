"""
Sprint 13 Due Diligence Fixes:
1. Add VCT (Virology Capabilities Test) publication node + author links
2. Add evidence strings to old biosecurity_eval edges that are missing them
3. Link Mantas Mazeika → WMDP
4. Connect RAND org → RAND publications via policy_forum
5. Link Beth Barnes → METR evaluation publication
6. Add METR task suite / evaluation publication node
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(f"{BASE}/data/graph_data.json") as f:
    g = json.load(f)

nodes = g["nodes"]
edges = g["edges"]
nodes_by_id = {n["id"]: n for n in nodes}
node_by_label = {n["label"].lower(): n["id"] for n in nodes}
node_ids = {n["id"] for n in nodes}
existing_edges = {(e["source"], e["target"], e["type"]) for e in edges}

max_eid = 0
for e in edges:
    eid = e.get("id", "")
    if eid.startswith("edge_"):
        try: max_eid = max(max_eid, int(eid.split("_")[1]))
        except (ValueError, IndexError): pass

def new_eid():
    global max_eid
    max_eid += 1
    return f"edge_{max_eid}"

new_nodes = []
new_edges = []
modified_edges = 0
log = []

# ─── FIX 1: Add VCT publication node ─────────────────────────────────────────
vct_id = "pub_vct_virology_capabilities_test_2025"
if vct_id not in node_ids:
    new_nodes.append({
        "id": vct_id,
        "label": "Virology Capabilities Test (VCT): A Multimodal Virology Q&A Benchmark",
        "type": "publication",
        "subtype": "research_paper",
        "url": "https://arxiv.org/abs/2504.16137",
        "year": 2025,
        "description": "SecureBio + CAIS benchmark measuring AI capability to troubleshoot complex virology lab protocols at expert level. Found frontier AI models provide expert-level virology assistance. More informative than WMDP for assessing real biological risk.",
        "details": {
            "arXiv": "2504.16137",
            "Authors": "Jasper Götting, Pedro Medeiros, Jon G Sanders, Nathaniel Li, Long Phan, Karam Elabd, Lennart Justen, Dan Hendrycks, Seth Donoughe",
            "Affiliation": "SecureBio, Center for AI Safety",
            "Source": "arxiv.org/abs/2504.16137; virologytest.ai"
        }
    })
    log.append("ADD NODE: VCT publication")

# Link VCT authors already in graph
vct_author_map = {
    "author_Nathaniel_Li1": "Nathaniel Li — first author team at SecureBio/CAIS (arxiv 2504.16137)",
    "author_Dan_Hendrycks1": "Dan Hendrycks — senior author, CAIS director (arxiv 2504.16137)",
}
# Seth Donoughe — check
seth_id = node_by_label.get("seth donoughe") or next((n["id"] for n in nodes if "donoughe" in n["label"].lower()), None)
if seth_id:
    vct_author_map[seth_id] = "Seth Donoughe — co-author (arxiv 2504.16137)"

for author_id, note in vct_author_map.items():
    if author_id in node_ids and (author_id, vct_id, "published_study") not in existing_edges:
        new_edges.append({
            "id": new_eid(),
            "source": author_id,
            "target": vct_id,
            "type": "published_study",
            "note": note
        })
        log.append(f"ADD EDGE: {nodes_by_id[author_id]['label']} → VCT (published_study)")

# SecureBio → VCT as biosecurity_eval (VCT is a SecureBio evaluation tool)
securebio_id = node_by_label.get("securebio")
if securebio_id and (securebio_id, vct_id, "biosecurity_eval") not in existing_edges:
    new_edges.append({
        "id": new_eid(),
        "source": securebio_id,
        "target": vct_id,
        "type": "biosecurity_eval",
        "confidence": "HIGH",
        "evidence": "VCT developed by SecureBio team (virologytest.ai; arxiv 2504.16137); found frontier models provide expert-level virology assistance"
    })
    log.append("ADD EDGE: SecureBio → VCT (biosecurity_eval)")

# ─── FIX 2: Add evidence to old biosecurity_eval edges missing it ─────────────
evidence_map = {
    # (source_label, target_label): evidence string
    ("SecureBio", "Anthropic"): "SecureBio Substack 'AI Biorisk Evaluations' series (securebio.substack.com); evaluated Claude 3.7 Sonnet and Claude 4 for biosecurity uplift",
    ("SecureBio", "OpenAI"): "SecureBio Substack 'AI Biorisk Evaluations' series (securebio.substack.com); evaluated GPT-4.5, o3-mini, o4-mini",
    ("SecureBio", "Google DeepMind"): "SecureBio Substack 'AI Biorisk Evaluations' series (securebio.substack.com); evaluated Gemini 2.5 Pro",
    ("SecureBio", "xAI"): "SecureBio Substack mentioned xAI evaluation (MEDIUM confidence — specific model not named)",
    ("SecureBio", "Signature Science"): "SecureBio collaboration with Signature Science on biosecurity evaluation protocols",
    ("SecureBio", "Deloitte"): "SecureBio/Deloitte evaluation partnership (confirmed via Sprint 5 policy bigtech raw data)",
    ("UK AI Safety Institute", "Anthropic"): "UK AISI evaluated Claude 3.5 Sonnet pre-deployment (FedScoop report 2024; Epoch AI biorisk analysis)",
    ("UK AI Safety Institute", "OpenAI"): "UK AISI evaluated OpenAI o1 pre-deployment (Epoch AI biorisk analysis; published results 2024)",
    ("FutureHouse", "Anthropic"): "FutureHouse LAB-Bench paper (arxiv) tested Claude alongside GPT-4 for biology research capabilities",
    ("Gryphon Scientific", "OpenAI"): "Gryphon Scientific conducted biosecurity evaluation of GPT-4 for OpenAI (OpenAI blog 2023; VentureBeat coverage)",
}

for e in edges:
    if e.get("type") != "biosecurity_eval":
        continue
    if e.get("evidence"):
        continue  # already has evidence

    src_label = nodes_by_id.get(e["source"], {}).get("label", "")
    tgt_label = nodes_by_id.get(e["target"], {}).get("label", "")
    key = (src_label, tgt_label)
    if key in evidence_map:
        e["evidence"] = evidence_map[key]
        modified_edges += 1
        log.append(f"ADD EVIDENCE: {src_label} → {tgt_label}")

# ─── FIX 3: Link Mantas Mazeika → WMDP ───────────────────────────────────────
wmdp_id = "pub_s2_The_WMDP_Benchmark__Measuring_and_Reduci_2024"
mantas_id = next((n["id"] for n in nodes if "mazeika" in n["label"].lower()), None)
if mantas_id and (mantas_id, wmdp_id, "published_study") not in existing_edges:
    new_edges.append({
        "id": new_eid(),
        "source": mantas_id,
        "target": wmdp_id,
        "type": "published_study",
        "note": "Mantas Mazeika — co-author WMDP benchmark paper (arxiv 2403.03218, ICML 2024); CAIS affiliation"
    })
    log.append("ADD EDGE: Mantas Mazeika → WMDP (published_study)")

# ─── FIX 4: Connect RAND org → RAND publications via policy_forum ─────────────
rand_org_id = node_by_label.get("rand corporation")
rand_pubs = [n for n in nodes if n["type"] == "publication" and "rand" in n["id"].lower()]
if rand_org_id:
    for rp in rand_pubs:
        if (rand_org_id, rp["id"], "policy_forum") not in existing_edges:
            new_edges.append({
                "id": new_eid(),
                "source": rand_org_id,
                "target": rp["id"],
                "type": "policy_forum",
                "evidence": f"RAND Corporation authored this report (rand.org); {rp['label'][:60]}"
            })
            log.append(f"ADD EDGE: RAND Corp → {rp['label'][:50]} (policy_forum)")

# ─── FIX 5: Add METR evaluation publication + Beth Barnes link ────────────────
metr_pub_id = "pub_metr_task_suite_2024"
if metr_pub_id not in node_ids:
    new_nodes.append({
        "id": metr_pub_id,
        "label": "METR Task Suite: Evaluating Autonomous AI Agents for Dangerous Capabilities",
        "type": "publication",
        "subtype": "research_report",
        "url": "https://metr.org/research/",
        "year": 2024,
        "description": "METR's evaluation framework and task suite for measuring dangerous autonomous capability in frontier AI models; used in pre-deployment evaluations for Anthropic and OpenAI; co-authored by Beth Barnes and team.",
        "details": {
            "Source": "metr.org/research — publicly documented evaluation methodology used for o3, o4-mini, GPT-4o, Claude pre-deployment evals"
        }
    })
    log.append("ADD NODE: METR task suite publication")

# Beth Barnes → METR pub
beth_id = "author_beth_barnes"
if (beth_id, metr_pub_id, "published_study") not in existing_edges:
    new_edges.append({
        "id": new_eid(),
        "source": beth_id,
        "target": metr_pub_id,
        "type": "published_study",
        "note": "Beth Barnes — CEO of METR; leads evaluation methodology development documented at metr.org/research"
    })
    log.append("ADD EDGE: Beth Barnes → METR task suite (published_study)")

# METR org → METR pub  
metr_id = "org_metr"
if (metr_id, metr_pub_id, "biosecurity_eval") not in existing_edges:
    new_edges.append({
        "id": new_eid(),
        "source": metr_id,
        "target": metr_pub_id,
        "type": "biosecurity_eval",
        "confidence": "HIGH",
        "evidence": "METR developed and published this evaluation suite; used for pre-deployment evaluations of Anthropic and OpenAI frontier models (metr.org/research)"
    })
    log.append("ADD EDGE: METR → METR task suite (biosecurity_eval)")

# ─── SAVE STAGED OUTPUT ────────────────────────────────────────────────────────
staged = {
    "sprint": "13_dd",
    "date": "2026-03-13",
    "new_nodes": [n["id"] for n in new_nodes],
    "new_edges": [{"id": e["id"], "source": e["source"], "target": e["target"], "type": e["type"]} for e in new_edges],
    "modified_edges": modified_edges,
    "log": log
}
with open(f"{BASE}/data/staged/s13_dd_nodes.json", "w") as f:
    json.dump(new_nodes, f, indent=2)
with open(f"{BASE}/data/staged/s13_dd_edges.json", "w") as f:
    json.dump(new_edges, f, indent=2)

# ─── MERGE ────────────────────────────────────────────────────────────────────
nodes.extend(new_nodes)
edges.extend(new_edges)
g["nodes"] = nodes
g["edges"] = edges
with open(f"{BASE}/data/graph_data.json", "w") as f:
    json.dump(g, f, separators=(",", ":"))

print(f"Sprint 13 DD complete:")
print(f"  New nodes: {len(new_nodes)}")
print(f"  New edges: {len(new_edges)}")
print(f"  Modified edges (evidence added): {modified_edges}")
print(f"  Total: {len(nodes)} nodes, {len(edges)} edges")
print()
for item in log:
    print(f"  {item}")
