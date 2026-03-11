#!/usr/bin/env python3
"""Build the complete graph data structure with nodes, edges, and enriched metadata."""
import json
import csv
import re

with open("raw_data.json") as f:
    data = json.load(f)

# === Build nodes and edges ===
nodes = {}  # id -> node
edges = []  # list of {source, target, type}

# Known institution homepage mappings
INST_URLS = {
    "University of California, Berkeley": "https://www.berkeley.edu",
    "UC Berkeley": "https://www.berkeley.edu",
    "Stanford University": "https://www.stanford.edu",
    "MIT": "https://www.mit.edu",
    "Massachusetts Institute of Technology": "https://www.mit.edu",
    "Harvard University": "https://www.harvard.edu",
    "University of Oxford": "https://www.ox.ac.uk",
    "University of Cambridge": "https://www.cam.ac.uk",
    "Google DeepMind": "https://deepmind.google",
    "Google": "https://www.google.com",
    "DeepMind": "https://deepmind.google",
    "Carnegie Mellon University": "https://www.cmu.edu",
    "Princeton University": "https://www.princeton.edu",
    "University of Pennsylvania": "https://www.upenn.edu",
    "New York University": "https://www.nyu.edu",
    "Columbia University": "https://www.columbia.edu",
    "ETH Zurich": "https://ethz.ch",
    "Technical University of Munich": "https://www.tum.de",
    "TU Munich": "https://www.tum.de",
    "LMU Munich": "https://www.lmu.de",
    "Ludwig-Maximilians-Universität München": "https://www.lmu.de",
    "EleutherAI": "https://www.eleuther.ai",
    "Anthropic": "https://www.anthropic.com",
    "OpenAI": "https://openai.com",
    "Meta": "https://www.meta.com",
    "Meta AI": "https://ai.meta.com",
    "Microsoft": "https://www.microsoft.com",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/",
    "Allen Institute for AI": "https://allenai.org",
    "AI2": "https://allenai.org",
    "University of Virginia": "https://www.virginia.edu",
    "Johns Hopkins University": "https://www.jhu.edu",
    "University of Washington": "https://www.washington.edu",
    "University of Toronto": "https://www.utoronto.ca",
    "Center for AI Safety": "https://www.safe.ai",
    "University of Illinois Urbana-Champaign": "https://illinois.edu",
    "University of Wisconsin-Madison": "https://www.wisc.edu",
    "University of Notre Dame": "https://www.nd.edu",
    "University of Galway": "https://www.universityofgalway.ie",
    "National University of Singapore": "https://www.nus.edu.sg",
    "University of Michigan": "https://umich.edu",
    "Lawrence Livermore National Laboratory": "https://www.llnl.gov",
    "SecureBio": "https://securebio.org",
    "iGEM Foundation": "https://igem.org",
    "Scale AI": "https://scale.com",
    "Constellation": "https://www.constellation.org",
    "Institut Polytechnique de Paris": "https://www.ip-paris.fr",
    "Oxford Internet Institute": "https://www.oii.ox.ac.uk",
    "University of Wroclaw": "https://uni.wroc.pl",
    "Wrocław University of Science and Technology": "https://pwr.edu.pl",
    "Chinese Academy of Sciences": "https://english.cas.cn",
    "Peking University": "https://english.pku.edu.cn",
    "Tsinghua University": "https://www.tsinghua.edu.cn/en/",
    "University of Sydney": "https://www.sydney.edu.au",
    "Bosch": "https://www.bosch.com",
    "Bosch Center for Artificial Intelligence": "https://www.bosch-ai.com",
    "Siemens AG": "https://www.siemens.com",
    "University College London": "https://www.ucl.ac.uk",
    "UK AI Safety Institute": "https://www.aisi.gov.uk",
    "FAR AI": "https://far.ai",
    "MATS": "https://www.matsprogram.org",
    "Redwood Research": "https://www.redwoodresearch.org",
    "UC Berkeley / Algoverse AI Research": "https://www.berkeley.edu",
    "Unknown - Further research required": "",
}

