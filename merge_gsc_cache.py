#!/usr/bin/env python3
"""Merge a single-property GSC refresh into the full gsc_raw/daily cache.

fetch_gsc.py --site X rewrites the cache with only that property, so a
per-site refresh would drop every other brand. Restore the full cache first
(backup arg), then overlay the fresh rows.
"""
import gzip, json, sys

fresh_raw = json.load(gzip.open('data/gsc_raw.json.gz', 'rt', encoding='utf-8'))
fresh_day = json.load(gzip.open('data/gsc_daily.json.gz', 'rt', encoding='utf-8'))
old_raw = json.load(open(sys.argv[1]))
old_day = json.load(open(sys.argv[2]))

raw = dict(old_raw); raw.update(fresh_raw)
day = dict(old_day); day.update(fresh_day)

for name, payload in (('gsc_raw.json', raw), ('gsc_daily.json', day)):
    with gzip.open('data/' + name + '.gz', 'wt', encoding='utf-8') as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
print(f'old {len(old_raw)} + fresh {len(fresh_raw)} -> {len(raw)} pages')