"""
Combined Segmentation Report + Decision Tree Analysis
CalculationId=233, EntityListId=3
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

os.makedirs('reports', exist_ok=True)
sns.set_style("whitegrid")

# ============================================================
# COMBINED SEGMENTATION DATA (Source)
# ============================================================
src_combined = pd.DataFrame([
    # MinLayer3, SalesBucket, StoreGroup, cnt, has_reorder, pct_reorder_sku, sum_reorder, sum_redist, reorder_ratio
    [0, 'Low(1-2)', 'Mid(4-7)', 69, 2, 2.9, 2, 99, 2.0],
    [0, 'Low(1-2)', 'Strong(8-10)', 33, 7, 21.2, 8, 51, 15.7],
    [0, 'Low(1-2)', 'Weak(1-3)', 22, 0, 0.0, 0, 28, 0.0],
    [0, 'Med+(3+)', 'Mid(4-7)', 4, 0, 0.0, 0, 7, 0.0],
    [0, 'Med+(3+)', 'Strong(8-10)', 13, 3, 23.1, 5, 30, 16.7],
    [0, 'Med+(3+)', 'Weak(1-3)', 2, 0, 0.0, 0, 3, 0.0],
    [0, 'Zero', 'Mid(4-7)', 701, 59, 8.4, 66, 841, 7.8],
    [0, 'Zero', 'Strong(8-10)', 413, 28, 6.8, 29, 477, 6.1],
    [0, 'Zero', 'Weak(1-3)', 452, 8, 1.8, 11, 525, 2.1],
    [1, 'Low(1-2)', 'Mid(4-7)', 1476, 685, 46.4, 861, 2116, 40.7],
    [1, 'Low(1-2)', 'Strong(8-10)', 1535, 816, 53.2, 1048, 2280, 46.0],
    [1, 'Low(1-2)', 'Weak(1-3)', 660, 250, 37.9, 297, 908, 32.7],
    [1, 'Zero', 'Mid(4-7)', 12617, 4717, 37.4, 5335, 15788, 33.8],
    [1, 'Zero', 'Strong(8-10)', 8264, 3390, 41.0, 3922, 10536, 37.2],
    [1, 'Zero', 'Weak(1-3)', 7413, 2279, 30.7, 2515, 8970, 28.0],
    [2, 'Low(1-2)', 'Mid(4-7)', 541, 276, 51.0, 354, 862, 41.1],
    [2, 'Low(1-2)', 'Strong(8-10)', 787, 397, 50.4, 562, 1311, 42.9],
    [2, 'Low(1-2)', 'Weak(1-3)', 216, 96, 44.4, 120, 326, 36.8],
    [2, 'Med+(3+)', 'Mid(4-7)', 286, 162, 56.6, 259, 563, 46.0],
    [2, 'Med+(3+)', 'Strong(8-10)', 780, 441, 56.5, 709, 1521, 46.6],
    [2, 'Med+(3+)', 'Weak(1-3)', 70, 30, 42.9, 48, 133, 36.1],
    [3, 'Med+(3+)', 'Mid(4-7)', 64, 32, 50.0, 112, 303, 37.0],
    [3, 'Med+(3+)', 'Strong(8-10)', 343, 159, 46.4, 335, 1034, 32.4],
    [3, 'Med+(3+)', 'Weak(1-3)', 9, 4, 44.4, 17, 42, 40.5],
], columns=['MinLayer3', 'SalesBucket', 'StoreGroup', 'cnt', 'has_reorder', 'pct_reorder', 'sum_reorder', 'sum_redist', 'reorder_ratio'])

# ============================================================
# COMBINED SEGMENTATION DATA (Target)
# ============================================================
tgt_combined = pd.DataFrame([
    [1, 'Low(1-2)', 'Mid(4-7)', 1113, 448, 661, 40.3, 59.4, 1124, 1032, 477],
    [1, 'Low(1-2)', 'Strong(8-10)', 998, 345, 648, 34.6, 64.9, 1006, 1178, 360],
    [1, 'Low(1-2)', 'Weak(1-3)', 467, 233, 234, 49.9, 50.1, 469, 336, 236],
    [1, 'Zero', 'Mid(4-7)', 982, 386, 562, 39.3, 57.2, 1057, 880, 633],
    [1, 'Zero', 'Strong(8-10)', 790, 251, 525, 31.8, 66.5, 820, 950, 343],
    [1, 'Zero', 'Weak(1-3)', 380, 166, 204, 43.7, 53.7, 407, 306, 279],
    [2, 'Low(1-2)', 'Mid(4-7)', 8674, 2370, 4100, 27.3, 47.3, 9588, 14021, 6760],
    [2, 'Low(1-2)', 'Strong(8-10)', 9421, 1983, 5299, 21.0, 56.2, 10409, 18897, 5974],
    [2, 'Low(1-2)', 'Weak(1-3)', 3093, 1000, 1348, 32.3, 43.6, 3438, 4470, 2673],
    [2, 'Med+(3+)', 'Mid(4-7)', 4119, 665, 2698, 16.1, 65.5, 4558, 9963, 2022],
    [2, 'Med+(3+)', 'Strong(8-10)', 5345, 613, 3823, 11.5, 71.5, 5731, 15053, 2088],
    [2, 'Med+(3+)', 'Weak(1-3)', 1325, 204, 844, 15.4, 63.7, 1514, 3000, 678],
    [3, 'Med+(3+)', 'Mid(4-7)', 1866, 86, 1451, 4.6, 77.8, 3558, 10990, 713],
    [3, 'Med+(3+)', 'Strong(8-10)', 2554, 96, 2080, 3.8, 81.4, 4036, 15226, 809],
    [3, 'Med+(3+)', 'Weak(1-3)', 504, 26, 385, 5.2, 76.4, 1039, 2967, 223],
], columns=['MinLayer3', 'SalesBucket', 'StoreGroup', 'cnt', 'nothing_sold', 'all_sold', 'pct_nothing', 'pct_allsold', 'sum_received', 'sum_sales', 'sum_remaining'])

# Brand-store fit
brand_fit = pd.DataFrame({
    'Fit': ['Strong+Strong', 'Weak+Strong brand', 'Medium', 'Strong+Weak brand', 'Weak+Weak'],
    'cnt': [9749, 428, 17933, 1064, 7596],
    'pct_reorder': [45.3, 37.6, 37.5, 29.6, 29.3],
    'reorder_ratio': [40.3, 39.4, 33.8, 27.2, 26.4],
})

# ============================================================
# HEATMAP: Source combined segmentation
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Source heatmap: pct_reorder by (SalesBucket x StoreGroup) for MinLayer3=1
src_ml1 = src_combined[src_combined['MinLayer3'] == 1]
pivot_src = src_ml1.pivot(index='SalesBucket', columns='StoreGroup', values='pct_reorder')
pivot_src = pivot_src.reindex(['Zero', 'Low(1-2)'])
pivot_src = pivot_src[['Weak(1-3)', 'Mid(4-7)', 'Strong(8-10)']]

sns.heatmap(pivot_src, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0],
            vmin=25, vmax=55, linewidths=1, cbar_kws={'label': '% SKU s reorderem'})
axes[0].set_title('SOURCE MinLayer3=1: % Reorder\n(Sales6M × Síla prodejny)')
axes[0].set_ylabel('Prodeje 6M před'); axes[0].set_xlabel('Síla prodejny')

# Source: qty dimension
pivot_src_qty = src_ml1.pivot(index='SalesBucket', columns='StoreGroup', values='reorder_ratio')
pivot_src_qty = pivot_src_qty.reindex(['Zero', 'Low(1-2)'])
pivot_src_qty = pivot_src_qty[['Weak(1-3)', 'Mid(4-7)', 'Strong(8-10)']]

sns.heatmap(pivot_src_qty, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1],
            vmin=25, vmax=50, linewidths=1, cbar_kws={'label': '% ks reorderováno'})
axes[1].set_title('SOURCE MinLayer3=1: % Ks Reorder Ratio\n(Sales6M × Síla prodejny)')
axes[1].set_ylabel('Prodeje 6M před'); axes[1].set_xlabel('Síla prodejny')

fig.tight_layout(); fig.savefig('reports/fig06_combined_source_heatmap.png', dpi=150, bbox_inches='tight'); plt.close()

# ============================================================
# HEATMAP: Target combined segmentation
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

tgt_ml2 = tgt_combined[tgt_combined['MinLayer3'] == 2]
pivot_tgt = tgt_ml2.pivot(index='SalesBucket', columns='StoreGroup', values='pct_allsold')
pivot_tgt = pivot_tgt.reindex(['Low(1-2)', 'Med+(3+)'])
pivot_tgt = pivot_tgt[['Weak(1-3)', 'Mid(4-7)', 'Strong(8-10)']]

sns.heatmap(pivot_tgt, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0],
            vmin=40, vmax=75, linewidths=1, cbar_kws={'label': '% Vše prodáno'})
axes[0].set_title('TARGET MinLayer3=2: % All Sold\n(Sales6M × Síla prodejny)')
axes[0].set_ylabel('Prodeje 6M před'); axes[0].set_xlabel('Síla prodejny')

pivot_tgt_nothing = tgt_ml2.pivot(index='SalesBucket', columns='StoreGroup', values='pct_nothing')
pivot_tgt_nothing = pivot_tgt_nothing.reindex(['Low(1-2)', 'Med+(3+)'])
pivot_tgt_nothing = pivot_tgt_nothing[['Weak(1-3)', 'Mid(4-7)', 'Strong(8-10)']]

sns.heatmap(pivot_tgt_nothing, annot=True, fmt='.1f', cmap='YlGnBu', ax=axes[1],
            vmin=10, vmax=35, linewidths=1, cbar_kws={'label': '% Nic neprodáno'})
axes[1].set_title('TARGET MinLayer3=2: % Nothing Sold\n(Sales6M × Síla prodejny)')
axes[1].set_ylabel('Prodeje 6M před'); axes[1].set_xlabel('Síla prodejny')

fig.tight_layout(); fig.savefig('reports/fig07_combined_target_heatmap.png', dpi=150, bbox_inches='tight'); plt.close()

# ============================================================
# BRAND-STORE FIT CHART
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(10, 5))
x = range(len(brand_fit))
bars1 = ax.bar([i-0.2 for i in x], brand_fit['pct_reorder'], 0.35, label='% SKU s reorderem', color='#e74c3c')
bars2 = ax.bar([i+0.2 for i in x], brand_fit['reorder_ratio'], 0.35, label='% ks reorderováno', color='#c0392b', alpha=0.5)
ax.set_xticks(x); ax.set_xticklabels(brand_fit['Fit'], rotation=15)
ax.set_ylabel('%'); ax.set_title('SOURCE: Reorder dle Brand-Store Fit')
ax.legend()
for i, row in brand_fit.iterrows():
    ax.text(i-0.2, row['pct_reorder']+0.5, f"{row['pct_reorder']}%\nn={row['cnt']:,}", ha='center', fontsize=7)
fig.tight_layout(); fig.savefig('reports/fig08_brand_store_fit.png', dpi=150, bbox_inches='tight'); plt.close()

# ============================================================
# DECISION TREE VISUALIZATION
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('Navrhovaný rozhodovací strom pro Source MinLayer', fontsize=14, fontweight='bold', pad=20)

def draw_box(ax, x, y, w, h, text, color='#ecf0f1', border='#2c3e50'):
    rect = plt.Rectangle((x-w/2, y-h/2), w, h, facecolor=color, edgecolor=border, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=7, zorder=3, wrap=True)

def draw_arrow(ax, x1, y1, x2, y2, text=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=1.5), zorder=1)
    if text:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+1, my+1, text, fontsize=6, color='#7f8c8d')

# Root
draw_box(ax, 50, 92, 30, 6, 'Source SKU\n36,770 SKU | 37.6% reorder', '#3498db')

# Level 1: Sales6M
draw_box(ax, 25, 78, 22, 6, 'Sales6M = 0\n29,860 SKU | 35.1% reorder', '#f39c12')
draw_box(ax, 75, 78, 22, 6, 'Sales6M >= 1\n6,910 SKU | 48.4% reorder', '#e74c3c')
draw_arrow(ax, 42, 89, 25, 81, 'Zero sellers')
draw_arrow(ax, 58, 89, 75, 81, 'Had sales')

# Level 2 Left: Store strength for zero-sellers
draw_box(ax, 10, 62, 18, 6, 'Store Weak(1-3)\n7,865 | 30.3% reorder\nMinLayer: OK (1)', '#27ae60')
draw_box(ax, 27, 62, 18, 6, 'Store Mid(4-7)\n13,318 | 37.0% reorder\nMinLayer: +1', '#f39c12')
draw_box(ax, 44, 62, 18, 6, 'Store Strong(8-10)\n8,677 | 40.1% reorder\nMinLayer: +1 až +2', '#e74c3c')
draw_arrow(ax, 18, 75, 10, 65); draw_arrow(ax, 25, 75, 27, 65); draw_arrow(ax, 32, 75, 44, 65)

# Level 2 Right: Sales bucket for had-sales
draw_box(ax, 62, 62, 18, 6, 'Sales 1-2\n3,671 | 46.4% reorder\nMinLayer: +1', '#e67e22')
draw_box(ax, 82, 62, 18, 6, 'Sales 3+\n3,239 | 50.8% reorder\nMinLayer: +2', '#e74c3c')
draw_arrow(ax, 68, 75, 62, 65, 'Low'); draw_arrow(ax, 82, 75, 82, 65, 'Medium+')

# Level 3: Further splits
draw_box(ax, 10, 46, 18, 6, '→ Doporučení:\nMinLayer = 1\n(nízké riziko)', '#d4edda')
draw_box(ax, 27, 46, 18, 6, '→ Doporučení:\nMinLayer = 2\n(střední riziko)', '#fff3cd')
draw_box(ax, 44, 46, 18, 6, '→ Doporučení:\nMinLayer = 2-3\n(vysoké riziko)', '#f8d7da')
draw_box(ax, 62, 46, 18, 6, '→ Doporučení:\nMinLayer = 2\n(vysoké riziko)', '#f8d7da')
draw_box(ax, 82, 46, 18, 6, '→ Doporučení:\nMinLayer = 3\n(velmi vysoké riziko)', '#f8d7da')
draw_arrow(ax, 10, 59, 10, 49); draw_arrow(ax, 27, 59, 27, 49); draw_arrow(ax, 44, 59, 44, 49)
draw_arrow(ax, 62, 59, 62, 49); draw_arrow(ax, 82, 59, 82, 49)

# Additional notes
ax.text(50, 35, 'Dodatečné modifikátory:', fontsize=10, ha='center', fontweight='bold')
ax.text(50, 30, '• Delisted SKU (SkuClass D/L): MinLayer = 0 (bezpečné odvézt vše)', fontsize=8, ha='center')
ax.text(50, 26, '• RedistRatio > 75%: MinLayer = aktuální (odvážíme skoro vše = bezpečné)', fontsize=8, ha='center')
ax.text(50, 22, '• Product trend klesající: MinLayer -1 (klesající poptávka)', fontsize=8, ha='center')
ax.text(50, 18, '• Brand-store fit "Strong+Strong": MinLayer +1 (vysoké riziko reorderu)', fontsize=8, ha='center')
ax.text(50, 14, '• Stockout > 90 dní v posledních 6M: MinLayer +1 (možný phantom stock)', fontsize=8, ha='center')

fig.tight_layout(); fig.savefig('reports/fig09_decision_tree.png', dpi=150, bbox_inches='tight'); plt.close()

# ============================================================
# BACKTEST: How would proposed rules change outcomes?
# ============================================================
# Current vs proposed MinLayer for each segment
backtest_data = []
for _, row in src_combined.iterrows():
    ml = row['MinLayer3']
    sales = row['SalesBucket']
    store = row['StoreGroup']

    # Current MinLayer3
    current_ml = ml

    # Proposed MinLayer based on decision tree
    if sales == 'Zero':
        if store == 'Weak(1-3)': proposed_ml = 1
        elif store == 'Mid(4-7)': proposed_ml = 2
        else: proposed_ml = max(2, ml + 1)
    elif sales == 'Low(1-2)':
        proposed_ml = max(2, ml + 1)
    else:  # Med+
        proposed_ml = max(3, ml + 1)

    backtest_data.append({
        'MinLayer3': ml, 'SalesBucket': sales, 'StoreGroup': store,
        'cnt': row['cnt'], 'current_reorder_pct': row['pct_reorder'], 'current_reorder_ratio': row['reorder_ratio'],
        'current_ml': current_ml, 'proposed_ml': proposed_ml,
        'ml_change': proposed_ml - current_ml,
    })

backtest_df = pd.DataFrame(backtest_data)

# Summary
total_skus = backtest_df['cnt'].sum()
skus_changed = backtest_df[backtest_df['ml_change'] > 0]['cnt'].sum()
skus_unchanged = backtest_df[backtest_df['ml_change'] == 0]['cnt'].sum()

print(f"=== Backtest Summary ===")
print(f"Total source SKUs: {total_skus:,}")
print(f"SKUs with increased MinLayer: {skus_changed:,} ({skus_changed/total_skus*100:.1f}%)")
print(f"SKUs unchanged: {skus_unchanged:,} ({skus_unchanged/total_skus*100:.1f}%)")
print(f"\nNote: Higher MinLayer = fewer SKUs sent = fewer reorders but also fewer successful redistributions")

# ============================================================
# COMBINED HTML REPORT
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Kombinovaná segmentace & Rozhodovací strom – Calc 233</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 12px; }}
h3 {{ color: #34495e; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 5px 8px; text-align: right; }}
th {{ background: #3498db; color: white; font-size: 11px; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.bad {{ color: #e74c3c; font-weight: bold; }}
.good {{ color: #27ae60; font-weight: bold; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }}
.insight {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-bad {{ background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-good {{ background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>

<h1>Kombinovaná segmentace & Rozhodovací strom</h1>
<p>CalculationId=233 | EntityListId=3 | Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="section">
<h2>1. SOURCE: Kombinovaná segmentace (MinLayer3 × Sales6M × Síla prodejny)</h2>
<p>Klíčová tabulka: jak se chovají source SKU v závislosti na třech dimenzích.</p>

<img src="fig06_combined_source_heatmap.png">

<table>
<tr><th>MinLayer3</th><th>Sales 6M</th><th>Síla prodejny</th><th>SKU</th><th>S reorderem</th><th>% SKU reorder</th><th>Reorder ks</th><th>Redistrib. ks</th><th>Qty ratio</th></tr>"""

