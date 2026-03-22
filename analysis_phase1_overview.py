"""
Phase 1 Overview Analysis: Source Reorder/Oversell & Target NotSold rates
by MinLayer3 values for CalculationId=233.

Outputs:
- reports/phase1_overview.html  (full HTML report with charts)
- reports/phase1_source_by_minlayer.png
- reports/phase1_target_by_minlayer.png
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

# ============================================================
# DATA: Source metrics by MinLayer3
# ============================================================
source_data = pd.DataFrame({
    'MinLayer3': [0, 1, 2, 3],
    'SKU_count': [1709, 31965, 2680, 416],
    'has_reorder': [107, 12137, 1402, 195],
    'has_reorder_4m': [57, 6275, 686, 69],
    'pct_reorder': [6.3, 38.0, 52.3, 46.9],
    'pct_reorder_4m': [3.3, 19.6, 25.6, 16.6],
    'has_oversell': [39, 4008, 596, 75],
    'has_oversell_4m': [19, 1147, 137, 14],
    'pct_oversell': [2.3, 12.5, 22.2, 18.0],
    'pct_oversell_4m': [1.1, 3.6, 5.1, 3.4],
    'total_reorder_qty': [121, 13978, 2052, 464],
    'total_oversell_qty': [43, 4564, 812, 159],
    'total_redistributed': [2061, 40598, 4716, 1379]
})
source_data['pct_no_reorder'] = 100 - source_data['pct_reorder']
source_data['pct_no_oversell'] = 100 - source_data['pct_oversell']

# ============================================================
# DATA: Target metrics by MinLayer3
# ============================================================
target_data = pd.DataFrame({
    'MinLayer3': [1, 2, 3],
    'SKU_count': [4730, 31977, 4924],
    'nothing_sold_total': [1829, 6835, 208],
    'nothing_sold_4m': [2840, 13995, 717],
    'all_sold_total': [2834, 18112, 3916],
    'all_sold_4m': [1846, 9234, 2551],
    'pct_nothing_sold': [38.7, 21.4, 4.2],
    'pct_all_sold': [59.9, 56.6, 79.5],
    'pct_all_sold_4m': [39.0, 28.9, 51.8],
    'total_received': [4883, 35238, 8633],
    'total_sales_post': [4682, 65404, 29183],
    'total_remaining': [2328, 20195, 1745]
})
target_data['pct_partial_sold'] = 100 - target_data['pct_nothing_sold'] - target_data['pct_all_sold']

# ============================================================
# CHART 1: Source - Reorder & Oversell rates by MinLayer3
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Reorder rates
x = source_data['MinLayer3']
width = 0.35
bars1 = axes[0].bar(x - width/2, source_data['pct_reorder'], width, label='Reorder (total)', color='#e74c3c', alpha=0.8)
bars2 = axes[0].bar(x + width/2, source_data['pct_reorder_4m'], width, label='Reorder (4M)', color='#e74c3c', alpha=0.4)
axes[0].set_xlabel('Source MinLayer3')
axes[0].set_ylabel('% SKU with Reorder')
axes[0].set_title('SOURCE: Reorder Rate by MinLayer3')
axes[0].legend()
axes[0].set_xticks(x)
for bar in bars1:
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)

# Right: Oversell rates
bars3 = axes[1].bar(x - width/2, source_data['pct_oversell'], width, label='Oversell (total)', color='#8e44ad', alpha=0.8)
bars4 = axes[1].bar(x + width/2, source_data['pct_oversell_4m'], width, label='Oversell (4M)', color='#8e44ad', alpha=0.4)
axes[1].set_xlabel('Source MinLayer3')
axes[1].set_ylabel('% SKU with Oversell')
axes[1].set_title('SOURCE: Oversell Rate by MinLayer3')
axes[1].legend()
axes[1].set_xticks(x)
for bar in bars3:
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in bars4:
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)

# Add SKU counts as secondary info
for ax, data in [(axes[0], source_data), (axes[1], source_data)]:
    for i, row in data.iterrows():
        ax.text(row['MinLayer3'], -3, f'n={row["SKU_count"]:,}', ha='center', fontsize=8, color='gray')

plt.tight_layout()
fig.savefig('reports/phase1_source_by_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# CHART 2: Target - Sold/NotSold breakdown by MinLayer3
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Stacked bar - nothing sold / partial / all sold
x = np.arange(len(target_data))
width = 0.5
axes[0].bar(x, target_data['pct_nothing_sold'], width, label='Nothing sold', color='#e74c3c', alpha=0.8)
axes[0].bar(x, target_data['pct_partial_sold'], width, bottom=target_data['pct_nothing_sold'], label='Partially sold', color='#f39c12', alpha=0.8)
axes[0].bar(x, target_data['pct_all_sold'], width, bottom=target_data['pct_nothing_sold'] + target_data['pct_partial_sold'], label='All sold (problem!)', color='#27ae60', alpha=0.8)
axes[0].set_xlabel('Target MinLayer3')
axes[0].set_ylabel('% of Target SKUs')
axes[0].set_title('TARGET: Sales Outcome by MinLayer3 (total period)')
axes[0].legend(loc='upper left')
axes[0].set_xticks(x)
axes[0].set_xticklabels(target_data['MinLayer3'])
# Add counts
for i, row in target_data.iterrows():
    axes[0].text(x[i], -5, f'n={row["SKU_count"]:,}', ha='center', fontsize=8, color='gray')

# Right: All sold rate comparison 4M vs total
width = 0.35
bars1 = axes[1].bar(x - width/2, target_data['pct_all_sold'], width, label='All sold (total)', color='#c0392b', alpha=0.8)
bars2 = axes[1].bar(x + width/2, target_data['pct_all_sold_4m'], width, label='All sold (4M)', color='#c0392b', alpha=0.4)
axes[1].set_xlabel('Target MinLayer3')
axes[1].set_ylabel('% Target SKUs where ALL sold')
axes[1].set_title('TARGET: All-Sold Rate (triggers reorder)')
axes[1].legend()
axes[1].set_xticks(x)
axes[1].set_xticklabels(target_data['MinLayer3'])
for bar in bars1:
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
fig.savefig('reports/phase1_target_by_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# HTML REPORT
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Fáze 1: Přehled redistribuce CalculationId=233</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #34495e; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: right; }}
th {{ background: #3498db; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.highlight {{ background: #fff3cd !important; font-weight: bold; }}
.bad {{ color: #e74c3c; font-weight: bold; }}
.good {{ color: #27ae60; font-weight: bold; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
.metric-box {{ display: inline-block; background: white; padding: 15px 25px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
.metric-box .value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
.metric-box .label {{ font-size: 12px; color: #7f8c8d; }}
</style>
</head>
<body>

<h1>Analytika SalesBased MinLayers – CalculationId=233</h1>
<p>Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div style="text-align: center;">
  <div class="metric-box"><div class="value">42,404</div><div class="label">Redistribučních řádků</div></div>
  <div class="metric-box"><div class="value">36,770</div><div class="label">Unikátních Source SKU</div></div>
  <div class="metric-box"><div class="value">41,631</div><div class="label">Unikátních Target SKU</div></div>
  <div class="metric-box"><div class="value">48,754</div><div class="label">Celkem přesunuto ks</div></div>
</div>

<div class="section">
<h2>SOURCE: Reorder &amp; Oversell dle MinLayer3</h2>
<p><b>Reorder</b> = po redistribuci se na source SKU objednalo nové zboží (jakýkoliv inbound).<br>
<b>Oversell</b> = po redistribuci se na source prodalo víc, než zůstalo po odeslání (část redistribuce by se prodala i tak).</p>

<img src="phase1_source_by_minlayer.png" alt="Source reorder/oversell">

<table>
<tr><th>MinLayer3</th><th>SKU</th><th>Reorder %</th><th>Reorder 4M %</th><th>Oversell %</th><th>Oversell 4M %</th><th>Reorder ks</th><th>Oversell ks</th><th>Redistrib. ks</th></tr>
"""

