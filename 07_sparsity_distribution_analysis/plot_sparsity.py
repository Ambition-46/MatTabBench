#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate plots for sparsity analysis and copy files into output folder.
Produces:
 - rank_frequency.png (log-log) from entities_per_property.csv
 - properties_per_entity_cdf.png (CDF) from properties_per_entity.csv
 - result_set_size_hist.png from sparsity_report.json histogram
Copies relevant files into target folder.
"""
import os
import json
import shutil
import math
from pathlib import Path

SRC_DIR = Path('.')
OUT_DIR = Path('.')
OUT_DIR.mkdir(exist_ok=True)

# plotting imports
try:
    import pandas as pd
    import matplotlib
    # use non-interactive backend to allow headless image generation
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
except Exception as e:
    print('Missing plotting dependencies:', e)
    print('Install with: pip install pandas matplotlib numpy')
    raise

# 1) Rank-frequency (entities per property, 0-coverage properties excluded from log-log)
ep_csv = SRC_DIR / 'entities_per_property.csv'
if ep_csv.exists():
    df_ep = pd.read_csv(ep_csv)
    counts = df_ep['entity_count'].astype(int).values
    counts_sorted = np.sort(counts[counts > 0])[::-1]
    ranks = np.arange(1, len(counts_sorted)+1)

    plt.figure(figsize=(6,4))
    plt.loglog(ranks, counts_sorted, marker='.', linestyle='none')
    plt.xlabel('Rank (covered properties only)')
    plt.ylabel('Entities per property (count)')
    plt.title('Rank-frequency (log-log) of property coverage')
    plt.grid(True, which='both', ls='--', lw=0.5)
    p1 = OUT_DIR / 'rank_frequency.png'
    plt.tight_layout()
    plt.savefig(p1, dpi=200)
    plt.close()
    print('Saved', p1)
else:
    print('Missing', ep_csv)

# 2) CDF of properties per entity
pe_csv = SRC_DIR / 'properties_per_entity.csv'
if pe_csv.exists():
    df_pe = pd.read_csv(pe_csv)
    vals = df_pe['property_count'].astype(int).values
    vals_sorted = np.sort(vals)
    cdf = np.arange(1, len(vals_sorted)+1) / len(vals_sorted)

    plt.figure(figsize=(6,4))
    plt.plot(vals_sorted, cdf)
    plt.xscale('linear')
    plt.xlabel('Properties per entity')
    plt.ylabel('CDF')
    plt.title('CDF of properties per entity')
    plt.grid(True, ls='--', lw=0.5)
    p2 = OUT_DIR / 'properties_per_entity_cdf.png'
    plt.tight_layout()
    plt.savefig(p2, dpi=200)
    plt.close()
    print('Saved', p2)
else:
    print('Missing', pe_csv)

# 3) Result set size histogram (from sparsity_report.json)
sr = SRC_DIR / 'sparsity_report.json'
if sr.exists():
    with open(sr, 'r', encoding='utf-8') as f:
        report = json.load(f)
    hist = report.get('result_set_size_stats', {}).get('histogram_samples', {})
    # ensure ordered bins
    bins = ['0','1','2-5','6-20','21-100','>100']
    counts = [hist.get(b,0) for b in bins]

    plt.figure(figsize=(6,4))
    plt.bar(bins, counts, color='C0')
    plt.xlabel('Result set size bins')
    plt.ylabel('Number of samples')
    plt.title('Result set size distribution (500 samples)')
    p3 = OUT_DIR / 'result_set_size_hist.png'
    plt.tight_layout()
    plt.savefig(p3, dpi=200)
    plt.close()
    print('Saved', p3)
else:
    print('Missing', sr)

# 4) Copy auxiliary files into OUT_DIR
to_copy = [
    'sparsity_report.json', 'sparsity_summary.txt', 'entities_per_property.csv',
    'properties_per_entity.csv', 'compute_sparsity.py'
]
for fn in to_copy:
    src = SRC_DIR / fn
    if src.exists():
        dst = OUT_DIR / fn
        if src.resolve() != dst.resolve():
            shutil.copy(src, dst)
            print('Copied', src, '->', dst)
        else:
            print('Skip self-copy:', fn)
    else:
        print('Not found, skip copy:', fn)

print('All outputs placed in', OUT_DIR)