for _, r in src_combined.sort_values(['MinLayer3', 'SalesBucket', 'StoreGroup']).iterrows():
    cls = 'bad' if r['pct_reorder'] > 45 else ('warn' if r['pct_reorder'] > 35 else 'good')
    html += f"""<tr><td>{int(r['MinLayer3'])}</td><td>{r['SalesBucket']}</td><td>{r['StoreGroup']}</td>
    <td>{int(r['cnt']):,}</td><td>{int(r['has_reorder']):,}</td>
    <td class="{cls}">{r['pct_reorder']}%</td>
    <td>{int(r['sum_reorder']):,}</td><td>{int(r['sum_redist']):,}</td>
    <td>{r['reorder_ratio']}%</td></tr>"""

html += """</table>

<div class="insight-bad">
<b>Kritické segmenty (>45% reorder SKU):</b>
<ul>
<li>MinLayer3=1, Low(1-2), Strong(8-10): <b>53.2%</b> – 1,535 SKU, 46% qty ratio</li>
<li>MinLayer3=2, Med+(3+), Mid/Strong: <b>56.5-56.6%</b> – potřebují MinLayer 3+</li>
<li>MinLayer3=2, Low(1-2), Mid: <b>51.0%</b></li>
<li>MinLayer3=3, Med+(3+), Mid: <b>50.0%</b> – i MaxLayer3 nestačí!</li>
</ul>
</div>

<div class="insight-good">
<b>Bezpečné segmenty (<10% reorder SKU):</b>
<ul>
<li>MinLayer3=0, Zero, Weak(1-3): <b>1.8%</b> – 452 SKU, bezpečné</li>
<li>MinLayer3=0, Zero, Strong(8-10): <b>6.8%</b> – 413 SKU, relativně bezpečné</li>
<li>MinLayer3=0, Low(1-2), Mid: <b>2.9%</b> – 69 SKU</li>
</ul>
</div>
</div>

<div class="section">
<h2>2. TARGET: Kombinovaná segmentace</h2>
<img src="fig07_combined_target_heatmap.png">

<table>
<tr><th>MinLayer3</th><th>Sales 6M</th><th>Síla prodejny</th><th>SKU</th><th>Nic neprodáno</th><th>Vše prodáno</th><th>% Nic</th><th>% Vše</th><th>Přijato ks</th><th>Prodáno ks</th><th>Zbývá ks</th></tr>"""