for _, row in source_data.iterrows():
    bad_class = ' class="highlight"' if row['pct_reorder'] > 40 else ''
    html += f"""<tr{bad_class}>
<td>{int(row['MinLayer3'])}</td>
<td>{int(row['SKU_count']):,}</td>
<td class="{'bad' if row['pct_reorder']>30 else ''}">{row['pct_reorder']:.1f}%</td>
<td>{row['pct_reorder_4m']:.1f}%</td>
<td class="{'bad' if row['pct_oversell']>15 else ''}">{row['pct_oversell']:.1f}%</td>
<td>{row['pct_oversell_4m']:.1f}%</td>
<td>{int(row['total_reorder_qty']):,}</td>
<td>{int(row['total_oversell_qty']):,}</td>
<td>{int(row['total_redistributed']):,}</td>
</tr>"""

html += """</table>

<h3>Klíčové zjištění – SOURCE:</h3>
<ul>
<li><span class="bad">MinLayer3=1 má 38% reorder rate</span> – největší skupina (32k SKU). To je obrovský problém.</li>
<li><span class="bad">MinLayer3=2 má 52.3% reorder rate</span> – víc než polovina se musela doobjednat!</li>
<li>MinLayer3=0 má jen 6.3% reorder – tyto SKU se správně identifikovaly jako "bezpečné k odeslání".</li>
<li>Oversell je nižší (2-22%), ale i tak znamená, že redistribuované kusy by se prodaly na source.</li>
<li>MinLayer3=3 má paradoxně nižší reorder (46.9%) než MinLayer3=2 (52.3%) – vyšší vrstva chrání lépe, ale pořád ne dost.</li>
</ul>
</div>

<div class="section">
<h2>TARGET: Výsledek redistribuce na cílové prodejně</h2>
<p><b>All sold</b> = vše se prodalo = zásoba klesla na 0 → prodejna objednala automaticky → redistribuce "zbytečná".<br>
<b>Nothing sold</b> = nic se neprodalo → produkt na cílové prodejně nefunguje.<br>
<b>Cíl:</b> na targetu má zůstat alespoň 1 kus (ne 0!).</p>

<img src="phase1_target_by_minlayer.png" alt="Target sales outcome">

<table>
<tr><th>MinLayer3</th><th>SKU</th><th>Nic neprodáno %</th><th>Vše prodáno %</th><th>Vše prodáno 4M %</th><th>Přijato ks</th><th>Prodáno ks</th><th>Zbývá ks</th></tr>
"""

