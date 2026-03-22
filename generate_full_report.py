"""
Full Analysis Report Generator: SalesBased MinLayers - CalculationId=233
Generates comprehensive HTML report with all findings from all phases.
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
# ALL DATA FROM SQL QUERIES
# ============================================================

# --- SOURCE by MinLayer3 (SKU + QTY dimension) ---
src_ml = pd.DataFrame({
    'MinLayer3': [0, 1, 2, 3],
    'total_skus': [1709, 31965, 2680, 416],
    'no_reorder': [1602, 19828, 1278, 221],
    'reorder_0_25pct': [2, 53, 27, 6],
    'reorder_25_50pct': [11, 1101, 133, 27],
    'reorder_50_75pct': [1, 114, 39, 8],
    'reorder_75_100pct': [93, 10869, 1203, 154],
    'sum_reorder_qty': [121, 13978, 2052, 464],
    'sum_redist_qty': [2061, 40598, 4716, 1379],
    'pct_reorder_sku': [6.3, 38.0, 52.3, 46.9],
    'reorder_ratio_pct': [5.9, 34.4, 43.5, 33.6],
    'pct_oversell_sku': [2.3, 12.5, 22.2, 18.0],
})

# --- TARGET by MinLayer3 ---
tgt_ml = pd.DataFrame({
    'MinLayer3': [1, 2, 3],
    'total_skus': [4730, 31977, 4924],
    'nothing_sold': [1829, 6835, 208],
    'all_sold': [2834, 18112, 3916],
    'pct_nothing_sold': [38.7, 21.4, 4.2],
    'pct_all_sold': [59.9, 56.6, 79.5],
    'total_received': [4883, 35238, 8633],
    'total_sales_post': [4682, 65404, 29183],
    'total_remaining': [2328, 20195, 1745],
})

# --- Store decile SOURCE ---
src_decile = pd.DataFrame({
    'Decile': list(range(1, 11)),
    'skus': [1751, 3445, 3648, 3600, 3835, 4155, 4168, 4157, 3971, 4040],
    'pct_reorder': [26.0, 30.7, 31.6, 34.2, 37.2, 38.8, 39.9, 41.4, 43.7, 44.1],
    'pct_oversell': [6.6, 7.1, 9.1, 9.1, 11.0, 12.7, 14.5, 15.6, 17.6, 19.6],
})

# --- Store decile TARGET ---
tgt_decile = pd.DataFrame({
    'Decile': list(range(1, 11)),
    'skus': [954, 2267, 2548, 2830, 3254, 4959, 5711, 6168, 5991, 6949],
    'pct_all_sold': [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1],
    'pct_nothing_sold': [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7],
})

# --- SkuClass change ---
skuclass_src = pd.DataFrame({
    'ClassChange': ['Stayed Active/Z', 'Delisted after', 'Already delisted'],
    'cnt': [30505, 6047, 218],
    'pct_reorder_sku': [42.7, 13.2, 7.3],
    'reorder_ratio_pct': [39.4, 10.9, 6.8],
    'sum_reorder': [15628, 969, 18],
    'sum_redist': [39635, 8854, 265],
})
skuclass_tgt = pd.DataFrame({
    'ClassChange': ['Stayed Active/Z', 'Delisted after'],
    'cnt': [34523, 7108],
    'pct_nothing_sold': [20.7, 24.5],
    'pct_all_sold': [59.3, 61.8],
})

# --- Price bands ---
price = pd.DataFrame({
    'PriceBand': ['<15 EUR', '15-30', '30-60', '60+ EUR'],
    'src_skus': [63, 1178, 16728, 18801],
    'src_pct_reorder': [55.6, 36.2, 34.8, 40.2],
    'src_reorder_ratio': [36.5, 28.8, 31.7, 36.7],
    'tgt_skus': [66, 1202, 18247, 22116],
    'tgt_pct_nothing': [1.5, 16.1, 25.1, 18.5],
    'tgt_pct_allsold': [80.3, 64.0, 55.4, 63.0],
})

# --- Product trend ---
trend = pd.DataFrame({
    'TrendBucket': ['Declining (>50%)', 'Slightly declining', 'Stable', 'Slightly growing', 'Growing (>50%)'],
    'products': [416, 2527, 935, 574, 700],
    'src_pct_reorder': [31.3, 39.3, 35.9, 36.4, 39.6],
    'tgt_pct_allsold': [65.2, 58.3, 58.7, 55.3, 62.2],
})

# --- Zero-seller sources (Sales6M_Pre = 0) ---
zero_sellers = pd.DataFrame({
    'PostSales': ['Still no sales', 'Sold 1 pc', 'Sold 2-3 pcs', 'Sold 4+ pcs'],
    'cnt': [16144, 8330, 4466, 920],
    'has_reorder': [859, 5014, 3784, 824],
    'pct_reorder': [5.3, 60.2, 84.7, 89.6],
    'sum_reorder': [928, 5230, 4569, 1151],
    'sum_redist': [19363, 10563, 5849, 1362],
})

# --- Stockout days ---
stockout = pd.DataFrame({
    'StockoutDays': ['0 days', '1-30 days', '31-90 days', '91-150 days', '150+ days'],
    'cnt': [33239, 3034, 393, 97, 7],
    'pct_reorder': [37.3, 39.7, 45.5, 53.6, 42.9],
    'reorder_ratio': [33.6, 38.2, 42.0, 52.5, 50.0],
})

# --- Redistribution ratio ---
redist_ratio = pd.DataFrame({
    'Bucket': ['<=25%', '26-50%', '51-75%', '76-100%'],
    'cnt': [7304, 24490, 3774, 1202],
    'pct_reorder': [35.1, 38.9, 42.8, 10.7],
    'reorder_ratio': [32.8, 36.8, 31.4, 11.4],
    'pct_oversell': [8.1, 13.6, 19.2, 5.4],
})

# --- Reorder timing ---
reorder_timing = pd.DataFrame({
    'Timing': ['First 4M', 'Xmas (Nov-Dec)', '2026+', 'No reorder'],
    'cnt': [7160, 2569, 4112, 22929],
    'sum_reorder_qty': [8856, 3122, 4637, 0],
    'sum_redist_qty': [9766, 3516, 5533, 29939],
})

# --- Inbound types ---
inbound_types = pd.DataFrame({
    'Type': ['PURCHASE', 'STORE TRANSFER', 'Y-STORE TRANSFER', 'INVENTORY_CHECK', 'ADJUSTMENT'],
    'distinct_skus': [11055, 3057, 3117, 867, 63],
    'total_qty': [23413, 4249, 4054, 630, 41],
    'qty_4M': [9568, 247, 1360, 472, 7],
    'qty_after_4M': [13845, 4002, 2694, 158, 34],
})

# ============================================================
# CHARTS
# ============================================================

# Chart 1: Source reorder - SKU% vs QTY% side by side
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
x = src_ml['MinLayer3']
w = 0.35
axes[0].bar(x - w/2, src_ml['pct_reorder_sku'], w, label='% SKU s reorderem', color='#e74c3c')
axes[0].bar(x + w/2, src_ml['reorder_ratio_pct'], w, label='% ks reorderováno', color='#c0392b', alpha=0.5)
axes[0].set_xlabel('Source MinLayer3'); axes[0].set_ylabel('%'); axes[0].set_title('SOURCE: Reorder Rate - SKU vs Množství')
axes[0].legend(); axes[0].set_xticks(x)
for i, row in src_ml.iterrows():
    axes[0].text(row['MinLayer3']-w/2, row['pct_reorder_sku']+0.8, f"{row['pct_reorder_sku']}%", ha='center', fontsize=8)
    axes[0].text(row['MinLayer3']+w/2, row['reorder_ratio_pct']+0.8, f"{row['reorder_ratio_pct']}%", ha='center', fontsize=8)

# Chart 1b: Reorder ratio distribution (stacked)
bottom = np.zeros(4)
colors = ['#27ae60', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
labels = ['Bez reorderu', '≤25% ks', '25-50% ks', '50-75% ks', '75-100% ks']
cols = ['no_reorder', 'reorder_0_25pct', 'reorder_25_50pct', 'reorder_50_75pct', 'reorder_75_100pct']
for col, color, label in zip(cols, colors, labels):
    vals = (src_ml[col] / src_ml['total_skus'] * 100).values
    axes[1].bar(x, vals, 0.6, bottom=bottom, label=label, color=color)
    bottom += vals
axes[1].set_xlabel('Source MinLayer3'); axes[1].set_ylabel('% SKU')
axes[1].set_title('SOURCE: Rozložení míry reorderu'); axes[1].legend(fontsize=7, loc='upper left'); axes[1].set_xticks(x)
fig.tight_layout(); fig.savefig('reports/fig01_source_reorder.png', dpi=150, bbox_inches='tight'); plt.close()

# Chart 2: Store decile vs reorder/oversell
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(src_decile['Decile'], src_decile['pct_reorder'], 'o-', color='#e74c3c', label='Reorder %', linewidth=2)
axes[0].plot(src_decile['Decile'], src_decile['pct_oversell'], 's-', color='#8e44ad', label='Oversell %', linewidth=2)
axes[0].set_xlabel('Decil prodejny (1=slabá, 10=silná)'); axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Reorder/Oversell dle síly prodejny'); axes[0].legend()
axes[0].set_xticks(range(1,11))

axes[1].plot(tgt_decile['Decile'], tgt_decile['pct_all_sold'], 'o-', color='#e74c3c', label='Vše prodáno %', linewidth=2)
axes[1].plot(tgt_decile['Decile'], tgt_decile['pct_nothing_sold'], 's-', color='#3498db', label='Nic neprodáno %', linewidth=2)
axes[1].set_xlabel('Decil prodejny (1=slabá, 10=silná)'); axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Výsledek dle síly prodejny'); axes[1].legend()
axes[1].set_xticks(range(1,11))
fig.tight_layout(); fig.savefig('reports/fig02_store_decile.png', dpi=150, bbox_inches='tight'); plt.close()

# Chart 3: Decile flow heatmap
flow_data = [
    [8,113,67,124,135,218,294,457,299,216],
    [99,183,247,389,327,462,405,395,701,658],
    [110,82,270,266,592,465,472,774,404,707],
    [71,213,247,250,246,498,677,519,686,698],
    [84,143,303,302,269,426,671,630,732,808],
    [113,401,213,408,310,754,693,683,438,762],
    [114,199,290,292,297,642,544,730,713,905],
    [58,226,443,270,436,598,605,720,689,815],
    [161,396,373,319,294,405,496,704,677,765],
    [158,343,144,267,399,581,973,691,750,735],
]
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
flow_df = pd.DataFrame(flow_data, index=range(1,11), columns=range(1,11))
sns.heatmap(flow_df, annot=True, fmt='d', cmap='YlOrRd', ax=ax, linewidths=0.5, cbar_kws={'label': 'Počet SKU párů'})
ax.set_xlabel('Target Decil (1=slabá, 10=silná)'); ax.set_ylabel('Source Decil (1=slabá, 10=silná)')
ax.set_title('Matice přetoku: Source → Target (počet redistribucí)')
fig.tight_layout(); fig.savefig('reports/fig03_decile_flow.png', dpi=150, bbox_inches='tight'); plt.close()

# Chart 4: Zero-sellers fate
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors_zs = ['#27ae60', '#f1c40f', '#e67e22', '#e74c3c']
axes[0].bar(range(4), zero_sellers['cnt'], color=colors_zs)
axes[0].set_xticks(range(4)); axes[0].set_xticklabels(zero_sellers['PostSales'], rotation=15)
axes[0].set_title('SOURCE (Sales6M=0): Co se stalo po redistribuci?')
axes[0].set_ylabel('Počet SKU')
for i, row in zero_sellers.iterrows():
    axes[0].text(i, row['cnt']+200, f"n={row['cnt']:,}", ha='center', fontsize=9)

axes[1].bar(range(4), zero_sellers['pct_reorder'], color=colors_zs)
axes[1].set_xticks(range(4)); axes[1].set_xticklabels(zero_sellers['PostSales'], rotation=15)
axes[1].set_title('SOURCE (Sales6M=0): Reorder rate dle post-prodejů')
axes[1].set_ylabel('% s reorderem')
for i, row in zero_sellers.iterrows():
    axes[1].text(i, row['pct_reorder']+1, f"{row['pct_reorder']}%", ha='center', fontsize=9)
fig.tight_layout(); fig.savefig('reports/fig04_zero_sellers.png', dpi=150, bbox_inches='tight'); plt.close()

# Chart 5: Redistribution ratio impact
fig, ax = plt.subplots(1, 1, figsize=(8, 5))
x_rr = range(4)
ax.bar([i-0.2 for i in x_rr], redist_ratio['pct_reorder'], 0.35, label='% SKU s reorderem', color='#e74c3c')
ax.bar([i+0.2 for i in x_rr], redist_ratio['pct_oversell'], 0.35, label='% SKU s oversellem', color='#8e44ad')
ax.set_xticks(x_rr); ax.set_xticklabels(redist_ratio['Bucket'])
ax.set_xlabel('% zásoby odvezeno'); ax.set_ylabel('%')
ax.set_title('SOURCE: Reorder/Oversell dle poměru redistribuce k zásobě')
ax.legend()
for i, row in redist_ratio.iterrows():
    ax.text(i-0.2, row['pct_reorder']+0.5, f"{row['pct_reorder']}%\nn={row['cnt']:,}", ha='center', fontsize=7)
fig.tight_layout(); fig.savefig('reports/fig05_redist_ratio.png', dpi=150, bbox_inches='tight'); plt.close()

# ============================================================
# HTML REPORT
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Kompletní analytika: SalesBased MinLayers – Calc 233</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 12px; }}
h3 {{ color: #34495e; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 13px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: right; }}
th {{ background: #3498db; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.bad {{ color: #e74c3c; font-weight: bold; }}
.good {{ color: #27ae60; font-weight: bold; }}
.warn {{ color: #e67e22; font-weight: bold; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }}
.metric {{ display: inline-block; background: white; padding: 12px 20px; margin: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; min-width: 140px; }}
.metric .v {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
.metric .l {{ font-size: 11px; color: #7f8c8d; }}
.insight {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-good {{ background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-bad {{ background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>

<h1>Kompletní analytika: SalesBased MinLayers</h1>
<p><b>CalculationId=233</b> | Datum kalkulace: 2025-07-13 | Období: do 2026-03-22 | Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribučních párů</div></div>
<div class="metric"><div class="v">36,770</div><div class="l">Unikátních Source SKU</div></div>
<div class="metric"><div class="v">41,631</div><div class="l">Unikátních Target SKU</div></div>
<div class="metric"><div class="v">48,754 ks</div><div class="l">Celkem přesunuto</div></div>
<div class="metric"><div class="v">37.6%</div><div class="l">Source SKU s reorderem</div></div>
<div class="metric"><div class="v">34.1%</div><div class="l">Reorder qty ratio</div></div>
<div class="metric"><div class="v">59.8%</div><div class="l">Target vše prodáno</div></div>
<div class="metric"><div class="v">21.3%</div><div class="l">Target nic neprodáno</div></div>
</div>

<!-- SECTION 1: SOURCE by MinLayer -->
<div class="section">
<h2>1. SOURCE: Reorder &amp; Oversell dle MinLayer3</h2>
<p>Dvě dimenze: <b>% SKU</b> (kolik SKU mělo jakýkoliv reorder) vs. <b>% kusů</b> (kolik kusů z redistribuovaných se muselo reorderovat).</p>

<img src="fig01_source_reorder.png">

<div class="insight-bad">
<b>Klíčový nález:</b> MinLayer3=2 má 52.3% SKU s reorderem, ale jen 43.5% kusů – reorder je často jen část.
MinLayer3=1 (hlavní skupina 32k SKU): 38% SKU, 34.4% kusů. Absolutně: 14k kusů z 41k se muselo doobjednat.
</div>

<div class="insight">
<b>Rozložení míry reorderu:</b> U MinLayer3=1, z 12k SKU co reorderovaly – 10,869 (89%) reorderovalo 75-100% redistribuovaného množství!
Tzn. když se reorderuje, reorderuje se skoro vše. Reorder je buď "celý" nebo žádný – málo částečných.
</div>

<table>
<tr><th>MinLayer3</th><th>SKU</th><th>Bez reorderu</th><th>Reorder ≤25%</th><th>Reorder 25-50%</th><th>Reorder 50-75%</th><th>Reorder 75-100%</th><th>Reorder ks</th><th>Redistrib. ks</th><th>Qty ratio</th></tr>"""

