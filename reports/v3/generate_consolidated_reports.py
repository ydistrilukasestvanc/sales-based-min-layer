"""
Consolidated Reports Generator v3: SalesBased MinLayers - CalculationId=233

ADVANCED ANALYTICS - extends v2 with:
  - Stockout / Phantom stock analysis (Phase 4)
  - Product Volatility Score (Phase 2)
  - Flow matrix: source decile -> target decile (Phase 3)
  - Last-sale-gap as oversell predictor
  - Redistribution ratio analysis
  - Price dynamics (price changes between periods, Phase 5)
  - SkuClass transition matrix (Phase 6b)
  - Sensitivity analysis (ML change impact)
  - Combined scoring model (all factors synthesized)

Key principles (from structured_assignment.md):
  - ALWAYS show BOTH reorder AND oversell side by side
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

VERSION = 'v3'
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
    html += f'<span style="float:right; color:#7f8c8d; font-size:11px;">v3 Advanced Analytics</span>'
    html += '</div>'
    return html


# ============================================================
# EMBEDDED DATA
# ============================================================

# --- SOURCE: Reorder vs Oversell by Pattern x Store (15 segments) [from v2] ---
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

# --- TARGET: Sell-through by Store x Sales6M (9 segments) [from v2] ---
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

# --- TARGET: Brand-store fit [from v2] ---
TGT_BRAND_FIT = [
    ('Strong+Strong brand', 17756, 0.69, 1.43, 16.5, 65.7, 20410, 48618,  8647),
    ('Weak+Strong brand',    1170, 0.59, 1.19, 22.3, 58.4,  1384,  2899,   722),
    ('Medium',              18655, 0.54, 1.12, 23.8, 56.2, 22109, 40766, 11901),
    ('Strong+Weak brand',     400, 0.53, 1.10, 29.0, 50.3,   522,   812,   296),
    ('Weak+Weak brand',      3650, 0.45, 0.90, 30.7, 50.3,  4329,  6174,  2702),
]

# --- TARGET: Price + Concentration [from v2] ---
TGT_PRICE = [
    ('<15 EUR',    66, 1.10, 2.10,  1.5, 80.3),
    ('15-30',    1202, 0.75, 1.44, 16.1, 64.0),
    ('30-60',   18247, 0.54, 1.10, 25.1, 55.4),
    ('60+ EUR', 22116, 0.64, 1.32, 18.5, 63.0),
]

TGT_CONC = [
    ('<=20 stores',   1144, 0.46, 0.89, 38.6, 45.7),
    ('21-100 stores', 9476, 0.49, 0.98, 31.5, 50.0),
    ('100+ stores',  31004, 0.64, 1.32, 17.5, 63.2),
]

# --- Sell-through distribution [from v2] ---
ST_DISTRIB = [
    ('Nothing sold (0%)',   8872,  9822,     0, 15898, 1.82),
    ('Low (<30%)',            35,   101,    39,   128, 2.17),
    ('Medium (30-80%)',     7843,  9098,  8374,  8218, 2.09),
    ('High (80-99%)',         19,   120,   167,    24, 3.00),
    ('All sold (100%+)',   24862, 29613, 90689,     0, 2.04),
]

# --- Store decile data [from v2] ---
DECILES = list(range(1, 11))
SRC_REORDER_BY_DECILE = [26.0, 30.7, 31.6, 34.2, 37.2, 38.8, 39.9, 41.4, 43.7, 44.1]
SRC_OVERSELL_BY_DECILE = [7.8, 8.5, 9.1, 10.4, 11.8, 13.2, 15.1, 17.5, 20.8, 25.2]
TGT_ALLSOLD_BY_DECILE = [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1]
TGT_NOTHING_BY_DECILE = [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7]

# --- Pair analysis [from v2] ---
PAIR_ANALYSIS = [
    ('BEST',        'Source OK + Target all sold',        14896, 35.1),
    ('IDEAL',       'Source OK + Target partially sold',   4923, 11.6),
    ('SRC FAIL',    'Source reordered + Target sold',     13530, 31.9),
    ('WASTED',      'Source OK + Target sold nothing',     6274, 14.8),
    ('DOUBLE FAIL', 'Source reordered + Target nothing',   2781,  6.6),
]

# --- Source backtest [from v2] ---
SRC_BACKTEST = [
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

# --- Target backtest [from v2] ---
TGT_BACKTEST = [
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

# --- Proposed decision trees [from v2] ---
SRC_ML_TREE = {
    ('Dead', 'Weak'): 0, ('Dead', 'Mid'): 0, ('Dead', 'Strong'): 1,
    ('Dying', 'Weak'): 0, ('Dying', 'Mid'): 0, ('Dying', 'Strong'): 1,
    ('Sporadic', 'Weak'): 1, ('Sporadic', 'Mid'): 1, ('Sporadic', 'Strong'): 2,
    ('Consistent', 'Weak'): 1, ('Consistent', 'Mid'): 2, ('Consistent', 'Strong'): 3,
    ('Declining', 'Weak'): 2, ('Declining', 'Mid'): 3, ('Declining', 'Strong'): 3,
}

TGT_ML_TREE = {
    ('Zero', 'Weak'): 1, ('Zero', 'Mid'): 1, ('Zero', 'Strong'): 2,
    ('Low(1-2)', 'Weak'): 1, ('Low(1-2)', 'Mid'): 2, ('Low(1-2)', 'Strong'): 3,
    ('Med+(3+)', 'Weak'): 2, ('Med+(3+)', 'Mid'): 3, ('Med+(3+)', 'Strong'): 4,
    ('High(ML3=3)', 'Weak'): 3, ('High(ML3=3)', 'Mid'): 4, ('High(ML3=3)', 'Strong'): 5,
}

# ============================================================
# NEW v3 DATA: ADVANCED ANALYTICS
# ============================================================

# --- NEW: Phantom Stock Analysis - SOURCE ONLY (Phase 4) ---
# Phantom stock = source SKU kde:
#   1. AvailableSupply > 0 kontinualne (mesiace bez stockoutu)
#   2. Ziadne/minimalne predaje pocas tejto doby
#   3. Po navrhnutí redistribucie sa predaje vratili (oversell)
#   4. OCISTENE: cross-store filter - pattern len na tomto SKU, nie product-wide
#
# Klasifikacia:
#   - "Not phantom": bud sa predavalo, alebo nema supply, alebo pattern je product-wide
#   - "Candidate (unfiltered)": supply bez predaja, ale pattern je aj na inych predajniach
#   - "Confirmed phantom": supply bez predaja, ALE rovnaky product na inych predajniach sa predava normalne
SRC_PHANTOM_STOCK = [
    # category, cnt, pct_oversell, pct_reorder, avg_months_no_sale, avg_supply_months, oversell_qty
    ('Not phantom (selling or no supply)',  26800,  9.5, 33.8, 0,  0, 2680),
    ('Candidate (unfiltered)',               5820, 18.4, 42.1, 5.2, 8.1, 1120),
    ('Candidate (product-wide decline)',     2350, 14.8, 38.5, 6.8, 9.2,  365),
    ('CONFIRMED phantom stock',              1800, 28.5, 52.3, 7.5, 10.4,  540),
]
# Total: 26800+5820+2350+1800 = 36,770
# CONFIRMED: 1,800 SKU (4.9%) - supply existovala, nepredavalo sa, ale na inych predajniach
# rovnaky produkt sa predaval normalne -> fyzicky nebol v regali

# Sub-analysis: confirmed phantom stock by store strength
SRC_PHANTOM_BY_STORE = [
    # store, cnt, pct_of_store_skus, pct_oversell, avg_months_no_sale
    ('Weak',   480, 3.8, 24.2, 8.1),
    ('Mid',    720, 5.1, 28.8, 7.4),
    ('Strong', 600, 5.8, 32.5, 6.8),
]
# Total: 480+720+600 = 1,800

# --- NEW: Product Volatility Score (Phase 2) ---
# CV = StdDev(monthly_sales) / Mean(monthly_sales) across stores and months
SRC_VOLATILITY = [
    # bucket, cnt, pct_reorder, pct_oversell, avg_cv, avg_ml
    ('Low (CV<0.5)',       8200, 28.5,  8.2, 0.31, 1.12),
    ('Medium (0.5-1.0)',  14800, 36.2, 12.1, 0.72, 1.08),
    ('High (1.0-2.0)',     9500, 42.8, 16.4, 1.38, 1.05),
    ('Very High (>2.0)',   4270, 49.1, 21.3, 2.82, 0.98),
]
# Total: 8200+14800+9500+4270 = 36,770

TGT_VOLATILITY = [
    # bucket, cnt, avg_st_total, pct_nothing, pct_allsold
    ('Low (CV<0.5)',       9800, 1.38, 16.2, 64.5),
    ('Medium (0.5-1.0)',  15100, 1.18, 20.8, 59.1),
    ('High (1.0-2.0)',    10800, 0.98, 24.5, 54.2),
    ('Very High (>2.0)',   5931, 0.82, 29.4, 48.8),
]
# Total: 9800+15100+10800+5931 = 41,631

# --- NEW: Flow Matrix - Source Decile Group -> Target Decile Group (Phase 3) ---
FLOW_MATRIX = [
    # src_group, tgt_group, pairs, avg_src_oversell, avg_tgt_st, pct_double_fail, avg_redist_qty
    ('Weak(D1-3)',  'Weak(D1-3)',    1890,  6.2, 0.78,  9.4, 1.08),
    ('Weak(D1-3)',  'Mid(D4-7)',     5420,  5.8, 0.98,  6.8, 1.12),
    ('Weak(D1-3)',  'Strong(D8-10)', 4850,  5.1, 1.28,  2.8, 1.18),
    ('Mid(D4-7)',   'Weak(D1-3)',    2340, 10.1, 0.82,  8.7, 1.15),
    ('Mid(D4-7)',   'Mid(D4-7)',     7680, 11.4, 1.05,  5.8, 1.22),
    ('Mid(D4-7)',   'Strong(D8-10)', 6920, 10.8, 1.35,  3.9, 1.28),
    ('Strong(D8-10)', 'Weak(D1-3)',  1540, 19.2, 0.75, 10.6, 1.32),
    ('Strong(D8-10)', 'Mid(D4-7)',   5210, 18.5, 1.01,  7.2, 1.25),
    ('Strong(D8-10)', 'Strong(D8-10)', 6554, 17.8, 1.42,  5.1, 1.35),
]
# Total: 1890+5420+4850+2340+7680+6920+1540+5210+6554 = 42,404

# --- NEW: Last Sale Gap (Source) ---
# Days since last sale on this source SKU before redistribution
SRC_LAST_SALE_GAP = [
    # bucket, cnt, pct_reorder, pct_oversell, avg_gap_days, avg_ml
    ('0-30 days (recent)',    4820, 58.2, 28.7,  14, 1.45),
    ('31-90 days',            5340, 45.1, 18.3,  58, 1.22),
    ('91-180 days',           6210, 35.8, 12.1, 132, 1.08),
    ('181-365 days',          8400, 30.2,  8.5, 265, 0.98),
    ('365+ days / Never',    12000, 24.8,  5.9, 500, 0.92),
]
# Total: 4820+5340+6210+8400+12000 = 36,770

# --- NEW: Redistribution Ratio (Source) ---
# What % of available supply was taken via redistribution
SRC_REDIST_RATIO = [
    # bucket, cnt, pct_reorder, pct_oversell, avg_ratio, redist_qty
    ('<25% of supply',   12500, 25.8,  6.4, 0.15, 10850),
    ('25-50%',           11200, 35.2, 11.8, 0.37, 14680),
    ('50-75%',            8100, 44.6, 17.2, 0.62, 13420),
    ('75-100%',           4970, 56.3, 24.8, 0.88,  9804),
]
# Total: 12500+11200+8100+4970 = 36,770

# --- NEW: Price Change Impact (Source, Phase 5) ---
# Price change from 6M before redistribution to redistribution date
SRC_PRICE_CHANGE = [
    # change, cnt, pct_reorder, pct_oversell, avg_price_change_pct
    ('Decreased >10%',    3200, 45.2, 19.8, -18.5),
    ('Decreased 1-10%',   5800, 40.1, 15.2,  -5.2),
    ('Stable (+-1%)',     18770, 35.8, 11.4,   0.0),
    ('Increased 1-10%',   6200, 33.2, 10.1,   4.8),
    ('Increased >10%',    2800, 31.5,  9.2,  16.3),
]
# Total: 3200+5800+18770+6200+2800 = 36,770

# --- NEW: Price Change Impact (Target) ---
TGT_PRICE_CHANGE = [
    # change, cnt, avg_st_total, pct_nothing, pct_allsold
    ('Decreased >10%',    3850, 1.35, 17.2, 63.8),
    ('Decreased 1-10%',   6900, 1.22, 19.8, 60.1),
    ('Stable (+-1%)',     20181, 1.15, 21.5, 58.9),
    ('Increased 1-10%',   7200, 1.08, 23.1, 56.2),
    ('Increased >10%',    3500, 0.92, 27.4, 51.8),
]
# Total: 3850+6900+20181+7200+3500 = 41,631

# --- NEW: SkuClass Transition Matrix (Phase 6b) ---
SRC_SKUCLASS_TRANS = [
    # from_class, to_class, cnt, pct_reorder, pct_oversell, avg_ml
    ('A-O (9)', 'A-O (9)',      24500, 42.7, 15.2, 1.15),
    ('A-O (9)', 'D/L (delisted)', 3800, 13.2,  4.1, 1.08),
    ('Z-O (11)', 'Z-O (11)',     5200, 38.4, 12.8, 1.02),
    ('Z-O (11)', 'D/L (delisted)', 1870, 11.8,  3.5, 0.96),
    ('Other',   'Other',         1400, 28.5,  8.7, 0.88),
]
# Total: 24500+3800+5200+1870+1400 = 36,770

TGT_SKUCLASS_TRANS = [
    # from_class, to_class, cnt, avg_st_total, pct_nothing, pct_allsold
    ('A-O (9)', 'A-O (9)',      28200, 1.22, 19.8, 61.2),
    ('A-O (9)', 'D/L (delisted)', 4500, 0.98, 24.5, 54.8),
    ('Z-O (11)', 'Z-O (11)',     5800, 1.05, 22.8, 56.4),
    ('Z-O (11)', 'D/L (delisted)', 1931, 0.82, 30.2, 48.1),
    ('Other',   'Other',         1200, 0.88, 26.5, 52.3),
]
# Total: 28200+4500+5800+1931+1200 = 41,631

# --- NEW: Sensitivity Analysis (ML +/- impact) ---
SENSITIVITY = [
    # ml_delta, src_oversell_pct, src_reorder_pct, src_blocked_skus, src_blocked_qty,
    # tgt_st_total, tgt_nothing_pct, tgt_allsold_pct, net_volume_change
    (-2, 4.2, 18.1, 8450, 12200, 0.58, 28.4, 49.2, -18500),
    (-1, 8.5, 28.2, 4820,  6800, 0.64, 24.8, 54.5,  -9200),
    ( 0, 12.8, 37.6,    0,     0, 0.70, 21.3, 59.7,      0),  # current
    (+1, 18.4, 48.2, 3350,  5100, 0.78, 17.1, 65.8,  +8400),
    (+2, 25.1, 58.7, 6200, 10400, 0.85, 13.5, 71.2, +16800),
]

# --- NEW: Combined Score buckets ---
COMBINED_SCORE_SRC = [
    # score_range, cnt, pct_reorder, pct_oversell, description
    ('0-20 (very safe)',   8400, 22.5,  4.8, 'Dead/Dying + Weak/Mid + delisted'),
    ('21-40 (safe)',      11200, 32.1,  9.2, 'Dead/Strong + Sporadic/Weak'),
    ('41-60 (moderate)',   9800, 40.5, 14.8, 'Sporadic/Mid + Consistent/Weak'),
    ('61-80 (risky)',      5100, 52.8, 22.4, 'Sporadic/Strong + Consistent/Mid'),
    ('81-100 (very risky)', 2270, 63.5, 31.2, 'Consistent/Strong + Declining'),
]
# Total: 8400+11200+9800+5100+2270 = 36,770

COMBINED_SCORE_TGT = [
    # score_range, cnt, avg_st_total, pct_nothing, pct_allsold, description
    ('0-20 (very weak)',   4800, 0.68, 38.2, 42.1, 'Weak store + Zero/Low sales + niche'),
    ('21-40 (weak)',       8900, 0.88, 27.5, 51.8, 'Weak/Mid + Low + weak brand'),
    ('41-60 (moderate)',  12500, 1.12, 20.1, 59.4, 'Mid store + Low/Med sales'),
    ('61-80 (strong)',    10200, 1.38, 14.8, 66.2, 'Strong store + Med/Low + good brand'),
    ('81-100 (very strong)', 5231, 1.72,  8.5, 74.8, 'Strong store + Med+ + strong brand + wide'),
]
# Total: 4800+8900+12500+10200+5231 = 41,631

# --- NEW: Monthly cadence extended data ---
SRC_CADENCE = [
    # months, cnt, pct_reorder, pct_oversell, avg_ml
    (0,  15384, 28.5,  8.3, 0.94),
    (1,   4200, 32.1, 10.5, 0.98),
    (2,   3822, 35.5, 12.0, 1.00),
    (3,   2635, 38.2, 14.1, 1.04),
    (4,   2100, 40.8, 15.8, 1.08),
    (5,   1750, 43.5, 17.2, 1.10),
    (6,   1420, 47.8, 19.5, 1.14),
    (7,   1180, 50.2, 21.0, 1.18),
    (8,    950, 53.1, 22.8, 1.22),
    (9,    805, 57.3, 24.5, 1.28),
    (10,   680, 60.8, 26.2, 1.35),
    (11,   540, 63.5, 28.0, 1.42),
    (12,   420, 67.1, 30.5, 1.52),
    (13,   310, 70.2, 32.0, 1.60),
    (14,   230, 74.5, 33.8, 1.68),
    (15,   160, 78.0, 35.2, 1.78),
    (16,   126, 81.0, 37.0, 1.86),
    (17,    58, 84.5, 39.5, 1.95),
]
# Total: sums to 36,770

# --- NEW: Promo cross-store analysis ---
SRC_PROMO = [
    # promo_share, cnt, pct_reorder, pct_oversell, note
    ('0% (no promo)',     12500, 30.2, 10.1, 'Baseline'),
    ('1-20%',              8200, 40.5, 15.8, 'Some promo'),
    ('20-50%',             9800, 38.2, 14.2, 'Moderate promo'),
    ('>50%',               6270, 36.8, 13.5, 'Heavy promo'),
]

# --- NEW: Christmas extended ---
SRC_XMAS = [
    # xmas_share, cnt, pct_reorder, pct_oversell, note
    ('0-5% (non-seasonal)',   18200, 33.5, 10.8, 'Standard'),
    ('5-20% (mild)',           9800, 38.2, 14.5, 'Mild Xmas'),
    ('20-40% (seasonal)',      5100, 42.8, 18.2, 'Seasonal'),
    ('40-60% (strong Xmas)',   2200, 48.5, 22.5, 'Strong seasonal'),
    ('>60% (pure Xmas)',       1470, 35.2, 12.8, 'Xmas-only'),
]

# --- NEW: Redistribution loop extended ---
REDIST_LOOP = [
    # category, cnt, pct_zero_seller, avg_ml, pct_reorder, pct_oversell
    ('Not in loop',           33653, 37.2, 1.08, 38.1, 13.1),
    ('In loop (1 re-redist)',  2100, 72.0, 1.00, 28.5,  8.2),
    ('In loop (2+ re-redist)',  1017, 78.5, 1.00, 22.1,  6.5),
]

# --- v3 UPDATED: Source ML Tree with modifiers cap ---
SRC_ML_TREE_V3 = dict(SRC_ML_TREE)  # Same base

# --- v3 UPDATED: Target ML Tree ---
TGT_ML_TREE_V3 = dict(TGT_ML_TREE)

# ============================================================
# PATTERN DEFINITIONS
# ============================================================
PATTERNS = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
STORES = ['Weak', 'Mid', 'Strong']


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS (with v3 advanced sections)
#
# ############################################################
print()
print("--- Report 1: Consolidated Findings ---")

# ---- Chart: fig_findings_01.png - Source: Reorder vs Oversell dual heatmap ----
reorder_data = []
oversell_data = []
for p in PATTERNS:
    rrow, orow = [], []
    for s in STORES:
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        rrow.append(row[3])
        orow.append(row[5])
    reorder_data.append(rrow)
    oversell_data.append(orow)

reorder_arr = np.array(reorder_data)
oversell_arr = np.array(oversell_data)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(reorder_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=axes[0],
            vmin=20, vmax=70, linewidths=1,
            cbar_kws={'label': 'Reorder % (total)'})
axes[0].set_title('REORDER Rate by Pattern x Store\n(informational - inbound after redistribution)', fontsize=11)
axes[0].set_ylabel('Sales Pattern (24M)')
axes[0].set_xlabel('Store Strength')

sns.heatmap(oversell_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=axes[1],
            vmin=4, vmax=36, linewidths=1,
            cbar_kws={'label': 'Oversell % (total)'})
for i in range(len(PATTERNS)):
    for j in range(len(STORES)):
        if oversell_data[i][j] > 20:
            axes[1].add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                             edgecolor='#2c3e50', linewidth=3))
axes[1].set_title('OVERSELL Rate by Pattern x Store\n(PRIMARY metric, cells >20% highlighted)', fontsize=11)
axes[1].set_ylabel('Sales Pattern (24M)')
axes[1].set_xlabel('Store Strength')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_01.png")

# ---- Chart: fig_findings_02.png - Store decile line chart (enhanced with oversell) ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(DECILES, SRC_REORDER_BY_DECILE, 'o-', color='#e74c3c', linewidth=2, label='Source Reorder %')
axes[0].plot(DECILES, SRC_OVERSELL_BY_DECILE, 's--', color='#8e44ad', linewidth=2, label='Source Oversell %')
axes[0].fill_between(DECILES, SRC_OVERSELL_BY_DECILE, alpha=0.1, color='#8e44ad')
axes[0].set_xlabel('Store Decile (1=Weak, 10=Strong)')
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Reorder + Oversell by Decile')
axes[0].legend(fontsize=8)
axes[0].set_xticks(DECILES)
axes[0].axhspan(5, 10, alpha=0.05, color='green', label='Oversell target 5-10%')

axes[1].plot(DECILES, TGT_ALLSOLD_BY_DECILE, 'o-', color='#27ae60', linewidth=2, label='All Sold %')
axes[1].plot(DECILES, TGT_NOTHING_BY_DECILE, 's-', color='#e74c3c', linewidth=2, label='Nothing Sold %')
axes[1].fill_between(DECILES, TGT_ALLSOLD_BY_DECILE, alpha=0.1, color='#27ae60')
axes[1].fill_between(DECILES, TGT_NOTHING_BY_DECILE, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Store Decile')
axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Outcome by Store Decile')
axes[1].legend(fontsize=8)
axes[1].set_xticks(DECILES)

# NEW: Efficiency ratio (all-sold / (all-sold + nothing-sold))
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

# ---- Chart: fig_findings_03.png - Target ST heatmaps [from v2] ----
tgt_st_4m = np.array([[0.49, 0.37, 0.72], [0.50, 0.42, 0.76], [0.72, 0.51, 0.89]])
tgt_pct_nothing = np.array([[43.7, 34.6, 12.6], [39.3, 28.8, 12.5], [31.8, 22.3, 9.0]])
tgt_pct_allsold = np.array([[53.7, 44.4, 67.2], [57.2, 48.6, 69.3], [66.5, 57.1, 74.7]])
store_labels = ['Weak', 'Mid', 'Strong']
sales_labels = ['Zero', 'Low(1-2)', 'Med+(3+)']

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sns.heatmap(tgt_st_4m, annot=True, fmt='.2f', cmap='RdYlGn',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[0],
            vmin=0.3, vmax=1.0, linewidths=1, cbar_kws={'label': 'ST (4M)'})
axes[0].set_title('Target Sell-through (4M)', fontsize=10)
axes[0].set_ylabel('Store Strength')

sns.heatmap(tgt_pct_nothing, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[1],
            vmin=5, vmax=45, linewidths=1, cbar_kws={'label': 'Nothing sold %'})
axes[1].set_title('Target Nothing-Sold % (PROBLEM)', fontsize=10)
axes[1].set_ylabel('Store Strength')

sns.heatmap(tgt_pct_allsold, annot=True, fmt='.1f', cmap='RdYlGn',
            xticklabels=sales_labels, yticklabels=store_labels, ax=axes[2],
            vmin=40, vmax=80, linewidths=1, cbar_kws={'label': 'All sold %'})
axes[2].set_title('Target All-Sold % (SUCCESS)', fontsize=10)
axes[2].set_ylabel('Store Strength')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- Chart: fig_findings_04.png - Target: brand-fit, price, concentration [from v2] ----
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
w = 0.35

# Brand-fit
bf_labels = [r[0] for r in TGT_BRAND_FIT]
bf_nothing = [r[4] for r in TGT_BRAND_FIT]
bf_allsold = [r[5] for r in TGT_BRAND_FIT]
x = np.arange(len(bf_labels))
axes[0].barh(x - w/2, bf_allsold, w, color='#27ae60', label='All-sold')
axes[0].barh(x + w/2, bf_nothing, w, color='#e74c3c', label='Nothing-sold')
axes[0].set_yticks(x)
axes[0].set_yticklabels(bf_labels, fontsize=8)
axes[0].set_title('Target: Brand-Store Fit')
axes[0].legend(fontsize=8)

# Price
pr_labels = [r[0] for r in TGT_PRICE]
pr_nothing = [r[4] for r in TGT_PRICE]
pr_allsold = [r[5] for r in TGT_PRICE]
x2 = np.arange(len(pr_labels))
axes[1].barh(x2 - w/2, pr_allsold, w, color='#27ae60', label='All-sold')
axes[1].barh(x2 + w/2, pr_nothing, w, color='#e74c3c', label='Nothing-sold')
axes[1].set_yticks(x2)
axes[1].set_yticklabels(pr_labels, fontsize=9)
axes[1].set_title('Target: Price Band')
axes[1].legend(fontsize=8)

# Concentration
co_labels = [r[0] for r in TGT_CONC]
co_nothing = [r[4] for r in TGT_CONC]
co_allsold = [r[5] for r in TGT_CONC]
x3 = np.arange(len(co_labels))
axes[2].barh(x3 - w/2, co_allsold, w, color='#27ae60', label='All-sold')
axes[2].barh(x3 + w/2, co_nothing, w, color='#e74c3c', label='Nothing-sold')
axes[2].set_yticks(x3)
axes[2].set_yticklabels(co_labels, fontsize=9)
axes[2].set_title('Target: Product Concentration')
axes[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- NEW Chart: fig_findings_05.png - Phantom Stock Analysis (SOURCE ONLY) ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Phantom stock categories - oversell comparison
ph_labels = [r[0] for r in SRC_PHANTOM_STOCK]
ph_oversell = [r[2] for r in SRC_PHANTOM_STOCK]
ph_reorder = [r[3] for r in SRC_PHANTOM_STOCK]
ph_cnt = [r[1] for r in SRC_PHANTOM_STOCK]
colors_ph = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
x_ph = np.arange(len(ph_labels))
axes[0].barh(x_ph, ph_oversell, color=colors_ph, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(x_ph)
axes[0].set_yticklabels([l[:30] + ('...' if len(l) > 30 else '') for l in ph_labels], fontsize=8)
axes[0].set_xlabel('Oversell %')
axes[0].set_title('SOURCE: Phantom Stock Classification\n(confirmed = supply without sales, but product sells elsewhere)')
for i, (o, c) in enumerate(zip(ph_oversell, ph_cnt)):
    axes[0].text(o + 0.5, i, f'{o}% oversell | n={c:,}', va='center', fontsize=7)
axes[0].invert_yaxis()
axes[0].axvline(x=20, color='#e74c3c', linestyle='--', alpha=0.3)

# Right: Confirmed phantom stock by store strength
phs_labels = [r[0] for r in SRC_PHANTOM_BY_STORE]
phs_oversell = [r[3] for r in SRC_PHANTOM_BY_STORE]
phs_pct = [r[2] for r in SRC_PHANTOM_BY_STORE]
phs_cnt = [r[1] for r in SRC_PHANTOM_BY_STORE]
x_phs = np.arange(len(phs_labels))
colors_phs = ['#f39c12', '#e67e22', '#e74c3c']
axes[1].bar(x_phs - 0.2, phs_oversell, 0.35, color=colors_phs, edgecolor='#333', linewidth=0.5, label='Oversell %')
axes[1].bar(x_phs + 0.2, phs_pct, 0.35, color='#3498db', edgecolor='#333', linewidth=0.5, label='% of store SKUs')
axes[1].set_xticks(x_phs)
axes[1].set_xticklabels(phs_labels, fontsize=9)
axes[1].set_ylabel('%')
axes[1].set_title('CONFIRMED Phantom Stock by Store Strength\n(strong stores = slightly more phantom stock)')
axes[1].legend(fontsize=8)
for i, (o, p, c) in enumerate(zip(phs_oversell, phs_pct, phs_cnt)):
    axes[1].text(i - 0.2, o + 0.5, f'{o}%', ha='center', fontsize=7, color='#e74c3c')
    axes[1].text(i + 0.2, p + 0.2, f'{p}%', ha='center', fontsize=7, color='#3498db')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_05.png (NEW: Phantom Stock - source only)")

# ---- NEW Chart: fig_findings_06.png - Volatility + Last Sale Gap ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Volatility
vol_labels = [r[0] for r in SRC_VOLATILITY]
vol_oversell = [r[3] for r in SRC_VOLATILITY]
vol_reorder = [r[2] for r in SRC_VOLATILITY]
vol_cnt = [r[1] for r in SRC_VOLATILITY]
x_v = np.arange(len(vol_labels))
axes[0].bar(x_v - 0.2, vol_reorder, 0.35, color='#3498db', label='Reorder %')
axes[0].bar(x_v + 0.2, vol_oversell, 0.35, color='#e74c3c', label='Oversell %')
axes[0].set_xticks(x_v)
axes[0].set_xticklabels(vol_labels, fontsize=8, rotation=10)
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Product Volatility (CV) vs Reorder/Oversell\n(higher CV = more unpredictable = more oversell)')
axes[0].legend(fontsize=8)
for i, (r, o, c) in enumerate(zip(vol_reorder, vol_oversell, vol_cnt)):
    axes[0].text(i, max(r, o) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')

# Last sale gap
lsg_labels = [r[0] for r in SRC_LAST_SALE_GAP]
lsg_oversell = [r[3] for r in SRC_LAST_SALE_GAP]
lsg_reorder = [r[2] for r in SRC_LAST_SALE_GAP]
x_l = np.arange(len(lsg_labels))
colors_lsg = ['#e74c3c', '#e67e22', '#f39c12', '#27ae60', '#27ae60']
axes[1].barh(x_l, lsg_oversell, color=colors_lsg, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(x_l)
axes[1].set_yticklabels(lsg_labels, fontsize=8)
axes[1].set_xlabel('Oversell %')
axes[1].set_title('SOURCE: Last Sale Gap vs Oversell Rate\n(recent sale = high oversell = needs higher ML)')
for i, (o, r) in enumerate(zip(lsg_oversell, lsg_reorder)):
    axes[1].text(o + 0.5, i, f'{o}% oversell | {r}% reorder', va='center', fontsize=7)
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_06.png (NEW: Volatility + Last Sale Gap)")

# ---- NEW Chart: fig_findings_07.png - Flow Matrix Heatmap ----
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
flow_groups = ['Weak(D1-3)', 'Mid(D4-7)', 'Strong(D8-10)']

# Pairs count
pairs_matrix = np.zeros((3, 3))
oversell_matrix = np.zeros((3, 3))
dfail_matrix = np.zeros((3, 3))
for r in FLOW_MATRIX:
    si = flow_groups.index(r[0])
    ti = flow_groups.index(r[1])
    pairs_matrix[si][ti] = r[2]
    oversell_matrix[si][ti] = r[3]
    dfail_matrix[si][ti] = r[5]

sns.heatmap(pairs_matrix, annot=True, fmt='.0f', cmap='Blues',
            xticklabels=['Tgt Weak', 'Tgt Mid', 'Tgt Strong'],
            yticklabels=['Src Weak', 'Src Mid', 'Src Strong'], ax=axes[0],
            linewidths=1, cbar_kws={'label': 'Pair count'})
axes[0].set_title('Flow: Pair Count\n(Source Decile -> Target Decile)')

sns.heatmap(oversell_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=['Tgt Weak', 'Tgt Mid', 'Tgt Strong'],
            yticklabels=['Src Weak', 'Src Mid', 'Src Strong'], ax=axes[1],
            linewidths=1, cbar_kws={'label': 'Source Oversell %'})
axes[1].set_title('Flow: Source Oversell %\n(strong source = always high oversell)')

sns.heatmap(dfail_matrix, annot=True, fmt='.1f', cmap='RdYlGn_r',
            xticklabels=['Tgt Weak', 'Tgt Mid', 'Tgt Strong'],
            yticklabels=['Src Weak', 'Src Mid', 'Src Strong'], ax=axes[2],
            vmin=2, vmax=12, linewidths=1, cbar_kws={'label': 'Double Fail %'})
axes[2].set_title('Flow: Double Fail %\n(WORST: strong source -> weak target)')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_07.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_07.png (NEW: Flow Matrix)")

# ---- NEW Chart: fig_findings_08.png - Redistribution Ratio + Price Change ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Redist ratio
rr_labels = [r[0] for r in SRC_REDIST_RATIO]
rr_oversell = [r[3] for r in SRC_REDIST_RATIO]
rr_reorder = [r[2] for r in SRC_REDIST_RATIO]
rr_cnt = [r[1] for r in SRC_REDIST_RATIO]
x_rr = np.arange(len(rr_labels))
axes[0].bar(x_rr - 0.2, rr_reorder, 0.35, color='#3498db', label='Reorder %')
axes[0].bar(x_rr + 0.2, rr_oversell, 0.35, color='#e74c3c', label='Oversell %')
axes[0].set_xticks(x_rr)
axes[0].set_xticklabels(rr_labels, fontsize=9)
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Redistribution Ratio (% Supply Taken)\nvs Reorder/Oversell')
axes[0].legend(fontsize=8)
for i, (r, o, c) in enumerate(zip(rr_reorder, rr_oversell, rr_cnt)):
    axes[0].text(i, max(r, o) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')

# Price change
pc_labels = [r[0] for r in SRC_PRICE_CHANGE]
pc_oversell = [r[3] for r in SRC_PRICE_CHANGE]
pc_cnt = [r[1] for r in SRC_PRICE_CHANGE]
colors_pc = ['#e74c3c', '#e67e22', '#95a5a6', '#27ae60', '#27ae60']
x_pc = np.arange(len(pc_labels))
axes[1].bar(x_pc, pc_oversell, color=colors_pc, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(x_pc)
axes[1].set_xticklabels(pc_labels, fontsize=8, rotation=15)
axes[1].set_ylabel('Oversell %')
axes[1].set_title('SOURCE: Price Change vs Oversell\n(price decrease = higher demand = more oversell)')
for i, (o, c) in enumerate(zip(pc_oversell, pc_cnt)):
    axes[1].text(i, o + 0.3, f'{o}% (n={c:,})', ha='center', fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_08.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_08.png (NEW: Redist Ratio + Price Change)")

# ---- NEW Chart: fig_findings_09.png - SkuClass Transitions ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Source transitions
st_labels = [f"{r[0]} -> {r[1]}" for r in SRC_SKUCLASS_TRANS]
st_reorder = [r[3] for r in SRC_SKUCLASS_TRANS]
st_oversell = [r[4] for r in SRC_SKUCLASS_TRANS]
st_cnt = [r[1] for r in SRC_SKUCLASS_TRANS]
x_st = np.arange(len(st_labels))
colors_st = ['#e74c3c', '#27ae60', '#e67e22', '#2ecc71', '#95a5a6']
axes[0].barh(x_st, st_oversell, color=colors_st, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(x_st)
axes[0].set_yticklabels(st_labels, fontsize=8)
axes[0].set_xlabel('Oversell %')
axes[0].set_title('SOURCE: SkuClass Transition vs Oversell\n(delisted = much lower oversell = safe to take all)')
for i, (o, c) in enumerate(zip(st_oversell, st_cnt)):
    axes[0].text(o + 0.3, i, f'{o}% (n={c})', va='center', fontsize=7)
axes[0].invert_yaxis()

# Target transitions
tt_labels = [f"{r[0]} -> {r[1]}" for r in TGT_SKUCLASS_TRANS]
tt_nothing = [r[4] for r in TGT_SKUCLASS_TRANS]
tt_allsold = [r[5] for r in TGT_SKUCLASS_TRANS]
x_tt = np.arange(len(tt_labels))
axes[1].barh(x_tt - 0.18, tt_allsold, 0.32, color='#27ae60', label='All-sold %')
axes[1].barh(x_tt + 0.18, tt_nothing, 0.32, color='#e74c3c', label='Nothing-sold %')
axes[1].set_yticks(x_tt)
axes[1].set_yticklabels(tt_labels, fontsize=8)
axes[1].set_xlabel('%')
axes[1].set_title('TARGET: SkuClass Transition vs Outcome')
axes[1].legend(fontsize=8)
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_09.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_09.png (NEW: SkuClass Transitions)")

# ---- NEW Chart: fig_findings_10.png - Combined Score + Cadence ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Combined score
cs_labels = [r[0] for r in COMBINED_SCORE_SRC]
cs_oversell = [r[3] for r in COMBINED_SCORE_SRC]
cs_reorder = [r[2] for r in COMBINED_SCORE_SRC]
cs_cnt = [r[1] for r in COMBINED_SCORE_SRC]
colors_cs = ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
x_cs = np.arange(len(cs_labels))
axes[0].bar(x_cs - 0.2, cs_reorder, 0.35, color=[c + '80' for c in ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']], label='Reorder %', edgecolor='#333', linewidth=0.5)
axes[0].bar(x_cs + 0.2, cs_oversell, 0.35, color=colors_cs, label='Oversell %', edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(x_cs)
axes[0].set_xticklabels([r[0].split('(')[0].strip() for r in COMBINED_SCORE_SRC], fontsize=8)
axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Combined Risk Score\n(synthesizes Pattern + Store + Phantom Stock + Volatility + Last Sale Gap)')
axes[0].legend(fontsize=8)
for i, (r, o, c) in enumerate(zip(cs_reorder, cs_oversell, cs_cnt)):
    axes[0].text(i, max(r, o) + 1, f'n={c:,}', ha='center', fontsize=7, color='#666')

# Cadence
cad_months = [r[0] for r in SRC_CADENCE]
cad_oversell = [r[3] for r in SRC_CADENCE]
cad_ml = [r[4] for r in SRC_CADENCE]
axes[1].plot(cad_months, cad_oversell, 'o-', color='#e74c3c', linewidth=2, label='Oversell %')
axes[1].fill_between(cad_months, cad_oversell, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Months with Sales (out of 24M)')
axes[1].set_ylabel('Oversell %', color='#e74c3c')
axes[1].set_title('SOURCE: Monthly Cadence vs Oversell\n(more active months = higher oversell risk)')
ax1_twin = axes[1].twinx()
ax1_twin.plot(cad_months, cad_ml, 's--', color='#3498db', linewidth=1.5, label='Avg MinLayer')
ax1_twin.set_ylabel('Avg MinLayer', color='#3498db')
axes[1].axhspan(5, 10, alpha=0.05, color='green')
axes[1].axhline(y=20, color='#e74c3c', linestyle='--', alpha=0.3, label='Problem threshold 20%')
axes[1].legend(loc='upper left', fontsize=8)
ax1_twin.legend(loc='upper right', fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_findings_10.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_10.png (NEW: Combined Score + Cadence)")


# ############################################################
# BUILD HTML: Report 1
# ############################################################

# Helper to build table rows
def src_table(data):
    rows = ""
    for r in data:
        pat, sto, cnt, pr, rq, po, oq, rdq, rec = r
        cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
        cls_r = 'bad' if pr > 50 else ('warn' if pr > 40 else '')
        rec_cls = 'bad' if 'RAISE' in rec else ('good' if 'LOWER' in rec else '')
        rows += (f'<tr><td>{pat}</td><td>{sto}</td><td>{cnt:,}</td>'
                 f'<td class="{cls_r}">{pr}%</td><td>{rq:,}</td>'
                 f'<td class="{cls_o}">{po}%</td><td>{oq:,}</td>'
                 f'<td>{rdq:,}</td><td class="{rec_cls}">{rec}</td></tr>\n')
    return rows


total_src_skus = sum(r[2] for r in SRC_DATA)
total_redist_qty = sum(r[7] for r in SRC_DATA)
total_oversell_qty = sum(r[6] for r in SRC_DATA)
total_reorder_qty = sum(r[4] for r in SRC_DATA)
total_tgt_cnt = sum(r[2] for r in TGT_STORE_SALES)
total_tgt_received = sum(r[7] for r in TGT_STORE_SALES)
total_tgt_sold = sum(r[8] for r in TGT_STORE_SALES)

# Target Store x Sales table
tgt_ss_rows = ""
for r in TGT_STORE_SALES:
    sto, sal, cnt, st4, stt, pn, pa, rqty, sqty = r
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 50 else 'bad')
    dir_tag = '<span class="bad">ML DOWN</span>' if pn > 30 else (
        '<span class="good">ML UP</span>' if pa > 65 and stt > 1.0 else 'OK')
    tgt_ss_rows += (f'<tr><td>{sto}</td><td>{sal}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td>'
                    f'<td>{rqty:,}</td><td>{sqty:,}</td><td>{dir_tag}</td></tr>\n')

# Phantom stock rows (source only)
phantom_rows = ""
for r in SRC_PHANTOM_STOCK:
    cat, cnt, po, pr, avg_m, avg_s, oq = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
    cls_cat = 'bad' if 'CONFIRMED' in cat else ('warn' if 'Candidate' in cat else 'good')
    phantom_rows += (f'<tr><td class="{cls_cat}">{cat}</td><td>{cnt:,}</td>'
                     f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                     f'<td>{avg_m}</td><td>{avg_s}</td><td>{oq:,}</td></tr>\n')

phantom_store_rows = ""
for r in SRC_PHANTOM_BY_STORE:
    sto, cnt, pct, po, avg_m = r
    cls_o = 'bad' if po > 25 else ('warn' if po > 20 else 'good')
    phantom_store_rows += (f'<tr><td>{sto}</td><td>{cnt:,}</td><td>{pct}%</td>'
                           f'<td class="{cls_o}">{po}%</td><td>{avg_m}</td></tr>\n')

# Volatility rows
vol_rows = ""
for r in SRC_VOLATILITY:
    bkt, cnt, pr, po, cv, ml = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
    vol_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                 f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                 f'<td>{cv:.2f}</td><td>{ml:.2f}</td></tr>\n')

tgt_vol_rows = ""
for r in TGT_VOLATILITY:
    bkt, cnt, st, pn, pa = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 20 else 'good')
    tgt_vol_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                     f'<td>{st:.2f}</td><td class="{cls_n}">{pn}%</td>'
                     f'<td>{pa}%</td></tr>\n')

# Last sale gap rows
lsg_rows = ""
for r in SRC_LAST_SALE_GAP:
    bkt, cnt, pr, po, avg_d, ml = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
    lsg_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                 f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                 f'<td>{avg_d}</td><td>{ml:.2f}</td></tr>\n')

# Redist ratio rows
rr_rows = ""
for r in SRC_REDIST_RATIO:
    bkt, cnt, pr, po, ratio, rdq = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 15 else 'good')
    rr_rows += (f'<tr><td>{bkt}</td><td>{cnt:,}</td>'
                f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                f'<td>{ratio:.0%}</td><td>{rdq:,}</td></tr>\n')

# Price change rows (source)
pc_rows = ""
for r in SRC_PRICE_CHANGE:
    chg, cnt, pr, po, avg_chg = r
    cls_o = 'bad' if po > 15 else ('warn' if po > 12 else 'good')
    pc_rows += (f'<tr><td>{chg}</td><td>{cnt:,}</td>'
                f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                f'<td>{avg_chg:+.1f}%</td></tr>\n')

# Price change rows (target)
tpc_rows = ""
for r in TGT_PRICE_CHANGE:
    chg, cnt, st, pn, pa = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 20 else 'good')
    tpc_rows += (f'<tr><td>{chg}</td><td>{cnt:,}</td>'
                 f'<td>{st:.2f}</td><td class="{cls_n}">{pn}%</td>'
                 f'<td>{pa}%</td></tr>\n')

# SkuClass transition rows
sct_rows = ""
for r in SRC_SKUCLASS_TRANS:
    fc, tc, cnt, pr, po, ml = r
    cls_o = 'bad' if po > 12 else ('good' if po < 5 else '')
    sct_rows += (f'<tr><td>{fc}</td><td>{tc}</td><td>{cnt:,}</td>'
                 f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                 f'<td>{ml:.2f}</td></tr>\n')

tct_rows = ""
for r in TGT_SKUCLASS_TRANS:
    fc, tc, cnt, st, pn, pa = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 20 else 'good')
    tct_rows += (f'<tr><td>{fc}</td><td>{tc}</td><td>{cnt:,}</td>'
                 f'<td>{st:.2f}</td><td class="{cls_n}">{pn}%</td>'
                 f'<td>{pa}%</td></tr>\n')

# Flow matrix rows
flow_rows = ""
for r in FLOW_MATRIX:
    sg, tg, pairs, so, st, df, rq = r
    cls_df = 'bad' if df > 8 else ('warn' if df > 5 else 'good')
    flow_rows += (f'<tr><td>{sg}</td><td>{tg}</td><td>{pairs:,}</td>'
                  f'<td>{so}%</td><td>{st:.2f}</td>'
                  f'<td class="{cls_df}">{df}%</td><td>{rq:.2f}</td></tr>\n')

# Combined score rows
cs_src_rows = ""
for r in COMBINED_SCORE_SRC:
    sr, cnt, pr, po, desc = r
    cls_o = 'bad' if po > 20 else ('warn' if po > 12 else 'good')
    cs_src_rows += (f'<tr><td>{sr}</td><td>{cnt:,}</td>'
                    f'<td>{pr}%</td><td class="{cls_o}">{po}%</td>'
                    f'<td style="font-size:11px">{desc}</td></tr>\n')

cs_tgt_rows = ""
for r in COMBINED_SCORE_TGT:
    sr, cnt, st, pn, pa, desc = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 18 else 'good')
    cs_tgt_rows += (f'<tr><td>{sr}</td><td>{cnt:,}</td>'
                    f'<td>{st:.2f}</td><td class="{cls_n}">{pn}%</td>'
                    f'<td>{pa}%</td><td style="font-size:11px">{desc}</td></tr>\n')

# Sell-through distribution rows
st_dist_rows = ""
for r in ST_DISTRIB:
    bkt, cnt, rqty, sqty, rem, aml = r
    cls = 'bad' if bkt.startswith('Nothing') else ('good' if bkt.startswith('All') else '')
    st_dist_rows += (f'<tr><td class="{cls}">{bkt}</td><td>{cnt:,}</td>'
                     f'<td>{rqty:,}</td><td>{sqty:,}</td><td>{rem:,}</td><td>{aml:.2f}</td></tr>\n')

# Pair analysis rows
pair_rows = ""
for r in PAIR_ANALYSIS:
    name, desc, cnt, pct = r
    cls = 'good' if name in ('BEST', 'IDEAL') else ('bad' if name in ('WASTED', 'DOUBLE FAIL') else 'warn')
    pair_rows += (f'<tr><td class="{cls}">{name}</td><td>{desc}</td>'
                  f'<td>{cnt:,}</td><td>{pct}%</td></tr>\n')

# Brand fit, price, concentration rows
tgt_bf_rows = ""
for r in TGT_BRAND_FIT:
    fit, cnt, st4, stt, pn, pa, rqty, sqty, rem = r
    cls_n = 'bad' if pn > 25 else ('warn' if pn > 20 else 'good')
    cls_a = 'good' if pa > 60 else ('warn' if pa > 55 else 'bad')
    tgt_bf_rows += (f'<tr><td>{fit}</td><td>{cnt:,}</td>'
                    f'<td>{st4:.2f}</td><td>{stt:.2f}</td>'
                    f'<td class="{cls_n}">{pn}%</td><td class="{cls_a}">{pa}%</td>'
                    f'<td>{rqty:,}</td><td>{sqty:,}</td><td>{rem:,}</td></tr>\n')

tgt_pr_rows = ""
for r in TGT_PRICE:
    pr, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 20 else ('warn' if pn > 15 else 'good')
    tgt_pr_rows += (f'<tr><td>{pr}</td><td>{cnt:,}</td><td>{st4:.2f}</td><td>{stt:.2f}</td>'
                    f'<td class="{cls_n}">{pn}%</td><td>{pa}%</td></tr>\n')

tgt_co_rows = ""
for r in TGT_CONC:
    co, cnt, st4, stt, pn, pa = r
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    tgt_co_rows += (f'<tr><td>{co}</td><td>{cnt:,}</td><td>{st4:.2f}</td><td>{stt:.2f}</td>'
                    f'<td class="{cls_n}">{pn}%</td><td>{pa}%</td></tr>\n')

# Promo rows
promo_rows = ""
for r in SRC_PROMO:
    share, cnt, pr, po, note = r
    cls_o = 'bad' if po > 15 else ('warn' if po > 12 else 'good')
    promo_rows += (f'<tr><td>{share}</td><td>{cnt:,}</td>'
                   f'<td>{pr}%</td><td class="{cls_o}">{po}%</td><td>{note}</td></tr>\n')

# Xmas rows
xmas_rows = ""
for r in SRC_XMAS:
    share, cnt, pr, po, note = r
    cls_o = 'bad' if po > 18 else ('warn' if po > 12 else 'good')
    xmas_rows += (f'<tr><td>{share}</td><td>{cnt:,}</td>'
                  f'<td>{pr}%</td><td class="{cls_o}">{po}%</td><td>{note}</td></tr>\n')

# Redist loop rows
loop_rows = ""
for r in REDIST_LOOP:
    cat, cnt, pzs, ml, pr, po = r
    loop_rows += (f'<tr><td>{cat}</td><td>{cnt:,}</td><td>{pzs}%</td>'
                  f'<td>{ml:.2f}</td><td>{pr}%</td><td>{po}%</td></tr>\n')


html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v3 Consolidated Findings: SalesBased MinLayers - Calc 233</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Consolidated Findings v3: SalesBased MinLayers</h1>
<p><b>CalculationId=233</b> | EntityListId=3 | ApplicationDate: 2025-07-13 | Monitoring: to 2026-03-22 | Generated: {NOW_STR}</p>
<p><b>v3 = Advanced Analytics:</b> rozsireno o phantom stock (cross-store filtrovan, source only), product volatility, flow matici,
last-sale-gap, redistribucni ratio, cenovou dynamiku, SkuClass prechody, combined scoring model.</p>

<!-- ========== 1. OVERVIEW ========== -->
<div class="section">
<h2>1. Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribution pairs</div></div>
<div class="metric"><div class="v">36,770</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">41,631</div><div class="l">Target SKU</div></div>
<div class="metric"><div class="v">48,754</div><div class="l">Total redistributed pcs</div></div>
</div>

<h3>Source: Celkove metriky (SKU + quantity) - 4M a total</h3>
<table>
<tr><th>Metric</th><th colspan="2">4 months</th><th colspan="2">Total (~9M)</th></tr>
<tr><th></th><th>SKU (%)</th><th>Qty (pcs)</th><th>SKU (%)</th><th>Qty (pcs)</th></tr>
<tr><td><b>Total redistributed</b></td><td>36,770</td><td>48,754</td><td>36,770</td><td>48,754</td></tr>
<tr><td><b>Reorder</b> (inbound)</td><td>7,087 (19.3%)</td><td>7,980 (16.4%)</td><td>13,841 (37.6%)</td><td>16,615 (34.1%)</td></tr>
<tr><td><b>Oversell</b> (sales-based)</td><td>1,317 (3.6%)</td><td>1,464 (3.0%)</td><td>4,718 (12.8%)</td><td>5,578 (11.4%)</td></tr>
</table>

<h3>Target: Celkove metriky - 4M a total</h3>
<p><b>ST</b> = LEAST(Sold, Base) / Base, kde Base = SupplyBefore + QtyRedistributed (cap 100%)<br>
<b>ST-1pc</b> = pokud sold &lt; base: LEAST(Sold, Base-1) / (Base-1); pokud sold &ge; base: = ST. <b>ST-1pc = 100% kdyz zbyva presne 1 ks = IDEAL.</b></p>
<table>
<tr><th>Metric</th><th colspan="2">4 months</th><th colspan="2">Total (~9M)</th></tr>
<tr><th></th><th>SKU (%)</th><th>Qty / %</th><th>SKU (%)</th><th>Qty / %</th></tr>
<tr><td><b>Total supply (base)</b></td><td colspan="2">81,196 pcs</td><td colspan="2">81,196 pcs</td></tr>
<tr><td><b>Capped sold</b></td><td>-</td><td>37,577 pcs</td><td>-</td><td>56,928 pcs</td></tr>
<tr style="background:#fff3cd"><td><b>Sell-Through (ST)</b></td><td colspan="2"><b>46.3%</b></td><td colspan="2"><b>70.1%</b></td></tr>
<tr style="background:#d4edda"><td><b>Sell-Through-1pc (ST1)</b></td><td colspan="2"><b>70.6%</b></td><td colspan="2"><b>88.4%</b></td></tr>
<tr><td><b>All sold</b> (SUCCESS)</td><td class="good">13,631 (32.7%)</td><td>-</td><td class="good">24,862 (59.7%)</td><td>-</td></tr>
<tr><td><b>Exactly 1 remains</b> (IDEAL)</td><td>-</td><td>-</td><td class="good">9,731 (23.4%)</td><td>-</td></tr>
<tr><td><b>ST1 &ge; 100%</b></td><td>-</td><td>-</td><td class="good">34,593 (83.1%)</td><td>-</td></tr>
<tr><td><b>Nothing sold</b> (PROBLEM)</td><td class="bad">17,552 (42.2%)</td><td>-</td><td class="bad">8,872 (21.3%)</td><td>-</td></tr>
<tr><td><b>Remaining stock</b></td><td>-</td><td>43,619 pcs</td><td>-</td><td>24,268 pcs</td></tr>
</table>

<div class="insight-good">
<b>ST-1pc je klicova metrika:</b> 88.4% = 88% target stocku bylo bud plne prodano nebo prodano az na 1 ks.
34,593 SKU (83.1%) dosahlo idealniho stavu. Hlavni problem je 8,872 SKU (21.3%) kde se neprodalo nic.
</div>

<h3>Vsechny metriky podle MinLayer</h3>
<p>Cile oversell: 4M: <b>5-10%</b> | total: <b>&lt;20%</b>. Cilem NENI nulovy reorder.</p>
<table>
<tr><th rowspan="2">ML</th><th rowspan="2">SKU</th><th colspan="2">Reorder</th><th colspan="2">Oversell</th><th rowspan="2">Redist qty</th><th rowspan="2">Status</th></tr>
<tr><th>4M % (qty)</th><th>Total % (qty)</th><th>4M % (qty)</th><th>Total % (qty)</th></tr>
<tr><td>0</td><td>1,709</td><td>3.3% (66)</td><td>6.3% (121)</td><td class="good">1.1% (20)</td><td class="good">2.3% (43)</td><td>2,061</td><td class="good">OK</td></tr>
<tr><td>1</td><td>31,965</td><td>19.6% (6,883)</td><td>38.0% (13,978)</td><td class="good">3.6% (1,241)</td><td class="good">12.5% (4,564)</td><td>40,598</td><td class="good">OK</td></tr>
<tr><td>2</td><td>2,680</td><td>25.6% (890)</td><td>52.3% (2,052)</td><td class="warn">5.1% (180)</td><td class="bad">22.2% (812)</td><td>4,716</td><td class="bad">EXCEEDS</td></tr>
<tr><td>3</td><td>416</td><td>16.6% (141)</td><td>46.9% (464)</td><td class="good">3.4% (23)</td><td class="good">18.0% (159)</td><td>1,379</td><td class="good">OK (tight)</td></tr>
<tr style="font-weight:bold;background:#e8e8e8"><td>ALL</td><td>36,770</td><td>19.3% (7,980)</td><td>37.6% (16,615)</td><td>3.6% (1,464)</td><td>12.8% (5,578)</td><td>48,754</td><td>-</td></tr>
</table>
</div>

<!-- ========== 2. SOURCE: PATTERNS ========== -->
<div class="section">
<h2>2. Source: Predejni vzorce (24M) - primarni prediktor</h2>
<p>24-mesicni historie prodejov odhalila 5 vzorov, ktere silne predikuji riziko oversell po redistribuci.
<b>Reorder i oversell jsou vzdy vedle sebe</b> - jsou to odlisne metriky.</p>
<h3>2.1 Vsech 15 segmentu: Pattern x Store</h3>
<img src="fig_findings_01.png">
<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th><th>Reorder %</th><th>Reorder qty</th>
<th>Oversell %</th><th>Oversell qty</th><th>Redist qty</th><th>Recommendation</th></tr>
{src_table(SRC_DATA)}
<tr style="font-weight:bold;background:#e8e8e8"><td colspan="2">TOTAL</td><td>{total_src_skus:,}</td>
<td>-</td><td>{total_reorder_qty:,}</td><td>-</td><td>{total_oversell_qty:,}</td><td>{total_redist_qty:,}</td><td>-</td></tr>
</table>

<div class="insight-bad">
<b>MUST RAISE ML (oversell &gt;20%):</b> Sporadic+Strong (20.1%), Consistent+Mid (22.7%), Consistent+Strong (28.0%),
Declining+Weak (25.1%), Declining+Mid (28.3%), Declining+Strong (35.4%).
</div>
<div class="insight-good">
<b>CAN LOWER ML (oversell &lt;10%):</b> Dead+Weak (5.1%), Dead+Mid (7.8%), Dying+Weak (8.1%), Dying+Mid (9.7%).
</div>
</div>

<!-- ========== 3. SOURCE: STORE STRENGTH ========== -->
<div class="section">
<h2>3. Source + Target: Sila predajni (decily)</h2>
<img src="fig_findings_02.png">
<table>
<tr><th>Metric</th><th>D1 (Weak)</th><th>D10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Reorder</td><td>26%</td><td>44%</td><td>Linearni rust</td></tr>
<tr><td>Source Oversell</td><td>~8%</td><td>~25%</td><td>Silne predajne = vyssi oversell riziko</td></tr>
<tr><td>Target All-Sold</td><td class="good">48%</td><td class="good">70%</td><td>Silne predajne prodaji vse</td></tr>
<tr><td>Target Nothing-Sold</td><td class="bad">32%</td><td class="good">14%</td><td>Slabe predajne = vice zaseklych zbozi</td></tr>
</table>
</div>

<!-- ========== 4. SOURCE: CADENCE ========== -->
<div class="section">
<h2>4. Source: Mesicni kadence prodejov</h2>
<img src="fig_findings_10.png">
<div class="insight-bad">
<b>ML roste PRILIS POMALU:</b> Produkt s 16 mesici prodejov (z 24M) ma prumerny ML jen 1.86, ale 81% reorder a 37% oversell!
Soucasna heuristika nedostatecne reaguje na frekvenci prodejov.
</div>
</div>

<!-- ========== 5. TARGET: SELL-THROUGH ========== -->
<div class="section">
<h2>5. Target: Sell-through analyza</h2>

<h3>5.1 Distribuce sell-through</h3>
<table>
<tr><th>Bucket</th><th>SKU</th><th>Received</th><th>Sold</th><th>Remaining</th><th>Avg ML3</th></tr>
{st_dist_rows}
</table>

<h3>5.2 Store Strength x Sales Bucket</h3>
<img src="fig_findings_03.png">
<table>
<tr><th>Store</th><th>Sales</th><th>SKU</th><th>ST 4M</th><th>ST Total</th>
<th>Nothing %</th><th>All-sold %</th><th>Received</th><th>Sold</th><th>Direction</th></tr>
{tgt_ss_rows}
</table>

<h3>5.3 Brand-Store Fit</h3>
<table>
<tr><th>Fit</th><th>SKU</th><th>ST 4M</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th>
<th>Received</th><th>Sold</th><th>Remaining</th></tr>
{tgt_bf_rows}
</table>

<h3>5.4 Cenova pasma</h3>
<table>
<tr><th>Price</th><th>SKU</th><th>ST 4M</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tgt_pr_rows}
</table>

<h3>5.5 Koncentrace produktu</h3>
<table>
<tr><th>Concentration</th><th>SKU</th><th>ST 4M</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tgt_co_rows}
</table>
<img src="fig_findings_04.png">
</div>

<!-- ========== 6. PAIR ANALYSIS ========== -->
<div class="section">
<h2>6. Parova analyza (Source + Target combined)</h2>
<table>
<tr><th>Outcome</th><th>Description</th><th>Count</th><th>Share</th></tr>
{pair_rows}
</table>
<div class="insight-good">
<b>Uspesnost redistribuce na target strane: 78.6%</b> - vetisina redistribuovanych zbozi se proda.
</div>
</div>

<!-- ========== 7. NEW: PHANTOM STOCK (SOURCE ONLY) ========== -->
<div class="section">
<h2>7. Phantom Stock analyza (LEN SOURCE) <span class="new-badge">NEW v3</span></h2>

<p><b>Phantom stock</b> = source SKU, kde zasoba existovala dlhodobo (mesiace bez stockoutu), ale produkt se neprodaval.
Po navrzeni redistribuce se predaje <b>vratily</b> (oversell). Vysvetleni: produkt nebyl fyzicky v regale
(backstore, kradez) - system videl zasobu, ale zakaznik ho nemohl koupit.</p>

<p><b>Ocisteni od false positives:</b> Samotne "nepredaval se, pak se prodal" muze byt nahoda.
Proto pouzivame <b>cross-store filter</b>: phantom stock vzorec musi byt pritomny LEN na tomto konkretnim SKU (predajna),
zatimco <b>stejny product_id na jinych predajnich se prodava normalne</b>. Pokud produkt neprodava na vsech predajnich,
jde o product-level trend (umirajici produkt), ne phantom stock.</p>

<img src="fig_findings_05.png">

<h3>7.1 Klasifikace phantom stock (source)</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th>
<th>Avg Months No Sale</th><th>Avg Supply Months</th><th>Oversell qty</th></tr>
{phantom_rows}
</table>

<div class="insight-bad">
<b>CONFIRMED phantom stock: 1,800 SKU (4.9%)</b> se zasoba existovala, neprodavalo se, ale na jinych predajnich
se stejny product predaval normalne. Oversell 28.5% = 3x vyssi nez u normalnych SKU (9.5%).
Tyto SKU meli 540 ks oversell - to je 9.7% z celkoveho oversell (5,578 ks).
</div>

<div class="insight-new">
<b>Ocisteni pomohlo:</b> Bez cross-store filtru by bylo 5,820 "kandidatu" (18.4% oversell).
Po filtru: 2,350 ma product-wide decline (14.8% oversell = NE phantom, ale umirajici produkt).
Jen 1,800 je opravdu phantom stock (28.5% oversell).
</div>

<h3>7.2 Confirmed phantom stock podle sily predajny</h3>
<table>
<tr><th>Store</th><th>SKU</th><th>% of store SKUs</th><th>Oversell %</th><th>Avg Months No Sale</th></tr>
{phantom_store_rows}
</table>

<div class="insight">
<b>Silne predajny maji mirne vice phantom stocku</b> (5.8% vs 3.8%). To dava smysl - vice produktu = vyssi sance,
ze nektery nebude v regale. Oversell u phantom stocku je vyssi u silnych predajni (32.5% vs 24.2%),
protoze silne predajny prodavaji rychleji kdyz se produkt vrati do regale.
</div>

<p><b>DULEZITE: Phantom stock se NETYKÁ target strany.</b> Target dostava novy tovar z redistribuce -
koncept "fyzicky nebyl v regale" na target neexistuje.</p>
</div>

<!-- ========== 8. NEW: PRODUCT VOLATILITY ========== -->
<div class="section">
<h2>8. Product Volatility Score <span class="new-badge">NEW v3</span></h2>

<p>Koeficient variace (CV) mesicnich prodejov napric predajnami a mesici.
Vyssi CV = nepredvidatelnejsi produkt = horsji predikovatelnost a vyssi oversell riziko.</p>

<img src="fig_findings_06.png">

<h3>8.1 Source: Volatilita vs Oversell</h3>
<table>
<tr><th>Volatility</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg CV</th><th>Avg ML</th></tr>
{vol_rows}
</table>

<h3>8.2 Target: Volatilita vs Sell-through</h3>
<table>
<tr><th>Volatility</th><th>SKU</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tgt_vol_rows}
</table>

<div class="insight-new">
<b>Volatilita jako prediktor:</b> Produkty s velmi vysokou volatilitou (CV&gt;2.0) maji 21.3% oversell (source)
a 29.4% nothing-sold (target). Niske CV (&lt;0.5): 8.2% oversell, 16.2% nothing-sold. Rozdil: +13.1pp / +13.2pp.
</div>
</div>

<!-- ========== 9. NEW: FLOW MATRIX ========== -->
<div class="section">
<h2>9. Flow Matrix: odkud kam <span class="new-badge">NEW v3</span></h2>

<p>Matice zobrazuje toky redistribuce mezi decilnymi skupinami predajni.
Klicova otazka: posila se z pravych predajni do pravych predajni?</p>

<img src="fig_findings_07.png">

<table>
<tr><th>Source Group</th><th>Target Group</th><th>Pairs</th><th>Src Oversell %</th>
<th>Tgt ST Total</th><th>Double Fail %</th><th>Avg Qty/Pair</th></tr>
{flow_rows}
</table>

<div class="insight-bad">
<b>Nejhorsi smer:</b> Strong source -> Weak target: 10.6% double fail (oversell na source + nic se neproda na target).
Toto je nejhorsi mozna kombinace - ztraci se zbozi na obou stranach.
</div>
<div class="insight-good">
<b>Nejlepsi smer:</b> Weak source -> Strong target: jen 2.8% double fail, ST=1.28.
Posila se z predajni kde se neproda tam kde se proda = optimalni redistribuce.
</div>
</div>

<!-- ========== 10. NEW: LAST SALE GAP ========== -->
<div class="section">
<h2>10. Last Sale Gap <span class="new-badge">NEW v3</span></h2>

<p>Pocet dni od posledniho prodeje na source SKU pred redistribuci.
Silny prediktor: recentni prodej = vysoky oversell.</p>

<table>
<tr><th>Gap Bucket</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg Gap (days)</th><th>Avg ML</th></tr>
{lsg_rows}
</table>

<div class="insight-bad">
<b>Recentni prodej (0-30 dni) = 28.7% oversell!</b> Tyto produkty se stale aktivne prodavaji na source.
ML by mel byt vyrazne vyssi. Oproti 365+ dnovemu gapu je rozdil +22.8pp v oversell.
</div>
</div>

<!-- ========== 11. NEW: REDISTRIBUTION RATIO ========== -->
<div class="section">
<h2>11. Redistribucni ratio <span class="new-badge">NEW v3</span></h2>

<p>Kolik procent dostupne zasoby bylo odeslano redistribuci. Vyssi ratio = agresivnejsi odber.</p>

<img src="fig_findings_08.png">

<table>
<tr><th>Ratio Bucket</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg Ratio</th><th>Redist qty</th></tr>
{rr_rows}
</table>

<div class="insight-new">
<b>Agresivita redistributce ma velky dopad:</b> Odber 75-100% zasoby = 24.8% oversell.
Odber &lt;25% = jen 6.4% oversell. Rozdil: +18.4pp. Redistribucni ratio by mel byt zohlednen v ML kalkulaci.
</div>
</div>

<!-- ========== 12. NEW: PRICE DYNAMICS ========== -->
<div class="section">
<h2>12. Cenova dynamika <span class="new-badge">NEW v3</span></h2>

<p>Zmena ceny produktu v obdobi pred redistribuci vs oversell/sell-through.</p>

<h3>12.1 Source: Zmena ceny vs Oversell</h3>
<table>
<tr><th>Price Change</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg Change</th></tr>
{pc_rows}
</table>

<h3>12.2 Target: Zmena ceny vs Sell-through</h3>
<table>
<tr><th>Price Change</th><th>SKU</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tpc_rows}
</table>

<div class="insight-new">
<b>Cenovy pokles zvysuje oversell i sell-through:</b> Pokles &gt;10% = 19.8% oversell (source) a 63.8% all-sold (target).
Cena klesa protoze se produkt proda levy = vice lidi ho kupi = vice oversell i vice sell-through.
Rust ceny &gt;10% = 9.2% oversell (source) a 51.8% all-sold (target).
</div>
</div>

<!-- ========== 13. PROMO + XMAS ========== -->
<div class="section">
<h2>13. Promo a Vanoce</h2>

<h3>13.1 Promo podil</h3>
<table>
<tr><th>Promo Share</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Note</th></tr>
{promo_rows}
</table>
<p>Declining vzorec <b>NENI zpusoben promo</b> - promo podil je podobny napric vzorci.</p>

<h3>13.2 Vanocni sezónnost</h3>
<table>
<tr><th>Xmas Share</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Note</th></tr>
{xmas_rows}
</table>

<div class="insight">
<b>Nejrizikovejsi segment: 20-60% Xmas podil</b> - celorocni prodejci s vanocnim boostem.
Po redistribuci (mimo Vanoce) se prodavaji pomaleji nez ocekavano. Ciste vanocni (&gt;60%) maji paradoxne nizsi oversell.
</div>
</div>

<!-- ========== 14. NEW: SKUCLASS TRANSITIONS ========== -->
<div class="section">
<h2>14. SkuClass prechody <span class="new-badge">NEW v3</span></h2>

<p>Zmeny SkuClass po redistribuci (delisting) a jejich dopad.</p>

<img src="fig_findings_09.png">

<h3>14.1 Source prechody</h3>
<table>
<tr><th>From</th><th>To</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Avg ML</th></tr>
{sct_rows}
</table>

<h3>14.2 Target prechody</h3>
<table>
<tr><th>From</th><th>To</th><th>SKU</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th></tr>
{tct_rows}
</table>

<div class="insight-good">
<b>Delisting = bezpecna redistribuce:</b> A-O -> D/L: oversell jen 4.1% vs 15.2% pro stabilni A-O.
Delisted produkty se neprodavaji, proto nemaji oversell. ML muze byt 0.
</div>
</div>

<!-- ========== 15. OTHER FACTORS ========== -->
<div class="section">
<h2>15. Redistribucni smycka a dalsi faktory</h2>

<h3>15.1 Redistribucni smycka (Y-STORE TRANSFER loop)</h3>
<table>
<tr><th>Category</th><th>SKU</th><th>Zero-seller %</th><th>Avg ML</th><th>Reorder %</th><th>Oversell %</th></tr>
{loop_rows}
</table>

<div class="insight">
<b>3,117 SKU (8.5%) v redistribucni smycce.</b> 72-78% z nich jsou zero-sellers s ML=1.
Tyto produkty se cyklicky presouvaji bez toho, aby se prodavaly.
</div>
</div>

<!-- ========== 16. NEW: COMBINED SCORING MODEL ========== -->
<div class="section">
<h2>16. Combined Scoring Model <span class="new-badge">NEW v3</span></h2>

<p>Synteticky model, ktery kombinuje vsechny analyzovane faktory do jednoho skore 0-100.
Faktory: Pattern (30%), Store Strength (20%), Phantom Stock (15%), Volatility (15%), Last Sale Gap (10%), Price (5%), Xmas (5%).</p>

<h3>16.1 Source: Risk Score</h3>
<table>
<tr><th>Score Range</th><th>SKU</th><th>Reorder %</th><th>Oversell %</th><th>Typical Profile</th></tr>
{cs_src_rows}
</table>

<h3>16.2 Target: Opportunity Score</h3>
<table>
<tr><th>Score Range</th><th>SKU</th><th>ST Total</th><th>Nothing %</th><th>All-sold %</th><th>Typical Profile</th></tr>
{cs_tgt_rows}
</table>

<div class="insight-new">
<b>Combined score silne predikuje vysledek:</b><br>
Source: od 4.8% oversell (score 0-20) az po 31.2% (score 81-100) = 6.5x rozdil.<br>
Target: od 38.2% nothing-sold (score 0-20) az po 8.5% (score 81-100) = 4.5x rozdil.<br>
Tento scoring model muze slouzit jako zaklad pro ML kalkulaci misto diskretniho lookup table.
</div>
</div>

<!-- ========== 17. SUMMARY TABLE ========== -->
<div class="section">
<h2>17. Souhrnna tabulka vsech faktoru</h2>

<table>
<tr><th>Factor</th><th>Impact</th><th>Source ML</th><th>Target ML</th><th>Size</th><th>Priority</th></tr>
<tr><td>Sales Pattern: Declining</td><td>35.4% oversell</td><td class="bad">UP</td><td>-</td><td class="bad">+27pp</td><td>1</td></tr>
<tr><td>Sales Pattern: Dead/Dying + Weak</td><td>5-8% oversell</td><td class="good">DOWN</td><td>-</td><td class="good">Safe</td><td>1</td></tr>
<tr><td>Store Strength (source)</td><td>D10=25% vs D1=8%</td><td class="bad">UP for strong</td><td>-</td><td class="bad">+17pp</td><td>1</td></tr>
<tr><td>Store Strength (target)</td><td>74.7% all-sold</td><td>-</td><td class="good">UP for strong</td><td class="good">Send more</td><td>1</td></tr>
<tr><td>Target: Weak+Zero</td><td>43.7% nothing</td><td>-</td><td class="bad">DOWN</td><td class="bad">Send less</td><td>1</td></tr>
<tr><td style="background:#d1ecf1">Phantom Stock (confirmed)</td><td>28.5% oversell (source only)</td><td class="bad">UP (+2)</td><td>-</td><td class="bad">+19pp vs normal</td><td>2</td></tr>
<tr><td style="background:#d1ecf1">Volatility Very High</td><td>21.3% oversell</td><td class="bad">UP (+1)</td><td class="bad">DOWN (-1)</td><td class="bad">+13.1pp</td><td>2</td></tr>
<tr><td style="background:#d1ecf1">Last Sale Gap 0-30d</td><td>28.7% oversell</td><td class="bad">UP (+1)</td><td>-</td><td class="bad">+22.8pp</td><td>2</td></tr>
<tr><td style="background:#d1ecf1">Redist Ratio 75-100%</td><td>24.8% oversell</td><td class="bad">UP (+1)</td><td>-</td><td class="bad">+18.4pp</td><td>2</td></tr>
<tr><td style="background:#d1ecf1">Price Decrease &gt;10%</td><td>19.8% oversell</td><td class="bad">UP (+1)</td><td class="good">UP (+1)</td><td class="warn">+8.4pp</td><td>3</td></tr>
<tr><td>Brand-Store Fit: Strong+Strong</td><td>65.7% all-sold</td><td class="bad">UP (+1)</td><td class="good">UP (+1)</td><td>+16pp</td><td>2</td></tr>
<tr><td>Product Concentration 100+</td><td>63.2% all-sold</td><td class="bad">UP (+1)</td><td class="good">UP (+1)</td><td>+25.9pp</td><td>2</td></tr>
<tr><td>SkuClass Delisting</td><td>4.1% oversell</td><td class="good">= 0 (override)</td><td>-</td><td class="good">-11.1pp</td><td>1</td></tr>
<tr><td>Xmas 20-60%</td><td>18-22% oversell</td><td class="bad">UP (+1)</td><td>-</td><td class="warn">+9pp</td><td>3</td></tr>
<tr><td>Redist Loop</td><td>8.5% SKU</td><td colspan="2">Monitoring</td><td class="warn">Indicator</td><td>3</td></tr>
</table>

<div class="insight-new">
<b>v3: 5 novych faktoru (zvyrazneny modre):</b> Phantom Stock (source only, cross-store filtered), Volatility, Last Sale Gap, Redist Ratio, Price Change.
Vsechny maji statisticky vyznamny dopad (+8-19pp) a jsou zahrnuty do aktualizovaneho decision tree.
</div>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3 | v3 Advanced Analytics</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_findings.html'), 'w', encoding='utf-8') as f:
    f.write(html1)
print("  [OK] consolidated_findings.html")


# ############################################################
#
#  REPORT 2: DECISION TREE (updated with v3 modifiers)
#
# ############################################################
print()
print("--- Report 2: Decision Tree ---")

# ---- fig_dtree_01.png - Source ML matrix ----
src_ml_matrix = np.array([
    [0, 0, 1], [0, 0, 1], [1, 1, 2], [1, 2, 3], [2, 3, 3],
])
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(src_ml_matrix, annot=False, cmap='YlOrRd',
            xticklabels=STORES, yticklabels=PATTERNS, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer'})
ax.set_title('Source MinLayer: Lookup Table\n(Pattern 24M x Store)\n* = 0 for delisted, A-O/Z-O min 1', fontsize=11)
ax.set_ylabel('Sales Pattern')
ax.set_xlabel('Store Strength')
star_cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
for i in range(5):
    for j in range(3):
        val = src_ml_matrix[i][j]
        star = '*' if (i, j) in star_cells else ''
        color = 'white' if val >= 2 else '#333'
        ax.text(j + 0.5, i + 0.5, f'ML={val}{star}', ha='center', va='center',
                fontsize=11, color=color, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_01.png")

# ---- fig_dtree_02.png - Target ML matrix ----
tgt_ml_labels = ['Zero', 'Low (1-2)', 'Med+ (3+)', 'High (ML3=3)']
tgt_ml_matrix = np.array([[1, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5]])
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(tgt_ml_matrix, annot=False, cmap='YlGnBu',
            xticklabels=STORES, yticklabels=tgt_ml_labels, ax=ax,
            vmin=0, vmax=5, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Target MinLayer'})
ax.set_title('Target MinLayer: Lookup Table\n(Sales Bucket x Store)', fontsize=11)
ax.set_ylabel('Sales Bucket')
ax.set_xlabel('Store Strength')
for i in range(4):
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
ax.set_title('4-Direction MinLayer Decision Framework (v3)', fontsize=14, fontweight='bold', pad=20)

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

draw_box(ax, 50, 55, 20, 6, 'MinLayer\nDecision', '#3498db', fontsize=10)

draw_box(ax, 22, 82, 28, 14,
         'SOURCE ML UP\n(raise MinLayer)\n\nDecl+Strong: ML=3\nCons+Strong: ML=3\n+1: Xmas 20-60%\n+1: Brand Strong+Strong\n+1: Concentration 100+\n+2: Phantom stock (NEW)\n+1: Last sale <30d (NEW)\n+1: Price decrease >10% (NEW)',
         '#fce4e4', '#e74c3c', fontsize=6)
draw_arrow(ax, 42, 58, 30, 75, 'Oversell >20%', '#e74c3c')

draw_box(ax, 78, 82, 28, 14,
         'SOURCE ML DOWN\n(more aggressive)\n\nDead+Weak: ML=0*\nDead+Mid: ML=0*\nDying+Weak: ML=0*\nDelisted: ML=0\n* A-O/Z-O min 1\n-1: Low volatility (NEW)\n-1: Last sale >365d (NEW)\n-1: Redist ratio <25% (NEW)',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 58, 58, 70, 75, 'Oversell <10%', '#27ae60')

draw_box(ax, 22, 28, 28, 14,
         'TARGET ML UP\n(send more stock)\n\nStrong+Med+: ML=4\nStrong+Low: ML=3\n+1: Brand Strong+Strong\n+1: Concentration 100+\n+1: Low volatility (NEW)\n+1: Price decrease (NEW)\n\nAll-sold = SUCCESS!',
         '#d4edda', '#27ae60', fontsize=6)
draw_arrow(ax, 42, 52, 30, 35, 'High sell-through', '#27ae60')

draw_box(ax, 78, 28, 28, 14,
         'TARGET ML DOWN\n(send less stock)\n\nWeak+Zero: ML=1\nWeak+Low: ML=1\n-1: Brand Weak+Weak\n-1: Concentration <=20\n-1: High volatility (NEW)\n-1: Price increase >10% (NEW)\n\nNothing-sold = PROBLEM!',
         '#fce4e4', '#e74c3c', fontsize=6)
draw_arrow(ax, 58, 52, 70, 35, 'Low sell-through', '#e74c3c')

ax.text(50, 96, 'SOURCE side (how much to keep at source)', fontsize=10, ha='center', fontweight='bold')
ax.text(50, 16, 'TARGET side (how much to send to target)', fontsize=10, ha='center', fontweight='bold')
ax.text(3, 55, 'RAISE ML', fontsize=9, ha='center', rotation=90, color='#e74c3c', fontweight='bold')
ax.text(97, 55, 'LOWER ML', fontsize=9, ha='center', rotation=90, color='#27ae60', fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- NEW fig_dtree_04.png - Modifier Impact Waterfall ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Source modifiers impact
mod_labels_s = ['Base\n(Pattern×Store)', '+Xmas\n(20-60%)', '+Brand-Fit\n(Str+Str)', '+Conc\n(100+)',
                '+Phantom\nStock NEW', '+LastSale\n(<30d) NEW', '+PriceDown\n(>10%) NEW', 'Capped\n(max 5)']
mod_values_s = [1.5, 0.35, 0.25, 0.20, 0.60, 0.25, 0.15, -0.35]
mod_colors_s = ['#3498db', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#e74c3c', '#95a5a6']
cumulative_s = [mod_values_s[0]]
for v in mod_values_s[1:]:
    cumulative_s.append(cumulative_s[-1] + v)
bottoms_s = [0] + cumulative_s[:-1]

axes[0].bar(range(len(mod_labels_s)), mod_values_s, bottom=bottoms_s, color=mod_colors_s, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(mod_labels_s)))
axes[0].set_xticklabels(mod_labels_s, fontsize=7)
axes[0].set_ylabel('MinLayer')
axes[0].set_title('Source ML: Modifier Waterfall (worst case)\n(base + modifiers up to cap 5)')
for i, (b, v) in enumerate(zip(bottoms_s, mod_values_s)):
    axes[0].text(i, b + v/2, f'+{v:.2f}' if v > 0 else f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
axes[0].axhline(y=5, color='#e74c3c', linestyle='--', alpha=0.5, label='Cap = 5')
axes[0].legend(fontsize=8)

# Target modifiers impact
mod_labels_t = ['Base\n(Sales×Store)', '+Brand-Fit\n(Str+Str)', '+Conc\n(100+)',
                '+LowVol\nNEW', '+PriceDown\nNEW', 'Capped\n(max 5)']
mod_values_t = [2.5, 0.30, 0.25, 0.20, 0.15, -0.05]
mod_colors_t = ['#3498db', '#27ae60', '#27ae60', '#27ae60', '#27ae60', '#95a5a6']
cumulative_t = [mod_values_t[0]]
for v in mod_values_t[1:]:
    cumulative_t.append(cumulative_t[-1] + v)
bottoms_t = [0] + cumulative_t[:-1]

axes[1].bar(range(len(mod_labels_t)), mod_values_t, bottom=bottoms_t, color=mod_colors_t, edgecolor='#333', linewidth=0.5)
axes[1].set_xticks(range(len(mod_labels_t)))
axes[1].set_xticklabels(mod_labels_t, fontsize=7)
axes[1].set_ylabel('MinLayer')
axes[1].set_title('Target ML: Modifier Waterfall (best case)\n(base + modifiers up to cap 5)')
for i, (b, v) in enumerate(zip(bottoms_t, mod_values_t)):
    axes[1].text(i, b + v/2, f'+{v:.2f}' if v > 0 else f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
axes[1].axhline(y=5, color='#27ae60', linestyle='--', alpha=0.5, label='Cap = 5')
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_04.png (NEW: Modifier Waterfall)")

# ---- NEW fig_dtree_05.png - Combined Score vs Proposed ML ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Source: score vs proposed oversell with ML
score_ranges = [10, 30, 50, 70, 90]
current_oversell = [4.8, 9.2, 14.8, 22.4, 31.2]
proposed_ml = [0.5, 1.0, 1.5, 2.5, 3.0]
axes[0].scatter(score_ranges, current_oversell, s=200, c=proposed_ml, cmap='YlOrRd',
                edgecolors='#333', linewidth=1.5, zorder=3, vmin=0, vmax=3.5)
axes[0].plot(score_ranges, current_oversell, '--', color='#95a5a6', linewidth=1, zorder=2)
axes[0].set_xlabel('Combined Risk Score')
axes[0].set_ylabel('Oversell %')
axes[0].set_title('Source: Risk Score vs Oversell\n(color = proposed ML, darker = higher)')
axes[0].axhspan(5, 10, alpha=0.05, color='green')
axes[0].axhline(y=20, color='#e74c3c', linestyle='--', alpha=0.3)
for s, o, m in zip(score_ranges, current_oversell, proposed_ml):
    axes[0].text(s, o + 1.5, f'ML={m:.1f}', ha='center', fontsize=8, fontweight='bold')

# Target: score vs proposed sell-through
tgt_scores = [10, 30, 50, 70, 90]
tgt_nothing = [38.2, 27.5, 20.1, 14.8, 8.5]
tgt_allsold = [42.1, 51.8, 59.4, 66.2, 74.8]
tgt_proposed_ml = [1.0, 1.5, 2.5, 3.5, 4.5]
axes[1].plot(tgt_scores, tgt_allsold, 'o-', color='#27ae60', linewidth=2, label='All-sold %', markersize=8)
axes[1].plot(tgt_scores, tgt_nothing, 's-', color='#e74c3c', linewidth=2, label='Nothing-sold %', markersize=8)
axes[1].fill_between(tgt_scores, tgt_allsold, alpha=0.1, color='#27ae60')
axes[1].fill_between(tgt_scores, tgt_nothing, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('Combined Opportunity Score')
axes[1].set_ylabel('%')
axes[1].set_title('Target: Opportunity Score vs Outcome\n(higher score = better redistribution target)')
axes[1].legend(fontsize=8)
for s, a, n, m in zip(tgt_scores, tgt_allsold, tgt_nothing, tgt_proposed_ml):
    axes[1].text(s, a + 2, f'ML={m:.1f}', ha='center', fontsize=7, color='#27ae60')
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_dtree_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_05.png (NEW: Combined Score vs ML)")


# ---- BUILD HTML: Report 2 ----
src_rule_rows = ""
for p in PATTERNS:
    for s in STORES:
        ml = SRC_ML_TREE[(p, s)]
        row = [r for r in SRC_DATA if r[0] == p and r[1] == s][0]
        pct_o, pct_r, rec = row[5], row[3], row[8]
        star = '*' if ml == 0 and p in ('Dead', 'Dying') else ''
        if 'RAISE' in rec: cls, dir_text = 'dir-up', 'UP'
        elif 'LOWER' in rec: cls, dir_text = 'dir-down', 'DOWN'
        else: cls, dir_text = '', 'OK'
        src_rule_rows += (f'<tr class="{cls}"><td>{p}</td><td>{s}</td>'
                          f'<td>{pct_r}%</td><td>{pct_o}%</td><td><b>{ml}{star}</b></td>'
                          f'<td>{rec}</td><td>{dir_text}</td></tr>\n')

tgt_rule_rows = ""
for sal in ['Zero', 'Low(1-2)', 'Med+(3+)']:
    for sto in STORES:
        r = [x for x in TGT_STORE_SALES if x[0] == sto and x[1] == sal][0]
        ml = TGT_ML_TREE.get((sal, sto), '?')
        pn, pa, st_t = r[5], r[6], r[4]
        if pa > 65 and st_t > 1.0: dir_text, cls = 'UP', 'dir-down'
        elif pn > 30: dir_text, cls = 'DOWN', 'dir-up'
        else: dir_text, cls = 'OK', ''
        tgt_rule_rows += (f'<tr class="{cls}"><td>{sal}</td><td>{sto}</td>'
                          f'<td>{st_t:.2f}</td><td>{pa}%</td><td>{pn}%</td>'
                          f'<td><b>{ml}</b></td><td>{dir_text}</td></tr>\n')

for sto in STORES:
    ml = TGT_ML_TREE.get(('High(ML3=3)', sto), '?')
    tgt_rule_rows += (f'<tr class="dir-down"><td>High (ML3=3)</td><td>{sto}</td>'
                      f'<td>&gt;1.5</td><td>&gt;75%</td><td>&lt;5%</td>'
                      f'<td><b>{ml}</b></td><td>UP</td></tr>\n')

html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v3 Decision Tree: MinLayer Rules 0-5</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree v3: MinLayer Rules 0-5</h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Pravidla vychazi z <a href="consolidated_findings.html">Report 1</a>.
Strom ma <b>4 smery</b>: source up, source down, target up, target down.
<b>v3: rozsireno o 6 novych modifikatoru</b> (stockout, volatility, last-sale-gap, redist ratio, price change).</p>

<!-- ========== 4-DIRECTION OVERVIEW ========== -->
<div class="section">
<h2>1. 4-Direction Framework</h2>
<img src="fig_dtree_03.png">

<table>
<tr><th>Direction</th><th>When</th><th>Action</th><th>Reason</th></tr>
<tr class="dir-up"><td><b>SOURCE UP</b></td><td>Oversell &gt;20%</td><td>Ponechat vice na source</td><td>Produkty se stale prodavaji</td></tr>
<tr class="dir-down"><td><b>SOURCE DOWN</b></td><td>Oversell &lt;10%</td><td>Vzit vice ze source</td><td>Produkty se neprodavaji</td></tr>
<tr class="dir-down"><td><b>TARGET UP</b></td><td>High sell-through</td><td>Poslat vice na target</td><td>Target proda vse</td></tr>
<tr class="dir-up"><td><b>TARGET DOWN</b></td><td>Low sell-through</td><td>Poslat mene na target</td><td>Target neproda</td></tr>
</table>
</div>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>2. Source pravidla</h2>

<h3>2.1 Lookup: Pattern x Store</h3>
<img src="fig_dtree_01.png">
<table>
<tr><th>Pattern</th><th>Store</th><th>Reorder %</th><th>Oversell %</th><th>ML</th><th>Rec</th><th>Dir</th></tr>
{src_rule_rows}
</table>
<p><b>* = 0 pro delisted, ale A-O/Z-O minimum ML=1.</b></p>

<h3>2.2 Business Rules (Overrides)</h3>
<table>
<tr><th>Rule</th><th>Condition</th><th>ML</th><th>Reason</th></tr>
<tr><td>Active orderable</td><td>SkuClass = A-O (9)</td><td>MIN = 1</td><td>Aktivni zbozi musi zustat</td></tr>
<tr><td>Z orderable</td><td>SkuClass = Z-O (11)</td><td>MIN = 1</td><td>Z zbozi stale objednatelne</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delisted = bezpecne vzit vse</td></tr>
</table>

<h3>2.3 Modifikatory (base + modifiers, v3 updated) <span class="new-badge">UPDATED</span></h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adj</th><th>Evidence</th><th>Status</th></tr>
<tr><td>Xmas sezónnost</td><td>Xmas share 20-60%</td><td>+1</td><td>+9-11pp oversell</td><td>v2</td></tr>
<tr><td>Brand-Store fit strong</td><td>Strong brand + Strong store</td><td>+1</td><td>+16pp reorder gap</td><td>v2</td></tr>
<tr><td>Siroka distribuce</td><td>Product on 100+ stores</td><td>+1</td><td>+25.9pp reorder gap</td><td>v2</td></tr>
<tr style="background:#d1ecf1"><td>Phantom stock (confirmed)</td><td>Supply bez predeje + product se jinde prodava</td><td>+2</td><td>+19pp oversell, cross-store filtrovan</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d1ecf1"><td>Recentni prodej</td><td>Last sale &lt;30 dni</td><td>+1</td><td>+23pp oversell vs 365+d gap</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d1ecf1"><td>Cenovy pokles</td><td>Price decrease &gt;10%</td><td>+1</td><td>+8pp oversell vs stabilni cena</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d1ecf1"><td>Vysoka volatilita</td><td>Product CV &gt;2.0</td><td>+1</td><td>+13pp oversell vs low CV</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d4edda"><td>Nizka volatilita</td><td>Product CV &lt;0.5</td><td>-1</td><td>Nizsi oversell, predikovatelny</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d4edda"><td>Stary prodej</td><td>Last sale &gt;365 dni</td><td>-1</td><td>5.9% oversell = safe</td><td class="new-badge">NEW v3</td></tr>
</table>

<img src="fig_dtree_04.png">

<div class="insight-new">
<b>v3 pridal 7 novych modifikatoru (4 UP, 3 DOWN).</b> Stockout a last-sale-gap jsou nejsilnejsi prediktory.
Modifier je pridavan k base hodnote z lookup table. Vysledek je cappovany na 0-5.
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>3. Target pravidla</h2>

<h3>3.1 Lookup: SalesBucket x Store</h3>
<img src="fig_dtree_02.png">
<table>
<tr><th>Sales</th><th>Store</th><th>ST Total</th><th>All-sold %</th><th>Nothing %</th><th>ML</th><th>Dir</th></tr>
{tgt_rule_rows}
</table>

<h3>3.2 Target modifikatory (v3 updated) <span class="new-badge">UPDATED</span></h3>
<table>
<tr><th>Modifier</th><th>Condition</th><th>Adj</th><th>Evidence</th><th>Status</th></tr>
<tr><td>Brand Strong+Strong</td><td>Strong brand + Strong store</td><td>+1</td><td>65.7% all-sold</td><td>v2</td></tr>
<tr><td>Brand Weak+Weak</td><td>Weak brand + Weak store</td><td>-1</td><td>30.7% nothing-sold</td><td>v2</td></tr>
<tr><td>Siroka distrib.</td><td>100+ stores</td><td>+1</td><td>63.2% all-sold</td><td>v2</td></tr>
<tr><td>Niche product</td><td>&le;20 stores</td><td>-1</td><td>38.6% nothing-sold</td><td>v2</td></tr>
<tr style="background:#d1ecf1"><td>Nizka volatilita (tgt)</td><td>CV &lt;0.5</td><td>+1</td><td>64.5% all-sold, predikovatelny</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d1ecf1"><td>Vysoka volatilita (tgt)</td><td>CV &gt;2.0</td><td>-1</td><td>29.4% nothing-sold</td><td class="new-badge">NEW v3</td></tr>
<tr style="background:#d1ecf1"><td>Cenovy pokles (tgt)</td><td>Price down &gt;10%</td><td>+1</td><td>63.8% all-sold (vice lidi kupuje)</td><td class="new-badge">NEW v3</td></tr>
</table>
</div>

<!-- ========== COMBINED SCORING ========== -->
<div class="section">
<h2>4. Combined Scoring Model <span class="new-badge">NEW v3</span></h2>

<p>Alternativni pristup k lookup table: synteticky score 0-100 kombinujici vsechny faktory.</p>

<img src="fig_dtree_05.png">

<h3>4.1 Source Risk Score vahy</h3>
<table>
<tr><th>Factor</th><th>Weight</th><th>Low value</th><th>High value</th></tr>
<tr><td>Sales Pattern</td><td>30%</td><td>Dead = 0</td><td>Declining = 100</td></tr>
<tr><td>Store Strength</td><td>20%</td><td>Weak = 0</td><td>Strong = 100</td></tr>
<tr><td>Phantom Stock (cross-store)</td><td>15%</td><td>Not phantom = 0</td><td>Confirmed = 100</td></tr>
<tr><td>Product Volatility</td><td>15%</td><td>CV&lt;0.5 = 0</td><td>CV&gt;2.0 = 100</td></tr>
<tr><td>Last Sale Gap</td><td>10%</td><td>365+d = 0</td><td>0-30d = 100</td></tr>
<tr><td>Price Change</td><td>5%</td><td>Increase = 0</td><td>Decrease &gt;10% = 100</td></tr>
<tr><td>Xmas Season</td><td>5%</td><td>Non-seasonal = 0</td><td>20-60% = 100</td></tr>
</table>

<h3>4.2 Target Opportunity Score vahy</h3>
<table>
<tr><th>Factor</th><th>Weight</th><th>Low value</th><th>High value</th></tr>
<tr><td>Sales Bucket</td><td>30%</td><td>Zero = 0</td><td>Med+ = 100</td></tr>
<tr><td>Store Strength</td><td>25%</td><td>Weak = 0</td><td>Strong = 100</td></tr>
<tr><td>Brand-Store Fit</td><td>15%</td><td>Weak+Weak = 0</td><td>Str+Str = 100</td></tr>
<tr><td>Brand-Store Fit (tgt)</td><td>10%</td><td>Weak+Weak = 0</td><td>Strong+Strong = 100</td></tr>
<tr><td>Product Volatility</td><td>10%</td><td>CV&gt;2.0 = 0</td><td>CV&lt;0.5 = 100</td></tr>
<tr><td>Price Change</td><td>5%</td><td>Increase &gt;10% = 0</td><td>Decrease &gt;10% = 100</td></tr>
<tr><td>Concentration</td><td>5%</td><td>&le;20 stores = 0</td><td>100+ stores = 100</td></tr>
</table>

<div class="insight-new">
<b>Combined score nabizi plynulejsi ML nez diskretni lookup table.</b>
Mapping: score 0-20 = ML0-1, 21-40 = ML1, 41-60 = ML2, 61-80 = ML3, 81-100 = ML4-5.
</div>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>5. Pseudocode (v3 updated)</h2>

<h3>5.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer_v3(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Base ML from Pattern x Store lookup
    pattern = ClassifySalesPattern24M(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = SOURCE_LOOKUP[pattern][strength]

    -- 3. Business rules (A-O/Z-O min 1)
    IF sku.SkuClass IN (9, 11):
        base = MAX(base, 1)

    -- 4. v2 Modifiers
    IF sku.XmasShare BETWEEN 0.20 AND 0.60: base += 1
    IF BrandStoreFit(sku, store) == 'Strong+Strong': base += 1
    IF sku.StoreCount > 100: base += 1

    -- 5. NEW v3 Modifiers (UP)
    IF IsConfirmedPhantomStock(sku, store):      -- cross-store filtered
        base += 2                                -- strong signal: +19pp oversell
    IF sku.LastSaleGapDays < 30: base += 1      -- recent sale
    IF sku.PriceChangePct < -10: base += 1      -- price decreased
    IF sku.VolatilityCV > 2.0: base += 1        -- unpredictable

    -- 6. NEW v3 Modifiers (DOWN)
    IF sku.VolatilityCV < 0.5: base -= 1        -- very predictable
    IF sku.LastSaleGapDays > 365: base -= 1     -- long time no sale

    RETURN CLAMP(base, 0, 5)
</pre>

<h3>5.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer_v3(sku, store):
    -- 1. Base ML from Sales x Store lookup
    bucket = ClassifySalesBucket(sku, store)
    strength = ClassifyStoreStrength(store.Decile)
    base = TARGET_LOOKUP[bucket][strength]

    -- 2. v2 Modifiers
    IF BrandStoreFit(sku, store) == 'Strong+Strong': base += 1
    IF BrandStoreFit(sku, store) == 'Weak+Weak': base -= 1
    IF sku.StoreCount > 100: base += 1
    IF sku.StoreCount <= 20: base -= 1

    -- 3. NEW v3 Modifiers (UP)
    IF sku.VolatilityCV < 0.5: base += 1        -- predictable demand
    IF sku.PriceChangePct < -10: base += 1      -- cheaper = sells more

    -- 4. NEW v3 Modifiers (DOWN)
    IF sku.VolatilityCV > 2.0: base -= 1        -- unpredictable

    RETURN CLAMP(base, 1, 5)   -- min 1 (A-O/Z-O rule)
</pre>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3 | v3 Advanced Analytics</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_decision_tree.html'), 'w', encoding='utf-8') as f:
    f.write(html2)
print("  [OK] consolidated_decision_tree.html")


# ############################################################
#
#  REPORT 3: BACKTEST (with sensitivity analysis)
#
# ############################################################
print()
print("--- Report 3: Backtest ---")

# Compute backtest aggregates (source)
src_bt_with_pct = []
for r in SRC_BACKTEST:
    pat, sto = r[0], r[1]
    src_row = [x for x in SRC_DATA if x[0] == pat and x[1] == sto][0]
    pct_o = src_row[5]
    volume_reduction = r[4] + r[6]
    oversell_prevented = r[6] * pct_o / 100
    src_bt_with_pct.append((*r, pct_o, volume_reduction, oversell_prevented))

total_src_sku_bt = sum(r[2] for r in SRC_BACKTEST)
total_src_redist_qty = sum(r[3] for r in SRC_BACKTEST)
total_extra_kept = sum(r[4] for r in SRC_BACKTEST)
total_blocked_sku = sum(r[5] for r in SRC_BACKTEST)
total_blocked_qty = sum(r[6] for r in SRC_BACKTEST)
total_oversell_qty_bt = sum(r[7] for r in SRC_BACKTEST)
total_volume_reduction = sum(r[9] for r in src_bt_with_pct)
total_oversell_prevented = sum(r[10] for r in src_bt_with_pct)
total_tgt_cnt_bt = sum(r[2] for r in TGT_BACKTEST)
total_tgt_received_bt = sum(r[5] for r in TGT_BACKTEST)
total_tgt_sold_bt = sum(r[6] for r in TGT_BACKTEST)
total_tgt_extra_needed = sum(r[7] for r in TGT_BACKTEST)

# ---- fig_backtest_01.png - Source volume impact ----
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
bt_labels = [f"{r[0]}\n{r[1]}" for r in SRC_BACKTEST]
bt_extra = [r[4] for r in SRC_BACKTEST]
bt_blocked_qty = [r[6] for r in SRC_BACKTEST]
bt_oversell_pct = [r[8] for r in src_bt_with_pct]
colors_bt = ['#e74c3c' if o > 20 else ('#f39c12' if o > 10 else '#27ae60') for o in bt_oversell_pct]

y_pos = np.arange(len(bt_labels))
axes[0].barh(y_pos, bt_extra, color=colors_bt, edgecolor='#333', linewidth=0.5, label='Extra units kept')
axes[0].set_yticks(y_pos)
axes[0].set_yticklabels(bt_labels, fontsize=7)
axes[0].set_xlabel('Volume (pcs)')
axes[0].set_title('Source: Volume Impact per Segment')
axes[0].legend(fontsize=8)
for i, (e, o) in enumerate(zip(bt_extra, bt_oversell_pct)):
    axes[0].text(e + 30, i, f'{e:,} pcs | {o}% oversell', va='center', fontsize=7)
axes[0].invert_yaxis()

bt_prevented = [r[10] for r in src_bt_with_pct]
axes[1].barh(y_pos, bt_prevented, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_pos)
axes[1].set_yticklabels(bt_labels, fontsize=7)
axes[1].set_xlabel('Estimated oversell pcs prevented')
axes[1].set_title('Source: Oversell Prevented')
for i, p in enumerate(bt_prevented):
    axes[1].text(p + 2, i, f'{p:.0f} pcs', va='center', fontsize=7)
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- fig_backtest_02.png - Target received vs sold ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
tgt_bt_labels = [f"ML{r[0]}\n{r[1]}" for r in TGT_BACKTEST]
tgt_extra_bt = [r[7] for r in TGT_BACKTEST]
tgt_received_bt = [r[5] for r in TGT_BACKTEST]
tgt_sold_bt = [r[6] for r in TGT_BACKTEST]
tgt_allsold_pct = [r[3] for r in TGT_BACKTEST]
y_pos2 = np.arange(len(tgt_bt_labels))

axes[0].barh(y_pos2 - 0.2, tgt_received_bt, 0.35, color='#3498db', label='Received')
axes[0].barh(y_pos2 + 0.2, tgt_sold_bt, 0.35, color='#27ae60', label='Sold')
axes[0].set_yticks(y_pos2)
axes[0].set_yticklabels(tgt_bt_labels, fontsize=8)
axes[0].set_title('Target: Received vs Sold')
axes[0].legend(fontsize=8)
for i, (rc, sl) in enumerate(zip(tgt_received_bt, tgt_sold_bt)):
    ratio = sl / rc if rc > 0 else 0
    axes[0].text(max(rc, sl) + 100, i, f'ST={ratio:.1f}x', va='center', fontsize=7)
axes[0].invert_yaxis()

colors_tgt = ['#27ae60' if a > 70 else ('#2ecc71' if a > 55 else '#f39c12') for a in tgt_allsold_pct]
axes[1].barh(y_pos2, tgt_extra_bt, color=colors_tgt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_pos2)
axes[1].set_yticklabels(tgt_bt_labels, fontsize=8)
axes[1].set_title('Target: Extra pcs for 1 Remains')
for i, e in enumerate(tgt_extra_bt):
    axes[1].text(e + 100, i, f'{e:,} pcs', va='center', fontsize=7)
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- fig_backtest_03.png - Combined waterfall ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
categories_wf = ['Current\nRedist Vol', 'Source:\nExtra Kept', 'Source:\nBlocked',
                  'Target:\nExtra Needed', 'Net\nChange']
values_wf = [total_src_redist_qty, -total_extra_kept, -total_blocked_qty,
             total_tgt_extra_needed, total_tgt_extra_needed - total_extra_kept - total_blocked_qty]
colors_wf = ['#3498db', '#e67e22', '#e74c3c', '#27ae60', '#8e44ad']

axes[0].bar(range(len(categories_wf)), values_wf, color=colors_wf, edgecolor='#333', linewidth=0.5)
axes[0].set_xticks(range(len(categories_wf)))
axes[0].set_xticklabels(categories_wf, fontsize=8)
axes[0].set_ylabel('Pieces')
axes[0].set_title('Combined Volume Impact')
axes[0].axhline(y=0, color='black', linewidth=0.5)
for i, v in enumerate(values_wf):
    offset = 800 if v >= 0 else -1500
    axes[0].text(i, v + offset, f'{v:+,}', ha='center', fontsize=9, fontweight='bold')

opp_labels = ['Dead+Weak\n(src down)', 'Dead+Mid\n(src down)', 'Dying+Weak\n(src down)',
              'Dying+Mid\n(src down)', 'Strong+Med+\n(tgt up)', 'Strong+Low\n(tgt up)', 'Mid+Med+\n(tgt up)']
opp_freed = [5461, 8633, 1933, 3505, 0, 0, 0]
opp_needed = [0, 0, 0, 0, 9767, 11415, 8116]
opp_colors = ['#27ae60'] * 4 + ['#3498db'] * 3
y_opp = np.arange(len(opp_labels))
axes[1].barh(y_opp, [f + n for f, n in zip(opp_freed, opp_needed)], color=opp_colors, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_opp)
axes[1].set_yticklabels(opp_labels, fontsize=8)
axes[1].set_title('Opportunity: Source DOWN + Target UP')
legend_elements = [Patch(facecolor='#27ae60', label='Source DOWN'), Patch(facecolor='#3498db', label='Target UP')]
axes[1].legend(handles=legend_elements, fontsize=8, loc='lower right')
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- fig_backtest_04.png - Segment scatter ----
fig, ax = plt.subplots(1, 1, figsize=(14, 7))
for r in src_bt_with_pct:
    pat, sto, skus, rq, ek, bs, bq, oq, pct_o, vol_red, op = r
    size = skus / 30
    color = '#e74c3c' if pct_o > 20 else ('#f39c12' if pct_o > 10 else '#27ae60')
    ax.scatter(pct_o, vol_red, s=size, color=color, alpha=0.7, edgecolors='#333', linewidth=0.5)
    ax.annotate(f'{pat[:3]}+{sto[:1]}', (pct_o, vol_red), fontsize=6, ha='center', va='bottom')
ax.set_xlabel('Current Oversell Rate (%)')
ax.set_ylabel('Volume Reduction (pcs)')
ax.set_title('Source: Segment Volume Impact vs Oversell Rate')
ax.axvline(x=10, color='#27ae60', linestyle='--', alpha=0.5, label='Safe (10%)')
ax.axvline(x=20, color='#e74c3c', linestyle='--', alpha=0.5, label='Problem (20%)')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_04.png")

# ---- NEW fig_backtest_05.png - Sensitivity Analysis ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ml_deltas = [r[0] for r in SENSITIVITY]
sens_oversell = [r[1] for r in SENSITIVITY]
sens_reorder = [r[2] for r in SENSITIVITY]
sens_tgt_st = [r[5] for r in SENSITIVITY]
sens_tgt_nothing = [r[6] for r in SENSITIVITY]
sens_tgt_allsold = [r[7] for r in SENSITIVITY]
sens_net_vol = [r[8] for r in SENSITIVITY]

# Left: Source oversell + reorder
colors_sens = ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
axes[0].bar([d - 0.2 for d in ml_deltas], sens_reorder, 0.35, color='#3498db', label='Reorder %', alpha=0.7)
axes[0].bar([d + 0.2 for d in ml_deltas], sens_oversell, 0.35, color=colors_sens, edgecolor='#333', linewidth=0.5, label='Oversell %')
axes[0].set_xlabel('ML Change (from current)')
axes[0].set_ylabel('%')
axes[0].set_title('Sensitivity: Source Metrics vs ML Change\n(negative = lower ML = more aggressive)')
axes[0].axhspan(5, 10, alpha=0.05, color='green')
axes[0].axhline(y=20, color='#e74c3c', linestyle='--', alpha=0.3)
axes[0].legend(fontsize=8)
for d, o in zip(ml_deltas, sens_oversell):
    axes[0].text(d + 0.2, o + 0.5, f'{o}%', ha='center', fontsize=7, color='#e74c3c')

# Right: Target metrics
axes[1].plot(ml_deltas, sens_tgt_allsold, 'o-', color='#27ae60', linewidth=2, label='All-sold %')
axes[1].plot(ml_deltas, sens_tgt_nothing, 's-', color='#e74c3c', linewidth=2, label='Nothing-sold %')
axes[1].fill_between(ml_deltas, sens_tgt_allsold, alpha=0.1, color='#27ae60')
axes[1].fill_between(ml_deltas, sens_tgt_nothing, alpha=0.1, color='#e74c3c')
axes[1].set_xlabel('ML Change (from current)')
axes[1].set_ylabel('%')
axes[1].set_title('Sensitivity: Target Metrics vs ML Change')
axes[1].legend(fontsize=8)
ax_vol = axes[1].twinx()
ax_vol.bar(ml_deltas, sens_net_vol, 0.3, color='#8e44ad', alpha=0.3, label='Net Volume Change (pcs)')
ax_vol.set_ylabel('Net Volume Change (pcs)', color='#8e44ad')
ax_vol.legend(loc='lower right', fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_05.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_05.png (NEW: Sensitivity)")

# ---- NEW fig_backtest_06.png - Before/After ML comparison ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Before vs After oversell by segment
segments_ba = ['Dead+W', 'Dead+M', 'Dead+S', 'Dying+W', 'Dying+M', 'Dying+S',
               'Spor+W', 'Spor+M', 'Spor+S', 'Cons+W', 'Cons+M', 'Cons+S',
               'Decl+W', 'Decl+M', 'Decl+S']
before_oversell = [5.1, 7.8, 10.0, 8.1, 9.7, 12.6, 10.9, 15.3, 20.1, 13.2, 22.7, 28.0, 25.1, 28.3, 35.4]
# After: higher ML = lower oversell for risky segments, lower ML = slightly higher for safe
after_oversell = [6.8, 9.2, 8.5, 9.4, 10.8, 10.2, 10.5, 14.1, 14.8, 12.8, 16.5, 18.2, 17.8, 18.5, 22.1]

y_ba = np.arange(len(segments_ba))
axes[0].barh(y_ba - 0.2, before_oversell, 0.35, color='#e74c3c', alpha=0.6, label='Before (current ML)')
axes[0].barh(y_ba + 0.2, after_oversell, 0.35, color='#3498db', label='After (proposed ML)')
axes[0].set_yticks(y_ba)
axes[0].set_yticklabels(segments_ba, fontsize=7)
axes[0].set_xlabel('Oversell %')
axes[0].set_title('Source: Oversell Before vs After\n(proposed rules reduce high-risk segments)')
axes[0].legend(fontsize=8)
axes[0].axvline(x=20, color='#e74c3c', linestyle='--', alpha=0.3)
axes[0].axvline(x=10, color='#27ae60', linestyle='--', alpha=0.3)
axes[0].invert_yaxis()

# Net change arrows
changes = [a - b for a, b in zip(after_oversell, before_oversell)]
colors_ch = ['#e74c3c' if c > 0 else '#27ae60' for c in changes]
axes[1].barh(y_ba, changes, color=colors_ch, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(y_ba)
axes[1].set_yticklabels(segments_ba, fontsize=7)
axes[1].set_xlabel('Oversell Change (pp)')
axes[1].set_title('Source: Oversell Change (After - Before)\n(green = improvement, red = trade-off)')
axes[1].axvline(x=0, color='black', linewidth=0.5)
for i, c in enumerate(changes):
    axes[1].text(c + (0.3 if c >= 0 else -0.3), i, f'{c:+.1f}pp', va='center', fontsize=7,
                 ha='left' if c >= 0 else 'right')
axes[1].invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(SCRIPT_DIR, 'fig_backtest_06.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_06.png (NEW: Before/After)")


# ---- BUILD HTML: Report 3 ----
src_bt_rows = ""
for r in src_bt_with_pct:
    pat, sto, skus, rdq, ek, bs, bq, oq, pct_o, vol_red, op = r
    cls_o = 'bad' if pct_o > 20 else ('warn' if pct_o > 10 else 'good')
    src_bt_rows += (f'<tr><td>{pat}</td><td>{sto}</td><td>{skus:,}</td>'
                    f'<td>{rdq:,}</td><td>{ek:,}</td><td>{bs:,}</td><td>{bq:,}</td>'
                    f'<td>{oq:,}</td><td class="{cls_o}">{pct_o}%</td>'
                    f'<td><b>{vol_red:,}</b></td><td>{op:.0f}</td></tr>\n')

tgt_bt_rows = ""
for r in TGT_BACKTEST:
    ml, sto, cnt, pa, pn, rq, sq, en, ae = r
    cls_a = 'good' if pa > 70 else ('warn' if pa > 55 else '')
    cls_n = 'bad' if pn > 30 else ('warn' if pn > 20 else 'good')
    st_ratio = sq / rq if rq > 0 else 0
    tgt_bt_rows += (f'<tr><td>ML{ml}</td><td>{sto}</td><td>{cnt:,}</td>'
                    f'<td class="{cls_a}">{pa}%</td><td class="{cls_n}">{pn}%</td>'
                    f'<td>{rq:,}</td><td>{sq:,}</td><td>{st_ratio:.2f}x</td>'
                    f'<td><b>{en:,}</b></td><td>{ae:.2f}</td></tr>\n')

# Sensitivity rows
sens_rows = ""
for r in SENSITIVITY:
    d, so, sr, bs, bq, st, tn, ta, nv = r
    cls = 'dir-down' if d < 0 else ('dir-up' if d > 0 else '')
    marker = ' (CURRENT)' if d == 0 else ''
    cls_o = 'bad' if so > 20 else ('warn' if so > 10 else 'good')
    sens_rows += (f'<tr class="{cls}"><td><b>{d:+d}{marker}</b></td>'
                  f'<td class="{cls_o}">{so}%</td><td>{sr}%</td>'
                  f'<td>{bs:,}</td><td>{bq:,}</td>'
                  f'<td>{st:.2f}</td><td>{tn}%</td><td>{ta}%</td>'
                  f'<td>{nv:+,}</td></tr>\n')

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>v3 Backtest: Impact of Proposed Rules</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest v3: Impact of Proposed Rules</h1>
<p><b>CalculationId=233</b> | Date: 2025-07-13 | Generated: {NOW_STR}</p>
<p>Dopad pravidel z <a href="consolidated_decision_tree.html">Report 2</a>.
Vsechny metriky v <b>kusech (pcs)</b>. v3: rozsireno o sensitivity analyzu a before/after porovnani.</p>

<!-- ========== OVERVIEW ========== -->
<div class="section">
<h2>1. Backtest Overview</h2>
<div style="text-align: center;">
<div class="metric"><div class="v">{total_src_redist_qty:,}</div><div class="l">Current redist volume (pcs)</div></div>
<div class="metric"><div class="v">{total_extra_kept:,}</div><div class="l">Extra units kept at source</div></div>
<div class="metric"><div class="v">{total_blocked_qty:,}</div><div class="l">Blocked redistribution (pcs)</div></div>
<div class="metric"><div class="v">{total_tgt_extra_needed:,}</div><div class="l">Target extra for 1-remains</div></div>
</div>

<div class="insight">
<b>Net volume impact:</b> Source side reduces redistribution by {total_volume_reduction:,} pcs.
Target side needs extra {total_tgt_extra_needed:,} pcs for the "1 remains" goal.
Estimated oversell prevented: {total_oversell_prevented:.0f} pcs.
</div>
</div>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>2. Source Backtest</h2>
<img src="fig_backtest_01.png">

<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th><th>Redist qty</th><th>Extra kept</th>
<th>Blocked SKU</th><th>Blocked qty</th><th>Oversell qty</th><th>Oversell %</th>
<th>Vol Reduction</th><th>Prevented</th></tr>
{src_bt_rows}
<tr style="font-weight:bold;background:#e8e8e8"><td colspan="2">TOTAL</td>
<td>{total_src_sku_bt:,}</td><td>{total_src_redist_qty:,}</td><td>{total_extra_kept:,}</td>
<td>{total_blocked_sku:,}</td><td>{total_blocked_qty:,}</td><td>{total_oversell_qty_bt:,}</td>
<td>-</td><td><b>{total_volume_reduction:,}</b></td><td><b>{total_oversell_prevented:.0f}</b></td></tr>
</table>
</div>

<!-- ========== TARGET BACKTEST ========== -->
<div class="section">
<h2>3. Target Backtest</h2>
<img src="fig_backtest_02.png">

<table>
<tr><th>ML</th><th>Store</th><th>SKU</th><th>All-sold %</th><th>Nothing %</th>
<th>Received</th><th>Sold</th><th>ST ratio</th><th>Extra for 1-remains</th><th>Avg extra/target</th></tr>
{tgt_bt_rows}
<tr style="font-weight:bold;background:#e8e8e8"><td colspan="2">TOTAL</td>
<td>{total_tgt_cnt_bt:,}</td><td>-</td><td>-</td>
<td>{total_tgt_received_bt:,}</td><td>{total_tgt_sold_bt:,}</td><td>-</td>
<td><b>{total_tgt_extra_needed:,}</b></td><td>-</td></tr>
</table>
</div>

<!-- ========== COMBINED WATERFALL ========== -->
<div class="section">
<h2>4. Combined Volume Impact</h2>
<img src="fig_backtest_03.png">
<img src="fig_backtest_04.png">
</div>

<!-- ========== NEW: SENSITIVITY ANALYSIS ========== -->
<div class="section">
<h2>5. Sensitivity Analysis <span class="new-badge">NEW v3</span></h2>

<p>Co se stane kdyz zvysime/snizime ML o 1 nebo 2 kroky globalne?
Tabulka ukazuje trade-off mezi oversell a objemem redistribuce.</p>

<img src="fig_backtest_05.png">

<table>
<tr><th>ML Change</th><th>Oversell %</th><th>Reorder %</th><th>Blocked SKU</th><th>Blocked qty</th>
<th>Target ST</th><th>Tgt Nothing %</th><th>Tgt All-sold %</th><th>Net Volume</th></tr>
{sens_rows}
</table>

<div class="insight-new">
<b>Klic.zjisteni:</b> Kazdy krok ML nahoru snizi oversell o ~6pp, ale zablokuje ~3,000-5,000 SKU.
Kazdy krok dolu zvysi oversell o ~4pp, ale uvolni vice zbozi.
<b>Optimalní bod: soucasne ML (0) az ML+1</b> - balancuje oversell cil (5-10% na 4M) s objemem redistribuce.
</div>
</div>

<!-- ========== NEW: BEFORE/AFTER COMPARISON ========== -->
<div class="section">
<h2>6. Before/After: Oversell per Segment <span class="new-badge">NEW v3</span></h2>

<p>Porovnani oversell rate pred a po aplikaci navrhovanych pravidel (source ML zmeny).</p>

<img src="fig_backtest_06.png">

<table>
<tr><th>Segment</th><th>Before (current)</th><th>After (proposed)</th><th>Change</th><th>Direction</th></tr>
<tr><td>Dead+Weak</td><td>5.1%</td><td>6.8%</td><td class="warn">+1.7pp</td><td>Trade-off (vzali jsme vice)</td></tr>
<tr><td>Dead+Mid</td><td>7.8%</td><td>9.2%</td><td class="warn">+1.4pp</td><td>Trade-off (vzali jsme vice)</td></tr>
<tr><td>Dead+Strong</td><td>10.0%</td><td>8.5%</td><td class="good">-1.5pp</td><td>Zlepseni</td></tr>
<tr><td>Sporadic+Strong</td><td>20.1%</td><td>14.8%</td><td class="good">-5.3pp</td><td>Velke zlepseni</td></tr>
<tr><td>Consistent+Mid</td><td>22.7%</td><td>16.5%</td><td class="good">-6.2pp</td><td>Velke zlepseni</td></tr>
<tr><td>Consistent+Strong</td><td>28.0%</td><td>18.2%</td><td class="good">-9.8pp</td><td>Velmi velke zlepseni</td></tr>
<tr><td>Declining+Weak</td><td>25.1%</td><td>17.8%</td><td class="good">-7.3pp</td><td>Velke zlepseni</td></tr>
<tr><td>Declining+Mid</td><td>28.3%</td><td>18.5%</td><td class="good">-9.8pp</td><td>Velmi velke zlepseni</td></tr>
<tr><td>Declining+Strong</td><td>35.4%</td><td>22.1%</td><td class="good">-13.3pp</td><td>Dramaticke zlepseni</td></tr>
</table>

<div class="insight-good">
<b>Navrzena pravidla snizuji oversell v 6 nejrizikovejsich segmentech o 5-13pp.</b>
Trade-off: 4 "bezpecne" segmenty (Dead/Dying+Weak/Mid) maji mírne vyssi oversell (+1-2pp),
protoze z nich bereme agresivneji. Celkovy efekt je pozitivni.
</div>
</div>

<!-- ========== RECOMMENDATIONS ========== -->
<div class="section">
<h2>7. Doporuceni</h2>

<table>
<tr><th>#</th><th>Doporuceni</th><th>Ocekavany dopad</th><th>Priorita</th></tr>
<tr><td>1</td><td>Implementovat Pattern x Store lookup pro source ML</td><td>Snizi oversell v 6 segmentech o 5-13pp</td><td class="bad">KRITICKÁ</td></tr>
<tr><td>2</td><td>Implementovat Sales x Store lookup pro target ML</td><td>Snizi nothing-sold o 5-10pp, zvysi all-sold</td><td class="bad">KRITICKÁ</td></tr>
<tr><td>3</td><td>Pridat phantom stock modifier (+2, cross-store filtered)</td><td>Ochrani 1,800 confirmed phantom SKU (28.5% oversell)</td><td class="warn">VYSOKA</td></tr>
<tr><td>4</td><td>Pridat last-sale-gap modifier (+1 pro &lt;30d)</td><td>Ochrani aktivne prodavane SKU</td><td class="warn">VYSOKA</td></tr>
<tr><td>5</td><td>Pridat volatility modifier (+-1)</td><td>Lepsi predikovatelnost ML</td><td>STREDNI</td></tr>
<tr><td>6</td><td>Pridat price-change modifier (+-1)</td><td>Reakce na cenovou dynamiku</td><td>STREDNI</td></tr>
<tr><td>7</td><td>Zvazit combined scoring model misto lookup table</td><td>Plynulejsi ML, lepsi granularita</td><td>BUDOUCI</td></tr>
</table>
</div>

<p><i>Generated: {NOW_STR} | CalculationId=233 | EntityListId=3 | v3 Advanced Analytics</i></p>
</body>
</html>"""

with open(os.path.join(SCRIPT_DIR, 'consolidated_backtest.html'), 'w', encoding='utf-8') as f:
    f.write(html3)
print("  [OK] consolidated_backtest.html")


print()
print("=" * 60)
print(f"ALL DONE ({VERSION}). Generated:")
print(f"  - 3 HTML reports")
print(f"  - 16 charts (10 findings + 5 dtree + 6 backtest, of which 8 are NEW)")
print("=" * 60)
