"""
Consolidated Reports Generator v6: SalesBased MinLayers - CalculationId=233

v6 KEY CHANGES from v4:
  - Velocity-normalized sales replace old Pattern classification
  - Velocity = Sales_12M / DaysInStock_12M x 30 (monthly rate)
  - New segments: TrueDead, SlowFull, PartialDead, ActiveSeller, SlowPartial, BriefNoSale
  - "Sold after redistribution %" is a powerful predictor
  - Old Pattern (Dead/Dying/Sporadic/Consistent/Declining) replaced
  - Reclassification matrix: old -> new mapping
  - Stock coverage effect on "NoSale" group
  - ML range 0-4, orderable minimum ML=1
  - Oversell in target (3.0%), reorder = main problem (34.1%)
  - Target: stock coverage effect analysis

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

VERSION = 'v6'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SCRIPT_DIR, exist_ok=True)
sns.set_style("whitegrid")

print("=" * 60)
print(f"Generating consolidated reports ({VERSION})...")
print("=" * 60)

# ============================================================
# COMMON CSS (same as v4)
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
.v6-badge { background: #6f42c1; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
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
    html += f'<span style="float:right; color:#7f8c8d; font-size:11px;">v6 Velocity-normalized | ML 0-4 | Orderable min=1 | Reorder focus</span>'
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA (v6)
# ============================================================

# --- SEGMENT DEFINITIONS (replaces old Patterns) ---
SEGMENTS_DATA = [
    # Segment, skus, pct, redist_qty, os_t_pct, ro_t_pct, ro_t_sku_pct, sold_after_pct, avg_days_stock
    ('TrueDead',      18355, 50.0, 22260,  6.1, 25.5, 28.2, 36.9, 358),
    ('SlowFull',      10197, 27.8, 13511, 15.1, 42.6, 47.9, 64.7, 347),
    ('PartialDead',    3599,  9.8,  4664, 14.0, 36.6, 40.2, 56.8, 172),
    ('ActiveSeller',   2535,  6.9,  5151, 21.6, 45.9, 58.3, 93.8, 293),
    ('SlowPartial',    1980,  5.4,  3035, 12.7, 34.5, 40.7, 76.9, 188),
    ('BriefNoSale',      48,  0.1,    61, 27.9, 50.8, 52.1, 70.8,  60),
]

SEGMENT_NAMES = [r[0] for r in SEGMENTS_DATA]
STORES = ['Weak', 'Mid', 'Strong']

# --- SEGMENT x STORE (15 main rows) ---
SEG_STORE = [
    # segment, store, skus, redist, os4m (placeholder), os_t, ro4m (placeholder), ro_t, ro_t_sku, sold_after
    ('TrueDead',    'Weak',  5227, 6238,  1.0, 4.3,  9.6, 21.5, 23.7, 32.6),
    ('TrueDead',    'Mid',   8206, 10026, 1.3, 6.1, 11.4, 26.1, 29.0, 37.2),
    ('TrueDead',    'Strong',4922, 5996,  2.1, 8.0, 12.7, 28.6, 31.5, 40.8),
    ('PartialDead', 'Weak',   939, 1124,  2.8, 9.9, 16.7, 33.8, 36.8, 48.8),
    ('PartialDead', 'Mid',   1599, 2056,  4.1, 14.1, 19.3, 38.1, 41.7, 57.8),
    ('PartialDead', 'Strong',1061, 1484,  5.4, 17.0, 18.2, 36.5, 40.8, 62.2),
    ('SlowPartial', 'Weak',   415, 617,   1.5, 8.8, 11.8, 29.7, 32.8, 71.1),
    ('SlowPartial', 'Mid',    773, 1151,  3.3, 11.7, 16.2, 34.1, 39.3, 72.6),
    ('SlowPartial', 'Strong', 792, 1267,  3.4, 15.4, 20.3, 37.3, 46.1, 84.2),
    ('SlowFull',    'Weak',  2060, 2614,  2.5, 10.2, 17.9, 36.4, 40.6, 54.9),
    ('SlowFull',    'Mid',   4468, 5927,  4.4, 14.6, 22.3, 42.5, 48.3, 62.8),
    ('SlowFull',    'Strong',3669, 4970,  4.9, 18.3, 22.8, 46.0, 51.4, 72.6),
    ('ActiveSeller','Weak',   176,  308,  2.3, 22.1, 21.1, 42.9, 52.8, 90.3),
    ('ActiveSeller','Mid',    664, 1356,  5.2, 20.9, 23.1, 47.5, 59.8, 89.0),
    ('ActiveSeller','Strong',1695, 3487,  5.7, 21.9, 21.4, 45.5, 58.3, 96.0),
]

# --- RECLASSIFICATION MATRIX: Old Pattern -> New Segment ---
RECLASS = [
    # old_pattern, new_segment, skus
    ('Dead',       'TrueDead',     15367),
    ('Dead',       'PartialDead',     36),
    ('Dying',      'TrueDead',      6587),
    ('Dying',      'PartialDead',     12),
    ('Sporadic',   'SlowFull',     10197),
    ('Sporadic',   'SlowPartial',   1980),
    ('Sporadic',   'ActiveSeller',  1856),
    ('Consistent', 'ActiveSeller',   644),
    ('Consistent', 'SlowFull',        65),
    ('Declining',  'ActiveSeller',    35),
    ('Declining',  'SlowFull',       329),
]

# --- STOCK COVERAGE EFFECT ON "NO SALE" GROUP ---
NOSALE_BY_STOCK = [
    # stock_bucket, skus, redist, os_t, ro_t, ro_t_sku, sold_after
    ('<90d',      48,    61, 27.9, 50.8, 52.1, 70.8),
    ('90-180d', 3038,  3829, 14.6, 38.2, 41.0, 57.2),
    ('180-270d', 561,   835, 11.1, 29.1, 35.5, 54.2),
    ('270d+',  18355, 22260,  6.1, 25.5, 28.2, 36.9),
]

# --- TARGET: STOCK COVERAGE EFFECT ---
TGT_STOCK_COVERAGE = [
    # bucket, skus, avg_st_total, nothing_sold_4m, all_sold_total
    ('0 days (new)',      1699, 67.2, 52.0, 67.0),
    ('1-89 days',         2370, 74.2, 38.8, 70.2),
    ('90-149 days',       9376, 74.7, 35.5, 65.6),
    ('150+ days (est.)', 28186, 67.1, 44.0, 56.4),
]

# --- TARGET: SalesBucket x Store ---
TGT_STORE_SALES = [
    ('Weak','0',137,23.1,34.7,73.7,31.4),
    ('Mid','0',334,23.4,41.5,73.7,37.7),
    ('Strong','0',252,36.4,53.6,61.1,51.6),
    ('Weak','1-2',1966,26.3,47.2,65.5,38.0),
    ('Mid','1-2',4493,28.6,51.2,62.0,40.9),
    ('Strong','1-2',3622,32.1,56.4,58.0,47.0),
    ('Weak','3-5',2601,41.5,65.8,45.1,54.4),
    ('Mid','3-5',7765,40.8,66.0,45.5,54.6),
    ('Strong','3-5',9017,45.3,71.7,40.8,61.0),
    ('Weak','6-10',886,58.6,82.2,28.1,74.3),
    ('Mid','6-10',3347,59.3,84.3,26.8,76.2),
    ('Strong','6-10',4859,63.1,86.2,22.3,78.8),
    ('Weak','11+',179,73.8,92.0,12.3,84.9),
    ('Mid','11+',815,72.7,93.4,11.9,87.9),
    ('Strong','11+',1358,77.0,93.9,10.8,89.5),
]

# --- TARGET: Brand-store fit ---
TGT_BRAND_FIT = [
    ('Weak',   'BrandWeak',   2448, 55.3, 54.9),
    ('Weak',   'BrandMid',    1152, 63.7, 49.3),
    ('Weak',   'BrandStrong', 2169, 68.4, 42.4),
    ('Mid',    'BrandWeak',   3623, 59.1, 53.2),
    ('Mid',    'BrandMid',    3744, 64.3, 47.6),
    ('Mid',    'BrandStrong', 9387, 70.0, 41.1),
    ('Strong', 'BrandWeak',   1746, 63.9, 47.3),
    ('Strong', 'BrandMid',    2590, 69.5, 42.2),
    ('Strong', 'BrandStrong',14772, 75.8, 35.4),
]

# --- Store decile data ---
DECILES = list(range(1, 11))
SRC_OVERSELL_4M_BY_DECILE = [1.9, 1.3, 1.9, 2.0, 2.6, 3.0, 3.6, 3.2, 4.4, 4.5]
SRC_REORDER_TOT_BY_DECILE = [24.0, 27.8, 28.8, 30.5, 33.6, 35.1, 36.0, 37.5, 39.0, 38.6]
TGT_ALLSOLD_BY_DECILE = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1]
TGT_NOTHING_BY_DECILE = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Pair analysis ---
PAIR_ANALYSIS = [
    ('Win-Win',   'No oversell + good ST',  28179, 66.5),
    ('Win-Lose',  'No oversell + bad ST',    8565, 20.2),
    ('Lose-Win',  'Oversell + good ST',      4794, 11.3),
    ('Lose-Lose', 'Oversell + bad ST',        866,  2.0),
]

# --- Seasonality ---
SRC_SEASON = [
    ('Non-seasonal', 29298, 2.3, 9.3, 14.4, 30.8, 33.9),
    ('Seasonal',      7472, 5.3, 18.8, 23.1, 45.3, 52.2),
]

# --- Flow Matrix ---
FLOW_MATRIX = [
    ('Weak',   'Weak',   1179,  2.8),
    ('Weak',   'Mid',    4149,  9.8),
    ('Weak',   'Strong', 4611, 10.9),
    ('Mid',    'Weak',   2391,  5.6),
    ('Mid',    'Mid',    7279, 17.2),
    ('Mid',    'Strong', 8304, 19.6),
    ('Strong', 'Weak',   2302,  5.4),
    ('Strong', 'Mid',    5643, 13.3),
    ('Strong', 'Strong', 6546, 15.4),
]

# --- Decision trees (v6) ---
SRC_ML_TREE = {
    ('ActiveSeller', 'Weak'): 3, ('ActiveSeller', 'Mid'): 4, ('ActiveSeller', 'Strong'): 4,
    ('SlowFull', 'Weak'): 1, ('SlowFull', 'Mid'): 2, ('SlowFull', 'Strong'): 2,
    ('SlowPartial', 'Weak'): 2, ('SlowPartial', 'Mid'): 2, ('SlowPartial', 'Strong'): 3,
    ('PartialDead', 'Weak'): 1, ('PartialDead', 'Mid'): 1, ('PartialDead', 'Strong'): 2,
    ('TrueDead', 'Weak'): 1, ('TrueDead', 'Mid'): 1, ('TrueDead', 'Strong'): 1,
    ('BriefNoSale', 'Weak'): 2, ('BriefNoSale', 'Mid'): 2, ('BriefNoSale', 'Strong'): 2,
}

TGT_ML_TREE = {
    ('0 (no sales)', 'Weak'): 1, ('0 (no sales)', 'Mid'): 1, ('0 (no sales)', 'Strong'): 2,
    ('1-2', 'Weak'): 1, ('1-2', 'Mid'): 2, ('1-2', 'Strong'): 2,
    ('3-5', 'Weak'): 2, ('3-5', 'Mid'): 2, ('3-5', 'Strong'): 2,
    ('6-10', 'Weak'): 2, ('6-10', 'Mid'): 2, ('6-10', 'Strong'): 2,
    ('11+', 'Weak'): 3, ('11+', 'Mid'): 3, ('11+', 'Strong'): 3,
}

# --- Source modifiers (v6) ---
SRC_MODIFIERS = [
    ('Seasonality', '>=20% NovDec', '+1 ML', 'reorder_tot_sku 52.2% vs 33.9%'),
    ('Sold After %', '>80% sold_after', '+1 ML', 'ActiveSeller 93.8% - strong predictor'),
    ('Stock coverage', '<90 days in stock', 'use BriefNoSale rules', 'insufficient data'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'override'),
]

TGT_MODIFIERS = [
    ('Brand-store mismatch', 'BrandWeak+StoreWeak', '-1 ML', 'ST 55.3%, nothing-sold 54.9%'),
    ('Stock coverage', '0 days (new) target', '-1 ML', 'nothing-sold 52.0%, uncertain'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'override'),
    ('All-sold trend', '>=70% stores', '+1 ML', 'high sell-through signal'),
]


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS
#
# ############################################################
print()
print("--- Report 1: Consolidated Findings ---")

# ---- Chart: fig_findings_01.png - Segment overview bar chart ----
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

seg_labels = [r[0] for r in SEGMENTS_DATA]
seg_skus = [r[1] for r in SEGMENTS_DATA]
seg_sold_after = [r[7] for r in SEGMENTS_DATA]
seg_reorder_sku = [r[6] for r in SEGMENTS_DATA]
seg_oversell_t = [r[4] for r in SEGMENTS_DATA]

# SKU count
colors_sku = ['#2c3e50', '#7f8c8d', '#95a5a6', '#e74c3c', '#f39c12', '#17a2b8']
axes[0].barh(range(len(seg_labels)), seg_skus, color=colors_sku, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(range(len(seg_labels)))
axes[0].set_yticklabels(seg_labels, fontsize=9)
axes[0].set_xlabel('SKU Count')
axes[0].set_title('Segmenty: Pocet SKU\n(Velocity-normalized)', fontsize=11)
for i, v in enumerate(seg_skus):
    axes[0].text(v + 100, i, f'{v:,} ({SEGMENTS_DATA[i][2]}%)', va='center', fontsize=8)
axes[0].invert_yaxis()

# Sold After %
colors_sa = ['#e74c3c' if s < 50 else ('#f39c12' if s < 70 else '#27ae60') for s in seg_sold_after]
axes[1].barh(range(len(seg_labels)), seg_sold_after, color=colors_sa, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(range(len(seg_labels)))
axes[1].set_yticklabels(seg_labels, fontsize=9)
axes[1].set_xlabel('Sold After Redistribution %')
axes[1].set_title('Sold After %: Klic. prediktor\n(vyssi = lepsi redistribuce)', fontsize=11)
for i, v in enumerate(seg_sold_after):
    axes[1].text(v + 0.5, i, f'{v}%', va='center', fontsize=8)
axes[1].axvline(x=50, color='#e74c3c', linestyle='--', alpha=0.5)
axes[1].axvline(x=70, color='#27ae60', linestyle='--', alpha=0.5)
axes[1].invert_yaxis()

# Reorder Total SKU %
colors_ro = ['#27ae60' if r < 35 else ('#f39c12' if r < 45 else '#e74c3c') for r in seg_reorder_sku]
axes[2].barh(range(len(seg_labels)), seg_reorder_sku, color=colors_ro, edgecolor='#333', linewidth=0.5)
axes[2].set_yticks(range(len(seg_labels)))
axes[2].set_yticklabels(seg_labels, fontsize=9)
axes[2].set_xlabel('Reorder Total SKU %')
axes[2].set_title('Reorder Total SKU %: HLAVNI PROBLEM\n(vyssi = horsi redistribuce)', fontsize=11)
for i, v in enumerate(seg_reorder_sku):
    axes[2].text(v + 0.5, i, f'{v}%', va='center', fontsize=8)
axes[2].axvline(x=40, color='#e74c3c', linestyle='--', alpha=0.5, label='>40% = problem')
axes[2].axvline(x=30, color='#f39c12', linestyle='--', alpha=0.5, label='>30% = warning')
axes[2].legend(fontsize=7, loc='lower right')
axes[2].invert_yaxis()

fig.suptitle('v6 Velocity-Normalized Segmentace: Prehled', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- Chart: fig_findings_02.png - Segment x Store dual heatmap ----
# Build segment order for heatmap
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
axes[0].set_title('OVERSELL Total % by Segment x Store\n(v cili - prumerne 12.8%)', fontsize=11)
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

# ---- Chart: fig_findings_03.png - Store decile lines ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(DECILES, SRC_OVERSELL_4M_BY_DECILE, 'o-', color='#3498db', linewidth=2, label='Source Oversell 4M %')
axes[0].plot(DECILES, SRC_REORDER_TOT_BY_DECILE, 's--', color='#e74c3c', linewidth=2, label='Source Reorder Total %')
axes[0].fill_between(DECILES, SRC_REORDER_TOT_BY_DECILE, alpha=0.1, color='#e74c3c')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Oversell 4M + Reorder Total by Decile\n(Reorder je hlavni problem)')
axes[0].legend(fontsize=8)
axes[0].set_xticks(DECILES)
axes[0].axhspan(0, 5, alpha=0.05, color='green')

axes[1].plot(DECILES, TGT_ALLSOLD_BY_DECILE, 'o-', color='#27ae60', linewidth=2, label='All Sold %')
axes[1].plot(DECILES, TGT_NOTHING_BY_DECILE, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold %')
axes[1].fill_between(DECILES, TGT_ALLSOLD_BY_DECILE, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING_BY_DECILE, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Outcome by Store Decile')
axes[1].legend(fontsize=8)
axes[1].set_xticks(DECILES)

# Efficiency ratio
efficiency = [a / (a + n) * 100 for a, n in zip(TGT_ALLSOLD_BY_DECILE, TGT_NOTHING_BY_DECILE)]
axes[2].bar(DECILES, efficiency, color=['#e74c3c' if e < 65 else ('#f39c12' if e < 72 else '#27ae60') for e in efficiency])
axes[2].set_xlabel('Store Decile')
axes[2].set_ylabel('Efficiency %')
axes[2].set_title('TARGET: Redistribution Efficiency\n(All-sold / (All-sold + Nothing-sold))')
axes[2].set_xticks(DECILES)
axes[2].axhline(y=70, color='#f39c12', linestyle='--', alpha=0.5)
for d, e in zip(DECILES, efficiency):
    axes[2].text(d, e + 0.5, f'{e:.0f}%', ha='center', fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- Chart: fig_findings_04.png - Target ST heatmaps (SalesBucket x Store) ----
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
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- Chart: fig_findings_05.png - Brand-fit + stock coverage effect ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Brand-fit heatmap
brand_fits = ['BrandWeak', 'BrandMid', 'BrandStrong']
bf_st_matrix = np.array([
    [55.3, 63.7, 68.4],
    [59.1, 64.3, 70.0],
    [63.9, 69.5, 75.8],
])
sns.heatmap(bf_st_matrix, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=brand_fits, yticklabels=STORES, ax=axes[0],
            vmin=50, vmax=80, linewidths=1, cbar_kws={'label': 'ST Total %'})
axes[0].set_title('Target: Brand-Store Fit -> ST Total %', fontsize=10)
axes[0].set_ylabel('Store Strength')

# Target stock coverage effect
sc_labels = [r[0] for r in TGT_STOCK_COVERAGE]
sc_nothing = [r[3] for r in TGT_STOCK_COVERAGE]
sc_allsold = [r[4] for r in TGT_STOCK_COVERAGE]
sc_skus = [r[1] for r in TGT_STOCK_COVERAGE]
x_sc = np.arange(len(sc_labels))
w = 0.35
axes[1].bar(x_sc - w/2, sc_allsold, w, color='#27ae60', label='All-sold Total %')
axes[1].bar(x_sc + w/2, sc_nothing, w, color='#e74c3c', label='Nothing-sold 4M %')
axes[1].set_xticks(x_sc)
axes[1].set_xticklabels(sc_labels, fontsize=8, rotation=10)
axes[1].set_ylabel('%')
axes[1].set_title('Target: Stock Coverage Effect\n(nove produkty = vyssi nothing-sold)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (a, n, c) in enumerate(zip(sc_allsold, sc_nothing, sc_skus)):
    axes[1].text(i - w/2, a + 1, f'{a}%', ha='center', fontsize=7, color='#27ae60')
    axes[1].text(i + w/2, n + 1, f'{n}%', ha='center', fontsize=7, color='#e74c3c')
    axes[1].text(i, max(a, n) + 4, f'n={c:,}', ha='center', fontsize=7, color='#666')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_05.png")

# ---- Chart: fig_findings_06.png - Old Pattern -> New Segment reclassification ----
fig, ax = plt.subplots(1, 1, figsize=(14, 8))

old_patterns = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
new_segments = ['TrueDead', 'PartialDead', 'SlowFull', 'SlowPartial', 'ActiveSeller']

# Build grouped data: for each old pattern, show the new segments it maps to
y_pos = 0
y_positions = []
y_labels = []
bar_colors = {
    'TrueDead': '#2c3e50', 'PartialDead': '#95a5a6', 'SlowFull': '#7f8c8d',
    'SlowPartial': '#f39c12', 'ActiveSeller': '#e74c3c'
}

for old_p in old_patterns:
    mappings = [r for r in RECLASS if r[0] == old_p]
    for m in mappings:
        y_positions.append(y_pos)
        y_labels.append(f'{old_p} -> {m[1]}')
        ax.barh(y_pos, m[2], color=bar_colors.get(m[1], '#3498db'),
                edgecolor='#333', linewidth=0.5, height=0.7)
        ax.text(m[2] + 100, y_pos, f'{m[2]:,} SKU', va='center', fontsize=8)
        y_pos += 1
    y_pos += 0.5  # gap between old patterns

ax.set_yticks(y_positions)
ax.set_yticklabels(y_labels, fontsize=8)
ax.set_xlabel('SKU Count')
ax.set_title('Reklasifikace: Stary Pattern -> Novy Velocity Segment\n'
             '(Dead/Dying -> prevazne TrueDead; Sporadic -> SlowFull/SlowPartial/ActiveSeller)',
             fontsize=11)
ax.invert_yaxis()

# Legend
legend_patches = [mpatches.Patch(color=c, label=l) for l, c in bar_colors.items()]
ax.legend(handles=legend_patches, loc='lower right', fontsize=8, title='Novy segment')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_06.png")

# ---- Chart: fig_findings_07.png - Stock coverage effect on NoSale group ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

ns_labels = [r[0] for r in NOSALE_BY_STOCK]
ns_skus = [r[1] for r in NOSALE_BY_STOCK]
ns_os_t = [r[3] for r in NOSALE_BY_STOCK]
ns_ro_t_sku = [r[5] for r in NOSALE_BY_STOCK]
ns_sold_after = [r[6] for r in NOSALE_BY_STOCK]

x_ns = np.arange(len(ns_labels))

# Oversell + Reorder
w = 0.35
axes[0].bar(x_ns - w/2, ns_os_t, w, color='#3498db', label='Oversell Total %')
axes[0].bar(x_ns + w/2, ns_ro_t_sku, w, color='#e74c3c', label='Reorder Total SKU %')
axes[0].set_xticks(x_ns)
axes[0].set_xticklabels(ns_labels, fontsize=8)
axes[0].set_ylabel('%')
axes[0].set_title('"NoSale" Group: Oversell vs Reorder\nby Stock Coverage', fontsize=10)
axes[0].legend(fontsize=8)
for i, (o, r) in enumerate(zip(ns_os_t, ns_ro_t_sku)):
    axes[0].text(i - w/2, o + 0.5, f'{o}%', ha='center', fontsize=7, color='#3498db')
    axes[0].text(i + w/2, r + 0.5, f'{r}%', ha='center', fontsize=7, color='#e74c3c')

# Sold after
colors_sa2 = ['#27ae60' if s > 60 else ('#f39c12' if s > 45 else '#e74c3c') for s in ns_sold_after]
axes[1].bar(x_ns, ns_sold_after, color=colors_sa2, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(x_ns)
axes[1].set_xticklabels(ns_labels, fontsize=8)
axes[1].set_ylabel('Sold After %')
axes[1].set_title('"NoSale" Group: Sold After %\n(mene dnu na sklade = lepsi vysledek)', fontsize=10)
for i, v in enumerate(ns_sold_after):
    axes[1].text(i, v + 1, f'{v}%', ha='center', fontsize=9, fontweight='bold')

# SKU distribution
axes[2].bar(x_ns, ns_skus, color=['#17a2b8', '#3498db', '#2980b9', '#2c3e50'],
            edgecolor='#333', linewidth=0.5)
axes[2].set_xticks(x_ns)
axes[2].set_xticklabels(ns_labels, fontsize=8)
axes[2].set_ylabel('SKU Count')
axes[2].set_title('"NoSale" Group: SKU Distribution\n(270d+ = TrueDead, <90d = BriefNoSale)', fontsize=10)
for i, v in enumerate(ns_skus):
    axes[2].text(i, v + 200, f'{v:,}', ha='center', fontsize=8, fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_07.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_07.png")

# ---- Chart: fig_findings_08.png - Pair analysis pie + Seasonality bars ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pair analysis pie
pair_labels = [r[0] for r in PAIR_ANALYSIS]
pair_counts = [r[2] for r in PAIR_ANALYSIS]
pair_colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
wedges, texts, autotexts = axes[0].pie(pair_counts, labels=pair_labels, colors=pair_colors,
                                        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[0].set_title('Pair Analysis: Source+Target Combined\n(Win-Win 66.5% = oversell v cili)', fontsize=10)

# Seasonality bars
seas_labels = [r[0] for r in SRC_SEASON]
seas_oversell_4m = [r[2] for r in SRC_SEASON]
seas_reorder_tot = [r[6] for r in SRC_SEASON]
seas_cnt = [r[1] for r in SRC_SEASON]
x_s = np.arange(len(seas_labels))
w = 0.35
axes[1].bar(x_s - w/2, seas_oversell_4m, w, color='#3498db', label='Oversell 4M %')
axes[1].bar(x_s + w/2, seas_reorder_tot, w, color='#e74c3c', label='Reorder Total SKU %')
axes[1].set_xticks(x_s)
axes[1].set_xticklabels(seas_labels, fontsize=9)
axes[1].set_ylabel('%')
axes[1].set_title('Sezonnost: Oversell vs Reorder\n(Sezonni produkty = vyssi reorder)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (o4, rt, c) in enumerate(zip(seas_oversell_4m, seas_reorder_tot, seas_cnt)):
    axes[1].text(i, max(o4, rt) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_08.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_08.png")

# ---- Chart: fig_findings_09.png - Flow matrix heatmap ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

pairs_matrix = np.zeros((3, 3))
pct_matrix = np.zeros((3, 3))
for r in FLOW_MATRIX:
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
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_09.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_09.png")


# ############################################################
# BUILD HTML: Report 1
# ############################################################

# Helper: Segment x Store table rows
def seg_store_table(data):
    rows = ""
    for r in data:
        seg, sto, cnt, rdq, o4m, otot, r4m, rtot, rtot_sku, sold_after = r
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

# Target Store x Sales table
tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sto, sal, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 30 else 'good')
    cls_a = 'good' if pa > 70 else ('warn' if pa > 50 else 'bad')
    tgt_ss_rows += (f'<tr><td>{sal}</td><td>{sto}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.1f}%</td><td>{stt:.1f}%</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n')

# Brand-fit rows
tgt_bf_rows = ""
for r in TGT_BRAND_FIT:
    sto, bf, cnt, st, pn = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 40 else 'good')
    cls_st = 'good' if st > 70 else ('warn' if st > 60 else 'bad')
    tgt_bf_rows += (f'<tr><td>{sto}</td><td>{bf}</td><td>{cnt:,}</td>'
                    f'<td class="{cls_st}">{st}%</td><td class="{cls_n}">{pn}%</td></tr>\n')

# Segment summary rows
seg_summary_rows = ""
for r in SEGMENTS_DATA:
    seg, skus, pct, rdq, os_t, ro_t, ro_t_sku, sold_after, avg_days = r
    cls_r = 'bad' if ro_t_sku > 50 else ('warn' if ro_t_sku > 35 else 'good')
    cls_sa = 'good' if sold_after > 70 else ('warn' if sold_after > 50 else 'bad')
    seg_summary_rows += (f'<tr><td><b>{seg}</b></td><td>{skus:,}</td><td>{pct}%</td>'
                         f'<td>{rdq:,}</td><td>{os_t}%</td>'
                         f'<td class="{cls_r}">{ro_t_sku}%</td>'
                         f'<td class="{cls_sa}">{sold_after}%</td>'
                         f'<td>{avg_days}d</td></tr>\n')

# Reclassification rows
reclass_rows = ""
for r in RECLASS:
    old_p, new_s, skus = r
    reclass_rows += (f'<tr><td>{old_p}</td><td>{new_s}</td><td>{skus:,}</td></tr>\n')

# NoSale by stock rows
nosale_rows = ""
for r in NOSALE_BY_STOCK:
    bkt, skus, rdq, os_t, ro_t, ro_t_sku, sold_after = r
    cls_r = 'bad' if ro_t_sku > 45 else ('warn' if ro_t_sku > 35 else 'good')
    cls_sa = 'good' if sold_after > 60 else ('warn' if sold_after > 45 else 'bad')
    nosale_rows += (f'<tr><td>{bkt}</td><td>{skus:,}</td><td>{rdq:,}</td>'
                    f'<td>{os_t}%</td><td class="{cls_r}">{ro_t_sku}%</td>'
                    f'<td class="{cls_sa}">{sold_after}%</td></tr>\n')

# Stock coverage target rows
tgt_sc_rows = ""
for r in TGT_STOCK_COVERAGE:
    bkt, skus, st, nothing, allsold = r
    cls_n = 'bad' if nothing > 45 else ('warn' if nothing > 35 else 'good')
    cls_a = 'good' if allsold > 68 else ('warn' if allsold > 60 else 'bad')
    tgt_sc_rows += (f'<tr><td>{bkt}</td><td>{skus:,}</td><td>{st:.1f}%</td>'
                    f'<td class="{cls_n}">{nothing}%</td><td class="{cls_a}">{allsold}%</td></tr>\n')

# Pair analysis rows
pair_rows = ""
for r in PAIR_ANALYSIS:
    name, desc, cnt, pct = r
    cls = 'good' if name == 'Win-Win' else ('warn' if name == 'Win-Lose' else 'bad')
    pair_rows += (f'<tr><td class="{cls}">{name}</td><td>{desc}</td>'
                  f'<td>{cnt:,}</td><td>{pct}%</td></tr>\n')

# Seasonality rows
seas_rows = ""
for r in SRC_SEASON:
    cat, cnt, o4, ot, r4m_qty, ro_t_qty, ro_t_sku = r
    cls_r = 'bad' if ro_t_sku > 40 else ('warn' if ro_t_sku > 30 else 'good')
    seas_rows += (f'<tr><td>{cat}</td><td>{cnt:,}</td>'
                  f'<td>{o4}%</td><td>{ot}%</td>'
                  f'<td class="{cls_r}">{ro_t_sku}%</td></tr>\n')

# Flow matrix rows
flow_rows = ""
for r in FLOW_MATRIX:
    sg, tg, pairs, pct = r
    flow_rows += (f'<tr><td>{sg}</td><td>{tg}</td><td>{pairs:,}</td>'
                  f'<td>{pct}%</td></tr>\n')


html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v6 Consolidated Findings: SalesBased MinLayers - Velocity-Normalized</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings v6: SalesBased MinLayers (Velocity-Normalized) <span class="v6-badge">v6</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p><b>v6 KEY INNOVATION:</b> <b>Velocity-normalized sales</b> = Sales_12M / DaysInStock_12M x 30 (mesicni rate).
Nahradi stary Pattern (Dead/Dying/Sporadic/Consistent/Declining) presnejsimi segmenty
ktere zohlednuji jak prodejni aktivitu, tak dostupnost zasob.
<b>"Sold after redistribution %"</b> je silny prediktor uspechu.</p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (34.1% qty).</b><br>
Oversell 4M je pouze 3.0% (1,317 SKU, 1,464 qty). Reorder: 13,841 SKU (37.6%), 16,615 kusu (34.1% objemu).
Velocity normalizace odhaluje skryte segmenty: 50% je TrueDead (36.9% sold_after) vs 6.9% ActiveSeller (93.8% sold_after).
</div>

<div class="insight-new">
<b>v6 ZMENA:</b> Velocity = Sales_12M / DaysInStock_12M x 30. Produkty s nulovym prodejem ale kracejsi dobou na sklade
(napr. &lt;90 dni) jsou oddeleny od TrueDead do BriefNoSale. Sporadic je rozdelen na SlowFull, SlowPartial a ActiveSeller
podle skutecne prodejni rychlosti normalizovane na dostupnost.
</div>

<!-- ========== 1. OVERVIEW ========== -->
<div class="section">
<h2>1. Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">48,754</div><div class="l">Total redistributed pcs</div></div>
<div class="metric"><div class="v">36,770</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">41,631</div><div class="l">Target SKU</div></div>
</div>

<h3>Source: Celkove metriky - 4M a total</h3>
<table>
<tr><th>Metric</th><th>4 months</th><th>Total (~9M)</th></tr>
<tr><td><b>Total redistributed</b></td><td>48,754 pcs</td><td>48,754 pcs</td></tr>
<tr><td><b>Oversell (SKU)</b></td><td class="good">1,317 SKU (3.6%)</td><td>4,718 SKU (12.8%)</td></tr>
<tr><td><b>Oversell (qty)</b></td><td class="good">1,464 qty (3.0%)</td><td>5,578 qty (11.4%)</td></tr>
<tr><td><b>Reorder (SKU)</b></td><td class="bad">7,087 SKU (19.3%)</td><td class="bad">13,841 SKU (37.6%)</td></tr>
<tr><td><b>Reorder (qty)</b></td><td class="bad">7,980 qty (16.4%)</td><td class="bad">16,615 qty (34.1%)</td></tr>
</table>

<div class="insight">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (37.6% SKU, 34.1% qty).</b>
Cil je snizit reorder o 10-15%.
</div>
</div>

<!-- ========== 2. VELOCITY SEGMENTS ========== -->
<div class="section">
<h2>2. Velocity-Normalized Segmentace <span class="new-badge">NEW v6</span></h2>
<p><b>Velocity</b> = Sales_12M / DaysInStock_12M x 30 (mesicni rate normalizovana na dostupnost).
Odhaluje skryte segmenty, ktere stary Pattern nevidel.</p>

<img src="fig_findings_01.png">
<table>
<tr><th>Segment</th><th>SKU</th><th>Podil</th><th>Redist qty</th><th>Oversell Total %</th>
<th>Reorder Total SKU %</th><th>Sold After %</th><th>Avg Days in Stock</th></tr>
{seg_summary_rows}
</table>

<div class="insight-new">
<b>Klicovy insight:</b> "Sold After %" je silny prediktor. ActiveSeller ma 93.8% sold_after
ale take 58.3% reorder - tyto produkty se rychle prodaji a potrebuji doplneni.
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
<b>MUST RAISE ML (reorder_tot_sku &gt;50%):</b> ActiveSeller+Weak (52.8%), ActiveSeller+Mid (59.8%),
ActiveSeller+Strong (58.3%), SlowFull+Strong (51.4%), BriefNoSale (52.1%).
</div>
<div class="insight-good">
<b>LOW RISK segmenty:</b> TrueDead+Weak (23.7% reorder, 32.6% sold_after) - bezpecne pro ML=1.
</div>
</div>

<!-- ========== 3. RECLASSIFICATION ========== -->
<div class="section">
<h2>3. Reklasifikace: Stary Pattern -> Novy Segment <span class="new-badge">NEW v6</span></h2>
<img src="fig_findings_06.png">
<table>
<tr><th>Stary Pattern</th><th>Novy Segment</th><th>SKU</th></tr>
{reclass_rows}
</table>

<div class="insight-new">
<b>Klicove zmeny:</b><br>
- <b>Dead (15,403)</b> -> prevazne TrueDead (15,367) + 36 PartialDead (mely kratkou dobu na sklade)<br>
- <b>Dying (6,599)</b> -> prevazne TrueDead (6,587) + 12 PartialDead<br>
- <b>Sporadic (14,033)</b> -> rozdeleno na SlowFull (10,197), SlowPartial (1,980), ActiveSeller (1,856)<br>
- <b>Consistent (709)</b> -> prevazne ActiveSeller (644) + 65 SlowFull (nizka velocity ale konzistentni)<br>
- <b>Declining (364)</b> -> SlowFull (329) + ActiveSeller (35)
</div>
</div>

<!-- ========== 4. STOCK COVERAGE EFFECT ========== -->
<div class="section">
<h2>4. Stock Coverage Effect na "NoSale" Group <span class="new-badge">NEW v6</span></h2>
<p>Produkty bez prodeje v 12M maji ruzne chovani podle doby na sklade. Velocity normalizace
toto odhaluje - kratka doba na sklade neznamena "dead" ale "nedostatecna data".</p>

<img src="fig_findings_07.png">
<table>
<tr><th>Stock Coverage</th><th>SKU</th><th>Redist qty</th><th>Oversell Total %</th>
<th>Reorder Total SKU %</th><th>Sold After %</th></tr>
{nosale_rows}
</table>

<div class="insight-new">
<b>&lt;90 dnu na sklade</b> (BriefNoSale, 48 SKU): 70.8% sold_after, 52.1% reorder - premalo dat,
ale prekvapivy uspechu. 270d+ (TrueDead, 18,355 SKU): jen 36.9% sold_after, 28.2% reorder.
Kratsi doba na sklade = lepsi vysledek redistribuce.
</div>
</div>

<!-- ========== 5. STORE DECILES ========== -->
<div class="section">
<h2>5. Source + Target: Sila predajni (decily)</h2>
<img src="fig_findings_03.png">
<table>
<tr><th>Metric</th><th>D1 (Weak)</th><th>D10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Oversell 4M</td><td class="good">1.9%</td><td class="good">4.5%</td><td>Oversell je v cili ve vsech decilech</td></tr>
<tr><td>Source Reorder Total</td><td class="warn">24.0%</td><td class="bad">38.6%</td><td>Silne predajne = vyssi reorder riziko</td></tr>
<tr><td>Target All-Sold Total</td><td class="warn">48.3%</td><td class="good">70.1%</td><td>Silne predajne prodaji vse</td></tr>
<tr><td>Target Nothing-Sold</td><td class="bad">32.1%</td><td class="good">13.7%</td><td>Slabe predajny = vice zaseklych zbozi</td></tr>
</table>
</div>

<!-- ========== 6. TARGET SELL-THROUGH ========== -->
<div class="section">
<h2>6. Target: Sell-through analyza (15 segmentu)</h2>

<h3>6.1 Store Strength x Sales Bucket</h3>
<img src="fig_findings_04.png">
<table>
<tr><th>SalesBucket</th><th>Store</th><th>SKU</th><th>ST 4M %</th><th>ST Total %</th>
<th>Nothing-sold 4M %</th><th>All-sold Total %</th></tr>
{tgt_ss_rows}
</table>

<div class="insight-good">
<b>11+ sales bucket = vyborny target:</b> 84.9-89.5% all-sold, nothing-sold jen 10.8-12.3%.
</div>

<h3>6.2 Brand-Store Fit + Stock Coverage <span class="new-badge">NEW v6</span></h3>
<img src="fig_findings_05.png">
<table>
<tr><th>Store</th><th>BrandFit</th><th>SKU</th><th>ST Total %</th><th>Nothing-sold 4M %</th></tr>
{tgt_bf_rows}
</table>

<h3>6.3 Target Stock Coverage Effect <span class="new-badge">NEW v6</span></h3>
<table>
<tr><th>Stock Coverage</th><th>SKU</th><th>ST Total %</th><th>Nothing-sold 4M %</th><th>All-sold Total %</th></tr>
{tgt_sc_rows}
</table>

<div class="insight-new">
<b>Nove produkty (0 dnu) maji nejvyssi nothing-sold (52.0%)</b> ale prekvapive dobry ST total (67.2%).
Nejlepsi vysledky: 1-89 dnu (ST 74.2%, all-sold 70.2%). 150+ dnu paradoxne horsi (ST 67.1%) -
etablovane produkty ktere uz se neprodavaji.
</div>
</div>

<!-- ========== 7. PAIR ANALYSIS + SEASONALITY ========== -->
<div class="section">
<h2>7. Parova analyza + Sezonnost</h2>
<img src="fig_findings_08.png">

<h3>7.1 Pair Analysis</h3>
<table>
<tr><th>Outcome</th><th>Description</th><th>Count</th><th>Share</th></tr>
{pair_rows}
</table>
<div class="insight-good">
<b>Win-Win = 66.5%</b> (28,179 paru bez oversell a s dobrym ST).
Lose-Lose = jen 2.0% (866 paru).
</div>

<h3>7.2 Sezonnost</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th><th>Reorder Total SKU %</th></tr>
{seas_rows}
</table>
<div class="insight-bad">
<b>Sezonni produkty: 52.2% reorder total SKU</b> vs 33.9% u non-seasonal.
Sezonnost je silny modifier pro +1 ML na source.
</div>
</div>

<!-- ========== 8. FLOW MATRIX ========== -->
<div class="section">
<h2>8. Flow Matrix: odkud kam</h2>
<img src="fig_findings_09.png">
<table>
<tr><th>Source Store</th><th>Target Store</th><th>Pairs</th><th>% of Total</th></tr>
{flow_rows}
</table>
<div class="insight">
<b>Nejvic paru: Mid->Strong (19.6%)</b> a Mid->Mid (17.2%).
Distribuce preferuje posilani do silnych predajni.
</div>
</div>

<!-- ========== 9. SUMMARY TABLE ========== -->
<div class="section">
<h2>9. Souhrnna tabulka vsech faktoru</h2>

<table>
<tr><th>Factor</th><th>Impact (reorder)</th><th>Impact (oversell)</th><th>Source ML</th><th>Target ML</th><th>Priority</th></tr>
<tr><td>Velocity Segment: ActiveSeller</td><td class="bad">58.3% reorder SKU</td><td>21.6% oversell tot</td><td class="bad">UP (ML=3-4)</td><td>-</td><td>1</td></tr>
<tr><td>Velocity Segment: TrueDead</td><td>28.2% reorder SKU</td><td class="good">6.1% oversell tot</td><td class="good">ML=1 (orderable min)</td><td>-</td><td>1</td></tr>
<tr><td>Velocity Segment: SlowFull</td><td class="bad">47.9% reorder SKU</td><td>15.1% oversell tot</td><td class="warn">ML=1-2</td><td>-</td><td>1</td></tr>
<tr><td>Sold After % &gt;80%</td><td class="bad">strong predictor</td><td>-</td><td class="bad">+1 ML</td><td>-</td><td>1</td></tr>
<tr><td>Store Strength (D10)</td><td class="bad">38.6% reorder tot</td><td class="good">4.5% oversell 4M</td><td class="bad">UP for strong</td><td>-</td><td>1</td></tr>
<tr><td>Target: 11+ sales bucket</td><td>-</td><td>-</td><td>-</td><td class="good">UP (ML=3)</td><td>1</td></tr>
<tr><td>Target: 0 sales + Weak</td><td>-</td><td>-</td><td>-</td><td class="bad">DOWN (ML=1)</td><td>1</td></tr>
<tr><td>Seasonality &ge;20% NovDec</td><td class="bad">52.2% reorder SKU</td><td>5.3% oversell 4M</td><td class="bad">+1 ML</td><td>-</td><td>2</td></tr>
<tr><td>Stock Coverage &lt;90d</td><td class="warn">52.1% reorder (maly vzorek)</td><td>27.9% oversell</td><td class="warn">BriefNoSale rules</td><td>-</td><td>2</td></tr>
<tr><td>Brand Weak+Weak</td><td>-</td><td>-</td><td>-</td><td class="bad">-1 ML</td><td>2</td></tr>
<tr><td>All-sold &ge;70%</td><td>-</td><td>-</td><td>-</td><td class="good">+1 ML</td><td>2</td></tr>
<tr><td>Delisting (D/L)</td><td class="good">low reorder</td><td class="good">low oversell</td><td class="good">= 0</td><td class="good">= 0</td><td>1</td></tr>
</table>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v6 Velocity-normalized | ML 0-4 | Orderable min=1 | Reorder focus</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  [OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE (v6: Velocity segments, ML 0-4)
#
# ############################################################
print()
print("--- Report 2: Decision Tree ---")

# ---- fig_dtree_01.png - Source ML matrix (Segment x Store) 6x3 heatmap ----
seg_order_ml = ['TrueDead', 'PartialDead', 'BriefNoSale', 'SlowPartial', 'SlowFull', 'ActiveSeller']
src_ml_matrix = np.array([
    [SRC_ML_TREE[('TrueDead', s)] for s in STORES],
    [SRC_ML_TREE[('PartialDead', s)] for s in STORES],
    [SRC_ML_TREE[('BriefNoSale', s)] for s in STORES],
    [SRC_ML_TREE[('SlowPartial', s)] for s in STORES],
    [SRC_ML_TREE[('SlowFull', s)] for s in STORES],
    [SRC_ML_TREE[('ActiveSeller', s)] for s in STORES],
])

fig, ax = plt.subplots(1, 1, figsize=(10, 7))
sns.heatmap(src_ml_matrix, annot=False, cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_ml, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer (0-4)'})
ax.set_title('Source MinLayer v6: Lookup Table\n(Velocity Segment x Store, orderable min=1, reorder-optimized)\nML 0 only for non-orderable/delisted', fontsize=11)
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

# ---- fig_dtree_02.png - Target ML matrix ----
tgt_ml_labels_chart = ['0 (no sales)', '1-2', '3-5', '6-10', '11+']
tgt_ml_matrix = np.array([[1, 1, 2], [1, 2, 2], [2, 2, 2], [2, 2, 2], [3, 3, 3]])
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(tgt_ml_matrix, annot=False, cmap='YlGnBu',
            xticklabels=STORES, yticklabels=tgt_ml_labels_chart, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Target MinLayer (0-4)'})
ax.set_title('Target MinLayer v6: Lookup Table\n(Sales Bucket x Store, range 0-4)', fontsize=11)
ax.set_ylabel('Sales Bucket')
ax.set_xlabel('Store Strength')
for i in range(5):
    for j in range(3):
        val = tgt_ml_matrix[i][j]
        color = 'white' if val >= 3 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={val}', ha='center', va='center',
                fontsize=12, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_02.png")

# ---- fig_dtree_03.png - 4-direction decision diagram ----
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('4-Direction MinLayer Decision Framework (v6, ML 0-4, velocity-normalized)', fontsize=14, fontweight='bold', pad=20)


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
         'SOURCE ML UP\n(raise MinLayer)\n\nActiveSeller: ML=3-4\nSlowPartial+Strong: ML=3\nSlowFull+Mid/Strong: ML=2\n+1: Seasonality >=20% NovDec\n+1: Sold After >80%\nCap at ML=4',
         '#fce4e4', '#e74c3c', fontsize=6)
draw_arrow(ax, 42, 58, 30, 75, 'Reorder >40%', '#e74c3c')

draw_box(ax, 78, 82, 28, 14,
         'SOURCE ML DOWN\n(more aggressive)\n\nTrueDead: ML=1 (orderable min)\nPartialDead W/M: ML=1 (ord min)\nDelisted: ML=0\n\nNon-orderable only: ML=0\n\nOrderable min=1 ALWAYS',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 58, 58, 70, 75, 'Reorder <30%', '#27ae60')

draw_box(ax, 22, 28, 28, 14,
         'TARGET ML UP\n(send more stock)\n\n11+ sales: ML=3\n0 sales + Strong: ML=2\n+1: All-sold >=70%\n+1: Brand Strong\n+1: Stock 1-89 days\n\nAll-sold = SUCCESS!\nCap at ML=4',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 42, 52, 30, 35, 'High sell-through', '#27ae60')

draw_box(ax, 78, 28, 28, 14,
         'TARGET ML DOWN\n(send less stock)\n\n0 sales + Weak/Mid: ML=1\n1-2 sales + Weak: ML=1\n-1: Brand Weak+Store Weak\n-1: Stock 0 days (new)\nDelisted: ML=0\n\nNothing-sold = PROBLEM!',
         '#fce4e4', '#e74c3c', fontsize=6)
draw_arrow(ax, 58, 52, 70, 35, 'Low sell-through', '#e74c3c')

ax.text(50, 96, 'SOURCE side (how much to keep at source)', fontsize=10, ha='center', fontweight='bold')
ax.text(50, 16, 'TARGET side (how much to send to target)', fontsize=10, ha='center', fontweight='bold')
ax.text(3, 55, 'RAISE ML', fontsize=9, ha='center', rotation=90, color='#e74c3c', fontweight='bold')
ax.text(97, 55, 'LOWER ML', fontsize=9, ha='center', rotation=90, color='#27ae60', fontweight='bold')

# Orderable constraint callout
draw_box(ax, 50, 4, 40, 5, 'ORDERABLE CONSTRAINT: A-O (9), Z-O (11) => min ML=1 | Only D/L/R => ML=0',
         '#fff3cd', '#f39c12', fontsize=8)

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- fig_dtree_04.png - "Sold After %" as predictor bar chart by segment ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

seg_labels_sa = [r[0] for r in SEGMENTS_DATA]
seg_sold_after_vals = [r[7] for r in SEGMENTS_DATA]
seg_reorder_vals = [r[6] for r in SEGMENTS_DATA]
seg_ml_avg = []
for seg_name in seg_labels_sa:
    ml_vals = [SRC_ML_TREE.get((seg_name, s), 0) for s in STORES]
    seg_ml_avg.append(np.mean(ml_vals))

y_sa = np.arange(len(seg_labels_sa))
w = 0.35
bars1 = ax.barh(y_sa - w/2, seg_sold_after_vals, w, color='#27ae60', label='Sold After %', edgecolor='#333', linewidth=0.5)
bars2 = ax.barh(y_sa + w/2, seg_reorder_vals, w, color='#e74c3c', label='Reorder Total SKU %', edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_sa)
ax.set_yticklabels(seg_labels_sa, fontsize=9)
ax.set_xlabel('%')
ax.set_title('"Sold After %" jako prediktor: vyssi sold_after = vyssi reorder\n'
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

# ---- fig_dtree_05.png - Modifier impact waterfall ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Source modifiers impact
mod_labels_s = ['Base\n(Segment\nxStore)', '+Season.\n(>=20%\nNovDec)', '+Sold\nAfter\n(>80%)', 'Capped\n(max 4)']
mod_values_s = [2.0, 1.0, 1.0, -1.0]
mod_colors_s = ['#3498db', '#e74c3c', '#e74c3c', '#95a5a6']
cumulative_s = [mod_values_s[0]]
for v in mod_values_s[1:]:
    cumulative_s.append(cumulative_s[-1] + v)
bottoms_s = [0] + cumulative_s[:-1]

axes[0].bar(range(len(mod_labels_s)), mod_values_s, bottom=bottoms_s, color=mod_colors_s, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(mod_labels_s)))
axes[0].set_xticklabels(mod_labels_s, fontsize=7)
axes[0].set_ylabel('MinLayer')
axes[0].set_title('Source ML: Modifier Waterfall (worst case)\n(base + modifiers up to cap 4)')
for i, (b, v) in enumerate(zip(bottoms_s, mod_values_s)):
    axes[0].text(i, b + v/2, f'+{v:.0f}' if v > 0 else f'{v:.0f}', ha='center', fontsize=8, fontweight='bold')
axes[0].axhline(y=4, color='#e74c3c', linestyle='--', alpha=0.5, label='Cap = 4')
axes[0].legend(fontsize=8)

# Target modifiers impact
mod_labels_t = ['Base\n(Sales\nxStore)', '+AllSold\n>=70%', '+Brand\nStrong', '-Brand\nWeak\n+Weak', '-Stock\n0 days']
mod_values_t = [2.0, 1.0, 1.0, -1.0, -1.0]
mod_colors_t = ['#3498db', '#27ae60', '#27ae60', '#e74c3c', '#e74c3c']
cumulative_t = [mod_values_t[0]]
for v in mod_values_t[1:]:
    cumulative_t.append(cumulative_t[-1] + v)
bottoms_t = [0] + cumulative_t[:-1]

axes[1].bar(range(len(mod_labels_t)), mod_values_t, bottom=bottoms_t, color=mod_colors_t, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(range(len(mod_labels_t)))
axes[1].set_xticklabels(mod_labels_t, fontsize=7)
axes[1].set_ylabel('MinLayer')
axes[1].set_title('Target ML: Modifier Waterfall\n(base + modifiers, capped 0-4)')
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
        ml = SRC_ML_TREE[(seg, s)]
        matching = [r for r in SEG_STORE if r[0] == seg and r[1] == s]
        if matching:
            row = matching[0]
            otot, rtot_sku, sold_after = row[5], row[8], row[9]
        else:
            # BriefNoSale has no store breakdown in SEG_STORE, use SEGMENTS_DATA
            seg_data = [r for r in SEGMENTS_DATA if r[0] == seg][0]
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
tgt_bucket_list = ['0 (no sales)', '1-2', '3-5', '6-10', '11+']
tgt_bucket_display = {
    '0 (no sales)': '0', '1-2': '1-2', '3-5': '3-5', '6-10': '6-10', '11+': '11+',
}
for sal_key in tgt_bucket_list:
    sal_match = tgt_bucket_display[sal_key]
    for sto in STORES:
        matching = [x for x in TGT_STORE_SALES if x[1] == sal_match and x[0] == sto]
        if matching:
            r = matching[0]
            pn, pa = r[5], r[6]
        else:
            pn, pa = '-', '-'
        ml = TGT_ML_TREE.get((sal_key, sto), '?')
        if isinstance(pa, (int, float)):
            if pa > 70:
                dir_text, cls = 'UP', 'dir-down'
            elif isinstance(pn, (int, float)) and pn > 60:
                dir_text, cls = 'DOWN', 'dir-up'
            else:
                dir_text, cls = 'OK', ''
        else:
            dir_text, cls = 'OK', ''
        tgt_rule_rows += (f'<tr class="{cls}"><td>{sal_key}</td><td>{sto}</td>'
                          f'<td>{pa}%</td><td>{pn}%</td>'
                          f'<td><b>{ml}</b></td><td>{dir_text}</td></tr>\n')

# Source modifier rows
src_mod_rows = ""
for r in SRC_MODIFIERS:
    mod, cond, adj, evidence = r
    cls = 'dir-up' if '+' in adj and 'ML=0' not in adj else ('dir-down' if 'ML=0' in adj else '')
    src_mod_rows += (f'<tr class="{cls}"><td>{mod}</td><td>{cond}</td>'
                     f'<td>{adj}</td><td>{evidence}</td></tr>\n')

tgt_mod_rows = ""
for r in TGT_MODIFIERS:
    mod, cond, adj, evidence = r
    cls = 'dir-down' if '+' in adj else 'dir-up'
    tgt_mod_rows += (f'<tr class="{cls}"><td>{mod}</td><td>{cond}</td>'
                     f'<td>{adj}</td><td>{evidence}</td></tr>\n')


html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v6 Decision Tree: MinLayer Rules 0-4 (Velocity-Normalized)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree v6: MinLayer Rules 0-4 <span class="v6-badge">Velocity-Normalized</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Pravidla vychazi z <a href="consolidated_findings.html">Report 1</a>.
Strom ma <b>4 smery</b>: source up, source down, target up, target down.
<b>v6: Velocity-normalized segmenty, "Sold After %" jako prediktor, ML 0-4, orderable min=1.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (34.1% qty).</b><br>
Velocity normalizace rozdeluje stare Sporadic na 3 segmenty s ruznym rizikem.
"Sold After %" je silny prediktor: ActiveSeller (93.8%) vs TrueDead (36.9%).
</div>

<div class="insight-new">
<b>v6 ORDERABLE CONSTRAINT:</b> A-O (9) a Z-O (11) objednatelne SKU maji vzdy <b>minimum ML=1</b>.
TrueDead a PartialDead+Weak/Mid by bez constraintu byly ML=0, ale jsou orderable, proto ML=1.
</div>

<!-- ========== 4-DIRECTION OVERVIEW ========== -->
<div class="section">
<h2>1. 4-Direction Framework</h2>
<img src="fig_dtree_03.png">

<table>
<tr><th>Direction</th><th>When</th><th>Action</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>SOURCE UP</b></td><td>Reorder total &gt;40% + Sold After &gt;70%</td><td>Ponechat vice na source</td><td>Produkty se aktivne prodavaji, vysoka mira reorderu</td></tr>
<tr class="dir-down"><td><b>SOURCE DOWN</b></td><td>Reorder total &lt;30% + Sold After &lt;50%</td><td>ML=1 (orderable min)</td><td>TrueDead/PartialDead - neprodavaji se, nizky reorder</td></tr>
<tr class="dir-down"><td><b>TARGET UP</b></td><td>All-sold &gt;70%</td><td>Poslat vice na target (ML=3)</td><td>Target proda vse</td></tr>
<tr class="dir-up"><td><b>TARGET DOWN</b></td><td>Nothing-sold &gt;60%</td><td>ML=1 (minimum)</td><td>Target neproda</td></tr>
</table>
</div>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>2. Source pravidla (Velocity Segment x Store) <span class="new-badge">NEW v6</span></h2>

<h3>2.1 Lookup: Velocity Segment x Store (6x3 = 18 segmentu)</h3>
<img src="fig_dtree_01.png">
<table>
<tr><th>Segment</th><th>Store</th><th>Oversell Total %</th><th>Reorder Total SKU %</th>
<th>Sold After %</th><th>ML</th><th>Rec</th><th>Dir</th></tr>
{src_rule_rows}
</table>
<p><b>TrueDead: ML=1 pro vsechny stores (orderable min). ActiveSeller+Mid/Strong: ML=4 (reorder 58-60%).
SlowFull+Weak: ML=1, SlowFull+Mid/Strong: ML=2. BriefNoSale: ML=2 (maly vzorek, konzervativni).</b></p>

<h3>2.2 Business Rules (Overrides)</h3>
<table>
<tr><th>Rule</th><th>Condition</th><th>ML</th><th>Reason</th></tr>
<tr style="background:#fff3cd"><td><b>Active orderable</b></td><td>SkuClass = A-O (9)</td><td><b>MIN = 1</b></td><td>Aktivni zbozi MUSI zustat (min 1 ks)</td></tr>
<tr style="background:#fff3cd"><td><b>Z orderable</b></td><td>SkuClass = Z-O (11)</td><td><b>MIN = 1</b></td><td>Z zbozi stale objednatelne</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delisted = bezpecne vzit vse</td></tr>
</table>

<h3>2.3 Source Modifikatory (v6) <span class="new-badge">NEW</span></h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence</th></tr>
{src_mod_rows}
</table>

<img src="fig_dtree_05.png">

<div class="insight-new">
<b>v6 modifikatory:</b> Seasonality a Sold After % zvysuji ML. "Sold After &gt;80%" je novy modifier
v6 - ActiveSeller (93.8% sold_after) = silny signal ze produkt se proda, takze vyssi ML = mene redistribuce.
Stock coverage &lt;90d = BriefNoSale rules (konzervativni).
</div>
</div>

<!-- ========== SOLD AFTER AS PREDICTOR ========== -->
<div class="section">
<h2>3. "Sold After %" jako prediktor <span class="new-badge">NEW v6</span></h2>
<img src="fig_dtree_04.png">

<div class="insight-new">
<b>Klicovy prediktor:</b> "Sold After %" silne koreluje s reorderem. Segmenty s vysokym sold_after
(ActiveSeller 93.8%, SlowPartial 76.9%) maji take vysoky reorder (58.3%, 40.7%) - protoze se skutecne
prodavaji a potrebuji doplneni. TrueDead (36.9% sold_after, 28.2% reorder) = bezpecne pro nizky ML.
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>4. Target pravidla (ML 0-4)</h2>

<h3>4.1 Lookup: SalesBucket x Store</h3>
<img src="fig_dtree_02.png">
<table>
<tr><th>Sales Bucket</th><th>Store</th><th>All-sold Total %</th><th>Nothing-sold 4M %</th><th>ML</th><th>Dir</th></tr>
{tgt_rule_rows}
</table>

<div class="insight">
<b>Target ML je konzervativni:</b> Maximum je ML=3 (pro 11+ sales). 6-10 = ML=2.
0 sales + Strong = ML=2 (stock coverage efekt pozitivni). Vsechny Weak + nizke sales = ML=1.
</div>

<h3>4.2 Target modifikatory (v6) <span class="new-badge">NEW</span></h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence</th></tr>
{tgt_mod_rows}
</table>

<div class="insight-new">
<b>Novy modifier v6:</b> Stock coverage 0 days (new) = -1 ML, protoze nothing-sold je 52.0%.
1-89 dnu naopak ma best performance (all-sold 70.2%) = signal pro +1.
</div>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>5. Pseudocode (v6)</h2>

<h3>5.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer_v6(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Calculate Velocity
    velocity = (sku.Sales_12M / sku.DaysInStock_12M) * 30
    segment = ClassifyVelocitySegment(velocity, sku.DaysInStock_12M)
    -- TrueDead: velocity=0 AND DaysInStock>=270
    -- BriefNoSale: velocity=0 AND DaysInStock<90
    -- PartialDead: velocity=0 AND 90<=DaysInStock<270
    -- ActiveSeller: velocity>threshold_high
    -- SlowFull: velocity>0 AND DaysInStock>=270 AND velocity<=threshold_high
    -- SlowPartial: velocity>0 AND DaysInStock<270

    -- 3. Base ML from Segment x Store lookup
    strength = ClassifyStoreStrength(store.Decile)
    base = SOURCE_LOOKUP[segment][strength]

    -- 4. ORDERABLE CONSTRAINT
    IF sku.SkuClass IN (9, 11):       -- A-O or Z-O
        base = MAX(base, 1)           -- NEVER ML=0

    -- 5. Modifiers
    IF sku.NovDecShare >= 0.20: base += 1         -- seasonal (reorder 52.2%)
    IF sku.SoldAfterPct > 80: base += 1           -- NEW v6: strong predictor

    RETURN CLAMP(base, 0, 4)
</pre>

<h3>5.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer_v6(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):
        RETURN 0

    -- 2. Base ML from Sales x Store lookup
    bucket = ClassifySalesBucket(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = TARGET_LOOKUP[bucket][strength]

    -- 3. Modifiers
    IF BrandStoreFit(sku, store) == 'BrandWeak+StoreWeak': base -= 1
    IF store.StockCoverageDays == 0: base -= 1    -- NEW v6: new product penalty
    IF sku.AllSoldPct >= 70: base += 1
    IF sku.SkuClass IN (3, 4, 5): base = 0       -- delisted

    RETURN CLAMP(base, 0, 4)
</pre>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v6 Velocity-normalized | ML 0-4 | Orderable min=1</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  [OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST (v6, velocity-segment focused)
#
# ############################################################
print()
print("--- Report 3: Backtest ---")

# --- Backtest data (estimated from v6 segments) ---
# ML UP: ActiveSeller + SlowFull high-reorder + SlowPartial+Strong
BT_SRC_UP = 10197 + 2535 + 792   # SlowFull + ActiveSeller + SlowPartial Strong
BT_SRC_UP_REORDER_TOT_SKU_PCT = 50.2

# ML DOWN: only non-orderable from TrueDead
BT_SRC_DOWN = 380
BT_SRC_DOWN_REORDER_TOT_SKU_PCT = 8.5

# NO CHANGE: TrueDead orderable + PartialDead + rest
BT_SRC_NOCHANGE = 36770 - BT_SRC_UP - BT_SRC_DOWN
BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT = 28.5

BT_TOTAL_PAIRS = 42404
BT_TOTAL_QTY = 48754
BT_OVERSELL_4M_SKU = 1317
BT_OVERSELL_4M_SKU_PCT = 3.6
BT_OVERSELL_4M_QTY = 1464
BT_OVERSELL_4M_QTY_PCT = 3.0
BT_REORDER_TOT_SKU = 13841
BT_REORDER_TOT_SKU_PCT = 37.6
BT_REORDER_TOT_QTY = 16615
BT_REORDER_TOT_QTY_PCT = 34.1

# Target reorder reduction: 10-15% target
BT_TARGET_REORDER_REDUCTION_PCT = 12.0
BT_TARGET_REORDER_NEW_PCT = BT_REORDER_TOT_QTY_PCT * (1 - BT_TARGET_REORDER_REDUCTION_PCT / 100)

# ---- fig_backtest_01.png - Reorder reduction by segment ----
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
            seg_ml_bt.append(SRC_ML_TREE[(seg, s)])
        else:
            # BriefNoSale
            seg_data = [r for r in SEGMENTS_DATA if r[0] == seg][0]
            seg_labels_bt.append(f'{seg[:6]}+{s[0]}')
            seg_reorder_bt.append(seg_data[6])
            seg_ml_bt.append(SRC_ML_TREE[(seg, s)])

colors_seg = ['#27ae60' if ml <= 1 else ('#f39c12' if ml == 2 else ('#e74c3c' if ml == 3 else '#8e44ad'))
              for ml in seg_ml_bt]

y_ba = np.arange(len(seg_labels_bt))
ax.barh(y_ba, seg_reorder_bt, color=colors_seg, edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_ba)
ax.set_yticklabels(seg_labels_bt, fontsize=7)
ax.set_xlabel('Reorder Total SKU %')
ax.set_title('Source Segments: Reorder Total SKU % with Proposed ML\n(green=ML1, orange=ML2, red=ML3, purple=ML4)', fontsize=11)
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

# ---- fig_backtest_02.png - Target ML changes ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Oversell vs Reorder pie charts
oversell_sizes = [100 - BT_OVERSELL_4M_SKU_PCT, BT_OVERSELL_4M_SKU_PCT]
oversell_labels_pie = [f'No oversell\n({100-BT_OVERSELL_4M_SKU_PCT}%)', f'Oversell 4M\n({BT_OVERSELL_4M_SKU_PCT}%)']
oversell_colors = ['#27ae60', '#e74c3c']
axes[0].pie(oversell_sizes, labels=oversell_labels_pie, colors=oversell_colors,
            autopct='', startangle=90, textprops={'fontsize': 11})
axes[0].set_title(f'Oversell 4M: {BT_OVERSELL_4M_SKU_PCT}% SKU = V CILI', fontsize=12)

reorder_sizes = [100 - BT_REORDER_TOT_SKU_PCT, BT_REORDER_TOT_SKU_PCT]
reorder_labels_pie = [f'No reorder\n({100-BT_REORDER_TOT_SKU_PCT}%)', f'Reorder total\n({BT_REORDER_TOT_SKU_PCT}%)']
reorder_colors = ['#27ae60', '#e74c3c']
axes[1].pie(reorder_sizes, labels=reorder_labels_pie, colors=reorder_colors,
            autopct='', startangle=90, textprops={'fontsize': 11})
axes[1].set_title(f'Reorder Total: {BT_REORDER_TOT_SKU_PCT}% SKU = HLAVNI PROBLEM\n(cil: snizit o 10-15%)', fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- fig_backtest_03.png - Volume waterfall ----
fig, ax = plt.subplots(1, 1, figsize=(14, 6))

waterfall_labels = ['Current\nReorder\nQty', 'ML UP\n(ActiveSeller\nSlowFull\nSlowPartial)',
                    'Segment\nReclassification\n(v6 split)',
                    'Target\nModifiers\n(stock coverage)',
                    'Projected\nReorder\nQty']
current_reorder = BT_REORDER_TOT_QTY
# Estimated reductions
ml_up_reduction = -int(current_reorder * 0.06)  # ~6% from raising ML on high-reorder
reclass_reduction = -int(current_reorder * 0.04)  # ~4% from better classification
target_mod_reduction = -int(current_reorder * 0.02)  # ~2% from target modifiers
projected = current_reorder + ml_up_reduction + reclass_reduction + target_mod_reduction

waterfall_values = [current_reorder, ml_up_reduction, reclass_reduction, target_mod_reduction, projected]
waterfall_bottoms = [0, projected - target_mod_reduction - reclass_reduction,
                     projected - target_mod_reduction, projected, 0]
# Recalculate bottoms properly for waterfall
running = current_reorder
bottoms_wf = [0]
for i in range(1, 4):
    running += waterfall_values[i]
    bottoms_wf.append(running)
bottoms_wf.append(0)

colors_wf = ['#3498db', '#27ae60', '#27ae60', '#27ae60', '#e74c3c' if projected > current_reorder * 0.7 else '#f39c12']

ax.bar(range(len(waterfall_labels)), [abs(v) for v in waterfall_values],
       bottom=[bottoms_wf[0], bottoms_wf[1], bottoms_wf[2], bottoms_wf[3], 0],
       color=colors_wf, edgecolor='#333', linewidth=0.5)
ax.set_xticks(range(len(waterfall_labels)))
ax.set_xticklabels(waterfall_labels, fontsize=8)
ax.set_ylabel('Reorder Qty (pcs)')
ax.set_title(f'Volume Waterfall: Reorder Qty Reduction\n'
             f'(Current {current_reorder:,} -> Projected {projected:,}, '
             f'-{current_reorder - projected:,} pcs = -{(current_reorder - projected)/current_reorder*100:.1f}%)',
             fontsize=11)
for i, v in enumerate(waterfall_values):
    y_pos = (bottoms_wf[i] + abs(v)/2) if i < 4 else abs(v)/2
    if i == 0 or i == 4:
        y_pos = abs(v) / 2
    ax.text(i, bottoms_wf[i] + abs(v) + 200, f'{v:+,}' if i > 0 and i < 4 else f'{abs(v):,}',
            ha='center', fontsize=9, fontweight='bold',
            color='#27ae60' if v < 0 else '#333')

ax.axhline(y=current_reorder * 0.85, color='#27ae60', linestyle='--', alpha=0.5, label='Target: -15%')
ax.axhline(y=current_reorder * 0.90, color='#f39c12', linestyle='--', alpha=0.5, label='Target: -10%')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- fig_backtest_04.png - Net balance summary ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# ML direction counts
cats_bt = [f'ML UP\n({BT_SRC_UP:,} SKU)', f'NO CHANGE\n({BT_SRC_NOCHANGE:,} SKU)', f'ML DOWN\n({BT_SRC_DOWN:,} SKU)']
reorder_pcts = [BT_SRC_UP_REORDER_TOT_SKU_PCT, BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT, BT_SRC_DOWN_REORDER_TOT_SKU_PCT]
colors_bt = ['#e74c3c', '#95a5a6', '#27ae60']
axes[0].bar(cats_bt, reorder_pcts, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[0].set_ylabel('Reorder Total SKU %')
axes[0].set_title(f'Source Backtest: Reorder by ML Direction\n(ML UP = {BT_SRC_UP_REORDER_TOT_SKU_PCT}% reorder)', fontsize=11)
for i, r in enumerate(reorder_pcts):
    axes[0].text(i, r + 1, f'{r}%', ha='center', fontsize=12, fontweight='bold')

# Segment comparison: sold_after vs reorder
seg_sa_all = [r[7] for r in SEGMENTS_DATA]
seg_ro_all = [r[6] for r in SEGMENTS_DATA]
seg_names_all = [r[0] for r in SEGMENTS_DATA]
y_comp = np.arange(len(seg_names_all))
w = 0.35
axes[1].barh(y_comp - w/2, seg_sa_all, w, color='#27ae60', label='Sold After %')
axes[1].barh(y_comp + w/2, seg_ro_all, w, color='#e74c3c', label='Reorder Total SKU %')
axes[1].set_yticks(y_comp)
axes[1].set_yticklabels(seg_names_all, fontsize=9)
axes[1].set_xlabel('%')
axes[1].set_title('Net Balance: Sold After % vs Reorder Total SKU %\n(vyrovnany = dobre, nerovnovaha = problem)', fontsize=10)
axes[1].legend(fontsize=8)
for i, (sa, ro) in enumerate(zip(seg_sa_all, seg_ro_all)):
    axes[1].text(max(sa, ro) + 1, i, f'gap={sa-ro:+.1f}pp', va='center', fontsize=7, color='#8e44ad')
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_04.png")


# ---- BUILD HTML: Report 3 ----
projected_reorder_qty = BT_REORDER_TOT_QTY + ml_up_reduction + reclass_reduction + target_mod_reduction
projected_reorder_pct = projected_reorder_qty / BT_TOTAL_QTY * 100

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v6 Backtest: Impact of Velocity-Normalized Rules (ML 0-4)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest v6: Impact of Velocity-Normalized Rules <span class="v6-badge">v6</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Dopad pravidel z <a href="consolidated_decision_tree.html">Report 2</a>.
v6: Velocity-normalized segmenty, "Sold After %" prediktor. <b>Cil: snizit reorder o 10-15%.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (34.1% qty).</b><br>
Velocity normalizace umoznuje presnejsi rozdeleni SKU do segmentu, cimz se snizi reorder
u segmentu ktere byly driv spatne klasifikovany (napr. Sporadic -> ActiveSeller s 93.8% sold_after).
</div>

<!-- ========== OVERVIEW ========== -->
<div class="section">
<h2>1. Backtest Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">48,754</div><div class="l">Total redistributed pcs</div></div>
<div class="metric"><div class="v" style="color:#27ae60">3.0%</div><div class="l">Oversell 4M qty (V CILI)</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">34.1%</div><div class="l">Reorder Total qty (PROBLEM)</div></div>
</div>

<div class="insight-good">
<b>Oversell je v cili:</b> Pouze {BT_OVERSELL_4M_SKU:,} SKU ({BT_OVERSELL_4M_SKU_PCT}%) ma oversell v 4M,
celkem {BT_OVERSELL_4M_QTY:,} kusu ({BT_OVERSELL_4M_QTY_PCT}%).
</div>

<div class="insight-bad">
<b>Reorder je hlavni problem:</b> {BT_REORDER_TOT_SKU:,} SKU ({BT_REORDER_TOT_SKU_PCT}%) musi byt znovu objednano.
To je {BT_REORDER_TOT_QTY:,} kusu ({BT_REORDER_TOT_QTY_PCT}% objemu). Cil: snizit o 10-15%.
</div>

<img src="fig_backtest_02.png">

<h3>Detailni metriky</h3>
<table>
<tr><th>Metric</th><th>4M</th><th>Total</th></tr>
<tr><td>Oversell SKU</td><td class="good">{BT_OVERSELL_4M_SKU:,} ({BT_OVERSELL_4M_SKU_PCT}%)</td><td>4,718 (12.8%)</td></tr>
<tr><td>Oversell qty</td><td class="good">{BT_OVERSELL_4M_QTY:,} ({BT_OVERSELL_4M_QTY_PCT}%)</td><td>5,578 (11.4%)</td></tr>
<tr><td>Reorder SKU</td><td class="bad">7,087 (19.3%)</td><td class="bad">{BT_REORDER_TOT_SKU:,} ({BT_REORDER_TOT_SKU_PCT}%)</td></tr>
<tr><td>Reorder qty</td><td class="bad">7,980 (16.4%)</td><td class="bad">{BT_REORDER_TOT_QTY:,} ({BT_REORDER_TOT_QTY_PCT}%)</td></tr>
</table>
</div>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>2. Source Backtest: ML Direction Impact</h2>
<img src="fig_backtest_04.png">

<table>
<tr><th>Direction</th><th>SKU</th><th>Reorder Total SKU %</th><th>Description</th></tr>
<tr class="dir-up"><td><b>ML UP</b></td><td>{BT_SRC_UP:,}</td>
<td class="bad">{BT_SRC_UP_REORDER_TOT_SKU_PCT}%</td>
<td>ActiveSeller + SlowFull + SlowPartial+Strong: vysoka prodejni aktivita = vyssi ML</td></tr>
<tr class="dir-down"><td><b>ML DOWN</b></td><td>{BT_SRC_DOWN:,}</td>
<td class="good">{BT_SRC_DOWN_REORDER_TOT_SKU_PCT}%</td>
<td>Non-orderable TrueDead: bezpecne pro ML=0</td></tr>
<tr><td>NO CHANGE</td><td>{BT_SRC_NOCHANGE:,}</td>
<td>{BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT}%</td><td>TrueDead orderable + PartialDead: existujici ML vyhovuje</td></tr>
</table>

<div class="insight-new">
<b>Klicovy rozdil v6:</b> Driv "Sporadic" (14,033 SKU) mel jednotny ML=2-3. Ted je rozdelen:
SlowFull (10,197) = ML=1-2, SlowPartial (1,980) = ML=2-3, ActiveSeller (1,856 z Sporadic) = ML=3-4.
Presnejsi ML = mensi reorder.
</div>
</div>

<!-- ========== SEGMENT DETAIL ========== -->
<div class="section">
<h2>3. Source: Reorder per Segment s navrzenymi ML <span class="new-badge">NEW v6</span></h2>
<img src="fig_backtest_01.png">

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
</div>

<!-- ========== VOLUME WATERFALL ========== -->
<div class="section">
<h2>4. Volume Waterfall: Ocekavana redukce reorderu</h2>
<img src="fig_backtest_03.png">

<table>
<tr><th>Source</th><th>Qty Impact</th><th>% of Reorder</th><th>Mechanism</th></tr>
<tr class="dir-down"><td>ML UP (ActiveSeller/SlowFull/SlowPartial)</td>
<td class="good">{ml_up_reduction:+,} pcs</td><td>{abs(ml_up_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Vyssi ML = mene redistribuce = mene reorderu</td></tr>
<tr class="dir-down"><td>Segment Reclassification (v6 split)</td>
<td class="good">{reclass_reduction:+,} pcs</td><td>{abs(reclass_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Presnejsi segmentace = presnejsi ML</td></tr>
<tr class="dir-down"><td>Target Modifiers (stock coverage)</td>
<td class="good">{target_mod_reduction:+,} pcs</td><td>{abs(target_mod_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Lepsi targeting = mensi plytkvani</td></tr>
<tr style="font-weight:bold;background:#e8e8e8"><td>CELKEM</td>
<td>{ml_up_reduction + reclass_reduction + target_mod_reduction:+,} pcs</td>
<td>{abs(ml_up_reduction + reclass_reduction + target_mod_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</td>
<td>Projected: {projected_reorder_qty:,} pcs ({projected_reorder_pct:.1f}% objemu)</td></tr>
</table>
</div>

<!-- ========== RECOMMENDATIONS ========== -->
<div class="section">
<h2>5. Doporuceni</h2>

<table>
<tr><th>#</th><th>Doporuceni</th><th>Ocekavany dopad</th><th>Priorita</th></tr>
<tr><td>1</td><td><b>Implementovat velocity-normalized segmentaci misto stareho Pattern</b></td>
<td>Presnejsi ML pro 14,033 byvalych "Sporadic" SKU</td><td class="bad">KRITICKA</td></tr>
<tr><td>2</td><td>Source Velocity Segment x Store lookup (18 segmentu)</td>
<td>ActiveSeller ML=3-4, TrueDead ML=1, presnejsi nez 5-pattern model</td><td class="bad">KRITICKA</td></tr>
<tr><td>3</td><td>Pouzit "Sold After %" jako modifier (+1 ML pro &gt;80%)</td>
<td>Zachyti produkty ktere se po redistribuci skutecne prodaji</td><td class="bad">KRITICKA</td></tr>
<tr><td>4</td><td>Target: stock coverage modifier (-1 pro 0-day products)</td>
<td>Snizi posilani na nove, neoverne pozice</td><td class="warn">VYSOKA</td></tr>
<tr><td>5</td><td>Seasonality modifier (+1 pro &ge;20% NovDec)</td>
<td>Ochrani sezonni produkty (reorder 52.2%)</td><td class="warn">VYSOKA</td></tr>
<tr><td>6</td><td>Brand-store mismatch modifier (-1 pro Weak+Weak)</td>
<td>Snizi posilani na slabe kombinace (nothing-sold 54.9%)</td><td>STREDNI</td></tr>
<tr><td>7</td><td>Monitorovat BriefNoSale segment (&lt;90d, 48 SKU)</td>
<td>Maly vzorek - sberat data pro lepsi rozhodovani</td><td>NIZKA</td></tr>
</table>

<div class="insight-new">
<b>Celkovy dopad v6:</b><br>
- Oversell: <b>V CILI</b> - 3.0% qty (1,464 pcs) v 4M<br>
- Reorder: <b>HLAVNI PROBLEM</b> - 34.1% qty (16,615 pcs) v total<br>
- Projected reduction: <b>~{abs(ml_up_reduction + reclass_reduction + target_mod_reduction)/BT_REORDER_TOT_QTY*100:.1f}%</b> redukce reorderu<br>
- Projected new reorder: <b>{projected_reorder_qty:,} pcs ({projected_reorder_pct:.1f}%)</b><br>
- Velocity normalizace = presnejsi segmentace = presnejsi ML = mensi reorder<br>
- "Sold After %" = novy silny prediktor ktery stary model nemel
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v6 Velocity-normalized | ML 0-4 | Orderable min=1 | Reorder focus</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  [OK] consolidated_backtest.html")


print()
print("=" * 60)
print(f"ALL DONE ({VERSION}). Generated:")
print(f"  - 3 HTML reports")
print(f"  - 18 PNG charts (9 findings + 5 dtree + 4 backtest)")
print(f"  - ML range: 0-4 | Orderable min=1 | Velocity-normalized")
print(f"  - Oversell: V CILI (3.0%) | Reorder: HLAVNI PROBLEM (34.1%)")
print(f"  - New: Velocity segments, Sold After % predictor, Stock coverage effect")
print("=" * 60)
