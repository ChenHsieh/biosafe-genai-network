#!/usr/bin/env python3
"""
Sprint 2 / 3: Extract Coefficient (prev. Open Philanthropy) grants.
Reads data/raw/op_grants_full.csv → writes data/staged/op_edges.json

Inclusion strategy (Sprint 3 unified filter):
- BIO_FOCUS_AREAS: always include every grant (no filter).
- EXCLUDED_FOCUS_AREAS: always skip (Alternatives to Animal Products, Farm Animal Welfare —
  false-positive risk on 'protein' keyword; not biosecurity-relevant).
- ALL other focus areas (AI, GCR, Global Health, Scientific Research, etc.):
  include only if grant title OR org name matches BIO_REL keyword regex.
  This replaces the old curated org-allowlist for AI/GCR focus areas.

Entity resolution:
- Alias table normalises known name variants (RAND, iGEM, JHU typo, BERI, Biosecure)
- Entity type classified: institution / org / individual / pooled_grant
- Individual grants (person name as grantee) use full grant title as node label
- All others use canonical org name as node label; full grant title stored on edge

URLs: ONLY verified homepage / grants-search URLs.
      No slugified or constructed grant-page URLs — those are unverified.
"""

import csv
import json
import re
import os
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV   = os.path.join(BASE_DIR, "data", "raw", "op_grants_full.csv")
STAGED_OUT = os.path.join(BASE_DIR, "data", "staged", "op_edges.json")

# ===========================================================================
# Focus area classification
# ===========================================================================
BIO_FOCUS_AREAS = {
    'Biosecurity & Pandemic Preparedness',
    'Science Supporting Biosecurity and Pandemic Preparedness',
}

# These focus areas generate false positives via the 'protein' keyword
# (plant-protein advocacy, alternative meats) — never biosecurity-relevant.
EXCLUDED_FOCUS_AREAS = {
    'Alternatives to Animal Products',
    'Farm Animal Welfare',
}

# ===========================================================================
# Grant-level blocklist — specific titles that pass the keyword filter but are
# not relevant to biosecurity / pandemic preparedness.
# Checked as case-insensitive substrings against the grant title.
# ===========================================================================
GRANT_BLOCKLIST = [
    # Canine oncology — not human/pandemic-pathogen relevant
    'Canine Cancer Vaccine',
    # Reproductive biology — developmental biology, not infectious disease
    'Reproductive Biology',
    # Gut microbiome repair — not biosecurity-relevant
    'Gut Microbiome Repair',
    # Plant protein food-science grant — false positive on 'protein' keyword
    'Plant Protein Optimization',
    # Nutrition / therapeutic food aid — not biosecurity
    'Ready-to-Use Therapeutic Food',
    'Project Peanut Butter',
    # Health economics only — no pathogen / diagnostic / vaccine component
    'Syphilis Vaccine Economic Research',
]

_blocklist_re = re.compile(
    '|'.join(re.escape(s) for s in GRANT_BLOCKLIST),
    re.I
)

def is_blocked(grant_name):
    return bool(_blocklist_re.search(grant_name))


# Bio-relevance keyword filter — applied to grant title + org name
# for ALL focus areas except BIO_FOCUS_AREAS and EXCLUDED_FOCUS_AREAS.
BIO_REL = re.compile(
    r'biolog|biosecur|biosafety|pandemic|pathogen|genomic|sequenc|'
    r'protein|antiviral|vaccine|virol|laborator|life science|'
    r'bioinformat|synthetic bio|metagenom|biosurveillance|bioweapon|'
    r'biodefense|biosensor|CRISPR|infectious|epidemic|'
    r'dangerous.*capabilit|dual.use|proliferat|'
    r'WMD|weapons of mass|chemical.*weapon|'
    r'drug.*discov|drug.*develop|therapeut|'
    r'frontier.*model.*bio|AI.*bio|bio.*AI|'
    r'benchmark.*bio|research.*biology|scientific.*research|'
    r'neuroscience|neurodegener|pandemic.*preparedness|'
    r'BlueDot',
    re.I
)

# ===========================================================================
# Alias table — maps any variant → canonical name
# Covers genuine same-entity aliases only: typos, abbreviations, project names
# NOT a filter — all rows stay regardless of alias match
# ===========================================================================
ALIAS_TABLE = {
    'RAND':                                                           'RAND Corporation',
    'John Hopkins Center for Health Security':                        'Johns Hopkins Center for Health Security',
    'International Genetically Engineered Machine Foundation':        'iGEM Foundation',
    'iGem,International Genetically Engineered Machine Foundation':   'iGEM Foundation',
    'iGEM':                                                           'iGEM Foundation',
    'Berkeley Existential Risk Initiative':                           'BERI (Berkeley Existential Risk Initiative)',
    'Biosecure':                                                      'Biosecure Ltd',
}