def normalize_institution(name):
    """Normalize institution names for deduplication."""
    name = name.strip()
    # Fix "X, X" duplicates
    if ', ' in name:
        parts = [p.strip() for p in name.split(', ')]
        if len(parts) == 2 and parts[0] == parts[1]:
            name = parts[0]
    # Common normalizations
    mappings = {
        "UC Berkeley": "University of California, Berkeley",
        "UC Berkeley / Algoverse AI Research": "University of California, Berkeley",
        "Ludwig-Maximilians-Universität München": "LMU Munich",
        "Ludwig Maximilians University Munich": "LMU Munich",
        "TU Munich": "Technical University of Munich",
        "Technische Universität München": "Technical University of Munich",
        "Unknown - Further research required": "",
    }
    return mappings.get(name, name)

def get_institution_url(name):
    """Get URL for institution."""
    # Check direct mapping
    if name in INST_URLS:
        return INST_URLS[name]
    # Check normalized
    norm = normalize_institution(name)
    if norm in INST_URLS:
        return INST_URLS[norm]
    # Try domain-based
    return ""

def make_safe_id(s):
    """Create a safe ID from a string."""
    return re.sub(r'[^a-zA-Z0-9]', '_', s).strip('_')[:80]

# === 1. Create Presentation nodes ===
for paper in data["papers"]:
    pid = f"paper_{paper['id']}"
    pdf_url = f"https://openreview.net/pdf?id={paper['forum']}" if paper.get('pdf') else ""
    forum_url = f"https://openreview.net/forum?id={paper['forum']}"
    nodes[pid] = {
        "id": pid,
        "label": paper["title"],
        "type": "presentation",
        "subtype": paper["type"].lower(),  # "oral" or "poster"
        "url": forum_url,
        "pdf_url": pdf_url,
        "keywords": paper.get("keywords", []),
        "abstract": paper.get("abstract", "")[:200],
        "tldr": paper.get("tldr", ""),
        "details": {
            "Forum": forum_url,
            "PDF": pdf_url,
            "Type": paper["type"],
            "Keywords": ", ".join(paper.get("keywords", [])),
        }
    }

# === 2. Create Author nodes ===
for aid, info in data["authors"].items():
    author_node_id = f"author_{make_safe_id(aid)}"
    openreview_url = f"https://openreview.net/profile?id={aid}" if aid.startswith("~") else ""

    links = info.get("links", {})
    details = {"OpenReview": openreview_url}
    if links.get("homepage"):
        details["Homepage"] = links["homepage"]
    if links.get("gscholar"):
        details["Google Scholar"] = links["gscholar"]
    if links.get("dblp"):
        details["DBLP"] = links["dblp"]
    if links.get("linkedin"):
        details["LinkedIn"] = links["linkedin"]
    if links.get("semanticScholar"):
        details["Semantic Scholar"] = links["semanticScholar"]
    if links.get("orcid"):
        details["ORCID"] = links["orcid"]
    if links.get("twitter"):
        details["Twitter"] = links["twitter"]

    nodes[author_node_id] = {
        "id": author_node_id,
        "label": info["name"],
        "type": "author",
        "subtype": "author",
        "url": links.get("homepage", openreview_url),
        "openreview_id": aid,
        "details": details,
    }

    # Create edges: author -> paper
    for paper_id in info["papers"]:
        edges.append({
            "source": author_node_id,
            "target": f"paper_{paper_id}",
            "type": "authored",
        })

# === 3. Create Affiliation nodes (institution + department) ===
institution_nodes = {}  # normalized_name -> node_id
department_nodes = {}   # (inst, dept) -> node_id

