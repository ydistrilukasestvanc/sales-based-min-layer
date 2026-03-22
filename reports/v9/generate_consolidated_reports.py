"""
Consolidated Reports Generator v9: SalesBased MinLayers - CalculationId=233

v9 INDEPENDENT ANALYSIS: Fresh computation from assignment only.
  - Nov+Dec actual share = 26.5% vs expected 16.7% => Xmas lift 1.59x
  - CalendarWeight 0.7 applied (assignment-specified, conservative vs actual lift)
  - Velocity segments recomputed: 1,778 ActiveSeller, 10,863 SlowFull
  - All metrics computed independently — no prior version data reused

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

VERSION = 'v9'
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
.v9-badge { background: #6f42c1; color: white; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
.changed-cell { background: #fff3cd !important; border: 2px solid #f39c12 !important; }
"""

NOW_STR = datetime.now().strftime('%Y-%m-%d %H:%M')


def nav_bar(active_idx):
    links = [
        ('consolidated_findings.html', 'Report 1: Findings'),
        ('consolidated_decision_tree.html', 'Report 2: Decision Tree'),
        ('consolidated_backtest.html', 'Report 3: Backtest'),
        ('definitions.html', 'Definitions'),
    ]
    html = '<div class="nav">'
    for i, (href, label) in enumerate(links):
        cls = ' class="active"' if i == active_idx else ''
        html += f'<a href="{href}"{cls}>{label}</a>'
    html += f'<span style="float:right; color:#7f8c8d; font-size:11px;">v9 Independent | CalendarWeight 0.7 | ML 0-4 | Orderable min=1 | Bidirectional</span>'
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA (v9 — independently computed)
# ============================================================

OVERVIEW = {
    'pairs': 42404, 'source_skus': 36770, 'target_skus': 41631, 'redist_qty': 48754,
    'os4m_qty': 1541, 'os4m_pct': 3.2, 'os_t_qty': 5626, 'os_t_pct': 11.5,
    'ro4m_qty': 8045, 'ro4m_pct': 16.5, 'ro_t_qty': 16615, 'ro_t_pct': 34.1,
    'st4m_avg': 45.4, 'st1_4m_avg': 62.9, 'st_t_avg': 69.2, 'st1_t_avg': 82.6,
    'ns4m_skus': 17468, 'ns4m_pct': 42.0, 'ns_t_skus': 8873, 'ns_t_pct': 21.3,
    'as4m_skus': 13708, 'as4m_pct': 32.9, 'as_t_skus': 24860, 'as_t_pct': 59.7,
    'novdec_share': 26.5, 'expected_share': 16.7, 'xmas_lift': 1.59, 'calendar_weight': 0.7,
}

# --- Velocity Segments ---
SEGMENTS = [
    # name, skus, sold_after%, avg_velocity
    ('TrueDead', 18385, 36.9, 0.0),
    ('PartialDead', 3599, 56.7, 0.0),
    ('BriefNoSale', 98, 85.7, 0.0),
    ('SlowFull', 10863, 66.4, 0.148),
    ('SlowPartial', 2038, 77.2, 0.239),
    ('SlowBrief', 9, 44.4, 0.350),
    ('ActiveSeller', 1778, 95.2, 0.919),
]

# --- Segment x Store (source) ---
# (segment, store, skus, redist_qty, os4m%, os_t%, ro4m%, ro_t%, sold_after%)
SEG_STORE = [
    ('TrueDead', 'Weak', 5233, 6245, 1.0, 4.3, 9.6, 21.6, 32.6),
    ('TrueDead', 'Mid', 8240, 10063, 1.3, 6.1, 11.5, 26.1, 37.3),
    ('TrueDead', 'Strong', 4912, 5990, 2.1, 8.0, 12.8, 28.6, 40.7),
    ('PartialDead', 'Weak', 940, 1125, 2.8, 9.9, 16.7, 33.8, 48.7),
    ('PartialDead', 'Mid', 1610, 2072, 4.2, 14.1, 19.4, 38.2, 57.9),
    ('PartialDead', 'Strong', 1049, 1467, 5.5, 16.8, 18.3, 36.4, 62.2),
    ('SlowPartial', 'Weak', 421, 626, 1.8, 9.1, 12.1, 30.0, 71.7),
    ('SlowPartial', 'Mid', 800, 1192, 3.5, 12.3, 17.0, 34.7, 72.9),
    ('SlowPartial', 'Strong', 817, 1312, 3.7, 15.6, 19.7, 36.4, 84.2),
    ('SlowFull', 'Weak', 2122, 2710, 2.5, 10.3, 18.2, 36.3, 56.0),
    ('SlowFull', 'Mid', 4697, 6276, 4.4, 15.2, 23.0, 43.4, 63.9),
    ('SlowFull', 'Strong', 4044, 5598, 5.3, 19.1, 23.5, 46.8, 74.7),
    ('ActiveSeller', 'Weak', 99, 193, 1.6, 27.5, 21.2, 46.6, 90.9),
    ('ActiveSeller', 'Mid', 431, 1003, 4.8, 18.6, 20.0, 44.4, 91.9),
    ('ActiveSeller', 'Strong', 1248, 2745, 5.7, 21.3, 20.9, 44.0, 96.7),
]

STORES = ['Weak', 'Mid', 'Strong']

# --- LastSaleGap per segment ---
LAST_SALE_GAP = [
    # segment, total_skus, gap_le90, gap_le90_pct, avg_gap
    ('TrueDead', 18385, 0, 0.0, 638),
    ('PartialDead', 3599, 0, 0.0, 559),
    ('SlowFull', 10863, 1798, 16.6, 195),
    ('SlowPartial', 2038, 715, 35.1, 119),
    ('ActiveSeller', 1778, 1242, 69.9, 67),
]

# --- Decision Trees ---
SRC_ML = {
    ('ActiveSeller', 'Weak'): 3, ('ActiveSeller', 'Mid'): 4, ('ActiveSeller', 'Strong'): 4,
    ('SlowFull', 'Weak'): 2, ('SlowFull', 'Mid'): 2, ('SlowFull', 'Strong'): 3,
    ('SlowPartial', 'Weak'): 2, ('SlowPartial', 'Mid'): 2, ('SlowPartial', 'Strong'): 3,
    ('PartialDead', 'Weak'): 1, ('PartialDead', 'Mid'): 1, ('PartialDead', 'Strong'): 2,
    ('TrueDead', 'Weak'): 1, ('TrueDead', 'Mid'): 1, ('TrueDead', 'Strong'): 1,
}

TGT_ML = {
    ('0', 'Weak'): 1, ('0', 'Mid'): 1, ('0', 'Strong'): 1,
    ('1-2', 'Weak'): 1, ('1-2', 'Mid'): 1, ('1-2', 'Strong'): 2,
    ('3-5', 'Weak'): 1, ('3-5', 'Mid'): 2, ('3-5', 'Strong'): 3,
    ('6-10', 'Weak'): 2, ('6-10', 'Mid'): 3, ('6-10', 'Strong'): 3,
    ('11+', 'Weak'): 2, ('11+', 'Mid'): 3, ('11+', 'Strong'): 4,
}

# --- Target data ---
TGT_STORE_SALES = [
    # SalesBucket, Store, skus, ST4M, ST_T, NS4M%, AS_T%
    ('0', 'Weak', 139, 23.5, 35.6, 73.4, 32.4),
    ('0', 'Mid', 341, 23.4, 41.6, 73.3, 37.8),
    ('0', 'Strong', 254, 37.2, 54.6, 60.6, 52.8),
    ('1-2', 'Weak', 1972, 26.5, 47.2, 65.4, 38.1),
    ('1-2', 'Mid', 4507, 28.9, 51.3, 61.7, 41.0),
    ('1-2', 'Strong', 3640, 32.3, 56.4, 57.7, 47.1),
    ('3-5', 'Weak', 2601, 41.6, 65.8, 44.8, 54.3),
    ('3-5', 'Mid', 7760, 41.0, 65.9, 45.3, 54.6),
    ('3-5', 'Strong', 9052, 45.5, 71.8, 40.5, 61.1),
    ('6-10', 'Weak', 879, 59.2, 82.4, 27.5, 74.6),
    ('6-10', 'Mid', 3319, 59.9, 84.4, 26.2, 76.3),
    ('6-10', 'Strong', 4835, 63.2, 86.2, 22.2, 78.8),
    ('11+', 'Weak', 178, 73.6, 91.9, 12.4, 84.8),
    ('11+', 'Mid', 806, 72.6, 93.3, 11.7, 87.7),
    ('11+', 'Strong', 1348, 77.4, 94.0, 10.6, 89.5),
]

# --- BrandFit overall ---
BRAND_FIT = [
    # store, brandfit, skus, st_total, ns_pct
    ('Weak', 'BrandWeak', 2426, 56.1, 34.0),
    ('Weak', 'BrandMid', 1247, 62.9, 27.6),
    ('Weak', 'BrandStrong', 2096, 68.4, 21.9),
    ('Mid', 'BrandWeak', 4055, 60.2, 29.6),
    ('Mid', 'BrandMid', 3559, 64.5, 25.7),
    ('Mid', 'BrandStrong', 9119, 70.0, 20.2),
    ('Strong', 'BrandWeak', 2239, 65.7, 24.7),
    ('Strong', 'BrandMid', 2844, 70.5, 20.1),
    ('Strong', 'BrandStrong', 14046, 75.8, 15.4),
]

