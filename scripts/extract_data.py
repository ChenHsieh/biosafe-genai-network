#!/usr/bin/env python3
"""Extract all accepted papers and author profiles from OpenReview for BioSafe GenAI 2025 workshop."""

import json
import time
import urllib.request
import urllib.parse
import ssl

# Disable SSL verification for API calls
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_API = "https://api2.openreview.net"

def api_get(endpoint, params=None):
    """Make a GET request to OpenReview API."""
    url = BASE_API + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def fetch_all_papers():
    """Fetch all accepted papers (oral + poster)."""
    papers = []
    offset = 0
    limit = 50
    while True:
        data = api_get("/notes/search", {
            "query": "BioSafe_GenAI",
            "limit": limit,
            "offset": offset
        })
        if not data or not data.get("notes"):
            break
        for note in data["notes"]:
            c = note.get("content", {})
            venue = c.get("venue", {}).get("value", "")
            # Only accepted papers
            if "BioSafe GenAI 2025" not in venue:
                continue
            if "Oral" not in venue and "Poster" not in venue:
                continue
            paper = {
                "id": note.get("id", ""),
                "forum": note.get("forum", ""),
                "title": c.get("title", {}).get("value", ""),
                "authors": c.get("authors", {}).get("value", []),
                "authorids": c.get("authorids", {}).get("value", []),
                "venue": venue,
                "type": "Oral" if "Oral" in venue else "Poster",
                "keywords": c.get("keywords", {}).get("value", []),
                "abstract": c.get("abstract", {}).get("value", ""),
                "tldr": c.get("TLDR", {}).get("value", ""),
                "pdf": c.get("pdf", {}).get("value", ""),
            }
            papers.append(paper)
        if len(data["notes"]) < limit:
            break
        offset += limit
    return papers

def fetch_author_profile(author_id):
    """Fetch an author's profile from OpenReview."""
    if not author_id or not author_id.startswith("~"):
        return None
    # Try the profile endpoint
    data = api_get("/profiles", {"id": author_id})
    if data and data.get("profiles"):
        return data["profiles"][0]
    return None

def extract_affiliations_from_profile(profile):
    """Extract current and historical affiliations from a profile."""
    affiliations = []
    if not profile:
        return affiliations

    content = profile.get("content", {})

    # Check history for affiliations
    history = content.get("history", [])
    for entry in history:
        aff = {
            "institution": entry.get("institution", {}).get("value", "") if isinstance(entry.get("institution"), dict) else entry.get("institution", ""),
            "department": entry.get("department", {}).get("value", "") if isinstance(entry.get("department"), dict) else entry.get("department", ""),
            "position": entry.get("position", {}).get("value", "") if isinstance(entry.get("position"), dict) else entry.get("position", ""),
            "start": entry.get("start", None),
            "end": entry.get("end", None),
        }
        if aff["institution"]:
            affiliations.append(aff)

    # Check for current institution in other fields
    for field in ["institution", "affiliation"]:
        val = content.get(field)
        if val:
            if isinstance(val, dict):
                val = val.get("value", "")
            if val and not any(a["institution"] == val for a in affiliations):
                affiliations.append({"institution": val, "department": "", "position": "", "start": None, "end": None})

    return affiliations

def extract_links_from_profile(profile):
    """Extract personal links from profile."""
    links = {}
    if not profile:
        return links

    content = profile.get("content", {})

    for field in ["homepage", "gscholar", "dblp", "orcid", "linkedin", "wikipedia", "semanticScholar"]:
        val = content.get(field)
        if val:
            if isinstance(val, dict):
                val = val.get("value", "")
            if val:
                links[field] = val

    # Also check emails
    emails = content.get("emails", [])
    if emails:
        links["email"] = emails[0] if isinstance(emails[0], str) else ""

    # Names
    names = content.get("names", [])
    if names:
        for n in names:
            if isinstance(n, dict):
                preferred = n.get("preferred", False)
                if preferred or not links.get("fullname"):
                    first = n.get("first", "")
                    middle = n.get("middle", "")
                    last = n.get("last", "")
                    full = " ".join(filter(None, [first, middle, last]))
                    if full:
                        links["fullname"] = full

    return links

def main():
    print("=== Fetching all accepted papers ===")
    papers = fetch_all_papers()
    print(f"Found {len(papers)} accepted papers")

    for p in papers:
        print(f"  [{p['type']}] {p['title']}")
        print(f"    Authors: {', '.join(p['authors'])}")

    # Collect unique author IDs
    author_map = {}  # author_id -> {name, profiles, affiliations, links}
    for p in papers:
        for name, aid in zip(p["authors"], p["authorids"]):
            if aid not in author_map:
                author_map[aid] = {
                    "name": name,
                    "author_id": aid,
                    "papers": [],
                    "affiliations": [],
                    "links": {},
                    "profile_raw": None
                }
            author_map[aid]["papers"].append(p["id"])

    print(f"\n=== Fetching profiles for {len(author_map)} unique authors ===")

    for i, (aid, info) in enumerate(author_map.items()):
        print(f"  [{i+1}/{len(author_map)}] Fetching profile for {info['name']} ({aid})")
        profile = fetch_author_profile(aid)
        if profile:
            info["affiliations"] = extract_affiliations_from_profile(profile)
            info["links"] = extract_links_from_profile(profile)
            info["profile_raw"] = profile.get("content", {})
            print(f"    Found {len(info['affiliations'])} affiliations, {len(info['links'])} links")
        else:
            print(f"    No profile found")
        time.sleep(0.3)  # Rate limiting

    # Save everything
    output = {
        "papers": papers,
        "authors": author_map,
        "metadata": {
            "workshop": "NeurIPS 2025 Workshop on Biosecurity Safeguards for Generative AI (BioSafe GenAI)",
            "total_papers": len(papers),
            "total_authors": len(author_map),
            "oral_count": sum(1 for p in papers if p["type"] == "Oral"),
            "poster_count": sum(1 for p in papers if p["type"] == "Poster"),
        }
    }

    with open("/sessions/eloquent-jolly-knuth/biosafe_graph/raw_data.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n=== Summary ===")
    print(f"Papers: {output['metadata']['total_papers']} ({output['metadata']['oral_count']} oral, {output['metadata']['poster_count']} poster)")
    print(f"Unique authors: {output['metadata']['total_authors']}")
    print(f"Data saved to raw_data.json")

if __name__ == "__main__":
    main()