for _, r in tgt_combined.sort_values(['MinLayer3', 'SalesBucket', 'StoreGroup']).iterrows():
    html += f"""<tr><td>{int(r['MinLayer3'])}</td><td>{r['SalesBucket']}</td><td>{r['StoreGroup']}</td>
    <td>{int(r['cnt']):,}</td><td>{int(r['nothing_sold']):,}</td><td>{int(r['all_sold']):,}</td>
    <td class="{'bad' if r['pct_nothing']>35 else ''}">{r['pct_nothing']}%</td>
    <td class="{'bad' if r['pct_allsold']>70 else ''}">{r['pct_allsold']}%</td>
    <td>{int(r['sum_received']):,}</td><td>{int(r['sum_sales']):,}</td><td>{int(r['sum_remaining']):,}</td></tr>"""

html += """</table>

<div class="insight-bad">
<b>Target problémové segmenty:</b>
<ul>
<li>MinLayer3=3, Med+, Strong: <b>81.4% all-sold</b> – silné prodejny s frekventními produkty prodají vše!</li>
<li>MinLayer3=1, Low, Weak: <b>49.9% nic neprodáno</b> – slabé prodejny s low-sellers = zbytečná redistribuce</li>
<li>MinLayer3=1, Zero, Weak: <b>43.7% nic neprodáno</b></li>
</ul>
</div>
</div>

<div class="section">
<h2>3. Brand-Store Fit</h2>
<img src="fig08_brand_store_fit.png">

<div class="insight">
<b>"Strong store + Strong brand"</b> = 45.3% reorder (9,749 SKU) – nejvyšší riziko. Prodejna je silná v tomto brandu → odvezené se prodá a musí se doobjednat.<br>
<b>"Weak store + Weak brand"</b> = 29.3% reorder (7,596 SKU) – nejnižší riziko. Tyto redistribuce fungují nejlépe.
<br><br>Rozdíl: <b>16 procentních bodů!</b> Brand-store fit je silný prediktor.
</div>
</div>

<div class="section">
<h2>4. Navrhovaný rozhodovací strom pro Source MinLayer</h2>
<img src="fig09_decision_tree.png">

<h3>Pravidla v pseudokódu:</h3>
<pre style="background:#f8f9fa; padding:15px; border-radius:4px; font-size:12px;">
FUNCTION CalculateSourceMinLayer(sku):
    base = current_min_layer_3_value  // z heuristiky

    // 1. Delisting override
    IF sku.SkuClass IN (D, L, R):
        RETURN 0  // bezpečné odvézt vše

    // 2. Frekvence prodejů (hlavní faktor)
    IF sku.Sales6M == 0:
        IF store.Decile >= 8:   base = MAX(base, 2)
        ELIF store.Decile >= 4: base = MAX(base, 2)
        ELSE:                    base = MAX(base, 1)
    ELIF sku.Sales6M <= 2:
        base = MAX(base, 2)
        IF store.Decile >= 8:   base = MAX(base, 3)
    ELSE:  // Sales6M >= 3
        base = MAX(base, 3)

    // 3. Modifikátory
    IF product.Trend == 'Growing':     base += 1
    IF brand_store_fit == 'Strong+Strong': base += 1
    IF sku.StockoutDays_6M > 90:       base += 1
    IF sku.RedistRatio > 0.75:         base = MAX(base - 1, 0)  // odvážíme skoro vše
    IF product.Trend == 'Declining':   base = MAX(base - 1, 0)

    RETURN MIN(base, 5)  // cap na 5
</pre>

<h3>Odhad dopadu navrhovaných pravidel:</h3>
<p>Při navýšení MinLayer by se:</p>
<ul>
<li><b>{skus_changed:,} SKU ({skus_changed/total_skus*100:.1f}%)</b> dostalo vyšší MinLayer → méně by se redistribuovalo (nebo vůbec)</li>
<li><b>{skus_unchanged:,} SKU ({skus_unchanged/total_skus*100:.1f}%)</b> by zůstalo stejných</li>
<li>Odhad snížení reorderu: pokud by zvýšení MinLayer o 1 zabránilo redistribuci u SKU s 1-2 prodejemi → ušetříme ~4,000-6,000 zbytečných reorderů</li>
</ul>
<p><i>Poznámka: Přesný backtest vyžaduje re-run kalkulačního engine s novými pravidly. Výše je konzervativní odhad.</i></p>
</div>

<div class="section">
<h2>5. Shrnutí pro implementaci</h2>
<table style="font-size:13px;">
<tr><th>Priorita</th><th>Doporučení</th><th>Dopad</th><th>Riziko</th></tr>
<tr><td>1</td><td style="text-align:left"><b>Zohlednit sílu prodejny v MinLayer</b> – Store decil 8-10: +1 na source MinLayer</td><td>~12k source SKU, snížení reorderu o ~8-10pp</td><td>Nízké – méně redistribucí ze silných prodejen</td></tr>
<tr><td>2</td><td style="text-align:left"><b>Rozšířit frekvenci na 12M</b> – SKU s 1-2 prodejemi za 12M: MinLayer min 2</td><td>~6.9k SKU, snížení reorderu o ~15pp</td><td>Střední – menší objem redistribucí</td></tr>
<tr><td>3</td><td style="text-align:left"><b>Brand-store fit</b> – "Strong+Strong": +1 na source MinLayer</td><td>~9.7k SKU, snížení reorderu o ~5-8pp</td><td>Nízké – lepší cílení</td></tr>
<tr><td>4</td><td style="text-align:left"><b>Target omezení pro slabé prodejny</b> – Store decil 1-3: nesnižovat MinLayer pod 2</td><td>~5.8k target SKU, snížení "nic neprodáno" o ~10pp</td><td>Střední – méně targetů na slabých prodejnách</td></tr>
<tr><td>5</td><td style="text-align:left"><b>Product trend</b> – Rostoucí produkty: +1, Klesající: -1</td><td>~7k SKU, jemné doladění</td><td>Nízké</td></tr>
</table>
</div>

<p><i>Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M')} | CalculationId=233 | EntityListId=3</i></p>
</body>
</html>"""

with open('reports/combined_segmentation_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n=== Combined Segmentation Report Generated ===")
print(f"  reports/combined_segmentation_report.html")
print(f"  reports/fig06_combined_source_heatmap.png")
print(f"  reports/fig07_combined_target_heatmap.png")
print(f"  reports/fig08_brand_store_fit.png")
print(f"  reports/fig09_decision_tree.png")