for _, r in src_ml.iterrows():
    html += f"""<tr><td>{int(r['MinLayer3'])}</td><td>{int(r['total_skus']):,}</td>
    <td class="good">{int(r['no_reorder']):,}</td><td>{int(r['reorder_0_25pct']):,}</td>
    <td>{int(r['reorder_25_50pct']):,}</td><td>{int(r['reorder_50_75pct']):,}</td>
    <td class="bad">{int(r['reorder_75_100pct']):,}</td>
    <td>{int(r['sum_reorder_qty']):,}</td><td>{int(r['sum_redist_qty']):,}</td>
    <td class="{'bad' if r['reorder_ratio_pct']>30 else ''}">{r['reorder_ratio_pct']}%</td></tr>"""

html += """</table>
</div>

<!-- SECTION 2: Store strength -->
<div class="section">
<h2>2. Síla prodejny vs. výsledky redistribuce</h2>
<img src="fig02_store_decile.png">

<div class="insight-bad">
<b>Lineární závislost:</b> Source reorder roste z 26% (slabé prodejny) na 44% (silné).
Silné prodejny prodávají víc → vyšší šance, že se odvezený produkt prodá → reorder. MinLayer musí zohledňovat sílu prodejny.
</div>

<div class="insight-bad">
<b>Target problém:</b> Na silných prodejnách (decil 10) se 70% targetů prodá kompletně → spouštějí automatickou objednávku.
Na slabých (decil 1) se 32% neprodá vůbec. Redistribuce do slabých prodejen je rizikovější z hlediska "zaseknutí" zboží.
</div>

<h3>Matice přetoku: Source → Target (odkud kam posíláme)</h3>
<img src="fig03_decile_flow.png">

<div class="insight">
<b>Zjištění:</b> Redistribuce jde primárně zleva doprava a shora dolů – ze slabších do silnějších.
Nejvíc redistribucí: decily 7-10 source → decily 7-10 target. To znamená přesuny mezi silnými prodejnami, kde je vysoká šance prodeje na obou stranách.
</div>
</div>

<!-- SECTION 3: Zero sellers -->
<div class="section">
<h2>3. Sporadičtí prodejci (Sales6M_Pre = 0)</h2>
<p>29,860 source SKU (81%) nemělo žádný prodej za 6 měsíců před redistribucí.</p>

<img src="fig04_zero_sellers.png">

<div class="insight">
<b>54% (16k) zůstalo bez prodejů i po redistribuci</b> – správně identifikované přebytky.<br>
<b>28% (8.3k) prodalo přesně 1 kus</b> → 60% z nich mělo reorder. Jeden prodej = skoro jistý reorder.<br>
<b>18% (5.4k) prodalo 2+ kusů</b> → 85-90% reorder. Tyto SKU jsou "spící prodejci" a MinLayer je podcenilo.
</div>

<table>
<tr><th>Co se stalo po redistribuci</th><th>SKU</th><th>% ze zero-sellers</th><th>S reorderem</th><th>% s reorderem</th><th>Reorder ks</th><th>Redistrib. ks</th></tr>"""

