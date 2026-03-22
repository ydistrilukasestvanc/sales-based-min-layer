"""
Extended Analysis Report: 5 new analyses + backtest
1. Redistribuční smyčka (Y-STORE TRANSFER loop)
2. Párová analýza Source↔Target
3. Backtest navrhovaných pravidel
4. Měsíční kadence prodejů
5. Product concentration
+ Ověření trend analýzy
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
# DATA
# ============================================================

# Pair analysis
pairs = pd.DataFrame({
    'Outcome': ['GOOD-ISH\n(src OK, tgt sold all)', 'SRC FAIL\n(src reorder, tgt all)',
                'WASTED\n(src OK, tgt nothing)', 'IDEAL\n(src OK, tgt partial)',
                'SRC FAIL\n(src reorder, tgt partial)', 'DOUBLE FAIL\n(src reorder, tgt nothing)'],
    'pairs': [14896, 10390, 6274, 4923, 3140, 2781],
    'total_qty': [17343, 12270, 6853, 5743, 3576, 2969],
    'color': ['#f39c12', '#e67e22', '#e74c3c', '#27ae60', '#c0392b', '#8e44ad']
})
pairs['pct'] = pairs['pairs'] / pairs['pairs'].sum() * 100

# Monthly cadence
cadence = pd.DataFrame({
    'months': [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
    'cnt': [15384,8022,4506,2635,1667,1146,805,565,465,343,258,206,172,127,116,105,58,62,42,38,21],
    'pct_reorder': [28.5,35.5,39.0,47.8,50.1,55.8,57.3,56.1,57.2,60.6,67.1,68.4,66.9,71.7,72.4,72.4,81.0,77.4,69.0,76.3,85.7],
    'reorder_ratio': [26.1,31.8,34.7,42.2,44.6,47.9,49.9,45.4,46.4,49.8,53.8,54.7,54.4,58.0,57.4,51.0,61.0,50.7,36.1,55.6,45.6],
    'avg_ml': [0.94,0.98,1.08,1.11,1.16,1.21,1.29,1.35,1.35,1.50,1.50,1.54,1.62,1.65,1.80,1.81,1.86,2.0,2.17,2.39,2.52],
})

# Product concentration
concentration = pd.DataFrame({
    'Bucket': ['<=5 stores', '6-20 stores', '21-100 stores', '100+ stores'],
    'products': [133, 581, 1947, 2485],
    'src_skus': [151, 972, 8973, 26667],
    'pct_reorder': [16.6, 17.0, 24.7, 42.9],
    'tgt_skus': [156, 988, 9476, 31004],
    'pct_allsold': [54.5, 44.3, 50.0, 63.2],
})

# Pair outcome by store flow
pair_flow = pd.DataFrame([
    ['Mid→Mid', 7279, 11.9, 7.5, 16.1],
    ['Mid→Strong', 8304, 12.4, 4.4, 12.6],
    ['Mid→Weak', 2391, 12.1, 9.6, 18.8],
    ['Strong→Mid', 5643, 9.7, 9.0, 15.1],
    ['Strong→Strong', 6546, 10.7, 6.0, 12.4],
    ['Strong→Weak', 2302, 8.8, 10.6, 17.9],
    ['Weak→Mid', 4149, 12.8, 6.1, 17.3],
    ['Weak→Strong', 4611, 12.8, 2.8, 13.0],
    ['Weak→Weak', 1179, 13.7, 8.7, 18.8],
], columns=['Flow', 'pairs', 'pct_ideal', 'pct_double_fail', 'pct_wasted'])

# Backtest
backtest = pd.DataFrame({
    'Outcome': ['Beze změny', 'Snížení ML', 'Zvýšení ML\n(méně ks)', 'Zvýšení ML\n(NEPROBĚHNE)'],
    'skus': [18088, 6044, 6876, 5762],
    'had_reorder': [6083, 1691, 2961, 3106],
    'pct_reorder': [33.6, 28.0, 43.1, 53.9],
    'reorder_qty': [7047, 1910, 4340, 3318],
    'redist_qty': [23107, 7430, 11973, 6244],
    'reorder_ratio': [30.5, 25.7, 36.2, 53.1],
})

# Redistribution loop
loop_summary = pd.DataFrame({
    'Metric': ['SKU v redistribuční smyčce', 'Celkem Y-ST inbound ks', 'Průměr dní do smyčky',
               'Z toho MinLayer3=1 Zero-sellers', 'Z toho MinLayer3=1 Low-sellers',
               'Z toho MinLayer3=2+ Med+'],
    'Value': ['3,117 (8.5% ze všech source)', '4,054 ks', '160 dní',
              '2,231 (71.6%)', '430 (13.8%)', '227 (7.3%)']
})

# ============================================================
# CHARTS
# ============================================================

# Fig14: Pair outcome distribution
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
colors = ['#f39c12', '#e67e22', '#e74c3c', '#27ae60', '#c0392b', '#8e44ad']
wedges, texts, autotexts = axes[0].pie(pairs['pairs'], labels=None, autopct='%1.1f%%',
    colors=colors, startangle=90, pctdistance=0.8)
axes[0].set_title('Redistribuční páry: Výsledek (% párů)')
axes[0].legend(pairs['Outcome'], loc='center left', bbox_to_anchor=(-0.3, 0.5), fontsize=8)
for t in autotexts:
    t.set_fontsize(8)

# Stacked bar version
bottom = 0
for _, row in pairs.iterrows():
    axes[1].barh(0, row['pct'], left=bottom, color=row['color'], height=0.5)
    if row['pct'] > 5:
        axes[1].text(bottom + row['pct']/2, 0, f"{row['pct']:.1f}%", ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    bottom += row['pct']
axes[1].set_xlim(0, 100); axes[1].set_yticks([])
axes[1].set_xlabel('% redistribučních párů')
axes[1].set_title('Redistribuční páry: Rozložení výsledků')
labels_short = ['Good-ish', 'Src fail\n(tgt all)', 'Wasted', 'IDEAL', 'Src fail\n(tgt part)', 'Double fail']
handles = [plt.Rectangle((0,0),1,1, facecolor=c) for c in colors]
axes[1].legend(handles, labels_short, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)

fig.tight_layout()
fig.savefig('reports/fig14_pair_outcomes.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig15: Monthly cadence
fig, ax1 = plt.subplots(1, 1, figsize=(14, 6))
x = cadence['months'][:16]
y_sku = cadence['pct_reorder'][:16]
y_qty = cadence['reorder_ratio'][:16]
y_ml = cadence['avg_ml'][:16]
cnt = cadence['cnt'][:16]

ax1.bar(x, cnt, color='#bdc3c7', alpha=0.5, label='Počet SKU (pravá osa)')
ax1.set_ylabel('Počet source SKU', color='gray')
ax1.tick_params(axis='y', labelcolor='gray')

ax2 = ax1.twinx()
ax2.plot(x, y_sku, 'o-', color='#e74c3c', linewidth=2, label='% SKU reorder', markersize=6)
ax2.plot(x, y_qty, 's--', color='#c0392b', linewidth=1.5, alpha=0.6, label='% ks ratio', markersize=4)
ax2.plot(x, [m*20 for m in y_ml[:16]], '^-', color='#3498db', linewidth=1.5, label='Avg MinLayer3 (×20)', markersize=4)
ax2.set_ylabel('% / MinLayer×20')
ax2.set_ylim(0, 100)

ax1.set_xlabel('Počet měsíců s prodejem (z 24M)')
ax1.set_title('Měsíční kadence: Reorder rate roste s počtem aktivních měsíců')
ax1.set_xticks(range(0, 16))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)

# Annotate key points
ax2.annotate('0 měsíců:\n15.4k SKU\n28.5% reorder', xy=(0, 28.5), xytext=(2, 15),
            arrowprops=dict(arrowstyle='->', color='gray'), fontsize=8)
ax2.annotate('10+ měsíců:\n67-86% reorder\nML stále jen 1.5-2.5!', xy=(10, 67.1), xytext=(12, 50),
            arrowprops=dict(arrowstyle='->', color='red'), fontsize=8, color='red')

fig.tight_layout()
fig.savefig('reports/fig15_monthly_cadence.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig16: Product concentration
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
x = range(4)
axes[0].bar(x, concentration['pct_reorder'], color=['#27ae60', '#2ecc71', '#f39c12', '#e74c3c'])
axes[0].set_xticks(x); axes[0].set_xticklabels(concentration['Bucket'], rotation=15)
axes[0].set_ylabel('% SKU s reorderem')
axes[0].set_title('SOURCE: Reorder dle koncentrace produktu')
for i, row in concentration.iterrows():
    axes[0].text(i, row['pct_reorder']+1, f"{row['pct_reorder']}%\n({row['src_skus']:,} SKU)", ha='center', fontsize=8)

axes[1].bar(x, concentration['pct_allsold'], color=['#27ae60', '#2ecc71', '#f39c12', '#e74c3c'])
axes[1].set_xticks(x); axes[1].set_xticklabels(concentration['Bucket'], rotation=15)
axes[1].set_ylabel('% Target all-sold')
axes[1].set_title('TARGET: All-sold dle koncentrace produktu')
for i, row in concentration.iterrows():
    axes[1].text(i, row['pct_allsold']+1, f"{row['pct_allsold']}%\n({row['tgt_skus']:,} SKU)", ha='center', fontsize=8)

fig.tight_layout()
fig.savefig('reports/fig16_product_concentration.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig17: Backtest
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
x = range(4)
colors_bt = ['#95a5a6', '#3498db', '#f39c12', '#e74c3c']
axes[0].bar(x, backtest['skus'], color=colors_bt)
axes[0].set_xticks(x); axes[0].set_xticklabels(backtest['Outcome'], fontsize=8)
axes[0].set_ylabel('Počet SKU'); axes[0].set_title('BACKTEST: Dopad navrhovaných pravidel na Source SKU')
for i, row in backtest.iterrows():
    axes[0].text(i, row['skus']+200, f"{int(row['skus']):,}\n({row['pct_reorder']}% reorder)", ha='center', fontsize=8)

# Show reorder savings
axes[1].bar(['Aktuální\nreordery', 'Ušetřené\n(neproběhne)', 'Ušetřené\n(méně ks)', 'Zbývající\nreordery'],
    [13841, 3106, 800, 13841-3106-800], color=['#e74c3c', '#27ae60', '#2ecc71', '#f39c12'])
axes[1].set_ylabel('Počet SKU s reorderem')
axes[1].set_title('BACKTEST: Odhad úspor (Source reordery)')
axes[1].text(0, 14200, '13,841', ha='center', fontsize=10, fontweight='bold')
axes[1].text(1, 3500, '3,106\nušetřeno', ha='center', fontsize=9, color='green')
axes[1].text(3, 10300, '~9,935\nzbývá', ha='center', fontsize=9)

fig.tight_layout()
fig.savefig('reports/fig17_backtest.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig18: Pair flow heatmap
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, (col, title, cmap) in enumerate([
    ('pct_ideal', '% IDEAL párů', 'Greens'),
    ('pct_double_fail', '% DOUBLE FAIL párů', 'Reds'),
    ('pct_wasted', '% WASTED párů', 'Oranges'),
]):
    data = {}
    for _, row in pair_flow.iterrows():
        src, tgt = row['Flow'].split('→')
        if src not in data: data[src] = {}
        data[src][tgt] = row[col]
    df = pd.DataFrame(data).T
    df = df.reindex(['Weak', 'Mid', 'Strong'])[['Weak', 'Mid', 'Strong']]
    sns.heatmap(df, annot=True, fmt='.1f', cmap=cmap, ax=axes[idx], linewidths=1,
                cbar_kws={'label': '%'}, vmin=0, vmax=max(pair_flow[col])*1.2)
    axes[idx].set_title(title); axes[idx].set_ylabel('Source store'); axes[idx].set_xlabel('Target store')
fig.tight_layout()
fig.savefig('reports/fig18_pair_flow_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# HTML REPORT
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Rozšířená analytika – 5 nových analýz + Backtest</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 40px; border-left: 4px solid #e74c3c; padding-left: 12px; }}
h3 {{ color: #34495e; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 5px 8px; text-align: right; }}
th {{ background: #e74c3c; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }}
.insight {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-bad {{ background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-good {{ background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 11px; overflow-x: auto; }}
.metric {{ display: inline-block; background: white; padding: 12px 20px; margin: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; min-width: 140px; }}
.metric .v {{ font-size: 24px; font-weight: bold; }}
.metric .l {{ font-size: 11px; color: #7f8c8d; }}
</style>
</head>
<body>

<h1>Rozšířená analytika: 5 nových analýz + Backtest</h1>
<p>CalculationId=233 | EntityListId=3 | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<!-- SECTION 1: PAIR ANALYSIS -->
<div class="section">
<h2>1. Párová analýza Source↔Target</h2>
<p>Každý z 42,404 redistribučních párů klasifikován dle výsledku na obou stranách:</p>

<div style="text-align:center;">
<div class="metric"><div class="v" style="color:#27ae60">11.6%</div><div class="l">IDEAL<br>src OK + tgt partial</div></div>
<div class="metric"><div class="v" style="color:#f39c12">35.1%</div><div class="l">GOOD-ISH<br>src OK + tgt all sold</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">14.8%</div><div class="l">WASTED<br>src OK + tgt nothing</div></div>
<div class="metric"><div class="v" style="color:#8e44ad">6.6%</div><div class="l">DOUBLE FAIL<br>src reorder + tgt nothing</div></div>
</div>

<img src="fig14_pair_outcomes.png">

<div class="insight-bad">
<b>Pouze 11.6% párů je IDEÁLNÍCH</b> (source nereorderoval + target prodal částečně = zůstal 1+ ks).
35.1% je "good-ish" (source OK, ale target prodal vše → spustí reorder na targetu).
<b>6.6% je DOUBLE FAIL</b> – source musel reorderovat A zároveň target neprodal nic. To je 2,781 párů = čistá ztráta.
14.8% je WASTED – source nepotřeboval reorder, ale target nic neprodal → zbytečný přesun 6,853 ks.
</div>

<h3>Párové výsledky dle toku Source→Target (síla prodejny)</h3>
<img src="fig18_pair_flow_heatmap.png">

<div class="insight">
<b>Nejvíc IDEAL párů:</b> Weak→Weak (13.7%), Weak→Strong (12.8%), Weak→Mid (12.8%). Přesouvání ze slabých prodejen funguje nejlépe!<br>
<b>Nejvíc DOUBLE FAIL:</b> Strong→Weak (10.6%), Weak→Weak (8.7%), Mid→Weak (9.6%). Posílání na slabé prodejny z jakéhokoliv zdroje má vysoký double-fail.<br>
<b>Nejvíc WASTED:</b> Mid→Weak a Weak→Weak (18.8%). Na slabé prodejny se často neprodá nic.
<br><br>
<b>Závěr:</b> Nejlepší tok je Weak→Strong (2.8% double fail, 13.0% wasted). Nejhorší je *→Weak.
Pravidla pro target by měla omezit posílání na slabé prodejny.
</div>
</div>

<!-- SECTION 2: REDISTRIBUTION LOOP -->
<div class="section">
<h2>2. Redistribuční smyčka (Y-STORE TRANSFER loop)</h2>
<p>3,117 source SKU (8.5%) obdrželo po redistribuci nový Y-STORE TRANSFER inbound = byly redistribuovány ZNOVU.</p>

<div style="text-align:center;">
<div class="metric"><div class="v" style="color:#e74c3c">3,117</div><div class="l">SKU ve smyčce</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">4,054 ks</div><div class="l">Znovu redistribuováno</div></div>
<div class="metric"><div class="v">160 dní</div><div class="l">Průměr dní do smyčky</div></div>
<div class="metric"><div class="v">71.6%</div><div class="l">Z toho ML3=1 Zero-sellers</div></div>
</div>

<div class="insight-bad">
<b>71.6% smyčkových SKU (2,231) jsou zero-sellers s MinLayer3=1.</b>
Tyto SKU neměly žádné prodeje za 6M, byly redistribuovány, a za ~160 dní přišla další redistribuce zpět na ně.
Loop ratio je ~100% – vrátí se prakticky stejné množství, co se odvezlo. To je cyklické přesouvání bez přidané hodnoty.
<br><br>
<b>Doporučení:</b> SKU, které byly v posledních 6-12 měsících redistribuovány, by měly mít zvýšený MinLayer (+2).
Toto by eliminovalo většinu smyček.
</div>
</div>

<!-- SECTION 3: MONTHLY CADENCE -->
<div class="section">
<h2>3. Měsíční kadence prodejů (24M)</h2>
<p>Kolik měsíců z posledních 24 mělo alespoň 1 prodej? Toto je výrazně lepší prediktor než binární 6M frekvence.</p>

<img src="fig15_monthly_cadence.png">

<div class="insight-bad">
<b>Reorder rate roste téměř lineárně s počtem aktivních měsíců:</b><br>
0 měsíců → 28.5% | 3 měsíce → 47.8% | 6 měsíců → 57.3% | 10 měsíců → 67.1% | 16+ měsíců → 81%<br><br>
<b>Ale MinLayer roste mnohem pomaleji!</b> 0 měsíců: ML=0.94 | 10 měsíců: ML=1.50 | 16 měsíců: ML=1.86<br>
SKU s 10+ aktivními měsíci má 67%+ reorder, ale průměrný MinLayer je jen 1.5! To je zásadní nesoulad.<br><br>
<b>Doporučení:</b> Počet aktivních měsíců (z 24M) by měl být PRIMÁRNÍ vstup pro MinLayer kalkulaci.
Navrhovaná tabulka: 0M→ML0, 1-2M→ML1, 3-5M→ML2, 6-9M→ML3, 10-15M→ML4, 16+M→ML5.
</div>
</div>

<!-- SECTION 4: PRODUCT CONCENTRATION -->
<div class="section">
<h2>4. Koncentrace produktu</h2>
<p>Na kolika prodejnách se produkt prodává? Koncentrovaný produkt (málo prodejen) = redistribuce na novou prodejnu rizikovější.</p>

<img src="fig16_product_concentration.png">

<div class="insight">
<b>Masivní rozdíl:</b> Produkty prodávané na <=20 prodejnách: 16.6-17.0% source reorder.<br>
Produkty na 100+ prodejnách: <b>42.9% source reorder</b> – 2.5× víc!<br><br>
Proč? Široce distribuované produkty se prodávají pravidelněji → vyšší šance, že se na source prodá odvezený kus.
Koncentrované produkty se prodávají jen na několika místech → na source se po redistribuci nic nestane.<br><br>
Target: 100+ prodejen = 63.2% all-sold (vs. 44.3% u 6-20 prodejen). Široce distribuované produkty se prodávají všude → i na targetu se prodá vše.
<br><br>
<b>Doporučení:</b> Počet prodejen produktu jako vstup pro MinLayer. Widespread (100+): +1 na source ML, -1 na target ML (nepotřebujeme tam tolik, prodá se i méně).
</div>
</div>

<!-- SECTION 5: BACKTEST -->
<div class="section">
<h2>5. Backtest navrhovaných Source pravidel</h2>
<p>Aplikace navrhovaných pravidel (sales pattern × store strength → MinLayer 0-5) na skutečná data kalkulace 233.</p>

<img src="fig17_backtest.png">

<table>
<tr><th>Dopad</th><th>SKU</th><th>% z celku</th><th>Mělo reorder</th><th>% reorder</th><th>Reorder ks</th><th>Redistrib. ks</th><th>Qty ratio</th></tr>
<tr><td style="text-align:left">Beze změny (ML stejný)</td><td>18,088</td><td>49.2%</td><td>6,083</td><td>33.6%</td><td>7,047</td><td>23,107</td><td>30.5%</td></tr>
<tr><td style="text-align:left">Snížení ML (víc se odveze)</td><td>6,044</td><td>16.4%</td><td>1,691</td><td>28.0%</td><td>1,910</td><td>7,430</td><td>25.7%</td></tr>
<tr><td style="text-align:left">Zvýšení ML (odveze se méně)</td><td>6,876</td><td>18.7%</td><td>2,961</td><td>43.1%</td><td>4,340</td><td>11,973</td><td>36.2%</td></tr>
<tr><td style="text-align:left"><b>Zvýšení ML → NEPROBĚHNE</b></td><td>5,762</td><td>15.7%</td><td class="bad">3,106</td><td class="bad">53.9%</td><td>3,318</td><td>6,244</td><td>53.1%</td></tr>
</table>

<div class="insight-good">
<b>5,762 SKU by se neredistribuovalo</b> (navrhovaný ML >= aktuální zásoba).<br>
Z nich <b>3,106 (53.9%) skutečně mělo reorder</b> → tyto reordery bychom ušetřili!<br>
Ale 2,656 (46.1%) nemělo reorder → tyto redistribuce by se ztratily (false positive).<br><br>
<b>Bilance:</b><br>
- Ušetřeno: 3,106 zbytečných reorderů (SKU) a 3,318 ks reorder množství<br>
- Ztraceno: 2,823 ks úspěšných redistribucí (SKU kde nebylo reorder a redistribuce proběhla)<br>
- <b>Čistý přínos: 3,318 - 2,823 = 495 ks netto úspora</b><br>
- Plus: 6,876 SKU s méně redistribuovanými ks (43.1% reorder) → další úspory<br><br>
<b>Celkový odhad:</b> Snížení reorderu z 13,841 na ~9,000-10,000 SKU (27-35% úspora).
</div>
</div>

<!-- SECTION 6: TREND VERIFICATION -->
<div class="section">
<h2>6. Ověření: Trend analýza používá jen PRE-redistribuční data</h2>
<p>Kontrola, zda vstupní data pro product trend jsou výhradně z období PŘED redistribucí:</p>

<table>
<tr><th>Období</th><th>Datum od</th><th>Datum do</th><th>Status</th></tr>
<tr><td style="text-align:left">Sales_Older (referenční)</td><td>2024-07-13</td><td>2025-01-12</td><td class="good">PRE-redistribuce</td></tr>
<tr><td style="text-align:left">Sales_Recent (srovnávané)</td><td>2025-01-13</td><td>2025-07-12</td><td class="good">PRE-redistribuce</td></tr>
<tr><td style="text-align:left">Redistribuce</td><td colspan="2">2025-07-13</td><td><b>REFERENČNÍ DATUM</b></td></tr>
<tr><td style="text-align:left">Post-redistribuce (výsledky)</td><td>2025-07-13</td><td>2026-03-22</td><td>POST (jen výsledky)</td></tr>
</table>

<div class="insight-good">
<b>POTVRZENO:</b> Trend analýza (Growing/Declining/Stable) je počítána výhradně z dat PŘED redistribucí.
Oba srovnávané periody (Older: 2024-07 až 2025-01, Recent: 2025-01 až 2025-07) končí před referenčním datem.
Výsledky redistribuce (reorder/oversell/not-sold) jsou z POST období a slouží jen k vyhodnocení, ne jako vstup.
Trend je tedy validní prediktor pro decision tree.
</div>
</div>

<p><i>{datetime.now().strftime('%Y-%m-%d %H:%M')} | CalculationId=233 | EntityListId=3</i></p>
</body>
</html>"""

with open('reports/extended_analysis_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("=== Extended Analysis Report Generated ===")
for f in ['fig14_pair_outcomes', 'fig15_monthly_cadence', 'fig16_product_concentration',
          'fig17_backtest', 'fig18_pair_flow_heatmap']:
    print(f"  reports/{f}.png")
print("  reports/extended_analysis_report.html")