for _, row in target_data.iterrows():
    html += f"""<tr>
<td>{int(row['MinLayer3'])}</td>
<td>{int(row['SKU_count']):,}</td>
<td class="{'bad' if row['pct_nothing_sold']>30 else ''}">{row['pct_nothing_sold']:.1f}%</td>
<td class="{'bad' if row['pct_all_sold']>60 else ''}">{row['pct_all_sold']:.1f}%</td>
<td>{row['pct_all_sold_4m']:.1f}%</td>
<td>{int(row['total_received']):,}</td>
<td>{int(row['total_sales_post']):,}</td>
<td>{int(row['total_remaining']):,}</td>
</tr>"""

html += """</table>

<h3>Klíčové zjištění – TARGET:</h3>
<ul>
<li><span class="bad">MinLayer3=3: 79.5% all-sold</span> – na silně prodávajících targetech se prodá vše a prodejna objedná znovu. Redistribuce nesplnila cíl "udržet zásobu".</li>
<li><span class="bad">MinLayer3=1: 38.7% nothing-sold</span> – na slabých targetech se neprodá nic → redistribuce sem je zbytečná.</li>
<li>MinLayer3=2 (hlavní skupina 32k SKU): 56.6% all-sold, 21.4% nothing-sold → rozštěpený výsledek.</li>
<li>Celkově se na targetech prodalo 99,269 ks, ale přijato jen 48,754 ks → targety prodávaly i vlastní zásobu.</li>
</ul>
</div>

<div class="section">
<h2>Předběžný závěr</h2>
<p>MinLayer heuristika má systémové problémy:</p>
<ol>
<li><b>Source ochrana je nedostatečná</b> – MinLayer 1-2 nechává na source málo, 38-52% potřebuje reorder.</li>
<li><b>Target přesycení</b> – MinLayer3=3 targety prodají vše příliš rychle (silné prodejny), ale MinLayer3=1 targety neprodají nic (slabé prodejny).</li>
<li><b>Potřeba diferenciace</b> – stejný MinLayer se aplikuje na silné i slabé prodejny, na sporadické i pravidelné prodejce. To je klíčový problém.</li>
</ol>
<p><i>Další fáze: rozpad dle síly prodejen, sezónnosti, brandu, stockoutů a cenových pásem.</i></p>
</div>

</body>
</html>"""

with open('reports/phase1_overview.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("=== Phase 1 Overview Report Generated ===")
print(f"  reports/phase1_overview.html")
print(f"  reports/phase1_source_by_minlayer.png")
print(f"  reports/phase1_target_by_minlayer.png")