for _, r in zero_sellers.iterrows():
    pct_of_total = r['cnt'] / 29860 * 100
    html += f"""<tr><td style="text-align:left">{r['PostSales']}</td><td>{int(r['cnt']):,}</td>
    <td>{pct_of_total:.1f}%</td><td>{int(r['has_reorder']):,}</td>
    <td class="{'bad' if r['pct_reorder']>50 else ''}">{r['pct_reorder']}%</td>
    <td>{int(r['sum_reorder']):,}</td><td>{int(r['sum_redist']):,}</td></tr>"""

html += """</table>
</div>

<!-- SECTION 4: Redistribution ratio -->
<div class="section">
<h2>4. Poměr redistribuce k zásobě</h2>
<p>Kolik procent zásoby jsme ze source odvezli?</p>
<img src="fig05_redist_ratio.png">

<div class="insight">
<b>Paradox 76-100%:</b> Když odvezeme skoro vše (76-100%), reorder je jen 10.7%! Proč? Protože to jsou SKU s vysokou zásobou a minimálním prodejem – proto se odveze většina. Naopak 51-75% odvezení má nejvyšší reorder (42.8%) – to jsou SKU kde odvážíme hodně, ale ne vše → zbylá zásoba nestačí.
</div>

<table>
<tr><th>% zásoby odvezeno</th><th>SKU</th><th>% SKU s reorderem</th><th>Reorder qty ratio</th><th>% SKU s oversellem</th></tr>"""

