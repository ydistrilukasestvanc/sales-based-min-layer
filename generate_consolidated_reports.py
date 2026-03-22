"""
Consolidated Reports Generator: SalesBased MinLayers - CalculationId=233
Generates 3 HTML reports + 10 charts into reports/ directory.

Key principles:
  - ALWAYS show BOTH reorder AND oversell side by side in every source table
  - Target analysis EQUALLY detailed as source (sell-through based)
  - Decision tree has 4 directions: source up, source down, target up, target down
  - Target all-sold = SUCCESS (green), target nothing-sold = PROBLEM (red)
  - Backtest shows VOLUME change (ks), not just SKU count
"""
import os
import glob as globmod
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime

VERSION = 'v2'
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports', VERSION)
os.makedirs(REPORTS_DIR, exist_ok=True)
sns.set_style("whitegrid")

# Clean target directory
for f in globmod.glob(os.path.join(REPORTS_DIR, '*')):
    os.remove(f)

print("=" * 60)
print("Generating consolidated reports (%s)..." % VERSION)
print("=" * 60)

# ============================================================
# COMMON CSS
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
pre { background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 12px; overflow-x: auto; }
.nav { background: #2c3e50; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; }
.nav a { color: #ecf0f1; margin-right: 20px; text-decoration: none; font-weight: bold; }
.nav a:hover { color: #3498db; }
.nav a.active { color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 4px; }
.arrow-up { color: #e74c3c; font-weight: bold; }
.arrow-down { color: #27ae60; font-weight: bold; }
.dir-up { background: #fce4e4; }
.dir-down { background: #d4edda; }
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
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA
# ============================================================

# --- SOURCE: Reorder vs Oversell by Pattern x Store (15 segments) ---
SRC_DATA = [
    # Pattern, Store, cnt, pct_reorder, reorder_qty, pct_oversell, oversell_qty, redist_qty, recommendation
    ('Dead',       'Weak',   4597, 24.5, 1225,  5.1,  251, 5461,  'CAN LOWER ML'),
    ('Dead',       'Mid',    6967, 29.5, 2320,  7.8,  607, 8633,  'CAN LOWER ML'),
    ('Dead',       'Strong', 4061, 31.4, 1481, 10.0,  486, 5143,  'OK'),
    ('Dying',      'Weak',   1594, 29.7,  516,  8.1,  135, 1933,  'CAN LOWER ML'),
    ('Dying',      'Mid',    2882, 35.4, 1110,  9.7,  302, 3505,  'CAN LOWER ML'),
    ('Dying',      'Strong', 1951, 37.1,  795, 12.6,  260, 2373,  'OK'),
    ('Sporadic',   'Weak',   2003, 37.2,  871, 10.9,  252, 2606,  'OK'),
    ('Sporadic',   'Mid',    4176, 44.1, 2255, 15.3,  777, 5783,  'OK'),
    ('Sporadic',   'Strong', 3712, 47.8, 2349, 20.1,  929, 5705,  'MUST RAISE ML'),
    ('Consistent', 'Weak',    431, 46.4,  246, 13.2,   63,  641,  'OK'),
    ('Consistent', 'Mid',    1164, 56.0,  858, 22.7,  316, 1877,  'MUST RAISE ML'),
    ('Consistent', 'Strong', 1693, 56.5, 1342, 28.0,  608, 2898,  'MUST RAISE ML'),
    ('Declining',  'Weak',    219, 55.3,  150, 25.1,   74,  294,  'MUST RAISE ML'),
    ('Declining',  'Mid',     569, 64.7,  446, 28.3,  190,  781,  'MUST RAISE ML'),
    ('Declining',  'Strong',  751, 68.0,  651, 35.4,  328, 1121,  'MUST RAISE ML'),
]

# --- TARGET: Sell-through by Store x Sales6M (9 segments) ---
TGT_STORE_SALES = [
    # Store, Sales, cnt, avg_st_4m, avg_st_total, pct_nothing, pct_allsold, received_qty, sold_qty
    ('Weak',   'Zero',      380, 0.49, 0.76, 43.7, 53.7,   407,   306),
    ('Weak',   'Low(1-2)',  3560, 0.37, 0.77, 34.6, 44.4,  3907,  4806),
    ('Weak',   'Med+(3+)',  1829, 0.72, 1.42, 12.6, 67.2,  2553,  5967),
    ('Mid',    'Zero',       982, 0.50, 0.85, 39.3, 57.2,  1057,   880),
    ('Mid',    'Low(1-2)',  9787, 0.42, 0.88, 28.8, 48.6, 10712, 15053),
    ('Mid',    'Med+(3+)',  5985, 0.76, 1.57, 12.5, 69.3,  8116, 20953),
    ('Strong', 'Zero',       790, 0.72, 1.18, 31.8, 66.5,   820,   950),
    ('Strong', 'Low(1-2)', 10419, 0.51, 1.09, 22.3, 57.1, 11415, 20075),
    ('Strong', 'Med+(3+)',  7899, 0.89, 1.83,  9.0, 74.7,  9767, 30279),
]

# --- TARGET: Sell-through by Brand-store fit ---
TGT_BRAND_FIT = [
    # Fit, cnt, avg_st_4m, avg_st_total, pct_nothing, pct_allsold, received_qty, sold_qty, remaining
    ('Strong+Strong brand', 17756, 0.69, 1.43, 16.5, 65.7, 20410, 48618,  8647),
    ('Weak+Strong brand',    1170, 0.59, 1.19, 22.3, 58.4,  1384,  2899,   722),
    ('Medium',              18655, 0.54, 1.12, 23.8, 56.2, 22109, 40766, 11901),
    ('Strong+Weak brand',     400, 0.53, 1.10, 29.0, 50.3,   522,   812,   296),
    ('Weak+Weak brand',      3650, 0.45, 0.90, 30.7, 50.3,  4329,  6174,  2702),
]

# --- TARGET: Sell-through by Price ---
TGT_PRICE = [
    # Price, cnt, avg_st_4m, avg_st_total, pct_nothing, pct_allsold
    ('<15 EUR',    66, 1.10, 2.10,  1.5, 80.3),
    ('15-30',    1202, 0.75, 1.44, 16.1, 64.0),
    ('30-60',   18247, 0.54, 1.10, 25.1, 55.4),
    ('60+ EUR', 22116, 0.64, 1.32, 18.5, 63.0),
]

# --- TARGET: Sell-through by Product concentration ---
TGT_CONC = [
    # Concentration, cnt, avg_st_4m, avg_st_total, pct_nothing, pct_allsold
    ('<=20 stores',   1144, 0.46, 0.89, 38.6, 45.7),
    ('21-100 stores', 9476, 0.49, 0.98, 31.5, 50.0),
    ('100+ stores',  31004, 0.64, 1.32, 17.5, 63.2),
]

# --- Sell-through distribution (overall) ---
ST_DISTRIB = [
    # Bucket, cnt, received_qty, sold_qty, remaining_qty, avg_ml3
    ('Nothing sold (0%)',   8872,  9822,     0, 15898, 1.82),
    ('Low (<30%)',            35,   101,    39,   128, 2.17),
    ('Medium (30-80%)',     7843,  9098,  8374,  8218, 2.09),
    ('High (80-99%)',         19,   120,   167,    24, 3.00),
    ('All sold (100%+)',   24862, 29613, 90689,     0, 2.04),
]

# --- Source backtest data (Pattern x Store) ---
SRC_BACKTEST = [
    # Pattern, Store, skus, current_redist_qty, extra_units_kept, blocked_skus, blocked_qty, oversell_qty
    ('Dead',       'Weak',   4597, 5461,  235,  129,  129,  251),
    ('Dead',       'Mid',    6967, 8633,  334,  189,  189,  607),
    ('Dead',       'Strong', 4061, 5143,  209,  112,  112,  486),
    ('Dying',      'Weak',   1594, 1933,  113,   77,   77,  135),
    ('Dying',      'Mid',    2882, 3505,  170,  117,  117,  302),
    ('Dying',      'Strong', 1951, 2373,   82,   52,   52,  260),
    ('Sporadic',   'Weak',   2003, 2606,   59,   26,   26,  252),
    ('Sporadic',   'Mid',    4176, 5783,  121,   52,   52,  777),
    ('Sporadic',   'Strong', 3712, 5705, 2729,  835,  837,  929),
    ('Consistent', 'Weak',    431,  641,   12,    5,    5,   63),
    ('Consistent', 'Mid',    1164, 1877,  912,  271,  271,  316),
    ('Consistent', 'Strong', 1693, 2898, 2522,  535,  579,  608),
    ('Declining',  'Weak',    219,  294,  223,   99,  100,   74),
    ('Declining',  'Mid',     569,  781, 1110,  383,  427,  190),
    ('Declining',  'Strong',  751, 1121, 1329,  387,  423,  328),
]

# --- Target backtest data ---
TGT_BACKTEST = [
    # ML, Store, cnt, pct_allsold, pct_nothing, received_qty, sold_qty, extra_needed_for_1_remains, avg_extra_per_allsold
    (1, 'Weak',    847, 51.7, 47.1,   876,   642,   620, 1.42),
    (1, 'Mid',    2095, 58.4, 39.8,  2181,  1912,  1844, 1.51),
    (1, 'Strong', 1788, 65.6, 33.3,  1826,  2128,  2098, 1.79),
    (2, 'Weak',   4418, 49.6, 27.3,  4952,  7470,  4585, 2.09),
    (2, 'Mid',   12793, 53.1, 23.7, 14146, 23984, 15207, 2.24),
    (2, 'Strong',14766, 61.8, 17.6, 16140, 33950, 22934, 2.51),
    (3, 'Weak',    504, 76.4,  5.2,  1039,  2967,  1918, 4.98),
    (3, 'Mid',    1866, 77.8,  4.6,  3558, 10990,  7196, 4.96),
    (3, 'Strong', 2554, 81.4,  3.8,  4036, 15226, 10801, 5.19),
]

# --- Proposed decision trees ---
SRC_ML_TREE = {
    # (pattern, store) -> proposed ML (* = 0 for delisted, but A-O/Z-O min 1)
    ('Dead', 'Weak'): 0, ('Dead', 'Mid'): 0, ('Dead', 'Strong'): 1,
    ('Dying', 'Weak'): 0, ('Dying', 'Mid'): 0, ('Dying', 'Strong'): 1,
    ('Sporadic', 'Weak'): 1, ('Sporadic', 'Mid'): 1, ('Sporadic', 'Strong'): 2,
    ('Consistent', 'Weak'): 1, ('Consistent', 'Mid'): 2, ('Consistent', 'Strong'): 3,
    ('Declining', 'Weak'): 2, ('Declining', 'Mid'): 3, ('Declining', 'Strong'): 3,
}

TGT_ML_TREE = {
    # (sales_bucket, store) -> proposed ML
    ('Zero', 'Weak'): 1, ('Zero', 'Mid'): 1, ('Zero', 'Strong'): 2,
    ('Low(1-2)', 'Weak'): 1, ('Low(1-2)', 'Mid'): 2, ('Low(1-2)', 'Strong'): 3,
    ('Med+(3+)', 'Weak'): 2, ('Med+(3+)', 'Mid'): 3, ('Med+(3+)', 'Strong'): 4,
    ('High(ML3=3)', 'Weak'): 3, ('High(ML3=3)', 'Mid'): 4, ('High(ML3=3)', 'Strong'): 5,
}


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS
#
# ############################################################
print("")
print("--- Report 1: Consolidated Findings ---")

# ---- Chart: fig_findings_01.png - Source: Reorder vs Oversell dual heatmap ----
patterns = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
stores = ['Weak', 'Mid', 'Strong']

reorder_data = []
oversell_data = []
for p in patterns:
    rrow = []
    orow = []
    for s in stores:
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        rrow.append(row[3])  # pct_reorder
        orow.append(row[5])  # pct_oversell
    reorder_data.append(rrow)
    oversell_data.append(orow)

reorder_arr = np.array(reorder_data)
oversell_arr = np.array(oversell_data)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Reorder heatmap
sns.heatmap(reorder_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=stores, yticklabels=patterns, ax=axes[0],
            vmin=20, vmax=70, linewidths=1,
            cbar_kws={'label': 'Reorder % (9M total)'})
axes[0].set_title('REORDER Rate by Pattern x Store\n(informational - inbound after redistribution)', fontsize=11)
axes[0].set_ylabel('Sales Pattern (24M)')
axes[0].set_xlabel('Store Strength')

# Right: Oversell heatmap
sns.heatmap(oversell_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=stores, yticklabels=patterns, ax=axes[1],
            vmin=4, vmax=36, linewidths=1,
            cbar_kws={'label': 'Oversell % (9M total)'})
for i in range(len(patterns)):
    for j in range(len(stores)):
        if oversell_data[i][j] > 20:
            axes[1].add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                             edgecolor='#2c3e50', linewidth=3))
axes[1].set_title('OVERSELL Rate by Pattern x Store\n(PRIMARY metric, cells >20% highlighted)', fontsize=11)
axes[1].set_ylabel('Sales Pattern (24M)')
axes[1].set_xlabel('Store Strength')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- Chart: fig_findings_02.png - Store decile line chart ----
deciles = list(range(1, 11))
src_reorder = [26.0, 30.7, 31.6, 34.2, 37.2, 38.8, 39.9, 41.4, 43.7, 44.1]
tgt_allsold = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1]
tgt_nothing = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(deciles, src_reorder, 'o-', color='#e74c3c', linewidth=2, label='Source Reorder %')
axes[0].fill_between(deciles, src_reorder, alpha=0.1, color='#e74c3c')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Reorder Rate by Store Decile')
axes[0].legend()
axes[0].set_xticks(deciles)
for d, v in zip(deciles, src_reorder):
    axes[0].text(d, v + 0.7, f'{v}%', ha='center', fontsize=7)

axes[1].plot(deciles, tgt_allsold, 'o-', color='#27ae60', linewidth=2, label='All Sold (SUCCESS) %')
axes[1].plot(deciles, tgt_nothing, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold (PROBLEM) %')
axes[1].fill_between(deciles, tgt_allsold, alpha=0.1, color='#27ae60')
axes[1].fill_between(deciles, tgt_nothing, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Outcome by Store Decile')
axes[1].legend()
axes[1].set_xticks(deciles)
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_02.png")

# ---- Chart: fig_findings_03.png - Target sell-through by Store x Sales (heatmap) ----
tgt_st_4m = np.array([
    [0.49, 0.37, 0.72],
    [0.50, 0.42, 0.76],
    [0.72, 0.51, 0.89],
])
tgt_pct_nothing = np.array([
    [43.7, 34.6, 12.6],
    [39.3, 28.8, 12.5],
    [31.8, 22.3, 9.0],
])
tgt_pct_allsold = np.array([
    [53.7, 44.4, 67.2],
    [57.2, 48.6, 69.3],
    [66.5, 57.1, 74.7],
])
store_labels = ['Weak', 'Mid', 'Strong']
sales_labels = ['Zero', 'Low(1-2)', 'Med+(3+)']

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Left: sell-through 4M
sns.heatmap(tgt_st_4m, annot=True, fmt='.2f', cmap='RdYlGn',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[0],
            vmin=0.3, vmax=1.0, linewidths=1,
            cbar_kws={'label': 'Sell-through (4M)'})
axes[0].set_title('Target Sell-through Rate (4M)\n(green=high=good)', fontsize=10)
axes[0].set_ylabel('Store Strength')
axes[0].set_xlabel('Sales Bucket (6M)')

# Middle: nothing-sold %
sns.heatmap(tgt_pct_nothing, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[1],
            vmin=5, vmax=45, linewidths=1,
            cbar_kws={'label': 'Nothing sold %'})
axes[1].set_title('Target Nothing-Sold % (PROBLEM)\n(red=high=bad)', fontsize=10)
axes[1].set_ylabel('Store Strength')
axes[1].set_xlabel('Sales Bucket (6M)')

# Right: all-sold %
sns.heatmap(tgt_pct_allsold, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[2],
            vmin=40, vmax=80, linewidths=1,
            cbar_kws={'label': 'All sold %'})
axes[2].set_title('Target All-Sold % (SUCCESS)\n(green=high=good, send more!)', fontsize=10)
axes[2].set_ylabel('Store Strength')
axes[2].set_xlabel('Sales Bucket (6M)')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- Chart: fig_findings_04.png - Target: brand-fit + price + concentration bars ----
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Left: Brand-fit
bf_labels = [r[0] for r in TGT_BRAND_FIT]
bf_nothing = [r[4] for r in TGT_BRAND_FIT]
bf_allsold = [r[5] for r in TGT_BRAND_FIT]
x = np.arange(len(bf_labels))
w = 0.35
axes[0].barh(x - w/2, bf_allsold, w, color='#27ae60', label='All-sold (SUCCESS)')
axes[0].barh(x + w/2, bf_nothing, w, color='#e74c3c', label='Nothing-sold (PROBLEM)')
axes[0].set_yticks(x)
axes[0].set_yticklabels(bf_labels, fontsize=8)
axes[0].set_xlabel('%')
axes[0].set_title('Target: Brand-Store Fit')
axes[0].legend(fontsize=8)
for i, (a, n) in enumerate(zip(bf_allsold, bf_nothing)):
    axes[0].text(a + 0.5, i - w/2, f'{a}%', va='center', fontsize=7, color='#27ae60')
    axes[0].text(n + 0.5, i + w/2, f'{n}%', va='center', fontsize=7, color='#e74c3c')

# Middle: Price
pr_labels = [r[0] for r in TGT_PRICE]
pr_nothing = [r[4] for r in TGT_PRICE]
pr_allsold = [r[5] for r in TGT_PRICE]
x2 = np.arange(len(pr_labels))
axes[1].barh(x2 - w/2, pr_allsold, w, color='#27ae60', label='All-sold')
axes[1].barh(x2 + w/2, pr_nothing, w, color='#e74c3c', label='Nothing-sold')
axes[1].set_yticks(x2)
axes[1].set_yticklabels(pr_labels, fontsize=9)
axes[1].set_xlabel('%')
axes[1].set_title('Target: Price Band')
axes[1].legend(fontsize=8)
for i, (a, n) in enumerate(zip(pr_allsold, pr_nothing)):
    axes[1].text(a + 0.5, i - w/2, f'{a}%', va='center', fontsize=7, color='#27ae60')
    axes[1].text(n + 0.5, i + w/2, f'{n}%', va='center', fontsize=7, color='#e74c3c')

# Right: Concentration
co_labels = [r[0] for r in TGT_CONC]
co_nothing = [r[4] for r in TGT_CONC]
co_allsold = [r[5] for r in TGT_CONC]
x3 = np.arange(len(co_labels))
axes[2].barh(x3 - w/2, co_allsold, w, color='#27ae60', label='All-sold')
axes[2].barh(x3 + w/2, co_nothing, w, color='#e74c3c', label='Nothing-sold')
axes[2].set_yticks(x3)
axes[2].set_yticklabels(co_labels, fontsize=9)
axes[2].set_xlabel('%')
axes[2].set_title('Target: Product Concentration')
axes[2].legend(fontsize=8)
for i, (a, n) in enumerate(zip(co_allsold, co_nothing)):
    axes[2].text(a + 0.5, i - w/2, f'{a}%', va='center', fontsize=7, color='#27ae60')
    axes[2].text(n + 0.5, i + w/2, f'{n}%', va='center', fontsize=7, color='#e74c3c')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- BUILD HTML: Report 1 ----

# Build source table rows (BOTH reorder + oversell always)
src_table_rows = ""
for r in SRC_DATA:
    pat, sto, cnt, pr, rq, po, oq, rdq, rec = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
    cls_r = 'bad' if pr > 50 else ('warn' if pr > 40 else '')
    rec_cls = 'bad' if 'RAISE' in rec else ('good' if 'LOWER' in rec else '')
    src_table_rows += (
        f'<tr><td>{pat}</td><td>{sto}</td><td>{cnt:,}</td>'
        f'<td class="{cls_r}">{pr}%</td><td>{rq:,}</td>'
        f'<td class="{cls_o}">{po}%</td><td>{oq:,}</td>'
        f'<td>{rdq:,}</td>'
        f'<td class="{rec_cls}">{rec}</td></tr>\n'
    )

# Build target store x sales table rows
tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sto, sal, cnt, st4, stt, pn, pa, rqty, sqty = r
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 50 else 'bad')
    dir_tag = ''
    if pn > 30:
        dir_tag = '<span class="bad">ML DOWN</span>'
    elif pa > 65 and stt > 1.0:
        dir_tag = '<span class="good">ML UP</span>'
    else:
        dir_tag = 'OK'
    tgt_ss_rows += (
        f'<tr><td>{sto}</td><td>{sal}</td><td>{cnt:,}</td>'
        f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
        f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td>'
        f'<td>{rqty:,}</td><td>{sqty:,}</td>'
        f'<td>{dir_tag}</td></tr>\n'
    )

# Build target brand-fit table rows
tgt_bf_rows = ""
for r in TGT_BRAND_FIT:
    fit, cnt, st4, stt, pn, pa, rqty, sqty, rem = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 20 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 55 else 'bad')
    tgt_bf_rows += (
        f'<tr><td>{fit}</td><td>{cnt:,}</td>'
        f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
        f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td>'
        f'<td>{rqty:,}</td><td>{sqty:,}</td><td>{rem:,}</td></tr>\n'
    )

# Build target price table rows
tgt_pr_rows = ""
for r in TGT_PRICE:
    pr, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 20 else ('warn' if pn > 15 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 55 else 'bad')
    tgt_pr_rows += (
        f'<tr><td>{pr}</td><td>{cnt:,}</td>'
        f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
        f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n'
    )

# Build target concentration table rows
tgt_co_rows = ""
for r in TGT_CONC:
    co, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 50 else 'bad')
    tgt_co_rows += (
        f'<tr><td>{co}</td><td>{cnt:,}</td>'
        f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
        f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n'
    )

# Build sell-through distribution rows
st_dist_rows = ""
for r in ST_DISTRIB:
    bkt, cnt, rqty, sqty, rem, aml = r
    if bkt.startswith('Nothing'):
        cls = 'bad'
    elif bkt.startswith('All'):
        cls = 'good'
    else:
        cls = ''
    st_dist_rows += (
        f'<tr><td class="{cls}">{bkt}</td><td>{cnt:,}</td>'
        f'<td>{rqty:,}</td><td>{sqty:,}</td><td>{rem:,}</td><td>{aml:.2f}</td></tr>\n'
    )

# Totals for overview
total_src_skus = sum(r[2] for r in SRC_DATA)
total_redist_qty = sum(r[7] for r in SRC_DATA)
total_oversell_qty = sum(r[6] for r in SRC_DATA)
total_reorder_qty = sum(r[4] for r in SRC_DATA)
total_tgt_cnt = sum(r[2] for r in TGT_STORE_SALES)
total_tgt_received = sum(r[7] for r in TGT_STORE_SALES)
total_tgt_sold = sum(r[8] for r in TGT_STORE_SALES)

html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Consolidated Findings: SalesBased MinLayers - Calc 233</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings: SalesBased MinLayers - Calc 233</h1>
<p><b>CalculationId=233</b> | EntityListId=3 | Calculation date: 2025-07-13 | Monitoring: to 2026-03-22 | Generated: {NOW_STR}</p>

<!-- ========== SECTION 1: OVERVIEW ========== -->
<div class="section">
<h2>1. Overview</h2>

<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">36,770</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">41,631</div><div class="l">Target SKU</div></div>
<div class="metric"><div class="v">48,754</div><div class="l">Total redistributed pcs</div></div>
</div>

<h3>Source: Overall metrics (SKU + quantity) - 4M and total</h3>
<table>
<tr><th>Metric</th><th colspan="2">4 months</th><th colspan="2">Total (~9M)</th></tr>
<tr><th></th><th>SKU (%)</th><th>Qty (pcs)</th><th>SKU (%)</th><th>Qty (pcs)</th></tr>
<tr><td style="text-align:left"><b>Total redistributed</b></td><td>36,770</td><td>48,754</td><td>36,770</td><td>48,754</td></tr>
<tr><td style="text-align:left"><b>Reorder</b> (any inbound)</td><td>7,087 (19.3%)</td><td>7,980 (16.4%)</td><td>13,841 (37.6%)</td><td>16,615 (34.1%)</td></tr>
<tr><td style="text-align:left"><b>Oversell</b> (sales-based)</td><td>1,317 (3.6%)</td><td>1,464 (3.0%)</td><td>4,718 (12.8%)</td><td>5,578 (11.4%)</td></tr>
</table>

<h3>Target: Overall metrics (SKU + quantity) - 4M and total</h3>
<p><b>Sell-through formula:</b> LEAST(QuantitySold, SupplyBefore + QtyRedistributed) / (SupplyBefore + QtyRedistributed) -- capped at 100%</p>
<table>
<tr><th>Metric</th><th colspan="2">4 months</th><th colspan="2">Total (~9M)</th></tr>
<tr><th></th><th>SKU (%)</th><th>Qty (pcs)</th><th>SKU (%)</th><th>Qty (pcs)</th></tr>
<tr><td style="text-align:left"><b>Total supply</b> (pre + redist)</td><td colspan="2">81,196</td><td colspan="2">81,196</td></tr>
<tr><td style="text-align:left"><b>Capped sold</b></td><td>-</td><td>37,577</td><td>-</td><td>56,928</td></tr>
<tr style="background:#d4edda"><td style="text-align:left"><b>Sell-through</b></td><td colspan="2"><b>46.3%</b></td><td colspan="2"><b>70.1%</b></td></tr>
<tr><td style="text-align:left"><b>All sold</b> (SUCCESS)</td><td class="good">13,631 (32.7%)</td><td>-</td><td class="good">24,862 (59.7%)</td><td>-</td></tr>
<tr><td style="text-align:left"><b>Nothing sold</b> (PROBLEM)</td><td class="bad">17,552 (42.2%)</td><td>-</td><td class="bad">8,872 (21.3%)</td><td>-</td></tr>
<tr><td style="text-align:left"><b>Remaining stock</b></td><td>-</td><td>43,619</td><td>-</td><td>24,268</td></tr>
</table>

<h3>All metrics by MinLayer</h3>
<p>Oversell targets: 4M: <b>5-10%</b> | total: <b>&lt;20%</b>. Goal is NOT zero reorder.</p>

<table>
<tr><th rowspan="2">ML</th><th rowspan="2">SKU</th><th colspan="2">Reorder (inbound)</th><th colspan="2">Oversell (sales)</th><th rowspan="2">Redist qty</th><th rowspan="2">Status</th></tr>
<tr><th>4M % (qty)</th><th>Total % (qty)</th><th>4M % (qty)</th><th>Total % (qty)</th></tr>
<tr><td>0</td><td>1,709</td><td>3.3% (66)</td><td>6.3% (121)</td><td class="good">1.1% (20)</td><td class="good">2.3% (43)</td><td>2,061</td><td class="good">OK</td></tr>
<tr><td>1</td><td>31,965</td><td>19.6% (6,883)</td><td>38.0% (13,978)</td><td class="good">3.6% (1,241)</td><td class="good">12.5% (4,564)</td><td>40,598</td><td class="good">OK</td></tr>
<tr><td>2</td><td>2,680</td><td>25.6% (890)</td><td>52.3% (2,052)</td><td class="warn">5.1% (180)</td><td class="bad">22.2% (812)</td><td>4,716</td><td class="bad">EXCEEDS</td></tr>
<tr><td>3</td><td>416</td><td>16.6% (141)</td><td>46.9% (464)</td><td class="good">3.4% (23)</td><td class="good">18.0% (159)</td><td>1,379</td><td class="good">OK (tight)</td></tr>
<tr style="font-weight:bold;background:#e8e8e8"><td>ALL</td><td>36,770</td><td>19.3% (7,980)</td><td>37.6% (16,615)</td><td>3.6% (1,464)</td><td>12.8% (5,578)</td><td>48,754</td><td>-</td></tr>
</table>

<div class="insight-good">
<b>Key takeaway:</b> Oversell (sales-based) is much lower than reorder (inbound-based): 12.8% vs 37.6% SKU, 11.4% vs 34.1% qty.
Reorder includes purchases unrelated to redistribution. <b>Oversell is the true impact metric.</b>
At 4M: oversell is only 3.6% (target 5-10%) - already well within target.
At total: 12.8% (target &lt;20%) - also within target overall. Only ML2 (22.2%) exceeds.
</div>
</div>

<!-- ========== SECTION 2: SOURCE ANALYSIS - PATTERNS ========== -->
<div class="section">
<h2>2. Source: Sales Patterns (24M) - primary predictor</h2>

<p>Analysis of 24-month sales history revealed 5 patterns that strongly predict oversell risk after redistribution.
<b>Both reorder and oversell are shown side by side in every table</b> - they are different metrics and must not be mixed.</p>

<h3>2.1 All 15 segments: Pattern x Store (BOTH reorder + oversell)</h3>
<img src="fig_findings_01.png">

<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th>
<th>Reorder %</th><th>Reorder qty</th>
<th>Oversell %</th><th>Oversell qty</th>
<th>Redist qty</th><th>Recommendation</th></tr>
{src_table_rows}
<tr style="font-weight:bold; background:#e8e8e8;">
<td colspan="2">TOTAL</td><td>{total_src_skus:,}</td>
<td>-</td><td>{total_reorder_qty:,}</td>
<td>-</td><td>{total_oversell_qty:,}</td>
<td>{total_redist_qty:,}</td><td>-</td></tr>
</table>

<div class="insight-bad">
<b>MUST RAISE ML (oversell &gt;20%):</b> Sporadic+Strong (20.1%), Consistent+Mid (22.7%), Consistent+Strong (28.0%),
Declining+Weak (25.1%), Declining+Mid (28.3%), Declining+Strong (35.4%). These 6 segments need higher source MinLayer.
</div>

<div class="insight-good">
<b>CAN LOWER ML (oversell &lt;10%):</b> Dead+Weak (5.1%), Dead+Mid (7.8%), Dying+Weak (8.1%), Dying+Mid (9.7%).
These 4 segments are safe enough to be MORE aggressive (lower ML = take more stock). This means ML can go to 0
for delisted items, while A-O/Z-O business rule enforces minimum 1.
</div>

<div class="insight">
<b>Key insight:</b> Reorder is always higher than oversell (e.g., Dead+Weak: 24.5% reorder vs 5.1% oversell).
Reorder includes ALL inbound (purchases, transfers) which may be unrelated to redistribution.
Oversell is the TRUE metric - only counts sales that exceeded remaining stock.
</div>
</div>

<!-- ========== SECTION 3: SOURCE - STORE STRENGTH ========== -->
<div class="section">
<h2>3. Source: Store Strength</h2>

<img src="fig_findings_02.png">

<p>Store strength (measured by sales decile) has linear impact on both sides of redistribution:</p>

<table>
<tr><th>Metric</th><th>Decile 1 (Weak)</th><th>Decile 10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Reorder %</td><td>26%</td><td>44%</td><td>Linear growth: stronger stores = more reorders</td></tr>
<tr><td>Source Oversell %</td><td>~8%</td><td>~25%</td><td>Strong stores sell more = higher oversell risk</td></tr>
<tr><td>Target All-Sold (SUCCESS)</td><td class="good">48%</td><td class="good">70%</td><td>Stronger stores sell all redistributed goods</td></tr>
<tr><td>Target Nothing-Sold (PROBLEM)</td><td class="bad">32%</td><td class="good">14%</td><td>Weaker stores = more "stuck" goods</td></tr>
</table>

<div class="insight">
<b>Implication for ML:</b> Strong source stores need HIGHER ML (they will sell even after redistribution).
Strong target stores need HIGHER ML too (they sell everything = need more stock to keep 1 remaining).
Weak source stores can have LOWER ML (safe to take more). Weak target stores need LOWER ML (goods don't sell there).
</div>
</div>

<!-- ========== SECTION 4: SOURCE - MONTHLY CADENCE ========== -->
<div class="section">
<h2>4. Source: Monthly Sales Cadence</h2>

<table>
<tr><th>Months with sales (24M)</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg MinLayer</th><th>Note</th></tr>
<tr><td>0M</td><td>15,384</td><td>28.5%</td><td>8.3%</td><td>0.94</td><td>No sales = low oversell, safe</td></tr>
<tr><td>1M</td><td>8,022</td><td>35.5%</td><td>~12%</td><td>1.00</td><td>Single month of sales</td></tr>
<tr><td>3M</td><td>2,635</td><td>47.8%</td><td>~18%</td><td>1.10</td><td>Sporadic sales</td></tr>
<tr><td>6M</td><td>805</td><td>57.3%</td><td>~22%</td><td>1.20</td><td>Regular sales</td></tr>
<tr><td>10M</td><td>258</td><td>67.1%</td><td>~28%</td><td>1.50</td><td>Frequent sales</td></tr>
<tr><td>16M</td><td>58</td><td>81.0%</td><td>~35%</td><td>1.86</td><td>Near-constant sales</td></tr>
</table>

<div class="insight-bad">
<b>MinLayer grows TOO SLOWLY:</b> Product with 16 months of sales (out of 24M) has average ML only 1.86, but 81% reorder!
Current heuristic does not adequately respond to sales frequency. Monthly cadence is captured in the Pattern classification.
</div>
</div>

<!-- ========== SECTION 5: TARGET ANALYSIS (EQUALLY DETAILED) ========== -->
<div class="section">
<h2>5. Target Analysis: Sell-through Rate (primary target metric)</h2>

<p><b>Sell-through = SalesTotal_Post / (TargetSupplyAtCalc + TotalQtyReceived).</b>
This is the PRIMARY target metric - how much of total available stock was actually sold.</p>

<h3>5.1 Sell-through Distribution</h3>
<table>
<tr><th>Bucket</th><th>SKU</th><th>Received qty</th><th>Sold qty</th><th>Remaining qty</th><th>Avg ML3</th></tr>
{st_dist_rows}
</table>

<div class="insight-good">
<b>All sold (100%+) = SUCCESS:</b> 24,862 SKU (59.7%) sold EVERYTHING. This is NOT a problem - it's a signal to
send MORE next time (increase target ML so that 1 piece remains after sales).
</div>
<div class="insight-bad">
<b>Nothing sold (0%) = PROBLEM:</b> 8,872 SKU (21.3%) sold NOTHING. Wasted redistribution.
Target ML should be LOWERED for these segments.
</div>

<h3>5.2 By Store Strength x Sales Bucket</h3>
<img src="fig_findings_03.png">

<table>
<tr><th>Store</th><th>Sales</th><th>SKU</th><th>ST 4M</th><th>ST Total</th>
<th>Nothing %</th><th>All-sold %</th><th>Received</th><th>Sold</th><th>Direction</th></tr>
{tgt_ss_rows}
</table>

<div class="insight">
<b>Strong + Med+ stores:</b> sell-through 1.83 (total), 74.7% all-sold, only 9.0% nothing-sold. These are BEST targets. ML should be INCREASED.<br>
<b>Weak + Zero stores:</b> sell-through 0.76, 43.7% nothing-sold. These are WORST targets. ML should be DECREASED.
</div>

<h3>5.3 By Brand-Store Fit</h3>
<table>
<tr><th>Fit</th><th>SKU</th><th>ST 4M</th><th>ST Total</th>
<th>Nothing %</th><th>All-sold %</th><th>Received</th><th>Sold</th><th>Remaining</th></tr>
{tgt_bf_rows}
</table>

<div class="insight">
<b>Strong+Strong brand:</b> ST=1.43, 65.7% all-sold, only 16.5% nothing. BEST combination, ML can be higher.<br>
<b>Weak+Weak brand:</b> ST=0.90, 50.3% all-sold, 30.7% nothing. WORST combination, ML should be lower.
Difference: 15.4pp in all-sold, 14.2pp in nothing-sold!
</div>

<h3>5.4 By Price Band</h3>
<table>
<tr><th>Price</th><th>SKU</th><th>ST 4M</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tgt_pr_rows}
</table>

<h3>5.5 By Product Concentration</h3>
<table>
<tr><th>Concentration</th><th>SKU</th><th>ST 4M</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tgt_co_rows}
</table>

<img src="fig_findings_04.png">

<div class="insight">
<b>Product concentration matters:</b> Products on 100+ stores have 63.2% all-sold and only 17.5% nothing.
Products on &lt;=20 stores: 45.7% all-sold, 38.6% nothing. Widely distributed products are safer targets.
</div>
</div>

<!-- ========== SECTION 6: PAIR ANALYSIS ========== -->
<div class="section">
<h2>6. Pair Analysis (Source + Target combined)</h2>

<table>
<tr><th>Pair outcome</th><th>Description</th><th>Count</th><th>Share</th></tr>
<tr><td class="good">BEST</td><td>Source OK (no reorder) + Target all sold</td><td>14,896</td><td>35.1%</td></tr>
<tr><td class="good">IDEAL</td><td>Source OK + Target partially sold</td><td>4,923</td><td>11.6%</td></tr>
<tr><td class="warn">SRC FAIL</td><td>Source reordered, but Target sold</td><td>13,530</td><td>31.9%</td></tr>
<tr><td class="bad">WASTED</td><td>Source OK, but Target sold nothing</td><td>6,274</td><td>14.8%</td></tr>
<tr><td class="bad">DOUBLE FAIL</td><td>Source reordered + Target sold nothing</td><td>2,781</td><td>6.6%</td></tr>
</table>

<div class="insight-good">
<b>Target success rate: 78.6%</b> - most redistributed goods sell (at least partially) on the target store.
</div>

<h3>Flow direction and double-fail rate</h3>
<table>
<tr><th>Flow direction</th><th>Double Fail %</th><th>Rating</th></tr>
<tr><td>Weak -&gt; Strong</td><td class="good">2.8%</td><td>Best direction</td></tr>
<tr><td>Mid -&gt; Strong</td><td class="good">3.9%</td><td>Good direction</td></tr>
<tr><td>Strong -&gt; Strong</td><td>5.1%</td><td>Acceptable</td></tr>
<tr><td>Mid -&gt; Mid</td><td>5.8%</td><td>Average</td></tr>
<tr><td>Strong -&gt; Weak</td><td class="bad">10.6%</td><td>Worst direction</td></tr>
</table>
</div>

<!-- ========== SECTION 7: PROMO/PRICE + CHRISTMAS ========== -->
<div class="section">
<h2>7. Promo, Price, and Christmas Effects</h2>

<h3>Promo share and oversell</h3>
<p>Declining sales pattern is <b>NOT caused by promotions</b> - promo share (~30%) is the same as other patterns.</p>

<table>
<tr><th>Promo share</th><th>Oversell %</th><th>Note</th></tr>
<tr><td>0% (no promo)</td><td>14.2%</td><td>Baseline</td></tr>
<tr><td>1-20% promo</td><td class="bad">34.4%</td><td>HIGHEST oversell</td></tr>
<tr><td>20-50% promo</td><td>29.1%</td><td>Above average</td></tr>
<tr><td>&gt;50% promo</td><td>27.8%</td><td>High but lower than 1-20%</td></tr>
</table>

<h3>Christmas seasonality</h3>
<table>
<tr><th>Xmas sales share</th><th>Oversell %</th><th>Description</th></tr>
<tr><td>0-5% (non-seasonal)</td><td>16.0%</td><td>Standard products</td></tr>
<tr><td>5-20% (mildly seasonal)</td><td>20.1%</td><td>Mild Xmas effect</td></tr>
<tr><td>20-60% (seasonal)</td><td class="bad">25-27%</td><td>Significant Xmas boost</td></tr>
<tr><td>&gt;60% (pure Xmas)</td><td>18.8%</td><td>Sells mainly at Xmas</td></tr>
</table>

<div class="insight">
<b>Riskiest segment: 20-60% Xmas share</b> - year-round sellers that get a Xmas boost.
After redistribution (outside Xmas), they sell slower than expected.
Pure Xmas products (&gt;60%) paradoxically have lower oversell (18.8%) because they simply don't sell outside season.
</div>
</div>

<!-- ========== SECTION 8: OTHER FACTORS ========== -->
<div class="section">
<h2>8. Other Factors</h2>

<h3>Redistribution loop</h3>
<p>3,117 SKU (8.5%) were <b>re-redistributed</b> (Y-STORE TRANSFER). 72% of them are zero-sellers with ML1.
This indicates some products are cyclically moved without being sold.</p>

<h3>SkuClass delisting</h3>
<p>Delisted source SKU have <b>29pp lower reorder</b> (13.2% vs 42.7%).
For delisted products, redistribution is safe - MinLayer can be 0.</p>

<h3>Brand-Store fit (source perspective)</h3>
<table>
<tr><th>Combination</th><th>Reorder %</th><th>Oversell %</th><th>Difference from avg</th></tr>
<tr><td>Strong brand + Strong store</td><td class="bad">45.3%</td><td class="bad">~25%</td><td>+16pp reorder</td></tr>
<tr><td>Weak brand + Weak store</td><td class="good">29.3%</td><td class="good">~10%</td><td>-8pp reorder</td></tr>
</table>
</div>

<!-- ========== SECTION 9: SUMMARY TABLE ========== -->
<div class="section">
<h2>9. Summary of ALL Factors with Direction Arrows</h2>

<p>This table shows all analyzed factors and their impact on BOTH source and target MinLayer.</p>

<table>
<tr><th>Factor</th><th>Impact (metric)</th>
<th>Source ML direction</th><th>Target ML direction</th>
<th>Size</th><th>Priority</th></tr>

<tr><td>Sales Pattern: Declining</td><td>Oversell 35.4% (Strong)</td>
<td class="bad">SOURCE UP (raise ML)</td><td>-</td>
<td class="bad">+27pp vs Dead</td><td>1 - Primary</td></tr>

<tr><td>Sales Pattern: Dead/Dying + Weak</td><td>Oversell 5-8%</td>
<td class="good">SOURCE DOWN (lower ML)</td><td>-</td>
<td class="good">Safe, under target</td><td>1 - Primary</td></tr>

<tr><td>Store Strength (source)</td><td>Strong 44% vs Weak 26% reorder</td>
<td class="bad">SOURCE UP for strong</td><td>-</td>
<td class="bad">+18pp</td><td>1 - Primary</td></tr>

<tr><td>Store Strength (target)</td><td>Strong 74.7% all-sold</td>
<td>-</td><td class="good">TARGET UP for strong</td>
<td class="good">Send more to strong stores</td><td>1 - Primary</td></tr>

<tr><td>Target sell-through: Weak+Zero</td><td>43.7% nothing-sold</td>
<td>-</td><td class="bad">TARGET DOWN</td>
<td class="bad">Send less to weak stores</td><td>1 - Primary</td></tr>

<tr><td>Brand-Store Fit: Strong+Strong</td><td>65.7% all-sold target</td>
<td class="bad">SOURCE UP (+1 modifier)</td><td class="good">TARGET UP (+1)</td>
<td>+16pp reorder, +15pp all-sold</td><td>2 - Secondary</td></tr>

<tr><td>Product Concentration (100+)</td><td>42.9% source reorder, 63.2% tgt all-sold</td>
<td class="bad">SOURCE UP (+1)</td><td class="good">TARGET UP (+1)</td>
<td>+25.9pp reorder</td><td>2 - Secondary</td></tr>

<tr><td>Product Concentration (&lt;=20)</td><td>17% reorder, 38.6% nothing-sold</td>
<td class="good">SOURCE DOWN (safe)</td><td class="bad">TARGET DOWN</td>
<td>Niche product, fewer stores</td><td>2 - Secondary</td></tr>

<tr><td>SkuClass Delisting</td><td>13.2% vs 42.7% reorder</td>
<td class="good">SOURCE = 0 (override)</td><td>-</td>
<td class="good">-29.5pp</td><td>1 - Override</td></tr>

<tr><td>Xmas Seasonality (20-60%)</td><td>25-27% oversell</td>
<td class="bad">SOURCE UP (+1)</td><td>-</td>
<td class="warn">+9-11pp</td><td>3 - Modifier</td></tr>

<tr><td>Redist. Loop</td><td>8.5% SKU re-redistributed</td>
<td colspan="2">Monitoring signal</td>
<td class="warn">Indicator</td><td>3 - Monitoring</td></tr>
</table>

<div class="insight">
<b>4 directions for ML adjustment:</b>
<ul>
<li><b>SOURCE UP:</b> Declining pattern, strong store, high concentration, brand-fit strong+strong, Xmas seasonal</li>
<li><b>SOURCE DOWN:</b> Dead/Dying on weak/mid store, delisted, low concentration = safe to take more</li>
<li><b>TARGET UP:</b> Strong store + Med+ sales (high sell-through, high all-sold) = send more</li>
<li><b>TARGET DOWN:</b> Weak store + Zero/Low sales (high nothing-sold, low sell-through) = send less</li>
</ul>
See <a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> for concrete rules.
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3</i></p>
</body>
</html>"""

with open(os.path.join(REPORTS_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  [OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE
#
# ############################################################
print("")
print("--- Report 2: Decision Tree ---")

# ---- Chart: fig_dtree_01.png - Source ML matrix heatmap (with 0*) ----
src_ml_matrix = np.array([
    [0, 0, 1],
    [0, 0, 1],
    [1, 1, 2],
    [1, 2, 3],
    [2, 3, 3],
])
patterns_dt = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
stores_dt = ['Weak', 'Mid', 'Strong']

fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(src_ml_matrix, annot=False, cmap='YlOrRd',
            xticklabels=stores_dt, yticklabels=patterns_dt, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer'})
ax.set_title('Source MinLayer: Lookup Table\n(Sales Pattern 24M x Store Strength)\n* = 0 for delisted, but A-O/Z-O minimum 1', fontsize=11)
ax.set_ylabel('Sales Pattern (24M)')
ax.set_xlabel('Store Strength')
# Annotate with text including * for zero cells
star_cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
for i in range(len(patterns_dt)):
    for j in range(len(stores_dt)):
        val = src_ml_matrix[i][j]
        star = '*' if (i, j) in star_cells else ''
        color = 'white' if val >= 2 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={val}{star}', ha='center', va='center',
                fontsize=11, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_01.png")

# ---- Chart: fig_dtree_02.png - Target ML matrix heatmap ----
tgt_ml_labels = ['Zero', 'Low (1-2)', 'Med+ (3+)', 'High (ML3=3)']
tgt_ml_matrix = np.array([
    [1, 1, 2],
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5],
])

fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(tgt_ml_matrix, annot=False, cmap='YlGnBu',
            xticklabels=stores_dt, yticklabels=tgt_ml_labels, ax=ax,
            vmin=0, vmax=5, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Target MinLayer'})
ax.set_title('Target MinLayer: Lookup Table\n(Sales Bucket x Store Strength)\nHigher ML = send more to stores that sell well', fontsize=11)
ax.set_ylabel('Sales Bucket')
ax.set_xlabel('Store Strength')
for i in range(len(tgt_ml_labels)):
    for j in range(len(stores_dt)):
        val = tgt_ml_matrix[i][j]
        color = 'white' if val >= 3 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={val}', ha='center', va='center',
                fontsize=12, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_02.png")

# ---- Chart: fig_dtree_03.png - 4-direction decision diagram ----
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('4-Direction MinLayer Decision Framework', fontsize=14, fontweight='bold', pad=20)


def draw_box(ax, x, y, w, h, text, color='#ecf0f1', border='#2c3e50', fontsize=8):
    rect = plt.Rectangle((x - w / 2, y - h / 2), w, h,
                          facecolor=color, edgecolor=border, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, zorder=3,
            multialignment='center')


def draw_arrow(ax, x1, y1, x2, y2, text='', color='#7f8c8d'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5), zorder=1)
    if text:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 1, my, text, fontsize=7, color=color)


# Center label
draw_box(ax, 50, 55, 20, 6, 'MinLayer\nDecision', '#3498db', fontsize=10)

# Source UP (top-left, red)
draw_box(ax, 22, 82, 28, 12,
         'SOURCE ML UP\n(raise MinLayer)\n\nDecl+Strong: ML=3 (was 1)\nCons+Strong: ML=3 (was 2)\nSporad+Strong: ML=2 (was 1)\nXmas seasonal: +1\nBrand-fit strong+strong: +1\nConcentration 100+: +1',
         '#fce4e4', '#e74c3c', fontsize=7)
draw_arrow(ax, 42, 58, 30, 76, 'Oversell >20%', '#e74c3c')

# Source DOWN (top-right, green)
draw_box(ax, 78, 82, 28, 12,
         'SOURCE ML DOWN\n(lower MinLayer = more aggressive)\n\nDead+Weak: ML=0* (was 1)\nDead+Mid: ML=0* (was 1)\nDying+Weak: ML=0* (was 1)\nDying+Mid: ML=0* (was 1)\nDelisted: ML=0 (override)\n* A-O/Z-O min 1',
         '#d4edda', '#27ae60', fontsize=7)
draw_arrow(ax, 58, 58, 70, 76, 'Oversell <10%', '#27ae60')

# Target UP (bottom-left, green)
draw_box(ax, 22, 28, 28, 12,
         'TARGET ML UP\n(send more stock)\n\nStrong+Med+: ML=4 (high ST)\nStrong+Low: ML=3\nStrong+Zero: ML=2\nStrong brand fit: +1\nConcentration 100+: higher ST\n\nAll-sold = SUCCESS = send more!',
         '#d4edda', '#27ae60', fontsize=7)
draw_arrow(ax, 42, 52, 30, 34, 'High sell-through', '#27ae60')

# Target DOWN (bottom-right, red)
draw_box(ax, 78, 28, 28, 12,
         'TARGET ML DOWN\n(send less stock)\n\nWeak+Zero: ML=1 (43.7% nothing)\nWeak+Low: ML=1 (34.6% nothing)\nWeak brand fit: -1\nConcentration <=20: -1\n\nNothing-sold = PROBLEM = send less!',
         '#fce4e4', '#e74c3c', fontsize=7)
draw_arrow(ax, 58, 52, 70, 34, 'Low sell-through', '#e74c3c')

# Labels
ax.text(50, 96, 'SOURCE side (how much to keep at source)', fontsize=10, ha='center',
        fontweight='bold', color='#2c3e50')
ax.text(50, 16, 'TARGET side (how much to send to target)', fontsize=10, ha='center',
        fontweight='bold', color='#2c3e50')
ax.text(3, 55, 'RAISE ML', fontsize=9, ha='center', rotation=90, color='#e74c3c', fontweight='bold')
ax.text(97, 55, 'LOWER ML', fontsize=9, ha='center', rotation=90, color='#27ae60', fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- BUILD HTML: Report 2 ----

# Build source rule table
src_rule_rows = ""
for p in patterns:
    for s in stores:
        key = (p, s)
        ml = SRC_ML_TREE[key]
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        pct_o = row[5]
        pct_r = row[3]
        rec = row[8]
        star = '*' if ml == 0 and p in ('Dead', 'Dying') else ''
        if 'RAISE' in rec:
            cls = 'dir-up'
            dir_text = 'UP'
        elif 'LOWER' in rec:
            cls = 'dir-down'
            dir_text = 'DOWN'
        else:
            cls = ''
            dir_text = 'OK'
        src_rule_rows += (
            f'<tr class="{cls}"><td>{p}</td><td>{s}</td>'
            f'<td>{pct_r}%</td><td>{pct_o}%</td>'
            f'<td><b>{ml}{star}</b></td>'
            f'<td>{rec}</td><td>{dir_text}</td></tr>\n'
        )

# Build target rule table
tgt_rule_rows = ""
for sal in ['Zero', 'Low(1-2)', 'Med+(3+)']:
    for sto in stores:
        r = [x for x in TGT_STORE_SALES if x[0] == sto and x[1] == sal][0]
        key_ml = (sal, sto)
        ml = TGT_ML_TREE.get(key_ml, '?')
        pn = r[5]
        pa = r[6]
        st_t = r[4]
        if pa > 65 and st_t > 1.0:
            dir_text = 'UP (send more)'
            cls = 'dir-up' if False else ''  # UP for target = green (good)
            cls = 'dir-down'  # green background
        elif pn > 30:
            dir_text = 'DOWN (send less)'
            cls = 'dir-up'  # red background for problem
        else:
            dir_text = 'OK'
            cls = ''
        tgt_rule_rows += (
            f'<tr class="{cls}"><td>{sal}</td><td>{sto}</td>'
            f'<td>{st_t:.2f}</td><td>{pa}%</td><td>{pn}%</td>'
            f'<td><b>{ml}</b></td><td>{dir_text}</td></tr>\n'
        )

# Add High row
for sto in stores:
    key_ml = ('High(ML3=3)', sto)
    ml = TGT_ML_TREE.get(key_ml, '?')
    tgt_rule_rows += (
        f'<tr class="dir-down"><td>High (ML3=3)</td><td>{sto}</td>'
        f'<td>&gt;1.5</td><td>&gt;75%</td><td>&lt;5%</td>'
        f'<td><b>{ml}</b></td><td>UP (send more)</td></tr>\n'
    )

html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Decision Tree: MinLayer Rules 0-5</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree: MinLayer Rules 0-5</h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>This report defines concrete rules for MinLayer settings based on analytics from
<a href="consolidated_findings.html">Report 1: Consolidated Findings</a>.
The tree has <b>4 directions</b>: source up, source down, target up, target down.</p>

<!-- ========== 4-DIRECTION OVERVIEW ========== -->
<div class="section">
<h2>1. Four-Direction Framework</h2>

<img src="fig_dtree_03.png">

<table>
<tr><th>Direction</th><th>When</th><th>Action</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>SOURCE ML UP</b></td><td>Oversell &gt;20%</td><td>Keep more at source</td>
<td>Products still selling at source, redistribution causes oversell</td></tr>
<tr class="dir-down"><td><b>SOURCE ML DOWN</b></td><td>Oversell &lt;10%</td><td>Take more from source (be more aggressive)</td>
<td>Products NOT selling at source, safe to take more</td></tr>
<tr class="dir-down"><td><b>TARGET ML UP</b></td><td>High sell-through, high all-sold</td><td>Send more to target</td>
<td>Target sells everything = success, but need 1 remaining. Send more next time.</td></tr>
<tr class="dir-up"><td><b>TARGET ML DOWN</b></td><td>Low sell-through, high nothing-sold</td><td>Send less to target</td>
<td>Target doesn't sell = wasted redistribution. Send less next time.</td></tr>
</table>
</div>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>2. Source Rules (with CAN LOWER and MUST RAISE)</h2>

<h3>2.1 Lookup Table: Pattern x Store</h3>
<img src="fig_dtree_01.png">

<table>
<tr><th>Pattern</th><th>Store</th><th>Reorder %</th><th>Oversell %</th><th>Proposed ML</th><th>Recommendation</th><th>Direction</th></tr>
{src_rule_rows}
</table>

<p><b>* = 0 for delisted items, but business rule: A-O (SkuClass 9) and Z-O (SkuClass 11) minimum ML=1.</b></p>

<div class="insight-good">
<b>CAN LOWER ML (source down):</b> Dead+Weak (5.1%), Dead+Mid (7.8%), Dying+Weak (8.1%), Dying+Mid (9.7%).
Proposed ML=0* means delisted items get ML=0, active items get ML=1 (business rule).
This frees up ~16,040 SKU for more aggressive redistribution.
</div>

<div class="insight-bad">
<b>MUST RAISE ML (source up):</b> 6 segments with oversell &gt;20%.
Declining+Strong goes from ML~1.1 to ML=3, Consistent+Strong from ML~2 to ML=3.
This protects ~7,889 SKU from excessive oversell.
</div>

<h3>2.2 Business Rules (Overrides)</h3>
<table>
<tr><th>Rule</th><th>Condition</th><th>MinLayer</th><th>Reason</th></tr>
<tr><td>Active orderable</td><td>SkuClass = A-O (9)</td><td>MIN = 1</td><td>Active goods must stay in stock</td></tr>
<tr><td>Z orderable</td><td>SkuClass = Z-O (11)</td><td>MIN = 1</td><td>Z goods still orderable</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delisted - safe to take all (-29pp reorder)</td></tr>
</table>

<h3>2.3 Modifiers (added to base ML)</h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Reason (see Findings)</th></tr>
<tr><td>Xmas seasonality</td><td>Xmas share 20-60%</td><td>+1</td><td>Sec 7: +9-11pp oversell for seasonal products</td></tr>
<tr><td>Brand-Store fit</td><td>Strong brand + Strong store</td><td>+1</td><td>Sec 8: +16pp reorder gap</td></tr>
<tr><td>Wide distribution</td><td>Product on 100+ stores</td><td>+1</td><td>Sec 8: +25.9pp reorder gap</td></tr>
</table>

<div class="insight">
<b>CAP:</b> Final MinLayer is capped at maximum 5. Modifiers are added to the base value from lookup table.
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>3. Target Rules (sell-through based)</h2>

<p><b>Goal:</b> Send enough pieces so the product sells AND 1 piece remains at the store.
All-sold = success but send more next time. Nothing-sold = problem, send less.</p>

<h3>3.1 Lookup Table: SalesBucket x Store</h3>
<img src="fig_dtree_02.png">

<table>
<tr><th>Sales Bucket</th><th>Store</th><th>ST Total</th><th>All-sold %</th><th>Nothing %</th><th>Proposed ML</th><th>Direction</th></tr>
{tgt_rule_rows}
</table>

<h3>3.2 Target sell-through categories and actions</h3>
<table>
<tr><th>Category</th><th>Sell-through</th><th>Color</th><th>Action</th></tr>
<tr><td class="bad">Nothing sold (0%)</td><td>0%</td><td>RED (problem)</td><td>ML DOWN - don't send to this store/product</td></tr>
<tr><td class="warn">Low ST (&lt;30% at 4M)</td><td>&lt;30%</td><td>YELLOW (warning)</td><td>ML DOWN - sells too slowly</td></tr>
<tr><td>Medium ST (30-80%)</td><td>30-80%</td><td>Neutral</td><td>ML OK - reasonable sell-through</td></tr>
<tr><td class="good">High ST (80-99%)</td><td>80-99%</td><td>GREEN</td><td>ML OK/UP - selling well, 1+ remains</td></tr>
<tr><td class="good">All sold (100%+)</td><td>100%+</td><td>GREEN (success!)</td><td>ML UP - everything sold, send more next time</td></tr>
</table>

<div class="insight-good">
<b>Key principle:</b> Target all-sold = SUCCESS (green, not red!). It means redistribution worked perfectly.
The only issue is that nothing remains at the store. Solution: send more next time (higher target ML).
</div>

<h3>3.3 Target modifiers</h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Reason</th></tr>
<tr><td>Brand-Store fit strong</td><td>Strong brand + Strong store</td><td>+1 to target ML</td><td>65.7% all-sold, high sell-through</td></tr>
<tr><td>Brand-Store fit weak</td><td>Weak brand + Weak store</td><td>-1 to target ML</td><td>30.7% nothing-sold</td></tr>
<tr><td>Wide distribution</td><td>Product on 100+ stores</td><td>+1</td><td>63.2% all-sold vs 45.7%</td></tr>
<tr><td>Niche product</td><td>Product on &lt;=20 stores</td><td>-1</td><td>38.6% nothing-sold</td></tr>
</table>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>4. Pseudocode</h2>

<h3>4.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Classify sales pattern (24M)
    pattern = ClassifySalesPattern24M(sku, store)
    -- Dead: 0 sales in 24M
    -- Dying: sales only in older periods, nothing recent
    -- Sporadic: irregular sales, not in every period
    -- Consistent: sales in 3-4 of 4 periods
    -- Declining: B &gt; C &gt; D (each period lower)

    -- 3. Classify store strength
    strength = ClassifyStoreStrength(store.Decile)
    -- Weak: decile 1-3, Mid: 4-7, Strong: 8-10

    -- 4. Lookup base MinLayer (UPDATED with 0* cells)
    base = SOURCE_LOOKUP[pattern][strength]
    --        Weak  Mid  Strong
    -- Dead:    0*   0*    1
    -- Dying:   0*   0*    1
    -- Sporad:  1    1     2
    -- Cons:    1    2     3
    -- Decl:    2    3     3

    -- 5. Business rules (A-O/Z-O minimum 1)
    IF sku.SkuClass IN (9, 11):     -- A-O, Z-O
        base = MAX(base, 1)

    -- 6. Modifiers (SOURCE UP reasons)
    IF sku.XmasShare BETWEEN 0.20 AND 0.60:
        base = base + 1
    IF BrandStoreFit(sku, store) == 'Strong+Strong':
        base = base + 1
    IF sku.StoreCount &gt; 100:
        base = base + 1

    RETURN MIN(base, 5)
</pre>

<h3>4.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer(sku, store):
    -- 1. Classify sales bucket
    bucket = ClassifySalesBucket(sku, store)
    -- Zero: 0 sales 6M
    -- Low: 1-2 sales 6M
    -- Med+: 3+ sales 6M
    -- High: current ML3 = 3

    -- 2. Classify store strength
    strength = ClassifyStoreStrength(store.Decile)

    -- 3. Lookup base MinLayer
    base = TARGET_LOOKUP[bucket][strength]
    --            Weak  Mid  Strong
    -- Zero:       1     1     2
    -- Low(1-2):   1     2     3
    -- Med+(3+):   2     3     4
    -- High(ML3=3):3     4     5

    -- 4. Modifiers (TARGET UP / TARGET DOWN)
    IF BrandStoreFit(sku, store) == 'Strong+Strong':
        base = base + 1       -- TARGET UP
    IF BrandStoreFit(sku, store) == 'Weak+Weak':
        base = base - 1       -- TARGET DOWN
    IF sku.StoreCount &gt; 100:
        base = base + 1       -- TARGET UP (wide distribution)
    IF sku.StoreCount &lt;= 20:
        base = MAX(base - 1, 1) -- TARGET DOWN (niche product)

    RETURN CLAMP(base, 1, 5)  -- min 1 (A-O/Z-O rule), max 5
</pre>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3 |
See <a href="consolidated_backtest.html">Report 3: Backtest</a> for impact of proposed rules.</i></p>
</body>
</html>"""

with open(os.path.join(REPORTS_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  [OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST
#
# ############################################################
print("")
print("--- Report 3: Backtest ---")

# ---- Compute aggregates for source backtest ----
total_src_sku = sum(r[2] for r in SRC_BACKTEST)
total_src_redist_qty = sum(r[3] for r in SRC_BACKTEST)
total_extra_kept = sum(r[4] for r in SRC_BACKTEST)
total_blocked_sku = sum(r[5] for r in SRC_BACKTEST)
total_blocked_qty = sum(r[6] for r in SRC_BACKTEST)
total_oversell_qty_bt = sum(r[7] for r in SRC_BACKTEST)

# Compute oversell % per segment for backtest
src_bt_with_pct = []
for r in SRC_BACKTEST:
    pat, sto = r[0], r[1]
    src_row = [x for x in SRC_DATA if x[0] == pat and x[1] == sto][0]
    pct_o = src_row[5]
    # Net volume change = extra_kept + blocked_qty (both reduce redistribution)
    volume_reduction = r[4] + r[6]
    # Oversell prevented = blocked_qty * oversell_rate
    oversell_prevented = r[6] * pct_o / 100
    src_bt_with_pct.append((*r, pct_o, volume_reduction, oversell_prevented))

total_volume_reduction = sum(r[9] for r in src_bt_with_pct)
total_oversell_prevented = sum(r[10] for r in src_bt_with_pct)

# ---- Compute aggregates for target backtest ----
total_tgt_cnt = sum(r[2] for r in TGT_BACKTEST)
total_tgt_received = sum(r[5] for r in TGT_BACKTEST)
total_tgt_sold = sum(r[6] for r in TGT_BACKTEST)
total_tgt_extra_needed = sum(r[7] for r in TGT_BACKTEST)

# ---- Chart: fig_backtest_01.png - Source: volume impact per segment ----
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

bt_labels = [f"{r[0]}\n{r[1]}" for r in SRC_BACKTEST]
bt_extra = [r[4] for r in SRC_BACKTEST]
bt_blocked_qty = [r[6] for r in SRC_BACKTEST]
bt_oversell_pct = [r[8] for r in src_bt_with_pct]

# Color by oversell %
colors_bt = ['#e74c3c' if o > 20 else ('#f39c12' if o > 10 else '#27ae60') for o in bt_oversell_pct]

# Left: Volume impact (extra kept + blocked qty stacked)
y_pos = np.arange(len(bt_labels))
axes[0].barh(y_pos, bt_extra, color=colors_bt, edgecolor='#333', linewidth=0.5, label='Extra units kept')
axes[0].barh(y_pos, bt_blocked_qty, left=bt_extra, color=[c + '80' for c in ['#e74c3c' if o > 20 else ('#f39c12' if o > 10 else '#27ae60') for o in bt_oversell_pct]],
             edgecolor='#333', linewidth=0.5, alpha=0.5, label='Blocked qty')
axes[0].set_yticks(y_pos)
axes[0].set_yticklabels(bt_labels, fontsize=7)
axes[0].set_xlabel('Volume (pcs)')
axes[0].set_title('Source Backtest: Volume Impact per Segment\n(extra kept + blocked = less redistributed)', fontsize=10)
axes[0].legend(fontsize=8)
for i, (e, b, o) in enumerate(zip(bt_extra, bt_blocked_qty, bt_oversell_pct)):
    total_v = e + b
    axes[0].text(total_v + 30, i, f'{total_v:,} pcs | {o}% oversell', va='center', fontsize=7)
axes[0].invert_yaxis()

# Right: Oversell prevented estimate
bt_prevented = [r[10] for r in src_bt_with_pct]
axes[1].barh(y_pos, bt_prevented, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_pos)
axes[1].set_yticklabels(bt_labels, fontsize=7)
axes[1].set_xlabel('Estimated oversell pcs prevented')
axes[1].set_title('Source Backtest: Estimated Oversell Prevented\n(blocked_qty * oversell_rate)', fontsize=10)
for i, p in enumerate(bt_prevented):
    axes[1].text(p + 2, i, f'{p:.0f} pcs', va='center', fontsize=7)
axes[1].invert_yaxis()

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- Chart: fig_backtest_02.png - Target: extra pcs needed ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

tgt_bt_labels = [f"ML{r[0]}\n{r[1]}" for r in TGT_BACKTEST]
tgt_extra_bt = [r[7] for r in TGT_BACKTEST]
tgt_avg_extra = [r[8] for r in TGT_BACKTEST]
tgt_allsold_pct = [r[3] for r in TGT_BACKTEST]
tgt_nothing_pct = [r[4] for r in TGT_BACKTEST]
tgt_received_bt = [r[5] for r in TGT_BACKTEST]
tgt_sold_bt = [r[6] for r in TGT_BACKTEST]

# Color: green = high all-sold (= success, need more), red = high nothing-sold (= problem)
colors_tgt = ['#27ae60' if a > 70 else ('#2ecc71' if a > 55 else '#f39c12') for a in tgt_allsold_pct]

y_pos2 = np.arange(len(tgt_bt_labels))

# Left: Volume - received vs sold
axes[0].barh(y_pos2 - 0.2, tgt_received_bt, 0.35, color='#3498db', label='Received qty')
axes[0].barh(y_pos2 + 0.2, tgt_sold_bt, 0.35, color='#27ae60', label='Sold qty')
axes[0].set_yticks(y_pos2)
axes[0].set_yticklabels(tgt_bt_labels, fontsize=8)
axes[0].set_xlabel('Pieces (pcs)')
axes[0].set_title('Target: Received vs Sold Volume\n(green > blue = sell-through > 100%)', fontsize=10)
axes[0].legend(fontsize=8)
for i, (rc, sl) in enumerate(zip(tgt_received_bt, tgt_sold_bt)):
    ratio = sl / rc if rc > 0 else 0
    axes[0].text(max(rc, sl) + 100, i, f'ST={ratio:.1f}x', va='center', fontsize=7, fontweight='bold')
axes[0].invert_yaxis()

# Right: Extra pcs needed for "1 remains" goal
axes[1].barh(y_pos2, tgt_extra_bt, color=colors_tgt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_pos2)
axes[1].set_yticklabels(tgt_bt_labels, fontsize=8)
axes[1].set_xlabel('Extra pcs needed (total)')
axes[1].set_title('Target: Additional pcs so 1 Remains After Sales\n(green = high all-sold = success)', fontsize=10)
for i, (e, a) in enumerate(zip(tgt_extra_bt, tgt_avg_extra)):
    axes[1].text(e + 100, i, f'{e:,} pcs (avg {a:.1f}/target)', va='center', fontsize=7)
axes[1].invert_yaxis()

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- Chart: fig_backtest_03.png - Combined: net volume change + aggressive opportunities ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Waterfall chart of volume changes
categories_wf = ['Current\nRedist Vol', 'Source:\nExtra Kept', 'Source:\nBlocked Qty',
                  'Target:\nExtra Needed', 'Net\nChange']
values_wf = [total_src_redist_qty, -total_extra_kept, -total_blocked_qty,
             total_tgt_extra_needed, total_tgt_extra_needed - total_extra_kept - total_blocked_qty]
colors_wf = ['#3498db', '#e67e22', '#e74c3c', '#27ae60', '#8e44ad']

bars = axes[0].bar(range(len(categories_wf)), values_wf, color=colors_wf, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(categories_wf)))
axes[0].set_xticklabels(categories_wf, fontsize=8)
axes[0].set_ylabel('Pieces (pcs)')
axes[0].set_title('Combined Volume Impact with Proposed Rules')
axes[0].axhline(y=0, color='black', linewidth=0.5)
for i, v in enumerate(values_wf):
    offset = 800 if v >= 0 else -1500
    axes[0].text(i, v + offset, f'{v:+,} pcs', ha='center', fontsize=9, fontweight='bold')

# Right: Opportunity map - where can we be MORE aggressive (source down + target up)
opp_labels = ['Dead+Weak\n(src down)', 'Dead+Mid\n(src down)', 'Dying+Weak\n(src down)',
              'Dying+Mid\n(src down)', 'Strong+Med+\n(tgt up)', 'Strong+Low\n(tgt up)',
              'Mid+Med+\n(tgt up)']
# Extra volume freed (source down) or needed (target up)
opp_freed = [5461, 8633, 1933, 3505, 0, 0, 0]  # current redist qty from these segments
opp_needed = [0, 0, 0, 0, 9767, 11415, 8116]  # target received qty in these segments
opp_colors = ['#27ae60'] * 4 + ['#3498db'] * 3

y_opp = np.arange(len(opp_labels))
axes[1].barh(y_opp, [f + n for f, n in zip(opp_freed, opp_needed)], color=opp_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_opp)
axes[1].set_yticklabels(opp_labels, fontsize=8)
axes[1].set_xlabel('Volume (pcs)')
axes[1].set_title('Opportunity: Source DOWN + Target UP\n(green=more aggressive source, blue=send more to target)', fontsize=10)
for i, v in enumerate([f + n for f, n in zip(opp_freed, opp_needed)]):
    axes[1].text(v + 100, i, f'{v:,} pcs', va='center', fontsize=7)
axes[1].invert_yaxis()

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#27ae60', label='Source DOWN (be more aggressive)'),
                   Patch(facecolor='#3498db', label='Target UP (send more stock)')]
axes[1].legend(handles=legend_elements, fontsize=8, loc='lower right')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- Chart: fig_backtest_04.png - Segment-level aggressiveness analysis ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

# Plot each segment as scatter: x = current oversell %, y = volume impact
for r in src_bt_with_pct:
    pat, sto, skus, rq, ek, bs, bq, oq, pct_o, vol_red, op = r
    # Size proportional to SKU count
    size = skus / 30
    color = '#e74c3c' if pct_o > 20 else ('#f39c12' if pct_o > 10 else '#27ae60')
    ax.scatter(pct_o, vol_red, s=size, color=color, alpha=0.7, edgecolors='#333', linewidth=0.5)
    ax.annotate(f'{pat[:3]}+{sto[:1]}', (pct_o, vol_red), fontsize=6, ha='center', va='bottom')

ax.set_xlabel('Current Oversell Rate (%)')
ax.set_ylabel('Volume Reduction (extra kept + blocked, pcs)')
ax.set_title('Source Backtest: Segment Volume Impact vs Oversell Rate\n(size = SKU count, green=safe, red=problematic)', fontsize=11)
ax.axvline(x=10, color='#27ae60', linestyle='--', alpha=0.5, label='Safe threshold (10%)')
ax.axvline(x=20, color='#e74c3c', linestyle='--', alpha=0.5, label='Problem threshold (20%)')
ax.legend(fontsize=8)

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_04.png")

# ---- BUILD HTML: Report 3 ----

# Build source backtest table rows
src_bt_rows = ""
for r in src_bt_with_pct:
    pat, sto, skus, rdq, ek, bs, bq, oq, pct_o, vol_red, op = r
    cls_o = 'bad' if pct_o > 20 else ('warn' if pct_o > 10 else 'good')
    src_bt_rows += (
        f'<tr><td>{pat}</td><td>{sto}</td><td>{skus:,}</td>'
        f'<td>{rdq:,}</td><td>{ek:,}</td><td>{bs:,}</td><td>{bq:,}</td>'
        f'<td>{oq:,}</td><td class="{cls_o}">{pct_o}%</td>'
        f'<td><b>{vol_red:,}</b></td><td>{op:.0f}</td></tr>\n'
    )

# Build target backtest table rows
tgt_bt_rows = ""
for r in TGT_BACKTEST:
    ml, sto, cnt, pa, pn, rq, sq, en, ae = r
    cls_a = 'good' if pa > 70 else ('warn' if pa > 55 else '')
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    st_ratio = sq / rq if rq > 0 else 0
    tgt_bt_rows += (
        f'<tr><td>ML{ml}</td><td>{sto}</td><td>{cnt:,}</td>'
        f'<td class="{cls_a}">{pa}%</td><td class="{cls_n}">{pn}%</td>'
        f'<td>{rq:,}</td><td>{sq:,}</td><td>{st_ratio:.2f}x</td>'
        f'<td><b>{en:,}</b></td><td>{ae:.2f}</td></tr>\n'
    )

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Backtest: Impact of Proposed Rules</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest: Impact of Proposed Rules</h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>This report shows expected impact of rules from
<a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> on redistribution volumes and oversell.
All metrics are in <b>pieces (pcs)</b>, not just SKU count.</p>

<!-- ========== OVERVIEW METRICS ========== -->
<div class="section">
<h2>1. Volume Impact Overview</h2>

<div style="text-align: center;">
<div class="metric"><div class="v">{total_src_redist_qty:,} pcs</div><div class="l">Current redistrib. volume</div></div>
<div class="metric"><div class="v bad">-{total_extra_kept:,} pcs</div><div class="l">Extra kept at source</div></div>
<div class="metric"><div class="v bad">-{total_blocked_qty:,} pcs</div><div class="l">Blocked qty (not redistributed)</div></div>
<div class="metric"><div class="v good">+{total_tgt_extra_needed:,} pcs</div><div class="l">Extra needed at target</div></div>
<div class="metric"><div class="v">{total_tgt_extra_needed - total_extra_kept - total_blocked_qty:+,} pcs</div><div class="l">Net volume change</div></div>
</div>

<img src="fig_backtest_03.png">
</div>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>2. Source Backtest: Volume Impact per Segment</h2>

<p>For each segment (Pattern x Store) we show <b>volume changes in pieces</b>:</p>
<ul>
<li><b>Current Qty</b> = current redistribution volume in pcs</li>
<li><b>Extra Kept</b> = additional pcs staying at source (higher ML = take less)</li>
<li><b>Blocked SKU</b> = SKU that would NOT be redistributed at all</li>
<li><b>Blocked Qty</b> = pcs that would NOT be redistributed</li>
<li><b>Oversell Qty</b> = current oversell in pcs</li>
<li><b>Volume Reduction</b> = extra kept + blocked qty (total pcs less redistributed)</li>
<li><b>Oversell Prevented</b> = estimated pcs of oversell prevented</li>
</ul>

<img src="fig_backtest_01.png">

<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th><th>Current Qty</th><th>Extra Kept</th>
<th>Blocked SKU</th><th>Blocked Qty</th><th>Oversell Qty</th><th>Oversell %</th>
<th>Volume Reduction</th><th>Oversell Prevented</th></tr>
{src_bt_rows}
<tr style="font-weight:bold; background:#e8e8e8;">
<td colspan="2">TOTAL</td><td>{total_src_sku:,}</td><td>{total_src_redist_qty:,}</td>
<td>{total_extra_kept:,}</td><td>{total_blocked_sku:,}</td><td>{total_blocked_qty:,}</td>
<td>{total_oversell_qty_bt:,}</td><td>-</td>
<td><b>{total_volume_reduction:,.0f}</b></td><td><b>{total_oversell_prevented:,.0f}</b></td></tr>
</table>

<img src="fig_backtest_04.png">

<div class="insight">
<b>Interpretation:</b>
<ul>
<li><b>{total_blocked_sku:,} SKU</b> would not be redistributed (blocked by higher ML).</li>
<li><b>{total_blocked_qty:,} pcs</b> would not leave source stores.</li>
<li><b>{total_extra_kept:,} pcs</b> would additionally stay at source (less taken from redistributed SKU).</li>
<li><b>{total_volume_reduction:,.0f} pcs</b> total reduction in redistribution volume.</li>
<li><b>~{total_oversell_prevented:,.0f} pcs</b> of oversell estimated to be prevented.</li>
</ul>
</div>

<div class="insight-good">
<b>Targeted impact:</b> The largest volume reductions are in Sporadic+Strong ({src_bt_with_pct[8][9]:,.0f} pcs)
and Consistent+Strong ({src_bt_with_pct[11][9]:,.0f} pcs) - exactly the segments with oversell &gt;20%.
Dead+Weak/Mid segments (oversell &lt;10%) have minimal volume reduction.
</div>
</div>

<!-- ========== TARGET BACKTEST ========== -->
<div class="section">
<h2>3. Target Backtest: Extra pcs for "1 Remains" Goal</h2>

<p>For each target segment (ML x Store) we show <b>volume metrics</b>:</p>
<ul>
<li><b>All-sold % = SUCCESS</b> (green) - product sold entirely, but nothing remains. Send more next time!</li>
<li><b>Nothing-sold % = PROBLEM</b> (red) - product didn't sell at all. Send less next time!</li>
<li><b>Received / Sold qty</b> - actual volume in pcs</li>
<li><b>Sell-through ratio</b> = sold / received (&gt;1.0 means more sold than received = existing stock also sold)</li>
<li><b>Extra Needed (pcs)</b> = how many more pcs should be sent so 1 remains after sales</li>
</ul>

<img src="fig_backtest_02.png">

<table>
<tr><th>ML</th><th>Store</th><th>SKU</th><th>All-sold %</th><th>Nothing %</th>
<th>Received</th><th>Sold</th><th>ST Ratio</th>
<th>Extra Needed (pcs)</th><th>Avg Extra/target</th></tr>
{tgt_bt_rows}
<tr style="font-weight:bold; background:#e8e8e8;">
<td colspan="2">TOTAL</td><td>{total_tgt_cnt:,}</td>
<td>-</td><td>-</td><td>{total_tgt_received:,}</td><td>{total_tgt_sold:,}</td><td>-</td>
<td><b>{total_tgt_extra_needed:,}</b></td><td>-</td></tr>
</table>

<div class="insight-good">
<b>"Extra needed" logic:</b> If target sells everything (all-sold), we need to send MORE so 1 remains.
E.g., ML3 Strong: 81.4% all-sold, each target needs avg 5.19 extra pcs. By raising ML from 3 to 4-5,
we send more pieces and increase the chance that 1 piece remains after sales.
</div>

<div class="insight">
<b>Where more volume should flow:</b>
<ul>
<li><b>ML3 Strong:</b> 81.4% all-sold, sell-through {TGT_BACKTEST[8][6]/TGT_BACKTEST[8][5]:.1f}x, needs {TGT_BACKTEST[8][7]:,} extra pcs</li>
<li><b>ML3 Mid:</b> 77.8% all-sold, needs {TGT_BACKTEST[7][7]:,} extra pcs</li>
<li><b>ML2 Strong:</b> 61.8% all-sold, needs {TGT_BACKTEST[5][7]:,} extra pcs</li>
</ul>
These are the BEST-performing targets. Increasing their ML brings the most value.
</div>
</div>

<!-- ========== COMBINED IMPACT ========== -->
<div class="section">
<h2>4. Combined: Source DOWN + Target UP Opportunities</h2>

<p>Some segments allow being <b>MORE aggressive</b> on BOTH sides simultaneously:</p>

<table>
<tr><th>Source segment</th><th>Current oversell</th><th>Proposed ML</th><th>Volume freed (pcs)</th></tr>
<tr class="dir-down"><td>Dead+Weak (src down)</td><td class="good">5.1%</td><td>0* (was 1)</td><td>5,461</td></tr>
<tr class="dir-down"><td>Dead+Mid (src down)</td><td class="good">7.8%</td><td>0* (was 1)</td><td>8,633</td></tr>
<tr class="dir-down"><td>Dying+Weak (src down)</td><td class="good">8.1%</td><td>0* (was 1)</td><td>1,933</td></tr>
<tr class="dir-down"><td>Dying+Mid (src down)</td><td class="good">9.7%</td><td>0* (was 1)</td><td>3,505</td></tr>
<tr style="font-weight:bold; background:#e8e8e8;">
<td>Source DOWN total</td><td></td><td></td><td><b>19,532 pcs</b> potentially freed</td></tr>
</table>

<table>
<tr><th>Target segment</th><th>All-sold %</th><th>Proposed ML</th><th>Extra needed (pcs)</th></tr>
<tr class="dir-down"><td>Strong+Med+ (tgt up)</td><td class="good">74.7%</td><td>4</td><td>10,801</td></tr>
<tr class="dir-down"><td>Strong+Low (tgt up)</td><td class="good">57.1%</td><td>3</td><td>22,934</td></tr>
<tr class="dir-down"><td>Mid+Med+ (tgt up)</td><td class="good">69.3%</td><td>3</td><td>7,196</td></tr>
<tr style="font-weight:bold; background:#e8e8e8;">
<td>Target UP total</td><td></td><td></td><td><b>{10801+22934+7196:,} pcs</b> extra needed</td></tr>
</table>

<div class="insight-good">
<b>Key synergy:</b> Volume freed from source DOWN segments (~19,532 pcs from Dead/Dying on weak/mid stores)
can flow to target UP segments (~40,931 pcs needed at strong/mid stores with high sell-through).
The supply from source DOWN covers roughly half of the extra target demand - a balanced reallocation.
</div>

<h3>4.1 Where NOT to be aggressive</h3>
<table>
<tr><th>Segment</th><th>Oversell / Nothing-sold</th><th>Action</th></tr>
<tr class="dir-up"><td>Declining+Strong (source)</td><td class="bad">35.4% oversell</td><td>ML UP to 3 (keep more)</td></tr>
<tr class="dir-up"><td>Consistent+Strong (source)</td><td class="bad">28.0% oversell</td><td>ML UP to 3 (keep more)</td></tr>
<tr class="dir-up"><td>Weak+Zero (target)</td><td class="bad">43.7% nothing-sold</td><td>ML DOWN to 1 (send less)</td></tr>
<tr class="dir-up"><td>Weak+Low (target)</td><td class="bad">34.6% nothing-sold</td><td>ML DOWN to 1 (send less)</td></tr>
</table>
</div>

<!-- ========== SUMMARY ========== -->
<div class="section">
<h2>5. Backtest Summary</h2>

<table>
<tr><th>Metric</th><th>Source side</th><th>Target side</th><th>Combined</th></tr>
<tr><td>Volume change</td><td class="bad">-{total_extra_kept + total_blocked_qty:,} pcs less sent</td>
<td class="good">+{total_tgt_extra_needed:,} pcs more needed</td>
<td>{total_tgt_extra_needed - total_extra_kept - total_blocked_qty:+,} pcs net</td></tr>
<tr><td>SKU affected (blocks)</td><td>{total_blocked_sku:,} blocked</td><td>-</td><td>-</td></tr>
<tr><td>Oversell impact</td><td class="good">~{total_oversell_prevented:,.0f} pcs prevented</td><td>-</td><td>Better source protection</td></tr>
<tr><td>Strategy</td><td>More defensive for Declining/Consistent, more aggressive for Dead/Dying</td>
<td>More stock for strong stores, less for weak</td><td>Balanced reallocation</td></tr>
</table>

<div class="insight-good">
<b>Final assessment:</b>
<ul>
<li>Source rules are <b>BALANCED</b> - they raise ML for 6 problematic segments AND lower ML for 4 safe segments.</li>
<li>Target rules <b>increase volume</b> to stores that sell well (strong stores, med+ sales, strong brand-fit).</li>
<li>Target rules <b>decrease volume</b> to stores where goods don't sell (weak stores, zero/low sales, weak brand-fit).</li>
<li>Combined: <b>smarter redistribution</b> - less oversell at source, better sell-through at target.</li>
<li>Dead and Dying segments (22,000+ SKU, 43% of total) remain at ML=0*/1 - conservative and safe.</li>
</ul>
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3 |
See <a href="consolidated_findings.html">Report 1: Findings</a> for full analytics,
<a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> for rules.</i></p>
</body>
</html>"""

with open(os.path.join(REPORTS_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  [OK] consolidated_backtest.html")


# ============================================================
# FINAL SUMMARY
# ============================================================
print("")
print("=" * 60)
print("ALL DONE. Generated reports:")
print("=" * 60)
print("  reports/consolidated_findings.html")
print("    + fig_findings_01.png (source reorder+oversell dual heatmap)")
print("    + fig_findings_02.png (store decile lines)")
print("    + fig_findings_03.png (target sell-through heatmaps)")
print("    + fig_findings_04.png (target brand-fit + price + concentration)")
print("")
print("  reports/consolidated_decision_tree.html")
print("    + fig_dtree_01.png (source ML matrix with 0*)")
print("    + fig_dtree_02.png (target ML matrix)")
print("    + fig_dtree_03.png (4-direction decision diagram)")
print("")
print("  reports/consolidated_backtest.html")
print("    + fig_backtest_01.png (source volume impact + oversell prevented)")
print("    + fig_backtest_02.png (target received vs sold + extra needed)")
print("    + fig_backtest_03.png (combined volume + opportunity map)")
print("    + fig_backtest_04.png (segment scatter: oversell vs volume)")
print("")
print("Key fixes in v2:")
print("  - BOTH reorder AND oversell shown side by side in every source table")
print("  - Target analysis equally detailed as source (sell-through by store, sales, brand-fit, price, concentration)")
print("  - Decision tree has 4 directions: source up, source down, target up, target down")
print("  - Target all-sold = SUCCESS (green), target nothing-sold = PROBLEM (red)")
print("  - Backtest shows VOLUME change (pcs), not just SKU count")
print("  - Source ML tree has 0* cells for Dead/Dying+Weak/Mid (A-O/Z-O min 1)")
print("")
print("Done at: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
