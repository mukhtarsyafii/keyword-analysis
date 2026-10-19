#!/bin/bash
# Sync data WA/leads dashboard keyword-analysis (kolom WA & Leads/SO per LP).
# ponytail: skip fetch GSC/competitors (mahal quota) — cukup ledger WA + leads + rebuild.
cd /home/ubuntu/git/keyword-analysis || exit 1
python3 fetch_wa.py && timeout 300 python3 fetch_leads.py && python3 build_dashboard.py || exit 1
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "sync: data WA/leads $(date +%F)" && git push -q origin main
else
  echo "no changes"
fi