for _, r in redist_ratio.iterrows():
    html += f"""<tr><td>{r['Bucket']}</td><td>{int(r['cnt']):,}</td>
    <td class="{'bad' if r['pct_reorder']>40 else ''}">{r['pct_reorder']}%</td>
    <td>{r['reorder_ratio']}%</td><td>{r['pct_oversell']}%</td></tr>"""

html += """</table>
</div>

<!-- SECTION 5: SkuClass -->
<div class="section">
<h2>5. Vliv změny SkuClass (delisting)</h2>
<p>SkuClass hodnoty: A-O(9)=Active Orderable, Z-O(11)=Z Orderable, D(3)=Delisted Douglas, L(4)=Delisted supplier</p>

<div class="insight-good">
<b>Delisting dramaticky snižuje reorder!</b> Source SKU, která zůstala aktivní: 42.7% reorder (39.4% qty).
Delistovaná po redistribuci: jen 13.2% reorder (10.9% qty). Delisting = výrazně méně problémů.
6,047 source SKU (16.4%) bylo delistováno po redistribuci.
</div>

<table>
<tr><th>Změna SkuClass</th><th>Source SKU</th><th>% SKU reorder</th><th>Qty reorder ratio</th><th>Reorder ks</th><th>Redistrib. ks</th></tr>"""