def apply_alias(name):
    return ALIAS_TABLE.get(name, name)

# ===========================================================================
# Entity type classification
# Institution check runs FIRST to prevent false person-name matches
# (e.g. "Blueprint Biosecurity", "Gryphon Scientific", "Harvard University"
#  are two-word capitalised names that would otherwise match the person regex)
# ===========================================================================
INST_KW = [
    'University', 'Institute', 'Institution', 'College', 'School',
    'Foundation', 'Center', 'Centre', 'Commission', 'Council',
    'Association', 'Society', 'Organisation', 'Organization',
    'Research', 'Sciences', 'Biosciences', 'Scientific',
    'Philanthropy', 'Laboratory', 'Labs', 'Lab',
    'Network', 'Alliance', 'Entrepreneurship', 'Observatory',
    'Endowment', 'Partners', 'Partnership', 'Panel', 'Coalition',
    'Committee', 'Program', 'Initiative', 'Academy',
    'Ltd', 'Inc', 'Corp', 'Consulting', 'Strategy',
    'Policy', 'Studies', 'Affairs', 'Technology', 'Technologies',
    'Bio',        # Blueprint Biosecurity, Synonym Bio, Biosecure…
    'Security',   # Blueprint Biosecurity, SecureBio…
    'Shield',     # Global Shield
    'Bioscience', 'Biodefense', 'Genomic', 'Diagnostics',
    'Health',     # Global Health, Health Security…
    'Pharma', 'Pharmaceutical', 'Therapeutics', 'Vaccines',
    'Medicine', 'Medical', 'Clinical',
]

# Short two-word org names that contain none of the above keywords
KNOWN_ORG_NAMES = {
    'Global Shield',
    'Wilton Park',
    'Longview Philanthropy',   # has 'Philanthropy' — already caught, belt-and-suspenders
    'KU Leuven',               # Belgian university (KU = Katholieke Universiteit)
    'BlueDot Impact',          # COVID surveillance NGO, no INST_KW
    'PIBBSS',                  # Principles of Intelligent Behavior in Biological and Social Systems
    'ARLIS',                   # Applied Research Laboratory for Intelligence and Security
}

_person_re  = re.compile(r'^[A-Z][a-zA-Z\-]+\.? [A-Z][a-zA-Z\-]+\.?$')
_pooled_re  = re.compile(
    r'^(Funding for|Early-Career Funding|Open Philanthropy|Scholarship|'
    r'Biosecurity Fund|Travel Grant|Biosecurity Fellow)',
    re.I
)

def classify_entity(s):
    """Return entity type: institution / org / individual / pooled_grant / unknown."""
    s = str(s).strip() if s else ''
    if not s:
        return 'unknown'
    # 1. Institution keywords — must run before person check
    if any(kw in s for kw in INST_KW):
        return 'institution'
    # 2. Known short org names with no institution keyword
    if s in KNOWN_ORG_NAMES:
        return 'org'
    # 3. Pooled / anonymous funding vehicles
    if _pooled_re.match(s):
        return 'pooled_grant'
    # 4. Personal names (only reaches here if not already classified)
    if _person_re.match(s):
        return 'individual'
    # 5. Everything else: companies, NGOs, think-tanks
    return 'org'

# ===========================================================================
# Verified program URLs (fallback → general grants page)
# ===========================================================================
PROGRAM_URLS = {
    'Biosecurity & Pandemic Preparedness':
        'https://www.openphilanthropy.org/focus/biosecurity/',
    'Science Supporting Biosecurity and Pandemic Preparedness':
        'https://www.openphilanthropy.org/focus/biosecurity/',
    'Navigating Transformative AI':
        'https://www.openphilanthropy.org/focus/transformative-artificial-intelligence/',
    'Global Catastrophic Risks':
        'https://www.openphilanthropy.org/focus/global-catastrophic-risks/',
    'Global Catastrophic Risks Capacity Building':
        'https://www.openphilanthropy.org/focus/global-catastrophic-risks/',
    # Sprint 3 additions
    'Global Health & Development':
        'https://www.openphilanthropy.org/focus/global-health-and-wellbeing/',
    'Human Health and Wellbeing':
        'https://www.openphilanthropy.org/focus/global-health-and-wellbeing/',
    'Global Health R&D':
        'https://www.openphilanthropy.org/focus/global-health-and-wellbeing/',
    'Scientific Research':
        'https://www.openphilanthropy.org/focus/science/',
    'Transformative Basic Science':
        'https://www.openphilanthropy.org/focus/science/',
    'Other areas':
        'https://www.openphilanthropy.org/grants/',
}
_DEFAULT_PROGRAM_URL = 'https://www.openphilanthropy.org/grants/'