for aid, info in data["authors"].items():
    author_node_id = f"author_{make_safe_id(aid)}"

    for aff in info.get("affiliations", []):
        inst_name = normalize_institution(aff["institution"])
        if not inst_name or inst_name == "Unknown - Further research required":
            continue

        dept_name = aff.get("department", "").strip()

        # Create institution node
        if inst_name not in institution_nodes:
            inst_id = f"inst_{make_safe_id(inst_name)}"
            inst_url = get_institution_url(inst_name)
            if not inst_url and aff.get("institution_domain"):
                inst_url = f"https://{aff['institution_domain']}"
            institution_nodes[inst_name] = inst_id
            nodes[inst_id] = {
                "id": inst_id,
                "label": inst_name,
                "type": "institution",
                "subtype": "institution",
                "url": inst_url,
                "country": aff.get("country", ""),
                "details": {
                    "Website": inst_url,
                    "Country": aff.get("country", ""),
                },
            }

        inst_id = institution_nodes[inst_name]

        # Create department node if exists
        if dept_name:
            dept_key = (inst_name, dept_name)
            if dept_key not in department_nodes:
                dept_id = f"dept_{make_safe_id(inst_name)}_{make_safe_id(dept_name)}"
                department_nodes[dept_key] = dept_id
                nodes[dept_id] = {
                    "id": dept_id,
                    "label": dept_name,
                    "type": "department",
                    "subtype": "department",
                    "url": "",
                    "parent_institution": inst_name,
                    "details": {
                        "Department": dept_name,
                        "Institution": inst_name,
                    },
                }
                # Edge: department -> institution
                edges.append({
                    "source": dept_id,
                    "target": inst_id,
                    "type": "part_of",
                })

            dept_id = department_nodes[dept_key]
            # Edge: author -> department
            edge_key = (author_node_id, dept_id)
            # Check if edge already exists
            if not any(e["source"] == author_node_id and e["target"] == dept_id for e in edges):
                is_current = aff.get("end") is None or (isinstance(aff.get("end"), (int, float)) and aff["end"] >= 2025)
                edges.append({
                    "source": author_node_id,
                    "target": dept_id,
                    "type": "current_affiliation" if is_current else "past_affiliation",
                })
        else:
            # Edge: author -> institution directly
            if not any(e["source"] == author_node_id and e["target"] == inst_id for e in edges):
                is_current = aff.get("end") is None or (isinstance(aff.get("end"), (int, float)) and aff["end"] >= 2025)
                edges.append({
                    "source": author_node_id,
                    "target": inst_id,
                    "type": "current_affiliation" if is_current else "past_affiliation",
                })

# === Compute degrees ===
degree = {}
for e in edges:
    degree[e["source"]] = degree.get(e["source"], 0) + 1
    degree[e["target"]] = degree.get(e["target"], 0) + 1

for nid, node in nodes.items():
    node["degree"] = degree.get(nid, 0)

# === Summary ===
type_counts = {}
for n in nodes.values():
    t = n["type"]
    type_counts[t] = type_counts.get(t, 0) + 1

edge_type_counts = {}
for e in edges:
    t = e["type"]
    edge_type_counts[t] = edge_type_counts.get(t, 0) + 1

print("=== Graph Summary ===")
print(f"Total nodes: {len(nodes)}")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")
print(f"Total edges: {len(edges)}")
for t, c in sorted(edge_type_counts.items()):
    print(f"  {t}: {c}")

# Top institutions by degree
inst_by_degree = [(n["label"], n["degree"]) for n in nodes.values() if n["type"] == "institution"]
inst_by_degree.sort(key=lambda x: -x[1])
print("\nTop institutions by degree:")
for name, deg in inst_by_degree[:15]:
    print(f"  {name}: {deg}")

# === Save graph data ===
graph_data = {
    "nodes": list(nodes.values()),
    "edges": edges,
    "metadata": data["metadata"],
    "stats": {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": type_counts,
        "edge_types": edge_type_counts,
    }
}

with open("graph_data.json", "w") as f:
    json.dump(graph_data, f, indent=2)

# === Export CSV files ===
# Nodes CSV
with open("nodes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "label", "type", "subtype", "degree", "url", "details"])
    for n in nodes.values():
        writer.writerow([n["id"], n["label"], n["type"], n.get("subtype", ""),
                        n["degree"], n.get("url", ""),
                        json.dumps(n.get("details", {}))])

# Edges CSV
with open("edges.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["source", "target", "type"])
    for e in edges:
        writer.writerow([e["source"], e["target"], e["type"]])

print(f"\nSaved: graph_data.json, nodes.csv, edges.csv")