for _, r in skuclass_src.iterrows():
    html += f"""<tr><td style="text-align:left">{r['ClassChange']}</td><td>{int(r['cnt']):,}</td>
    <td>{r['pct_reorder_sku']}%</td><td>{r['reorder_ratio_pct']}%</td>
    <td>{int(r['sum_reorder']):,}</td><td>{int(r['sum_redist']):,}</td></tr>"""

html += """</table>

<h3>Target – vliv delistingu</h3>
<div class="insight">
Target delistovaná po redistribuci: <b>24.5% nic neprodáno</b> (vs. 20.7% u aktivních). Rozdíl není dramatický – delisting u targetu neznamená automaticky "nic neprodáno".
Ale <b>61.8% all-sold</b> u delistovaných – vyšší než u aktivních (59.3%)! Možné vysvětlení: delistované produkty se vyprodávají (clearance).
</div>
</div>

<!-- SECTION 6: Price bands -->
<div class="section">
<h2>6. Cenová analýza</h2>
<table>
<tr><th>Cenové pásmo</th><th>Source SKU</th><th>Source % reorder</th><th>Source qty ratio</th><th>Target SKU</th><th>Target % nic</th><th>Target % vše</th></tr>"""

for _, r in price.iterrows():
    html += f"""<tr><td>{r['PriceBand']}</td><td>{int(r['src_skus']):,}</td>
    <td>{r['src_pct_reorder']}%</td><td>{r['src_reorder_ratio']}%</td>
    <td>{int(r['tgt_skus']):,}</td><td>{r['tgt_pct_nothing']}%</td><td>{r['tgt_pct_allsold']}%</td></tr>"""

