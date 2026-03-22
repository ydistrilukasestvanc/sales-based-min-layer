"""
CALIBRATED Decision Tree: MinLayer rules targeting specific oversell rates.
Target: 4M oversell 5-10%, 9M oversell <20%.
NOT aiming for zero reorder - that would be too defensive.

Key insight: ML0 (1.1%/2.3%) and ML1 (3.6%/12.5%) are ALREADY within target!
Focus corrections ONLY on segments exceeding targets.
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
# ACTUAL OVERSELL RATES by Pattern x Store (sales-based, correct metric)
# ============================================================
oversell_data = pd.DataFrame([
    ['Dead', 'Weak', 4597, 1.1, 5.1],
    ['Dead', 'Mid', 6967, 1.9, 7.8],
    ['Dead', 'Strong', 4061, 3.0, 10.0],
    ['Dying', 'Weak', 1594, 2.6, 8.1],
    ['Dying', 'Mid', 2882, 2.6, 9.7],
    ['Dying', 'Strong', 1951, 3.7, 12.6],
    ['Sporadic', 'Weak', 2003, 2.6, 10.9],
    ['Sporadic', 'Mid', 4176, 4.6, 15.3],
    ['Sporadic', 'Strong', 3712, 5.1, 20.1],
    ['Consistent', 'Weak', 431, 2.1, 13.2],
    ['Consistent', 'Mid', 1164, 7.0, 22.7],
    ['Consistent', 'Strong', 1693, 7.7, 28.0],
    ['Declining', 'Weak', 219, 7.8, 25.1],
    ['Declining', 'Mid', 569, 10.2, 28.3],
    ['Declining', 'Strong', 751, 12.3, 35.4],
], columns=['Pattern', 'Store', 'cnt', 'oversell_4m', 'oversell_total'])

# Mark which segments EXCEED targets
oversell_data['exceeds_4m'] = oversell_data['oversell_4m'] > 10
oversell_data['exceeds_total'] = oversell_data['oversell_total'] > 20
oversell_data['needs_fix'] = oversell_data['exceeds_4m'] | oversell_data['exceeds_total']

# Current avg MinLayer per segment
current_ml = {
    ('Dead','Weak'): 0.9, ('Dead','Mid'): 0.9, ('Dead','Strong'): 0.9,
    ('Dying','Weak'): 0.9, ('Dying','Mid'): 0.9, ('Dying','Strong'): 0.9,
    ('Sporadic','Weak'): 1.1, ('Sporadic','Mid'): 1.1, ('Sporadic','Strong'): 1.1,
    ('Consistent','Weak'): 1.7, ('Consistent','Mid'): 1.7, ('Consistent','Strong'): 1.7,
    ('Declining','Weak'): 1.1, ('Declining','Mid'): 1.1, ('Declining','Strong'): 1.1,
}

# ============================================================
# CALIBRATED PROPOSED MinLayer
# Only increase where needed! Keep current where already in target.
# ============================================================
def proposed_ml(pattern, store, current):
    """Calibrated MinLayer: only increase where oversell exceeds target."""
    # Dead: all within target -> keep as-is (add +1 for A-O/Z-O business rule)
    if pattern == 'Dead':
        return max(1, current)  # business rule min 1 for orderable
    # Dying: all within target -> keep + business rule
    if pattern == 'Dying':
        return max(1, current)
    # Sporadic: Strong barely exceeds total target (20.1%) -> +1 only for Strong
    if pattern == 'Sporadic':
        if store == 'Strong': return max(2, current + 1)  # 20.1% -> needs +1
        return max(1, current)  # Mid/Weak within target
    # Consistent: Mid and Strong exceed total (22.7%, 28.0%) -> need increase
    if pattern == 'Consistent':
        if store == 'Strong': return max(3, current + 1)  # 28.0% -> +1-2
        if store == 'Mid': return max(2, current + 1)      # 22.7% -> +1
        return max(1, current)  # Weak OK (13.2%)
    # Declining: ALL exceed targets! Most problematic.
    if pattern == 'Declining':
        if store == 'Strong': return max(3, current + 2)  # 35.4% + 12.3% -> big increase
        if store == 'Mid': return max(3, current + 1)      # 28.3% + 10.2%
        if store == 'Weak': return max(2, current + 1)     # 25.1% + 7.8%
    return max(1, current)

oversell_data['current_ml'] = oversell_data.apply(lambda r: current_ml.get((r['Pattern'], r['Store']), 1), axis=1)
oversell_data['proposed_ml'] = oversell_data.apply(lambda r: proposed_ml(r['Pattern'], r['Store'], r['current_ml']), axis=1)
oversell_data['ml_change'] = oversell_data['proposed_ml'] - oversell_data['current_ml']

# ============================================================
# CHARTS
# ============================================================

# Fig19: Oversell heatmap with target zones
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
order = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
stores = ['Weak', 'Mid', 'Strong']

pivot_4m = oversell_data.pivot(index='Pattern', columns='Store', values='oversell_4m')
pivot_4m = pivot_4m[stores].reindex(order)
pivot_total = oversell_data.pivot(index='Pattern', columns='Store', values='oversell_total')
pivot_total = pivot_total[stores].reindex(order)

# Custom colormap: green (<5%), yellow (5-10%), orange (10-20%), red (>20%)
sns.heatmap(pivot_4m, annot=True, fmt='.1f', cmap='RdYlGn_r', ax=axes[0],
            vmin=0, vmax=15, linewidths=1, cbar_kws={'label': '% SKU s oversell'})
axes[0].set_title('SOURCE Oversell rate – 4M po redistribúcii\n(Cieľ: 5-10%)')
axes[0].set_ylabel('Predajný vzorec'); axes[0].set_xlabel('Sila predajne')

sns.heatmap(pivot_total, annot=True, fmt='.1f', cmap='RdYlGn_r', ax=axes[1],
            vmin=0, vmax=40, linewidths=1, cbar_kws={'label': '% SKU s oversell'})
axes[1].set_title('SOURCE Oversell rate – celkové (~9M)\n(Cieľ: <20%)')
axes[1].set_ylabel('Predajný vzorec'); axes[1].set_xlabel('Sila predajne')

# Draw target line on total
for i in range(5):
    for j in range(3):
        val = pivot_total.iloc[i, j]
        if val > 20:
            axes[1].text(j+0.5, i+0.85, 'OVER', ha='center', fontsize=7, color='red', fontweight='bold')

fig.tight_layout()
fig.savefig('reports/fig19_oversell_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig20: Current vs Proposed MinLayer
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

pivot_current = oversell_data.pivot(index='Pattern', columns='Store', values='current_ml')
pivot_current = pivot_current[stores].reindex(order)
pivot_proposed = oversell_data.pivot(index='Pattern', columns='Store', values='proposed_ml')
pivot_proposed = pivot_proposed[stores].reindex(order)

sns.heatmap(pivot_current, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0],
            vmin=0, vmax=4, linewidths=1, cbar_kws={'label': 'MinLayer'})
axes[0].set_title('AKTUÁLNY priemerný MinLayer3')
axes[0].set_ylabel('Predajný vzorec'); axes[0].set_xlabel('Sila predajne')

sns.heatmap(pivot_proposed, annot=True, fmt='.0f', cmap='YlOrRd', ax=axes[1],
            vmin=0, vmax=4, linewidths=1, cbar_kws={'label': 'MinLayer'})
axes[1].set_title('NAVRHOVANÝ MinLayer (kalibrovaný na cieľ)')
axes[1].set_ylabel('Predajný vzorec'); axes[1].set_xlabel('Sila predajne')

fig.tight_layout()
fig.savefig('reports/fig20_calibrated_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# Fig21: Which segments need fixing?
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
needs_fix = oversell_data[oversell_data['needs_fix']].sort_values('oversell_total', ascending=True)
ok = oversell_data[~oversell_data['needs_fix']].sort_values('oversell_total', ascending=True)

all_sorted = pd.concat([ok, needs_fix])
colors = ['#27ae60' if not nf else '#e74c3c' for nf in all_sorted['needs_fix']]
labels = [f"{r['Pattern']} / {r['Store']}" for _, r in all_sorted.iterrows()]
y = range(len(all_sorted))

ax.barh(y, all_sorted['oversell_total'], color=colors, height=0.7)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
ax.axvline(x=20, color='red', linestyle='--', linewidth=2, label='Cieľ: <20%')
ax.axvline(x=10, color='orange', linestyle='--', linewidth=1, label='Cieľ 4M: 5-10%')
ax.set_xlabel('% SKU s oversell (celkové ~9M)')
ax.set_title('Segmenty: zelené = v cieli, červené = prekračujú cieľ')
ax.legend()

for i, (_, row) in enumerate(all_sorted.iterrows()):
    ax.text(row['oversell_total'] + 0.3, i, f"{row['oversell_total']}% (n={int(row['cnt']):,})",
            fontsize=7, va='center')

fig.tight_layout()
fig.savefig('reports/fig21_segments_vs_target.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# SUMMARY
# ============================================================
total_skus = oversell_data['cnt'].sum()
skus_in_target = oversell_data[~oversell_data['needs_fix']]['cnt'].sum()
skus_over_target = oversell_data[oversell_data['needs_fix']]['cnt'].sum()
skus_ml_increase = oversell_data[oversell_data['ml_change'] > 0]['cnt'].sum()

print(f"=== CALIBRATED ANALYSIS ===")
print(f"Total source SKU: {total_skus:,}")
print(f"Already in target (<20% total oversell): {skus_in_target:,} ({skus_in_target/total_skus*100:.1f}%)")
print(f"Exceeding target (>20% total oversell): {skus_over_target:,} ({skus_over_target/total_skus*100:.1f}%)")
print(f"SKU that need ML increase: {skus_ml_increase:,} ({skus_ml_increase/total_skus*100:.1f}%)")
print()
print("Segments exceeding target:")
for _, r in oversell_data[oversell_data['needs_fix']].iterrows():
    print(f"  {r['Pattern']:12s} {r['Store']:8s}: 4M={r['oversell_4m']}%, total={r['oversell_total']}% "
          f"(n={int(r['cnt']):,}) ML: {r['current_ml']:.1f} -> {int(r['proposed_ml'])}")
print()
print("Pseudocode for CALIBRATED Source MinLayer:")
print("""
FUNCTION SourceMinLayer(sku, store):
    pattern = ClassifySalesPattern(sku)  // Dead/Dying/Sporadic/Consistent/Declining
    store_tier = ClassifyStore(store)     // Weak(1-3)/Mid(4-7)/Strong(8-10)

    // Business rule: A-O(9), Z-O(11) -> minimum 1
    min_ml = 1 if sku.SkuClass in (9, 11) else 0

    // Base table (CALIBRATED to target 4M: 5-10%, total: <20%)
    //                Weak  Mid   Strong
    // Dead            1     1     1       // all within target, keep min
    // Dying           1     1     1       <- all within target
    // Sporadic        1     1     2       <- Strong barely exceeds (20.1%)
    // Consistent      1     2     3       <- Mid (22.7%), Strong (28.0%) exceed
    // Declining       2     3     3       <- ALL exceed, most problematic

    base = LOOKUP[pattern][store_tier]
    RETURN MAX(base, min_ml)