# ===========================================================================
# Helpers
# ===========================================================================
def extract_org_from_grant(grant_title):
    """If org name is blank, extract org from grant title (left of ' — ')."""
    if ' — ' in grant_title:
        return grant_title.split(' — ')[0].strip()
    if ' - ' in grant_title:
        return grant_title.split(' - ')[0].strip()
    return grant_title.strip()


def make_node_id(label):
    """Stable node ID from node label."""
    slug = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')
    return f"org_{slug[:60]}"


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


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%B %Y", "%b-%y", "%b %Y"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m")
        except ValueError:
            continue
    return date_str.strip()


def resolve_org(org_name_raw, grant_name):
    """
    Returns (org_resolved, org_canonical, entity_type, node_label).
    - org_resolved:  raw org name, or extracted from grant title if blank
    - org_canonical: alias-normalised org name
    - entity_type:   institution / org / individual / pooled_grant / unknown
    - node_label:    what to show on the graph node
                     individual → full grant title  (context is in the title)
                     everything else → org_canonical (grant title stored on edge)
    """
    org_raw      = org_name_raw.strip() if org_name_raw else ''
    org_resolved = org_raw if org_raw else extract_org_from_grant(grant_name)
    org_canonical = apply_alias(org_resolved)
    entity_type   = classify_entity(org_resolved)

    if entity_type == 'individual':
        node_label = grant_name.strip()   # full title gives context for person grants
    else:
        node_label = org_canonical         # institution/org/pooled use canonical name

    return org_resolved, org_canonical, entity_type, node_label


def should_include(focus_area, org_name, grant_name):
    """
    Returns (include, node_label, entity_type, reason, confidence).

    Priority order:
    1. BIO_FOCUS_AREAS  → always include (HIGH confidence)
    2. EXCLUDED_FOCUS_AREAS → always exclude
    3. Everything else  → include if BIO_REL keyword matches (MEDIUM confidence)
    """
    # 1. Core biosecurity focus areas: capture everything
    if focus_area in BIO_FOCUS_AREAS:
        _, _, entity_type, node_label = resolve_org(org_name, grant_name)
        return True, node_label, entity_type, f"Focus area: {focus_area}", "HIGH"

    # 2. Explicitly excluded focus areas (false-positive risk, not bio-relevant)
    if focus_area in EXCLUDED_FOCUS_AREAS:
        return False, None, None, "", ""

    # 3. All other focus areas: bio-relevance keyword filter
    if BIO_REL.search(grant_name) or BIO_REL.search(org_name):
        _, _, entity_type, node_label = resolve_org(org_name, grant_name)
        return True, node_label, entity_type, f"Bio-relevant [{focus_area}]", "MEDIUM"

    return False, None, None, "", ""