html += """</table>

<div class="insight">
<b>Cenový vliv je mírný.</b> Levné (<15 EUR): 55.6% reorder, ale jen 63 SKU – malý vzorek.
Drahé (60+ EUR): 40.2% reorder vs 30-60 EUR s 34.8%. Drahé produkty mají mírně vyšší reorder.
Target: levné se téměř vždy prodají (80.3% all-sold), drahé méně (63%). U 30-60 EUR je nejvyšší "nic neprodáno" (25.1%).
</div>
</div>

<!-- SECTION 7: Product trends -->
<div class="section">
<h2>7. Trend produktu (cross-product analýza)</h2>
<p>Porovnání prodejů produktu 6M před redistribucí vs. 6M ještě před tím – je produkt na vzestupu nebo sestupu?</p>

<table>
<tr><th>Trend produktu</th><th>Produktů</th><th>Source % reorder</th><th>Target % all-sold</th></tr>"""

for _, r in trend.iterrows():
    html += f"""<tr><td style="text-align:left">{r['TrendBucket']}</td><td>{int(r['products']):,}</td>
    <td>{r['src_pct_reorder']}%</td><td>{r['tgt_pct_allsold']}%</td></tr>"""

html += """</table>

<div class="insight">
<b>Klesající produkty mají nejnižší reorder (31.3%)</b> ale nejvyšší target all-sold (65.2%)!
Paradox: u klesajících produktů odesíláme přebytky (málo reorderu), ale target je prodá (protože dostal zboží co potřeboval).
Rostoucí produkty: 39.6% reorder – odvážíme ze source, ale source potřebuje (roste poptávka).
</div>
</div>

<!-- SECTION 8: Stockout -->
<div class="section">
<h2>8. Stockout analýza</h2>
<table>
<tr><th>Dny ve stockoutu (6M před)</th><th>SKU</th><th>% s reorderem</th><th>Qty reorder ratio</th></tr>"""

