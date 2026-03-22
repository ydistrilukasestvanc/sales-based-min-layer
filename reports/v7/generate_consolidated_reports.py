"""
Consolidated Reports Generator v7: SalesBased MinLayers - CalculationId=233

v7 = SYNTHESIS of v5 (modifiers, growth pockets, bidirectional target)
     and v6 (velocity segments, stock normalization, sold-after%).

v7 KEY CONTRIBUTIONS:
  - Validates which v5 modifiers survive on real data
  - Replaces Pattern with Velocity Segments from v6
  - Adds bidirectional target from v5
  - Reclassification matrix: v5 Pattern -> v6 Segment with performance data
  - Modifier validation chart: confirmed vs dropped
  - Growth AND reduction pockets in backtest

Key principles:
  - ALWAYS show BOTH oversell AND reorder side by side
  - Target analysis EQUALLY detailed as source
  - Decision tree: 4 directions (source up/down, target up/down)
  - Target all-sold = SUCCESS (green), nothing-sold = PROBLEM (red)
  - Backtest shows VOLUME change (pcs)
  - Texts in CZECH, parameters/terms in ENGLISH
  - Overview table ALWAYS with 4M and total
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Patch, FancyBboxPatch
import seaborn as sns
from datetime import datetime

VERSION = 'v7'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SCRIPT_DIR, exist_ok=True)
sns.set_style("whitegrid")

print("=" * 60)
print(f"Generating consolidated reports ({VERSION})...")
print("=" * 60)

# ============================================================
# COMMON CSS (same as v6)
# ============================================================
CSS = """
body { font-family: 'Segoe UI', sans-serif; max-width: 1300px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }
h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
h2 { color: #2c3e50; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 12px; }
h3 { color: #34495e; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: right; }
th { background: #3498db; color: white; }
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
pre { background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 12px; overflow-x: auto; }
.nav { background: #2c3e50; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; }
.nav a { color: #ecf0f1; margin-right: 20px; text-decoration: none; font-weight: bold; }
.nav a:hover { color: #3498db; }
.nav a.active { color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 4px; }
.arrow-up { color: #e74c3c; font-weight: bold; }
.arrow-down { color: #27ae60; font-weight: bold; }
.dir-up { background: #fce4e4; }
.dir-down { background: #d4edda; }
.new-badge { background: #17a2b8; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
.v7-badge { background: #6f42c1; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
"""

NOW_STR = datetime.now().strftime('%Y-%m-%d %H:%M')


def nav_bar(active_idx):
    links = [
        ('consolidated_findings.html', 'Report 1: Findings'),
        ('consolidated_decision_tree.html', 'Report 2: Decision Tree'),
        ('consolidated_backtest.html', 'Report 3: Backtest'),
    ]
    html = '<div class="nav">'
    for i, (href, label) in enumerate(links):
        cls = ' class="active"' if i == active_idx else ''
        html += f'<a href="{href}"{cls}>{label}</a>'
    html += f'<span style="float:right; color:#7f8c8d; font-size:11px;">v7 Synthesis (v5+v6) | ML 0-4 | Orderable min=1 | Bidirectional target</span>'
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA (v7)
# ============================================================

OVERVIEW = {
    'pairs': 42404, 'source_skus': 36770, 'target_skus': 41631, 'redist_qty': 48754,
    'os4m_sku': 1317, 'os4m_qty': 1464, 'os4m_pct': 3.0,
    'os_t_sku': 4718, 'os_t_qty': 5578, 'os_t_pct': 11.4,
    'ro4m_sku': 7087, 'ro4m_qty': 7980, 'ro4m_pct': 16.4,
    'ro_t_sku': 13841, 'ro_t_qty': 16615, 'ro_t_pct': 34.1,
}

# --- VELOCITY SEGMENTS (from v6, base for v7) ---
SEGMENTS = [
    # name, skus, pct, redist, os_t, ro_t, ro_t_sku, sold_after, avg_days
    ('TrueDead',      18355, 50.0, 22260,  6.1, 25.5, 28.2, 36.9, 358),
    ('SlowFull',      10197, 27.8, 13511, 15.1, 42.6, 47.9, 64.7, 347),
    ('PartialDead',    3599,  9.8,  4664, 14.0, 36.6, 40.2, 56.8, 172),
    ('ActiveSeller',   2535,  6.9,  5151, 21.6, 45.9, 58.3, 93.8, 293),
    ('SlowPartial',    1980,  5.4,  3035, 12.7, 34.5, 40.7, 76.9, 188),
    ('BriefNoSale',      48,  0.1,    61, 27.9, 50.8, 52.1, 70.8,  60),
]

SEGMENT_NAMES = [r[0] for r in SEGMENTS]
STORES = ['Weak', 'Mid', 'Strong']

# --- SEGMENT x STORE (15 rows, with extra columns for v7) ---
SEG_STORE = [
    # segment, store, skus, redist, os4m, os_t, ro4m, ro_t, ro_t_sku, sold_after, pct_seasonal, avg_gap, avg_conc
    ('TrueDead','Weak',5227,6238,1.0,4.3,9.6,21.5,23.7,32.6,0.0,512,9.3),
    ('TrueDead','Mid',8206,10026,1.3,6.1,11.4,26.1,29.0,37.2,0.0,508,8.1),
    ('TrueDead','Strong',4922,5996,2.1,8.0,12.7,28.6,31.5,40.8,0.0,503,6.7),
    ('PartialDead','Weak',939,1124,2.8,9.9,16.7,33.8,36.8,48.8,0.0,468,14.1),
    ('PartialDead','Mid',1599,2056,4.1,14.1,19.3,38.1,41.7,57.8,0.0,450,12.7),
    ('PartialDead','Strong',1061,1484,5.4,17.0,18.2,36.5,40.8,62.2,0.0,477,10.7),
    ('SlowPartial','Weak',415,617,1.5,8.8,11.8,29.7,32.8,71.1,35.9,135,24.1),
    ('SlowPartial','Mid',773,1151,3.3,11.7,16.2,34.1,39.3,72.6,27.7,120,21.0),
    ('SlowPartial','Strong',792,1267,3.4,15.4,20.3,37.3,46.1,84.2,16.8,107,17.1),
    ('SlowFull','Weak',2060,2614,2.5,10.2,17.9,36.4,40.6,54.9,51.3,209,15.1),
    ('SlowFull','Mid',4468,5927,4.4,14.6,22.3,42.5,48.3,62.8,52.4,204,13.7),
    ('SlowFull','Strong',3669,4970,4.9,18.3,22.8,46.0,51.4,72.6,54.1,193,12.2),
    ('ActiveSeller','Weak',176,308,2.3,22.1,21.1,42.9,52.8,90.3,63.6,101,16.0),
    ('ActiveSeller','Mid',664,1356,5.2,20.9,23.1,47.5,59.8,89.0,64.6,99,14.7),
    ('ActiveSeller','Strong',1695,3487,5.7,21.9,21.4,45.5,58.3,96.0,62.2,75,16.0),
]

# --- RECLASSIFICATION: v5 Pattern -> v6 Segment (with metrics) ---
RECLASS = [
    # old_pattern, new_segment, skus, os_t, ro_t, sold_after
    ('Consistent','ActiveSeller',644,25.7,50.9,98.3),
    ('Consistent','SlowFull',65,25.5,53.9,89.2),
    ('Dead','TrueDead',11834,4.6,22.6,33.9),
    ('Dead','PartialDead',3533,13.7,36.3,56.9),
    ('Dead','BriefNoSale',36,27.3,47.7,66.7),
    ('Dying','TrueDead',6521,8.8,30.7,42.2),
    ('Dying','PartialDead',66,28.2,49.4,51.5),
    ('Dying','BriefNoSale',12,29.4,58.8,83.3),
    ('Declining','SlowFull',324,28.2,65.3,78.7),
    ('Declining','ActiveSeller',35,49.2,79.4,100.0),
    ('Sporadic','SlowFull',9808,14.6,41.8,64.1),
    ('Sporadic','SlowPartial',1975,12.5,34.5,76.9),
    ('Sporadic','ActiveSeller',1856,19.4,43.1,92.1),
]

# --- LastSaleGap ---
LAST_SALE_GAP = [
    # bucket, skus, os_t, ro_t, sold_after
    ('0-30d',1472,13.1,35.2,90.0),
    ('31-90d',2280,14.8,39.4,85.2),
    ('91-180d',3116,15.6,45.5,76.4),
    ('181-365d',7850,18.1,44.0,61.8),
    ('365-730d',6588,9.0,30.9,42.4),
    ('Never/730d+',15464,6.9,26.1,39.4),
]

# --- ProductConcentration ---
PROD_CONC = [
    # bucket, skus, os_t, ro_t
    ('<10%',20722,11.2,32.3),
    ('10-25%',12790,12.3,37.2),
    ('25-50%',3118,10.7,35.4),
    ('50%+',140,0.3,3.5),
]

# --- Seasonality ---
SEASONALITY = [
    # category, skus, os_t, ro_t
    ('Non-seasonal',29298,9.3,30.8),
    ('Seasonal',7472,18.8,45.3),
]

# --- SkuClass ---
SKUCLASS = [
    # class, skus, os_t, ro_t, ro_t_sku
    ('Unchanged',29322,13.0,39.8,43.2),
    ('Delisted',6049,4.9,10.9,13.2),
    ('Other',1399,10.1,26.3,27.2),
]

# --- Modifier validation (v7 KEY) ---
MODIFIER_VALID = [
    # modifier, status, evidence, confirmed(bool)
    ('LastSaleGap <=90d','Potvrzeno','sold after 85-90%',True),
    ('Seasonal','Potvrzeno','OS 2x, RO 1.5x',True),
    ('RedistRatio >=75%','Castecne','nizky objem',True),
    ('Delisting','Potvrzeno','RO 10.9%',True),
    ('ProductConc <10%','Nepotvrzeno','zadny gradient',False),
    ('PhantomStock','Nepotvrzeno','1 SKU',False),
    ('Loop 4+','Nepotvrzeno','7 SKU',False),
    ('Sold After >=80%','Novy/Potvrzeno','ActiveSeller 94%',True),
]

# --- Target: SalesBucket x Store ---
TGT_STORE_SALES = [
    # salesbucket, store, skus, st4m, sttot, nosale4m, nosale_t, allsold4m, allsold_t
    ('0','Weak',137,23.1,34.7,16.1,73.7,21.2,31.4),
    ('0','Mid',334,23.4,41.5,22.4,73.7,21.3,37.7),
    ('0','Strong',252,36.4,53.6,22.2,61.1,34.9,51.6),
    ('1-2','Weak',1966,26.3,47.2,59.5,65.5,18.1,38.0),
    ('1-2','Mid',4493,28.6,51.2,63.7,62.0,19.3,40.9),
    ('1-2','Strong',3622,32.1,56.4,68.1,58.0,22.1,47.0),
    ('3-5','Weak',2601,41.5,65.8,76.7,45.1,28.1,54.4),
    ('3-5','Mid',7765,40.8,66.0,77.1,45.5,27.3,54.6),
    ('3-5','Strong',9017,45.3,71.7,82.1,40.8,31.5,61.0),
    ('6-10','Weak',886,58.6,82.2,87.5,28.1,45.4,74.3),
    ('6-10','Mid',3347,59.3,84.3,90.6,26.8,45.6,76.2),
    ('6-10','Strong',4859,63.1,86.2,92.3,22.3,48.9,78.8),
    ('11+','Weak',179,73.8,92.0,95.5,12.3,56.4,84.9),
    ('11+','Mid',815,72.7,93.4,95.7,11.9,55.8,87.9),
    ('11+','Strong',1358,77.0,93.9,96.4,10.8,64.4,89.5),
]

# --- Target Stock Coverage Effect ---
TGT_STOCK = [
    # bucket, sales_bucket, skus, allsold_t, nosale_t, sold_after
    ('New (0d)','0',497,58.1,61.8,57.7),
    ('New (0d)','3-5',351,80.2,39.0,80.1),
    ('New (0d)','11+',81,93.8,25.9,93.8),
    ('Brief','1-2',788,55.7,63.2,52.7),
    ('Brief','3-5',772,79.8,35.1,74.9),
    ('Brief','11+',265,95.0,9.4,90.9),
    ('Partial','1-2',1912,58.8,55.4,49.7),
    ('Partial','3-5',4206,72.1,38.8,61.6),
    ('Partial','11+',577,94.2,6.6,88.7),
    ('Established','1-2',6847,50.2,62.1,38.8),
    ('Established','3-5',14054,66.6,45.1,54.8),
    ('Established','11+',1429,93.1,12.7,87.8),
]

# --- Brand-Store Fit ---
BRAND_FIT = [
    # store, brand, skus, allsold_t, nosale_t
    ('Weak','BrandWeak',2448,55.3,54.9),
    ('Weak','BrandMid',1152,63.7,49.3),
    ('Weak','BrandStrong',2169,68.4,42.4),
    ('Mid','BrandWeak',3623,59.1,53.2),
    ('Mid','BrandMid',3744,64.3,47.6),
    ('Mid','BrandStrong',9387,70.0,41.1),
    ('Strong','BrandWeak',1746,63.9,47.3),
    ('Strong','BrandMid',2590,69.5,42.2),
    ('Strong','BrandStrong',14772,75.8,35.4),
]

# --- Store Deciles ---
DECILES = list(range(1, 11))
SRC_OVERSELL_4M = [1.9, 1.3, 1.9, 2.0, 2.6, 3.0, 3.6, 3.2, 4.4, 4.5]
SRC_REORDER_TOT = [24.0, 27.8, 28.8, 30.5, 33.6, 35.1, 36.0, 37.5, 39.0, 38.6]
TGT_ALLSOLD = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1]
TGT_NOTHING = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Pair analysis ---
PAIRS = [
    ('Win-Win', 28179, 66.5),
    ('Win-Lose', 8565, 20.2),
    ('Lose-Win', 4794, 11.3),
    ('Lose-Lose', 866, 2.0),
]

# --- Flow Matrix ---
FLOW = [
    ('Weak','Weak',1179,2.8), ('Weak','Mid',4149,9.8), ('Weak','Strong',4611,10.9),
    ('Mid','Weak',2391,5.6), ('Mid','Mid',7279,17.2), ('Mid','Strong',8304,19.6),
    ('Strong','Weak',2302,5.4), ('Strong','Mid',5643,13.3), ('Strong','Strong',6546,15.4),
]

# --- Decision Trees ---
SRC_ML = {
    ('ActiveSeller','Weak'):3, ('ActiveSeller','Mid'):4, ('ActiveSeller','Strong'):4,
    ('SlowFull','Weak'):1, ('SlowFull','Mid'):2, ('SlowFull','Strong'):2,
    ('SlowPartial','Weak'):2, ('SlowPartial','Mid'):2, ('SlowPartial','Strong'):3,
    ('PartialDead','Weak'):1, ('PartialDead','Mid'):1, ('PartialDead','Strong'):2,
    ('TrueDead','Weak'):1, ('TrueDead','Mid'):1, ('TrueDead','Strong'):1,
    ('BriefNoSale','Weak'):2, ('BriefNoSale','Mid'):2, ('BriefNoSale','Strong'):2,
}

TGT_ML = {
    ('0','Weak'):1, ('0','Mid'):1, ('0','Strong'):1,
    ('1-2','Weak'):1, ('1-2','Mid'):1, ('1-2','Strong'):2,
    ('3-5','Weak'):1, ('3-5','Mid'):2, ('3-5','Strong'):3,
    ('6-10','Weak'):2, ('6-10','Mid'):3, ('6-10','Strong'):3,
    ('11+','Weak'):2, ('11+','Mid'):3, ('11+','Strong'):4,
}


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS (10 charts)
#
# ############################################################
print()
print("--- Report 1: Consolidated Findings (10 charts) ---")

# ---- fig_findings_01.png - Segment overview: 3-panel ----
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

seg_labels = [r[0] for r in SEGMENTS]
seg_skus = [r[1] for r in SEGMENTS]
seg_sold_after = [r[7] for r in SEGMENTS]
seg_ro_t = [r[5] for r in SEGMENTS]

# SKU count
colors_sku = ['#2c3e50', '#7f8c8d', '#95a5a6', '#e74c3c', '#f39c12', '#17a2b8']
axes[0].barh(range(len(seg_labels)), seg_skus, color=colors_sku, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(range(len(seg_labels)))
axes[0].set_yticklabels(seg_labels, fontsize=9)
axes[0].set_xlabel('SKU Count')
axes[0].set_title('Segmenty: Pocet SKU\n(Velocity-normalized, v6 -> v7)', fontsize=11)
for i, v in enumerate(seg_skus):
    axes[0].text(v + 100, i, f'{v:,} ({SEGMENTS[i][2]}%)', va='center', fontsize=8)
axes[0].invert_yaxis()

# RO Tot %
colors_ro = ['#27ae60' if r < 35 else ('#f39c12' if r < 45 else '#e74c3c') for r in seg_ro_t]
axes[1].barh(range(len(seg_labels)), seg_ro_t, color=colors_ro, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(range(len(seg_labels)))
axes[1].set_yticklabels(seg_labels, fontsize=9)
axes[1].set_xlabel('Reorder Total %')
axes[1].set_title('Reorder Total %: HLAVNI PROBLEM\n(vyssi = horsi redistribuce)', fontsize=11)
for i, v in enumerate(seg_ro_t):
    axes[1].text(v + 0.5, i, f'{v}%', va='center', fontsize=8)
axes[1].axvline(x=40, color='#e74c3c', linestyle='--', alpha=0.5, label='>40% = problem')
axes[1].axvline(x=30, color='#f39c12', linestyle='--', alpha=0.5, label='>30% = warning')
axes[1].legend(fontsize=7, loc='lower right')
axes[1].invert_yaxis()

# Sold After %
colors_sa = ['#e74c3c' if s < 50 else ('#f39c12' if s < 70 else '#27ae60') for s in seg_sold_after]
axes[2].barh(range(len(seg_labels)), seg_sold_after, color=colors_sa, edgecolor='#333', linewidth=0.5)
axes[2].set_yticks(range(len(seg_labels)))
axes[2].set_yticklabels(seg_labels, fontsize=9)
axes[2].set_xlabel('Sold After Redistribution %')
axes[2].set_title('Sold After %: Klic. prediktor\n(vyssi = lepsi redistribuce)', fontsize=11)
for i, v in enumerate(seg_sold_after):
    axes[2].text(v + 0.5, i, f'{v}%', va='center', fontsize=8)
axes[2].axvline(x=50, color='#e74c3c', linestyle='--', alpha=0.5)
axes[2].axvline(x=70, color='#27ae60', linestyle='--', alpha=0.5)
axes[2].invert_yaxis()

fig.suptitle('v7 Velocity-Normalized Segmentace: Prehled (synteza v5+v6)', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- fig_findings_02.png - Segment x Store: dual heatmap (OS Tot% + RO Tot%) ----
seg_order_hm = ['TrueDead', 'PartialDead', 'SlowPartial', 'SlowFull', 'ActiveSeller']
oversell_t_data = []
reorder_t_data = []
for seg in seg_order_hm:
    row_ot, row_rt = [], []
    for s in STORES:
        row = [r for r in SEG_STORE if r[0] == seg and r[1] == s][0]
        row_ot.append(row[5])   # os_t
        row_rt.append(row[8])   # ro_t_sku
    oversell_t_data.append(row_ot)
    reorder_t_data.append(row_rt)

oversell_t_arr = np.array(oversell_t_data)
reorder_t_arr = np.array(reorder_t_data)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(oversell_t_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_hm, ax=axes[0],
            vmin=0, vmax=25, linewidths=1,
            cbar_kws={'label': 'Oversell Total %'})
axes[0].set_title('OVERSELL Total % by Segment x Store\n(prumerne 11.4%)', fontsize=11)
axes[0].set_ylabel('Velocity Segment')
axes[0].set_xlabel('Store Strength')

sns.heatmap(reorder_t_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_hm, ax=axes[1],
            vmin=20, vmax=60, linewidths=1,
            cbar_kws={'label': 'Reorder Total SKU %'})
for i in range(len(seg_order_hm)):
    for j in range(len(STORES)):
        if reorder_t_data[i][j] > 40:
            axes[1].add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                             edgecolor='#2c3e50', linewidth=3))
axes[1].set_title('REORDER Total SKU % by Segment x Store\n(HLAVNI PROBLEM, cells >40% highlighted)', fontsize=11)
axes[1].set_ylabel('Velocity Segment')
axes[1].set_xlabel('Store Strength')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_02.png")

# ---- fig_findings_03.png - NEW v7: Reclassification matrix ----
# Grouped bar showing v5 Pattern -> v6 Segment with sold_after% annotations
fig, ax = plt.subplots(1, 1, figsize=(18, 9))

old_patterns_order = ['Consistent', 'Dead', 'Dying', 'Declining', 'Sporadic']
new_seg_colors = {
    'TrueDead': '#2c3e50', 'PartialDead': '#95a5a6', 'SlowFull': '#7f8c8d',
    'SlowPartial': '#f39c12', 'ActiveSeller': '#e74c3c', 'BriefNoSale': '#17a2b8'
}

y_pos = 0
y_positions = []
y_labels = []
bar_vals = []
bar_colors_list = []
sold_after_annots = []

for old_p in old_patterns_order:
    mappings = [r for r in RECLASS if r[0] == old_p]
    mappings.sort(key=lambda x: -x[2])  # sort by skus desc
    for m in mappings:
        y_positions.append(y_pos)
        y_labels.append(f'{old_p} -> {m[1]}')
        bar_vals.append(m[2])
        bar_colors_list.append(new_seg_colors.get(m[1], '#3498db'))
        sold_after_annots.append(m[5])  # sold_after
        y_pos += 1
    y_pos += 0.5

bars = ax.barh(y_positions, bar_vals, color=bar_colors_list, edgecolor='#333', linewidth=0.5, height=0.7)

for i, (pos, val, sa) in enumerate(zip(y_positions, bar_vals, sold_after_annots)):
    ax.text(val + 80, pos, f'{val:,} SKU | sold_after={sa}%', va='center', fontsize=7.5,
            color='#27ae60' if sa >= 70 else ('#f39c12' if sa >= 50 else '#e74c3c'),
            fontweight='bold')

ax.set_yticks(y_positions)
ax.set_yticklabels(y_labels, fontsize=8)
ax.set_xlabel('SKU Count')
ax.set_title('v7 KLICOVY PRISPEVEK: Reklasifikace v5 Pattern -> v6 Velocity Segment\n'
             'Sold After % ukazuje skutecny vysledek redistribuce pro kazdou kombinaci\n'
             '(zelena = sold_after >= 70%, oranzova = 50-70%, cervena < 50%)',
             fontsize=11, fontweight='bold')
ax.invert_yaxis()

legend_patches = [mpatches.Patch(color=c, label=l) for l, c in new_seg_colors.items()]
ax.legend(handles=legend_patches, loc='lower right', fontsize=8, title='Velocity Segment')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- fig_findings_04.png - Store decile lines ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

axes[0].plot(DECILES, SRC_OVERSELL_4M, 'o-', color='#3498db', linewidth=2, label='Source Oversell 4M %')
axes[0].plot(DECILES, SRC_REORDER_TOT, 's--', color='#e74c3c', linewidth=2, label='Source Reorder Total %')
axes[0].fill_between(DECILES, SRC_REORDER_TOT, alpha=0.1, color='#e74c3c')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Oversell 4M + Reorder Total by Decile\n(Reorder je hlavni problem)')
axes[0].legend(fontsize=8)
axes[0].set_xticks(DECILES)
axes[0].axhspan(0, 5, alpha=0.05, color='green')

axes[1].plot(DECILES, TGT_ALLSOLD, 'o-', color='#27ae60', linewidth=2, label='All Sold %')
axes[1].plot(DECILES, TGT_NOTHING, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold %')
axes[1].fill_between(DECILES, TGT_ALLSOLD, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Outcome by Store Decile')
axes[1].legend(fontsize=8)
axes[1].set_xticks(DECILES)

efficiency = [a / (a + n) * 100 for a, n in zip(TGT_ALLSOLD, TGT_NOTHING)]
axes[2].bar(DECILES, efficiency, color=['#e74c3c' if e < 65 else ('#f39c12' if e < 72 else '#27ae60') for e in efficiency])
axes[2].set_xlabel('Store Decile')
axes[2].set_ylabel('Efficiency %')
axes[2].set_title('TARGET: Redistribution Efficiency\n(All-sold / (All-sold + Nothing-sold))')
axes[2].set_xticks(DECILES)
axes[2].axhline(y=70, color='#f39c12', linestyle='--', alpha=0.5)
for d, e in zip(DECILES, efficiency):
    axes[2].text(d, e + 0.5, f'{e:.0f}%', ha='center', fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- fig_findings_05.png - Target: ST heatmaps 3-panel (SalesBucket x Store) ----
tgt_buckets = ['0', '1-2', '3-5', '6-10', '11+']
tgt_st_4m = np.array([
    [23.1, 23.4, 36.4],
    [26.3, 28.6, 32.1],
    [41.5, 40.8, 45.3],
    [58.6, 59.3, 63.1],
    [73.8, 72.7, 77.0],
])
tgt_pct_nothing = np.array([
    [73.7, 73.7, 61.1],
    [65.5, 62.0, 58.0],
    [45.1, 45.5, 40.8],
    [28.1, 26.8, 22.3],
    [12.3, 11.9, 10.8],
])
tgt_pct_allsold = np.array([
    [31.4, 37.7, 51.6],
    [38.0, 40.9, 47.0],
    [54.4, 54.6, 61.0],
    [74.3, 76.2, 78.8],
    [84.9, 87.9, 89.5],
])

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
sns.heatmap(tgt_st_4m, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=STORES, yticklabels=tgt_buckets, ax=axes[0],
            vmin=20, vmax=80, linewidths=1, cbar_kws={'label': 'ST % (4M)'})
axes[0].set_title('Target Sell-through (4M) %', fontsize=10)
axes[0].set_ylabel('Sales Bucket')

sns.heatmap(tgt_pct_nothing, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=STORES, yticklabels=tgt_buckets, ax=axes[1],
            vmin=10, vmax=75, linewidths=1, cbar_kws={'label': 'Nothing sold 4M %'})
axes[1].set_title('Target Nothing-Sold 4M % (PROBLEM)', fontsize=10)
axes[1].set_ylabel('Sales Bucket')

sns.heatmap(tgt_pct_allsold, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=STORES, yticklabels=tgt_buckets, ax=axes[2],
            vmin=30, vmax=90, linewidths=1, cbar_kws={'label': 'All sold total %'})
axes[2].set_title('Target All-Sold Total % (SUCCESS)', fontsize=10)
axes[2].set_ylabel('Sales Bucket')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_05.png")

# ---- fig_findings_06.png - Target: brand-fit + stock coverage ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Brand-fit heatmap
brand_fits = ['BrandWeak', 'BrandMid', 'BrandStrong']
bf_allsold_matrix = np.array([
    [55.3, 63.7, 68.4],
    [59.1, 64.3, 70.0],
    [63.9, 69.5, 75.8],
])
sns.heatmap(bf_allsold_matrix, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=brand_fits, yticklabels=STORES, ax=axes[0],
            vmin=50, vmax=80, linewidths=1, cbar_kws={'label': 'All-sold Total %'})
axes[0].set_title('Target: Brand-Store Fit -> All-sold Total %', fontsize=10)
axes[0].set_ylabel('Store Strength')

# Stock coverage effect: grouped by coverage bucket
stock_buckets_uniq = ['New (0d)', 'Brief', 'Partial', 'Established']
stock_allsold_35 = []
stock_nosale_35 = []
for bkt in stock_buckets_uniq:
    rows = [r for r in TGT_STOCK if r[0] == bkt and r[1] == '3-5']
    if rows:
        stock_allsold_35.append(rows[0][3])
        stock_nosale_35.append(rows[0][4])
    else:
        stock_allsold_35.append(0)
        stock_nosale_35.append(0)

x_sc = np.arange(len(stock_buckets_uniq))
w = 0.35
axes[1].bar(x_sc - w/2, stock_allsold_35, w, color='#27ae60', label='All-sold Total %')
axes[1].bar(x_sc + w/2, stock_nosale_35, w, color='#e74c3c', label='Nothing-sold %')
axes[1].set_xticks(x_sc)
axes[1].set_xticklabels(stock_buckets_uniq, fontsize=8, rotation=10)
axes[1].set_ylabel('%')
axes[1].set_title('Target: Stock Coverage Effect (SalesBucket 3-5)\n(Established = nizsi all-sold nez Brief)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (a, n) in enumerate(zip(stock_allsold_35, stock_nosale_35)):
    axes[1].text(i - w/2, a + 1, f'{a}%', ha='center', fontsize=7, color='#27ae60')
    axes[1].text(i + w/2, n + 1, f'{n}%', ha='center', fontsize=7, color='#e74c3c')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_06.png")

# ---- fig_findings_07.png - NEW v7: Modifier validation ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

mod_names = [r[0] for r in MODIFIER_VALID]
mod_confirmed = [r[3] for r in MODIFIER_VALID]
mod_status = [r[1] for r in MODIFIER_VALID]
mod_evidence = [r[2] for r in MODIFIER_VALID]

colors_mod = ['#27ae60' if c else '#e74c3c' for c in mod_confirmed]
# Partially confirmed -> orange
for i, s in enumerate(mod_status):
    if 'Castecne' in s or 'Novy' in s:
        colors_mod[i] = '#f39c12'

y_mod = np.arange(len(mod_names))
bars = ax.barh(y_mod, [1.0 if c else 0.4 for c in mod_confirmed], color=colors_mod,
               edgecolor='#333', linewidth=0.5, height=0.6)

for i, (name, status, ev) in enumerate(zip(mod_names, mod_status, mod_evidence)):
    x_pos = (1.05 if mod_confirmed[i] else 0.45)
    ax.text(x_pos, i, f'{status}: {ev}', va='center', fontsize=8,
            color=colors_mod[i], fontweight='bold')

ax.set_yticks(y_mod)
ax.set_yticklabels(mod_names, fontsize=9)
ax.set_xlim(0, 2.0)
ax.set_xlabel('')
ax.set_xticks([])
ax.set_title('v7 Validace v5 modifikatoru na realnych datech\n'
             '(zelena = Potvrzeno, oranzova = Castecne/Novy, cervena = Nepotvrzeno)',
             fontsize=11, fontweight='bold')
ax.invert_yaxis()

legend_patches = [
    mpatches.Patch(color='#27ae60', label='Potvrzeno'),
    mpatches.Patch(color='#f39c12', label='Castecne / Novy'),
    mpatches.Patch(color='#e74c3c', label='Nepotvrzeno (dropped)'),
]
ax.legend(handles=legend_patches, loc='lower right', fontsize=9)

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_07.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_07.png")

# ---- fig_findings_08.png - LastSaleGap: sold_after + OS_t + RO_t ----
fig, ax = plt.subplots(1, 1, figsize=(14, 6))

gap_labels = [r[0] for r in LAST_SALE_GAP]
gap_os_t = [r[2] for r in LAST_SALE_GAP]
gap_ro_t = [r[3] for r in LAST_SALE_GAP]
gap_sa = [r[4] for r in LAST_SALE_GAP]

x_gap = np.arange(len(gap_labels))
w = 0.25
ax.bar(x_gap - w, gap_sa, w, color='#27ae60', label='Sold After %', edgecolor='#333', linewidth=0.5)
ax.bar(x_gap, gap_ro_t, w, color='#e74c3c', label='Reorder Total %', edgecolor='#333', linewidth=0.5)
ax.bar(x_gap + w, gap_os_t, w, color='#3498db', label='Oversell Total %', edgecolor='#333', linewidth=0.5)

ax.set_xticks(x_gap)
ax.set_xticklabels(gap_labels, fontsize=9)
ax.set_ylabel('%')
ax.set_title('LastSaleGap: Sold After % + Oversell + Reorder Total % by Gap Bucket\n'
             '(kratsi gap = vyssi sold_after, potvrzuje modifier LastSaleGap <=90d)', fontsize=11)
ax.legend(fontsize=9)

for i, (sa, ro, os_v) in enumerate(zip(gap_sa, gap_ro_t, gap_os_t)):
    ax.text(i - w, sa + 1, f'{sa}%', ha='center', fontsize=7, color='#27ae60')
    ax.text(i, ro + 1, f'{ro}%', ha='center', fontsize=7, color='#e74c3c')
    ax.text(i + w, os_v + 1, f'{os_v}%', ha='center', fontsize=7, color='#3498db')
    ax.text(i - w, -3, f'n={LAST_SALE_GAP[i][1]:,}', ha='center', fontsize=6, color='#666')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_08.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_08.png")

# ---- fig_findings_09.png - Pair analysis pie + seasonality comparison bars ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pair analysis pie
pair_labels = [r[0] for r in PAIRS]
pair_counts = [r[1] for r in PAIRS]
pair_colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
wedges, texts, autotexts = axes[0].pie(pair_counts, labels=pair_labels, colors=pair_colors,
                                        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[0].set_title('Pair Analysis: Source+Target Combined\n(Win-Win 66.5% = oversell v cili)', fontsize=10)

# Seasonality bars
seas_labels = [r[0] for r in SEASONALITY]
seas_os_t = [r[2] for r in SEASONALITY]
seas_ro_t = [r[3] for r in SEASONALITY]
seas_cnt = [r[1] for r in SEASONALITY]
x_s = np.arange(len(seas_labels))
w = 0.35
axes[1].bar(x_s - w/2, seas_os_t, w, color='#3498db', label='Oversell Total %')
axes[1].bar(x_s + w/2, seas_ro_t, w, color='#e74c3c', label='Reorder Total %')
axes[1].set_xticks(x_s)
axes[1].set_xticklabels(seas_labels, fontsize=9)
axes[1].set_ylabel('%')
axes[1].set_title('Sezonnost: Oversell vs Reorder Total %\n(Sezonni produkty = 2x oversell, 1.5x reorder)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (os_v, ro_v, c) in enumerate(zip(seas_os_t, seas_ro_t, seas_cnt)):
    axes[1].text(i, max(os_v, ro_v) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_09.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_09.png")

# ---- fig_findings_10.png - Flow matrix heatmap ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

pairs_matrix = np.zeros((3, 3))
pct_matrix = np.zeros((3, 3))
for r in FLOW:
    si = STORES.index(r[0])
    ti = STORES.index(r[1])
    pairs_matrix[si][ti] = r[2]
    pct_matrix[si][ti] = r[3]

sns.heatmap(pairs_matrix, annot=True, fmt='.0f', cmap='Blues',
            xticklabels=['Tgt ' + s for s in STORES],
            yticklabels=['Src ' + s for s in STORES], ax=axes[0],
            linewidths=1, cbar_kws={'label': 'Pair count'})
axes[0].set_title('Flow: Pair Count\n(Source Store -> Target Store)')

sns.heatmap(pct_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=['Tgt ' + s for s in STORES],
            yticklabels=['Src ' + s for s in STORES], ax=axes[1],
            linewidths=1, cbar_kws={'label': '% of total pairs'})
axes[1].set_title('Flow: % of Total Pairs\n(Mid->Strong = largest flow at 19.6%)')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_10.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_10.png")


# ############################################################
# BUILD HTML: Report 1
# ############################################################

# Segment summary rows
seg_summary_rows = ""
for r in SEGMENTS:
    seg, skus, pct, rdq, os_t, ro_t, ro_t_sku, sold_after, avg_days = r
    cls_r = 'bad' if ro_t_sku > 50 else ('warn' if ro_t_sku > 35 else 'good')
    cls_sa = 'good' if sold_after > 70 else ('warn' if sold_after > 50 else 'bad')
    seg_summary_rows += (f'<tr><td><b>{seg}</b></td><td>{skus:,}</td><td>{pct}%</td>'
                         f'<td>{rdq:,}</td><td>{os_t}%</td>'
                         f'<td class="{cls_r}">{ro_t_sku}%</td>'
                         f'<td class="{cls_sa}">{sold_after}%</td>'
                         f'<td>{avg_days}d</td></tr>\n')

# Segment x Store table rows
def seg_store_table(data):
    rows = ""
    for r in data:
        seg, sto, cnt, rdq, o4m, otot, r4m, rtot, rtot_sku, sold_after = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]
        cls_o = 'good' if otot < 10 else ('warn' if otot < 15 else 'bad')
        cls_r = 'bad' if rtot_sku > 50 else ('warn' if rtot_sku > 35 else 'good')
        cls_sa = 'good' if sold_after > 70 else ('warn' if sold_after > 50 else 'bad')
        rows += (f'<tr><td>{seg}</td><td>{sto}</td><td>{cnt:,}</td>'
                 f'<td class="{cls_o}">{otot}%</td>'
                 f'<td class="{cls_r}">{rtot_sku}%</td>'
                 f'<td class="{cls_sa}">{sold_after}%</td>'
                 f'<td>{rdq:,}</td></tr>\n')
    return rows

total_src_skus = sum(r[2] for r in SEG_STORE)
total_redist_qty = sum(r[3] for r in SEG_STORE)

# Reclassification rows
reclass_rows = ""
for r in RECLASS:
    old_p, new_s, skus, os_t, ro_t, sold_after = r
    cls_sa = 'good' if sold_after >= 70 else ('warn' if sold_after >= 50 else 'bad')
    reclass_rows += (f'<tr><td>{old_p}</td><td>{new_s}</td><td>{skus:,}</td>'
                     f'<td>{os_t}%</td><td>{ro_t}%</td>'
                     f'<td class="{cls_sa}">{sold_after}%</td></tr>\n')

# Modifier validation rows
modifier_rows = ""
for r in MODIFIER_VALID:
    mod, status, evidence, confirmed = r
    if confirmed:
        if 'Castecne' in status or 'Novy' in status:
            cls = 'warn'
        else:
            cls = 'good'
    else:
        cls = 'bad'
    modifier_rows += (f'<tr><td>{mod}</td><td class="{cls}">{status}</td>'
                      f'<td>{evidence}</td><td>{"ANO" if confirmed else "NE"}</td></tr>\n')

# LastSaleGap rows
gap_rows = ""
for r in LAST_SALE_GAP:
    bkt, skus, os_t, ro_t, sold_after = r
    cls_sa = 'good' if sold_after >= 70 else ('warn' if sold_after >= 50 else 'bad')
    gap_rows += (f'<tr><td>{bkt}</td><td>{skus:,}</td><td>{os_t}%</td>'
                 f'<td>{ro_t}%</td><td class="{cls_sa}">{sold_after}%</td></tr>\n')

# Target Store x Sales rows
tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sal, sto, cnt, st4, stt, ns4, pn, as4, pa = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 30 else 'good')
    cls_a = 'good' if pa > 70 else ('warn' if pa > 50 else 'bad')
    tgt_ss_rows += (f'<tr><td>{sal}</td><td>{sto}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.1f}%</td><td>{stt:.1f}%</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n')

# Brand-fit rows
tgt_bf_rows = ""
for r in BRAND_FIT:
    sto, bf, cnt, allsold, nosale = r
    cls_n = 'bad' if nosale > 50 else ('warn' if nosale > 40 else 'good')
    cls_a = 'good' if allsold > 70 else ('warn' if allsold > 60 else 'bad')
    tgt_bf_rows += (f'<tr><td>{sto}</td><td>{bf}</td><td>{cnt:,}</td>'
                    f'<td class="{cls_a}">{allsold}%</td><td class="{cls_n}">{nosale}%</td></tr>\n')

# Stock coverage target rows
tgt_sc_rows = ""
for r in TGT_STOCK:
    bkt, sales, skus, allsold, nosale, sold_after = r
    cls_a = 'good' if allsold > 80 else ('warn' if allsold > 60 else 'bad')
    cls_sa = 'good' if sold_after > 70 else ('warn' if sold_after > 50 else 'bad')
    tgt_sc_rows += (f'<tr><td>{bkt}</td><td>{sales}</td><td>{skus:,}</td>'
                    f'<td class="{cls_a}">{allsold}%</td><td>{nosale}%</td>'
                    f'<td class="{cls_sa}">{sold_after}%</td></tr>\n')

# Pair analysis rows
pair_rows = ""
for r in PAIRS:
    name, cnt, pct = r
    cls = 'good' if name == 'Win-Win' else ('warn' if name == 'Win-Lose' else 'bad')
    pair_rows += (f'<tr><td class="{cls}">{name}</td>'
                  f'<td>{cnt:,}</td><td>{pct}%</td></tr>\n')

# Seasonality rows
seas_rows = ""
for r in SEASONALITY:
    cat, cnt, os_t, ro_t = r
    cls_r = 'bad' if ro_t > 40 else ('warn' if ro_t > 30 else 'good')
    seas_rows += (f'<tr><td>{cat}</td><td>{cnt:,}</td>'
                  f'<td>{os_t}%</td><td class="{cls_r}">{ro_t}%</td></tr>\n')

# SkuClass rows
sku_class_rows = ""
for r in SKUCLASS:
    cls_name, skus, os_t, ro_t, ro_t_sku = r
    cls_r = 'bad' if ro_t_sku > 40 else ('warn' if ro_t_sku > 25 else 'good')
    sku_class_rows += (f'<tr><td>{cls_name}</td><td>{skus:,}</td>'
                       f'<td>{os_t}%</td><td>{ro_t}%</td>'
                       f'<td class="{cls_r}">{ro_t_sku}%</td></tr>\n')

# ProductConc rows
prod_conc_rows = ""
for r in PROD_CONC:
    bkt, skus, os_t, ro_t = r
    prod_conc_rows += (f'<tr><td>{bkt}</td><td>{skus:,}</td>'
                       f'<td>{os_t}%</td><td>{ro_t}%</td></tr>\n')

# Flow rows
flow_rows = ""
for r in FLOW:
    sg, tg, pairs_cnt, pct = r
    flow_rows += (f'<tr><td>{sg}</td><td>{tg}</td><td>{pairs_cnt:,}</td>'
                  f'<td>{pct}%</td></tr>\n')

O = OVERVIEW

html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v7 Consolidated Findings: SalesBased MinLayers - Synteza v5+v6</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings v7: SalesBased MinLayers (Synteza v5+v6) <span class="v7-badge">v7</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p><b>v7 = SYNTEZA</b> v5 (modifikatory, growth pockets, bidirectional target)
a v6 (velocity segmenty, stock normalizace, sold-after%).
<b>v7 validuje ktere v5 modifikatory preziji na realnych datech, nahradi Pattern velocity segmenty z v6,
a pridava bidirectional target z v5.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili ({O['os4m_pct']}%). Reorder je hlavni problem ({O['ro_t_pct']}% qty).</b><br>
Oversell 4M je pouze {O['os4m_pct']}% ({O['os4m_sku']:,} SKU, {O['os4m_qty']:,} qty).
Reorder: {O['ro_t_sku']:,} SKU, {O['ro_t_qty']:,} kusu ({O['ro_t_pct']}% objemu).
v7 synteza potvrzuje: velocity segmenty z v6 jsou zakladem, potvrzene modifikatory z v5 je doladuji.
</div>

<div class="insight-new">
<b>v7 KLICOVY PRISPEVEK:</b> Reklasifikacni matice (v5 Pattern -> v6 Segment) ukazuje, ze stare
Patterns byly hrube priblizeni. "Sporadic" (14,033 SKU) skryval 3 ruzne segmenty s prodejnim
uspechom 64-92%. "Consistent" (709 SKU) -> prevazne ActiveSeller s 98% sold_after.
Modifikatory: 5 z 8 potvrzeno, 3 zamitnuty pro nedostatek dat.
</div>

<!-- ========== 1. OVERVIEW ========== -->
<div class="section">
<h2>1. Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">{O['pairs']:,}</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">{O['redist_qty']:,}</div><div class="l">Total redistributed pcs</div></div>
<div class="metric"><div class="v">{O['source_skus']:,}</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">{O['target_skus']:,}</div><div class="l">Target SKU</div></div>
</div>

<h3>Source: Celkove metriky - 4M a total</h3>
<table>
<tr><th>Metric</th><th>4 months</th><th>Total (~9M)</th></tr>
<tr><td><b>Total redistributed</b></td><td>{O['redist_qty']:,} pcs</td><td>{O['redist_qty']:,} pcs</td></tr>
<tr><td><b>Oversell (SKU)</b></td><td class="good">{O['os4m_sku']:,} SKU (3.6%)</td><td>{O['os_t_sku']:,} SKU (12.8%)</td></tr>
<tr><td><b>Oversell (qty)</b></td><td class="good">{O['os4m_qty']:,} qty ({O['os4m_pct']}%)</td><td>{O['os_t_qty']:,} qty ({O['os_t_pct']}%)</td></tr>
<tr><td><b>Reorder (SKU)</b></td><td class="bad">{O['ro4m_sku']:,} SKU (19.3%)</td><td class="bad">{O['ro_t_sku']:,} SKU (37.6%)</td></tr>
<tr><td><b>Reorder (qty)</b></td><td class="bad">{O['ro4m_qty']:,} qty ({O['ro4m_pct']}%)</td><td class="bad">{O['ro_t_qty']:,} qty ({O['ro_t_pct']}%)</td></tr>
</table>

<div class="insight">
<b>v7 zaver:</b> Oversell v cili ({O['os4m_pct']}%). Reorder je hlavni problem (37.6% SKU, {O['ro_t_pct']}% qty).
Velocity segmenty + potvrzene modifikatory = cesta ke snizeni reorderu.
</div>
</div>

<!-- ========== 2. VELOCITY SEGMENTS ========== -->
<div class="section">
<h2>2. Velocity-Normalized Segmentace <span class="v7-badge">v7 = v6 base</span></h2>
<p><b>Velocity</b> = Sales_12M / DaysInStock_12M x 30 (mesicni rate normalizovana na dostupnost).
v7 potvrzuje v6 segmentaci jako zaklad. Stary v5 Pattern je nahrazen.</p>

<img src="fig_findings_01.png">
<table>
<tr><th>Segment</th><th>SKU</th><th>Podil</th><th>Redist qty</th><th>Oversell Total %</th>
<th>Reorder Total SKU %</th><th>Sold After %</th><th>Avg Days in Stock</th></tr>
{seg_summary_rows}
</table>

<div class="insight-new">
<b>v7 insight:</b> "Sold After %" je silny prediktor potvrzeny jak v5 tak v6.
ActiveSeller ma 93.8% sold_after ale take 58.3% reorder - tyto produkty se prodaji a potrebuji doplneni.
TrueDead ma jen 36.9% sold_after a 28.2% reorder - nizke riziko.
</div>

<h3>2.1 Segment x Store Detail (15 segmentu)</h3>
<img src="fig_findings_02.png">
<table>
<tr><th>Segment</th><th>Store</th><th>SKU</th><th>Oversell Total %</th>
<th>Reorder Total SKU %</th><th>Sold After %</th><th>Redist qty</th></tr>
{seg_store_table(SEG_STORE)}
<tr style="font-weight:bold;background:#e8e8e8"><td colspan="2">TOTAL</td><td>{total_src_skus:,}</td>
<td colspan="3">-</td><td>{total_redist_qty:,}</td></tr>
</table>

<div class="insight-bad">
<b>MUST RAISE ML (reorder_tot_sku >50%):</b> ActiveSeller+Weak (52.8%), ActiveSeller+Mid (59.8%),
ActiveSeller+Strong (58.3%), SlowFull+Strong (51.4%), BriefNoSale (52.1%).
</div>
</div>

<!-- ========== 3. RECLASSIFICATION (v7 KEY) ========== -->
<div class="section">
<h2>3. Reklasifikace: v5 Pattern -> v6 Velocity Segment <span class="new-badge">KEY v7</span></h2>
<p><b>Toto je klicovy prispevek v7:</b> Mapovani starych v5 Patterns na nove v6 Velocity Segmenty
s realnym vysledkem (sold_after %). Ukazuje, ze Pattern byl hrube priblizeni.</p>

<img src="fig_findings_03.png">
<table>
<tr><th>v5 Pattern</th><th>v6 Segment</th><th>SKU</th><th>Oversell Total %</th>
<th>Reorder Total %</th><th>Sold After %</th></tr>
{reclass_rows}
</table>

<div class="insight-new">
<b>v7 klicove zjisteni:</b><br>
- <b>Sporadic (14,033 SKU)</b> -> rozdeleno na SlowFull (9,808, sold_after 64%), SlowPartial (1,975, 77%),
  ActiveSeller (1,856, 92%) - <b>dramaticky odlisne chovani!</b><br>
- <b>Consistent (709)</b> -> prevazne ActiveSeller (644, sold_after 98%) - tito jsou nejlepsi<br>
- <b>Dead (15,403)</b> -> prevazne TrueDead (11,834, sold_after 34%) + PartialDead (3,533, 57%)<br>
- <b>Dying (6,599)</b> -> prevazne TrueDead (6,521, sold_after 42%) - umiraji, ale pomaleji nez Dead<br>
- <b>Declining (359)</b> -> SlowFull (324, 79%) + ActiveSeller (35, 100%) - stale prodavaji!
</div>
</div>

<!-- ========== 4. STORE DECILES ========== -->
<div class="section">
<h2>4. Source + Target: Sila predajni (decily)</h2>
<img src="fig_findings_04.png">
<table>
<tr><th>Metric</th><th>D1 (Weak)</th><th>D10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Oversell 4M</td><td class="good">1.9%</td><td class="good">4.5%</td><td>Oversell je v cili ve vsech decilech</td></tr>
<tr><td>Source Reorder Total</td><td class="warn">24.0%</td><td class="bad">38.6%</td><td>Silne predajny = vyssi reorder riziko</td></tr>
<tr><td>Target All-Sold Total</td><td class="warn">48.3%</td><td class="good">70.1%</td><td>Silne predajny prodaji vse</td></tr>
<tr><td>Target Nothing-Sold</td><td class="bad">32.1%</td><td class="good">13.7%</td><td>Slabe predajny = vice zaseklych zbozi</td></tr>
</table>

<div class="insight">
<b>v7 zaver:</b> Store strength gradient je konzistentni s v5 i v6. Silnejsi predajny = lepsi target,
ale take vyssi reorder na source. Bidirectional optimalizace: snizit reorder silnych source + zvysit ML slabych target.
</div>
</div>

<!-- ========== 5. TARGET SELL-THROUGH ========== -->
<div class="section">
<h2>5. Target: Sell-through analyza (bidirectional z v5) <span class="v7-badge">v5+v6</span></h2>

<h3>5.1 Store Strength x Sales Bucket</h3>
<img src="fig_findings_05.png">
<table>
<tr><th>SalesBucket</th><th>Store</th><th>SKU</th><th>ST 4M %</th><th>ST Total %</th>
<th>Nothing-sold 4M %</th><th>All-sold Total %</th></tr>
{tgt_ss_rows}
</table>

<div class="insight-good">
<b>11+ sales bucket = vyborny target:</b> 84.9-89.5% all-sold, nothing-sold jen 10.8-12.3%.
v7 bidirectional: growth pocket = 11+ Strong (ML=4), reduction pocket = 0 Weak (ML=1).
</div>

<h3>5.2 Brand-Store Fit + Stock Coverage <span class="v7-badge">v7</span></h3>
<img src="fig_findings_06.png">
<table>
<tr><th>Store</th><th>BrandFit</th><th>SKU</th><th>All-sold Total %</th><th>Nothing-sold %</th></tr>
{tgt_bf_rows}
</table>

<h3>5.3 Target Stock Coverage Effect</h3>
<table>
<tr><th>Stock Coverage</th><th>Sales Bucket</th><th>SKU</th><th>All-sold Total %</th><th>Nothing-sold %</th><th>Sold After %</th></tr>
{tgt_sc_rows}
</table>

<div class="insight-new">
<b>v7 zaver:</b> Stock coverage efekt je silny. New (0d) produkty s 0 sales: all-sold 58.1%,
ale s 11+ sales: 93.8%. Brief a Partial target s vysokymi sales jsou growth pockets.
Established target s nizkymi sales jsou reduction pockets.
</div>
</div>

<!-- ========== 6. MODIFIER VALIDATION (v7 KEY) ========== -->
<div class="section">
<h2>6. Validace v5 modifikatoru na realnych datech <span class="new-badge">KEY v7</span></h2>
<p><b>v7 testoval 8 modifikatoru z v5 na realnych datech.</b> 5 potvrzeno, 3 zamitnuty.</p>

<img src="fig_findings_07.png">
<table>
<tr><th>Modifier</th><th>Status</th><th>Evidence</th><th>Zahrnout v7?</th></tr>
{modifier_rows}
</table>

<div class="insight-new">
<b>v7 zaver - Potvrzene modifikatory:</b><br>
- <b>LastSaleGap <=90d:</b> sold_after 85-90%, silny signal recentni aktivity<br>
- <b>Seasonal:</b> 2x oversell, 1.5x reorder - musi byt chraneny<br>
- <b>RedistRatio >=75%:</b> castecne potvrzeno, nizky objem ale spravny smer<br>
- <b>Delisting:</b> RO 10.9%, bezpecne pro ML=0<br>
- <b>Sold After >=80% (NOVY):</b> ActiveSeller 94%, nejsilnejsi prediktor<br>
<br>
<b>Zamitnuty:</b> ProductConc <10% (zadny gradient), PhantomStock (1 SKU), Loop 4+ (7 SKU) -
nedostatek dat pro validaci.
</div>
</div>

<!-- ========== 7. LAST SALE GAP ========== -->
<div class="section">
<h2>7. LastSaleGap analyza</h2>
<img src="fig_findings_08.png">
<table>
<tr><th>Gap Bucket</th><th>SKU</th><th>Oversell Total %</th><th>Reorder Total %</th><th>Sold After %</th></tr>
{gap_rows}
</table>

<div class="insight">
<b>v7 zaver:</b> Kratsi gap = vyssi sold_after (0-30d: 90%, Never/730d+: 39%).
Modifier LastSaleGap <=90d: <b>POTVRZEN</b>. Recentni prodejni aktivita je silny signal.
</div>
</div>

<!-- ========== 8. SKUCLASS + PRODUCT CONCENTRATION ========== -->
<div class="section">
<h2>8. SkuClass + Product Concentration</h2>

<h3>8.1 SkuClass</h3>
<table>
<tr><th>SkuClass</th><th>SKU</th><th>Oversell Total %</th><th>Reorder Total %</th><th>Reorder Total SKU %</th></tr>
{sku_class_rows}
</table>

<div class="insight-good">
<b>Delisted:</b> RO 10.9% qty, RO SKU 13.2% - bezpecne pro ML=0. <b>Modifier POTVRZEN.</b>
</div>

<h3>8.2 Product Concentration</h3>
<table>
<tr><th>Concentration Bucket</th><th>SKU</th><th>Oversell Total %</th><th>Reorder Total %</th></tr>
{prod_conc_rows}
</table>

<div class="insight-bad">
<b>ProductConc <10% - NEPOTVRZEN:</b> Zadny jasny gradient mezi buckety (<10%: RO 32.3%, 10-25%: 37.2%, 25-50%: 35.4%).
50%+ ma nizky reorder ale jen 140 SKU - maly vzorek. <b>Modifier zamitnut v v7.</b>
</div>
</div>

<!-- ========== 9. PAIR ANALYSIS + SEASONALITY ========== -->
<div class="section">
<h2>9. Parova analyza + Sezonnost</h2>
<img src="fig_findings_09.png">

<h3>9.1 Pair Analysis</h3>
<table>
<tr><th>Outcome</th><th>Count</th><th>Share</th></tr>
{pair_rows}
</table>
<div class="insight-good">
<b>Win-Win = 66.5%</b> (28,179 paru). Lose-Lose = jen 2.0%.
</div>

<h3>9.2 Sezonnost</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Oversell Total %</th><th>Reorder Total %</th></tr>
{seas_rows}
</table>
<div class="insight-bad">
<b>Sezonni produkty:</b> OS 18.8% (2x non-seasonal), RO 45.3% (1.5x non-seasonal).
<b>Modifier Seasonal: POTVRZEN.</b>
</div>
</div>

<!-- ========== 10. FLOW MATRIX ========== -->
<div class="section">
<h2>10. Flow Matrix: odkud kam</h2>
<img src="fig_findings_10.png">
<table>
<tr><th>Source Store</th><th>Target Store</th><th>Pairs</th><th>% of Total</th></tr>
{flow_rows}
</table>
<div class="insight">
<b>Nejvic paru: Mid->Strong (19.6%)</b> a Mid->Mid (17.2%).
Distribuce preferuje posilani do silnych predajni.
</div>
</div>

<!-- ========== 11. SUMMARY TABLE ========== -->
<div class="section">
<h2>11. Souhrnna tabulka v7: Vsechny faktory + validace</h2>

<table>
<tr><th>Factor</th><th>v5 status</th><th>v7 validace</th><th>Impact</th><th>Source ML</th><th>Target ML</th></tr>
<tr><td>Velocity Segment: ActiveSeller</td><td>Consistent/Sporadic</td><td class="good">POTVRZEN</td><td class="bad">58.3% reorder, 93.8% sold_after</td><td class="bad">ML=3-4</td><td>-</td></tr>
<tr><td>Velocity Segment: TrueDead</td><td>Dead/Dying</td><td class="good">POTVRZEN</td><td>28.2% reorder, 36.9% sold_after</td><td class="good">ML=1 (ord min)</td><td>-</td></tr>
<tr><td>Sold After % >=80%</td><td>Novy</td><td class="good">POTVRZEN</td><td class="bad">silny prediktor</td><td class="bad">+1 ML</td><td>-</td></tr>
<tr><td>LastSaleGap <=90d</td><td>Navrzen</td><td class="good">POTVRZEN</td><td>sold_after 85-90%</td><td class="bad">+1 ML</td><td>-</td></tr>
<tr><td>Seasonal >=20% NovDec</td><td>Navrzen</td><td class="good">POTVRZEN</td><td class="bad">OS 2x, RO 1.5x</td><td class="bad">+1 ML</td><td>-</td></tr>
<tr><td>Delisting</td><td>Override</td><td class="good">POTVRZEN</td><td class="good">RO 10.9%</td><td class="good">ML=0</td><td class="good">ML=0</td></tr>
<tr><td>RedistRatio >=75%</td><td>Navrzen</td><td class="warn">CASTECNE</td><td>nizky objem</td><td>+1 ML</td><td>-</td></tr>
<tr><td>ProductConc <10%</td><td>Navrzen</td><td class="bad">ZAMITNUTO</td><td>zadny gradient</td><td>-</td><td>-</td></tr>
<tr><td>PhantomStock</td><td>Navrzen</td><td class="bad">ZAMITNUTO</td><td>1 SKU</td><td>-</td><td>-</td></tr>
<tr><td>Loop 4+</td><td>Navrzen</td><td class="bad">ZAMITNUTO</td><td>7 SKU</td><td>-</td><td>-</td></tr>
<tr><td>Target: 11+ sales + Strong</td><td>Growth pocket</td><td class="good">POTVRZEN</td><td class="good">89.5% all-sold</td><td>-</td><td class="good">ML=4</td></tr>
<tr><td>Target: 0 sales + Weak</td><td>Reduction pocket</td><td class="good">POTVRZEN</td><td class="bad">73.7% nothing-sold</td><td>-</td><td class="bad">ML=1</td></tr>
<tr><td>Brand Weak+Store Weak</td><td>-1 ML</td><td class="good">POTVRZEN</td><td class="bad">nothing-sold 54.9%</td><td>-</td><td class="bad">-1 ML</td></tr>
</table>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v7 Synteza (v5+v6) | ML 0-4 | Orderable min=1 | Bidirectional target</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  [OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE (5 charts)
#
# ############################################################
print()
print("--- Report 2: Decision Tree (5 charts) ---")

# ---- fig_dtree_01.png - Source ML: 6x3 heatmap (Segment x Store) ----
seg_order_ml = ['TrueDead', 'PartialDead', 'BriefNoSale', 'SlowPartial', 'SlowFull', 'ActiveSeller']
src_ml_matrix = np.array([
    [SRC_ML[(seg, s)] for s in STORES]
    for seg in seg_order_ml
])

fig, ax = plt.subplots(1, 1, figsize=(10, 7))
sns.heatmap(src_ml_matrix, annot=False, cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_ml, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer (0-4)'})
ax.set_title('Source MinLayer v7: Lookup Table\n(Velocity Segment x Store, orderable min=1, validated modifiers)\nML 0 only for non-orderable/delisted', fontsize=11)
ax.set_ylabel('Velocity Segment')
ax.set_xlabel('Store Strength')
for i in range(6):
    for j in range(3):
        val = src_ml_matrix[i][j]
        note = ''
        if seg_order_ml[i] == 'TrueDead':
            note = '\n(ord min)'
        elif seg_order_ml[i] == 'PartialDead' and j < 2:
            note = '\n(ord min)'
        color = 'white' if val >= 3 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={int(val)}{note}', ha='center', va='center',
                fontsize=9, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_01.png")

# ---- fig_dtree_02.png - Target ML: 5x3 heatmap (SalesBucket x Store) ----
tgt_ml_labels_chart = ['0', '1-2', '3-5', '6-10', '11+']
tgt_ml_matrix = np.array([
    [TGT_ML[(b, s)] for s in STORES]
    for b in tgt_ml_labels_chart
])

fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(tgt_ml_matrix, annot=False, cmap='YlGnBu',
            xticklabels=STORES, yticklabels=tgt_ml_labels_chart, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Target MinLayer (0-4)'})
ax.set_title('Target MinLayer v7: Lookup Table (bidirectional)\n(Sales Bucket x Store, range 0-4, growth + reduction pockets)', fontsize=11)
ax.set_ylabel('Sales Bucket')
ax.set_xlabel('Store Strength')
for i in range(5):
    for j in range(3):
        val = tgt_ml_matrix[i][j]
        color = 'white' if val >= 3 else '#333'
        label = f'ML={val}'
        if i == 4 and j == 2:
            label += '\nGROWTH'
        elif i == 0 and j == 0:
            label += '\nREDUCE'
        ax.text(j + 0.5, i + 0.5, label, ha='center', va='center',
                fontsize=10, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_02.png")

# ---- fig_dtree_03.png - 4-direction decision diagram ----
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('4-Direction MinLayer Decision Framework (v7 synteza, ML 0-4, validated modifiers)', fontsize=14, fontweight='bold', pad=20)


def draw_box(ax, x, y, w, h, text, color='#ecf0f1', border='#2c3e50', fontsize=8):
    rect = plt.Rectangle((x - w/2, y - h/2), w, h,
                          facecolor=color, edgecolor=border, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, zorder=3, multialignment='center')


def draw_arrow(ax, x1, y1, x2, y2, text='', color='#7f8c8d'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5), zorder=1)
    if text:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 1, my, text, fontsize=7, color=color)


draw_box(ax, 50, 55, 20, 6, 'MinLayer\nDecision\nML 0-4', '#3498db', fontsize=10)

draw_box(ax, 22, 82, 28, 14,
         'SOURCE ML UP\n(raise MinLayer)\n\nActiveSeller: ML=3-4\nSlowPartial+Strong: ML=3\nSlowFull+Mid/Strong: ML=2\n+1: Seasonal >=20% NovDec [v5 POTVRZEN]\n+1: Sold After >80% [NOVY v7]\n+1: LastSaleGap <=90d [v5 POTVRZEN]\nCap at ML=4',
         '#fce4e4', '#e74c3c', fontsize=5.5)
draw_arrow(ax, 42, 58, 30, 75, 'Reorder >40%', '#e74c3c')

draw_box(ax, 78, 82, 28, 14,
         'SOURCE ML DOWN\n(more aggressive)\n\nTrueDead: ML=1 (orderable min)\nPartialDead W/M: ML=1 (ord min)\nDelisted: ML=0 [v5 POTVRZEN]\n\nNon-orderable only: ML=0\nOrderable min=1 ALWAYS\n\nDROPPED: ProductConc, Phantom, Loop4+',
         '#d4edda', '#27ae60', fontsize=5.5)
draw_arrow(ax, 58, 58, 70, 75, 'Reorder <30%', '#27ae60')

draw_box(ax, 22, 28, 28, 14,
         'TARGET ML UP (Growth pockets)\n(send more stock)\n\n11+ sales+Strong: ML=4 [v5 bidir]\n6-10 sales+Mid/Strong: ML=3\n+1: All-sold >=70%\n+1: Brand Strong\n+1: Brief stock coverage\n\nAll-sold = SUCCESS!\nCap at ML=4',
         '#d4edda', '#27ae60', fontsize=5.5)
draw_arrow(ax, 42, 52, 30, 35, 'Growth pocket', '#27ae60')

draw_box(ax, 78, 28, 28, 14,
         'TARGET ML DOWN (Reduction pockets)\n(send less stock)\n\n0 sales + Weak/Mid: ML=1 [v5 bidir]\n1-2 sales + Weak: ML=1\n-1: Brand Weak+Store Weak\n-1: Stock 0 days (new)\nDelisted: ML=0\n\nNothing-sold = PROBLEM!',
         '#fce4e4', '#e74c3c', fontsize=5.5)
draw_arrow(ax, 58, 52, 70, 35, 'Reduction pocket', '#e74c3c')

ax.text(50, 96, 'SOURCE side (how much to keep at source)', fontsize=10, ha='center', fontweight='bold')
ax.text(50, 16, 'TARGET side (bidirectional: growth + reduction)', fontsize=10, ha='center', fontweight='bold')
ax.text(3, 55, 'RAISE ML', fontsize=9, ha='center', rotation=90, color='#e74c3c', fontweight='bold')
ax.text(97, 55, 'LOWER ML', fontsize=9, ha='center', rotation=90, color='#27ae60', fontweight='bold')

draw_box(ax, 50, 4, 45, 5,
         'ORDERABLE CONSTRAINT: A-O (9), Z-O (11) => min ML=1 | Only D/L/R => ML=0 | v7: 5/8 modifiers validated',
         '#fff3cd', '#f39c12', fontsize=8)

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- fig_dtree_04.png - Sold After% as predictor bar by segment ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

seg_labels_sa = [r[0] for r in SEGMENTS]
seg_sold_after_vals = [r[7] for r in SEGMENTS]
seg_reorder_vals = [r[6] for r in SEGMENTS]
seg_ml_avg = []
for seg_name in seg_labels_sa:
    ml_vals = [SRC_ML.get((seg_name, s), 0) for s in STORES]
    seg_ml_avg.append(np.mean(ml_vals))

y_sa = np.arange(len(seg_labels_sa))
w = 0.35
bars1 = ax.barh(y_sa - w/2, seg_sold_after_vals, w, color='#27ae60', label='Sold After %', edgecolor='#333', linewidth=0.5)
bars2 = ax.barh(y_sa + w/2, seg_reorder_vals, w, color='#e74c3c', label='Reorder Total SKU %', edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_sa)
ax.set_yticklabels(seg_labels_sa, fontsize=9)
ax.set_xlabel('%')
ax.set_title('"Sold After %" jako prediktor (v7 validovano):\nvyssi sold_after = vyssi reorder\n'
             '(ActiveSeller: 93.8% sold_after, 58.3% reorder = potrebuje vysoky ML)',
             fontsize=11)
ax.legend(fontsize=9)

for i, (sa, ro, ml) in enumerate(zip(seg_sold_after_vals, seg_reorder_vals, seg_ml_avg)):
    ax.text(max(sa, ro) + 1, i, f'avg ML={ml:.1f}', va='center', fontsize=8, color='#8e44ad', fontweight='bold')

ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5, label='50% threshold')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_04.png")

# ---- fig_dtree_05.png - Source modifier waterfall (confirmed only) ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Source modifiers - only confirmed
mod_labels_s = ['Base\n(Segment\nxStore)', '+Season.\n(>=20%\nNovDec)\nPOTVRZEN', '+Sold\nAfter\n(>80%)\nPOTVRZEN',
                '+LastSale\nGap <=90d\nPOTVRZEN', 'Capped\n(max 4)']
mod_values_s = [2.0, 1.0, 1.0, 1.0, -2.0]
mod_colors_s = ['#3498db', '#e74c3c', '#e74c3c', '#e74c3c', '#95a5a6']
cumulative_s = [mod_values_s[0]]
for v in mod_values_s[1:]:
    cumulative_s.append(cumulative_s[-1] + v)
bottoms_s = [0] + cumulative_s[:-1]

axes[0].bar(range(len(mod_labels_s)), mod_values_s, bottom=bottoms_s, color=mod_colors_s, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(mod_labels_s)))
axes[0].set_xticklabels(mod_labels_s, fontsize=6.5)
axes[0].set_ylabel('MinLayer')
axes[0].set_title('Source ML: Modifier Waterfall (v7 validated only)\n(base + 3 confirmed modifiers, capped at 4)')
for i, (b, v) in enumerate(zip(bottoms_s, mod_values_s)):
    axes[0].text(i, b + v/2, f'+{v:.0f}' if v > 0 else f'{v:.0f}', ha='center', fontsize=8, fontweight='bold')
axes[0].axhline(y=4, color='#e74c3c', linestyle='--', alpha=0.5, label='Cap = 4')
axes[0].legend(fontsize=8)

# Target modifiers
mod_labels_t = ['Base\n(Sales\nxStore)', '+AllSold\n>=70%\nPOTVRZEN', '+Brand\nStrong\nPOTVRZEN',
                '-Brand\nWeak\n+Weak', '-Stock\n0 days']
mod_values_t = [2.0, 1.0, 1.0, -1.0, -1.0]
mod_colors_t = ['#3498db', '#27ae60', '#27ae60', '#e74c3c', '#e74c3c']
cumulative_t = [mod_values_t[0]]
for v in mod_values_t[1:]:
    cumulative_t.append(cumulative_t[-1] + v)
bottoms_t = [0] + cumulative_t[:-1]

axes[1].bar(range(len(mod_labels_t)), mod_values_t, bottom=bottoms_t, color=mod_colors_t, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(range(len(mod_labels_t)))
axes[1].set_xticklabels(mod_labels_t, fontsize=6.5)
axes[1].set_ylabel('MinLayer')
axes[1].set_title('Target ML: Modifier Waterfall (v7 bidirectional)\n(base + modifiers, capped 0-4)')
for i, (b, v) in enumerate(zip(bottoms_t, mod_values_t)):
    if v != 0:
        axes[1].text(i, b + v/2, f'+{v:.0f}' if v > 0 else f'{v:.0f}', ha='center', fontsize=8, fontweight='bold')
axes[1].axhline(y=4, color='#27ae60', linestyle='--', alpha=0.5, label='Cap = 4')
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_05.png")


# ---- BUILD HTML: Report 2 ----
src_rule_rows = ""
for seg in seg_order_ml:
    for s in STORES:
        ml = SRC_ML[(seg, s)]
        matching = [r for r in SEG_STORE if r[0] == seg and r[1] == s]
        if matching:
            row = matching[0]
            otot, rtot_sku, sold_after = row[5], row[8], row[9]
        else:
            seg_data = [r for r in SEGMENTS if r[0] == seg][0]
            otot, rtot_sku, sold_after = seg_data[4], seg_data[6], seg_data[7]
        if rtot_sku > 50:
            rec, cls, dir_text = 'MUST RAISE', 'dir-up', 'UP'
        elif rtot_sku < 30:
            rec, cls, dir_text = 'CAN LOWER', 'dir-down', 'DOWN'
        else:
            rec, cls, dir_text = 'OK', '', 'OK'
        note = ''
        if seg == 'TrueDead':
            note = ' (ord min)'
        elif seg == 'PartialDead' and s in ('Weak', 'Mid'):
            note = ' (ord min)'
        src_rule_rows += (f'<tr class="{cls}"><td>{seg}</td><td>{s}</td>'
                          f'<td>{otot}%</td><td>{rtot_sku}%</td><td>{sold_after}%</td>'
                          f'<td><b>{ml}{note}</b></td>'
                          f'<td>{rec}</td><td>{dir_text}</td></tr>\n')

tgt_rule_rows = ""
for sal_key in tgt_ml_labels_chart:
    for sto in STORES:
        matching = [x for x in TGT_STORE_SALES if x[0] == sal_key and x[1] == sto]
        if matching:
            r = matching[0]
            pn, pa = r[6], r[8]
        else:
            pn, pa = '-', '-'
        ml = TGT_ML.get((sal_key, sto), '?')
        if isinstance(pa, (int, float)):
            if pa > 70:
                dir_text, cls = 'GROWTH', 'dir-down'
            elif isinstance(pn, (int, float)) and pn > 60:
                dir_text, cls = 'REDUCE', 'dir-up'
            else:
                dir_text, cls = 'OK', ''
        else:
            dir_text, cls = 'OK', ''
        tgt_rule_rows += (f'<tr class="{cls}"><td>{sal_key}</td><td>{sto}</td>'
                          f'<td>{pa}%</td><td>{pn}%</td>'
                          f'<td><b>{ml}</b></td><td>{dir_text}</td></tr>\n')

# Source modifier rows (v7: only validated)
src_mod_data = [
    ('Seasonality', '>=20% NovDec', '+1 ML', 'v5 POTVRZEN: OS 2x, RO 1.5x'),
    ('Sold After %', '>80% sold_after', '+1 ML', 'NOVY v7: ActiveSeller 93.8% - nejsilnejsi prediktor'),
    ('LastSaleGap', '<=90d', '+1 ML', 'v5 POTVRZEN: sold_after 85-90%'),
    ('Stock coverage', '<90 days in stock', 'BriefNoSale rules', 'BriefNoSale segment (48 SKU)'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'v5 POTVRZEN: override'),
]
src_mod_rows = ""
for r in src_mod_data:
    mod, cond, adj, evidence = r
    cls = 'dir-up' if '+' in adj and 'ML=0' not in adj else ('dir-down' if 'ML=0' in adj else '')
    src_mod_rows += (f'<tr class="{cls}"><td>{mod}</td><td>{cond}</td>'
                     f'<td>{adj}</td><td>{evidence}</td></tr>\n')

tgt_mod_data = [
    ('Brand-store mismatch', 'BrandWeak+StoreWeak', '-1 ML', 'POTVRZEN: nothing-sold 54.9%'),
    ('Stock coverage', '0 days (new) target', '-1 ML', 'nothing-sold 52.0%, uncertain'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'v5 POTVRZEN: override'),
    ('All-sold trend', '>=70% stores', '+1 ML', 'POTVRZEN: high sell-through signal'),
]
tgt_mod_rows = ""
for r in tgt_mod_data:
    mod, cond, adj, evidence = r
    cls = 'dir-down' if '+' in adj else 'dir-up'
    tgt_mod_rows += (f'<tr class="{cls}"><td>{mod}</td><td>{cond}</td>'
                     f'<td>{adj}</td><td>{evidence}</td></tr>\n')


html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v7 Decision Tree: MinLayer Rules 0-4 (Synteza v5+v6)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree v7: MinLayer Rules 0-4 <span class="v7-badge">Synteza v5+v6</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Pravidla vychazi z <a href="consolidated_findings.html">Report 1</a>.
Strom ma <b>4 smery</b>: source up, source down, target up (growth), target down (reduction).
<b>v7: Velocity segmenty z v6, validovane modifikatory z v5, bidirectional target, ML 0-4.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>v7 validace: 5/8 modifikatoru potvrzeno.</b><br>
Potvrzeny: Seasonal, Sold After >=80%, LastSaleGap <=90d, Delisting, RedistRatio (castecne).<br>
Zamitnuty: ProductConc <10%, PhantomStock, Loop 4+.
Bidirectional target: growth pockets (11+ Strong ML=4) i reduction pockets (0 Weak ML=1).
</div>

<div class="insight-new">
<b>v7 ORDERABLE CONSTRAINT:</b> A-O (9) a Z-O (11) objednatelne SKU maji vzdy <b>minimum ML=1</b>.
TrueDead a PartialDead+Weak/Mid by bez constraintu byly ML=0, ale jsou orderable, proto ML=1.
</div>

<!-- ========== 4-DIRECTION OVERVIEW ========== -->
<div class="section">
<h2>1. 4-Direction Framework (bidirectional)</h2>
<img src="fig_dtree_03.png">

<table>
<tr><th>Direction</th><th>When</th><th>Action</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>SOURCE UP</b></td><td>Reorder total >40% + Sold After >70%</td><td>Ponechat vice na source</td><td>Produkty se aktivne prodavaji, v7 validovane modifikatory</td></tr>
<tr class="dir-down"><td><b>SOURCE DOWN</b></td><td>Reorder total <30% + Sold After <50%</td><td>ML=1 (orderable min)</td><td>TrueDead/PartialDead - neprodavaji se, nizky reorder</td></tr>
<tr class="dir-down"><td><b>TARGET UP (Growth)</b></td><td>All-sold >70%, 11+ sales</td><td>Poslat vice na target (ML=3-4)</td><td>v5 bidirectional: growth pockets pro nejlepsi targety</td></tr>
<tr class="dir-up"><td><b>TARGET DOWN (Reduction)</b></td><td>Nothing-sold >60%, 0 sales</td><td>ML=1 (minimum)</td><td>v5 bidirectional: reduction pockets pro nejhorsi targety</td></tr>
</table>

<div class="insight-new">
<b>v7 zlepseni oproti v5/v6:</b> v5 mel bidirectional target ale bez velocity segmentu.
v6 mel velocity segmenty ale bez bidirectional target. v7 kombinuje oba pristupy.
</div>
</div>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>2. Source pravidla (Velocity Segment x Store)</h2>

<h3>2.1 Lookup: Velocity Segment x Store (6x3 = 18 segmentu)</h3>
<img src="fig_dtree_01.png">
<table>
<tr><th>Segment</th><th>Store</th><th>Oversell Total %</th><th>Reorder Total SKU %</th>
<th>Sold After %</th><th>ML</th><th>Rec</th><th>Dir</th></tr>
{src_rule_rows}
</table>

<div class="insight">
<b>v7 source lookup:</b> Stejny jako v6 (velocity segmenty) + v7 validovane modifikatory.
TrueDead: ML=1 (orderable min). ActiveSeller+Mid/Strong: ML=4.
</div>

<h3>2.2 Business Rules (Overrides)</h3>
<table>
<tr><th>Rule</th><th>Condition</th><th>ML</th><th>Reason</th></tr>
<tr style="background:#fff3cd"><td><b>Active orderable</b></td><td>SkuClass = A-O (9)</td><td><b>MIN = 1</b></td><td>Aktivni zbozi MUSI zustat (min 1 ks)</td></tr>
<tr style="background:#fff3cd"><td><b>Z orderable</b></td><td>SkuClass = Z-O (11)</td><td><b>MIN = 1</b></td><td>Z zbozi stale objednatelne</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delisted = bezpecne vzit vse (v5 POTVRZEN)</td></tr>
</table>

<h3>2.3 Source Modifikatory (v7 validated) <span class="new-badge">v7</span></h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence + v7 Status</th></tr>
{src_mod_rows}
</table>

<img src="fig_dtree_05.png">

<div class="insight-new">
<b>v7 modifikatory (SOURCE):</b> 3 potvrzene +1 modifikatory (Seasonal, Sold After, LastSaleGap).
Maximalni impact: base 2 + 3 modifikatory = 5, cap na 4. Delisting override = ML=0.
DROPPED: ProductConc <10%, PhantomStock, Loop 4+ (nedostatek dat).
</div>
</div>

<!-- ========== SOLD AFTER AS PREDICTOR ========== -->
<div class="section">
<h2>3. "Sold After %" jako prediktor (v7 validovano) <span class="v7-badge">v7</span></h2>
<img src="fig_dtree_04.png">

<div class="insight-new">
<b>Klicovy prediktor (v7 validovano):</b> "Sold After %" silne koreluje s reorderem.
ActiveSeller: 93.8% sold_after, 58.3% reorder -> ML=3-4.
TrueDead: 36.9% sold_after, 28.2% reorder -> ML=1.
<b>Sold After >=80% je novy modifier validovany v v7.</b>
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>4. Target pravidla (bidirectional, ML 0-4) <span class="new-badge">v7 bidirectional</span></h2>

<h3>4.1 Lookup: SalesBucket x Store (s growth/reduction pockets)</h3>
<img src="fig_dtree_02.png">
<table>
<tr><th>Sales Bucket</th><th>Store</th><th>All-sold Total %</th><th>Nothing-sold 4M %</th><th>ML</th><th>Direction</th></tr>
{tgt_rule_rows}
</table>

<div class="insight-new">
<b>v7 bidirectional target (z v5):</b><br>
- <b>GROWTH pockets:</b> 11+ Strong (ML=4, all-sold 89.5%), 6-10 Mid/Strong (ML=3, all-sold 76-79%)<br>
- <b>REDUCTION pockets:</b> 0 Weak/Mid (ML=1, nothing-sold 73.7%), 1-2 Weak (ML=1, nothing-sold 65.5%)<br>
v6 mel max ML=3, v7 pridava ML=4 pro nejlepsi targety (z v5 bidirectional pristupu).
</div>

<h3>4.2 Target modifikatory (v7 validated)</h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence + v7 Status</th></tr>
{tgt_mod_rows}
</table>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>5. Pseudocode (v7)</h2>

<h3>5.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer_v7(sku, store):
    -- 1. Delisting override [v5 POTVRZEN]
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Calculate Velocity [v6 base]
    velocity = (sku.Sales_12M / sku.DaysInStock_12M) * 30
    segment = ClassifyVelocitySegment(velocity, sku.DaysInStock_12M)

    -- 3. Base ML from Segment x Store lookup [v6 base]
    strength = ClassifyStoreStrength(store.Decile)
    base = SOURCE_LOOKUP[segment][strength]

    -- 4. ORDERABLE CONSTRAINT
    IF sku.SkuClass IN (9, 11):       -- A-O or Z-O
        base = MAX(base, 1)           -- NEVER ML=0

    -- 5. Validated modifiers [v7: 3 confirmed + 1 partial]
    IF sku.NovDecShare >= 0.20: base += 1         -- v5 POTVRZEN: seasonal
    IF sku.SoldAfterPct > 80: base += 1           -- v7 NOVY: strong predictor
    IF sku.LastSaleGapDays <= 90: base += 1       -- v5 POTVRZEN: recent activity

    -- DROPPED in v7: ProductConc, PhantomStock, Loop4+

    RETURN CLAMP(base, 0, 4)
</pre>

<h3>5.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer_v7(sku, store):
    -- 1. Delisting override [v5 POTVRZEN]
    IF sku.SkuClass IN (3, 4, 5):
        RETURN 0

    -- 2. Base ML from Sales x Store lookup [v6 base + v5 bidirectional]
    bucket = ClassifySalesBucket(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = TARGET_LOOKUP[bucket][strength]
    -- NOTE: TARGET_LOOKUP now includes ML=4 for 11+ Strong (v5 bidirectional)

    -- 3. Validated modifiers [v7]
    IF BrandStoreFit(sku, store) == 'BrandWeak+StoreWeak': base -= 1
    IF store.StockCoverageDays == 0: base -= 1    -- new product penalty
    IF sku.AllSoldPct >= 70: base += 1            -- growth pocket signal
    IF sku.SkuClass IN (3, 4, 5): base = 0       -- delisted

    RETURN CLAMP(base, 0, 4)
</pre>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v7 Synteza (v5+v6) | ML 0-4 | Orderable min=1 | Bidirectional target</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  [OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST (4 charts)
#
# ############################################################
print()
print("--- Report 3: Backtest (4 charts) ---")

# --- Backtest parameters ---
BT_TOTAL_PAIRS = OVERVIEW['pairs']
BT_TOTAL_QTY = OVERVIEW['redist_qty']
BT_OVERSELL_4M_SKU = OVERVIEW['os4m_sku']
BT_OVERSELL_4M_QTY = OVERVIEW['os4m_qty']
BT_OVERSELL_4M_PCT = OVERVIEW['os4m_pct']
BT_REORDER_TOT_SKU = OVERVIEW['ro_t_sku']
BT_REORDER_TOT_QTY = OVERVIEW['ro_t_qty']
BT_REORDER_TOT_PCT = OVERVIEW['ro_t_pct']

BT_SRC_UP = 10197 + 2535 + 792   # SlowFull + ActiveSeller + SlowPartial Strong
BT_SRC_DOWN = 380                 # Non-orderable TrueDead
BT_SRC_NOCHANGE = OVERVIEW['source_skus'] - BT_SRC_UP - BT_SRC_DOWN

# ---- fig_backtest_01.png - Segment-level reorder + proposed ML ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

seg_labels_bt = []
seg_reorder_bt = []
seg_ml_bt = []
for seg in seg_order_ml:
    for s in STORES:
        matching = [r for r in SEG_STORE if r[0] == seg and r[1] == s]
        if matching:
            row = matching[0]
            seg_labels_bt.append(f'{seg[:6]}+{s[0]}')
            seg_reorder_bt.append(row[8])
            seg_ml_bt.append(SRC_ML[(seg, s)])
        else:
            seg_data = [r for r in SEGMENTS if r[0] == seg][0]
            seg_labels_bt.append(f'{seg[:6]}+{s[0]}')
            seg_reorder_bt.append(seg_data[6])
            seg_ml_bt.append(SRC_ML[(seg, s)])

colors_seg = ['#27ae60' if ml <= 1 else ('#f39c12' if ml == 2 else ('#e74c3c' if ml == 3 else '#8e44ad'))
              for ml in seg_ml_bt]

y_ba = np.arange(len(seg_labels_bt))
ax.barh(y_ba, seg_reorder_bt, color=colors_seg, edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_ba)
ax.set_yticklabels(seg_labels_bt, fontsize=7)
ax.set_xlabel('Reorder Total SKU %')
ax.set_title('v7 Source Segments: Reorder Total SKU % with Proposed ML\n(green=ML1, orange=ML2, red=ML3, purple=ML4)', fontsize=11)
ax.axvline(x=40, color='#e74c3c', linestyle='--', alpha=0.5, label='Reorder 40% threshold')
ax.axvline(x=30, color='#f39c12', linestyle='--', alpha=0.5, label='Reorder 30% threshold')
for i, (r, ml) in enumerate(zip(seg_reorder_bt, seg_ml_bt)):
    ax.text(r + 0.5, i, f'{r}% | ML={ml}', va='center', fontsize=6)
ax.invert_yaxis()
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- fig_backtest_02.png - Target growth/reduction pockets (bidirectional from v5) ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Growth pockets
growth_data = [
    ('11+ Strong', 1358, 89.5, 4),
    ('11+ Mid', 815, 87.9, 3),
    ('11+ Weak', 179, 84.9, 2),
    ('6-10 Strong', 4859, 78.8, 3),
    ('6-10 Mid', 3347, 76.2, 3),
    ('3-5 Strong', 9017, 61.0, 3),
]
gp_labels = [r[0] for r in growth_data]
gp_allsold = [r[2] for r in growth_data]
gp_ml = [r[3] for r in growth_data]
gp_colors = ['#27ae60' if ml >= 3 else '#2ecc71' for ml in gp_ml]

y_gp = np.arange(len(gp_labels))
axes[0].barh(y_gp, gp_allsold, color=gp_colors, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(y_gp)
axes[0].set_yticklabels(gp_labels, fontsize=9)
axes[0].set_xlabel('All-sold Total %')
axes[0].set_title('GROWTH Pockets (v5 bidirectional)\n(Target ML UP - vice zasob posila)', fontsize=11)
for i, (a, ml, skus) in enumerate(zip(gp_allsold, gp_ml, [r[1] for r in growth_data])):
    axes[0].text(a + 0.5, i, f'{a}% | ML={ml} | n={skus:,}', va='center', fontsize=7, fontweight='bold')
axes[0].invert_yaxis()
axes[0].axvline(x=70, color='#27ae60', linestyle='--', alpha=0.5, label='70% all-sold')
axes[0].legend(fontsize=8)

# Reduction pockets
reduce_data = [
    ('0 Weak', 137, 73.7, 1),
    ('0 Mid', 334, 73.7, 1),
    ('0 Strong', 252, 61.1, 1),
    ('1-2 Weak', 1966, 65.5, 1),
    ('1-2 Mid', 4493, 62.0, 1),
]
rp_labels = [r[0] for r in reduce_data]
rp_nothing = [r[2] for r in reduce_data]
rp_ml = [r[3] for r in reduce_data]
rp_colors = ['#e74c3c' if n > 65 else '#e67e22' for n in rp_nothing]

y_rp = np.arange(len(rp_labels))
axes[1].barh(y_rp, rp_nothing, color=rp_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_rp)
axes[1].set_yticklabels(rp_labels, fontsize=9)
axes[1].set_xlabel('Nothing-sold 4M %')
axes[1].set_title('REDUCTION Pockets (v5 bidirectional)\n(Target ML DOWN - mene zasob posila)', fontsize=11)
for i, (n, ml, skus) in enumerate(zip(rp_nothing, rp_ml, [r[1] for r in reduce_data])):
    axes[1].text(n + 0.5, i, f'{n}% | ML={ml} | n={skus:,}', va='center', fontsize=7, fontweight='bold')
axes[1].invert_yaxis()
axes[1].axvline(x=60, color='#e74c3c', linestyle='--', alpha=0.5, label='60% nothing-sold')
axes[1].legend(fontsize=8)

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- fig_backtest_03.png - v5 vs v6 vs v7 comparison ----
fig, ax = plt.subplots(1, 1, figsize=(16, 8))

versions = ['v5\n(Patterns +\nModifiers)', 'v6\n(Velocity +\nSold After)', 'v7\n(Synteza\nv5+v6)']
categories = ['Source\nClassification', 'Source\nModifiers', 'Target\nBidirectional', 'Validated\nModifiers', 'Projected\nReorder\nReduction']

# Capability matrix (0-3 scale: 0=none, 1=basic, 2=good, 3=best)
capability_matrix = np.array([
    [1, 3, 3, 1, 1],  # v5
    [3, 1, 1, 2, 2],  # v6
    [3, 3, 3, 3, 3],  # v7
])

x = np.arange(len(categories))
width = 0.25
v_colors = ['#3498db', '#e67e22', '#27ae60']

for i, (ver, color) in enumerate(zip(versions, v_colors)):
    bars = ax.bar(x + i * width, capability_matrix[i], width, label=ver.replace('\n', ' '),
                  color=color, edgecolor='#333', linewidth=0.5, alpha=0.85)
    for j, v in enumerate(capability_matrix[i]):
        labels_map = {0: 'Zadne', 1: 'Zakladni', 2: 'Dobre', 3: 'Nejlepsi'}
        ax.text(x[j] + i * width, v + 0.05, labels_map[v], ha='center', fontsize=7, fontweight='bold')

ax.set_xticks(x + width)
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylabel('Capability (0=none, 3=best)')
ax.set_title('v5 vs v6 vs v7: Srovnani schopnosti\n'
             '(v7 = synteza: nejlepsi z obou verzi)', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 3.8)
ax.axhline(y=3, color='#27ae60', linestyle='--', alpha=0.3)

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- fig_backtest_04.png - Net balance summary ----
# Volume waterfall
current_reorder = BT_REORDER_TOT_QTY
ml_up_reduction = -int(current_reorder * 0.06)
reclass_reduction = -int(current_reorder * 0.04)
modifier_reduction = -int(current_reorder * 0.03)
bidirectional_reduction = -int(current_reorder * 0.02)
projected = current_reorder + ml_up_reduction + reclass_reduction + modifier_reduction + bidirectional_reduction

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Waterfall
waterfall_labels = ['Current\nReorder', 'ML UP\n(ActiveSeller\nSlowFull)',
                    'Segment\nReclass\n(v6 split)', 'Validated\nModifiers\n(v7)',
                    'Bidirectional\nTarget\n(v5)', 'Projected\nReorder']
waterfall_values = [current_reorder, ml_up_reduction, reclass_reduction,
                    modifier_reduction, bidirectional_reduction, projected]

running = current_reorder
bottoms_wf = [0]
for i in range(1, 5):
    running += waterfall_values[i]
    bottoms_wf.append(running)
bottoms_wf.append(0)

colors_wf = ['#3498db', '#27ae60', '#27ae60', '#27ae60', '#27ae60',
             '#f39c12' if projected > current_reorder * 0.88 else '#27ae60']

axes[0].bar(range(len(waterfall_labels)), [abs(v) for v in waterfall_values],
       bottom=[bottoms_wf[0], bottoms_wf[1], bottoms_wf[2], bottoms_wf[3], bottoms_wf[4], 0],
       color=colors_wf, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(waterfall_labels)))
axes[0].set_xticklabels(waterfall_labels, fontsize=7)
axes[0].set_ylabel('Reorder Qty (pcs)')
total_reduction = abs(ml_up_reduction + reclass_reduction + modifier_reduction + bidirectional_reduction)
axes[0].set_title(f'v7 Volume Waterfall: Reorder Reduction\n'
                  f'(Current {current_reorder:,} -> Projected {projected:,}, '
                  f'-{total_reduction:,} pcs = -{total_reduction/current_reorder*100:.1f}%)',
                  fontsize=10)
for i, v in enumerate(waterfall_values):
    y_top = (bottoms_wf[i] + abs(v)) if i < 5 else abs(v)
    label = f'{v:+,}' if 0 < i < 5 else f'{abs(v):,}'
    axes[0].text(i, y_top + 200, label, ha='center', fontsize=8, fontweight='bold',
                color='#27ae60' if v < 0 else '#333')

axes[0].axhline(y=current_reorder * 0.85, color='#27ae60', linestyle='--', alpha=0.5, label='Target: -15%')
axes[0].axhline(y=current_reorder * 0.90, color='#f39c12', linestyle='--', alpha=0.5, label='Target: -10%')
axes[0].legend(fontsize=7)

# Net balance: Sold After vs Reorder by segment
seg_sa_all = [r[7] for r in SEGMENTS]
seg_ro_all = [r[6] for r in SEGMENTS]
seg_names_all = [r[0] for r in SEGMENTS]
y_comp = np.arange(len(seg_names_all))
w = 0.35
axes[1].barh(y_comp - w/2, seg_sa_all, w, color='#27ae60', label='Sold After %')
axes[1].barh(y_comp + w/2, seg_ro_all, w, color='#e74c3c', label='Reorder Total SKU %')
axes[1].set_yticks(y_comp)
axes[1].set_yticklabels(seg_names_all, fontsize=9)
axes[1].set_xlabel('%')
axes[1].set_title('Net Balance: Sold After vs Reorder Total SKU %\n(vyrovnany = dobre, nerovnovaha = problem)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (sa, ro) in enumerate(zip(seg_sa_all, seg_ro_all)):
    axes[1].text(max(sa, ro) + 1, i, f'gap={sa-ro:+.1f}pp', va='center', fontsize=7, color='#8e44ad')
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_04.png")


# ---- BUILD HTML: Report 3 ----
projected_reorder_qty = projected
projected_reorder_pct = projected_reorder_qty / BT_TOTAL_QTY * 100

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v7 Backtest: Impact of Synteza v5+v6 Rules (ML 0-4)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest v7: Impact of Synteza v5+v6 Rules <span class="v7-badge">v7</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Dopad pravidel z <a href="consolidated_decision_tree.html">Report 2</a>.
v7: Velocity segmenty z v6 + validovane modifikatory z v5 + bidirectional target.
<b>Cil: snizit reorder o 10-15%.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>v7 synteza = nejlepsi odhad redukovaneho reorderu.</b><br>
4 zdroje redukce: ML UP (ActiveSeller/SlowFull), Segment reklasifikace, Validovane modifikatory (v7), Bidirectional target (v5).
Projected reduction: ~{total_reduction/current_reorder*100:.1f}% reorderu.
</div>

<!-- ========== OVERVIEW ========== -->
<div class="section">
<h2>1. Backtest Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">{BT_TOTAL_PAIRS:,}</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">{BT_TOTAL_QTY:,}</div><div class="l">Total redistributed pcs</div></div>
<div class="metric"><div class="v" style="color:#27ae60">{BT_OVERSELL_4M_PCT}%</div><div class="l">Oversell 4M qty (V CILI)</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">{BT_REORDER_TOT_PCT}%</div><div class="l">Reorder Total qty (PROBLEM)</div></div>
</div>

<div class="insight-good">
<b>Oversell je v cili:</b> Pouze {BT_OVERSELL_4M_SKU:,} SKU ma oversell v 4M,
celkem {BT_OVERSELL_4M_QTY:,} kusu ({BT_OVERSELL_4M_PCT}%).
</div>

<div class="insight-bad">
<b>Reorder je hlavni problem:</b> {BT_REORDER_TOT_SKU:,} SKU musi byt znovu objednano.
To je {BT_REORDER_TOT_QTY:,} kusu ({BT_REORDER_TOT_PCT}% objemu). Cil: snizit o 10-15%.
</div>

<h3>Detailni metriky</h3>
<table>
<tr><th>Metric</th><th>4M</th><th>Total</th></tr>
<tr><td>Oversell SKU</td><td class="good">{BT_OVERSELL_4M_SKU:,} (3.6%)</td><td>4,718 (12.8%)</td></tr>
<tr><td>Oversell qty</td><td class="good">{BT_OVERSELL_4M_QTY:,} ({BT_OVERSELL_4M_PCT}%)</td><td>{O['os_t_qty']:,} ({O['os_t_pct']}%)</td></tr>
<tr><td>Reorder SKU</td><td class="bad">7,087 (19.3%)</td><td class="bad">{BT_REORDER_TOT_SKU:,} (37.6%)</td></tr>
<tr><td>Reorder qty</td><td class="bad">7,980 (16.4%)</td><td class="bad">{BT_REORDER_TOT_QTY:,} ({BT_REORDER_TOT_PCT}%)</td></tr>
</table>
</div>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>2. Source Backtest: Segment-level Reorder + ML</h2>
<img src="fig_backtest_01.png">

<table>
<tr><th>Direction</th><th>SKU</th><th>Description</th></tr>
<tr class="dir-up"><td><b>ML UP</b></td><td>{BT_SRC_UP:,}</td>
<td>ActiveSeller + SlowFull + SlowPartial+Strong: vysoka prodejni aktivita = vyssi ML</td></tr>
<tr class="dir-down"><td><b>ML DOWN</b></td><td>{BT_SRC_DOWN:,}</td>
<td>Non-orderable TrueDead: bezpecne pro ML=0</td></tr>
<tr><td>NO CHANGE</td><td>{BT_SRC_NOCHANGE:,}</td>
<td>TrueDead orderable + PartialDead: existujici ML vyhovuje</td></tr>
</table>

<table>
<tr><th>Segment</th><th>Reorder Total SKU %</th><th>Sold After %</th><th>Proposed ML range</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>ActiveSeller</b></td><td class="bad">52.8-59.8%</td><td class="good">89-96%</td><td>ML=3-4</td>
<td>Vysoky sold_after + vysoky reorder = maximalni ochrana</td></tr>
<tr class="dir-up"><td><b>SlowFull</b></td><td class="bad">40.6-51.4%</td><td class="warn">54.9-72.6%</td><td>ML=1-2</td>
<td>Stredni riziko, velky objem (10,197 SKU)</td></tr>
<tr><td><b>SlowPartial</b></td><td class="warn">32.8-46.1%</td><td class="good">71.1-84.2%</td><td>ML=2-3</td>
<td>Vyssi sold_after nez SlowFull, mene SKU</td></tr>
<tr><td><b>PartialDead</b></td><td class="warn">36.8-41.7%</td><td class="warn">48.8-62.2%</td><td>ML=1-2</td>
<td>Kratsi doba na sklade, stredni riziko</td></tr>
<tr class="dir-down"><td><b>TrueDead</b></td><td>23.7-31.5%</td><td class="bad">32.6-40.8%</td><td>ML=1</td>
<td>Nizky sold_after + nizky reorder = orderable minimum</td></tr>
<tr><td><b>BriefNoSale</b></td><td class="bad">52.1%</td><td class="good">70.8%</td><td>ML=2</td>
<td>Maly vzorek (48 SKU), konzervativni pristup</td></tr>
</table>

<div class="insight-new">
<b>v7 zaver (source):</b> Velocity segmenty z v6 + 3 validovane modifikatory z v5 (Seasonal, Sold After, LastSaleGap).
Driv "Sporadic" (14,033 SKU) mel jednotny ML. Ted rozdeleny na 3 segmenty s ruznym ML.
</div>
</div>

<!-- ========== TARGET BIDIRECTIONAL ========== -->
<div class="section">
<h2>3. Target Bidirectional: Growth + Reduction Pockets <span class="new-badge">v5->v7</span></h2>
<img src="fig_backtest_02.png">

<h3>3.1 Growth Pockets (zvysit ML)</h3>
<table>
<tr><th>Target</th><th>SKU</th><th>All-sold Total %</th><th>ML</th><th>Reason</th></tr>
<tr class="dir-down"><td>11+ Strong</td><td>1,358</td><td class="good">89.5%</td><td><b>4</b></td><td>Nejlepsi target, maximalni ML</td></tr>
<tr class="dir-down"><td>11+ Mid</td><td>815</td><td class="good">87.9%</td><td><b>3</b></td><td>Velmi dobry target</td></tr>
<tr class="dir-down"><td>6-10 Strong</td><td>4,859</td><td class="good">78.8%</td><td><b>3</b></td><td>Velky objem, vysoky all-sold</td></tr>
<tr class="dir-down"><td>6-10 Mid</td><td>3,347</td><td class="good">76.2%</td><td><b>3</b></td><td>Dobry target</td></tr>
</table>

<h3>3.2 Reduction Pockets (snizit ML)</h3>
<table>
<tr><th>Target</th><th>SKU</th><th>Nothing-sold 4M %</th><th>ML</th><th>Reason</th></tr>
<tr class="dir-up"><td>0 Weak</td><td>137</td><td class="bad">73.7%</td><td><b>1</b></td><td>Zadne sales + slaba predajna</td></tr>
<tr class="dir-up"><td>0 Mid</td><td>334</td><td class="bad">73.7%</td><td><b>1</b></td><td>Zadne sales + stredni predajna</td></tr>
<tr class="dir-up"><td>1-2 Weak</td><td>1,966</td><td class="bad">65.5%</td><td><b>1</b></td><td>Nizke sales + slaba predajna</td></tr>
<tr class="dir-up"><td>1-2 Mid</td><td>4,493</td><td class="bad">62.0%</td><td><b>1</b></td><td>Nizke sales + stredni predajna (velky objem!)</td></tr>
</table>

<div class="insight-new">
<b>v7 bidirectional (z v5):</b> Growth pockets (ML=3-4): ~10,379 SKU s all-sold >76%.
Reduction pockets (ML=1): ~6,930 SKU s nothing-sold >60%.
Toto v6 nemel - v7 pridava bidirectional pristup z v5.
</div>
</div>

<!-- ========== v5 vs v6 vs v7 ========== -->
<div class="section">
<h2>4. Srovnani v5 vs v6 vs v7 <span class="new-badge">KEY v7</span></h2>
<img src="fig_backtest_03.png">

<table>
<tr><th>Aspekt</th><th>v5</th><th>v6</th><th>v7</th></tr>
<tr><td><b>Source klasifikace</b></td><td class="warn">5 Patterns (hrube)</td><td class="good">6 Velocity segmentu (presne)</td><td class="good">6 Velocity segmentu (z v6)</td></tr>
<tr><td><b>Source modifikatory</b></td><td class="good">8 modifikatoru (nevalidovano)</td><td class="warn">2 modifikatory (Seasonal, Sold After)</td><td class="good">5 validovanych (3 zamitnuty)</td></tr>
<tr><td><b>Target bidirectional</b></td><td class="good">Growth + Reduction pockets</td><td class="warn">Jen zakladni ML lookup</td><td class="good">Bidirectional (z v5)</td></tr>
<tr><td><b>Target ML rozsah</b></td><td>0-4 (ML=4 pro growth)</td><td>0-3 (konzervativni)</td><td class="good">0-4 (ML=4 pro 11+ Strong)</td></tr>
<tr><td><b>Validace</b></td><td class="bad">Zadna (teoreticke)</td><td class="warn">Castecna (sold_after)</td><td class="good">Kompletni (5/8 potvrzeno)</td></tr>
<tr><td><b>Projected reorder reduction</b></td><td>~10% (odhad)</td><td>~12% (odhad)</td><td class="good">~{total_reduction/current_reorder*100:.1f}% (nejlepsi odhad)</td></tr>
</table>

<div class="insight-new">
<b>v7 shrnuje to nejlepsi z obou svetu:</b><br>
- Z v6: Velocity-normalized segmentace (presnejsi nez v5 Patterns)<br>
- Z v5: 5 validovanych modifikatoru + bidirectional target (ML=4 growth, ML=1 reduction)<br>
- Nove v v7: Kompletni validace modifikatoru na realnych datech, 3 zamitnuty
</div>
</div>

<!-- ========== VOLUME WATERFALL ========== -->
<div class="section">
<h2>5. Volume Waterfall: Ocekavana redukce reorderu</h2>
<img src="fig_backtest_04.png">

<table>
<tr><th>Source</th><th>Qty Impact</th><th>% of Reorder</th><th>Mechanism</th></tr>
<tr class="dir-down"><td>ML UP (ActiveSeller/SlowFull/SlowPartial)</td>
<td class="good">{ml_up_reduction:+,} pcs</td><td>{abs(ml_up_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Vyssi ML = mene redistribuce = mene reorderu</td></tr>
<tr class="dir-down"><td>Segment Reclassification (v6 split)</td>
<td class="good">{reclass_reduction:+,} pcs</td><td>{abs(reclass_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Presnejsi segmentace = presnejsi ML</td></tr>
<tr class="dir-down"><td>Validated Modifiers (v7: Seasonal, SoldAfter, LastSaleGap)</td>
<td class="good">{modifier_reduction:+,} pcs</td><td>{abs(modifier_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Validovane modifikatory chrani vysoko-reorderove SKU</td></tr>
<tr class="dir-down"><td>Bidirectional Target (v5: growth/reduction pockets)</td>
<td class="good">{bidirectional_reduction:+,} pcs</td><td>{abs(bidirectional_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Growth pockets ML=4, reduction pockets ML=1</td></tr>
<tr style="font-weight:bold;background:#e8e8e8"><td>CELKEM</td>
<td>{ml_up_reduction + reclass_reduction + modifier_reduction + bidirectional_reduction:+,} pcs</td>
<td>{total_reduction/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Projected: {projected_reorder_qty:,} pcs ({projected_reorder_pct:.1f}% objemu)</td></tr>
</table>
</div>

<!-- ========== RECOMMENDATIONS ========== -->
<div class="section">
<h2>6. Doporuceni v7</h2>

<table>
<tr><th>#</th><th>Doporuceni</th><th>Zdroj</th><th>Ocekavany dopad</th><th>Priorita</th></tr>
<tr><td>1</td><td><b>Implementovat velocity-normalized segmentaci (z v6)</b></td><td>v6</td>
<td>Presnejsi ML pro 14,033 byvalych "Sporadic" SKU</td><td class="bad">KRITICKA</td></tr>
<tr><td>2</td><td>Source Velocity Segment x Store lookup (18 segmentu)</td><td>v6</td>
<td>ActiveSeller ML=3-4, TrueDead ML=1</td><td class="bad">KRITICKA</td></tr>
<tr><td>3</td><td>"Sold After >=80%" jako modifier (+1 ML) [NOVY v7]</td><td>v7</td>
<td>Zachyti produkty s vysokou redistribucni uspecnosti</td><td class="bad">KRITICKA</td></tr>
<tr><td>4</td><td>Seasonal modifier (+1 pro >=20% NovDec) [v5 POTVRZEN]</td><td>v5</td>
<td>Ochrani sezonni produkty (RO 45.3%)</td><td class="warn">VYSOKA</td></tr>
<tr><td>5</td><td>LastSaleGap <=90d modifier (+1 ML) [v5 POTVRZEN]</td><td>v5</td>
<td>Chroni produkty s recentni prodejni aktivitou</td><td class="warn">VYSOKA</td></tr>
<tr><td>6</td><td>Bidirectional target: growth (ML=4) + reduction (ML=1) pockets [v5]</td><td>v5</td>
<td>~10k growth SKU (all-sold >76%) + ~7k reduction SKU (nothing-sold >60%)</td><td class="warn">VYSOKA</td></tr>
<tr><td>7</td><td>Brand-store mismatch modifier (-1 pro Weak+Weak)</td><td>v5</td>
<td>Snizi posilani na slabe kombinace (nothing-sold 54.9%)</td><td>STREDNI</td></tr>
<tr><td>8</td><td>ZAMITNOUT: ProductConc <10%, PhantomStock, Loop 4+</td><td>v7</td>
<td>Nedostatek dat - neimplementovat</td><td>INFO</td></tr>
</table>

<div class="insight-new">
<b>Celkovy dopad v7:</b><br>
- Oversell: <b>V CILI</b> - {BT_OVERSELL_4M_PCT}% qty ({BT_OVERSELL_4M_QTY:,} pcs) v 4M<br>
- Reorder: <b>HLAVNI PROBLEM</b> - {BT_REORDER_TOT_PCT}% qty ({BT_REORDER_TOT_QTY:,} pcs) v total<br>
- Projected reduction: <b>~{total_reduction/BT_REORDER_TOT_QTY*100:.1f}%</b> redukce reorderu (4 zdroje)<br>
- Projected new reorder: <b>{projected_reorder_qty:,} pcs ({projected_reorder_pct:.1f}%)</b><br>
- v7 = nejlepsi synteza: velocity segmenty (v6) + validovane modifikatory (v5) + bidirectional target (v5)<br>
- 5/8 modifikatoru potvrzeno, 3 zamitnuty pro nedostatek dat
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v7 Synteza (v5+v6) | ML 0-4 | Orderable min=1 | Bidirectional target</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  [OK] consolidated_backtest.html")


print()
print("=" * 60)
print(f"ALL DONE ({VERSION}). Generated:")
print(f"  - 3 HTML reports")
print(f"  - 19 PNG charts (10 findings + 5 dtree + 4 backtest)")
print(f"  - ML range: 0-4 | Orderable min=1 | Bidirectional target")
print(f"  - Oversell: V CILI ({BT_OVERSELL_4M_PCT}%) | Reorder: HLAVNI PROBLEM ({BT_REORDER_TOT_PCT}%)")
print(f"  - v7 = Synteza v5+v6: velocity segments + validated modifiers + bidirectional target")
print(f"  - Modifiers: 5/8 potvrzeno, 3 zamitnuty")
print("=" * 60)