""")

# Generate report
html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Kalibrované MinLayer pravidlá – Cieľ: 4M 5-10%, 9M &lt;20%</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #27ae60; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 40px; border-left: 4px solid #27ae60; padding-left: 12px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 13px; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: right; }}
th {{ background: #27ae60; color: white; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; }}
.insight {{ background: #fff3cd; border-left: 4px solid #f39c12; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-good {{ background: #d4edda; border-left: 4px solid #27ae60; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
.insight-bad {{ background: #f8d7da; border-left: 4px solid #e74c3c; padding: 10px 15px; margin: 10px 0; border-radius: 4px; }}
pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 12px; }}
.metric {{ display: inline-block; background: white; padding: 12px 20px; margin: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
.metric .v {{ font-size: 24px; font-weight: bold; }}
.metric .l {{ font-size: 11px; color: #7f8c8d; }}
</style>
</head>
<body>

<h1>Kalibrované MinLayer pravidlá</h1>
<p><b>Cieľ: 4M oversell 5-10%, celkový (~9M) oversell &lt;20%</b><br>
Cieľom NIE JE nulový reorder – to by vyžadovalo extrémnu defenzívu. Cieľom je rozumné zníženie.<br>
{GENERATED} | CalculationId=233 | EntityListId=3</p>

<div style="text-align:center;">
<div class="metric"><div class="v" style="color:#27ae60">{skus_in_target/total_skus*100:.0f}%</div><div class="l">SKU už v cieli</div></div>
<div class="metric"><div class="v" style="color:#e74c3c">{skus_over_target/total_skus*100:.0f}%</div><div class="l">SKU nad cieľom</div></div>
<div class="metric"><div class="v">{skus_ml_increase/total_skus*100:.0f}%</div><div class="l">Potrebuje zvýšiť ML</div></div>
</div>

<div class="section">
<h2>1. Aktuálny stav: Oversell rate podľa MinLayer3</h2>
<p>Oversell = koľko z redistribuovaných kusov by sa na source predalo aj tak (sales-based metrika).</p>

<table>
<tr><th>MinLayer3</th><th>SKU</th><th>Oversell 4M</th><th>Cieľ 4M</th><th>Status</th><th>Oversell total</th><th>Cieľ total</th><th>Status</th></tr>
<tr><td>0</td><td>1,709</td><td class="good">1.1%</td><td>5-10%</td><td style="color:green">OK</td><td class="good">2.3%</td><td>&lt;20%</td><td style="color:green">OK</td></tr>
<tr><td>1</td><td>31,965</td><td class="good">3.6%</td><td>5-10%</td><td style="color:green">OK</td><td class="good">12.5%</td><td>&lt;20%</td><td style="color:green">OK</td></tr>
<tr><td>2</td><td>2,680</td><td>5.1%</td><td>5-10%</td><td style="color:orange">Hranica</td><td class="bad">22.2%</td><td>&lt;20%</td><td style="color:red">NAD</td></tr>
<tr><td>3</td><td>416</td><td class="good">3.4%</td><td>5-10%</td><td style="color:green">OK</td><td>18.0%</td><td>&lt;20%</td><td style="color:green">OK</td></tr>
</table>

<div class="insight-good">
<b>Väčšina je UŽ v cieli!</b> MinLayer3=0 a MinLayer3=1 (33,674 SKU = 92%) majú oversell hlboko pod cieľom.
Problém je len MinLayer3=2 s celkovým oversellom 22.2%. Toto sú primárne SKU s vyššou frekvenciou predajov.
MinLayer3=3 je tesne pod cieľom (18.0%).
<br><br>
<b>DÔLEŽITÉ:</b> Oversell (sales-based) je výrazne nižší než reorder (inbound-based):
ML1 oversell=12.5% vs reorder=38.0%. Inbound zahŕňa objednávky, ktoré nesúvisia s redistribúciou.
Skutočný dopad redistribúcie na source je teda MENŠÍ, než sa zdalo z inbound dát.
</div>
</div>

<div class="section">
<h2>2. Oversell podľa predajného vzorca × sila predajne</h2>
<img src="fig19_oversell_heatmap.png">

<div class="insight-bad">
<b>Segmenty PREKRAČUJÚCE cieľ (>20% celkový oversell):</b>
<ul>
<li><b>Declining + Strong:</b> 35.4% total, 12.3% 4M – NAJHORŠIE. 751 SKU, aktuálny ML=1.1</li>
<li><b>Declining + Mid:</b> 28.3% total, 10.2% 4M – 569 SKU</li>
<li><b>Declining + Weak:</b> 25.1% total, 7.8% 4M – 219 SKU</li>
<li><b>Consistent + Strong:</b> 28.0% total, 7.7% 4M – 1,693 SKU</li>
<li><b>Consistent + Mid:</b> 22.7% total, 7.0% 4M – 1,164 SKU</li>
<li><b>Sporadic + Strong:</b> 20.1% total, 5.1% 4M – 3,712 SKU (ledva prekračuje)</li>
</ul>
Spolu: <b>{skus_over_target:,} SKU ({skus_over_target/total_skus*100:.1f}%)</b> – zvyšok je v cieli.
</div>

<div class="insight-good">
<b>Segmenty V CIELI (zelené):</b> Dead (15,625), Dying (6,427), Sporadic Weak+Mid (6,179), Consistent Weak (431).
Tieto segmenty tvoria {skus_in_target:,} SKU ({skus_in_target/total_skus*100:.1f}%) a NEPOTREBUJÚ zmenu.
To je kľúčový záver: <b>väčšinu redistributions netreba meniť!</b>
</div>
</div>

<div class="section">
<h2>3. Kde presne treba zasiahnuť</h2>
<img src="fig21_segments_vs_target.png">

<p>Z 15 segmentov (5 vzorov × 3 sily) len 6 prekračuje cieľ. Náprava je cielená, nie plošná.</p>
</div>

<div class="section">
<h2>4. Kalibrované MinLayer pravidlá</h2>
<img src="fig20_calibrated_minlayer.png">

<pre>
FUNCTION SourceMinLayer(sku, store):
    pattern = ClassifySalesPattern(sku)  // Dead/Dying/Sporadic/Consistent/Declining
    store_tier = ClassifyStore(store)     // Weak(1-3) / Mid(4-7) / Strong(8-10)

    // Business rule: A-O(9), Z-O(11) -> minimum 1
    min_ml = 1 if sku.SkuClass in (A-O, Z-O) else 0

    // KALIBROVANÁ tabuľka (cieľ: 4M 5-10%, total <20%)
    //                Weak  Mid   Strong
    // Dead            1     1     1       <- všetko v cieli, ponechať minimum
    // Dying           1     1     1       <- všetko v cieli
    // Sporadic        1     1     2       <- len Strong mierne prekračuje (20.1%)
    // Consistent      1     2     3       <- Mid (22.7%) a Strong (28.0%) prekračujú
    // Declining       2     3     3       <- VŠETKY prekračujú, najproblematickejšie

    base = LOOKUP[pattern][store_tier]
    RETURN MAX(base, min_ml)
</pre>

<table>
<tr><th>Vzorec</th><th>Predajňa</th><th>SKU</th><th>Aktuálny ML</th><th>Navrhovaný ML</th><th>Zmena</th><th>Oversell 4M</th><th>Oversell total</th><th>Zdôvodnenie</th></tr>"""