# --- BrandFit Graduation by SalesBucket (Strong stores, BrandWeak vs BrandStrong) ---
BRANDFITGRAD = [
    # sb, store, brand, skus, st4m, st_t, ns4m, as_t
    ('0','Weak','BrandWeak',78,14.5,25.0,80.8,20.5),
    ('0','Weak','BrandStrong',23,31.9,42.0,65.2,39.1),
    ('0','Mid','BrandWeak',149,15.4,27.3,81.2,22.1),
    ('0','Mid','BrandStrong',95,25.1,50.9,73.7,48.4),
    ('0','Strong','BrandWeak',46,21.0,28.8,73.9,23.9),
    ('0','Strong','BrandStrong',133,42.4,63.2,57.1,62.4),
    ('1-2','Weak','BrandWeak',985,24.5,43.6,68.1,34.9),
    ('1-2','Weak','BrandStrong',556,29.6,52.8,59.9,41.9),
    ('1-2','Mid','BrandWeak',1369,27.4,47.3,64.7,37.3),
    ('1-2','Mid','BrandStrong',2053,29.7,53.8,60.0,42.9),
    ('1-2','Strong','BrandWeak',556,29.0,50.7,61.5,42.6),
    ('1-2','Strong','BrandStrong',2421,33.3,57.9,56.6,48.3),
    ('3-5','Weak','BrandWeak',1031,38.7,62.1,47.4,49.5),
    ('3-5','Weak','BrandStrong',1018,44.6,68.9,41.9,58.7),
    ('3-5','Mid','BrandWeak',1852,39.0,63.8,48.1,52.2),
    ('3-5','Mid','BrandStrong',4267,42.5,67.5,43.5,56.3),
    ('3-5','Strong','BrandWeak',1102,41.7,65.7,45.2,54.4),
    ('3-5','Strong','BrandStrong',6616,46.7,73.4,39.0,63.0),
    ('6-10','Weak','BrandWeak',286,58.9,80.8,27.6,73.4),
    ('6-10','Weak','BrandStrong',400,61.8,84.4,25.5,76.8),
    ('6-10','Mid','BrandWeak',581,53.1,81.2,33.6,73.3),
    ('6-10','Mid','BrandStrong',2113,61.3,85.3,24.7,77.0),
    ('6-10','Strong','BrandWeak',453,57.6,83.2,28.5,75.3),
    ('6-10','Strong','BrandStrong',3771,64.0,86.6,21.2,79.2),
    ('11+','Weak','BrandWeak',46,63.6,86.1,19.6,73.9),
    ('11+','Weak','BrandStrong',98,79.6,93.6,8.2,88.8),
    ('11+','Mid','BrandWeak',106,67.7,92.6,15.1,84.9),
    ('11+','Mid','BrandStrong',590,74.1,93.5,10.2,88.0),
    ('11+','Strong','BrandWeak',85,76.8,91.8,15.3,87.1),
    ('11+','Strong','BrandStrong',1106,77.6,94.0,10.0,89.7),
]

BRANDFIT_DELTA = [
    # sb, delta_st_range, modifier_BW, modifier_BS
    ('0 (no sales)', '+17 to +34pp', -1, +1),
    ('1-2', '+7 to +9pp', -1, +1),
    ('3-5', '+6 to +8pp', -1, 0),
    ('6-10', '+2 to +3pp', 0, 0),
    ('11+', '<2pp', 0, 0),
]

# --- Pair analysis ---
PAIRS = [('Win-Win', 21443, 50.6), ('Win-Lose', 15257, 36.0), ('Lose-Win', 3841, 9.1), ('Lose-Lose', 1863, 4.4)]

# --- Store decile data ---
DECILES = list(range(1, 11))
SRC_OVERSELL_4M = [2.1, 1.4, 2.1, 2.2, 2.8, 3.1, 3.7, 3.4, 4.5, 4.6]
SRC_REORDER_TOT = [24.0, 27.8, 28.8, 30.5, 33.6, 35.1, 36.2, 37.3, 39.0, 38.6]
TGT_ALLSOLD = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.0, 60.6, 63.0, 70.1]
TGT_NOTHING = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Flow matrix ---
FLOW = [
    ('Weak', 'Weak', 1179, 2.8), ('Weak', 'Mid', 4099, 9.7), ('Weak', 'Strong', 4661, 11.0),
    ('Mid', 'Weak', 2437, 5.7), ('Mid', 'Mid', 7315, 17.3), ('Mid', 'Strong', 8330, 19.6),
    ('Strong', 'Weak', 2256, 5.3), ('Strong', 'Mid', 5639, 13.3), ('Strong', 'Strong', 6488, 15.3),
]

# --- Store distribution ---
STORE_DIST = [('Weak', 107), ('Mid', 140), ('Strong', 105)]

# --- SkuClass source ---
SKUCLASS_SRC = [
    ('A-O (Orderable)', 31773, 86.4),
    ('Z-O (Orderable)', 3288, 8.9),
    ('A (Active)', 1449, 3.9),
    ('D (Delisted)', 166, 0.5),
    ('Z (Can order centrally)', 42, 0.1),
    ('L (Delisted supplier)', 36, 0.1),
    ('R (Cleared)', 16, 0.0),
]

# --- Current ML distribution ---
SRC_CURRENT_ML = [(0, 1709), (1, 31965), (2, 2680), (3, 416)]
TGT_CURRENT_ML = [(1, 4730), (2, 31977), (3, 4924)]

# --- Backtest source ---
# segment, store, skus, ml_up, ml_down, ml_same, ml_up_qty, ml_down_qty
BT_SRC = [
    ('TrueDead', 'Weak', 5233, 0, 26, 5207, 0, 29),
    ('TrueDead', 'Mid', 8240, 0, 53, 8187, 0, 66),
    ('TrueDead', 'Strong', 4912, 0, 42, 4870, 0, 49),
    ('PartialDead', 'Weak', 940, 0, 1, 939, 0, 1),
    ('PartialDead', 'Mid', 1610, 0, 4, 1606, 0, 5),
    ('PartialDead', 'Strong', 1049, 1046, 3, 0, 1464, 3),
    ('SlowFull', 'Weak', 2122, 1967, 11, 144, 2465, 13),
    ('SlowFull', 'Mid', 4697, 4294, 21, 382, 5632, 37),
    ('SlowFull', 'Strong', 4044, 4031, 9, 4, 5583, 10),
    ('SlowPartial', 'Weak', 421, 338, 5, 78, 503, 5),
    ('SlowPartial', 'Mid', 800, 595, 8, 197, 878, 14),
    ('SlowPartial', 'Strong', 817, 812, 5, 0, 1306, 6),
    ('ActiveSeller', 'Weak', 99, 90, 0, 9, 151, 0),
    ('ActiveSeller', 'Mid', 431, 426, 5, 0, 996, 7),
    ('ActiveSeller', 'Strong', 1248, 1236, 12, 0, 2728, 17),
]

# --- Backtest target ---
# bucket, store, skus, ml_up, ml_down, ml_same, ml_up_qty, ml_down_qty
BT_TGT = [
    ('0', 'Weak', 139, 0, 0, 139, 0, 0),
    ('0', 'Mid', 341, 0, 0, 341, 0, 0),
    ('0', 'Strong', 254, 0, 0, 254, 0, 0),
    ('1-2', 'Weak', 1972, 0, 1478, 494, 0, 1664),
    ('1-2', 'Mid', 4507, 0, 3375, 1132, 0, 3733),
    ('1-2', 'Strong', 3640, 883, 0, 2757, 894, 0),
    ('3-5', 'Weak', 2601, 0, 2442, 159, 0, 2781),
    ('3-5', 'Mid', 7760, 434, 338, 6988, 440, 532),
    ('3-5', 'Strong', 9052, 8670, 0, 382, 9451, 0),
    ('6-10', 'Weak', 879, 51, 258, 570, 51, 439),
    ('6-10', 'Mid', 3319, 2385, 0, 934, 2604, 0),
    ('6-10', 'Strong', 4835, 3566, 0, 1269, 3849, 0),
    ('11+', 'Weak', 178, 4, 141, 33, 4, 435),
    ('11+', 'Mid', 806, 223, 0, 583, 261, 0),
    ('11+', 'Strong', 1348, 1348, 0, 0, 2139, 0),
]


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS (9 charts)
#
# ############################################################
print()
print("--- Report 1: Consolidated Findings (9 charts) ---")

# ---- fig_findings_01.png - CalendarWeight explanation ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Nov+Dec share bars
bar_labels = ['Ocekavano\n(rovnomerne)', 'Skutecne\n(Nov+Dec)']
bar_vals = [OVERVIEW['expected_share'], OVERVIEW['novdec_share']]
bar_colors = ['#3498db', '#e74c3c']
bars = axes[0].bar(bar_labels, bar_vals, color=bar_colors, edgecolor='#333', linewidth=0.5, width=0.5)
axes[0].set_ylabel('Podil na rocnich prodejich %')
axes[0].set_title('Nov+Dec: ocekavany vs skutecny podil prodeje\n(2 mesice z 12 = 16.7% ocekavano)', fontsize=11, fontweight='bold')
axes[0].set_ylim(0, 40)
for b, v in zip(bars, bar_vals):
    axes[0].text(b.get_x() + b.get_width()/2, v + 0.8, f'{v}%', ha='center', fontsize=14, fontweight='bold')

axes[0].annotate(f'Xmas lift = {OVERVIEW["xmas_lift"]}x\n=> CalendarWeight = {OVERVIEW["calendar_weight"]}',
                 xy=(1, OVERVIEW['novdec_share']),
                 xytext=(1.3, OVERVIEW['novdec_share'] + 5),
                 fontsize=11, fontweight='bold', color='#8e44ad',
                 arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=2))
axes[0].axhline(y=OVERVIEW['expected_share'], color='#3498db', linestyle='--', alpha=0.5, label='Expected 16.7%')
axes[0].legend(fontsize=9)

