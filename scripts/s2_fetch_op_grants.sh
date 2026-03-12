#!/bin/bash
# Sprint 2: Fetch Coefficient (prev. Open Philanthropy) full grants CSV
# Source: https://www.openphilanthropy.org/wp-admin/admin-ajax.php?action=generate_grants
# This is a single bulk download — no scraping, no rate limits.

set -e

OUTDIR="$(dirname "$0")/../data/raw"
OUTFILE="$OUTDIR/op_grants_full.csv"

mkdir -p "$OUTDIR"

echo "Downloading Coefficient (Open Philanthropy) grants CSV..."
curl -L -o "$OUTFILE" \
  "https://www.openphilanthropy.org/wp-admin/admin-ajax.php?action=generate_grants"

# Verify download
if [ ! -s "$OUTFILE" ]; then
  echo "ERROR: Download failed or file is empty"
  exit 1
fi

LINES=$(wc -l < "$OUTFILE")
echo "Downloaded: $OUTFILE ($LINES lines)"
echo "Header: $(head -1 "$OUTFILE")"
