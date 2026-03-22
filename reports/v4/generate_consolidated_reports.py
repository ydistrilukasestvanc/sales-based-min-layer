"""
Consolidated Reports Generator v4: SalesBased MinLayers - CalculationId=233

v4 KEY CHANGES from v3:
  - ML range is 0-4 (not 0-5)
  - Business rule: A-O (9) and Z-O (11) orderable SKUs -> NEVER ML=0, minimum ML=1
  - Only non-orderable/delisted SKUs can have ML=0
  - CORRECTED oversell formula: oversell is now IN TARGET (3.0% 4M)
  - REORDER is the MAIN PROBLEM (37.6% SKU reorder total)
  - Source heatmaps show BOTH oversell AND reorder side by side
  - Source heatmap highlights cells with reorder_tot_sku > 40%
  - New metric: ST1 (Sell-Through-1pc) for target
  - Brand-store fit analysis refined
  - TargetML3 x StoreStrength data
  - Redistribution loop analysis
  - Redistribution ratio analysis
  - Product volatility analysis
  - Seasonality analysis
  - SkuClass change analysis
  - Flow matrix with actual store strength labels
  - Decision tree optimized for REORDER reduction (not oversell)

Key principles (from structured_assignment.md):
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

VERSION = 'v4'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SCRIPT_DIR, exist_ok=True)
sns.set_style("whitegrid")

print("=" * 60)
print(f"Generating consolidated reports ({VERSION})...")
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
.v4-badge { background: #6f42c1; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
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
    html += f'<span style="float:right; color:#7f8c8d; font-size:11px;">v4 ML 0-4 | Orderable min=1 | Reorder focus</span>'
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA (v4 CORRECTED - oversell formula fixed)
# ============================================================

# --- SOURCE: Pattern x Store -> Oversell AND Reorder (15 segments) ---
# Pattern, Store, cnt, redist_qty, oversell_4m_pct, oversell_tot_pct,
#   reorder_4m_sku_pct, reorder_tot_sku_pct, reorder_4m_qty_pct, reorder_tot_qty_pct
SRC_DATA = [
    ('Dead',       'Weak',   4557, 5418, 1.0,  4.6, 11.4, 24.4, 10.1, 22.4),
    ('Dead',       'Mid',    6884, 8533, 1.6,  6.9, 13.8, 29.5, 12.0, 26.9),
    ('Dead',       'Strong', 4012, 5086, 2.7,  9.4, 15.0, 31.4, 13.1, 28.7),
    ('Dying',      'Weak',   1634, 1976, 2.2,  6.9, 14.6, 29.7, 12.7, 26.7),
    ('Dying',      'Mid',    2965, 3605, 2.3,  8.8, 16.9, 35.2, 14.9, 31.5),
    ('Dying',      'Strong', 2000, 2430, 3.1, 11.1, 18.2, 37.0, 15.9, 33.6),
    ('Sporadic',   'Weak',   2559, 3389, 2.1, 10.0, 20.7, 39.3, 16.7, 34.8),
    ('Sporadic',   'Mid',    5606, 7848, 4.1, 14.4, 26.4, 46.8, 21.2, 40.9),
    ('Sporadic',   'Strong', 5480, 8347, 4.5, 17.9, 27.0, 50.4, 21.1, 43.3),
    ('Consistent', 'Weak',     31,   62, 0.0, 21.0, 29.0, 67.7, 17.7, 43.5),
    ('Consistent', 'Mid',     162,  404, 7.2, 23.0, 42.6, 78.4, 21.3, 52.2),
    ('Consistent', 'Strong',  516, 1159, 8.2, 26.8, 39.1, 70.3, 26.1, 51.1),
    ('Declining',  'Weak',     63,   90, 11.1, 41.1, 36.5, 65.1, 32.2, 67.8),
    ('Declining',  'Mid',     141,  189, 9.5, 31.7, 41.8, 76.6, 37.0, 74.1),
    ('Declining',  'Strong',  160,  218, 9.2, 27.1, 42.5, 73.8, 33.9, 61.0),
]

# --- TARGET: SalesBucket x Store -> ST / nothing-sold / all-sold (15 segments) ---
TGT_STORE_SALES = [
    # SalesBucket, Store, cnt, avg_st_4m, avg_st_total, avg_st1_total, nothing_sold_4m_pct, all_sold_tot_pct
    ('0',    'Weak',    137, 23.1, 34.7, 16.1, 73.7, 31.4),
    ('0',    'Mid',     334, 23.4, 41.5, 22.4, 73.7, 37.7),
    ('0',    'Strong',  252, 36.4, 53.6, 22.2, 61.1, 51.6),
    ('1-2',  'Weak',   1966, 26.3, 47.2, 59.5, 65.5, 38.0),
    ('1-2',  'Mid',    4493, 28.6, 51.2, 63.7, 62.0, 40.9),
    ('1-2',  'Strong', 3622, 32.1, 56.4, 68.1, 58.0, 47.0),
    ('3-5',  'Weak',   2601, 41.5, 65.8, 76.7, 45.1, 54.4),
    ('3-5',  'Mid',    7765, 40.8, 66.0, 77.1, 45.5, 54.6),
    ('3-5',  'Strong', 9017, 45.3, 71.7, 82.1, 40.8, 61.0),
    ('6-10', 'Weak',    886, 58.6, 82.2, 87.5, 28.1, 74.3),
    ('6-10', 'Mid',    3347, 59.3, 84.3, 90.6, 26.8, 76.2),
    ('6-10', 'Strong', 4859, 63.1, 86.2, 92.3, 22.3, 78.8),
    ('11+',  'Weak',    179, 73.8, 92.0, 95.5, 12.3, 84.9),
    ('11+',  'Mid',     815, 72.7, 93.4, 95.7, 11.9, 87.9),
    ('11+',  'Strong', 1358, 77.0, 93.9, 96.4, 10.8, 89.5),
]

# --- TARGET: Brand-store fit ---
TGT_BRAND_FIT = [
    # StoreStrength, BrandFit, skus, avg_st_total, nothing_sold_4m_pct
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

# --- Store decile data (CORRECTED) ---
DECILES = list(range(1, 11))
SRC_OVERSELL_4M_BY_DECILE = [1.9, 1.3, 1.9, 2.0, 2.6, 3.0, 3.6, 3.2, 4.4, 4.5]
SRC_REORDER_TOT_BY_DECILE = [24.0, 27.8, 28.8, 30.5, 33.6, 35.1, 36.0, 37.5, 39.0, 38.6]
TGT_ALLSOLD_BY_DECILE = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1]
TGT_NOTHING_BY_DECILE = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Pair analysis (CORRECTED) ---
PAIR_ANALYSIS = [
    ('Win-Win',   'No oversell + good ST',  28179, 66.5),
    ('Win-Lose',  'No oversell + bad ST',    8565, 20.2),
    ('Lose-Win',  'Oversell + good ST',      4794, 11.3),
    ('Lose-Lose', 'Oversell + bad ST',        866,  2.0),
]

# --- Phantom Stock (source) - CORRECTED: minimal with correct oversell formula ---
# Only 1 confirmed phantom stock SKU
SRC_PHANTOM_STOCK_NOTE = "S opravenym vzorcem oversell je phantom stock minimalny: pouze 1 potvrzene SKU."

# --- Redistribution loop (CORRECTED) ---
REDIST_LOOP = [
    # category, cnt, oversell_4m_pct, oversell_tot_pct, reorder_tot_sku_pct, reorder_4m_qty_pct, reorder_tot_qty_pct
    ('No prior transfer',  35599, 3.0, 11.4, 37.6, 16.4, 34.1),
    ('1 transfer',          1014, 3.6, 12.0, 39.0, 16.1, 33.5),
    ('2 transfers',          132, 2.3,  8.7, 43.9, 14.2, 40.2),
    ('3+ transfers',          25, 1.3,  7.9, 48.0, 10.5, 34.2),
]

# --- Redistribution ratio (source) (CORRECTED) ---
SRC_REDIST_RATIO = [
    # bucket, cnt, oversell_4m_pct, oversell_tot_pct, reorder_4m_sku_pct, reorder_tot_sku_pct, reorder_4m_qty_pct, reorder_tot_qty_pct
    ('0-25%',   7304, 1.4,  7.4, 15.1, 35.1, 13.3, 32.8),
    ('25-50%', 24490, 3.4, 12.6, 20.3, 38.9, 18.4, 36.8),
    ('50-75%',  3774, 3.7, 12.9, 25.0, 42.8, 15.1, 31.4),
    ('75-100%', 1202, 1.8,  4.9,  6.4, 10.7,  5.4, 11.4),
]

# --- Product Volatility (source) (CORRECTED) ---
SRC_VOLATILITY = [
    # bucket, cnt, oversell_4m_pct, oversell_tot_pct, reorder_tot_sku_pct, reorder_4m_qty_pct, reorder_tot_qty_pct
    ('Low (<1 CV)',    19366, 3.7, 14.0, 45.2, 19.1, 39.4),
    ('Med (1-2 CV)',   17163, 2.1,  8.1, 29.4, 12.9, 27.3),
    ('High (2-3 CV)',    114, 0.7,  2.0,  9.6,  2.7,  7.4),
    ('VHigh (3+ CV)',     65, 0.0,  1.5, 10.8,  4.4, 10.3),
]

# --- Seasonality (source) (CORRECTED) ---
SRC_SEASONALITY = [
    # category, cnt, oversell_4m_pct, oversell_tot_pct, reorder_4m_sku_pct, reorder_tot_sku_pct, reorder_4m_qty_pct, reorder_tot_qty_pct
    ('Non-seasonal (<20% NovDec)', 29298, 2.3,  9.3, 16.8, 33.9, 14.4, 30.8),
    ('Seasonal (>=20% NovDec)',     7472, 5.3, 18.8, 29.1, 52.2, 23.1, 45.3),
]

# --- SkuClass changes (CORRECTED) ---
SRC_SKUCLASS = [
    # status, cnt, oversell_tot_pct, reorder_tot_sku_pct, reorder_tot_qty_pct
    ('Unchanged', 29322, 13.0, 43.2, 39.8),
    ('Delisted',   6049,  4.9, 13.2, 10.9),
    ('Other',      1385, 10.1, 27.2, 26.3),
]

TGT_SKUCLASS = [
    # status, cnt, st_tot_pct
    ('Unchanged', 33395, 69.6),
    ('Delisted',   7108, 68.7),
    ('Other',      1128, 63.2),
]

# --- Flow Matrix ---
FLOW_MATRIX = [
    # src_store, tgt_store, pairs, pct
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

# --- TargetML3 x StoreStrength ---
TGT_ML3_STORE = [
    # ML, Store, skus, ST_4M, ST1_4M, nothing_4m_pct, all_sold_tot_pct
    (1, 'Weak',    847, 33.4, 11.9, 66.0, 51.7),
    (1, 'Mid',    2095, 38.0, 13.4, 61.4, 58.4),
    (1, 'Strong', 1788, 43.9, 16.9, 55.6, 65.6),
    (2, 'Weak',   4418, 37.6, 49.9, 49.5, 49.6),
    (2, 'Mid',   12793, 39.6, 53.0, 46.7, 53.1),
    (2, 'Strong',14766, 46.6, 60.1, 39.5, 61.8),
    (3, 'Weak',    504, 66.7, 74.2, 16.7, 76.4),
    (3, 'Mid',    1866, 66.9, 74.3, 15.8, 77.8),
    (3, 'Strong', 2554, 69.9, 77.3, 13.3, 81.4),
]

# --- Proposed decision trees (v4, ML 0-4, orderable>=1, optimized for REORDER reduction) ---
SRC_ML_TREE = {
    ('Dead', 'Weak'): 1,
    ('Dead', 'Mid'): 1,
    ('Dead', 'Strong'): 1,
    ('Dying', 'Weak'): 1,
    ('Dying', 'Mid'): 1,
    ('Dying', 'Strong'): 2,
    ('Sporadic', 'Weak'): 2,
    ('Sporadic', 'Mid'): 2,
    ('Sporadic', 'Strong'): 3,
    ('Consistent', 'Weak'): 3,
    ('Consistent', 'Mid'): 4,
    ('Consistent', 'Strong'): 4,
    ('Declining', 'Weak'): 3,
    ('Declining', 'Mid'): 3,
    ('Declining', 'Strong'): 4,
}

TGT_ML_TREE = {
    ('0 (no sales)', 'Weak'): 1,
    ('0 (no sales)', 'Mid'): 1,
    ('0 (no sales)', 'Strong'): 2,
    ('1-2', 'Weak'): 1,
    ('1-2', 'Mid'): 2,
    ('1-2', 'Strong'): 2,
    ('3-5', 'Weak'): 2,
    ('3-5', 'Mid'): 2,
    ('3-5', 'Strong'): 2,
    ('6-10', 'Weak'): 2,
    ('6-10', 'Mid'): 2,
    ('6-10', 'Strong'): 2,
    ('11+', 'Weak'): 3,
    ('11+', 'Mid'): 3,
    ('11+', 'Strong'): 3,
}

# --- Source modifiers (v4) - optimized for REORDER reduction ---
SRC_MODIFIERS = [
    ('Seasonality', '>=20% NovDec', '+1 ML', 'reorder_tot_sku 52.2% vs 33.9%'),
    ('Redist loop', '2+ transfers', '+1 ML', 'reorder_tot_sku 43.9-48.0%'),
    ('Redist ratio', '25-50% supply', 'baseline', 'reorder_4m_sku 20.3%'),
    ('Low volatility', 'CV<1', '+1 ML', 'reorder_tot_sku 45.2%'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'override'),
]

TGT_MODIFIERS = [
    ('Brand-store mismatch', 'BrandWeak+StoreWeak', '-1 ML', 'ST 55.3%, nothing-sold 54.9%'),
    ('Delisting', 'SkuClass->D/L', 'ML=0', 'override'),
    ('All-sold trend', '>=70% stores', '+1 ML', 'high sell-through signal'),
]

# ============================================================
# PATTERN DEFINITIONS
# ============================================================
PATTERNS = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
STORES = ['Weak', 'Mid', 'Strong']


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS
#
# ############################################################
print()
print("--- Report 1: Consolidated Findings ---")

# ---- Chart: fig_findings_01.png - Source: Oversell + Reorder dual heatmap ----
oversell_4m_data = []
reorder_tot_data = []
for p in PATTERNS:
    row_o4m, row_rtot = [], []
    for s in STORES:
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        row_o4m.append(row[4])      # oversell_4m_pct
        row_rtot.append(row[7])     # reorder_tot_sku_pct
    oversell_4m_data.append(row_o4m)
    reorder_tot_data.append(row_rtot)

oversell_4m_arr = np.array(oversell_4m_data)
reorder_tot_arr = np.array(reorder_tot_data)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(oversell_4m_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=axes[0],
            vmin=0, vmax=12, linewidths=1,
            cbar_kws={'label': 'Oversell % (4M)'})
axes[0].set_title('OVERSELL Rate 4M by Pattern x Store\n(v cili - prumerne 3.0%)', fontsize=11)
axes[0].set_ylabel('Sales Pattern (24M)')
axes[0].set_xlabel('Store Strength')

sns.heatmap(reorder_tot_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=axes[1],
            vmin=20, vmax=80, linewidths=1,
            cbar_kws={'label': 'Reorder Total SKU %'})
for i in range(len(PATTERNS)):
    for j in range(len(STORES)):
        if reorder_tot_data[i][j] > 40:
            axes[1].add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                             edgecolor='#2c3e50', linewidth=3))
axes[1].set_title('REORDER Rate Total by Pattern x Store\n(HLAVNI PROBLEM, cells >40% highlighted)', fontsize=11)
axes[1].set_ylabel('Sales Pattern (24M)')
axes[1].set_xlabel('Store Strength')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- Chart: fig_findings_02.png - Store decile line chart ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(DECILES, SRC_OVERSELL_4M_BY_DECILE, 'o-', color='#3498db', linewidth=2, label='Source Oversell 4M %')
axes[0].plot(DECILES, SRC_REORDER_TOT_BY_DECILE, 's--', color='#e74c3c', linewidth=2, label='Source Reorder Total %')
axes[0].fill_between(DECILES, SRC_REORDER_TOT_BY_DECILE, alpha=0.1, color='#e74c3c')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Oversell 4M + Reorder Total by Decile\n(Reorder je hlavni problem)')
axes[0].legend(fontsize=8)
axes[0].set_xticks(DECILES)
axes[0].axhspan(0, 5, alpha=0.05, color='green', label='Oversell target <5%')

axes[1].plot(DECILES, TGT_ALLSOLD_BY_DECILE, 'o-', color='#27ae60', linewidth=2, label='All Sold %')
axes[1].plot(DECILES, TGT_NOTHING_BY_DECILE, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold %')
axes[1].fill_between(DECILES, TGT_ALLSOLD_BY_DECILE, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING_BY_DECILE, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Outcome by Store Decile')
axes[1].legend(fontsize=8)
axes[1].set_xticks(DECILES)

# Efficiency ratio (all-sold / (all-sold + nothing-sold))
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
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_02.png")

# ---- Chart: fig_findings_03.png - Target ST heatmaps (5 buckets x 3 stores) ----
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
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- Chart: fig_findings_04.png - Brand-fit heatmap ----
brand_fits = ['BrandWeak', 'BrandMid', 'BrandStrong']
bf_st_matrix = np.array([
    [55.3, 63.7, 68.4],
    [59.1, 64.3, 70.0],
    [63.9, 69.5, 75.8],
])
bf_nothing_matrix = np.array([
    [54.9, 49.3, 42.4],
    [53.2, 47.6, 41.1],
    [47.3, 42.2, 35.4],
])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.heatmap(bf_st_matrix, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=brand_fits, yticklabels=STORES, ax=axes[0],
            vmin=50, vmax=80, linewidths=1, cbar_kws={'label': 'ST Total %'})
axes[0].set_title('Target: Brand-Store Fit -> ST Total %', fontsize=10)
axes[0].set_ylabel('Store Strength')

sns.heatmap(bf_nothing_matrix, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=brand_fits, yticklabels=STORES, ax=axes[1],
            vmin=30, vmax=60, linewidths=1, cbar_kws={'label': 'Nothing sold 4M %'})
axes[1].set_title('Target: Brand-Store Fit -> Nothing-Sold 4M %', fontsize=10)
axes[1].set_ylabel('Store Strength')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- Chart: fig_findings_05.png - Volatility + Seasonality (source) ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Volatility - show both oversell and reorder
vol_labels = [r[0] for r in SRC_VOLATILITY]
vol_oversell_4m = [r[2] for r in SRC_VOLATILITY]
vol_reorder_tot = [r[4] for r in SRC_VOLATILITY]
vol_cnt = [r[1] for r in SRC_VOLATILITY]
x_v = np.arange(len(vol_labels))
axes[0].bar(x_v - 0.2, vol_oversell_4m, 0.35, color='#3498db', label='Oversell 4M %')
axes[0].bar(x_v + 0.2, vol_reorder_tot, 0.35, color='#e74c3c', label='Reorder Total SKU %')
axes[0].set_xticks(x_v)
axes[0].set_xticklabels(vol_labels, fontsize=8, rotation=10)
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Product Volatility (CV) vs Oversell/Reorder\n(Low CV = vyssi reorder = potrebuje vyssi ML)')
axes[0].legend(fontsize=8)
for i, (o4, rt, c) in enumerate(zip(vol_oversell_4m, vol_reorder_tot, vol_cnt)):
    axes[0].text(i, max(o4, rt) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')

# Seasonality - show both oversell and reorder
seas_labels = [r[0][:20] for r in SRC_SEASONALITY]
seas_oversell_4m = [r[2] for r in SRC_SEASONALITY]
seas_reorder_tot = [r[5] for r in SRC_SEASONALITY]
seas_cnt = [r[1] for r in SRC_SEASONALITY]
x_s = np.arange(len(seas_labels))
w = 0.35
axes[1].bar(x_s - w/2, seas_oversell_4m, w, color='#3498db', label='Oversell 4M %')
axes[1].bar(x_s + w/2, seas_reorder_tot, w, color='#e74c3c', label='Reorder Total SKU %')
axes[1].set_xticks(x_s)
axes[1].set_xticklabels(seas_labels, fontsize=8)
axes[1].set_ylabel('%')
axes[1].set_title('SOURCE: Seasonality vs Oversell/Reorder\n(Sezonni produkty = vyssi reorder)')
axes[1].legend(fontsize=8)
for i, (o4, rt, c) in enumerate(zip(seas_oversell_4m, seas_reorder_tot, seas_cnt)):
    axes[1].text(i, max(o4, rt) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_05.png")

# ---- Chart: fig_findings_06.png - Redist Ratio + Redist Loop ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Redist ratio - show reorder
rr_labels = [r[0] for r in SRC_REDIST_RATIO]
rr_oversell_4m = [r[2] for r in SRC_REDIST_RATIO]
rr_reorder_4m = [r[4] for r in SRC_REDIST_RATIO]
rr_cnt = [r[1] for r in SRC_REDIST_RATIO]
x_rr = np.arange(len(rr_labels))
axes[0].bar(x_rr - 0.2, rr_oversell_4m, 0.35, color='#3498db', label='Oversell 4M %')
axes[0].bar(x_rr + 0.2, rr_reorder_4m, 0.35, color='#e74c3c', label='Reorder 4M SKU %')
axes[0].set_xticks(x_rr)
axes[0].set_xticklabels(rr_labels, fontsize=9)
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Redistribution Ratio (% Supply Taken)\nvs Oversell + Reorder')
axes[0].legend(fontsize=8)
for i, (o4, r4, c) in enumerate(zip(rr_oversell_4m, rr_reorder_4m, rr_cnt)):
    axes[0].text(i, max(o4, r4) + 0.5, f'n={c:,}', ha='center', fontsize=7, color='#666')

# Redist loop - show reorder
loop_labels = [r[0] for r in REDIST_LOOP]
loop_reorder = [r[4] for r in REDIST_LOOP]
loop_cnt = [r[1] for r in REDIST_LOOP]
colors_loop = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
x_l = np.arange(len(loop_labels))
axes[1].barh(x_l, loop_reorder, color=colors_loop, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(x_l)
axes[1].set_yticklabels(loop_labels, fontsize=8)
axes[1].set_xlabel('Reorder Total SKU %')
axes[1].set_title('SOURCE: Redistribution Loop vs Reorder Total\n(vice transferu = vyssi reorder)')
for i, (rt, c) in enumerate(zip(loop_reorder, loop_cnt)):
    axes[1].text(rt + 0.3, i, f'{rt}% | n={c:,}', va='center', fontsize=7)
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_06.png")

# ---- Chart: fig_findings_07.png - Flow Matrix Heatmap ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pairs count matrix
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
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_07.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_07.png")

# ---- Chart: fig_findings_08.png - TargetML3 x StoreStrength ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

ml_levels = [1, 2, 3]
ml3_st4m = np.array([
    [33.4, 38.0, 43.9],
    [37.6, 39.6, 46.6],
    [66.7, 66.9, 69.9],
])
ml3_nothing = np.array([
    [66.0, 61.4, 55.6],
    [49.5, 46.7, 39.5],
    [16.7, 15.8, 13.3],
])
ml3_allsold = np.array([
    [51.7, 58.4, 65.6],
    [49.6, 53.1, 61.8],
    [76.4, 77.8, 81.4],
])

ml_labels = ['ML=1', 'ML=2', 'ML=3']
sns.heatmap(ml3_st4m, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=STORES, yticklabels=ml_labels, ax=axes[0],
            vmin=30, vmax=75, linewidths=1, cbar_kws={'label': 'ST 4M %'})
axes[0].set_title('Target: ST 4M % by ML x Store', fontsize=10)

sns.heatmap(ml3_nothing, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=STORES, yticklabels=ml_labels, ax=axes[1],
            vmin=10, vmax=70, linewidths=1, cbar_kws={'label': 'Nothing-sold 4M %'})
axes[1].set_title('Target: Nothing-Sold 4M % by ML x Store', fontsize=10)

sns.heatmap(ml3_allsold, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=STORES, yticklabels=ml_labels, ax=axes[2],
            vmin=45, vmax=85, linewidths=1, cbar_kws={'label': 'All-sold total %'})
axes[2].set_title('Target: All-Sold Total % by ML x Store', fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_08.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_08.png")

# ---- Chart: fig_findings_09.png - Pair analysis pie + SkuClass changes ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pair analysis
pair_labels = [r[0] for r in PAIR_ANALYSIS]
pair_counts = [r[2] for r in PAIR_ANALYSIS]
pair_colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
wedges, texts, autotexts = axes[0].pie(pair_counts, labels=pair_labels, colors=pair_colors,
                                        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[0].set_title('Pair Analysis: Source+Target Combined\n(Win-Win 66.5% = oversell v cili)', fontsize=10)

# SkuClass changes - show reorder for source, ST for target
x_sc = np.arange(3)
src_sc_reorder = [r[3] for r in SRC_SKUCLASS]
tgt_sc_vals = [r[2] for r in TGT_SKUCLASS]
sc_labels = [r[0] for r in SRC_SKUCLASS]
w = 0.35
axes[1].bar(x_sc - w/2, src_sc_reorder, w, color='#e74c3c', alpha=0.7, label='Source Reorder Total SKU %')
axes[1].bar(x_sc + w/2, tgt_sc_vals, w, color='#27ae60', alpha=0.7, label='Target ST Total %')
axes[1].set_xticks(x_sc)
axes[1].set_xticklabels(sc_labels, fontsize=9)
axes[1].set_ylabel('%')
axes[1].set_title('SkuClass Changes: Source Reorder vs Target ST')
axes[1].legend(fontsize=8)
for i, (s, t) in enumerate(zip(src_sc_reorder, tgt_sc_vals)):
    axes[1].text(i - w/2, s + 0.5, f'{s}%', ha='center', fontsize=7, color='#e74c3c')
    axes[1].text(i + w/2, t + 0.5, f'{t}%', ha='center', fontsize=7, color='#27ae60')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_09.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_09.png")


# ############################################################
# BUILD HTML: Report 1
# ############################################################

# Helper: Source table rows
def src_table(data):
    rows = ""
    for r in data:
        pat, sto, cnt, rdq, o4m, otot, r4m, rtot, r4mq, rtotq = r
        cls_o4 = 'good' if o4m < 5 else ('warn' if o4m < 10 else 'bad')
        cls_rt = 'bad' if rtot > 50 else ('warn' if rtot > 35 else 'good')
        if rtot > 50:
            rec = 'MUST RAISE ML'
        elif rtot < 30:
            rec = 'CAN LOWER ML'
        else:
            rec = 'OK'
        rec_cls = 'bad' if 'RAISE' in rec else ('good' if 'LOWER' in rec else '')
        rows += (f'<tr><td>{pat}</td><td>{sto}</td><td>{cnt:,}</td>'
                 f'<td class="{cls_o4}">{o4m}%</td><td>{otot}%</td>'
                 f'<td class="{cls_rt}">{rtot}%</td><td>{rdq:,}</td>'
                 f'<td class="{rec_cls}">{rec}</td></tr>\n')
    return rows


total_src_skus = sum(r[2] for r in SRC_DATA)
total_redist_qty = sum(r[3] for r in SRC_DATA)

# Target Store x Sales table
tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sal, sto, cnt, st4, stt, st1t, pn, pa = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 30 else 'good')
    cls_a = 'good' if pa > 70 else ('warn' if pa > 50 else 'bad')
    tgt_ss_rows += (f'<tr><td>{sal}</td><td>{sto}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.1f}%</td><td>{stt:.1f}%</td><td>{st1t:.1f}%</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n')

# Brand-fit rows
tgt_bf_rows = ""
for r in TGT_BRAND_FIT:
    sto, bf, cnt, st, pn = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 40 else 'good')
    cls_st = 'good' if st > 70 else ('warn' if st > 60 else 'bad')
    tgt_bf_rows += (f'<tr><td>{sto}</td><td>{bf}</td><td>{cnt:,}</td>'
                    f'<td class="{cls_st}">{st}%</td><td class="{cls_n}">{pn}%</td></tr>\n')

# Volatility rows
vol_rows = ""
for r in SRC_VOLATILITY:
    bkt, cnt, o4, ot, rt, r4mq, rtotq = r
    cls_r = 'bad' if rt > 40 else ('warn' if rt > 25 else 'good')
    cls_rq = 'bad' if rtotq > 35 else ('warn' if rtotq > 20 else 'good')
    vol_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                 f'<td>{o4}%</td><td>{ot}%</td><td class="{cls_r}">{rt}%</td>'
                 f'<td class="{cls_rq}">{rtotq}%</td></tr>\n')

# Seasonality rows
seas_rows = ""
for r in SRC_SEASONALITY:
    cat, cnt, o4, ot, r4, rt, r4mq, rtotq = r
    cls_r = 'bad' if rt > 40 else ('warn' if rt > 30 else 'good')
    cls_rq = 'bad' if rtotq > 35 else ('warn' if rtotq > 20 else 'good')
    seas_rows += (f'<tr><td>{cat}</td><td>{cnt:,}</td>'
                  f'<td>{o4}%</td><td>{ot}%</td><td>{r4}%</td><td class="{cls_r}">{rt}%</td>'
                  f'<td class="{cls_rq}">{rtotq}%</td></tr>\n')

# Redist ratio rows
rr_rows = ""
for r in SRC_REDIST_RATIO:
    bkt, cnt, o4, ot, r4, rt_sku, r4mq, rtotq = r
    cls_r = 'warn' if r4 > 20 else 'good'
    cls_rq = 'bad' if rtotq > 35 else ('warn' if rtotq > 20 else 'good')
    rr_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                f'<td>{o4}%</td><td>{ot}%</td><td class="{cls_r}">{r4}%</td>'
                f'<td class="{cls_rq}">{rtotq}%</td></tr>\n')

# Redist loop rows
loop_rows = ""
for r in REDIST_LOOP:
    cat, cnt, o4, ot, rt, r4mq, rtotq = r
    cls_r = 'bad' if rt > 43 else ('warn' if rt > 38 else 'good')
    cls_rq = 'bad' if rtotq > 35 else ('warn' if rtotq > 20 else 'good')
    loop_rows += (f'<tr><td>{cat}</td><td>{cnt:,}</td>'
                  f'<td>{o4}%</td><td>{ot}%</td><td class="{cls_r}">{rt}%</td>'
                  f'<td class="{cls_rq}">{rtotq}%</td></tr>\n')

# Pair analysis rows
pair_rows = ""
for r in PAIR_ANALYSIS:
    name, desc, cnt, pct = r
    cls = 'good' if name == 'Win-Win' else ('warn' if name == 'Win-Lose' else 'bad')
    pair_rows += (f'<tr><td class="{cls}">{name}</td><td>{desc}</td>'
                  f'<td>{cnt:,}</td><td>{pct}%</td></tr>\n')

# SkuClass rows
sct_rows = ""
for r in SRC_SKUCLASS:
    st, cnt, ot, rt, rtotq = r
    cls_r = 'bad' if rt > 40 else ('warn' if rt > 25 else 'good')
    cls_rq = 'bad' if rtotq > 35 else ('warn' if rtotq > 20 else 'good')
    sct_rows += (f'<tr><td>{st}</td><td>{cnt:,}</td><td>{ot}%</td>'
                 f'<td class="{cls_r}">{rt}%</td><td class="{cls_rq}">{rtotq}%</td></tr>\n')

tct_rows = ""
for r in TGT_SKUCLASS:
    st, cnt, stt = r
    cls_st = 'good' if stt > 68 else 'warn'
    tct_rows += (f'<tr><td>{st}</td><td>{cnt:,}</td><td class="{cls_st}">{stt}%</td></tr>\n')

# Flow matrix rows
flow_rows = ""
for r in FLOW_MATRIX:
    sg, tg, pairs, pct = r
    flow_rows += (f'<tr><td>{sg}</td><td>{tg}</td><td>{pairs:,}</td>'
                  f'<td>{pct}%</td></tr>\n')

# ML3 x Store rows
ml3_rows = ""
for r in TGT_ML3_STORE:
    ml, sto, skus, st4, st1, pn, pa = r
    cls_a = 'good' if pa > 70 else ('warn' if pa > 55 else 'bad')
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 30 else 'good')
    ml3_rows += (f'<tr><td>ML{ml}</td><td>{sto}</td><td>{skus:,}</td>'
                 f'<td>{st4:.1f}%</td><td>{st1:.1f}%</td>'
                 f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n')


html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v4 Consolidated Findings: SalesBased MinLayers - Calc 233</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings v4: SalesBased MinLayers (ML 0-4)</h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p><b>v4 KEY CHANGE:</b> ML rozsah 0-4 (misto 0-5). Objednatelne SKU (A-O, Z-O) maji <b>minimum ML=1</b> - NIKDY ML=0.
Pouze non-orderable/delisted SKU mohou mit ML=0. <b>OPRAVENY VZOREC OVERSELL</b> - oversell je nyni v cili, <b>reorder je hlavni problem</b>.</p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (37.6%).</b><br>
S opravenym vzorcem oversell je oversell 4M pouze 3.0% (1,317 SKU, 1,464 qty) - to je v akceptovatelnem rozsahu.
Hlavni problem je <b>reorder</b>: 37.6% SKU (13,841) musi byt v total perioade znovu objednano, coz znamena 16,615 kusu (34.1% objemu).
Rozhodovaci strom je optimalizovan na <b>redukci reorderu</b>.
</div>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>ORDERABLE CONSTRAINT (v4):</b> A-O (SkuClass=9) a Z-O (SkuClass=11) objednatelne SKU maji vzdy <b>minimum ML=1</b>.
Pouze 380 non-orderable SKU (1.0%) mohou mit ML=0. 95.4% vsech SKU je orderable, proto vsechny Dead/Dying segmenty
zacinaji na ML=1 (ne ML=0 jako v3).
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

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (37.6%).</b>
</div>

<h3>Target: Celkove metriky - 4M a total</h3>
<p><b>ST</b> = LEAST(Sold, Base) / Base (cap 100%)<br>
<b>ST-1pc (ST1)</b> = sell-through s toleranci 1 kusu = <b>IDEAL pokud zbyva presne 1 ks</b>.</p>
</div>

<!-- ========== 2. SOURCE: PATTERNS ========== -->
<div class="section">
<h2>2. Source: Predejni vzorce (24M) - primarni prediktor</h2>
<p>24-mesicni historie prodejov odhalila 5 vzorov, ktere silne predikuji riziko <b>reorderu</b> po redistribuci.
<b>v4 (opraveno):</b> Oversell je v cili (3.0%), primarni metrikou je nyni <b>reorder_tot_sku</b>.</p>

<h3>2.1 Vsech 15 segmentu: Pattern x Store</h3>
<img src="fig_findings_01.png">
<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th>
<th>Reorder Total SKU %</th><th>Redist qty</th><th>Recommendation</th></tr>
{src_table(SRC_DATA)}
<tr style="font-weight:bold;background:#e8e8e8"><td colspan="2">TOTAL</td><td>{total_src_skus:,}</td>
<td colspan="2">-</td><td>-</td><td>{total_redist_qty:,}</td><td>-</td></tr>
</table>

<div class="insight-bad">
<b>MUST RAISE ML (reorder_tot_sku &gt;50%):</b> Sporadic+Strong (50.4%), Consistent+Weak (67.7%), Consistent+Mid (78.4%),
Consistent+Strong (70.3%), Declining+Weak (65.1%), Declining+Mid (76.6%), Declining+Strong (73.8%).
</div>
<div class="insight-good">
<b>Oversell je v cili:</b> Maximalni oversell 4M je 11.1% (Declining+Weak, ale jen 63 SKU). Prumerny oversell 4M = 3.0%.
S opravenym vzorcem jsou vsechny segmenty pod 12% oversell 4M.
</div>
</div>

<!-- ========== 3. SOURCE + TARGET: STORE STRENGTH ========== -->
<div class="section">
<h2>3. Source + Target: Sila predajni (decily)</h2>
<img src="fig_findings_02.png">
<table>
<tr><th>Metric</th><th>D1 (Weak)</th><th>D10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Oversell 4M</td><td class="good">1.9%</td><td class="good">4.5%</td><td>Oversell je v cili ve vsech decilech</td></tr>
<tr><td>Source Reorder Total</td><td class="warn">24.0%</td><td class="bad">38.6%</td><td>Silne predajne = vyssi reorder riziko</td></tr>
<tr><td>Target All-Sold Total</td><td class="warn">48.3%</td><td class="good">70.1%</td><td>Silne predajne prodaji vse</td></tr>
<tr><td>Target Nothing-Sold</td><td class="bad">32.1%</td><td class="good">13.7%</td><td>Slabe predajny = vice zaseklych zbozi</td></tr>
</table>
</div>

<!-- ========== 4. TARGET: SELL-THROUGH ========== -->
<div class="section">
<h2>4. Target: Sell-through analyza (15 segmentu)</h2>

<h3>4.1 Store Strength x Sales Bucket</h3>
<img src="fig_findings_03.png">
<table>
<tr><th>SalesBucket</th><th>Store</th><th>SKU</th><th>ST 4M %</th><th>ST Total %</th><th>ST1 Total %</th>
<th>Nothing-sold 4M %</th><th>All-sold Total %</th></tr>
{tgt_ss_rows}
</table>

<div class="insight-good">
<b>11+ sales bucket = vyborny target:</b> 84.9-89.5% all-sold, nothing-sold jen 10.8-12.3%.
ST1 total 95.5-96.4% = prakticky vsechno se proda nebo zustane presne 1 ks.
</div>

<h3>4.2 Brand-Store Fit</h3>
<img src="fig_findings_04.png">
<table>
<tr><th>Store</th><th>BrandFit</th><th>SKU</th><th>ST Total %</th><th>Nothing-sold 4M %</th></tr>
{tgt_bf_rows}
</table>

<div class="insight-bad">
<b>BrandWeak + StoreWeak = nejhorsi kombinace:</b> ST total jen 55.3%, nothing-sold 54.9%.
Naopak BrandStrong + StoreStrong: ST total 75.8%, nothing-sold jen 35.4%.
Rozdil: +20.5pp v ST, -19.5pp v nothing-sold.
</div>
</div>

<!-- ========== 5. TARGET: ML3 x STORE ========== -->
<div class="section">
<h2>5. Target: Vykon podle ML a sily predajny <span class="v4-badge">v4</span></h2>

<img src="fig_findings_08.png">
<table>
<tr><th>ML</th><th>Store</th><th>SKU</th><th>ST 4M %</th><th>ST1 4M %</th>
<th>Nothing-sold 4M %</th><th>All-sold Total %</th></tr>
{ml3_rows}
</table>

<div class="insight-good">
<b>ML=3 je jasne nejlepsi target:</b> All-sold 76-81%, nothing-sold jen 13-17%.
ML=1 ma nejhorsi vykon (all-sold 52-66%, nothing-sold 56-66%).
ML=2 je stredni cesta s velkym objemem (31,977 SKU).
</div>
</div>

<!-- ========== 6. PAIR ANALYSIS ========== -->
<div class="section">
<h2>6. Parova analyza (Source + Target combined)</h2>
<img src="fig_findings_09.png">
<table>
<tr><th>Outcome</th><th>Description</th><th>Count</th><th>Share</th></tr>
{pair_rows}
</table>
<div class="insight-good">
<b>Win-Win = 66.5%</b> (28,179 paru bez oversell a s dobrym ST) - to je vyborny vysledek.
Win-Lose (20.2%) = bez oversell, ale spatny ST na targetu - fokus na zlepseni target vyberu.
Lose-Win + Lose-Lose = pouze 13.3% celku.
</div>
</div>

<!-- ========== 7. SOURCE FACTORS ========== -->
<div class="section">
<h2>7. Source: Dalsi faktory ovlivnujici reorder</h2>

<h3>7.1 Phantom Stock (source)</h3>
<div class="insight-good">
<b>Phantom stock: s opravenym vzorcem oversell je minimalny.</b> Pouze 1 potvrzene phantom stock SKU.
S korekci oversell vzorce prakticky zadne SKU nesplnuje kriteria phantom stocku.
Toto neni problem k reseni.
</div>

<h3>7.2 Redistribucni smycka</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th><th>Reorder Total SKU %</th><th>Reorder Total Qty %</th></tr>
{loop_rows}
</table>
<div class="insight-bad">
<b>3+ transfers = 48.0% reorder total!</b>
Kazdy dalsi transfer zvysuje reorder riziko. 2+ transfers = silny signal pro +1 ML modifier.
Pozor: oversell je nizky (1.3-2.3%), ale reorder roste.
</div>

<h3>7.3 Redistribucni ratio (% supply odeslano)</h3>
<img src="fig_findings_06.png">
<table>
<tr><th>Ratio Bucket</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th><th>Reorder 4M SKU %</th><th>Reorder Total Qty %</th></tr>
{rr_rows}
</table>
<div class="insight-new">
<b>Reorder roste s ratio:</b> 0-25% ratio = 15.1% reorder 4M, 50-75% = 25.0%.
Vyjimka: 75-100% ratio ma nizky reorder (6.4%) - kdyz se odeslalo skoro vse, neni co reorderovat.
Oversell je ve vsech bucketech nizky (1.4-3.7%).
</div>

<h3>7.4 Product Volatility (CV)</h3>
<img src="fig_findings_05.png">
<table>
<tr><th>Volatility</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th><th>Reorder Total SKU %</th><th>Reorder Total Qty %</th></tr>
{vol_rows}
</table>
<div class="insight-new">
<b>Low CV (&lt;1) = 45.2% reorder total!</b> Stabilni produkty maji vyssi reorder, protoze se predikovatelne prodavaji a dochazi k nim.
High CV (3+) = jen 9.6-10.8% reorder. Nestabilni produkty = mene predvidatelne = mene reorderu.
Modifier: Low CV -> +1 ML.
</div>

<h3>7.5 Sezonnost (NovDec share)</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Oversell 4M %</th><th>Oversell Total %</th><th>Reorder 4M SKU %</th><th>Reorder Total SKU %</th><th>Reorder Total Qty %</th></tr>
{seas_rows}
</table>
<div class="insight-bad">
<b>Sezonni produkty: 52.2% reorder total SKU</b> vs 33.9% u non-seasonal.
Rozdil: +18.3pp. Silny modifier: &ge;20% NovDec -> +1 ML.
Oversell je take vyssi (5.3% vs 2.3%), ale stale v akceptovatelnem rozsahu.
</div>
</div>

<!-- ========== 8. SKUCLASS CHANGES ========== -->
<div class="section">
<h2>8. SkuClass prechody</h2>

<h3>8.1 Source</h3>
<table>
<tr><th>Status</th><th>SKU</th><th>Oversell Total %</th><th>Reorder Total SKU %</th><th>Reorder Total Qty %</th></tr>
{sct_rows}
</table>

<h3>8.2 Target</h3>
<table>
<tr><th>Status</th><th>SKU</th><th>ST Total %</th></tr>
{tct_rows}
</table>

<div class="insight-good">
<b>Delisting override:</b> Delisted source: reorder_tot_sku jen 13.2% (vyrazne nizsi nez unchanged 43.2%).
Delisted target: ST total 68.7% (temer stejne jako unchanged 69.6%).
Delisting -> ML=0 je bezpecne pravidlo. Oversell delisted je take nizky (4.9%).
</div>
</div>

<!-- ========== 9. FLOW MATRIX ========== -->
<div class="section">
<h2>9. Flow Matrix: odkud kam</h2>

<img src="fig_findings_07.png">
<table>
<tr><th>Source Store</th><th>Target Store</th><th>Pairs</th><th>% of Total</th></tr>
{flow_rows}
</table>

<div class="insight">
<b>Nejvic paru: Mid->Strong (19.6%)</b> a Mid->Mid (17.2%).
Strong->Strong: 15.4%. Weak->Weak jen 2.8% (nejmensi tok).
Distribuce preferuje posilani do silnych predajni = spravny smer.
</div>
</div>

<!-- ========== 10. SUMMARY TABLE ========== -->
<div class="section">
<h2>10. Souhrnna tabulka vsech faktoru</h2>

<table>
<tr><th>Factor</th><th>Impact (reorder)</th><th>Impact (oversell)</th><th>Source ML</th><th>Target ML</th><th>Priority</th></tr>
<tr><td>Sales Pattern: Consistent/Declining</td><td class="bad">65-78% reorder tot</td><td>7-41% oversell tot</td><td class="bad">UP (ML=3-4)</td><td>-</td><td>1</td></tr>
<tr><td>Sales Pattern: Dead/Dying</td><td>24-37% reorder tot</td><td class="good">1-11% oversell tot</td><td class="good">ML=1 (orderable min)</td><td>-</td><td>1</td></tr>
<tr><td>Store Strength (source D10)</td><td class="bad">38.6% reorder tot</td><td class="good">4.5% oversell 4M</td><td class="bad">UP for strong</td><td>-</td><td>1</td></tr>
<tr><td>Target: 11+ sales bucket</td><td>-</td><td>-</td><td>-</td><td class="good">UP (ML=3)</td><td>1</td></tr>
<tr><td>Target: 0 sales + Weak</td><td>-</td><td>-</td><td>-</td><td class="bad">DOWN (ML=1)</td><td>1</td></tr>
<tr><td>Seasonality &ge;20% NovDec</td><td class="bad">52.2% reorder tot</td><td>5.3% oversell 4M</td><td class="bad">+1 ML</td><td>-</td><td>2</td></tr>
<tr><td>Redist loop 2+</td><td class="bad">43.9-48.0% reorder tot</td><td class="good">1.3-2.3% oversell 4M</td><td class="bad">+1 ML</td><td>-</td><td>2</td></tr>
<tr><td>Low volatility (CV&lt;1)</td><td class="bad">45.2% reorder tot</td><td>3.7% oversell 4M</td><td class="bad">+1 ML</td><td>-</td><td>2</td></tr>
<tr><td>Brand Weak+Weak</td><td>-</td><td>-</td><td>-</td><td class="bad">-1 ML</td><td>2</td></tr>
<tr><td>All-sold &ge;70%</td><td>-</td><td>-</td><td>-</td><td class="good">+1 ML</td><td>2</td></tr>
<tr><td>Delisting (D/L)</td><td class="good">reorder 13.2%</td><td class="good">oversell 4.9%</td><td class="good">= 0</td><td class="good">= 0</td><td>1</td></tr>
</table>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v4 ML 0-4 | Orderable min=1 | Reorder focus</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  [OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE (v4: ML 0-4, orderable min=1, reorder-optimized)
#
# ############################################################
print()
print("--- Report 2: Decision Tree ---")

# ---- fig_dtree_01.png - Source ML matrix ----
src_ml_matrix = np.array([
    [1, 1, 1], [1, 1, 2], [2, 2, 3], [3, 4, 4], [3, 3, 4],
])
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(src_ml_matrix, annot=False, cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer (0-4)'})
ax.set_title('Source MinLayer v4: Lookup Table\n(Pattern 24M x Store, orderable min=1, reorder-optimized)\nML 0 only for non-orderable/delisted', fontsize=11)
ax.set_ylabel('Sales Pattern')
ax.set_xlabel('Store Strength')
for i in range(5):
    for j in range(3):
        val = src_ml_matrix[i][j]
        note = ''
        if i == 0:
            note = '\n(ord min)'
        elif i == 1 and j < 2:
            note = '\n(ord min)'
        color = 'white' if val >= 3 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={val}{note}', ha='center', va='center',
                fontsize=10, color=color, fontweight='bold')
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
ax.set_title('Target MinLayer v4: Lookup Table\n(Sales Bucket x Store, range 0-4)', fontsize=11)
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
ax.set_title('4-Direction MinLayer Decision Framework (v4, ML 0-4, reorder-optimized)', fontsize=14, fontweight='bold', pad=20)

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
         'SOURCE ML UP\n(raise MinLayer)\n\nDying+Strong: ML=2\nSporadic+Strong: ML=3\nConsistent+Mid/Strong: ML=4\nDeclining: ML=3-4\n+1: Seasonality >=20% NovDec\n+1: Redist loop 2+\n+1: Low volatility CV<1\nCap at ML=4',
         '#fce4e4', '#e74c3c', fontsize=6)
draw_arrow(ax, 42, 58, 30, 75, 'Reorder >40%', '#e74c3c')

draw_box(ax, 78, 82, 28, 14,
         'SOURCE ML DOWN\n(more aggressive)\n\nDead: ML=1 (orderable min)\nDying W/M: ML=1 (orderable min)\nDelisted: ML=0\n\nNon-orderable only: ML=0\n(380 SKU, 1.0%)\n\nOrderable min=1 ALWAYS',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 58, 58, 70, 75, 'Reorder <30%', '#27ae60')

draw_box(ax, 22, 28, 28, 14,
         'TARGET ML UP\n(send more stock)\n\n11+ sales: ML=3\n0 sales + Strong: ML=2\n+1: All-sold >=70%\n+1: Brand Strong\n\nAll-sold = SUCCESS!\n\nCap at ML=4',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 42, 52, 30, 35, 'High sell-through', '#27ae60')

draw_box(ax, 78, 28, 28, 14,
         'TARGET ML DOWN\n(send less stock)\n\n0 sales + Weak/Mid: ML=1\n1-2 sales + Weak: ML=1\n-1: Brand Weak+Store Weak\nDelisted: ML=0\n\nNothing-sold = PROBLEM!',
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

# ---- fig_dtree_04.png - Modifier Impact Waterfall ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Source modifiers impact
mod_labels_s = ['Base\n(Pattern\nxStore)', '+Season.\n(>=20%\nNovDec)', '+Redist\nloop\n(2+)',
                '+Low\nVolatility\n(CV<1)', 'Capped\n(max 4)']
mod_values_s = [2.0, 1.0, 1.0, 1.0, -1.0]
mod_colors_s = ['#3498db', '#e74c3c', '#e74c3c', '#e74c3c', '#95a5a6']
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
mod_labels_t = ['Base\n(Sales\nxStore)', '+AllSold\n>=70%', '+Brand\nStrong', '-Brand\nWeak\n+Weak', 'Capped\n(max 4)']
mod_values_t = [2.0, 1.0, 1.0, -1.0, -0.0]
mod_colors_t = ['#3498db', '#27ae60', '#27ae60', '#e74c3c', '#95a5a6']
cumulative_t = [mod_values_t[0]]
for v in mod_values_t[1:]:
    cumulative_t.append(cumulative_t[-1] + v)
bottoms_t = [0] + cumulative_t[:-1]

axes[1].bar(range(len(mod_labels_t)), mod_values_t, bottom=bottoms_t, color=mod_colors_t, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(range(len(mod_labels_t)))
axes[1].set_xticklabels(mod_labels_t, fontsize=7)
axes[1].set_ylabel('MinLayer')
axes[1].set_title('Target ML: Modifier Waterfall\n(base + modifiers up to cap 4)')
for i, (b, v) in enumerate(zip(bottoms_t, mod_values_t)):
    if v != 0:
        axes[1].text(i, b + v/2, f'+{v:.0f}' if v > 0 else f'{v:.0f}', ha='center', fontsize=8, fontweight='bold')
axes[1].axhline(y=4, color='#27ae60', linestyle='--', alpha=0.5, label='Cap = 4')
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_04.png")

# ---- fig_dtree_05.png - Source reorder scatter by segment with proposed ML ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))
for r in SRC_DATA:
    pat, sto, cnt, rdq, o4m, otot, r4m, rtot, r4mq, rtotq = r
    ml = SRC_ML_TREE[(pat, sto)]
    size = max(cnt / 20, 30)
    color_map = {1: '#27ae60', 2: '#f39c12', 3: '#e74c3c', 4: '#8e44ad'}
    color = color_map.get(ml, '#95a5a6')
    ax.scatter(o4m, rtot, s=size, color=color, alpha=0.7, edgecolors='#333', linewidth=0.5)
    ax.annotate(f'{pat[:3]}+{sto[:1]}\nML={ml}', (o4m, rtot), fontsize=6, ha='center', va='bottom')
ax.set_xlabel('Oversell 4M %')
ax.set_ylabel('Reorder Total SKU %')
ax.set_title('Source: Oversell 4M vs Reorder Total with Proposed ML\n(green=ML1, orange=ML2, red=ML3, purple=ML4)')
ax.axhline(y=40, color='#e74c3c', linestyle='--', alpha=0.5, label='Reorder 40% threshold')
ax.axhline(y=30, color='#f39c12', linestyle='--', alpha=0.5, label='Reorder 30% threshold')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_05.png")


# ---- BUILD HTML: Report 2 ----
src_rule_rows = ""
for p in PATTERNS:
    for s in STORES:
        ml = SRC_ML_TREE[(p, s)]
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        o4m, otot, r4m, rtot = row[4], row[5], row[6], row[7]
        if rtot > 50:
            rec, cls, dir_text = 'MUST RAISE', 'dir-up', 'UP'
        elif rtot < 30:
            rec, cls, dir_text = 'CAN LOWER', 'dir-down', 'DOWN'
        else:
            rec, cls, dir_text = 'OK', '', 'OK'
        note = ' (ord min)' if p == 'Dead' or (p == 'Dying' and s in ('Weak', 'Mid')) else ''
        src_rule_rows += (f'<tr class="{cls}"><td>{p}</td><td>{s}</td>'
                          f'<td>{o4m}%</td><td>{rtot}%</td><td><b>{ml}{note}</b></td>'
                          f'<td>{rec}</td><td>{dir_text}</td></tr>\n')

tgt_rule_rows = ""
tgt_bucket_list = ['0 (no sales)', '1-2', '3-5', '6-10', '11+']
tgt_bucket_display = {
    '0 (no sales)': ('0', '0 (no sales)'),
    '1-2': ('1-2', '1-2'),
    '3-5': ('3-5', '3-5'),
    '6-10': ('6-10', '6-10'),
    '11+': ('11+', '11+'),
}
for sal_key in tgt_bucket_list:
    sal_match = tgt_bucket_display[sal_key][0]
    for sto in STORES:
        matching = [x for x in TGT_STORE_SALES if x[0] == sal_match and x[1] == sto]
        if matching:
            r = matching[0]
            pn, pa = r[6], r[7]
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
<title>v4 Decision Tree: MinLayer Rules 0-4 (Reorder-optimized)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree v4: MinLayer Rules 0-4 <span class="v4-badge">Reorder-optimized</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Pravidla vychazi z <a href="consolidated_findings.html">Report 1</a>.
Strom ma <b>4 smery</b>: source up, source down, target up, target down.
<b>v4: ML rozsah 0-4, orderable minimum ML=1. Strom optimalizovan na REDUKCI REORDERU.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (37.6%).</b><br>
S opravenym vzorcem je oversell minimalny. Strom je proto optimalizovan na minimalizaci reorderu.
Segmenty s vysokym reorderem (Consistent, Declining) dostali vyssi ML (3-4).
</div>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>v4 ORDERABLE CONSTRAINT:</b> A-O (9) a Z-O (11) objednatelne SKU maji vzdy <b>minimum ML=1</b>.
Dead+Weak / Dying+Weak by bez constraintu byly ML=0, ale 95.4% SKU je orderable, proto ML=1.
Pouze non-orderable (380 SKU) a delisted (D/L/R) mohou mit ML=0.
</div>

<!-- ========== 4-DIRECTION OVERVIEW ========== -->
<div class="section">
<h2>1. 4-Direction Framework</h2>
<img src="fig_dtree_03.png">

<table>
<tr><th>Direction</th><th>When</th><th>Action</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>SOURCE UP</b></td><td>Reorder total &gt;40%</td><td>Ponechat vice na source</td><td>Produkty se stale aktivne prodavaji, vysoka mira reorderu</td></tr>
<tr class="dir-down"><td><b>SOURCE DOWN</b></td><td>Reorder total &lt;30%</td><td>ML=1 (orderable min)</td><td>Dead/Dying - neprodavaji se, nizky reorder</td></tr>
<tr class="dir-down"><td><b>TARGET UP</b></td><td>All-sold &gt;70%</td><td>Poslat vice na target (ML=3)</td><td>Target proda vse</td></tr>
<tr class="dir-up"><td><b>TARGET DOWN</b></td><td>Nothing-sold &gt;60%</td><td>ML=1 (minimum)</td><td>Target neproda</td></tr>
</table>
</div>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>2. Source pravidla (ML 0-4, orderable min=1, reorder-optimized)</h2>

<h3>2.1 Lookup: Pattern x Store</h3>
<img src="fig_dtree_01.png">
<table>
<tr><th>Pattern</th><th>Store</th><th>Oversell 4M %</th><th>Reorder Total SKU %</th><th>ML</th><th>Rec</th><th>Dir</th></tr>
{src_rule_rows}
</table>
<p><b>Dead/Dying W/M: ML=1 pro orderable (95.4% SKU). Dying+Strong: ML=2 (reorder 37.0%).
Consistent+Mid/Strong a Declining+Strong: ML=4 (reorder 70-78%).</b></p>

<h3>2.2 Business Rules (Overrides)</h3>
<table>
<tr><th>Rule</th><th>Condition</th><th>ML</th><th>Reason</th></tr>
<tr style="background:#fff3cd"><td><b>Active orderable</b></td><td>SkuClass = A-O (9)</td><td><b>MIN = 1</b></td><td>Aktivni zbozi MUSI zustat (min 1 ks)</td></tr>
<tr style="background:#fff3cd"><td><b>Z orderable</b></td><td>SkuClass = Z-O (11)</td><td><b>MIN = 1</b></td><td>Z zbozi stale objednatelne</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delisted = bezpecne vzit vse</td></tr>
<tr><td>Non-orderable</td><td>Neither A-O nor Z-O nor delisted</td><td>= 0 (allowed)</td><td>380 SKU (1.0%)</td></tr>
</table>

<h3>2.3 Source Modifikatory (v4)</h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence</th></tr>
{src_mod_rows}
</table>

<img src="fig_dtree_04.png">

<div class="insight-new">
<b>v4 modifikatory (reorder-optimized):</b> Seasonality, Redist loop, Low volatility - vsechny zvysuji ML kvuli vysokemu reorderu.
Delisting je jediny modifier ktery snizuje na ML=0.
Vysledek cappovany na 0-4.
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>3. Target pravidla (ML 0-4)</h2>

<h3>3.1 Lookup: SalesBucket x Store</h3>
<img src="fig_dtree_02.png">
<table>
<tr><th>Sales Bucket</th><th>Store</th><th>All-sold Total %</th><th>Nothing-sold 4M %</th><th>ML</th><th>Dir</th></tr>
{tgt_rule_rows}
</table>

<div class="insight">
<b>Target ML je konzervativnejsi nez v3:</b> Maximum je ML=3 (pro 11+ sales). V v3 bylo az ML=5.
Rozsah 0-4 = mene extremni hodnoty, ale vsechny vysokoprodejni segmenty maji ML=3.
6-10 sales bucket ma ML=2 pro vsechny predajny (dostatecne, ale ne agresivni).
</div>

<h3>3.2 Target modifikatory (v4)</h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adjustment</th><th>Evidence</th></tr>
{tgt_mod_rows}
</table>
</div>

<!-- ========== SCATTER PLOT ========== -->
<div class="section">
<h2>4. Source: Oversell vs Reorder vs ML vizualizace</h2>
<img src="fig_dtree_05.png">
<div class="insight">
<b>Vizualizace:</b> Kazdy bod = 1 ze 15 segmentu. Barva = navrzeny ML (zelena=1, oranzova=2, cervena=3, fialova=4).
Osa X = oversell 4M (vsude nizke, pod 12%). Osa Y = reorder total SKU % (hlavni prediktor).
Consistent+Mid (ML=4) ma 78.4% reorder total. Dead+Weak (ML=1) ma jen 24.4%.
</div>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>5. Pseudocode (v4)</h2>

<h3>5.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer_v4(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Base ML from Pattern x Store lookup (reorder-optimized)
    pattern = ClassifySalesPattern24M(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = SOURCE_LOOKUP[pattern][strength]
    -- Dead = 1, Dying W/M = 1, Dying S = 2, Sporadic W/M = 2, Sporadic S = 3
    -- Consistent W = 3, Consistent M/S = 4, Declining W/M = 3, Declining S = 4

    -- 3. ORDERABLE CONSTRAINT (v4 key rule)
    IF sku.SkuClass IN (9, 11):       -- A-O or Z-O
        base = MAX(base, 1)           -- NEVER ML=0

    -- 4. Modifiers (UP only for source in v4, reorder-driven)
    IF sku.NovDecShare >= 0.20: base += 1         -- seasonal (reorder 52.2%)
    IF sku.RedistTransferCount >= 2: base += 1    -- loop (reorder 43.9-48.0%)
    IF sku.VolatilityCV < 1.0: base += 1          -- stable = sells = reorder

    RETURN CLAMP(base, 0, 4)
</pre>

<h3>5.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer_v4(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):
        RETURN 0

    -- 2. Base ML from Sales x Store lookup
    bucket = ClassifySalesBucket(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = TARGET_LOOKUP[bucket][strength]
    -- 0+Weak = 1, 11+ = 3, rest mostly 2

    -- 3. Modifiers
    IF BrandStoreFit(sku, store) == 'BrandWeak+StoreWeak': base -= 1
    IF sku.AllSoldPct >= 70: base += 1
    IF sku.SkuClass IN (3, 4, 5): base = 0       -- delisted

    RETURN CLAMP(base, 0, 4)
</pre>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v4 ML 0-4 | Orderable min=1 | Reorder-optimized</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  [OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST (v4, reorder-focused)
#
# ############################################################
print()
print("--- Report 3: Backtest ---")

# --- Backtest data (corrected - capped reorder qty) ---
BT_SRC_UP = 15435      # SKU
BT_SRC_UP_REDIST = 21688
BT_SRC_UP_REORDER_4M = 4592
BT_SRC_UP_REORDER_TOT = 9038
BT_SRC_UP_REORDER_TOT_SKU_PCT = 47.3
BT_SRC_UP_REORDER_TOT_QTY_PCT = 41.7

BT_SRC_DOWN = 310       # SKU
BT_SRC_DOWN_REDIST = 506
BT_SRC_DOWN_REORDER_4M = 35
BT_SRC_DOWN_REORDER_TOT = 99
BT_SRC_DOWN_REORDER_TOT_SKU_PCT = 10.0
BT_SRC_DOWN_REORDER_TOT_QTY_PCT = 19.6

BT_SRC_NOCHANGE = 21025
BT_SRC_NOCHANGE_REDIST = 26560
BT_SRC_NOCHANGE_REORDER_4M = 3353
BT_SRC_NOCHANGE_REORDER_TOT = 7478
BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT = 31.0
BT_SRC_NOCHANGE_REORDER_TOT_QTY_PCT = 28.2

BT_TOTAL_PAIRS = 42404
BT_TOTAL_QTY = 48754
BT_OVERSELL_4M_SKU = 1317
BT_OVERSELL_4M_SKU_PCT = 3.6
BT_OVERSELL_4M_QTY = 1464
BT_OVERSELL_4M_QTY_PCT = 3.0
BT_REORDER_4M_SKU = 7087
BT_REORDER_4M_SKU_PCT = 19.3
BT_REORDER_4M_QTY = 7980
BT_REORDER_4M_QTY_PCT = 16.4
BT_REORDER_TOT_SKU = 13841
BT_REORDER_TOT_SKU_PCT = 37.6
BT_REORDER_TOT_QTY = 16615
BT_REORDER_TOT_QTY_PCT = 34.1

# ---- fig_backtest_01.png - Overview: reorder by ML direction ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# SKU counts by direction
cats_bt = [f'ML UP\n({BT_SRC_UP:,} SKU)', f'NO CHANGE\n({BT_SRC_NOCHANGE:,} SKU)', f'ML DOWN\n({BT_SRC_DOWN:,} SKU)']
reorder_pcts = [BT_SRC_UP_REORDER_TOT_SKU_PCT, BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT, BT_SRC_DOWN_REORDER_TOT_SKU_PCT]
colors_bt = ['#e74c3c', '#95a5a6', '#27ae60']
axes[0].bar(cats_bt, reorder_pcts, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[0].set_ylabel('Reorder Total SKU %')
axes[0].set_title(f'Source Backtest: Reorder Total by ML Direction\n(ML UP SKU maji {BT_SRC_UP_REORDER_TOT_SKU_PCT}% reorder = target pro zlepseni)')
for i, r in enumerate(reorder_pcts):
    axes[0].text(i, r + 1, f'{r}%', ha='center', fontsize=12, fontweight='bold')

# Volume comparison
cats_vol = ['ML UP', 'NO CHANGE', 'ML DOWN']
reorder_vols = [BT_SRC_UP_REORDER_TOT, BT_SRC_NOCHANGE_REORDER_TOT, BT_SRC_DOWN_REORDER_TOT]
sku_counts = [BT_SRC_UP, BT_SRC_NOCHANGE, BT_SRC_DOWN]
x_bt = np.arange(len(cats_vol))
w = 0.35
axes[1].bar(x_bt - w/2, sku_counts, w, color='#3498db', label='SKU count')
axes[1].bar(x_bt + w/2, reorder_vols, w, color='#e74c3c', label='Reorder Total qty')
axes[1].set_xticks(x_bt)
axes[1].set_xticklabels(cats_vol, fontsize=10)
axes[1].set_ylabel('Count')
axes[1].set_title('Source Backtest: SKU count vs Reorder qty\n(ML UP = nejvice reorderu, proto ML zvyseno)')
axes[1].legend(fontsize=9)
for i, (sk, rq) in enumerate(zip(sku_counts, reorder_vols)):
    axes[1].text(i - w/2, sk + 300, f'{sk:,}', ha='center', fontsize=7, fontweight='bold')
    axes[1].text(i + w/2, rq + 300, f'{rq:,}', ha='center', fontsize=7, fontweight='bold', color='#e74c3c')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- fig_backtest_02.png - Oversell is fine overview ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Oversell pie
oversell_labels = [f'No oversell\n({100-BT_OVERSELL_4M_SKU_PCT}%)', f'Oversell 4M\n({BT_OVERSELL_4M_SKU_PCT}%)']
oversell_sizes = [100 - BT_OVERSELL_4M_SKU_PCT, BT_OVERSELL_4M_SKU_PCT]
oversell_colors = ['#27ae60', '#e74c3c']
axes[0].pie(oversell_sizes, labels=oversell_labels, colors=oversell_colors,
            autopct='', startangle=90, textprops={'fontsize': 11})
axes[0].set_title(f'Oversell 4M: {BT_OVERSELL_4M_SKU_PCT}% SKU = V CILI', fontsize=12)

# Reorder pie
reorder_labels = [f'No reorder\n({100-BT_REORDER_TOT_SKU_PCT}%)', f'Reorder total\n({BT_REORDER_TOT_SKU_PCT}%)']
reorder_sizes = [100 - BT_REORDER_TOT_SKU_PCT, BT_REORDER_TOT_SKU_PCT]
reorder_colors = ['#27ae60', '#e74c3c']
axes[1].pie(reorder_sizes, labels=reorder_labels, colors=reorder_colors,
            autopct='', startangle=90, textprops={'fontsize': 11})
axes[1].set_title(f'Reorder Total: {BT_REORDER_TOT_SKU_PCT}% SKU = HLAVNI PROBLEM', fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- fig_backtest_03.png - Reorder by segment (before = current data) ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))
segments_ba = ['Dead+W', 'Dead+M', 'Dead+S', 'Dying+W', 'Dying+M', 'Dying+S',
               'Spor+W', 'Spor+M', 'Spor+S', 'Cons+W', 'Cons+M', 'Cons+S',
               'Decl+W', 'Decl+M', 'Decl+S']
reorder_tot_pcts = [24.4, 29.5, 31.4, 29.7, 35.2, 37.0, 39.3, 46.8, 50.4,
                    67.7, 78.4, 70.3, 65.1, 76.6, 73.8]
ml_values = [1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 3, 3, 4]
colors_seg = ['#27ae60' if ml <= 1 else ('#f39c12' if ml == 2 else ('#e74c3c' if ml == 3 else '#8e44ad'))
              for ml in ml_values]

y_ba = np.arange(len(segments_ba))
ax.barh(y_ba, reorder_tot_pcts, color=colors_seg, edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_ba)
ax.set_yticklabels(segments_ba, fontsize=8)
ax.set_xlabel('Reorder Total SKU %')
ax.set_title('Source Segments: Reorder Total SKU % with Proposed ML\n(green=ML1, orange=ML2, red=ML3, purple=ML4)')
ax.axvline(x=40, color='#e74c3c', linestyle='--', alpha=0.5, label='Reorder 40% threshold')
ax.axvline(x=30, color='#f39c12', linestyle='--', alpha=0.5, label='Reorder 30% threshold')
for i, (r, ml) in enumerate(zip(reorder_tot_pcts, ml_values)):
    ax.text(r + 0.5, i, f'{r}% | ML={ml}', va='center', fontsize=7)
ax.invert_yaxis()
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- fig_backtest_04.png - Target ML performance ----
fig, ax = plt.subplots(1, 1, figsize=(12, 6))

# ML3 x Store bar chart
ml3_labels = [f"ML{r[0]}\n{r[1]}" for r in TGT_ML3_STORE]
ml3_allsold = [r[6] for r in TGT_ML3_STORE]
ml3_nothing = [r[5] for r in TGT_ML3_STORE]
y_ml3 = np.arange(len(ml3_labels))
w = 0.35
ax.barh(y_ml3 - w/2, ml3_allsold, w, color='#27ae60', label='All-sold Total %')
ax.barh(y_ml3 + w/2, ml3_nothing, w, color='#e74c3c', label='Nothing-sold 4M %')
ax.set_yticks(y_ml3)
ax.set_yticklabels(ml3_labels, fontsize=8)
ax.set_xlabel('%')
ax.set_title('Target: Performance by ML x Store\n(ML=3 = best target performance)')
ax.legend(fontsize=9)
for i, (a, n) in enumerate(zip(ml3_allsold, ml3_nothing)):
    ax.text(a + 0.5, i - w/2, f'{a}%', va='center', fontsize=7, color='#27ae60')
    ax.text(n + 0.5, i + w/2, f'{n}%', va='center', fontsize=7, color='#e74c3c')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_04.png")


# ---- BUILD HTML: Report 3 ----
html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v4 Backtest: Impact of Proposed Rules (ML 0-4, Reorder-optimized)</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest v4: Impact of Proposed Rules (ML 0-4) <span class="v4-badge">Reorder-optimized</span></h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Dopad pravidel z <a href="consolidated_decision_tree.html">Report 2</a>.
v4: ML rozsah 0-4, orderable minimum ML=1. <b>Optimalizovano na redukci reorderu.</b></p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili (3.0%). Reorder je hlavni problem (37.6%).</b><br>
S opravenym vzorcem oversell je oversell minimalny (3.0% qty). Hlavni metrikou pro optimalizaci je <b>reorder</b>:
37.6% SKU (13,841) musi byt znovu objednano, coz je 16,615 kusu (34.1% objemu).
</div>

<!-- ========== OVERVIEW ========== -->
<div class="section">
<h2>1. Backtest Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">48,754</div><div class="l">Total redistributed pcs</div></div>
<div class="metric"><div class="v" style="color:#27ae60">3.0%</div><div class="l">Oversell 4M qty (V CILI)</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">37.6%</div><div class="l">Reorder Total SKU (PROBLEM)</div></div>
</div>

<div class="insight-good">
<b>Oversell je v cili:</b> Pouze {BT_OVERSELL_4M_SKU:,} SKU ({BT_OVERSELL_4M_SKU_PCT}%) ma oversell v 4M periode,
celkem {BT_OVERSELL_4M_QTY:,} kusu ({BT_OVERSELL_4M_QTY_PCT}%). Toto je akceptovatelne.
</div>

<div class="insight-bad">
<b>Reorder je hlavni problem:</b> {BT_REORDER_TOT_SKU:,} SKU ({BT_REORDER_TOT_SKU_PCT}%) musi byt znovu objednano v total periode.
To je {BT_REORDER_TOT_QTY:,} kusu ({BT_REORDER_TOT_QTY_PCT}% objemu). Rozhodovaci strom cili na redukci tohoto cisla.
</div>

<img src="fig_backtest_02.png">

<h3>Detailni metriky</h3>
<table>
<tr><th>Metric</th><th>4M</th><th>Total</th></tr>
<tr><td>Oversell SKU</td><td class="good">{BT_OVERSELL_4M_SKU:,} ({BT_OVERSELL_4M_SKU_PCT}%)</td><td>4,718 (12.8%)</td></tr>
<tr><td>Oversell qty</td><td class="good">{BT_OVERSELL_4M_QTY:,} ({BT_OVERSELL_4M_QTY_PCT}%)</td><td>5,578 (11.4%)</td></tr>
<tr><td>Reorder SKU</td><td class="bad">7,087 (19.3%)</td><td class="bad">{BT_REORDER_TOT_SKU:,} ({BT_REORDER_TOT_SKU_PCT}%)</td></tr>
<tr><td>Reorder qty</td><td class="bad">{BT_REORDER_4M_QTY:,} ({BT_REORDER_4M_QTY_PCT}%)</td><td class="bad">{BT_REORDER_TOT_QTY:,} ({BT_REORDER_TOT_QTY_PCT}%)</td></tr>
</table>
</div>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>2. Source Backtest: ML Direction Impact</h2>
<img src="fig_backtest_01.png">

<table>
<tr><th>Direction</th><th>SKU</th><th>Reorder Total qty</th><th>Reorder Total SKU %</th><th>Description</th></tr>
<tr class="dir-up"><td><b>ML UP</b></td><td>{BT_SRC_UP:,}</td><td>{BT_SRC_UP_REORDER_TOT:,}</td>
<td class="bad">{BT_SRC_UP_REORDER_TOT_SKU_PCT}%</td>
<td>SKU s vysokym reorderem - ML zvyseno aby se snizil objem redistribuce</td></tr>
<tr class="dir-down"><td><b>ML DOWN</b></td><td>{BT_SRC_DOWN:,}</td><td>{BT_SRC_DOWN_REORDER_TOT:,}</td>
<td class="good">{BT_SRC_DOWN_REORDER_TOT_SKU_PCT}%</td>
<td>Pouze non-orderable SKU (nizky reorder, bezpecne snizit)</td></tr>
<tr><td>NO CHANGE</td><td>{BT_SRC_NOCHANGE:,}</td><td>{BT_SRC_NOCHANGE_REORDER_TOT:,}</td>
<td>{BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT}%</td><td>Existujici ML vyhovuje</td></tr>
</table>

<div class="insight-bad">
<b>ML UP skupina ma {BT_SRC_UP_REORDER_TOT_SKU_PCT}% reorder total</b> (vs {BT_SRC_NOCHANGE_REORDER_TOT_SKU_PCT}% u NO CHANGE a {BT_SRC_DOWN_REORDER_TOT_SKU_PCT}% u ML DOWN).
Zvyseni ML pro tech {BT_SRC_UP:,} SKU by melo snizit objem redistribuce a tim i objem reorderu.
</div>
</div>

<!-- ========== SEGMENT DETAIL ========== -->
<div class="section">
<h2>3. Source: Reorder per Segment s navrzenymi ML</h2>
<img src="fig_backtest_03.png">

<table>
<tr><th>Segment</th><th>Reorder Total SKU %</th><th>Proposed ML</th><th>Reason</th></tr>
<tr class="dir-up"><td>Consistent+Mid</td><td class="bad">78.4%</td><td><b>ML=4</b></td><td>Nejvyssi reorder - maximalni ochrana</td></tr>
<tr class="dir-up"><td>Declining+Mid</td><td class="bad">76.6%</td><td><b>ML=3</b></td><td>Velmi vysoky reorder</td></tr>
<tr class="dir-up"><td>Declining+Strong</td><td class="bad">73.8%</td><td><b>ML=4</b></td><td>Velmi vysoky reorder + silna predajna</td></tr>
<tr class="dir-up"><td>Consistent+Strong</td><td class="bad">70.3%</td><td><b>ML=4</b></td><td>Vysoky reorder + silna predajna</td></tr>
<tr class="dir-up"><td>Consistent+Weak</td><td class="bad">67.7%</td><td><b>ML=3</b></td><td>Vysoky reorder</td></tr>
<tr class="dir-up"><td>Declining+Weak</td><td class="bad">65.1%</td><td><b>ML=3</b></td><td>Vysoky reorder</td></tr>
<tr class="dir-up"><td>Sporadic+Strong</td><td class="bad">50.4%</td><td><b>ML=3</b></td><td>Nad 40% threshold</td></tr>
<tr><td>Sporadic+Mid</td><td class="warn">46.8%</td><td>ML=2</td><td>Stredni riziko</td></tr>
<tr><td>Sporadic+Weak</td><td class="warn">39.3%</td><td>ML=2</td><td>Pod 40% ale nad 30%</td></tr>
<tr><td>Dying+Strong</td><td class="warn">37.0%</td><td>ML=2</td><td>Stredni riziko</td></tr>
<tr><td>Dying+Mid</td><td class="warn">35.2%</td><td>ML=1</td><td>Orderable minimum</td></tr>
<tr><td>Dead+Strong</td><td>31.4%</td><td>ML=1</td><td>Orderable minimum</td></tr>
<tr class="dir-down"><td>Dying+Weak</td><td>29.7%</td><td>ML=1</td><td>Orderable minimum, nizky reorder</td></tr>
<tr class="dir-down"><td>Dead+Mid</td><td>29.5%</td><td>ML=1</td><td>Orderable minimum, nizky reorder</td></tr>
<tr class="dir-down"><td>Dead+Weak</td><td>24.4%</td><td>ML=1</td><td>Orderable minimum, nejnizsi reorder</td></tr>
</table>
</div>

<!-- ========== TARGET BACKTEST ========== -->
<div class="section">
<h2>4. Target Backtest</h2>

<img src="fig_backtest_04.png">

<div class="insight">
<b>Target pravidla zustavaji stejne jako pred korekci.</b> ML=3 pro 11+ sales (all-sold 76-81%),
ML=2 pro 3-10 sales (vyrovnany pristup), ML=1 pro 0-2 sales + slabe predajny.
</div>
</div>

<!-- ========== RECOMMENDATIONS ========== -->
<div class="section">
<h2>5. Doporuceni</h2>

<table>
<tr><th>#</th><th>Doporuceni</th><th>Ocekavany dopad</th><th>Priorita</th></tr>
<tr><td>1</td><td><b>Implementovat ML 0-4 rozsah s orderable min=1, reorder-optimized tree</b></td>
<td>Snizi reorder u ML UP skupiny ({BT_SRC_UP_REORDER_TOT_SKU_PCT}% -> target pod 35%)</td><td class="bad">KRITICKA</td></tr>
<tr><td>2</td><td>Source Pattern x Store lookup (15 segmentu, reorder-driven)</td>
<td>ML=3-4 pro Consistent/Declining (reorder 65-78%)</td><td class="bad">KRITICKA</td></tr>
<tr><td>3</td><td>Target Sales Bucket x Store lookup (15 segmentu)</td>
<td>ML=3 pro 11+ sales, ML=1 pro 0 sales + Weak</td><td class="bad">KRITICKA</td></tr>
<tr><td>4</td><td>Seasonality modifier (+1 pro >=20% NovDec)</td>
<td>Ochrani sezonni produkty (reorder 52.2% vs 33.9%)</td><td class="warn">VYSOKA</td></tr>
<tr><td>5</td><td>Redist loop modifier (+1 pro 2+ transfers)</td>
<td>Zabrazi cyklickemu presouvani (reorder roste s poctem transferu)</td><td class="warn">VYSOKA</td></tr>
<tr><td>6</td><td>Low volatility modifier (+1 pro CV&lt;1)</td>
<td>Ochrani stabilne prodavane produkty (reorder 45.2%)</td><td>STREDNI</td></tr>
<tr><td>7</td><td>Brand-store mismatch modifier (-1 pro Weak+Weak)</td>
<td>Snizi posilani na slabe kombinace</td><td>STREDNI</td></tr>
</table>

<div class="insight-new">
<b>Celkovy dopad v4 (opraveny):</b><br>
- Oversell: <b>V CILI</b> - 3.0% qty (1,464 pcs) v 4M, 11.4% v total<br>
- Reorder: <b>HLAVNI PROBLEM</b> - 37.6% SKU (13,841), 34.1% qty (16,615 pcs) v total<br>
- ML UP: {BT_SRC_UP:,} SKU ({BT_SRC_UP_REORDER_TOT_SKU_PCT}% reorder) - navysenim ML snizime objem redistribuce a tim reorder<br>
- ML DOWN: {BT_SRC_DOWN:,} SKU ({BT_SRC_DOWN_REORDER_TOT_SKU_PCT}% reorder) - bezpecne snizit ML pro non-orderable<br>
- Strom optimalizovan pro redukci reorderu, ne oversell (ktery je jiz v cili)
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | v4 ML 0-4 | Orderable min=1 | Reorder-optimized</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  [OK] consolidated_backtest.html")


print()
print("=" * 60)
print(f"ALL DONE ({VERSION}). Generated:")
print(f"  - 3 HTML reports")
print(f"  - 13 PNG charts (9 findings + 5 dtree + 4 backtest)")
print(f"  - ML range: 0-4 | Orderable min=1 | Reorder-optimized")
print(f"  - Oversell: V CILI (3.0%) | Reorder: HLAVNI PROBLEM (37.6%)")
print("=" * 60)