for _, r in stockout.iterrows():
    html += f"""<tr><td>{r['StockoutDays']}</td><td>{int(r['cnt']):,}</td>
    <td class="{'bad' if r['pct_reorder']>45 else ''}">{r['pct_reorder']}%</td><td>{r['reorder_ratio']}%</td></tr>"""

html += """</table>

<div class="insight">
<b>Dlouhý stockout → vyšší reorder:</b> 0 dní stockoutu: 37.3% reorder. 91-150 dní: 53.6%.
SKU, která byla delší dobu bez zásoby, mají tendenci k vyššímu reorderu po redistribuci – indikátor phantom stocku nebo sporadického prodejce.
Ale pozor: jen 497 SKU (1.4%) mělo 31+ dní stockoutu – malý vliv na celkové čísla.
</div>
</div>

<!-- SECTION 9: Reorder timing -->
<div class="section">
<h2>9. Časové rozložení reorderů</h2>
<table>
<tr><th>Období reorderu</th><th>SKU</th><th>% ze všech source</th><th>Reorder ks</th><th>Redistrib. ks</th><th>Qty ratio</th></tr>"""

for _, r in reorder_timing.iterrows():
    pct = r['cnt'] / 36770 * 100
    ratio = r['sum_reorder_qty'] / r['sum_redist_qty'] * 100 if r['sum_redist_qty'] > 0 else 0
    html += f"""<tr><td style="text-align:left">{r['Timing']}</td><td>{int(r['cnt']):,}</td>
    <td>{pct:.1f}%</td><td>{int(r['sum_reorder_qty']):,}</td><td>{int(r['sum_redist_qty']):,}</td>
    <td>{ratio:.1f}%</td></tr>"""

html += """</table>

<div class="insight">
<b>62.4% reorderů nemá reorder vůbec</b> (22,929 SKU). To je dobrá zpráva – většina redistribucí funguje.<br>
<b>19.5% (7,160 SKU)</b> reorderuje do 4 měsíců – nejkritičtější skupina. Qty ratio 90.7% – skoro vše se musí doobjednat.<br>
<b>7.0% (2,569)</b> reorderuje v Xmas – sezónní efekt.<br>
<b>11.2% (4,112)</b> reorderuje po novém roce 2026.
</div>
</div>

<!-- SECTION 10: Inbound types -->
<div class="section">
<h2>10. Typy příjmů (inbound) po redistribuci</h2>
<table>
<tr><th>Typ</th><th>SKU</th><th>Celkem ks</th><th>Do 4M ks</th><th>Po 4M ks</th></tr>"""