def main():
    print(f"Reading {RAW_CSV}...")

    funder_node = {
        "id": "funder_coefficient",
        "type": "funder",
        "label": "Coefficient (prev. Open Philanthropy)",
        "short": "Coefficient",
        "url": "https://www.openphilanthropy.org/",
        "description": "Major philanthropic funder of biosecurity and AI safety research.",
    }

    program_nodes = {}
    org_nodes     = {}   # keyed by node_id
    edges         = []
    seen_grants   = set()
    skipped_excl  = 0
    skipped_kw    = 0
    skipped_block = 0

    with open(RAW_CSV, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            grant_name = (row.get('Grant')            or '').strip()
            org_name   = (row.get('Organization Name') or '').strip()
            focus_area = (row.get('Focus Area')        or '').strip()
            amount_str = (row.get('Amount')            or '').strip()
            date_str   = (row.get('Date')              or '').strip()

            if focus_area in EXCLUDED_FOCUS_AREAS:
                skipped_excl += 1
                continue

            if is_blocked(grant_name):
                skipped_block += 1
                continue

            include, node_label, entity_type, reason, confidence = should_include(
                focus_area, org_name, grant_name
            )
            if not include or not node_label:
                skipped_kw += 1
                continue
            if grant_name in seen_grants:
                continue
            seen_grants.add(grant_name)

            amount = parse_amount(amount_str)
            date   = parse_date(date_str)

            # Program node
            if focus_area not in program_nodes:
                prog_slug = re.sub(r'[^a-z0-9]+', '_', focus_area.lower()).strip('_')
                prog_id   = f"program_{prog_slug}"
                program_nodes[focus_area] = {
                    "id":          prog_id,
                    "type":        "program",
                    "label":       focus_area,
                    "short":       focus_area[:30],
                    "parent":      "funder_coefficient",
                    "url":         PROGRAM_URLS.get(focus_area, _DEFAULT_PROGRAM_URL),
                    "description": f"Coefficient focus area: {focus_area}",
                }

            # Org / grantee node
            node_id = make_node_id(node_label)
            if node_id not in org_nodes:
                org_nodes[node_id] = {
                    "id":          node_id,
                    "type":        "org",
                    "label":       node_label,
                    "short":       node_label[:40],
                    "entity_type": entity_type,
                    "url":         None,
                }

            prog_id = program_nodes[focus_area]["id"]
            edge_id = f"funds_{prog_id}_{node_id}_{date or 'unknown'}"
            suffix, orig = 0, edge_id
            while edge_id in {e['id'] for e in edges}:
                suffix += 1
                edge_id = f"{orig}_{suffix}"

            edges.append({
                "id":                 edge_id,
                "source":             prog_id,
                "target":             node_id,
                "type":               "funds",
                "amount":             amount,
                "amount_note":        amount_str,
                "date_range":         date,
                "url":                None,
                "grant_title":        grant_name,
                "extraction_method":  "csv_parse",
                "confidence":         confidence,
                "needs_human_review": False,
                "review_reason":      "",
                "matched_text":       grant_name,
                "csv_row":            row_num,
                "csv_org_name":       org_name,
                "csv_focus_area":     focus_area,
                "inclusion_reason":   reason,
            })

    # Funder → program hierarchy edges
    funder_program_edges = []
    for fa, prog in program_nodes.items():
        funder_program_edges.append({
            "id":                 f"funds_funder_coefficient_{prog['id']}",
            "source":             "funder_coefficient",
            "target":             prog["id"],
            "type":               "funds",
            "amount":             None,
            "amount_note":        "Umbrella",
            "date_range":         None,
            "url":                prog["url"],
            "grant_title":        None,
            "extraction_method":  "inferred_hierarchy",
            "confidence":         "HIGH",
            "needs_human_review": False,
            "review_reason":      "",
            "matched_text":       f"Focus area: {fa}",
            "inclusion_reason":   f"Focus area: {fa}",
        })

    all_nodes = [funder_node] + list(program_nodes.values()) + list(org_nodes.values())
    all_edges = funder_program_edges + edges

    output = {
        "sprint": 3,
        "source": "Coefficient (prev. Open Philanthropy) grants CSV",
        "source_file": "data/raw/op_grants_full.csv",
        "extracted_at": datetime.now().isoformat(),
        "nodes": all_nodes,
        "edges": all_edges,
        "summary": {
            "total_grants_in_csv": 2714,
            "grants_matched": len(edges),
            "unique_org_nodes": len(org_nodes),
            "focus_areas_included": list(program_nodes.keys()),
            "focus_areas_excluded": list(EXCLUDED_FOCUS_AREAS),
            "total_amount": sum(e['amount'] for e in edges if e['amount']),
            "skipped_excluded_fa": skipped_excl,
            "skipped_blocklist":   skipped_block,
            "skipped_no_keyword":  skipped_kw,
            "needs_review_count":  0,
        }
    }

    os.makedirs(os.path.dirname(STAGED_OUT), exist_ok=True)
    with open(STAGED_OUT, 'w') as f:
        json.dump(output, f, indent=2)

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\nExtraction complete (Sprint 3):")
    print(f"  Grants matched:        {len(edges)}")
    print(f"  Unique grantee nodes:  {len(org_nodes)}")
    print(f"  Total funding:         ${output['summary']['total_amount']:,.0f}")
    print(f"  Skipped (excluded FA): {skipped_excl}")
    print(f"  Skipped (blocklist):   {skipped_block}")
    print(f"  Skipped (no keyword):  {skipped_kw}")

    from collections import Counter
    print(f"\nPer-entity-type breakdown:")
    et_counts = Counter(n['entity_type'] for n in org_nodes.values())
    for et, cnt in sorted(et_counts.items()):
        print(f"  {et:15s}: {cnt}")

    print(f"\nPer-focus-area breakdown:")
    fa_totals = {}
    for e in edges:
        fa = e['csv_focus_area']
        fa_totals.setdefault(fa, {'count': 0, 'total': 0})
        fa_totals[fa]['count'] += 1
        fa_totals[fa]['total'] += e['amount'] or 0
    for fa, info in sorted(fa_totals.items(), key=lambda x: -x[1]['total']):
        print(f"  {fa[:55]:55s}  {info['count']:3d} grants  ${info['total']:>15,.0f}")

    print(f"\nTop 25 grantees by total funding:")
    org_totals = {}
    for e in edges:
        org_totals.setdefault(e['target'], {'count': 0, 'total': 0, 'label': ''})
        org_totals[e['target']]['count'] += 1
        org_totals[e['target']]['total'] += e['amount'] or 0
        org_totals[e['target']]['label']  = org_nodes[e['target']]['label']
    for oid, info in sorted(org_totals.items(), key=lambda x: -x[1]['total'])[:25]:
        print(f"  {info['label'][:55]:55s}  {info['count']:3d}  ${info['total']:>15,.0f}")


if __name__ == "__main__":
    main()
