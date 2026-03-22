"""
Decision Tree Analysis for MinLayer Rules
Uses aggregated data from SQL to build rule-based decision trees.
Source and Target rules are SEPARATE - they may differ.
MinLayer range: 0-5.
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
# SOURCE DATA: Sales patterns + stockout + store + reorder outcomes
# Aggregated from SQL queries (no need to connect to DB)
# ============================================================

# Sales Pattern x Store Group -> reorder rates
src_pattern_store = pd.DataFrame([
    ['Consistent', 'Weak', 431, 46.4, 38.4],
    ['Consistent', 'Mid', 1164, 56.0, 45.7],
    ['Consistent', 'Strong', 1693, 56.5, 46.3],
    ['Dead', 'Weak', 4597, 24.5, 22.4],
    ['Dead', 'Mid', 6967, 29.5, 26.9],
    ['Dead', 'Strong', 4061, 31.4, 28.8],
    ['Declining', 'Weak', 219, 55.3, 51.0],
    ['Declining', 'Mid', 569, 64.7, 57.1],
    ['Declining', 'Strong', 751, 68.0, 58.1],
    ['Dying', 'Weak', 1594, 29.7, 26.7],
    ['Dying', 'Mid', 2882, 35.4, 31.7],
    ['Dying', 'Strong', 1951, 37.1, 33.5],
    ['Sporadic/Other', 'Weak', 2003, 37.2, 33.4],
    ['Sporadic/Other', 'Mid', 4176, 44.1, 39.0],
    ['Sporadic/Other', 'Strong', 3712, 47.8, 41.2],
], columns=['Pattern', 'Store', 'cnt', 'pct_reorder_sku', 'reorder_ratio'])

# Last sale gap -> reorder rate
last_sale_gap = pd.DataFrame([
    ['0-30d', 1472, 46.1, 35.2],
    ['31-90d', 2280, 46.9, 39.4],
    ['91-180d', 3116, 51.1, 45.5],
    ['181-365d', 7850, 48.8, 44.0],
    ['365+d', 13864, 44.5, 39.7],
    ['Never', 44958, 31.9, 29.1],  # includes duplicate rows from UNION
], columns=['Gap', 'cnt', 'pct_reorder', 'reorder_ratio'])

# Target data
tgt_data = pd.DataFrame([
    [1, 'Low(1-2)', 'Weak', 467, 49.9, 50.1],
    [1, 'Low(1-2)', 'Mid', 1113, 40.3, 59.4],
    [1, 'Low(1-2)', 'Strong', 998, 34.6, 64.9],
    [1, 'Zero', 'Weak', 380, 43.7, 53.7],
    [1, 'Zero', 'Mid', 982, 39.3, 57.2],
    [1, 'Zero', 'Strong', 790, 31.8, 66.5],
    [2, 'Low(1-2)', 'Weak', 3093, 32.3, 43.6],
    [2, 'Low(1-2)', 'Mid', 8674, 27.3, 47.3],
    [2, 'Low(1-2)', 'Strong', 9421, 21.0, 56.2],
    [2, 'Med+(3+)', 'Weak', 1325, 15.4, 63.7],
    [2, 'Med+(3+)', 'Mid', 4119, 16.1, 65.5],
    [2, 'Med+(3+)', 'Strong', 5345, 11.5, 71.5],
    [3, 'Med+(3+)', 'Weak', 504, 5.2, 76.4],
    [3, 'Med+(3+)', 'Mid', 1866, 4.6, 77.8],
    [3, 'Med+(3+)', 'Strong', 2554, 3.8, 81.4],
], columns=['MinLayer3', 'SalesBucket', 'Store', 'cnt', 'pct_nothing', 'pct_allsold'])

# ============================================================
# SOURCE DECISION TREE: Propose MinLayer 0-5
# ============================================================
# Rules based on data:
# Primary factor: Sales Pattern (2yr history)
# Secondary: Store Strength
# Tertiary: Last sale gap, stockout, brand-store fit

source_rules = pd.DataFrame([
    # Pattern, Store, Current avg ML, Proposed ML, Reasoning
    ['Dead', 'Weak', 0.9, 0, 'Nejnižší reorder (24.5%), produkt mrtvý, slabý obchod'],
    ['Dead', 'Mid', 0.9, 1, 'Nízký reorder (29.5%), ale střední obchod může prodat'],
    ['Dead', 'Strong', 0.9, 1, 'Reorder 31.4% - silný obchod občas prodá mrtvý produkt'],
    ['Dying', 'Weak', 0.9, 0, 'Produkt umírá + slabý obchod = bezpečné odvézt'],
    ['Dying', 'Mid', 0.9, 1, 'Umírající, ale střední obchod = nechej 1'],
    ['Dying', 'Strong', 0.9, 1, 'Umírající + silný obchod = 37% reorder, nechej 1'],
    ['Sporadic/Other', 'Weak', 1.1, 1, 'Nepravidelný, slabý = nechej 1'],
    ['Sporadic/Other', 'Mid', 1.1, 2, 'Nepravidelný, střední = zvýšená ochrana'],
    ['Sporadic/Other', 'Strong', 1.1, 3, 'Nepravidelný, silný = 47.8% reorder! Silná ochrana'],
    ['Declining', 'Weak', 1.1, 2, '55.3% reorder! I slabý obchod reorderuje klesající produkt'],
    ['Declining', 'Mid', 1.1, 3, '64.7% reorder! Vysoká ochrana'],
    ['Declining', 'Strong', 1.1, 4, '68.0% reorder! Maximální ochrana na silných'],
    ['Consistent', 'Weak', 1.7, 2, 'Pravidelný prodejce, slabý obchod'],
    ['Consistent', 'Mid', 1.7, 3, '56% reorder, pravidelný na středním'],
    ['Consistent', 'Strong', 1.7, 4, '56.5% reorder, pravidelný na silném → musí mít hodně'],
], columns=['Pattern', 'Store', 'current_ml', 'proposed_ml', 'reasoning'])

# ============================================================
# TARGET DECISION TREE: Propose MinLayer 0-5
# ============================================================
# Target rules: goal = keep at least 1 unit after sales
# Problem: high all-sold rate (60%+)
# Solution: higher MinLayer = more units sent = more likely to keep 1

target_rules = pd.DataFrame([
    # SalesBucket, Store, Current ML, Proposed ML, Reasoning
    ['Zero', 'Weak', 1, 1, 'Slabý obchod, žádné prodeje → nechej minimum. 43.7% nic neprodáno!'],
    ['Zero', 'Mid', 1, 1, 'Střední, žádné prodeje → 1 kus stačí. 39.3% nic neprodáno'],
    ['Zero', 'Strong', 1, 2, 'Silný obchod i se zero-sellers prodá (66.5% all-sold) → potřeba 2'],
    ['Low(1-2)', 'Weak', 2, 1, 'Slabý + low = 49.9% nic. Snížit na 1!'],
    ['Low(1-2)', 'Mid', 2, 2, 'Střední + low = vyrovnané. OK jako je'],
    ['Low(1-2)', 'Strong', 2, 3, 'Silný + low = 56.2% all-sold → potřeba 3 aby zůstal 1'],
    ['Med+(3+)', 'Weak', 2, 2, 'Slabý + med = funguje dobře. 63.7% all-sold ale ok'],
    ['Med+(3+)', 'Mid', 2, 3, 'Střední + med = 65.5% all-sold → potřeba 3'],
    ['Med+(3+)', 'Strong', 2, 4, 'Silný + med = 71.5% all-sold → potřeba 4 aby zůstal 1!'],
    ['Med+(3+) High', 'Weak', 3, 3, 'MinLayer3=3, slabý = 76.4% all-sold ale OK'],
    ['Med+(3+) High', 'Mid', 3, 4, 'MinLayer3=3, střední = 77.8% all-sold → potřeba 4'],
    ['Med+(3+) High', 'Strong', 3, 5, 'MinLayer3=3, silný = 81.4% all-sold → potřeba 5!'],
], columns=['Segment', 'Store', 'current_ml', 'proposed_ml', 'reasoning'])

# ============================================================
# CHARTS
# ============================================================

# Chart: Sales pattern x store heatmap
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

pivot_sku = src_pattern_store.pivot(index='Pattern', columns='Store', values='pct_reorder_sku')
pivot_sku = pivot_sku[['Weak', 'Mid', 'Strong']]
order = ['Dead', 'Dying', 'Sporadic/Other', 'Consistent', 'Declining']
pivot_sku = pivot_sku.reindex(order)

sns.heatmap(pivot_sku, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0],
            vmin=20, vmax=70, linewidths=1, cbar_kws={'label': '% SKU s reorderem'})
axes[0].set_title('SOURCE: % SKU Reorder\n(Prodejní vzorec × Síla prodejny)')
axes[0].set_ylabel('Prodejní vzorec (24M)'); axes[0].set_xlabel('Síla prodejny')

pivot_qty = src_pattern_store.pivot(index='Pattern', columns='Store', values='reorder_ratio')
pivot_qty = pivot_qty[['Weak', 'Mid', 'Strong']].reindex(order)

sns.heatmap(pivot_qty, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1],
            vmin=20, vmax=60, linewidths=1, cbar_kws={'label': '% ks reorderováno'})
axes[1].set_title('SOURCE: % Ks Reorder Ratio\n(Prodejní vzorec × Síla prodejny)')
axes[1].set_ylabel('Prodejní vzorec (24M)'); axes[1].set_xlabel('Síla prodejny')

fig.tight_layout()
fig.savefig('reports/fig10_sales_pattern_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart: Proposed Source MinLayer matrix
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
pivot_proposed = source_rules.pivot(index='Pattern', columns='Store', values='proposed_ml')
pivot_proposed = pivot_proposed[['Weak', 'Mid', 'Strong']].reindex(order)

sns.heatmap(pivot_proposed, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax,
            vmin=0, vmax=5, linewidths=1, cbar_kws={'label': 'Navrhovaný MinLayer'})
ax.set_title('SOURCE: Navrhovaný MinLayer (0-5)\n(Prodejní vzorec × Síla prodejny)')
ax.set_ylabel('Prodejní vzorec (24M)'); ax.set_xlabel('Síla prodejny')
fig.tight_layout()
fig.savefig('reports/fig11_proposed_source_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart: Proposed Target MinLayer
fig, ax = plt.subplots(1, 1, figsize=(10, 5))
tgt_pivot = pd.DataFrame({
    'Weak': [1, 1, 2, 3],
    'Mid': [1, 2, 3, 4],
    'Strong': [2, 3, 4, 5],
}, index=['Zero sales', 'Low (1-2)', 'Med (3+)', 'High freq (ML3=3)'])

sns.heatmap(tgt_pivot, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax,
            vmin=0, vmax=5, linewidths=1, cbar_kws={'label': 'Navrhovaný MinLayer'})
ax.set_title('TARGET: Navrhovaný MinLayer (0-5)\n(Frekvence prodejů × Síla prodejny)')
ax.set_ylabel('Frekvence prodejů 6M'); ax.set_xlabel('Síla prodejny')
fig.tight_layout()
fig.savefig('reports/fig12_proposed_target_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# Chart: Last sale gap
fig, ax = plt.subplots(1, 1, figsize=(10, 5))
x = range(len(last_sale_gap))
bars1 = ax.bar([i-0.2 for i in x], last_sale_gap['pct_reorder'], 0.35, label='% SKU reorder', color='#e74c3c')
bars2 = ax.bar([i+0.2 for i in x], last_sale_gap['reorder_ratio'], 0.35, label='% ks ratio', color='#c0392b', alpha=0.5)
ax.set_xticks(x); ax.set_xticklabels(last_sale_gap['Gap'])
ax.set_ylabel('%'); ax.set_title('SOURCE: Reorder dle doby od posledního prodeje')
ax.legend()
for i, row in last_sale_gap.iterrows():
    ax.text(i-0.2, row['pct_reorder']+0.5, f"{row['pct_reorder']}%", ha='center', fontsize=7)
fig.tight_layout()
fig.savefig('reports/fig13_last_sale_gap.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# HTML REPORT
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Decision Tree: MinLayer pravidla – Source & Target</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 12px; }}
h3 {{ color: #34495e; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 5px 8px; text-align: right; }}
th {{ background: #3498db; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }}
.insight {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-bad {{ background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-good {{ background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 11px; overflow-x: auto; }}
</style>
</head>
<body>

<h1>Decision Tree: MinLayer pravidla (0-5)</h1>
<p>CalculationId=233 | Source a Target pravidla jsou <b>ODLIŠNÁ</b> | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="section">
<h2>1. Prodejní vzorce (24M historie) – klíčový prediktor pro SOURCE</h2>
<p>Klasifikace SKU do 5 vzorců dle prodejů ve 4 půlročních periodách (A=18-24M, B=12-18M, C=6-12M, D=0-6M):</p>

<img src="fig10_sales_pattern_heatmap.png">

<table>
<tr><th>Vzorec</th><th>Popis</th><th>SKU</th><th>% reorder (SKU)</th><th>% reorder (ks)</th><th>Klíčové zjištění</th></tr>
<tr><td style="text-align:left"><b>Dead</b></td><td style="text-align:left">0 prodejů za 24M</td><td>15,625</td><td>28.5%</td><td>26.1%</td><td style="text-align:left">Nejbezpečnější – ale přesto 28%!</td></tr>
<tr><td style="text-align:left"><b>Dying</b></td><td style="text-align:left">Prodeje jen v A/B, pak 0</td><td>6,427</td><td>34.5%</td><td>31.0%</td><td style="text-align:left">Umírající, ale 1/3 se vrátí</td></tr>
<tr><td style="text-align:left"><b>Sporadic</b></td><td style="text-align:left">Nepravidelné prodeje</td><td>9,888</td><td>45.4%</td><td>39.6%</td><td style="text-align:left">Vysoké riziko – náhodné vzorce</td></tr>
<tr><td style="text-align:left"><b>Consistent</b></td><td style="text-align:left">Prodeje v 3-4 periodách</td><td>3,288</td><td>55.5%</td><td>44.5%</td><td style="text-align:left">Pravidelné – NESMÍ se odvézt moc</td></tr>
<tr><td style="text-align:left" class="bad"><b>Declining</b></td><td style="text-align:left">B>C>D klesající</td><td>1,539</td><td class="bad">65.0%</td><td class="bad">56.8%</td><td style="text-align:left"><b>NEJHORŠÍ!</b> Klesající = stále prodává</td></tr>
</table>

<div class="insight-bad">
<b>Klíčový nález: "Declining" vzorec je nejproblematičtější (65% reorder, 57% qty)!</b><br>
Proč? Produkt se stále prodává (klesá, ale ne nulově). MinLayer heuristika založená na 6M frekvenci ho vidí jako "slabý" (prodeje D < C < B),
ale ve skutečnosti se stále prodává. Aktuální průměrný MinLayer3 = 1.1 – drasticky nedostatečný.
</div>

<div class="insight">
<b>"Dead" (0 prodejů za 24M) = 15,625 SKU (43%)</b> – přesto 28.5% reorder. Tyto SKU neměly ŽÁDNÝ prodej 2 roky, ale po redistribuci se 4,455 z nich muselo doobjednat. Důvod: silná prodejna může prodat i mrtvý produkt, nebo jde o phantom stock.
</div>
</div>

<div class="section">
<h2>2. Doba od posledního prodeje</h2>
<img src="fig13_last_sale_gap.png">

<div class="insight">
<b>Paradoxní nález:</b> SKU s posledním prodejem 91-180 dní zpět má NEJVYŠŠÍ reorder (51.1%, 45.5% qty)!
Toto jsou "spící" produkty – nedávno se prodávaly, ale zastavily se. MinLayer je vidí jako slabé, ale pravděpodobnost prodeje je vysoká.
Naopak "Nikdy neprodané" = 31.9% reorder – nejnižší, ale stále třetina.
</div>
</div>

<div class="section">
<h2>3. Navrhovaná pravidla SOURCE MinLayer (0-5)</h2>
<img src="fig11_proposed_source_minlayer.png">

<pre>
FUNCTION SourceMinLayer(sku, store):
    // Klasifikace prodejního vzorce (24M historie)
    pattern = ClassifySalesPattern(sku.SalesA, .B, .C, .D)  // Dead/Dying/Sporadic/Consistent/Declining
    store_tier = ClassifyStore(store.RevenueDecile)          // Weak(1-3)/Mid(4-7)/Strong(8-10)

    // Lookup tabulka (hlavní pravidlo):
    //                  Weak  Mid   Strong
    // Dead              0     1     1
    // Dying             0     1     1
    // Sporadic          1     2     3
    // Consistent        2     3     4
    // Declining         2     3     4

    base = LOOKUP_TABLE[pattern][store_tier]

    // Modifikátory:
    IF sku.SkuClass IN (D, L, R):          base = 0     // Delisted → odvézt vše
    IF sku.RedistRatio > 0.75:             base = MAX(base - 1, 0)  // Odvážíme skoro vše
    IF sku.BrandStoreFit == 'Strong+Strong': base = MIN(base + 1, 5) // Silný brand v silném obchodě
    IF sku.LastSaleGap BETWEEN 91 AND 180d: base = MIN(base + 1, 5) // "Spící" produkt
    IF sku.StockoutDays_6M > 90:           base = MIN(base + 1, 5) // Phantom stock riziko

    RETURN MIN(base, 5)
</pre>

<table>
<tr><th>Vzorec</th><th>Síla prodejny</th><th>Aktuální ML (avg)</th><th>Navrhovaný ML</th><th>SKU</th><th>Zdůvodnění</th></tr>"""

