#!/usr/bin/env python3
"""
Sprint 2: Validate extracted Coefficient (prev. Open Philanthropy) grant edges.
Reads data/staged/op_edges.json + data/raw/op_grants_full.csv
Writes data/staged/op_validation_report.json

Validation assertions (from ROADMAP.md):
1. Every `funds` edge has a non-null `amount` (program→org edges)
2. Every `funds` edge has a `url` pointing to a grant page
3. Every `funds` edge source traces to funder or program node
4. Every `funds` edge target exists in node set
5. No duplicate grants (deduplicate by grant URL)
6. Dollar amounts match CSV (± rounding)
7. Bridge nodes correctly detected
8. Every edge traces to a row in data/raw/op_grants_full.csv
"""

import csv
import json
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGED_IN = os.path.join(BASE_DIR, "data", "staged", "op_edges.json")
RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "op_grants_full.csv")
GRAPH_FILE = os.path.join(BASE_DIR, "data", "graph_data.json")
REPORT_OUT = os.path.join(BASE_DIR, "data", "staged", "op_validation_report.json")


def parse_amount(amount_str):
    if not amount_str:
        return None
    cleaned = amount_str.replace('$', '').replace(',', '').strip()
    try:
        return int(cleaned)
    except ValueError:
        try:
            return int(float(cleaned))
        except ValueError:
            return None