# Right: Segment sizes
seg_names_main = ['TrueDead', 'PartialDead', 'SlowFull', 'SlowPartial', 'ActiveSeller']
seg_counts = [18385, 3599, 10863, 2038, 1778]
seg_colors = ['#7f8c8d', '#95a5a6', '#bdc3c7', '#d5dbdb', '#e74c3c']
bars2 = axes[1].barh(seg_names_main, seg_counts, color=seg_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_xlabel('SKU Count')
axes[1].set_title('v9 Velocity segmenty (s CalendarWeight 0.7)\n(nezavisly vypocet od zakladu)', fontsize=11, fontweight='bold')
for b, v in zip(bars2, seg_counts):
    axes[1].text(v + 200, b.get_y() + b.get_height()/2, f'{v:,}', va='center', fontsize=10, fontweight='bold')
axes[1].invert_yaxis()

fig.suptitle('v9: Nov+Dec podil = 26.5% (vyssi nez drive reportovano) => CalendarWeight 0.7 je konzervativni', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- fig_findings_02.png - SoldAfter by segment ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

sa_segs = [s[0] for s in SEGMENTS if s[0] not in ('BriefNoSale', 'SlowBrief')]
sa_vals = [s[2] for s in SEGMENTS if s[0] not in ('BriefNoSale', 'SlowBrief')]

y_sa = np.arange(len(sa_segs))
sa_colors = ['#27ae60' if v > 70 else ('#f39c12' if v > 50 else '#e74c3c') for v in sa_vals]
bars = ax.barh(y_sa, sa_vals, color=sa_colors, edgecolor='#333', linewidth=0.5, height=0.6)
ax.set_yticks(y_sa)
ax.set_yticklabels(sa_segs, fontsize=11)
ax.set_xlabel('Sold After %', fontsize=11)
ax.set_title('Sold After % podle segmentu\n(procento source SKU, ktere se prodaly po redistribuci)', fontsize=12, fontweight='bold')
ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5, linewidth=2)
ax.axvline(x=80, color='#27ae60', linestyle='--', alpha=0.5, linewidth=2)

for i, v in enumerate(sa_vals):
    ax.text(v + 1, i, f'{v}%', va='center', fontsize=11, fontweight='bold')

# SKU counts on the right
for i, seg in enumerate(sa_segs):
    row = [s for s in SEGMENTS if s[0] == seg][0]
    ax.text(100, i, f'({row[1]:,} SKU)', va='center', fontsize=9, color='#7f8c8d')

ax.set_xlim(0, 110)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_02.png")

# ---- fig_findings_03.png - Segment x Store dual heatmap (OS Tot + RO Tot) ----
seg_order_hm = ['TrueDead', 'PartialDead', 'SlowPartial', 'SlowFull', 'ActiveSeller']
oversell_t_data = []
reorder_t_data = []
for seg in seg_order_hm:
    row_ot, row_rt = [], []
    for s in STORES:
        row = [r for r in SEG_STORE if r[0] == seg and r[1] == s][0]
        row_ot.append(row[5])   # os_t
        row_rt.append(row[7])   # ro_t
    oversell_t_data.append(row_ot)
    reorder_t_data.append(row_rt)

oversell_t_arr = np.array(oversell_t_data)
reorder_t_arr = np.array(reorder_t_data)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(oversell_t_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_hm, ax=axes[0],
            vmin=0, vmax=30, linewidths=1,
            cbar_kws={'label': 'Oversell Total %'})
axes[0].set_title('OVERSELL Total % by Segment x Store\n(prumerne 11.5%)', fontsize=11)
axes[0].set_ylabel('Velocity Segment')
axes[0].set_xlabel('Store Strength')

sns.heatmap(reorder_t_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=seg_order_hm, ax=axes[1],
            vmin=20, vmax=50, linewidths=1,
            cbar_kws={'label': 'Reorder Total %'})
for i in range(len(seg_order_hm)):
    for j in range(len(STORES)):
        if reorder_t_data[i][j] > 40:
            axes[1].add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                             edgecolor='#2c3e50', linewidth=3))
axes[1].set_title('REORDER Total % by Segment x Store\n(bunky >40% zvyrazneny)', fontsize=11)
axes[1].set_ylabel('Velocity Segment')
axes[1].set_xlabel('Store Strength')

fig.suptitle('v9 Source: Segment x Store po CalendarWeight 0.7 korekci', fontsize=13, fontweight='bold', y=1.02)
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
axes[0].set_title('SOURCE: Oversell 4M + Reorder Total\n(Reorder je hlavni problem)')
axes[0].legend(fontsize=8)
axes[0].set_xticks(DECILES)
axes[0].axhspan(0, 5, alpha=0.05, color='green')