for _, r in source_rules.iterrows():
    diff = r['proposed_ml'] - r['current_ml']
    cls = 'bad' if diff > 1 else ('good' if diff <= 0 else '')
    html += f"""<tr><td style="text-align:left">{r['Pattern']}</td><td>{r['Store']}</td>
    <td>{r['current_ml']:.1f}</td><td class="{cls}">{int(r['proposed_ml'])}</td>
    <td>{src_pattern_store[(src_pattern_store['Pattern']==r['Pattern'])&(src_pattern_store['Store']==r['Store'])]['cnt'].values[0]:,}</td>
    <td style="text-align:left; font-size:11px">{r['reasoning']}</td></tr>"""

html += """</table>
</div>

<div class="section">
<h2>4. Navrhovaná pravidla TARGET MinLayer (0-5)</h2>
<p>Target cíl: po redistribuci zůstane alespoň 1 kus. Vyšší MinLayer = více kusů posíláme = větší šance, že 1 zůstane.</p>

<img src="fig12_proposed_target_minlayer.png">

<pre>
FUNCTION TargetMinLayer(sku, store):
    freq = sku.Sales6M                              // Frekvence prodejů
    store_tier = ClassifyStore(store.RevenueDecile)  // Weak/Mid/Strong

    // Lookup tabulka:
    //                    Weak  Mid   Strong
    // Zero (0)            1     1     2
    // Low (1-2)           1     2     3
    // Medium (3+)         2     3     4
    // High (ML3=3 / 7+)   3     4     5

    base = LOOKUP_TABLE[freq_bucket][store_tier]

    // Modifikátory:
    IF sku.SkuClass IN (D, L, R):    base = 0  // Delisted → neposílat
    IF product.Trend == 'Growing':   base = MIN(base + 1, 5)  // Rostoucí produkt

    RETURN MIN(base, 5)
</pre>

<table>
<tr><th>Segment</th><th>Síla prodejny</th><th>Aktuální ML</th><th>Navrhovaný ML</th><th>SKU</th><th>Zdůvodnění</th></tr>"""