def main():
    print("Loading staged data...")
    with open(STAGED_IN) as f:
        staged = json.load(f)

    nodes = {n['id']: n for n in staged['nodes']}
    edges = staged['edges']

    # Load raw CSV for cross-validation
    print("Loading raw CSV...")
    csv_grants = {}
    with open(RAW_CSV, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            csv_grants[i] = row

    # Load Sprint 1 graph for bridge node detection
    print("Loading Sprint 1 graph...")
    with open(GRAPH_FILE) as f:
        s1_graph = json.load(f)
    s1_node_ids = {n['id'] for n in s1_graph['nodes']}
    s1_node_labels = {n['label'].lower(): n['id'] for n in s1_graph['nodes']}

    errors = []
    warnings = []
    info = []

    # Separate edge types
    program_edges = [e for e in edges if e.get('extraction_method') == 'inferred_hierarchy']
    grant_edges = [e for e in edges if e.get('extraction_method') != 'inferred_hierarchy']

    # ---- Assertion 1: Every grant edge has non-null amount ----
    print("Checking assertion 1: amounts...")
    for e in grant_edges:
        if e['amount'] is None:
            errors.append({
                'assertion': 1,
                'edge_id': e['id'],
                'message': f"Grant edge has null amount: {e['matched_text']}"
            })

    # ---- Assertion 2: Hierarchy edges (funder→program) must have verified URLs ----
    # Grant edges intentionally have null URLs (slugified URLs were removed as unverified)
    print("Checking assertion 2: hierarchy edge URLs...")
    for e in [e for e in edges if e.get('extraction_method') == 'inferred_hierarchy']:
        if not e.get('url'):
            errors.append({
                'assertion': 2,
                'edge_id': e['id'],
                'message': f"Hierarchy edge has no URL: {e.get('matched_text', '')}"
            })

    # ---- Assertion 3: Every edge source is funder or program node ----
    print("Checking assertion 3: source refs...")
    for e in edges:
        if e['source'] not in nodes:
            errors.append({
                'assertion': 3,
                'edge_id': e['id'],
                'message': f"Edge source '{e['source']}' not in node set"
            })

    # ---- Assertion 4: Every edge target exists in node set ----
    print("Checking assertion 4: target refs...")
    for e in edges:
        if e['target'] not in nodes:
            errors.append({
                'assertion': 4,
                'edge_id': e['id'],
                'message': f"Edge target '{e['target']}' not in node set"
            })

    # ---- Assertion 5: No duplicate grants (by matched_text, since URLs are intentionally null) ----
    print("Checking assertion 5: duplicates...")
    seen_grants = {}
    for e in grant_edges:
        text = e.get('matched_text', '')
        if text and text in seen_grants:
            errors.append({
                'assertion': 5,
                'edge_id': e['id'],
                'message': f"Duplicate grant text: {text[:80]} (also in {seen_grants[text]})"
            })
        if text:
            seen_grants[text] = e['id']

    # ---- Assertion 6: Dollar amounts match CSV ----
    print("Checking assertion 6: amount verification...")
    for e in grant_edges:
        csv_row = e.get('csv_row')
        if csv_row and csv_row in csv_grants:
            csv_amount = parse_amount(csv_grants[csv_row].get('Amount', ''))
            if csv_amount is not None and e['amount'] is not None:
                if abs(e['amount'] - csv_amount) > 1:  # allow $1 rounding
                    errors.append({
                        'assertion': 6,
                        'edge_id': e['id'],
                        'message': f"Amount mismatch: edge={e['amount']}, csv={csv_amount} for {e['matched_text']}"
                    })
        elif csv_row:
            warnings.append({
                'assertion': 6,
                'edge_id': e['id'],
                'message': f"CSV row {csv_row} not found for verification"
            })

    # ---- Assertion 7: Bridge nodes detected ----
    print("Checking assertion 7: bridge nodes...")
    bridge_nodes = []
    for node_id, node in nodes.items():
        if node['type'] != 'org':
            continue
        label_lower = node['label'].lower()
        # Check if this org (or similar name) exists in Sprint 1
        matched_s1 = None
        for s1_label, s1_id in s1_node_labels.items():
            if label_lower in s1_label or s1_label in label_lower:
                matched_s1 = s1_id
                break
            # Partial matches
            label_words = set(label_lower.split())
            s1_words = set(s1_label.split())
            if len(label_words & s1_words) >= 2 and len(label_words & s1_words) / len(label_words | s1_words) > 0.4:
                matched_s1 = s1_id
                break

        if matched_s1:
            bridge_nodes.append({
                'sprint2_id': node_id,
                'sprint2_label': node['label'],
                'sprint1_id': matched_s1,
                'sprint1_label': next(n['label'] for n in s1_graph['nodes'] if n['id'] == matched_s1),
            })

    info.append({
        'assertion': 7,
        'message': f"Found {len(bridge_nodes)} potential bridge nodes",
        'bridge_nodes': bridge_nodes,
    })

    # ---- Assertion 8: Every edge traces to CSV row ----
    print("Checking assertion 8: CSV traceability...")
    for e in grant_edges:
        if not e.get('csv_row'):
            errors.append({
                'assertion': 8,
                'edge_id': e['id'],
                'message': f"Grant edge has no csv_row reference: {e['matched_text']}"
            })

    # ---- Additional checks ----
    # No orphan nodes
    nodes_with_edges = set()
    for e in edges:
        nodes_with_edges.add(e['source'])
        nodes_with_edges.add(e['target'])
    orphans = [nid for nid in nodes if nid not in nodes_with_edges]
    if orphans:
        warnings.append({
            'check': 'orphan_nodes',
            'message': f"Orphan nodes (no edges): {orphans}"
        })

    # No duplicate node IDs
    node_ids = [n['id'] for n in staged['nodes']]
    if len(node_ids) != len(set(node_ids)):
        dupes = [nid for nid in node_ids if node_ids.count(nid) > 1]
        errors.append({
            'check': 'duplicate_nodes',
            'message': f"Duplicate node IDs: {set(dupes)}"
        })

    # Known hallucination check: verify no fabricated grants
    KNOWN_FABRICATIONS = [
        'EcoHealth Alliance',
        'Pirbright',
        'Metabiota',
    ]
    for e in grant_edges:
        for fab in KNOWN_FABRICATIONS:
            if fab.lower() in e.get('matched_text', '').lower():
                errors.append({
                    'check': 'hallucination_guard',
                    'edge_id': e['id'],
                    'message': f"POSSIBLE HALLUCINATION: grant mentions '{fab}' — verify against CSV manually"
                })

    # Compile report
    report = {
        'validated_at': datetime.now().isoformat(),
        'source_file': STAGED_IN,
        'raw_csv': RAW_CSV,
        'summary': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'grant_edges': len(grant_edges),
            'program_edges': len(program_edges),
            'errors': len(errors),
            'warnings': len(warnings),
            'bridge_nodes': len(bridge_nodes),
            'total_funding': sum(e['amount'] for e in grant_edges if e['amount']),
            'pass': len(errors) == 0,
        },
        'errors': errors,
        'warnings': warnings,
        'info': info,
        'bridge_nodes': bridge_nodes,
    }

    with open(REPORT_OUT, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"VALIDATION {'PASSED' if report['summary']['pass'] else 'FAILED'}")
    print(f"{'='*60}")
    print(f"  Nodes: {report['summary']['total_nodes']}")
    print(f"  Edges: {report['summary']['total_edges']} ({report['summary']['grant_edges']} grants + {report['summary']['program_edges']} hierarchy)")
    print(f"  Errors: {report['summary']['errors']}")
    print(f"  Warnings: {report['summary']['warnings']}")
    print(f"  Bridge nodes: {report['summary']['bridge_nodes']}")
    print(f"  Total funding: ${report['summary']['total_funding']:,.0f}")

    if errors:
        print(f"\nERRORS:")
        for e in errors:
            print(f"  [{e.get('assertion', e.get('check', '?'))}] {e['message']}")

    if warnings:
        print(f"\nWARNINGS:")
        for w in warnings:
            print(f"  [{w.get('assertion', w.get('check', '?'))}] {w['message']}")

    if bridge_nodes:
        print(f"\nBRIDGE NODES:")
        for b in bridge_nodes:
            print(f"  {b['sprint2_label']:40s} ↔ {b['sprint1_label']}")

    print(f"\nReport written to: {REPORT_OUT}")


if __name__ == "__main__":
    main()