for _, r in inbound_types.iterrows():
    html += f"""<tr><td style="text-align:left">{r['Type']}</td><td>{int(r['distinct_skus']):,}</td>
    <td>{int(r['total_qty']):,}</td><td>{int(r['qty_4M']):,}</td><td>{int(r['qty_after_4M']):,}</td></tr>"""

html += f"""</table>

<div class="insight">
<b>72.2% reorderů je PURCHASE</b> (23,413 ks) – skutečná objednávka od dodavatele. To je hlavní problém.<br>
<b>Y-STORE TRANSFER (4,054 ks)</b> = další redistribuce Ydistri → zboží se posílá znovu!<br>
<b>STORE TRANSFER (4,249 ks)</b> = interní přesuny Douglas → nezávislé na Ydistri.
</div>
</div>

<!-- SUMMARY -->
<div class="section">
<h2>Souhrnné závěry a doporučení</h2>

<h3>Hlavní problémy MinLayer heuristiky:</h3>
<ol>
<li><b>MinLayer nerespektuje sílu prodejny.</b> Silné prodejny (decil 8-10) mají 41-44% reorder na source a 60-70% all-sold na target. Potřebují vyšší MinLayer na source a cílený nižší příjem na target.</li>

<li><b>"Sporadičtí prodejci" (81% source SKU) tvoří jádro problému.</b> Z 30k zero-sellers: 54% správně odvezeno (bez prodejů), ale 46% mělo alespoň 1 prodej → 60-90% reorder. Jednobitová predikce (prodával/neprodával za 6M) nestačí.</li>

<li><b>Reorder je "all or nothing".</b> 89% reorderů je v pásmu 75-100% redistribuovaného množství. Částečné reordery jsou vzácné. → Pokud se prodá 1 kus, doplní se vše.</li>

<li><b>Target prodá příliš rychle.</b> 60% targetů prodá vše → spouští automatickou objednávku. MinLayer na target musí zajistit, aby zůstal alespoň 1 kus.</li>

<li><b>Delisting pomáhá statistice.</b> 16% source SKU bylo delistováno → jen 13% reorder (vs. 43% u aktivních). Bez delistovaných by source reorder byl ještě horší.</li>
</ol>

<h3>Doporučení pro pravidla MinLayer:</h3>
<ol>
<li><b>Zohlednit sílu prodejny</b> – source MinLayer +1 pro silné prodejny (decil 8+), target MinLayer -1 pro slabé (decil 1-3).</li>
<li><b>Rozšířit frekvenci na 12M</b> – 6M okno je příliš krátké pro sporadické prodejce. Produkt s 2 prodeji za 12M je jiný než s 0.</li>
<li><b>Zohlednit trend produktu</b> – rostoucí produkty potřebují vyšší source MinLayer.</li>
<li><b>Cenové pásmo</b> – levné produkty (<30 EUR) se prodají téměř vždy, drahé (60+) mají vyšší reorder.</li>
<li><b>Brand-store fit</b> – nemáme dosud analyzováno, bude ve fázi 3 rozšířené analýzy.</li>
</ol>

<p><i>Generováno: {datetime.now().strftime('%Y-%m-%d %H:%M')} | CalculationId=233 | EntityListId=3</i></p>
</div>

</body>
</html>"""

with open('reports/full_analysis_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("=== Full Analysis Report Generated ===")
print(f"  reports/full_analysis_report.html")
print(f"  reports/fig01_source_reorder.png")
print(f"  reports/fig02_store_decile.png")
print(f"  reports/fig03_decile_flow.png")
print(f"  reports/fig04_zero_sellers.png")
print(f"  reports/fig05_redist_ratio.png")