for _, r in oversell_data.sort_values(['Pattern', 'Store']).iterrows():
    change = int(r['proposed_ml'] - r['current_ml'])
    change_str = f"+{change}" if change > 0 else str(change) if change < 0 else "="
    change_cls = 'bad' if change > 0 else ('good' if change < 0 else '')
    status = 'NAD' if r['needs_fix'] else 'OK'
    html += f"""<tr><td style="text-align:left">{r['Pattern']}</td><td>{r['Store']}</td><td>{int(r['cnt']):,}</td>
    <td>{r['current_ml']:.1f}</td><td>{int(r['proposed_ml'])}</td><td class="{change_cls}">{change_str}</td>
    <td>{r['oversell_4m']}%</td><td class="{'bad' if r['oversell_total']>20 else ''}">{r['oversell_total']}%</td>
    <td style="text-align:left;font-size:11px">{status}: {'Treba zvýšiť' if r['needs_fix'] else 'V cieli, ponechať'}</td></tr>"""

html += f"""</table>

<div class="insight">
<b>Kľúčový rozdiel oproti predchádzajúcemu návrhu:</b><br>
Predchádzajúci návrh: agresívne zvyšoval ML na 3-4 pre väčšinu segmentov (79.8% SKU by sa zmenilo).<br>
<b>Kalibrovaný návrh: mení len {skus_ml_increase:,} SKU ({skus_ml_increase/total_skus*100:.1f}%)</b> – len tie, ktoré prekračujú cieľ.<br>
Dead a Dying (60% SKU) sú úplne v poriadku a nepotrebujú zmenu. Hlavná zmena je len na Declining a Consistent vzorcoch.
</div>
</div>

<div class="section">
<h2>5. Zhrnutie</h2>

<table style="font-size:14px;">
<tr><th>Metrika</th><th>Aktuálne</th><th>Po kalibrácii (odhad)</th></tr>
<tr><td style="text-align:left">Oversell 4M (celkový priemer)</td><td>3.6%</td><td>~3%</td></tr>
<tr><td style="text-align:left">Oversell total (celkový priemer)</td><td>12.8%</td><td>~10-12%</td></tr>
<tr><td style="text-align:left">Segmenty nad cieľom</td><td>6 z 15</td><td>0-1 z 15</td></tr>
<tr><td style="text-align:left">SKU s upravenými pravidlami</td><td>-</td><td>{skus_ml_increase:,} ({skus_ml_increase/total_skus*100:.1f}%)</td></tr>
<tr><td style="text-align:left">Redistribúcia naďalej funguje pre</td><td>-</td><td>{skus_in_target:,} SKU bez zmeny</td></tr>
</table>

<div class="insight-good">
<b>Redistributions sú prevažne úspešné!</b> 78.6% target párkov predá niečo (úspech).
Source oversell (skutočný problém) je len 12.8% celkovo. Problém je sústredený v 6 segmentoch
(8,108 SKU = 22% source). Kalibrovaná náprava na tieto segmenty zníži celkový oversell
na ~10-12% bez toho, aby sme stratili úspešné redistribúcie v ostatných segmentoch.
</div>
</div>

<p><i>{GENERATED} | CalculationId=233 | EntityListId=3</i></p>
</body>
</html>"""

with open('reports/calibrated_rules_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nReports generated:")
print(f"  reports/calibrated_rules_report.html")
print(f"  reports/fig19_oversell_heatmap.png")
print(f"  reports/fig20_calibrated_minlayer.png")
print(f"  reports/fig21_segments_vs_target.png")