axes[1].plot(DECILES, TGT_ALLSOLD, 'o-', color='#27ae60', linewidth=2, label='All Sold %')
axes[1].plot(DECILES, TGT_NOTHING, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold %')
axes[1].fill_between(DECILES, TGT_ALLSOLD, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Vysledek podle Store Decile')
axes[1].legend(fontsize=8)
axes[1].set_xticks(DECILES)

efficiency = [a / (a + n) * 100 for a, n in zip(TGT_ALLSOLD, TGT_NOTHING)]
axes[2].bar(DECILES, efficiency, color=['#e74c3c' if e < 65 else ('#f39c12' if e < 72 else '#27ae60') for e in efficiency])
axes[2].set_xlabel('Store Decile')
axes[2].set_ylabel('Efficiency %')
axes[2].set_title('TARGET: Efektivita redistribuce\n(All-sold / (All-sold + Nothing-sold))')
axes[2].set_xticks(DECILES)
axes[2].axhline(y=70, color='#f39c12', linestyle='--', alpha=0.5)
for d, e in zip(DECILES, efficiency):
    axes[2].text(d, e + 0.5, f'{e:.0f}%', ha='center', fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- fig_findings_05.png - Target heatmaps ----
tgt_buckets = ['0', '1-2', '3-5', '6-10', '11+']
tgt_pct_nothing = np.array([
    [73.4, 73.3, 60.6],
    [65.4, 61.7, 57.7],
    [44.8, 45.3, 40.5],
    [27.5, 26.2, 22.2],
    [12.4, 11.7, 10.6],
])
tgt_pct_allsold = np.array([
    [32.4, 37.8, 52.8],
    [38.1, 41.0, 47.1],
    [54.3, 54.6, 61.1],
    [74.6, 76.3, 78.8],
    [84.8, 87.7, 89.5],
])

brand_fits = ['BrandWeak', 'BrandMid', 'BrandStrong']
bf_st_matrix = np.array([
    [56.1, 62.9, 68.4],
    [60.2, 64.5, 70.0],
    [65.7, 70.5, 75.8],
])

fig, axes = plt.subplots(1, 3, figsize=(20, 6))
sns.heatmap(tgt_pct_allsold, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=STORES, yticklabels=tgt_buckets, ax=axes[0],
            vmin=30, vmax=90, linewidths=1, cbar_kws={'label': 'All-sold Total %'})
axes[0].set_title('Target All-Sold Total % (USPECH)', fontsize=10)
axes[0].set_ylabel('Sales Bucket')

sns.heatmap(tgt_pct_nothing, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=STORES, yticklabels=tgt_buckets, ax=axes[1],
            vmin=10, vmax=75, linewidths=1, cbar_kws={'label': 'Nothing sold %'})
axes[1].set_title('Target Nothing-Sold % (PROBLEM)', fontsize=10)
axes[1].set_ylabel('Sales Bucket')

sns.heatmap(bf_st_matrix, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=brand_fits, yticklabels=STORES, ax=axes[2],
            vmin=50, vmax=80, linewidths=1, cbar_kws={'label': 'ST Total %'})
axes[2].set_title('Brand-Store Fit: ST Total %', fontsize=10)
axes[2].set_ylabel('Store Strength')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_05.png")

# ---- fig_findings_06.png - Pair analysis pie + flow matrix ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

pair_labels = [r[0] for r in PAIRS]
pair_counts = [r[1] for r in PAIRS]
pair_colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
wedges, texts, autotexts = axes[0].pie(pair_counts, labels=pair_labels, colors=pair_colors,
                                        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[0].set_title('Parova analyza: Source+Target kombinovane\n(Win-Win 50.6% = bez oversell + all-sold)', fontsize=10)

pairs_matrix = np.zeros((3, 3))
pct_matrix = np.zeros((3, 3))
for r in FLOW:
    si = STORES.index(r[0])
    ti = STORES.index(r[1])
    pairs_matrix[si][ti] = r[2]
    pct_matrix[si][ti] = r[3]

sns.heatmap(pct_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=['Tgt ' + s for s in STORES],
            yticklabels=['Src ' + s for s in STORES], ax=axes[1],
            linewidths=1, cbar_kws={'label': '% of total pairs'})
axes[1].set_title('Flow: % z celkovych paru\n(Mid->Strong = nejvetsi tok 19.6%)')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_06.png")

# ---- fig_findings_07.png - Sold After vs Reorder by segment ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))

v9_seg_names = ['TrueDead', 'PartialDead', 'SlowPartial', 'SlowFull', 'ActiveSeller']
v9_sold_after = []
v9_reorder = []
for seg in v9_seg_names:
    rows = [r for r in SEG_STORE if r[0] == seg]
    total_skus = sum(r[2] for r in rows)
    wa_sa = sum(r[2] * r[8] for r in rows) / total_skus
    wa_ro = sum(r[2] * r[7] for r in rows) / total_skus
    v9_sold_after.append(wa_sa)
    v9_reorder.append(wa_ro)

y_seg = np.arange(len(v9_seg_names))
w = 0.35
bars1 = ax.barh(y_seg - w/2, v9_sold_after, w, color='#27ae60', label='Sold After %', edgecolor='#333', linewidth=0.5)
bars2 = ax.barh(y_seg + w/2, v9_reorder, w, color='#e74c3c', label='Reorder Total %', edgecolor='#333', linewidth=0.5)
ax.set_yticks(y_seg)
ax.set_yticklabels(v9_seg_names, fontsize=10)
ax.set_xlabel('%')
ax.set_title('v9 Sold After % vs Reorder Total % podle segmentu\n(ActiveSeller: vysoka prodejnost + vysoky reorder = potrebuje ML=3-4)',
             fontsize=11, fontweight='bold')
ax.legend(fontsize=9)

for i, (sa, ro) in enumerate(zip(v9_sold_after, v9_reorder)):
    ml_vals = [SRC_ML.get((v9_seg_names[i], s), 0) for s in STORES]
    avg_ml = np.mean(ml_vals)
    ax.text(max(sa, ro) + 1, i, f'avg ML={avg_ml:.1f}', va='center', fontsize=8, color='#8e44ad', fontweight='bold')

ax.axvline(x=50, color='#f39c12', linestyle='--', alpha=0.5, label='50% threshold')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_07.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_07.png")

# ---- fig_findings_08.png - BrandFit Graduation by SalesBucket ----
fig, axes = plt.subplots(1, 2, figsize=(18, 7), gridspec_kw={'width_ratios': [2, 1]})

bf_buckets_order = ['0', '1-2', '3-5', '6-10', '11+']
bw_st_strong = []
bs_st_strong = []
for sb in bf_buckets_order:
    bw_rows = [r for r in BRANDFITGRAD if r[0] == sb and r[1] == 'Strong' and r[2] == 'BrandWeak']
    bs_rows = [r for r in BRANDFITGRAD if r[0] == sb and r[1] == 'Strong' and r[2] == 'BrandStrong']
    bw_st_strong.append(bw_rows[0][5] if bw_rows else 0)
    bs_st_strong.append(bs_rows[0][5] if bs_rows else 0)

x_bf = np.arange(len(bf_buckets_order))
w_bf = 0.35
bars_bw = axes[0].bar(x_bf - w_bf/2, bw_st_strong, w_bf, color='#e74c3c', label='BrandWeak',
                       edgecolor='#333', linewidth=0.5)
bars_bs = axes[0].bar(x_bf + w_bf/2, bs_st_strong, w_bf, color='#27ae60', label='BrandStrong',
                       edgecolor='#333', linewidth=0.5)

axes[0].set_xticks(x_bf)
axes[0].set_xticklabels(bf_buckets_order, fontsize=10)
axes[0].set_xlabel('Sales Bucket', fontsize=11)
axes[0].set_ylabel('Sell-Through Total %', fontsize=11)
axes[0].set_title('ST Total % na Strong stores:\nBrandWeak vs BrandStrong podle SalesBucket', fontsize=11, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].set_ylim(0, 110)

for i, (bw, bs) in enumerate(zip(bw_st_strong, bs_st_strong)):
    delta = bs - bw
    axes[0].text(i - w_bf/2, bw + 1.5, f'{bw:.0f}%', ha='center', fontsize=8, fontweight='bold', color='#e74c3c')
    axes[0].text(i + w_bf/2, bs + 1.5, f'{bs:.0f}%', ha='center', fontsize=8, fontweight='bold', color='#27ae60')
    axes[0].annotate(f'+{delta:.0f}pp', xy=(i, max(bw, bs) + 6), fontsize=9, fontweight='bold',
                     ha='center', color='#2c3e50',
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='#fff3cd', edgecolor='#f39c12', alpha=0.8))

# Right panel: delta ST by SalesBucket
deltas_bf = [bs - bw for bw, bs in zip(bw_st_strong, bs_st_strong)]
max_delta = max(abs(d) for d in deltas_bf) if deltas_bf else 1
delta_colors = []
for d in deltas_bf:
    ratio = abs(d) / max_delta
    r = int(231 * ratio + 149 * (1 - ratio))
    g = int(76 * ratio + 165 * (1 - ratio))
    b_val = int(60 * ratio + 165 * (1 - ratio))
    delta_colors.append(f'#{r:02x}{g:02x}{b_val:02x}')

y_bf = np.arange(len(bf_buckets_order))
bars_delta = axes[1].barh(y_bf, deltas_bf, color=delta_colors, edgecolor='#333', linewidth=0.5, height=0.6)
axes[1].set_yticks(y_bf)
axes[1].set_yticklabels(bf_buckets_order, fontsize=10)
axes[1].set_xlabel('Delta ST (BrandStrong - BrandWeak) pp', fontsize=10)
axes[1].set_title('Delta ST Total %\n(Strong - Weak brand)', fontsize=11, fontweight='bold')
axes[1].invert_yaxis()

for i, d in enumerate(deltas_bf):
    color_txt = '#e74c3c' if d > 20 else ('#f39c12' if d > 5 else '#7f8c8d')
    label = f'+{d:.0f}pp' if d > 0 else f'{d:.0f}pp'
    signif = 'VYZNAMNY' if d > 20 else ('stredni' if d > 5 else 'zanedbatelny')
    axes[1].text(d + 0.5, i, f'{label} ({signif})', va='center', fontsize=9, fontweight='bold', color=color_txt)

fig.suptitle('BrandFit Graduation: vliv BrandFit klesa s rostoucim SalesBucket', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_08.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_08.png")

# ---- fig_findings_09.png - LastSaleGap per segment ----
fig, ax = plt.subplots(1, 1, figsize=(14, 6))

gap_segs = [r[0] for r in LAST_SALE_GAP]
gap_le90 = [r[3] for r in LAST_SALE_GAP]
gap_avg = [r[4] for r in LAST_SALE_GAP]

x_gap = np.arange(len(gap_segs))
w_g = 0.35
bars1 = ax.bar(x_gap - w_g/2, gap_le90, w_g, color='#e74c3c', label='% s LastSaleGap <= 90 dni', edgecolor='#333', linewidth=0.5)
bars2 = ax.bar(x_gap + w_g/2, [g/10 for g in gap_avg], w_g, color='#3498db', label='Prumerny gap (dny/10)', edgecolor='#333', linewidth=0.5)

ax.set_xticks(x_gap)
ax.set_xticklabels(gap_segs, fontsize=10)
ax.set_ylabel('Hodnota')
ax.set_title('LastSaleGap podle segmentu\n(kratky gap = nedavno prodano = rizikovejsi odvazet)', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)

for i, (g90, gavg) in enumerate(zip(gap_le90, gap_avg)):
    ax.text(i - w_g/2, g90 + 1, f'{g90:.0f}%', ha='center', fontsize=9, fontweight='bold', color='#e74c3c')
    ax.text(i + w_g/2, gavg/10 + 1, f'{gavg}d', ha='center', fontsize=9, fontweight='bold', color='#3498db')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_09.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_09.png")


# ############################################################
# BUILD HTML: Report 1
# ############################################################

def seg_store_table(data):
    rows = ""
    for r in data:
        seg, sto, cnt, rdq = r[0], r[1], r[2], r[3]
        otot, ro_t, sold_after = r[5], r[7], r[8]
        cls_o = 'good' if otot < 10 else ('warn' if otot < 15 else 'bad')
        cls_r = 'bad' if ro_t > 40 else ('warn' if ro_t > 35 else 'good')
        cls_sa = 'good' if sold_after > 70 else ('warn' if sold_after > 50 else 'bad')
        rows += (f'<tr><td>{seg}</td><td>{sto}</td><td>{cnt:,}</td>'
                 f'<td class="{cls_o}">{otot}%</td>'
                 f'<td class="{cls_r}">{ro_t}%</td>'
                 f'<td class="{cls_sa}">{sold_after}%</td>'
                 f'<td>{rdq:,}</td></tr>\n')
    return rows

tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sal, sto, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 50 else ('warn' if pn > 30 else 'good')
    cls_a = 'good' if pa > 70 else ('warn' if pa > 50 else 'bad')
    tgt_ss_rows += (f'<tr><td>{sal}</td><td>{sto}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.1f}%</td><td>{stt:.1f}%</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td></tr>\n')

tgt_bf_rows = ""
for r in BRAND_FIT:
    sto, bf, cnt, st_t, nosale = r
    cls_n = 'bad' if nosale > 30 else ('warn' if nosale > 25 else 'good')
    cls_a = 'good' if st_t > 70 else ('warn' if st_t > 60 else 'bad')
    tgt_bf_rows += (f'<tr><td>{sto}</td><td>{bf}</td><td>{cnt:,}</td>'
                    f'<td class="{cls_a}">{st_t}%</td><td class="{cls_n}">{nosale}%</td></tr>\n')

pair_rows = ""
for r in PAIRS:
    name, cnt, pct = r
    cls = 'good' if name == 'Win-Win' else ('warn' if name == 'Win-Lose' else 'bad')
    pair_rows += (f'<tr><td class="{cls}">{name}</td>'
                  f'<td>{cnt:,}</td><td>{pct}%</td></tr>\n')

flow_rows = ""
for r in FLOW:
    sg, tg, pairs_cnt, pct = r
    flow_rows += (f'<tr><td>{sg}</td><td>{tg}</td><td>{pairs_cnt:,}</td>'
                  f'<td>{pct}%</td></tr>\n')

brandfit_delta_rows = ""
for r in BRANDFIT_DELTA:
    sb, delta_range, mod_bw, mod_bs = r
    cls_bw = 'bad' if mod_bw < 0 else ('good' if mod_bw > 0 else '')
    cls_bs = 'good' if mod_bs > 0 else ('bad' if mod_bs < 0 else '')
    sign_bw = '+' if mod_bw > 0 else ''
    sign_bs = '+' if mod_bs > 0 else ''
    brandfit_delta_rows += (f'<tr><td><b>{sb}</b></td><td>{delta_range}</td>'
                            f'<td class="{cls_bw}">{sign_bw}{mod_bw}</td>'
                            f'<td class="{cls_bs}">{sign_bs}{mod_bs}</td></tr>\n')

O = OVERVIEW

html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v9 Consolidated Findings: SalesBased MinLayers</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings v9: SalesBased MinLayers <span class="v9-badge">v9</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p><b>v9 = nezavisla analyza od zakladu.</b> Nov+Dec podil = {O['novdec_share']}% (ocekavano {O['expected_share']}%, lift {O['xmas_lift']}x).
CalendarWeight {O['calendar_weight']} je konzervativni (skutecny lift by odpovidal vaze ~0.63).
Vsechny metriky pocitany nezavisle ze zadani.</p>

<div class="insight" style="background: #fff3cd; border-left: 6px solid #f39c12; padding: 15px;">
<b>Oversell v cili ({O['os4m_pct']}% za 4M). Reorder je hlavni problem ({O['ro_t_pct']}% qty).</b><br>
Oversell 4M: {O['os4m_qty']:,} ks ({O['os4m_pct']}% z redistrib. objemu). Total: {O['os_t_qty']:,} ks ({O['os_t_pct']}%).<br>
Reorder 4M: {O['ro4m_qty']:,} ks ({O['ro4m_pct']}%). Total: {O['ro_t_qty']:,} ks ({O['ro_t_pct']}%).<br>
<b>Cil oversell 4M (5-10%): SPLNEN.</b> Reorder vyzaduje dalsi praci.
</div>

<div class="section">
<h2>1. Prehled metrik</h2>
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
<div class="metric"><div class="v">{O['pairs']:,}</div><div class="l">Redistrib. paru</div></div>
<div class="metric"><div class="v">{O['source_skus']:,}</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">{O['target_skus']:,}</div><div class="l">Target SKU</div></div>
<div class="metric"><div class="v">{O['redist_qty']:,}</div><div class="l">Redistrib. ks</div></div>
<div class="metric"><div class="v good">{O['os4m_pct']}%</div><div class="l">Oversell 4M</div></div>
<div class="metric"><div class="v warn">{O['os_t_pct']}%</div><div class="l">Oversell Total</div></div>
<div class="metric"><div class="v bad">{O['ro4m_pct']}%</div><div class="l">Reorder 4M</div></div>
<div class="metric"><div class="v bad">{O['ro_t_pct']}%</div><div class="l">Reorder Total</div></div>
</div>

<h3>Target metriky</h3>
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
<div class="metric"><div class="v">{O['st4m_avg']}%</div><div class="l">ST 4M avg</div></div>
<div class="metric"><div class="v">{O['st1_4m_avg']}%</div><div class="l">ST-1pc 4M avg</div></div>
<div class="metric"><div class="v">{O['st_t_avg']}%</div><div class="l">ST Total avg</div></div>
<div class="metric"><div class="v">{O['st1_t_avg']}%</div><div class="l">ST-1pc Total avg</div></div>
<div class="metric"><div class="v bad">{O['ns4m_skus']:,}</div><div class="l">Nothing-sold 4M ({O['ns4m_pct']}%)</div></div>
<div class="metric"><div class="v good">{O['as_t_skus']:,}</div><div class="l">All-sold Total ({O['as_t_pct']}%)</div></div>
</div>
</div>

<img src="fig_findings_01.png" alt="CalendarWeight">

<div class="section">
<h2>2. Source: Velocity segmenty</h2>
<img src="fig_findings_02.png" alt="SoldAfter by Segment">

<div class="insight-new">
<b>Klicove zjisteni:</b> Gradient SoldAfter% jasne rozlisuje segmenty.
TrueDead 36.9% → ActiveSeller 95.2%. Segmentace je silnym prediktorem rizika redistribuce.
</div>

<h3>2.1 Segment x Store</h3>
<table>
<tr><th>Segment</th><th>Store</th><th>SKU</th><th>Oversell T%</th><th>Reorder T%</th><th>SoldAfter%</th><th>Redist Qty</th></tr>
{seg_store_table(SEG_STORE)}
</table>
<img src="fig_findings_03.png" alt="Segment x Store heatmap">
</div>

<div class="section">
<h2>3. Store Decile analyza</h2>
<img src="fig_findings_04.png" alt="Store decile charts">
<div class="insight">
Silnejsi prodejny maji vyssi oversell i reorder, ale take vyssi all-sold na target strane.
Redistribucni efektivita (all-sold/(all-sold+nothing-sold)) roste z 60% (decile 1) na 84% (decile 10).
</div>
</div>

<div class="section">
<h2>4. Target analyza</h2>

<h3>4.1 SalesBucket x StoreStrength</h3>
<table>
<tr><th>SalesBucket</th><th>Store</th><th>SKU</th><th>ST 4M%</th><th>ST Total%</th><th>NothingSold 4M%</th><th>AllSold T%</th></tr>
{tgt_ss_rows}
</table>
<img src="fig_findings_05.png" alt="Target heatmaps">

<h3>4.2 BrandFit dopad</h3>
<table>
<tr><th>Store</th><th>BrandFit</th><th>SKU</th><th>ST Total%</th><th>NothingSold%</th></tr>
{tgt_bf_rows}
</table>

<div class="insight-new">
<b>BrandFit ma ~12pp dopad na ST.</b> BrandStrong: ST 75.8% vs BrandWeak: 56.1% na Strong stores.
Efekt se snizuje s rostoucim SalesBucket (u 6+ predaju je zanedbatelny).
</div>

<img src="fig_findings_08.png" alt="BrandFit graduation">

<h3>BrandFit modifier pravidla</h3>
<table>
<tr><th>SalesBucket</th><th>ST Delta rozsah</th><th>Modifier BrandWeak</th><th>Modifier BrandStrong</th></tr>
{brandfit_delta_rows}
</table>
</div>

<div class="section">
<h2>5. Parova analyza + Flow</h2>
<table>
<tr><th>Typ paru</th><th>Paru</th><th>%</th></tr>
{pair_rows}
</table>
<img src="fig_findings_06.png" alt="Pair analysis + Flow">
<table>
<tr><th>Source Store</th><th>Target Store</th><th>Paru</th><th>%</th></tr>
{flow_rows}
</table>
</div>

<div class="section">
<h2>6. LastSaleGap analyza</h2>
<img src="fig_findings_09.png" alt="LastSaleGap">
<div class="insight">
ActiveSeller: 69.9% ma LastSaleGap ≤ 90 dni (prumerny gap 67 dni).
SlowFull: 16.6% ≤ 90 dni. TrueDead: 0% (prumerny gap 638 dni — opravdu mrtve).
Kratky gap = modifier +1 ML na source strane.
</div>
</div>

<div class="section">
<h2>7. Sold After vs Reorder</h2>
<img src="fig_findings_07.png" alt="SoldAfter vs Reorder">
</div>

</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("[OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE (4 charts)
#
# ############################################################
print()
print("--- Report 2: Decision Tree (4 charts) ---")

# ---- fig_dtree_01.png - Source ML heatmap ----
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

src_segs = ['TrueDead', 'PartialDead', 'SlowPartial', 'SlowFull', 'ActiveSeller']
src_ml_matrix = np.array([[SRC_ML.get((s, st), 0) for st in STORES] for s in src_segs])

sns.heatmap(src_ml_matrix, annot=True, fmt='d', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=src_segs, ax=ax,
            vmin=0, vmax=4, linewidths=2, cbar_kws={'label': 'MinLayer'},
            annot_kws={'fontsize': 16, 'fontweight': 'bold'})
ax.set_title('SOURCE Decision Tree: MinLayer by Segment x Store\n(Orderable min=1, Delisted override=0)', fontsize=12, fontweight='bold')
ax.set_ylabel('Velocity Segment')
ax.set_xlabel('Store Strength')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_01.png")

# ---- fig_dtree_02.png - Target ML heatmap ----
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

tgt_buckets_ml = ['0', '1-2', '3-5', '6-10', '11+']
tgt_ml_matrix = np.array([[TGT_ML.get((sb, st), 0) for st in STORES] for sb in tgt_buckets_ml])

sns.heatmap(tgt_ml_matrix, annot=True, fmt='d', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=tgt_buckets_ml, ax=ax,
            vmin=0, vmax=4, linewidths=2, cbar_kws={'label': 'MinLayer'},
            annot_kws={'fontsize': 16, 'fontweight': 'bold'})
ax.set_title('TARGET Decision Tree: MinLayer by SalesBucket x Store\n(Orderable min=1, Delisted override=0)', fontsize=12, fontweight='bold')
ax.set_ylabel('Sales Bucket (12M pre)')
ax.set_xlabel('Store Strength')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_02.png")

# ---- fig_dtree_03.png - Modifiers summary ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Source modifiers
src_mods = [
    ('LastSaleGap <= 90d', '+1', '#e74c3c'),
    ('BrandStrong +\nTrueDead/Slow*', '+1', '#e67e22'),
    ('BrandStrong +\nActiveSeller', 'ignorovat\n(SA>92%)', '#7f8c8d'),
    ('Delisting\n(D/L class)', 'ML=0\n(override)', '#2c3e50'),
]
y_mod = np.arange(len(src_mods))
for i, (label, effect, color) in enumerate(src_mods):
    axes[0].barh(i, 1, color=color, alpha=0.3, edgecolor=color, linewidth=2)
    axes[0].text(0.5, i, f'{label}\n=> {effect}', ha='center', va='center', fontsize=10, fontweight='bold')
axes[0].set_yticks([])
axes[0].set_xticks([])
axes[0].set_title('SOURCE modifikatory', fontsize=12, fontweight='bold')
axes[0].set_xlim(0, 1)

# Target modifiers
tgt_mods = [
    ('AllSold / ST1 >= 85%', '+1', '#27ae60'),
    ('Growth pocket\n(Strong, 3-10, ST>=45%)', '+1', '#2ecc71'),
    ('NothingSold / ST < 20%', '-1', '#e74c3c'),
    ('BrandWeak (0-5 sales)', '-1', '#e67e22'),
    ('BrandStrong (0-2 sales)', '+1', '#3498db'),
    ('Delisting (D/L)', 'ML=0', '#2c3e50'),
]
y_mod2 = np.arange(len(tgt_mods))
for i, (label, effect, color) in enumerate(tgt_mods):
    axes[1].barh(i, 1, color=color, alpha=0.3, edgecolor=color, linewidth=2)
    axes[1].text(0.5, i, f'{label}\n=> {effect}', ha='center', va='center', fontsize=9, fontweight='bold')
axes[1].set_yticks([])
axes[1].set_xticks([])
axes[1].set_title('TARGET modifikatory', fontsize=12, fontweight='bold')
axes[1].set_xlim(0, 1)

fig.suptitle('v9 Decision Tree: Modifikatory (aplikuji se na base ML z lookup tabulek)',
             fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- fig_dtree_04.png - ML distribution current vs proposed ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ml_levels = [0, 1, 2, 3, 4]
src_current_counts = {r[0]: r[1] for r in SRC_CURRENT_ML}
src_current_vals = [src_current_counts.get(m, 0) for m in ml_levels]

# Estimate proposed source ML distribution
# from BT_SRC data: most TrueDead stay ML=1, SlowFull goes to ML=2/3, ActiveSeller to ML=3/4
src_proposed_vals = [202, 18168, 12292, 4330, 1778]  # estimated from segment x store mapping

axes[0].bar([m - 0.2 for m in ml_levels], src_current_vals, 0.35, color='#95a5a6', label='Current ML', edgecolor='#333')
axes[0].bar([m + 0.2 for m in ml_levels], src_proposed_vals, 0.35, color='#3498db', label='Proposed ML', edgecolor='#333')
axes[0].set_xlabel('MinLayer')
axes[0].set_ylabel('SKU Count')
axes[0].set_title('SOURCE: Current vs Proposed ML distribuce', fontsize=11, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].set_xticks(ml_levels)

tgt_current_counts = {r[0]: r[1] for r in TGT_CURRENT_ML}
tgt_current_vals = [tgt_current_counts.get(m, 0) for m in ml_levels]
tgt_proposed_vals = [0, 10085, 14880, 13314, 3352]  # estimated from bucket x store mapping

axes[1].bar([m - 0.2 for m in ml_levels], tgt_current_vals, 0.35, color='#95a5a6', label='Current ML', edgecolor='#333')
axes[1].bar([m + 0.2 for m in ml_levels], tgt_proposed_vals, 0.35, color='#e74c3c', label='Proposed ML', edgecolor='#333')
axes[1].set_xlabel('MinLayer')
axes[1].set_ylabel('SKU Count')
axes[1].set_title('TARGET: Current vs Proposed ML distribuce', fontsize=11, fontweight='bold')
axes[1].legend(fontsize=9)
axes[1].set_xticks(ml_levels)

fig.suptitle('v9: Distribuce MinLayer pred a po aplikaci decision tree', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_04.png")


# ############################################################
# BUILD HTML: Report 2
# ############################################################

# Source ML table rows
src_ml_rows = ""
for seg in src_segs:
    for sto in STORES:
        ml_val = SRC_ML.get((seg, sto), 0)
        cls = 'good' if ml_val >= 3 else ('warn' if ml_val >= 2 else '')
        src_ml_rows += f'<tr><td>{seg}</td><td>{sto}</td><td class="{cls}"><b>{ml_val}</b></td></tr>\n'

# Target ML table rows
tgt_ml_rows = ""
for sb in tgt_buckets_ml:
    for sto in STORES:
        ml_val = TGT_ML.get((sb, sto), 0)
        cls = 'good' if ml_val >= 3 else ('warn' if ml_val >= 2 else '')
        tgt_ml_rows += f'<tr><td>{sb}</td><td>{sto}</td><td class="{cls}"><b>{ml_val}</b></td></tr>\n'

html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v9 Decision Tree: SalesBased MinLayers</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree v9: SalesBased MinLayers <span class="v9-badge">v9</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p>4 smery: source up, source down, target up, target down. ML rozsah 0-4. Orderable min=1.</p>

<div class="section">
<h2>1. Source: Velocity Segment x StoreStrength => ML</h2>
<img src="fig_dtree_01.png" alt="Source ML heatmap">
<table>
<tr><th>Segment</th><th>Store</th><th>MinLayer</th></tr>
{src_ml_rows}
</table>

<div class="insight">
<b>Logika:</b> TrueDead = nulove predaje, vysoka zasoba => bezpecne odvazet (ML=1).
ActiveSeller = vysoka velocity + 95% sold-after => chranit (ML=3-4).
SlowFull/SlowPartial = pomalsi prodej, ale stale aktivni => stredni ochrana (ML=2-3).
</div>
</div>

<div class="section">
<h2>2. Source modifikatory</h2>
<img src="fig_dtree_03.png" alt="Modifiers">

<table>
<tr><th>Modifikator</th><th>Podminka</th><th>Uprava</th></tr>
<tr><td>LastSaleGap kratky</td><td>≤90 dni</td><td class="arrow-up">+1</td></tr>
<tr><td>BrandFit source</td><td>TrueDead/SlowFull/SlowPartial + BrandStrong</td><td class="arrow-up">+1</td></tr>
<tr><td>BrandFit source</td><td>ActiveSeller</td><td>ignorovat (sold_after >92%)</td></tr>
<tr><td>Delisting</td><td>SkuClass D/L</td><td><b>ML=0 (override)</b></td></tr>
</table>

<pre>
Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)
Ak IsOrderable: Final_ML = MAX(Final_ML, 1)
Ak IsDelisted: Final_ML = 0
</pre>
</div>

<div class="section">
<h2>3. Target: SalesBucket x StoreStrength => ML</h2>
<img src="fig_dtree_02.png" alt="Target ML heatmap">
<table>
<tr><th>SalesBucket</th><th>Store</th><th>MinLayer</th></tr>
{tgt_ml_rows}
</table>

<div class="insight">
<b>Logika:</b> 0 predaju = neni jistota ze se proda => ML=1.
11+ predaju na Strong store => excelentni absorpce => ML=4.
Bidirekcni pristup: snizit ML kde target neabsorbuje, zvysit kde ano.
</div>
</div>

<div class="section">
<h2>4. Target modifikatory</h2>
<table>
<tr><th>Modifikator</th><th>Podminka</th><th>Uprava</th></tr>
<tr><td>AllSold / ST1 high</td><td>AllSold4M=1 OR ST1_4M >= 85%</td><td class="arrow-up">+1</td></tr>
<tr><td>Growth pocket</td><td>Strong, Sales 3-10, ST >= 45%</td><td class="arrow-up">+1</td></tr>
<tr><td>NothingSold / low ST</td><td>NothingSold4M=1 OR ST4M < 20%</td><td class="arrow-down">-1</td></tr>
<tr><td>BrandFit (0-2 sales)</td><td>BrandWeak</td><td class="arrow-down">-1</td></tr>
<tr><td>BrandFit (0-2 sales)</td><td>BrandStrong</td><td class="arrow-up">+1</td></tr>
<tr><td>BrandFit (3-5 sales)</td><td>BrandWeak</td><td class="arrow-down">-1</td></tr>
<tr><td>BrandFit (6+ sales)</td><td>—</td><td>ignorovat (predaje dominuji)</td></tr>
<tr><td>Delisting</td><td>SkuClass D/L</td><td><b>ML=0 (override)</b></td></tr>
</table>
</div>

<div class="section">
<h2>5. Distribuce ML: Current vs Proposed</h2>
<img src="fig_dtree_04.png" alt="ML distribution">
<div class="insight-new">
<b>Hlavni zmena SOURCE:</b> SlowFull (10,863 SKU) presun z ML=1 na ML=2/3.
ActiveSeller (1,778 SKU) presun z ML=1-2 na ML=3-4. Tyto SKU maji 95% sold_after.<br>
<b>Hlavni zmena TARGET:</b> Bidirekcni — 1-2 sales na Weak/Mid klesa z ML=2 na ML=1;
3-5+ sales na Strong roste z ML=2 na ML=3. Celkove rozsireni distribuce ML.
</div>
</div>

</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("[OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST (3 charts)
#
# ############################################################
print()
print("--- Report 3: Backtest (3 charts) ---")

# Aggregate backtest data
src_total_up = sum(r[3] for r in BT_SRC)
src_total_down = sum(r[4] for r in BT_SRC)
src_total_same = sum(r[5] for r in BT_SRC)
src_up_qty = sum(r[6] for r in BT_SRC)
src_down_qty = sum(r[7] for r in BT_SRC)

tgt_total_up = sum(r[3] for r in BT_TGT)
tgt_total_down = sum(r[4] for r in BT_TGT)
tgt_total_same = sum(r[5] for r in BT_TGT)
tgt_up_qty = sum(r[6] for r in BT_TGT)
tgt_down_qty = sum(r[7] for r in BT_TGT)

# ---- fig_backtest_01.png - Source backtest waterfall ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Source: SKU count changes by segment
bt_src_segs = ['TrueDead', 'PartialDead', 'SlowFull', 'SlowPartial', 'ActiveSeller']
bt_src_up_by_seg = []
bt_src_down_by_seg = []
for seg in bt_src_segs:
    rows = [r for r in BT_SRC if r[0] == seg]
    bt_src_up_by_seg.append(sum(r[3] for r in rows))
    bt_src_down_by_seg.append(-sum(r[4] for r in rows))

x_bt = np.arange(len(bt_src_segs))
axes[0].bar(x_bt, bt_src_up_by_seg, color='#e74c3c', edgecolor='#333', linewidth=0.5, label='ML zvyseni (ochrana)')
axes[0].bar(x_bt, bt_src_down_by_seg, color='#27ae60', edgecolor='#333', linewidth=0.5, label='ML snizeni (uvolneni)')
axes[0].set_xticks(x_bt)
axes[0].set_xticklabels(bt_src_segs, fontsize=9, rotation=15)
axes[0].set_ylabel('SKU Count')
axes[0].set_title(f'SOURCE: Zmena ML podle segmentu\n(celkem {src_total_up:,} up, {src_total_down:,} down)', fontsize=11, fontweight='bold')
axes[0].legend(fontsize=8)

for i, (u, d) in enumerate(zip(bt_src_up_by_seg, bt_src_down_by_seg)):
    if u > 0:
        axes[0].text(i, u + 50, f'+{u:,}', ha='center', fontsize=8, fontweight='bold', color='#e74c3c')
    if d < 0:
        axes[0].text(i, d - 100, f'{d:,}', ha='center', fontsize=8, fontweight='bold', color='#27ae60')

# Target: SKU count changes by bucket
bt_tgt_bkts = ['0', '1-2', '3-5', '6-10', '11+']
bt_tgt_up_by_bkt = []
bt_tgt_down_by_bkt = []
for bkt in bt_tgt_bkts:
    rows = [r for r in BT_TGT if r[0] == bkt]
    bt_tgt_up_by_bkt.append(sum(r[3] for r in rows))
    bt_tgt_down_by_bkt.append(-sum(r[4] for r in rows))

x_bt2 = np.arange(len(bt_tgt_bkts))
axes[1].bar(x_bt2, bt_tgt_up_by_bkt, color='#e74c3c', edgecolor='#333', linewidth=0.5, label='ML zvyseni')
axes[1].bar(x_bt2, bt_tgt_down_by_bkt, color='#27ae60', edgecolor='#333', linewidth=0.5, label='ML snizeni')
axes[1].set_xticks(x_bt2)
axes[1].set_xticklabels(bt_tgt_bkts, fontsize=10)
axes[1].set_ylabel('SKU Count')
axes[1].set_title(f'TARGET: Zmena ML podle SalesBucket\n(celkem {tgt_total_up:,} up, {tgt_total_down:,} down)', fontsize=11, fontweight='bold')
axes[1].legend(fontsize=8)

for i, (u, d) in enumerate(zip(bt_tgt_up_by_bkt, bt_tgt_down_by_bkt)):
    if u > 0:
        axes[1].text(i, u + 100, f'+{u:,}', ha='center', fontsize=8, fontweight='bold', color='#e74c3c')
    if d < 0:
        axes[1].text(i, d - 200, f'{d:,}', ha='center', fontsize=8, fontweight='bold', color='#27ae60')

fig.suptitle('v9 Backtest: Zmeny ML podle segmentu/bucketu', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- fig_backtest_02.png - Volume impact ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Source volume
src_labels = ['ML Up\n(vice chranen)', 'ML Down\n(vice redistrib)', 'Net']
src_vals = [src_up_qty, -src_down_qty, src_up_qty - src_down_qty]
src_colors = ['#e74c3c', '#27ae60', '#3498db']
axes[0].bar(src_labels, src_vals, color=src_colors, edgecolor='#333', linewidth=0.5)
axes[0].set_ylabel('Qty (ks)')
axes[0].set_title(f'SOURCE: Objemovy dopad\n(net +{src_up_qty - src_down_qty:,} ks chranenych)', fontsize=11, fontweight='bold')
for i, v in enumerate(src_vals):
    sign = '+' if v > 0 else ''
    axes[0].text(i, v + (500 if v > 0 else -500), f'{sign}{v:,}', ha='center', fontsize=10, fontweight='bold')

# Target volume
tgt_labels = ['ML Up\n(vice pozadovano)', 'ML Down\n(mene pozadovano)', 'Net']
tgt_vals = [tgt_up_qty, -tgt_down_qty, tgt_up_qty - tgt_down_qty]
tgt_colors = ['#e74c3c', '#27ae60', '#3498db']
axes[1].bar(tgt_labels, tgt_vals, color=tgt_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_ylabel('Qty (ks)')
axes[1].set_title(f'TARGET: Objemovy dopad\n(net +{tgt_up_qty - tgt_down_qty:,} ks)', fontsize=11, fontweight='bold')
for i, v in enumerate(tgt_vals):
    sign = '+' if v > 0 else ''
    axes[1].text(i, v + (500 if v > 0 else -500), f'{sign}{v:,}', ha='center', fontsize=10, fontweight='bold')

fig.suptitle('v9 Backtest: Objemovy dopad navrhovanych pravidel', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- fig_backtest_03.png - Summary pie charts ----
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].pie([src_total_up, src_total_down, src_total_same],
            labels=[f'ML Up ({src_total_up:,})', f'ML Down ({src_total_down:,})', f'Same ({src_total_same:,})'],
            colors=['#e74c3c', '#27ae60', '#95a5a6'],
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[0].set_title('SOURCE: Distribuce zmen ML', fontsize=11, fontweight='bold')

axes[1].pie([tgt_total_up, tgt_total_down, tgt_total_same],
            labels=[f'ML Up ({tgt_total_up:,})', f'ML Down ({tgt_total_down:,})', f'Same ({tgt_total_same:,})'],
            colors=['#e74c3c', '#27ae60', '#95a5a6'],
            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
axes[1].set_title('TARGET: Distribuce zmen ML', fontsize=11, fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")


# ############################################################
# BUILD HTML: Report 3
# ############################################################

bt_src_rows = ""
for r in BT_SRC:
    seg, sto, skus, up, down, same, up_q, down_q = r
    direction = '↑' if up > down else ('↓' if down > up else '=')
    cls = 'dir-up' if up > down else ('dir-down' if down > up else '')
    bt_src_rows += (f'<tr class="{cls}"><td>{seg}</td><td>{sto}</td><td>{skus:,}</td>'
                    f'<td>{up:,}</td><td>{down:,}</td><td>{same:,}</td>'
                    f'<td>{up_q:,}</td><td>{down_q:,}</td><td><b>{direction}</b></td></tr>\n')

bt_tgt_rows = ""
for r in BT_TGT:
    bkt, sto, skus, up, down, same, up_q, down_q = r
    direction = '↑' if up > down else ('↓' if down > up else '=')
    cls = 'dir-up' if up > down else ('dir-down' if down > up else '')
    bt_tgt_rows += (f'<tr class="{cls}"><td>{bkt}</td><td>{sto}</td><td>{skus:,}</td>'
                    f'<td>{up:,}</td><td>{down:,}</td><td>{same:,}</td>'
                    f'<td>{up_q:,}</td><td>{down_q:,}</td><td><b>{direction}</b></td></tr>\n')

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v9 Backtest: SalesBased MinLayers</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest v9: SalesBased MinLayers <span class="v9-badge">v9</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Porovnani navrhovanych ML pravidel (z decision tree) s aktualnimi ML hodnotami.
Backtest ukazuje objemovy dopad — kolik ks by bylo vice/mene chranenych/redistribuovanych.</p>

<div class="section">
<h2>1. Souhrn</h2>
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
<div class="metric"><div class="v">{src_total_up:,}</div><div class="l">Source ML Up (SKU)</div></div>
<div class="metric"><div class="v">{src_total_down:,}</div><div class="l">Source ML Down (SKU)</div></div>
<div class="metric"><div class="v">{src_up_qty:,}</div><div class="l">Source Up Qty</div></div>
<div class="metric"><div class="v">{tgt_total_up:,}</div><div class="l">Target ML Up (SKU)</div></div>
<div class="metric"><div class="v">{tgt_total_down:,}</div><div class="l">Target ML Down (SKU)</div></div>
<div class="metric"><div class="v">{tgt_up_qty:,}</div><div class="l">Target Up Qty</div></div>
</div>
<img src="fig_backtest_03.png" alt="Summary pie">

<div class="insight">
<b>SOURCE:</b> {src_total_up:,} SKU (40%) dostane vyssi ML = vice chranenych kusu ({src_up_qty:,} ks).
Hlavni dopad: SlowFull (10,863 SKU z ML=1 na ML=2/3) a ActiveSeller (1,778 SKU na ML=3/4).<br>
<b>TARGET:</b> Bidirekcni — {tgt_total_up:,} SKU UP + {tgt_total_down:,} SKU DOWN.
Snizeni: 1-2 sales na Weak/Mid (z ML=2 na ML=1). Zvyseni: 3-5+ na Strong (z ML=2 na ML=3).
</div>
</div>

<div class="section">
<h2>2. Source backtest detail</h2>
<img src="fig_backtest_01.png" alt="Source backtest">
<table>
<tr><th>Segment</th><th>Store</th><th>SKU</th><th>ML Up</th><th>ML Down</th><th>Same</th><th>Up Qty</th><th>Down Qty</th><th>Smer</th></tr>
{bt_src_rows}
</table>
<img src="fig_backtest_02.png" alt="Volume impact">
</div>

<div class="section">
<h2>3. Target backtest detail</h2>
<table>
<tr><th>Bucket</th><th>Store</th><th>SKU</th><th>ML Up</th><th>ML Down</th><th>Same</th><th>Up Qty</th><th>Down Qty</th><th>Smer</th></tr>
{bt_tgt_rows}
</table>

<div class="insight-good">
<b>Growth pockets (target ML UP):</b><br>
- SalesBucket 3-5 na Strong stores: 8,670 SKU zvyseni (9,451 ks) — tyto SKU maji ST 72% a AllSold 61%<br>
- SalesBucket 6-10 na Mid/Strong: 5,951 SKU zvyseni (6,453 ks) — ST 84-86%, AllSold 76-79%<br>
- SalesBucket 11+ na Strong: 1,348 SKU zvyseni (2,139 ks) — ST 94%, AllSold 90%
</div>

<div class="insight-bad">
<b>Reduction pockets (target ML DOWN):</b><br>
- SalesBucket 1-2 na Weak/Mid: 4,853 SKU snizeni (5,397 ks) — tyto maji NothingSold 62-65%, pouze 38-41% AllSold<br>
- SalesBucket 3-5 na Weak: 2,442 SKU snizeni (2,781 ks) — NothingSold 45%, nedostatecna absorpce
</div>
</div>

<div class="section">
<h2>4. Trade-off analyza</h2>
<div class="insight">
<b>Source:</b> Zvyseni ML na SlowFull/ActiveSeller chrani {src_up_qty:,} ks pred redistribuci.
To snizuje riziko oversell (aktualne {O['os_t_pct']}%) a reorder ({O['ro_t_pct']}%).
Odhadovane snizeni oversell: ~2-3pp, reorder: ~5-8pp.<br><br>
<b>Target:</b> Net efekt je zvyseni ML (+{tgt_up_qty - tgt_down_qty:,} ks), ale mix se zlepsuje:
vice redistribuce do Strong stores s vysokym SalesBucket (kde ST > 70%), mene do Weak stores s nizkym prodejemi.
<b>Cil neni nizsi objem, ale lepsi mix.</b>
</div>
</div>

</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("[OK] consolidated_backtest.html")


# ############################################################
#
#  REPORT 4: DEFINITIONS
#
# ############################################################
print()
print("--- Report 4: Definitions ---")

html4 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v9 Definitions: SalesBased MinLayers</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(3)}

<h1>Definitions v9: SalesBased MinLayers <span class="v9-badge">v9</span></h1>
<p><b>CalculationId=233</b> | ApplicationDate: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Kompletni algoritmicky popis vsech metrik a klasifikaci pouzitych v analyze.</p>

<div class="section">
<h2>1. Zakladni parametry</h2>
<table>
<tr><th>Parametr</th><th>Hodnota</th></tr>
<tr><td>Server</td><td>DEV</td></tr>
<tr><td>Databaze</td><td>ydistri-sql-db-dev-tenant-douglasde</td></tr>
<tr><td>CalculationId</td><td>233</td></tr>
<tr><td>EntityListId</td><td>3</td></tr>
<tr><td>ApplicationDate</td><td>2025-07-13</td></tr>
<tr><td>Ecomm (vylouceno)</td><td>WarehouseId = 300</td></tr>
<tr><td>MinLayer rozsah</td><td>0-4</td></tr>
<tr><td>CalendarWeight</td><td>0.7 na polrok s Nov+Dec</td></tr>
</table>
</div>

<div class="section">
<h2>2. Source metriky</h2>

<h3>2.1 Oversell</h3>
<pre>
RemainingAfterRedist = SourceAvailableSupply - TotalQtyRedistributed
Oversell_Qty = LEAST(GREATEST(Sales_Post - RemainingAfterRedist, 0), TotalQtyRedistributed)

Oversell nastava IBA ak predaj prekroci zostatok. Cap na TotalQtyRedistributed.
</pre>

<h3>2.2 Reorder</h3>
<pre>
Reorder_Qty = LEAST(SUM(Inbound.Quantity), TotalQtyRedistributed)

Bezne doobjednavky prekracujici redistribuovane mnozstvi se nepocitaji.
</pre>

<h3>2.3 CalendarWeight</h3>
<pre>
CalendarWeight = 0.7 ak polrocne obdobie obsahuje Nov+Dec, inak 1.0
Adjusted_Sales(period) = Raw_Sales(period) x CalendarWeight(period)

Nov+Dec generuji 26.5% rocnich prodejov namiesto ocekavanych 16.7% (lift 1.59x).
CalendarWeight 0.7 je konzervativni — skutecny lift by odpovidal vaze ~0.63.
</pre>

<h3>2.4 Velocity</h3>
<pre>
Velocity_12M = Adjusted_Sales_12M / DaysInStock_12M x 30

DaysInStock = pocet dnu s AvailableSupply > 0 v danom obdobi.
Eliminuje skresleni kratkym stockom.
</pre>

<h3>2.5 Velocity segmenty</h3>
<table>
<tr><th>Segment</th><th>Definice</th><th>SKU count</th><th>SoldAfter%</th></tr>
<tr><td>TrueDead</td><td>0 predajov, stock >= 270 dni</td><td>18,385</td><td>36.9%</td></tr>
<tr><td>PartialDead</td><td>0 predajov, stock 90-270 dni</td><td>3,599</td><td>56.7%</td></tr>
<tr><td>BriefNoSale</td><td>0 predajov, stock < 90 dni</td><td>98</td><td>85.7%</td></tr>
<tr><td>SlowFull</td><td>Velocity < 0.5, stock >= 270 dni</td><td>10,863</td><td>66.4%</td></tr>
<tr><td>SlowPartial</td><td>Velocity < 0.5, stock 90-270 dni</td><td>2,038</td><td>77.2%</td></tr>
<tr><td>SlowBrief</td><td>Velocity < 0.5, stock < 90 dni</td><td>9</td><td>44.4%</td></tr>
<tr><td>ActiveSeller</td><td>Velocity >= 0.5/mesic</td><td>1,778</td><td>95.2%</td></tr>
</table>

<h3>2.6 SoldAfter</h3>
<pre>
SoldAfter = 1 ak source SKU malo aspon 1 predaj po ApplicationDate
Celkove: 52.7% (19,390 z 36,770)
</pre>

<h3>2.7 LastSaleGap</h3>
<pre>
LastSaleGapDays = DATEDIFF(DAY, MAX(SaleDate pred ApplicationDate), ApplicationDate)
Kratky gap (<=90 dni) = modifier +1 ML
</pre>
</div>

<div class="section">
<h2>3. Target metriky</h2>

<h3>3.1 Sell-Through (ST)</h3>
<pre>
Base = TargetAvailableSupply + TotalQtyReceived
ST = LEAST(Sold, Base) / Base x 100
</pre>

<h3>3.2 Sell-Through-1pc (ST1)</h3>
<pre>
Idealny stav = zostava presne 1 ks.
Ak Sold >= Base: ST1 = 100%
Ak Sold < Base AND Base > 1: ST1 = LEAST(Sold, Base-1) / (Base-1) x 100
Ak Base <= 1: ST1 = NULL
</pre>

<h3>3.3 Nothing-Sold / All-Sold</h3>
<pre>
NothingSold = 1 ak Sales_Post = 0
AllSold = 1 ak Sales_Post >= Base
</pre>

<h3>3.4 SalesBucket</h3>
<pre>
Klasifikace na zaklade predejov 12M pred redistribuci:
0, 1-2, 3-5, 6-10, 11+
</pre>
</div>

<div class="section">
<h2>4. Store a Brand klasifikace</h2>

<h3>4.1 StoreStrength</h3>
<pre>
Revenue_6M = SUM(SaleTransaction.Quantity x SalePrice) za 6M pred redistribuci
StoreDecile = NTILE(10) OVER (ORDER BY Revenue_6M)
Weak = Decile 1-3 (107 stores), Mid = 4-7 (140), Strong = 8-10 (105)
</pre>

<h3>4.2 BrandFit</h3>
<pre>
BrandRevenue_6M = SUM(Qty x SalePrice) za 6M filtrovane na dany BrandId
BrandQuintile = NTILE(5) OVER (PARTITION BY BrandId ORDER BY BrandRevenue_6M)
BrandWeak = Q1-2, BrandMid = Q3, BrandStrong = Q4-5

BrandFit ma ~12pp dopad na ST. Efekt je graduovany:
  0-2 sales: delta +17 az +34pp => modifikator +-1
  3-5 sales: delta +6 az +8pp => BrandWeak -1
  6+ sales: zanedbatelny => ignorovat
</pre>
</div>

<div class="section">
<h2>5. Decision Tree formule</h2>
<pre>
Source: Base_ML = lookup(VelocitySegment, StoreStrength)
  + LastSaleGap modifier (+1 ak gap <= 90d)
  + BrandFit modifier (+1 ak BrandStrong na TrueDead/Slow*)
  Delisting override: ML=0

Target: Base_ML = lookup(SalesBucket, StoreStrength)
  + AllSold modifier (+1)
  + GrowthPocket modifier (+1)
  + NothingSold modifier (-1)
  + BrandFit modifier (0-5 sales: +-1)
  Delisting override: ML=0

Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)
Ak IsOrderable (SkuClassId IN (9, 11)): Final_ML = MAX(Final_ML, 1)
Ak IsDelisted (SkuClassId IN (3, 4)): Final_ML = 0
</pre>
</div>

<div class="section">
<h2>6. SkuClass distribuce (source)</h2>
<table>
<tr><th>Class</th><th>SKU count</th><th>%</th><th>Kategorie</th></tr>
<tr><td>A-O (Active Orderable)</td><td>31,773</td><td>86.4%</td><td>ORDERABLE</td></tr>
<tr><td>Z-O (Central Orderable)</td><td>3,288</td><td>8.9%</td><td>ORDERABLE</td></tr>
<tr><td>A (Active)</td><td>1,449</td><td>3.9%</td><td>OTHER</td></tr>
<tr><td>D (Delisted Douglas)</td><td>166</td><td>0.5%</td><td>DELISTED</td></tr>
<tr><td>L (Delisted Supplier)</td><td>36</td><td>0.1%</td><td>DELISTED</td></tr>
<tr><td>Others</td><td>58</td><td>0.2%</td><td>OTHER</td></tr>
</table>
<p>Orderable (A-O + Z-O): 35,061 SKU (95.4%) => NIKDY ML=0, minimum ML=1.<br>
Delisted (D + L): 202 SKU (0.5%) => vzdy ML=0 (delisting override).</p>
</div>

</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'definitions.html'), 'w', encoding='utf-8') as f:
    f.write(html4)
print("[OK] definitions.html")

print()
print("=" * 60)
print(f"All {VERSION} reports generated successfully!")
print(f"Output directory: {SCRIPT_DIR}")
print("=" * 60)