for _, r in target_rules.iterrows():
    diff = r['proposed_ml'] - r['current_ml']
    cls = 'bad' if diff >= 2 else ('good' if diff < 0 else '')
    html += f"""<tr><td style="text-align:left">{r['Segment']}</td><td>{r['Store']}</td>
    <td>{r['current_ml']}</td><td class="{cls}">{r['proposed_ml']}</td>
    <td>-</td><td style="text-align:left; font-size:11px">{r['reasoning']}</td></tr>"""

html += f"""</table>

<div class="insight-good">
<b>Klíčový rozdíl Source vs Target:</b><br>
<b>Source:</b> MinLayer závisí primárně na <b>prodejním vzorci (24M)</b> + síle prodejny. Declining/Consistent = vysoké MinLayer (3-4).<br>
<b>Target:</b> MinLayer závisí primárně na <b>frekvenci prodejů (6M)</b> + síle prodejny. Silné prodejny = vysoké MinLayer (3-5) protože tam se prodá vše rychle.
</div>
</div>

<div class="section">
<h2>5. Kvantifikace dopadu</h2>

<h3>Source: Co by se stalo s navrhovanými pravidly?</h3>
<table>
<tr><th>Segment</th><th>SKU</th><th>Aktuální reorder %</th><th>Navrhovaný ML</th><th>Očekávaný efekt</th></tr>
<tr><td style="text-align:left">Declining + Strong</td><td>751</td><td class="bad">68.0%</td><td>4</td><td style="text-align:left">Tyto SKU by se neredistribuovaly (ML=4 zachová 4ks) → ušetříme ~511 reorderů</td></tr>
<tr><td style="text-align:left">Consistent + Strong</td><td>1,693</td><td class="bad">56.5%</td><td>4</td><td style="text-align:left">ML4 zachová 4ks → méně redistribucí → ušetříme ~956 reorderů</td></tr>
<tr><td style="text-align:left">Sporadic + Strong</td><td>3,712</td><td>47.8%</td><td>3</td><td style="text-align:left">ML3 zachová 3ks → ušetříme ~500-800 reorderů</td></tr>
<tr><td style="text-align:left">Dead + všechny</td><td>15,625</td><td>28.5%</td><td>0-1</td><td style="text-align:left">Beze změny (už je nízký ML). Reorder 28% je nevyhnutelný.</td></tr>
</table>

<h3>Odhad celkového dopadu:</h3>
<div class="insight-good">
<b>Konzervativní odhad:</b> Navrhovaná pravidla by snížila počet source reorderů o <b>~3,000-5,000 SKU</b> (z 13,841 na ~9,000-11,000).<br>
<b>V kusech:</b> snížení reorderu o <b>~4,000-6,000 ks</b> z celkových 16,615 ks reorderovaných.<br>
<b>Trade-off:</b> Méně redistribucí celkem = méně ušetřených přebytků. Ale redistribuce, které proběhnou, budou úspěšnější.
</div>
</div>

<p><i>{datetime.now().strftime('%Y-%m-%d %H:%M')} | CalculationId=233 | EntityListId=3</i></p>
</body>
</html>"""

with open('reports/decision_tree_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("=== Decision Tree Report Generated ===")
print("  reports/decision_tree_report.html")
print("  reports/fig10_sales_pattern_heatmap.png")
print("  reports/fig11_proposed_source_minlayer.png")
print("  reports/fig12_proposed_target_minlayer.png")
print("  reports/fig13_last_sale_gap.png")
