"""
v10 META-ANALYSIS: SalesBased MinLayers v2-v9
CalculationId=233, Douglas DE
Self-contained — generates all charts + HTML locally.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime

VERSION = 'v10'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SCRIPT_DIR, exist_ok=True)
sns.set_style("whitegrid")
NOW_STR = datetime.now().strftime('%Y-%m-%d %H:%M')

print("=" * 60)
print(f"Generating v10 meta-analysis reports...")
print("=" * 60)

# ============================================================
# EMBEDDED DATA (consolidated from v2-v9)
# ============================================================

# --- Constant params ---
PARAMS = {
    'pairs': 42404, 'source_skus': 36770, 'target_skus': 41631, 'redist_qty': 48754,
    'stores': 353, 'products': 5152, 'orderable_pct': 95.4,
}

# --- KPI evolution across versions (source) ---
# v2-v8 share same base data; v9 independent recalc
SRC_KPI_VERSIONS = {
    # version: (os4m_qty, os4m_pct, os_t_qty, os_t_pct, ro4m_qty, ro4m_pct, ro_t_qty, ro_t_pct)
    'v2': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v3': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v4': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v5': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v6': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v7': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v8': (1464, 3.0, 5578, 11.4, 7980, 16.4, 16615, 34.1),
    'v9': (1541, 3.2, 5626, 11.5, 8045, 16.5, 16615, 34.1),
}

# --- KPI evolution (target) ---
TGT_KPI_VERSIONS = {
    # version: (st4m, st_t, st1_4m, st1_t, ns4m_skus, ns4m_pct, as_t_skus, as_t_pct)
    'v2': (46.3, 70.1, 70.6, 88.4, 17552, 42.2, 24862, 59.7),
    'v5': (45.3, 69.2, 58.2, 79.6, 17552, 42.2, 24862, 59.7),
    'v9': (45.4, 69.2, 62.9, 82.6, 17468, 42.0, 24860, 59.7),
}

# --- Velocity Segments (final v8-v9, with CalendarWeight 0.7) ---
SEGMENTS = [
    ('TrueDead',    18385, 36.9, 0.0,   22260),
    ('PartialDead',  3599, 56.7, 0.0,    4664),
    ('BriefNoSale',    98, 85.7, 0.0,       0),
    ('SlowFull',    10863, 66.4, 0.148, 14586),
    ('SlowPartial',  2038, 77.2, 0.239,  3130),
    ('ActiveSeller', 1778, 95.2, 0.919,  3941),
]

# --- Segment x Store (v9 data) ---
# (segment, store, skus, redist_qty, os4m%, os_t%, ro4m%, ro_t%, sold_after%)
SEG_STORE = [
    ('TrueDead','Weak',5233,6245,1.0,4.3,9.6,21.6,32.6),
    ('TrueDead','Mid',8240,10063,1.3,6.1,11.5,26.1,37.3),
    ('TrueDead','Strong',4912,5990,2.1,8.0,12.8,28.6,40.7),
    ('PartialDead','Weak',940,1125,2.8,9.9,16.7,33.8,48.7),
    ('PartialDead','Mid',1610,2072,4.2,14.1,19.4,38.2,57.9),
    ('PartialDead','Strong',1049,1467,5.5,16.8,18.3,36.4,62.2),
    ('SlowPartial','Weak',421,626,1.8,9.1,12.1,30.0,71.7),
    ('SlowPartial','Mid',800,1192,3.5,12.3,17.0,34.7,72.9),
    ('SlowPartial','Strong',817,1312,3.7,15.6,19.7,36.4,84.2),
    ('SlowFull','Weak',2122,2710,2.5,10.3,18.2,36.3,56.0),
    ('SlowFull','Mid',4697,6276,4.4,15.2,23.0,43.4,63.9),
    ('SlowFull','Strong',4044,5598,5.3,19.1,23.5,46.8,74.7),
    ('ActiveSeller','Weak',99,193,1.6,27.5,21.2,46.6,90.9),
    ('ActiveSeller','Mid',431,1003,4.8,18.6,20.0,44.4,91.9),
    ('ActiveSeller','Strong',1248,2745,5.7,21.3,20.9,44.0,96.7),
]
STORES = ['Weak', 'Mid', 'Strong']

# --- CalendarWeight ---
CALWEIGHT = {'novdec_share': 26.5, 'expected': 16.7, 'lift': 1.59, 'weight': 0.7, 'reclassified': 734}

# --- LastSaleGap ---
LAST_SALE_GAP = [
    ('0-30d', 1472, 13.1, 35.2, 90.0),
    ('31-90d', 2280, 14.8, 39.4, 85.2),
    ('91-180d', 3116, 15.6, 45.5, 76.4),
    ('181-365d', 7850, 18.1, 44.0, 61.8),
    ('365-730d', 6588, 9.0, 30.9, 42.4),
    ('730d+/Never', 15464, 6.9, 26.1, 39.4),
]

# --- Source BrandFit ---
SRC_BRANDFIT = [
    ('TrueDead', 35.3, 43.4, 8.1),
    ('SlowFull', 64.0, 74.7, 10.7),
    ('SlowPartial', 72.3, 82.1, 9.8),
    ('PartialDead', 55.4, 60.7, 5.3),
    ('ActiveSeller', 92.2, 96.8, 4.6),
]

# --- Target SalesBucket x Store ---
TGT_STORE_SALES = [
    ('0','Weak',139,23.5,35.6,73.4,32.4),
    ('0','Mid',341,23.4,41.6,73.3,37.8),
    ('0','Strong',254,37.2,54.6,60.6,52.8),
    ('1-2','Weak',1972,26.5,47.2,65.4,38.1),
    ('1-2','Mid',4507,28.9,51.3,61.7,41.0),
    ('1-2','Strong',3640,32.3,56.4,57.7,47.1),
    ('3-5','Weak',2601,41.6,65.8,44.8,54.3),
    ('3-5','Mid',7760,41.0,65.9,45.3,54.6),
    ('3-5','Strong',9052,45.5,71.8,40.5,61.1),
    ('6-10','Weak',879,59.2,82.4,27.5,74.6),
    ('6-10','Mid',3319,59.9,84.4,26.2,76.3),
    ('6-10','Strong',4835,63.2,86.2,22.2,78.8),
    ('11+','Weak',178,73.6,91.9,12.4,84.8),
    ('11+','Mid',806,72.6,93.3,11.7,87.7),
    ('11+','Strong',1348,77.4,94.0,10.6,89.5),
]

# --- Target BrandFit 9-matrix ---
BRAND_FIT = [
    ('Weak','BrandWeak',2426,56.1,34.0),
    ('Weak','BrandMid',1247,62.9,27.6),
    ('Weak','BrandStrong',2096,68.4,21.9),
    ('Mid','BrandWeak',4055,60.2,29.6),
    ('Mid','BrandMid',3559,64.5,25.7),
    ('Mid','BrandStrong',9119,70.0,20.2),
    ('Strong','BrandWeak',2239,65.7,24.7),
    ('Strong','BrandMid',2844,70.5,20.1),
    ('Strong','BrandStrong',14046,75.8,15.4),
]

# --- BrandFit Graduation by SalesBucket ---
BRANDFIT_DELTA = [
    ('0 (no sales)', '+17 to +34pp', -1, +1),
    ('1-2', '+7 to +9pp', -1, +1),
    ('3-5', '+6 to +8pp', -1, 0),
    ('6-10', '+2 to +3pp', 0, 0),
    ('11+', '<2pp', 0, 0),
]

# BrandFit detail for Strong stores
BRANDFITGRAD_STRONG = [
    ('0', 28.8, 63.2, 34.4),
    ('1-2', 50.7, 57.9, 7.2),
    ('3-5', 65.7, 73.4, 7.7),
    ('6-10', 83.2, 86.6, 3.4),
    ('11+', 91.8, 94.0, 2.2),
]

# --- Store decile data ---
DECILES = list(range(1, 11))
SRC_OVERSELL_4M = [2.1, 1.4, 2.1, 2.2, 2.8, 3.1, 3.7, 3.4, 4.5, 4.6]
SRC_REORDER_TOT = [24.0, 27.8, 28.8, 30.5, 33.6, 35.1, 36.2, 37.3, 39.0, 38.6]
TGT_ALLSOLD = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.0, 60.6, 63.0, 70.1]
TGT_NOTHING = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Flow matrix ---
FLOW = [
    ('Weak','Weak',1179,2.8),('Weak','Mid',4099,9.7),('Weak','Strong',4661,11.0),
    ('Mid','Weak',2437,5.7),('Mid','Mid',7315,17.3),('Mid','Strong',8330,19.6),
    ('Strong','Weak',2256,5.3),('Strong','Mid',5639,13.3),('Strong','Strong',6488,15.3),
]

# --- Pair analysis ---
PAIRS = [('Win-Win',21443,50.6),('Win-Lose',15257,36.0),('Lose-Win',3841,9.1),('Lose-Lose',1863,4.4)]

# --- Decision trees ---
SRC_ML = {
    ('TrueDead','Weak'):1,('TrueDead','Mid'):1,('TrueDead','Strong'):1,
    ('PartialDead','Weak'):1,('PartialDead','Mid'):1,('PartialDead','Strong'):2,
    ('SlowPartial','Weak'):2,('SlowPartial','Mid'):2,('SlowPartial','Strong'):3,
    ('SlowFull','Weak'):2,('SlowFull','Mid'):2,('SlowFull','Strong'):3,
    ('ActiveSeller','Weak'):3,('ActiveSeller','Mid'):4,('ActiveSeller','Strong'):4,
}
TGT_ML = {
    ('0','Weak'):1,('0','Mid'):1,('0','Strong'):1,
    ('1-2','Weak'):1,('1-2','Mid'):1,('1-2','Strong'):2,
    ('3-5','Weak'):1,('3-5','Mid'):2,('3-5','Strong'):3,
    ('6-10','Weak'):2,('6-10','Mid'):3,('6-10','Strong'):3,
    ('11+','Weak'):2,('11+','Mid'):3,('11+','Strong'):4,
}

# Current ML distribution
SRC_CURRENT_ML = [(0,1709),(1,31965),(2,2680),(3,416)]
TGT_CURRENT_ML = [(1,4730),(2,31977),(3,4924)]

# Store distribution
STORE_DIST = [('Weak',107),('Mid',140),('Strong',105)]

# --- Evolution: Source Lookup across versions ---
# v6, v7, v8-v9
SRC_ML_EVO = {
    ('TrueDead','Weak'):    [1,1,1],
    ('TrueDead','Mid'):     [1,1,1],
    ('TrueDead','Strong'):  [1,1,1],
    ('PartialDead','Weak'): [1,1,1],
    ('PartialDead','Mid'):  [1,1,1],
    ('PartialDead','Strong'):[2,2,2],
    ('SlowPartial','Weak'): [2,2,2],
    ('SlowPartial','Mid'):  [2,2,2],
    ('SlowPartial','Strong'):[3,3,3],
    ('SlowFull','Weak'):    [1,1,2],  # changed v8
    ('SlowFull','Mid'):     [2,2,2],
    ('SlowFull','Strong'):  [2,2,3],  # changed v8
    ('ActiveSeller','Weak'):[3,3,3],
    ('ActiveSeller','Mid'): [4,4,4],
    ('ActiveSeller','Strong'):[4,4,4],
}

# v6, v7, v8-v9
TGT_ML_EVO = {
    ('0','Weak'):     [1,1,1],
    ('0','Mid'):      [1,1,1],
    ('0','Strong'):   [2,1,1],  # changed v7
    ('1-2','Weak'):   [1,1,1],
    ('1-2','Mid'):    [2,1,1],  # changed v7
    ('1-2','Strong'): [2,2,2],
    ('3-5','Weak'):   [2,1,1],  # changed v7
    ('3-5','Mid'):    [2,2,2],
    ('3-5','Strong'): [2,3,3],  # changed v7
    ('6-10','Weak'):  [2,2,2],
    ('6-10','Mid'):   [2,3,3],  # changed v7
    ('6-10','Strong'):[2,3,3],  # changed v7
    ('11+','Weak'):   [3,2,2],  # changed v7
    ('11+','Mid'):    [3,3,3],
    ('11+','Strong'): [3,4,4],  # changed v7
}


# ============================================================
# CHART GENERATION
# ============================================================

# ---- Chart 1: CalendarWeight + Segment sizes ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
bar_labels = ['Ocekavano\n(rovnomerne)', 'Skutecne\n(Nov+Dec)']
bar_vals = [CALWEIGHT['expected'], CALWEIGHT['novdec_share']]
bars = axes[0].bar(bar_labels, bar_vals, color=['#3498db','#e74c3c'], edgecolor='#333', linewidth=0.5, width=0.5)
axes[0].set_ylabel('Podil na rocnich prodejich %')
axes[0].set_title('Nov+Dec: ocekavany vs skutecny podil\n(2 mesice z 12 = 16.7%)', fontsize=11, fontweight='bold')
axes[0].set_ylim(0, 40)
for b, v in zip(bars, bar_vals):
    axes[0].text(b.get_x()+b.get_width()/2, v+0.8, f'{v}%', ha='center', fontsize=14, fontweight='bold')
axes[0].annotate(f'Lift={CALWEIGHT["lift"]}x => CW={CALWEIGHT["weight"]}',
    xy=(1, CALWEIGHT['novdec_share']), xytext=(1.3, CALWEIGHT['novdec_share']+5),
    fontsize=11, fontweight='bold', color='#8e44ad',
    arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=2))
axes[0].axhline(y=CALWEIGHT['expected'], color='#3498db', linestyle='--', alpha=0.5)

seg_names = [s[0] for s in SEGMENTS if s[0] not in ('BriefNoSale',)]
seg_counts = [s[1] for s in SEGMENTS if s[0] not in ('BriefNoSale',)]
seg_colors = ['#95a5a6','#bdc3c7','#aed6f1','#85c1e9','#e74c3c']
bars2 = axes[1].barh(seg_names, seg_counts, color=seg_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_xlabel('SKU Count')
axes[1].set_title('Velocity segmenty (CalendarWeight 0.7)', fontsize=11, fontweight='bold')
for b, v in zip(bars2, seg_counts):
    axes[1].text(v+200, b.get_y()+b.get_height()/2, f'{v:,}', va='center', fontsize=10, fontweight='bold')
axes[1].invert_yaxis()
fig.suptitle('v10 META: Vianocna korekce a segmentace source SKU', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_01_calendar_segments.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_01")

# ---- Chart 2: SoldAfter by segment ----
fig, ax = plt.subplots(figsize=(14, 7))
sa_segs = [s[0] for s in SEGMENTS if s[0] not in ('BriefNoSale',)]
sa_vals = [s[2] for s in SEGMENTS if s[0] not in ('BriefNoSale',)]
y_sa = np.arange(len(sa_segs))
sa_colors = ['#27ae60' if v > 70 else ('#f39c12' if v > 50 else '#e74c3c') for v in sa_vals]
bars = ax.barh(y_sa, sa_vals, color=sa_colors, edgecolor='#333', linewidth=0.5, height=0.6)
ax.set_yticks(y_sa); ax.set_yticklabels(sa_segs, fontsize=11)
ax.set_xlabel('Sold After %', fontsize=11)
ax.set_title('Sold After % podle segmentu (source SKU prodane po redistribuci)', fontsize=12, fontweight='bold')
ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5, linewidth=2)
ax.axvline(x=80, color='#27ae60', linestyle='--', alpha=0.5, linewidth=2)
for i, v in enumerate(sa_vals):
    skus = [s[1] for s in SEGMENTS if s[0] == sa_segs[i]][0]
    ax.text(v+1, i, f'{v}% ({skus:,} SKU)', va='center', fontsize=10, fontweight='bold')
ax.set_xlim(0, 115); ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_02_sold_after.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_02")

# ---- Chart 3: Source Segment x Store heatmaps (OS + RO) ----
seg_order = ['TrueDead','PartialDead','SlowPartial','SlowFull','ActiveSeller']
os_data, ro_data = [], []
for seg in seg_order:
    row_o, row_r = [], []
    for s in STORES:
        r = [x for x in SEG_STORE if x[0]==seg and x[1]==s][0]
        row_o.append(r[5]); row_r.append(r[7])
    os_data.append(row_o); ro_data.append(row_r)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(np.array(os_data), annot=True, fmt='.1f', cmap='YlOrRd',
    xticklabels=STORES, yticklabels=seg_order, ax=axes[0], vmin=0, vmax=30, linewidths=1,
    cbar_kws={'label': 'Oversell Total %'})
axes[0].set_title('SOURCE: Oversell Total %', fontsize=11)
sns.heatmap(np.array(ro_data), annot=True, fmt='.1f', cmap='YlOrRd',
    xticklabels=STORES, yticklabels=seg_order, ax=axes[1], vmin=20, vmax=50, linewidths=1,
    cbar_kws={'label': 'Reorder Total %'})
axes[1].set_title('SOURCE: Reorder Total %', fontsize=11)
fig.suptitle('v10: Source Segment x Store (s CalendarWeight 0.7)', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_03_src_heatmaps.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_03")

# ---- Chart 4: Store decile gradients ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(DECILES, SRC_OVERSELL_4M, 'o-', color='#3498db', lw=2, label='Oversell 4M%')
axes[0].plot(DECILES, SRC_REORDER_TOT, 's--', color='#e74c3c', lw=2, label='Reorder Total%')
axes[0].fill_between(DECILES, SRC_REORDER_TOT, alpha=0.1, color='#e74c3c')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)'); axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: OS 4M + RO Total'); axes[0].legend(fontsize=8); axes[0].set_xticks(DECILES)

axes[1].plot(DECILES, TGT_ALLSOLD, 'o-', color='#27ae60', lw=2, label='All Sold%')
axes[1].plot(DECILES, TGT_NOTHING, 's-', color='#e74c3c', lw=2, label='Nothing Sold%')
axes[1].fill_between(DECILES, TGT_ALLSOLD, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile'); axes[1].set_ylabel('%')
axes[1].set_title('TARGET: All-sold vs Nothing-sold'); axes[1].legend(fontsize=8); axes[1].set_xticks(DECILES)

eff = [a/(a+n)*100 for a,n in zip(TGT_ALLSOLD, TGT_NOTHING)]
axes[2].bar(DECILES, eff, color=['#e74c3c' if e<65 else ('#f39c12' if e<72 else '#27ae60') for e in eff])
axes[2].set_xlabel('Store Decile'); axes[2].set_ylabel('Efficiency %')
axes[2].set_title('TARGET: Redistrib. efektivita'); axes[2].set_xticks(DECILES)
axes[2].axhline(y=70, color='#f39c12', linestyle='--', alpha=0.5)
for d, e in zip(DECILES, eff):
    axes[2].text(d, e+0.5, f'{e:.0f}%', ha='center', fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_04_store_deciles.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_04")

# ---- Chart 5: Target heatmaps (AllSold + NothingSold + BrandFit) ----
tgt_buckets = ['0','1-2','3-5','6-10','11+']
ns_arr = np.array([[73.4,73.3,60.6],[65.4,61.7,57.7],[44.8,45.3,40.5],[27.5,26.2,22.2],[12.4,11.7,10.6]])
as_arr = np.array([[32.4,37.8,52.8],[38.1,41.0,47.1],[54.3,54.6,61.1],[74.6,76.3,78.8],[84.8,87.7,89.5]])
bf_arr = np.array([[56.1,62.9,68.4],[60.2,64.5,70.0],[65.7,70.5,75.8]])

fig, axes = plt.subplots(1, 3, figsize=(20, 6))
sns.heatmap(as_arr, annot=True, fmt='.1f', cmap='RdYlGn', xticklabels=STORES, yticklabels=tgt_buckets,
    ax=axes[0], vmin=30, vmax=90, linewidths=1, cbar_kws={'label': 'All-sold Total %'})
axes[0].set_title('Target All-Sold Total % (USPECH)', fontsize=10); axes[0].set_ylabel('Sales Bucket')
sns.heatmap(ns_arr, annot=True, fmt='.1f', cmap='RdYlGn_r', xticklabels=STORES, yticklabels=tgt_buckets,
    ax=axes[1], vmin=10, vmax=75, linewidths=1, cbar_kws={'label': 'Nothing sold %'})
axes[1].set_title('Target Nothing-Sold % (PROBLEM)', fontsize=10); axes[1].set_ylabel('Sales Bucket')
sns.heatmap(bf_arr, annot=True, fmt='.1f', cmap='RdYlGn', xticklabels=['BrandWeak','BrandMid','BrandStrong'],
    yticklabels=STORES, ax=axes[2], vmin=50, vmax=80, linewidths=1, cbar_kws={'label': 'ST Total %'})
axes[2].set_title('Brand-Store Fit: ST Total %', fontsize=10); axes[2].set_ylabel('Store Strength')
fig.suptitle('v10: Target analytika — SalesBucket, Store, BrandFit', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_05_tgt_heatmaps.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_05")

# ---- Chart 6: Pair analysis + Flow matrix ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
pair_labels = [r[0] for r in PAIRS]; pair_counts = [r[1] for r in PAIRS]
pair_colors = ['#27ae60','#f39c12','#e67e22','#e74c3c']
axes[0].pie(pair_counts, labels=pair_labels, colors=pair_colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize':9})
axes[0].set_title('Parova analyza: Source+Target', fontsize=10)

pct_matrix = np.zeros((3,3))
for r in FLOW:
    pct_matrix[STORES.index(r[0])][STORES.index(r[1])] = r[3]
sns.heatmap(pct_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
    xticklabels=['Tgt '+s for s in STORES], yticklabels=['Src '+s for s in STORES],
    ax=axes[1], linewidths=1, cbar_kws={'label': '% of pairs'})
axes[1].set_title('Flow Matrix: % z celkovych paru', fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_06_pairs_flow.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_06")

# ---- Chart 7: BrandFit graduation ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
bf_bkts = [r[0] for r in BRANDFITGRAD_STRONG]
bw_vals = [r[1] for r in BRANDFITGRAD_STRONG]
bs_vals = [r[2] for r in BRANDFITGRAD_STRONG]
x_bf = np.arange(len(bf_bkts)); w_bf = 0.35
axes[0].bar(x_bf-w_bf/2, bw_vals, w_bf, color='#e74c3c', label='BrandWeak', edgecolor='#333', linewidth=0.5)
axes[0].bar(x_bf+w_bf/2, bs_vals, w_bf, color='#27ae60', label='BrandStrong', edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(x_bf); axes[0].set_xticklabels(bf_bkts)
axes[0].set_xlabel('Sales Bucket'); axes[0].set_ylabel('ST Total %')
axes[0].set_title('Strong stores: BW vs BS dle SalesBucket', fontsize=11, fontweight='bold')
axes[0].legend(); axes[0].set_ylim(0, 110)
for i, (bw, bs) in enumerate(zip(bw_vals, bs_vals)):
    axes[0].annotate(f'+{bs-bw:.0f}pp', xy=(i, max(bw,bs)+4), fontsize=9, fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#fff3cd', edgecolor='#f39c12', alpha=0.8))

deltas = [r[3] for r in BRANDFITGRAD_STRONG]
y_d = np.arange(len(bf_bkts))
d_colors = ['#e74c3c' if d>20 else ('#f39c12' if d>5 else '#95a5a6') for d in deltas]
axes[1].barh(y_d, deltas, color=d_colors, edgecolor='#333', linewidth=0.5, height=0.6)
axes[1].set_yticks(y_d); axes[1].set_yticklabels(bf_bkts)
axes[1].set_xlabel('Delta ST (BS-BW) pp'); axes[1].set_title('Delta: vliv BrandFit klesa s SalesBucket', fontsize=11, fontweight='bold')
axes[1].invert_yaxis()
for i, d in enumerate(deltas):
    sig = 'VYZNAMNY' if d>20 else ('stredni' if d>5 else 'maly')
    axes[1].text(d+0.5, i, f'+{d:.0f}pp ({sig})', va='center', fontsize=9, fontweight='bold')
fig.suptitle('v10: BrandFit Graduation — vliv klesa s poctem prodejov', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_07_brandfit_grad.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_07")

# ---- Chart 8: Decision tree heatmaps (Source + Target) ----
seg_order_dt = ['TrueDead','PartialDead','SlowPartial','SlowFull','ActiveSeller']
src_ml_arr = np.array([[SRC_ML[(seg,s)] for s in STORES] for seg in seg_order_dt])
tgt_ml_arr = np.array([[TGT_ML[(b,s)] for s in STORES] for b in tgt_buckets])

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(src_ml_arr, annot=True, fmt='d', cmap='RdYlGn_r', xticklabels=STORES, yticklabels=seg_order_dt,
    ax=axes[0], vmin=0, vmax=4, linewidths=2, cbar_kws={'label': 'MinLayer'})
axes[0].set_title('SOURCE: Navrzeny ML (Segment x Store)', fontsize=11, fontweight='bold')
sns.heatmap(tgt_ml_arr, annot=True, fmt='d', cmap='RdYlGn_r', xticklabels=STORES, yticklabels=tgt_buckets,
    ax=axes[1], vmin=0, vmax=4, linewidths=2, cbar_kws={'label': 'MinLayer'})
axes[1].set_title('TARGET: Navrzeny ML (SalesBucket x Store)', fontsize=11, fontweight='bold')
fig.suptitle('v10 FINAL: Decision Tree Lookup tabulky (ML 0-4)', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_08_decision_tree.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_08")

# ---- Chart 9: ML distribution current vs proposed ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Source: current vs proposed
src_cur = {ml: cnt for ml, cnt in SRC_CURRENT_ML}
src_prop = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
for (seg, sto), ml in SRC_ML.items():
    row = [r for r in SEG_STORE if r[0]==seg and r[1]==sto]
    if row:
        src_prop[ml] = src_prop.get(ml, 0) + row[0][2]

mls = [0, 1, 2, 3, 4]
x_ml = np.arange(len(mls)); w_ml = 0.35
cur_vals = [src_cur.get(m, 0) for m in mls]
prop_vals = [src_prop.get(m, 0) for m in mls]
axes[0].bar(x_ml - w_ml/2, cur_vals, w_ml, color='#bdc3c7', label='Aktualni', edgecolor='#333', linewidth=0.5)
axes[0].bar(x_ml + w_ml/2, prop_vals, w_ml, color='#8e44ad', label='Navrzeny', edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(x_ml); axes[0].set_xticklabels([f'ML={m}' for m in mls])
axes[0].set_ylabel('SKU count'); axes[0].set_title('SOURCE: Aktualni vs Navrzeny ML', fontsize=11, fontweight='bold')
axes[0].legend()
for i, (c, p) in enumerate(zip(cur_vals, prop_vals)):
    if c > 0: axes[0].text(i-w_ml/2, c+300, f'{c:,}', ha='center', fontsize=7, rotation=45)
    if p > 0: axes[0].text(i+w_ml/2, p+300, f'{p:,}', ha='center', fontsize=7, rotation=45, color='#8e44ad')

# Target: current vs proposed
tgt_cur = {ml: cnt for ml, cnt in TGT_CURRENT_ML}
tgt_prop = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
for (bkt, sto), ml in TGT_ML.items():
    rows = [r for r in TGT_STORE_SALES if r[0]==bkt and r[1]==sto]
    if rows:
        tgt_prop[ml] = tgt_prop.get(ml, 0) + rows[0][2]

cur_t = [tgt_cur.get(m, 0) for m in mls]
prop_t = [tgt_prop.get(m, 0) for m in mls]
axes[1].bar(x_ml - w_ml/2, cur_t, w_ml, color='#bdc3c7', label='Aktualni', edgecolor='#333', linewidth=0.5)
axes[1].bar(x_ml + w_ml/2, prop_t, w_ml, color='#27ae60', label='Navrzeny', edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(x_ml); axes[1].set_xticklabels([f'ML={m}' for m in mls])
axes[1].set_ylabel('SKU count'); axes[1].set_title('TARGET: Aktualni vs Navrzeny ML', fontsize=11, fontweight='bold')
axes[1].legend()
for i, (c, p) in enumerate(zip(cur_t, prop_t)):
    if c > 0: axes[1].text(i-w_ml/2, c+300, f'{c:,}', ha='center', fontsize=7, rotation=45)
    if p > 0: axes[1].text(i+w_ml/2, p+300, f'{p:,}', ha='center', fontsize=7, rotation=45, color='#27ae60')

fig.suptitle('v10: ML distribuce — aktualni vs navrzeny (87% ML=1 → diferencovano)', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_09_ml_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_09")

# ---- Chart 10: Sold After vs Reorder by segment ----
fig, ax = plt.subplots(figsize=(14, 7))
v_segs = ['TrueDead','PartialDead','SlowPartial','SlowFull','ActiveSeller']
v_sa, v_ro = [], []
for seg in v_segs:
    rows = [r for r in SEG_STORE if r[0]==seg]
    ts = sum(r[2] for r in rows)
    v_sa.append(sum(r[2]*r[8] for r in rows)/ts)
    v_ro.append(sum(r[2]*r[7] for r in rows)/ts)
y_v = np.arange(len(v_segs)); w_v = 0.35
ax.barh(y_v-w_v/2, v_sa, w_v, color='#27ae60', label='Sold After%', edgecolor='#333', linewidth=0.5)
ax.barh(y_v+w_v/2, v_ro, w_v, color='#e74c3c', label='Reorder Total%', edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_v); ax.set_yticklabels(v_segs, fontsize=10)
ax.set_xlabel('%'); ax.set_title('Sold After% vs Reorder Total% podle segmentu', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)
for i, (sa, ro) in enumerate(zip(v_sa, v_ro)):
    ml_vals = [SRC_ML.get((v_segs[i],s),0) for s in STORES]
    ax.text(max(sa,ro)+1, i, f'ML={np.mean(ml_vals):.1f}', va='center', fontsize=8, color='#8e44ad', fontweight='bold')
ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_10_sa_vs_ro.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_10")

print("\nAll 10 charts generated.")

# ============================================================
# HTML GENERATION
# ============================================================

CSS_HTML = """
body { font-family: 'Segoe UI', sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }
h1 { color: #2c3e50; border-bottom: 3px solid #8e44ad; padding-bottom: 10px; }
h2 { color: #2c3e50; margin-top: 40px; border-left: 4px solid #8e44ad; padding-left: 12px; }
h3 { color: #34495e; }
h4 { color: #7f8c8d; margin-top: 25px; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: right; }
th { background: #8e44ad; color: white; }
tr:nth-child(even) { background: #f9f9f9; }
td:first-child, th:first-child { text-align: left; }
.bad { color: #e74c3c; font-weight: bold; }
.good { color: #27ae60; font-weight: bold; }
.warn { color: #e67e22; font-weight: bold; }
.section { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
img { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }
.metric { display: inline-block; background: white; padding: 12px 20px; margin: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; min-width: 140px; }
.metric .v { font-size: 24px; font-weight: bold; color: #2c3e50; }
.metric .l { font-size: 11px; color: #7f8c8d; }
.insight { background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }
.insight-good { background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }
.insight-bad { background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }
.insight-new { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }
.evo-table th { background: #34495e; font-size: 12px; }
.evo-table td { font-size: 12px; }
.changed { background: #fff3cd; }
pre { background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 12px; overflow-x: auto; }
.nav { background: #2c3e50; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; }
.nav a { color: #ecf0f1; margin-right: 20px; text-decoration: none; font-weight: bold; }
.nav a:hover { color: #8e44ad; }
.nav a.active { color: #8e44ad; border-bottom: 2px solid #8e44ad; padding-bottom: 4px; }
.source-header { background: #2980b9; color: white; padding: 8px 15px; border-radius: 4px 4px 0 0; margin-top: 20px; font-weight: bold; }
.target-header { background: #27ae60; color: white; padding: 8px 15px; border-radius: 4px 4px 0 0; margin-top: 20px; font-weight: bold; }
.source-box { border: 2px solid #2980b9; border-radius: 0 0 4px 4px; padding: 15px; margin-bottom: 20px; background: white; }
.target-box { border: 2px solid #27ae60; border-radius: 0 0 4px 4px; padding: 15px; margin-bottom: 20px; background: white; }
.ml-0 { background: #e8f8f5; } .ml-1 { background: #d5f5e3; } .ml-2 { background: #fdebd0; }
.ml-3 { background: #fadbd8; } .ml-4 { background: #f5b7b1; }
.arrow-up { color: #e74c3c; font-weight: bold; }
.arrow-down { color: #27ae60; font-weight: bold; }
.dir-up { background: #fce4e4; } .dir-down { background: #d4edda; } .dir-ok { background: #fef9e7; }
.v10-badge { background: #8e44ad; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
"""

def nav(active):
    links = [('consolidated_findings.html','Findings'),('consolidated_decision_tree.html','Decision Tree'),('definitions.html','Definitions')]
    h = '<div class="nav">'
    for i,(href,label) in enumerate(links):
        cls = ' class="active"' if i==active else ''
        h += f'<a href="{href}"{cls}>{label}</a>'
    h += '<span style="float:right;color:#7f8c8d;font-size:11px;">v10 META | v2-v9 | ML 0-4</span></div>'
    return h


# ############################################################
# HTML 1: FINDINGS
# ############################################################
print("\n--- Building Findings HTML ---")

# Build segment x store rows
seg_store_rows = ""
for r in SEG_STORE:
    seg,sto,cnt,rdq,os4,ost,ro4,rot,sa = r
    cls_o = 'good' if ost<10 else ('warn' if ost<15 else 'bad')
    cls_r = 'bad' if rot>40 else ('warn' if rot>35 else 'good')
    cls_sa = 'good' if sa>70 else ('warn' if sa>50 else 'bad')
    seg_store_rows += f'<tr><td>{seg}</td><td>{sto}</td><td>{cnt:,}</td><td class="{cls_o}">{ost}%</td><td class="{cls_r}">{rot}%</td><td class="{cls_sa}">{sa}%</td><td>{rdq:,}</td></tr>\n'

# Target rows
tgt_rows = ""
for r in TGT_STORE_SALES:
    sal,sto,cnt,st4,stt,pn,pa = r
    cls_n = 'bad' if pn>50 else ('warn' if pn>30 else 'good')
    cls_a = 'good' if pa>70 else ('warn' if pa>50 else 'bad')
    tgt_rows += f'<tr><td>{sal}</td><td>{sto}</td><td>{cnt:,}</td><td>{st4:.1f}%</td><td>{stt:.1f}%</td><td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n'

# BrandFit rows
bf_rows = ""
for r in BRAND_FIT:
    sto,bf,cnt,st_t,ns = r
    cls_s = 'good' if st_t>70 else ('warn' if st_t>60 else 'bad')
    cls_n = 'bad' if ns>30 else ('warn' if ns>25 else 'good')
    bf_rows += f'<tr><td>{sto}</td><td>{bf}</td><td>{cnt:,}</td><td class="{cls_s}">{st_t}%</td><td class="{cls_n}">{ns}%</td></tr>\n'

# BrandFit delta rows
bfd_rows = ""
for r in BRANDFIT_DELTA:
    sb,dr,mbw,mbs = r
    cls_bw = 'bad' if mbw<0 else ''
    cls_bs = 'good' if mbs>0 else ''
    bfd_rows += f'<tr><td><b>{sb}</b></td><td>{dr}</td><td class="{cls_bw}">{mbw:+d}</td><td class="{cls_bs}">{mbs:+d}</td></tr>\n'

# LastSaleGap rows
lsg_rows = ""
for r in LAST_SALE_GAP:
    gap,skus,ost,rot,sa = r
    cls_sa = 'good' if sa>70 else ('warn' if sa>50 else 'bad')
    lsg_rows += f'<tr><td>{gap}</td><td>{skus:,}</td><td>{ost}%</td><td>{rot}%</td><td class="{cls_sa}">{sa}%</td></tr>\n'

# Source BrandFit rows
sbf_rows = ""
for r in SRC_BRANDFIT:
    seg,bw,bs,delta = r
    mod = '+1 ML' if delta > 5 else 'ignorovat'
    if seg == 'ActiveSeller': mod = 'ignorovat (SA>92%)'
    sbf_rows += f'<tr><td>{seg}</td><td>{bw}%</td><td>{bs}%</td><td class="bad">+{delta}pp</td><td>{mod}</td></tr>\n'

html1 = f"""<!DOCTYPE html>
<html lang="cs"><head><meta charset="UTF-8"><title>v10 Findings — Meta-analyza v2-v9</title>
<style>{CSS_HTML}</style></head><body>
{nav(0)}

<h1>v10 — Meta-analyza verzi v2-v9 <span class="v10-badge">META</span></h1>
<p><b>CalculationId:</b> 233 | <b>ApplicationDate:</b> 2025-07-13 | <b>Tenant:</b> Douglas DE | <b>Generovano:</b> {NOW_STR}</p>
<p>Tato verze syntetizuje zjisteni ze vsech predchozich verzi (v2-v9). Backtest neni soucasti v10.</p>

<!-- 1. KPI -->
<h2>1. Celkove KPI</h2>
<div class="section">
<h3>1.1 Zakladni parametry (konstantni napric verzemi)</h3>
<table>
<tr><th>Parametr</th><th>Hodnota</th></tr>
<tr><td>Redistribucni pary</td><td>42 404</td></tr>
<tr><td>Source SKU</td><td>36 770</td></tr>
<tr><td>Target SKU</td><td>41 631</td></tr>
<tr><td>Redistribuovano ks</td><td>48 754</td></tr>
<tr><td>Prodejen (excl. ecomm)</td><td>353</td></tr>
<tr><td>Orderable (A-O + Z-O)</td><td>35 061 (95.4%)</td></tr>
</table>

<h3>1.2 Klicove metriky</h3>
<div style="text-align:center;">
<div class="metric"><div class="v good">3.0-3.2%</div><div class="l">Oversell 4M (cil 5-10%)</div></div>
<div class="metric"><div class="v bad">34.1%</div><div class="l">Reorder Total</div></div>
<div class="metric"><div class="v">69-70%</div><div class="l">ST Total</div></div>
<div class="metric"><div class="v bad">42%</div><div class="l">Nothing-sold 4M</div></div>
<div class="metric"><div class="v good">60%</div><div class="l">All-sold Total</div></div>
</div>

<div class="insight">
<b>Oversell je v cili</b> (3.0-3.2%, cil 5-10%). Hlavni problem je <b>reorder na 34.1%</b> — cil snizit o 10-15%.
Target: 42% SKU nemelo zadny prodej za 4M, ale 60% se prodalo uplne za celou dobu. Redistribuce funguje dobre tam,
kde produkt jde na odbyt, ale velka cast je zbytecna.
</div>

<h3>1.3 Source KPI — evoluce</h3>
<table class="evo-table">
<tr><th>Metrika</th><th>v2-v8</th><th>v9</th><th>Pozn.</th></tr>
<tr><td>Oversell 4M qty</td><td>1 464 (3.0%)</td><td class="changed">1 541 (3.2%)</td><td>v9 nezavisly prepocet</td></tr>
<tr><td>Oversell Total qty</td><td>5 578 (11.4%)</td><td class="changed">5 626 (11.5%)</td><td></td></tr>
<tr><td>Reorder 4M qty</td><td>7 980 (16.4%)</td><td class="changed">8 045 (16.5%)</td><td></td></tr>
<tr><td>Reorder Total qty</td><td>16 615 (34.1%)</td><td>16 615 (34.1%)</td><td>Stejne</td></tr>
</table>

<h3>1.4 Target KPI — evoluce</h3>
<table class="evo-table">
<tr><th>Metrika</th><th>v2-v4, v6-v8</th><th>v5</th><th>v9</th></tr>
<tr><td>ST 4M avg</td><td>46.3%</td><td>45.3%</td><td>45.4%</td></tr>
<tr><td>ST Total avg</td><td>70.1%</td><td>69.2%</td><td>69.2%</td></tr>
<tr><td>ST-1pc 4M avg</td><td>70.6%</td><td>58.2%</td><td>62.9%</td></tr>
<tr><td>Nothing-sold 4M</td><td>17 552 (42.2%)</td><td>17 552</td><td>17 468 (42.0%)</td></tr>
<tr><td>All-sold Total</td><td>24 862 (59.7%)</td><td>24 862</td><td>24 860 (59.7%)</td></tr>
</table>
</div>

<!-- 2. SOURCE -->
<h2>2. SOURCE — Velocity segmentace</h2>
<div class="source-header">SOURCE ANALYZA</div>
<div class="source-box">

<h3>2.1 Evoluce klasifikace</h3>
<table class="evo-table">
<tr><th>Verze</th><th>System</th><th>Segmenty</th></tr>
<tr><td>v2-v5</td><td>Pattern-based</td><td>Dead, Dying, Sporadic, Consistent, Declining</td></tr>
<tr><td>v6-v7</td><td>Velocity-normalized</td><td>TrueDead, PartialDead, BriefNoSale, SlowFull, SlowPartial, ActiveSeller</td></tr>
<tr><td>v8-v9</td><td>Velocity + CalendarWeight</td><td>Stejne segmenty, 734 SKU reklasifikovano z ActiveSeller do SlowFull/SlowPartial</td></tr>
</table>

<h3>2.2 CalendarWeight (vianocna korekce)</h3>
<img src="fig_01_calendar_segments.png" alt="CalendarWeight + Segments">
<div class="insight">
<b>Douglas = parfumerie:</b> Nov+Dec = 26.5% rocnich prodejov (ocekavano 16.7%, lift 1.59×).
CalendarWeight 0.7 aplikovany na pololeti s Nov+Dec. 734 SKU reklasifikovano z ActiveSeller (sold_after 91%).
CW 0.7 je konzervativni — skutecny by odpovidal ~0.63.
</div>

<h3>2.3 Velocity segmenty — finalni (v8-v9)</h3>
<table>
<tr><th>Segment</th><th>Definice</th><th>SKU</th><th>Podil</th><th>Sold After%</th><th>Redist qty</th></tr>
<tr class="ml-0"><td><b>TrueDead</b></td><td>0 prodejov, stock ≥270d</td><td>18 385</td><td>50.0%</td><td class="warn">36.9%</td><td>22 260</td></tr>
<tr><td><b>PartialDead</b></td><td>0 prodejov, stock 90-270d</td><td>3 599</td><td>9.8%</td><td class="warn">56.7%</td><td>4 664</td></tr>
<tr class="ml-2"><td><b>SlowFull</b></td><td>Velocity &lt;0.5, stock ≥270d</td><td>10 863</td><td>29.5%</td><td class="warn">66.4%</td><td>14 586</td></tr>
<tr class="ml-2"><td><b>SlowPartial</b></td><td>Velocity &lt;0.5, stock 90-270d</td><td>2 038</td><td>5.5%</td><td class="good">77.2%</td><td>3 130</td></tr>
<tr class="ml-3"><td><b>ActiveSeller</b></td><td>Velocity ≥0.5</td><td>1 778</td><td>4.8%</td><td class="good">95.2%</td><td>3 941</td></tr>
</table>

<img src="fig_02_sold_after.png" alt="Sold After by Segment">
<img src="fig_10_sa_vs_ro.png" alt="SoldAfter vs Reorder">

<h3>2.4 Segment × Store</h3>
<img src="fig_03_src_heatmaps.png" alt="Source heatmaps">
<table>
<tr><th>Segment</th><th>Store</th><th>SKU</th><th>OS Total%</th><th>RO Total%</th><th>Sold After%</th><th>Redist qty</th></tr>
{seg_store_rows}
</table>
<div class="insight-bad">
<b>Gradient StoreStrength:</b> Silnejsi obchod = vyssi oversell + reorder + sold_after (2-3× mezi Weak a Strong).
ActiveSeller+Strong: 96.7% sold_after ale 21.3% oversell — nejvyssi riziko.
</div>

<h3>2.5 Declining — kam se zaradil</h3>
<table>
<tr><th>Puv. Pattern</th><th>Novy Segment</th><th>SKU</th><th>OS Total%</th><th>Sold After%</th></tr>
<tr><td>Declining</td><td>SlowFull</td><td>324</td><td>28.2%</td><td>78.7%</td></tr>
<tr><td>Declining</td><td>ActiveSeller</td><td>35</td><td>49.2%</td><td>100.0%</td></tr>
</table>
<div class="insight">Declining produkty jsou aktivne se prodavajici SKU s klesajicim trendem — vysoka sold_after (79-100%)
ukazuje, ze redistribuce z nich je <b>velmi rizikova</b>.</div>

<h3>2.6 LastSaleGap</h3>
<table>
<tr><th>Gap</th><th>SKU</th><th>OS Total%</th><th>RO Total%</th><th>Sold After%</th></tr>
{lsg_rows}
</table>
<div class="insight-good"><b>Potvrzeny modifier (v7-v9):</b> LastSaleGap ≤90d → sold_after 85-90% → +1 ML.</div>

<h3>2.7 Source BrandFit</h3>
<table>
<tr><th>Segment</th><th>BW Sold After</th><th>BS Sold After</th><th>Delta</th><th>Modifier</th></tr>
{sbf_rows}
</table>
<div class="insight"><b>BrandStrong source:</b> +5-11pp sold_after. Modifier +1 ML pro TrueDead/SlowFull/SlowPartial. Ignorovat u ActiveSeller.</div>

</div>

<!-- 3. TARGET -->
<h2>3. TARGET — Sell-Through a segmentace</h2>
<div class="target-header">TARGET ANALYZA</div>
<div class="target-box">

<h3>3.1 SalesBucket × Store</h3>
<img src="fig_05_tgt_heatmaps.png" alt="Target heatmaps">
<table>
<tr><th>Bucket</th><th>Store</th><th>SKU</th><th>ST 4M%</th><th>ST Total%</th><th>Nothing-sold 4M%</th><th>All-sold Total%</th></tr>
{tgt_rows}
</table>
<div class="insight-good">
<b>SalesBucket = nejsilnejsi prediktor:</b> ST roste z 35-55% (bucket 0) na 92-94% (bucket 11+).<br>
<b>Growth pockets:</b> Bucket 6+ na Strong/Mid (ST >80%, all-sold >75%).<br>
<b>Reduction pockets:</b> Bucket 0-2 na Weak/Mid (nothing-sold >60%).
</div>

<h3>3.2 Target BrandFit — 9-matrix</h3>
<table>
<tr><th>Store</th><th>BrandFit</th><th>SKU</th><th>ST Total%</th><th>Nothing-sold%</th></tr>
{bf_rows}
</table>
<div class="insight">
<b>BrandStoreFit dopad ~12pp ST.</b> Rozsah: 56.1% (Weak+BW) az 75.8% (Strong+BS) = 19.7pp.
Efekt je aditivni: Store ~10pp + Brand ~10-12pp.
</div>

<h3>3.3 BrandFit Graduation</h3>
<img src="fig_07_brandfit_grad.png" alt="BrandFit Graduation">
<table>
<tr><th>SalesBucket</th><th>ST Delta (BS-BW)</th><th>BW modifier</th><th>BS modifier</th></tr>
{bfd_rows}
</table>
<div class="insight-new">
<b>Graduovany BrandFit (v8-v9):</b> Pri 0-2 prodejich delta az +34pp → BW=-1, BS=+1.
Pri 3-5: BW=-1 jeste. Pri 6+: ignorovat (prodeje dominuji).
</div>
</div>

<!-- 4. STORE STRENGTH -->
<h2>4. Sila obchodu</h2>
<div class="section">
<img src="fig_04_store_deciles.png" alt="Store deciles">
<table>
<tr><th>Metrika</th><th>D1 (Weak)</th><th>D10 (Strong)</th><th>Gradient</th></tr>
<tr><td>Source Oversell 4M</td><td>2.1%</td><td>4.6%</td><td>2.2× (silnejsi = vice OS)</td></tr>
<tr><td>Source Reorder Total</td><td>24.0%</td><td>38.6%</td><td>1.6×</td></tr>
<tr><td>Target All-Sold Total</td><td>48.3%</td><td>70.1%</td><td>1.5× (silnejsi = vice prodano)</td></tr>
<tr><td>Target Nothing-Sold</td><td>32.1%</td><td>13.7%</td><td>0.4× (mene neuspesnych)</td></tr>
</table>
<div class="insight"><b>Dualita:</b> Silne obchody jsou lepsi targety ale horsi source.</div>

<h3>4.1 Flow matrix</h3>
<img src="fig_06_pairs_flow.png" alt="Pairs + Flow">
<table>
<tr><th>Source\\Target</th><th>Weak</th><th>Mid</th><th>Strong</th></tr>
<tr><td><b>Weak</b></td><td>1 179 (2.8%)</td><td>4 099 (9.7%)</td><td>4 661 (11.0%)</td></tr>
<tr><td><b>Mid</b></td><td>2 437 (5.7%)</td><td>7 315 (17.3%)</td><td>8 330 (19.6%)</td></tr>
<tr><td><b>Strong</b></td><td>2 256 (5.3%)</td><td>5 639 (13.3%)</td><td>6 488 (15.3%)</td></tr>
</table>
</div>

<!-- 5. ML distribuce -->
<h2>5. Aktualni ML distribuce</h2>
<div class="section">
<img src="fig_09_ml_distribution.png" alt="ML distribution">
<div class="two-col">
<div>
<div class="source-header">SOURCE ML (aktualni)</div>
<div class="source-box">
<table><tr><th>ML</th><th>SKU</th><th>%</th></tr>
<tr class="ml-0"><td>0</td><td>1 709</td><td>4.6%</td></tr>
<tr class="ml-1"><td>1</td><td>31 965</td><td>86.9%</td></tr>
<tr class="ml-2"><td>2</td><td>2 680</td><td>7.3%</td></tr>
<tr class="ml-3"><td>3</td><td>416</td><td>1.1%</td></tr></table>
<p class="insight-bad"><b>87% source SKU ma ML=1</b> — system nediferencuje.</p>
</div></div>
<div>
<div class="target-header">TARGET ML (aktualni)</div>
<div class="target-box">
<table><tr><th>ML</th><th>SKU</th><th>%</th></tr>
<tr class="ml-1"><td>1</td><td>4 730</td><td>11.4%</td></tr>
<tr class="ml-2"><td>2</td><td>31 977</td><td>76.8%</td></tr>
<tr class="ml-3"><td>3</td><td>4 924</td><td>11.8%</td></tr></table>
<p class="insight-bad"><b>77% target SKU ma ML=2</b> — system nediferencuje.</p>
</div></div>
</div>
</div>

<!-- 6. Evoluce modifikatoru -->
<h2>6. Evoluce modifikatoru</h2>
<div class="section">
<div class="two-col">
<div>
<div class="source-header">SOURCE modifikatory</div>
<div class="source-box">
<table class="evo-table">
<tr><th>Modifier</th><th>v2-v3</th><th>v4-v5</th><th>v6-v7</th><th>v8-v9</th></tr>
<tr><td>Seasonal/Xmas</td><td>+1</td><td>+1</td><td>+1</td><td class="changed">—*</td></tr>
<tr><td>BrandStrong src</td><td>+1</td><td>—</td><td>—</td><td class="changed">+1**</td></tr>
<tr><td>LastSaleGap ≤90d</td><td>+1</td><td>+1</td><td>+1</td><td>+1</td></tr>
<tr><td>SoldAfter ≥80%</td><td>—</td><td>—</td><td>+1</td><td class="changed">—***</td></tr>
<tr><td>Delisting</td><td>ML=0</td><td>ML=0</td><td>ML=0</td><td>ML=0</td></tr>
</table>
<p><small>* CalendarWeight nahrazuje seasonal flag<br>
** +1 pro TrueDead/SlowFull/SlowPartial + BrandStrong<br>
*** Absorbovano do segmentace</small></p>
</div></div>
<div>
<div class="target-header">TARGET modifikatory</div>
<div class="target-box">
<table class="evo-table">
<tr><th>Modifier</th><th>v2-v5</th><th>v6-v7</th><th>v8-v9</th></tr>
<tr><td>BrandWeak -1</td><td>-1 (plochy)</td><td>-1</td><td>-1 (graduovany)</td></tr>
<tr><td>BrandStrong +1</td><td>—</td><td>—</td><td>+1 (0-2 sales)</td></tr>
<tr><td>AllSold/ST1 +1</td><td>+1</td><td>+1</td><td>+1</td></tr>
<tr><td>Growth pocket +1</td><td>—</td><td>+1</td><td>+1</td></tr>
<tr><td>NothingSold -1</td><td>-1</td><td>—</td><td>-1</td></tr>
<tr><td>Delisting</td><td>ML=0</td><td>ML=0</td><td>ML=0</td></tr>
</table>
</div></div>
</div>

<h3>6.1 Nepotvrzene (zamitnute) modifikatory</h3>
<table>
<tr><th>Modifier</th><th>Proc zamitnut</th></tr>
<tr><td>PhantomStock</td><td>Se spravnym oversell vzorcem ~1-10 SKU. Statisticky nevyznamne.</td></tr>
<tr><td>ProductConcentration &lt;10%</td><td>Zadny gradient v OS/RO.</td></tr>
<tr><td>RedistLoop 4+</td><td>Pouze 7 SKU. Irelevantni.</td></tr>
<tr><td>Xmas per-SKU flag</td><td>Nahrazeno CalendarWeight 0.7.</td></tr>
<tr><td>Volatility CV</td><td>Nestabilni prediktor — obratny efekt v4.</td></tr>
</table>
</div>

<p style="text-align:center;color:#7f8c8d;margin-top:40px;">v10 Meta-analysis Findings | {NOW_STR} | CalculationId=233 | Douglas DE</p>
</body></html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  -> consolidated_findings.html")


# ############################################################
# HTML 2: DECISION TREE
# ############################################################
print("\n--- Building Decision Tree HTML ---")

# Source evolution rows
src_evo_rows = ""
seg_order_evo = ['TrueDead','PartialDead','SlowPartial','SlowFull','ActiveSeller']
for seg in seg_order_evo:
    for sto in STORES:
        vals = SRC_ML_EVO[(seg,sto)]
        final = vals[2]
        changed = vals[0] != vals[2] or vals[1] != vals[2]
        cls = ' class="changed"' if changed else ''
        src_evo_rows += f'<tr><td>{seg} / {sto}</td><td>{vals[0]}</td><td>{vals[1]}</td><td{cls}><b>{vals[2]}</b></td></tr>\n'

# Target evolution rows
tgt_evo_rows = ""
for bkt in ['0','1-2','3-5','6-10','11+']:
    for sto in STORES:
        vals = TGT_ML_EVO[(bkt,sto)]
        changed = vals[0] != vals[2] or vals[1] != vals[2]
        cls = ' class="changed"' if changed else ''
        tgt_evo_rows += f'<tr><td>{bkt} / {sto}</td><td>{vals[0]}</td><td>{vals[1]}</td><td{cls}><b>{vals[2]}</b></td></tr>\n'

html2 = f"""<!DOCTYPE html>
<html lang="cs"><head><meta charset="UTF-8"><title>v10 Decision Tree — Meta-analyza</title>
<style>{CSS_HTML}</style></head><body>
{nav(1)}

<h1>v10 — Decision Tree <span class="v10-badge">META</span></h1>
<p><b>CalculationId:</b> 233 | <b>Generovano:</b> {NOW_STR}</p>
<p>Finalni decision tree konsolidovany z v2-v9. Stabilizovany od v8, potvrzeny v9.</p>

<img src="fig_08_decision_tree.png" alt="Decision Tree Lookup">

<!-- SOURCE -->
<h2>1. SOURCE Decision Tree</h2>
<div class="source-header">SOURCE — Lookup: Segment × Store → ML 0-4</div>
<div class="source-box">

<h3>1.1 Evoluce Source Lookup (velocity system v6+)</h3>
<table class="evo-table">
<tr><th>Segment / Store</th><th>v6</th><th>v7</th><th>v8-v9 (FINAL)</th></tr>
{src_evo_rows}
</table>
<div class="insight">
<b>Zmeny v8:</b> SlowFull+Weak 1→2, SlowFull+Strong 2→3. Duvod: sold_after 56-75%, CalendarWeight odhalil
ze cast "ActiveSeller" byly SlowFull. v9 potvrdil nezavisle.
</div>

<h3>1.2 Finalni Source Lookup</h3>
<table>
<tr><th>Segment</th><th>Weak</th><th>Mid</th><th>Strong</th><th>Smer</th></tr>
<tr class="ml-1"><td><b>TrueDead</b></td><td>1</td><td>1</td><td>1</td><td>DOWN — bezpecne odvazet</td></tr>
<tr class="ml-1"><td><b>PartialDead</b></td><td>1</td><td>1</td><td class="ml-2">2</td><td>OK — opatrnost u Strong</td></tr>
<tr class="ml-2"><td><b>SlowPartial</b></td><td>2</td><td>2</td><td class="ml-3">3</td><td>OK — rozjizdi se</td></tr>
<tr class="ml-2"><td><b>SlowFull</b></td><td>2</td><td>2</td><td class="ml-3">3</td><td>OK/UP — vyssi ochrana od v8</td></tr>
<tr class="ml-3"><td><b>ActiveSeller</b></td><td>3</td><td class="ml-4">4</td><td class="ml-4">4</td><td>UP — chranit!</td></tr>
</table>

<h3>1.3 Source modifikatory</h3>
<table>
<tr><th>Modifier</th><th>Podminka</th><th>Uprava</th><th>Potvrzeno</th></tr>
<tr><td><b>LastSaleGap</b></td><td>≤90 dni</td><td class="arrow-up">+1 ML</td><td>v7-v9 (SA 85-90%)</td></tr>
<tr><td><b>BrandFit source</b></td><td>TrueDead/SlowFull/SlowPartial + BrandStrong</td><td class="arrow-up">+1 ML</td><td>v8-v9 (delta 5-11pp)</td></tr>
<tr><td><b>BrandFit source</b></td><td>ActiveSeller</td><td>ignorovat</td><td>SA >92%</td></tr>
<tr><td><b>Delisting</b></td><td>D/L</td><td><b>ML = 0</b></td><td>v2-v9</td></tr>
</table>

<h3>1.4 Clamp</h3>
<pre>
Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)
IF IsOrderable (A-O=9, Z-O=11): Final_ML = MAX(Final_ML, 1)
IF IsDelisted (D=3, L=4):       Final_ML = 0
</pre>
</div>

<!-- TARGET -->
<h2>2. TARGET Decision Tree</h2>
<div class="target-header">TARGET — Lookup: SalesBucket × Store → ML 0-4</div>
<div class="target-box">

<h3>2.1 Evoluce Target Lookup (v6+)</h3>
<table class="evo-table">
<tr><th>Bucket / Store</th><th>v6</th><th>v7</th><th>v8-v9 (FINAL)</th></tr>
{tgt_evo_rows}
</table>
<div class="insight-new">
<b>Bidirectional pivot (v7):</b> Snizeni slabych targetu (0/Strong 2→1, 1-2/Mid 2→1, 3-5/Weak 2→1).
Zvyseni silnych (3-5/Strong 2→3, 6-10/Mid+Strong 2→3, 11+/Strong 3→4).
</div>

<h3>2.2 Finalni Target Lookup</h3>
<table>
<tr><th>Bucket</th><th>Weak</th><th>Mid</th><th>Strong</th><th>Smer</th></tr>
<tr class="ml-1"><td><b>0</b></td><td>1</td><td>1</td><td>1</td><td class="arrow-down">REDUCE (NS 61-73%)</td></tr>
<tr class="ml-1"><td><b>1-2</b></td><td>1</td><td>1</td><td class="ml-2">2</td><td class="arrow-down">REDUCE (NS 58-65%)</td></tr>
<tr><td><b>3-5</b></td><td class="ml-1">1</td><td class="ml-2">2</td><td class="ml-3">3</td><td>OK — zlom (ST 42-46%)</td></tr>
<tr class="ml-2"><td><b>6-10</b></td><td>2</td><td class="ml-3">3</td><td class="ml-3">3</td><td class="arrow-up">GROWTH (ST 59-63%)</td></tr>
<tr><td><b>11+</b></td><td class="ml-2">2</td><td class="ml-3">3</td><td class="ml-4">4</td><td class="arrow-up">GROWTH (ST 73-77%)</td></tr>
</table>

<h3>2.3 Target modifikatory</h3>
<table>
<tr><th>Modifier</th><th>Podminka</th><th>Uprava</th><th>Potvrzeno</th></tr>
<tr><td><b>AllSold / ST1 high</b></td><td>AllSold4M=1 OR ST1_4M ≥85%</td><td class="arrow-up">+1</td><td>v4-v9</td></tr>
<tr><td><b>Growth pocket</b></td><td>Strong, Sales 3-10, ST ≥45%</td><td class="arrow-up">+1</td><td>v7-v9</td></tr>
<tr><td><b>NothingSold / low ST</b></td><td>NothingSold4M=1 OR ST4M &lt;20%</td><td class="arrow-down">-1</td><td>v5, v8-v9</td></tr>
<tr><td><b>BrandFit (0-2 sales) BW</b></td><td>BrandWeak</td><td class="arrow-down">-1</td><td>v8-v9</td></tr>
<tr><td><b>BrandFit (0-2 sales) BS</b></td><td>BrandStrong</td><td class="arrow-up">+1</td><td>v8-v9</td></tr>
<tr><td><b>BrandFit (3-5) BW</b></td><td>BrandWeak</td><td class="arrow-down">-1</td><td>v8-v9</td></tr>
<tr><td><b>BrandFit (6+)</b></td><td>—</td><td>ignorovat</td><td>delta &lt;4pp</td></tr>
<tr><td><b>Delisting</b></td><td>D/L</td><td><b>ML = 0</b></td><td>v2-v9</td></tr>
</table>

<h3>2.4 Clamp</h3>
<pre>
Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)
IF IsOrderable (A-O=9, Z-O=11): Final_ML = MAX(Final_ML, 1)
IF IsDelisted (D=3, L=4):       Final_ML = 0
</pre>
</div>

<!-- 3. PSEUDOKOD -->
<h2>3. Kompletni pseudokod</h2>
<div class="section">
<h3>3.1 Source</h3>
<pre>
-- Velocity classification (s CalendarWeight)
CalendarWeight = 0.7 IF half-year contains Nov+Dec ELSE 1.0
Velocity_12M = (Adjusted_Sales_12M / DaysInStock_12M) × 30

IF Sales_12M = 0 AND DaysInStock >= 270:  TrueDead
IF Sales_12M = 0 AND DaysInStock 90-270:  PartialDead
IF Sales_12M = 0 AND DaysInStock < 90:    BriefNoSale
IF Velocity >= 0.5:                        ActiveSeller
IF Velocity < 0.5 AND DaysInStock >= 270:  SlowFull
IF Velocity < 0.5 AND DaysInStock < 270:   SlowPartial

base_ml = SOURCE_LOOKUP[segment][store]
IF LastSaleGapDays <= 90:                              base_ml += 1
IF segment IN (TrueDead,SlowFull,SlowPartial) AND BS:  base_ml += 1
final_ml = CLAMP(base_ml, 0, 4)
IF IsOrderable: final_ml = MAX(final_ml, 1)
IF IsDelisted:  final_ml = 0
</pre>

<h3>3.2 Target</h3>
<pre>
bucket = CASE WHEN sales=0 THEN '0' WHEN <=2 '1-2' WHEN <=5 '3-5' WHEN <=10 '6-10' ELSE '11+' END

base_ml = TARGET_LOOKUP[bucket][store]
IF AllSold4M=1 OR ST1_4M >= 85%:               base_ml += 1
IF Strong AND sales 3-10 AND ST_4M >= 45%:      base_ml += 1
IF NothingSold4M=1 OR ST_4M < 20%:              base_ml -= 1
IF sales <= 2 AND BrandWeak:                     base_ml -= 1
IF sales <= 2 AND BrandStrong:                   base_ml += 1
IF sales 3-5 AND BrandWeak:                      base_ml -= 1
final_ml = CLAMP(base_ml, 0, 4)
IF IsOrderable: final_ml = MAX(final_ml, 1)
IF IsDelisted:  final_ml = 0
</pre>
</div>

<!-- 4. SMERY -->
<h2>4. Souhrn — smery zasahu</h2>
<div class="section">
<div class="two-col">
<div>
<div class="source-header">SOURCE</div>
<div class="source-box"><table>
<tr><th>Segment</th><th>Smer</th><th>Prinos</th></tr>
<tr class="dir-down"><td>TrueDead (vsechny)</td><td>DOWN (ML=1)</td><td>SA 33-41%</td></tr>
<tr class="dir-ok"><td>PartialDead (W/M)</td><td>OK (ML=1)</td><td>Opatrnost</td></tr>
<tr class="dir-up"><td>PartialDead (S)</td><td>UP (ML=2)</td><td>SA 62%</td></tr>
<tr class="dir-up"><td>SlowFull (W/M)</td><td>UP (ML=2)</td><td>SA 56-64%</td></tr>
<tr class="dir-up"><td>SlowFull (S)</td><td>UP (ML=3)</td><td>SA 75%</td></tr>
<tr class="dir-up"><td>SlowPartial</td><td>UP (ML=2-3)</td><td>SA 72-84%</td></tr>
<tr class="dir-up"><td>ActiveSeller</td><td>UP (ML=3-4)</td><td>SA 91-97%</td></tr>
</table></div></div>
<div>
<div class="target-header">TARGET</div>
<div class="target-box"><table>
<tr><th>Bucket × Store</th><th>Smer</th><th>Prinos</th></tr>
<tr class="dir-down"><td>0 / vsechny</td><td>REDUCE (ML=1)</td><td>NS 61-73%</td></tr>
<tr class="dir-down"><td>1-2 / W,M</td><td>REDUCE (ML=1)</td><td>NS 62-65%</td></tr>
<tr class="dir-ok"><td>1-2 / S</td><td>OK (ML=2)</td><td>ST 56%</td></tr>
<tr class="dir-down"><td>3-5 / W</td><td>REDUCE (ML=1)</td><td>NS 45%</td></tr>
<tr class="dir-ok"><td>3-5 / M</td><td>OK (ML=2)</td><td>ST 66%</td></tr>
<tr class="dir-up"><td>3-5 / S</td><td>GROWTH (ML=3)</td><td>ST 72%</td></tr>
<tr class="dir-up"><td>6-10 / M,S</td><td>GROWTH (ML=3)</td><td>ST 84-86%</td></tr>
<tr class="dir-up"><td>11+ / S</td><td>GROWTH (ML=4)</td><td>ST 94%</td></tr>
</table></div></div>
</div>
</div>

<p style="text-align:center;color:#7f8c8d;margin-top:40px;">v10 Decision Tree | {NOW_STR} | CalculationId=233</p>
</body></html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  -> consolidated_decision_tree.html")


# ############################################################
# HTML 3: DEFINITIONS
# ############################################################
print("\n--- Building Definitions HTML ---")

html3 = f"""<!DOCTYPE html>
<html lang="cs"><head><meta charset="UTF-8"><title>v10 Definitions</title>
<style>{CSS_HTML}</style></head><body>
{nav(2)}

<h1>v10 — Definitions <span class="v10-badge">META</span></h1>

<div class="section">
<h2>Metriky</h2>

<h3>OVERSELL (source)</h3>
<pre>
RemainingAfterRedist = SourceAvailableSupply - TotalQtyRedistributed
Oversell_Qty = LEAST(GREATEST(Sales_Post - RemainingAfterRedist, 0), TotalQtyRedistributed)
</pre>

<h3>REORDER (source)</h3>
<pre>Reorder_Qty = LEAST(SUM(Inbound.Quantity), TotalQtyRedistributed)</pre>

<h3>SELL-THROUGH (target)</h3>
<pre>
Base = TargetAvailableSupply + TotalQtyReceived
ST = LEAST(Sold, Base) / Base × 100
</pre>

<h3>SELL-THROUGH-1pc (target)</h3>
<pre>
Ak Sold >= Base:  ST1 = 100%
Ak Sold < Base AND Base > 1:  ST1 = LEAST(Sold, Base-1) / (Base-1) × 100
Ak Base <= 1:  ST1 = NULL
</pre>

<h3>NOTHING-SOLD / ALL-SOLD</h3>
<pre>
NothingSold = 1 ak Sales_Post = 0
AllSold = 1 ak Sales_Post >= Base
</pre>
</div>

<div class="section">
<h2>Klasifikace</h2>

<h3>Velocity segmenty (source)</h3>
<pre>
CalendarWeight = 0.7 IF half-year contains Nov+Dec ELSE 1.0
Adjusted_Sales(period) = Raw_Sales(period) × CalendarWeight(period)
Velocity_12M = Adjusted_Sales_12M / DaysInStock_12M × 30

TrueDead:    Sales_12M = 0, DaysInStock >= 270
PartialDead: Sales_12M = 0, DaysInStock 90-270
BriefNoSale: Sales_12M = 0, DaysInStock < 90
ActiveSeller: Velocity >= 0.5/mesic
SlowFull:    Velocity < 0.5, DaysInStock >= 270
SlowPartial: Velocity < 0.5, DaysInStock 90-270
</pre>

<h3>StoreStrength</h3>
<pre>
Revenue_6M = SUM(SaleTransaction.Quantity × SalePrice) za 6M pred redistribuci
StoreDecile = NTILE(10) OVER (ORDER BY Revenue_6M)
Weak = Decile 1-3, Mid = 4-7, Strong = 8-10
</pre>

<h3>BrandFit</h3>
<pre>
BrandRevenue_6M = SUM(Quantity × SalePrice) za 6M, GROUP BY WarehouseId, BrandId
BrandQuintile = NTILE(5) OVER (PARTITION BY BrandId ORDER BY BrandRevenue_6M)
BrandWeak = Q1-2, BrandMid = Q3, BrandStrong = Q4-5
</pre>

<h3>SalesBucket (target)</h3>
<pre>
0: sales_12m = 0 | 1-2: 1-2 | 3-5: 3-5 | 6-10: 6-10 | 11+: >= 11
</pre>

<h3>LastSaleGap</h3>
<pre>LastSaleGapDays = DATEDIFF(DAY, MAX(SaleDate pred ApplicationDate), ApplicationDate)</pre>

<h3>SoldAfter</h3>
<pre>SoldAfter = 1 ak source SKU malo aspon 1 predaj po ApplicationDate</pre>

<h3>DaysInStock</h3>
<pre>DaysInStock = pocet dni s AvailableSupply > 0 v danom obdobi (z SkuAvailableSupply)</pre>
</div>

<div class="section">
<h2>Business Rules</h2>
<pre>
A-O (SkuClass=9):  MIN ML = 1 (nikdy ML=0)
Z-O (SkuClass=11): MIN ML = 1 (nikdy ML=0)
D (SkuClass=3):    ML = 0 (override)
L (SkuClass=4):    ML = 0 (override)
ML range: 0-4
</pre>
</div>

<div class="section">
<h2>Parametry</h2>
<table>
<tr><th>Parametr</th><th>Hodnota</th></tr>
<tr><td>Server</td><td>DEV</td></tr>
<tr><td>Databaze</td><td>ydistri-sql-db-dev-tenant-douglasde</td></tr>
<tr><td>CalculationId</td><td>233</td></tr>
<tr><td>EntityListId</td><td>3</td></tr>
<tr><td>Ecomm (vyloucit)</td><td>WarehouseId = 300</td></tr>
<tr><td>ApplicationDate</td><td>2025-07-13</td></tr>
<tr><td>CalendarWeight</td><td>0.7</td></tr>
</table>
</div>

<p style="text-align:center;color:#7f8c8d;margin-top:40px;">v10 Definitions | {NOW_STR}</p>
</body></html>"""

with open(os.path.join(SCRIPT_DIR, 'definitions.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  -> definitions.html")

print("\n" + "=" * 60)
print(f"v10 ALL DONE: {SCRIPT_DIR}")
print("=" * 60)
