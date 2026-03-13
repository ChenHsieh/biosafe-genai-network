# Biosecurity Atlas

An interactive map of the people, institutions, funding, and research connecting **biosafety, biosecurity, and AI**.

**[Explore the Atlas](https://chenhsieh.github.io/biosafe-genai-network/)**

---

## Why This Exists

AI is transforming biology at an extraordinary pace — from protein design to genome editing to pandemic forecasting. That creates both tremendous opportunity and real risk. Yet the landscape of who is working on these problems, who is funding them, and how the research community is connected has been surprisingly hard to see in one place.

The Biosecurity Atlas makes that landscape visible. It connects researchers from major AI-biology workshops to the grants, programs, and institutions behind their work, spanning government agencies (DARPA, NIH, NSF), philanthropic funders (Coefficient/Open Philanthropy), and international bodies (UKRI).

---

## What's in the Atlas

The atlas currently tracks **738 entities** and **1,216 connections** between them:

- **236 researchers** from biosecurity, AI safety, gene editing, and related fields
- **171 universities and research institutions** worldwide, with 70 geolocated
- **171 organizations** receiving funding for biosecurity and pandemic preparedness work
- **68 research programs** funded by DARPA, NIH, NSF, UKRI, and Coefficient
- **57 research papers** from four NeurIPS 2025 workshops and key biosecurity reports
- **$703M in tracked funding** across biosecurity, pandemic preparedness, and AI safety

Nineteen institutions serve as "bridge nodes" — they appear in both the research community and the funding landscape, including Harvard, Stanford, MIT, Oxford, Johns Hopkins, and SecureBio.

---

## How to Use It

Open the [live demo](https://chenhsieh.github.io/biosafe-genai-network/) and explore:

- **Search** for any person, institution, or program by name
- **Click** any node to see its connections, funding totals, and links to source material
- **Switch layouts** between grouped (by type), force-directed (clustered), and radial views
- **Filter by layer** to focus on just the workshop community, just the funding landscape, or everything together
- **Toggle edge types** to highlight specific relationships like funding flows, affiliations, or co-authorship

The visualization is fully self-contained — no server needed, works offline, and runs in any modern browser.

---

## Where the Data Comes From

Every connection in the atlas traces back to a verifiable source. The graph was built across 12 sprints, each adding one data source at a time:

- **NeurIPS 2025 Workshops**: Papers and authors from BioSafe GenAI, MLGenX, GenAI4Health, and AI4Science workshops via the OpenReview API
- **Coefficient / Open Philanthropy**: 272 bio-relevant grants from their public database, covering $543M in biosecurity, pandemic preparedness, and health R&D
- **DARPA & IARPA**: Programs including SAFE GENES, PREEMPT, PREPARE, PROPHECY, and Fun GCAT, sourced from official announcements
- **NIH**: $35M across gene editing, metagenomics, and bio-engineering grants via the NIH RePORTER API
- **NSF**: 10 matched awards ($9.5M) for key researchers via the NSF Awards API
- **UKRI**: Pandemic preparedness funding from the UK Gateway to Research API
- **Policy & Industry**: Biosecurity evaluations from OpenAI, Gryphon Scientific, RAND Corporation, Anthropic, and the NTI AIxBio Forum
- **Semantic Scholar**: Publication records for key PIs connecting their funded work to the published literature

A 14-point automated quality check runs after every update to catch dangling references, duplicate records, and structural issues.

---

## For Developers

The full technical roadmap, sprint logs, and schema details are in [ROADMAP.md](ROADMAP.md).

To reproduce or extend the atlas:

```bash
# Quality check
python scripts/quality_check.py

# Regenerate visualization
python scripts/generate_html_v3.py    # → index.html
python scripts/generate_webgl.py      # → index_webgl.html
```

Requires Python 3.8+, standard library only. All data files are in `data/` with raw sources preserved in `data/raw/`.

---

## Deploy

Push to GitHub and enable Pages (Settings → Pages → Branch: `main`, folder: `/`).

Both `index.html` and `index_webgl.html` are self-contained with all data embedded — no CDN dependencies.

---

## License

Data sourced from [OpenReview](https://openreview.net), [Coefficient/Open Philanthropy](https://www.openphilanthropy.org/grants/), [NIH RePORTER](https://reporter.nih.gov/), [NSF Awards](https://www.nsf.gov/awardsearch/), and [UKRI Gateway to Research](https://gtr.ukri.org/) (all public data). Visualization code is MIT licensed.
