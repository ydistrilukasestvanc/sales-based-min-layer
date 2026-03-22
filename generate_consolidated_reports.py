"""
Consolidated Reports Generator: SalesBased MinLayers - CalculationId=233
Generates 3 HTML reports with all charts into reports/ directory.
Deletes old individual reports first.
"""
import os
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)
sns.set_style("whitegrid")

# ============================================================
# DELETE OLD INDIVIDUAL REPORTS
# ============================================================
old_reports = [
    'full_analysis_report.html',
    'combined_segmentation_report.html',
    'decision_tree_report.html',
    'extended_analysis_report.html',
    'calibrated_rules_report.html',
]
for fname in old_reports:
    fpath = os.path.join(REPORTS_DIR, fname)
    if os.path.exists(fpath):
        os.remove(fpath)
        print("[DELETED] " + fname)
    else:
        print("[SKIP] " + fname + " (not found)")

print("")
print("=" * 60)
print("Generating consolidated reports...")
print("=" * 60)

# ============================================================
# COMMON CSS
# ============================================================
CSS = """
body { font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }
h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
h2 { color: #2c3e50; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 12px; }
h3 { color: #34495e; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; font-size: 13px; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: right; }
th { background: #3498db; color: white; }
tr:nth-child(even) { background: #f9f9f9; }
td:first-child { text-align: left; }
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


# ############################################################
#
#  REPORT 1: CONSOLIDATED FINDINGS
#
# ############################################################
print("")
print("--- Report 1: Consolidated Findings ---")

# ---- Chart: fig_findings_01.png - Oversell heatmap (Pattern x Store) ----
patterns = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
stores = ['Weak', 'Mid', 'Strong']
oversell_data = [
    [5.1, 7.8, 10.0],
    [8.1, 9.7, 12.6],
    [10.9, 15.3, 20.1],
    [13.2, 22.7, 28.0],
    [25.1, 28.3, 35.4],
]
oversell_arr = np.array(oversell_data)

fig, ax = plt.subplots(1, 1, figsize=(9, 6))
sns.heatmap(oversell_arr, annot=True, fmt='.1f', cmap='YlOrRd',
            xticklabels=stores, yticklabels=patterns, ax=ax,
            vmin=4, vmax=36, linewidths=1,
            cbar_kws={'label': 'Oversell % (9M total)'})
# Draw a rectangle around cells > 20%
for i in range(len(patterns)):
    for j in range(len(stores)):
        if oversell_data[i][j] > 20:
            ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False,
                         edgecolor='#2c3e50', linewidth=3))
ax.set_title('Oversell Rate by Sales Pattern (24M) x Store Strength\n(cells >20% highlighted)', fontsize=12)
ax.set_ylabel('Sales Pattern (24M history)')
ax.set_xlabel('Store Strength')
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

# ---- Chart: fig_findings_03.png - Monthly cadence bar+line ----
months_labels = ['0M', '1M', '3M', '6M', '10M', '16M']
months_skus = [15384, 8022, 2635, 805, 258, 58]
months_reorder = [8.3, 35.5, 47.8, 57.3, 67.1, 81.0]
months_ml = [0.94, 1.00, 1.10, 1.20, 1.50, 1.86]

fig, ax1 = plt.subplots(1, 1, figsize=(10, 6))
color_bar = '#3498db'
color_line = '#e74c3c'
x_pos = np.arange(len(months_labels))

bars = ax1.bar(x_pos - 0.2, months_skus, 0.4, color=color_bar, alpha=0.7, label='SKU count')
ax1.set_xlabel('Months with sales (24M history)')
ax1.set_ylabel('SKU Count', color=color_bar)
ax1.tick_params(axis='y', labelcolor=color_bar)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(months_labels)
for i, (s, r) in enumerate(zip(months_skus, months_reorder)):
    ax1.text(i - 0.2, s + 300, f'{s:,}', ha='center', fontsize=8, color=color_bar)

ax2 = ax1.twinx()
ax2.plot(x_pos, months_reorder, 'o-', color=color_line, linewidth=2.5, markersize=8, label='Reorder/Oversell %')
ax2.set_ylabel('Reorder / Oversell %', color=color_line)
ax2.tick_params(axis='y', labelcolor=color_line)
for i, r in enumerate(months_reorder):
    ax2.text(i + 0.1, r + 1.5, f'{r}%', ha='center', fontsize=9, color=color_line, fontweight='bold')

ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))
ax3.plot(x_pos, months_ml, 's--', color='#8e44ad', linewidth=1.5, markersize=6, label='Avg MinLayer')
ax3.set_ylabel('Avg MinLayer', color='#8e44ad')
ax3.tick_params(axis='y', labelcolor='#8e44ad')
for i, m in enumerate(months_ml):
    ax3.text(i + 0.15, m + 0.03, f'{m}', ha='center', fontsize=8, color='#8e44ad')

ax1.set_title('Monthly Sales Cadence (24M): SKU Count vs Reorder Rate vs MinLayer')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
lines3, labels3 = ax3.get_legend_handles_labels()
ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_03.png")

# ---- Chart: fig_findings_04.png - Pair flow outcomes ----
pair_labels = ['BEST\n(src OK +\ntgt all sold)', 'IDEAL\n(src OK +\ntgt partial)',
               'SRC FAIL\n(tgt sold)', 'WASTED\n(src OK +\ntgt nothing)', 'DOUBLE\nFAIL']
pair_pcts = [35.1, 11.6, 31.9, 14.8, 6.6]
pair_counts = [14896, 4923, 13530, 6274, 2781]
pair_colors = ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pie chart
wedges, texts, autotexts = axes[0].pie(pair_pcts, labels=pair_labels, autopct='%1.1f%%',
                                        colors=pair_colors, startangle=90, textprops={'fontsize': 8})
for t in autotexts:
    t.set_fontsize(9)
    t.set_fontweight('bold')
axes[0].set_title('Pair Outcome Distribution (42,404 pairs)')

# Flow heatmap: direction vs double-fail rate
flow_labels = ['Weak -> Strong', 'Mid -> Strong', 'Strong -> Strong',
               'Weak -> Mid', 'Mid -> Mid', 'Strong -> Mid',
               'Weak -> Weak', 'Mid -> Weak', 'Strong -> Weak']
flow_dfail = [2.8, 3.9, 5.1, 4.2, 5.8, 7.2, 6.1, 8.3, 10.6]
flow_arr = np.array(flow_dfail).reshape(3, 3)
flow_ylabels = ['-> Strong', '-> Mid', '-> Weak']
flow_xlabels = ['Weak src', 'Mid src', 'Strong src']

sns.heatmap(flow_arr, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1],
            xticklabels=flow_xlabels, yticklabels=flow_ylabels,
            vmin=2, vmax=11, linewidths=1,
            cbar_kws={'label': 'Double Fail %'})
axes[1].set_title('Double Fail Rate by Flow Direction\n(Source strength -> Target strength)')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_findings_04.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_findings_04.png")

# ---- BUILD HTML: Report 1 ----
html1 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Konsolidovana analytika: SalesBased MinLayers - Calc 233</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(0)}

<h1>Konsolidovana analytika: SalesBased MinLayers - Calc 233</h1>
<p><b>CalculationId=233</b> | EntityListId=3 | Datum kalkulace: 2025-07-13 | Monitoring: do 2026-03-22 | Generovano: {NOW_STR}</p>

<!-- ========== SECTION 1: OVERVIEW ========== -->
<div class="section">
<h2>1. Prehled</h2>

<div style="text-align: center;">
<div class="metric"><div class="v">42,404</div><div class="l">Redistribucnich paru</div></div>
<div class="metric"><div class="v">36,770</div><div class="l">Source SKU</div></div>
<div class="metric"><div class="v">41,631</div><div class="l">Target SKU</div></div>
<div class="metric"><div class="v">48,754 ks</div><div class="l">Celkem presunuto</div></div>
</div>

<h3>Cilove miry oversell</h3>
<p>Cil pro 4M oversell: <b>5-10%</b> | Cil pro 9M total: <b>&lt;20%</b></p>

<table>
<tr><th>MinLayer</th><th>4M Oversell</th><th>9M Total Oversell</th><th>Stav</th></tr>
<tr><td>ML0</td><td class="good">1.1%</td><td class="good">2.3%</td><td class="good">V CILI</td></tr>
<tr><td>ML1</td><td class="good">3.6%</td><td class="good">12.5%</td><td class="good">V CILI</td></tr>
<tr><td>ML2</td><td class="warn">5.1%</td><td class="bad">22.2%</td><td class="bad">PREKRACUJE total cil</td></tr>
<tr><td>ML3</td><td class="good">3.4%</td><td class="good">18.0%</td><td class="good">V CILI</td></tr>
</table>

<div class="insight-good">
<b>Klicovy zaver:</b> ML0 a ML1 jsou JIZ v cilovych mezich. ML3 je tesne pod cilem. Jediny problem je ML2 (22.2% total oversell),
ktery prekracuje 20% cil. Optimalizace by se mela zameret primarne na ML2 segment.
</div>
</div>

<!-- ========== SECTION 2: SALES PATTERNS ========== -->
<div class="section">
<h2>2. Prodejni vzory (24M historie) - primarni prediktor</h2>

<p>Analyza 24-mesicni prodejni historie odhalila 5 vzoru, ktere silne predikuji oversell risk po redistribuci.</p>

<table>
<tr><th>Pattern</th><th>Popis</th><th>SKU</th><th>Oversell %</th><th>Avg MinLayer</th></tr>
<tr><td>Dead</td><td>0 prodeju za 24M</td><td>15,625</td><td>7.8%</td><td>0.94</td></tr>
<tr><td>Dying</td><td>Prodeje jen ve starsich obdobich</td><td>6,427</td><td>9.7%</td><td>0.90</td></tr>
<tr><td>Sporadic</td><td>Nepravidelne prodeje</td><td>9,891</td><td>15.3%</td><td>1.10</td></tr>
<tr><td>Consistent</td><td>Prodeje v 3-4 obdobich</td><td>3,288</td><td class="bad">22.7%</td><td>1.70</td></tr>
<tr><td>Declining</td><td>Klesajici trend (B&gt;C&gt;D)</td><td>1,539</td><td class="bad">28.3%</td><td>1.10</td></tr>
</table>

<div class="insight-bad">
<b>Declining pattern je NEJHORSI:</b> 28.3% oversell navzdory nizkemu prumerenemu MinLayer (1.1).
Tyto produkty maji klesajici prodeje - redistribuce z nich odvazi zbozi, ale zdrojova prodejna ho stale prodava (jen mene nez drive).
</div>

<h3>Kombinace Pattern x Store Strength</h3>
<img src="fig_findings_01.png">

<table>
<tr><th>Pattern</th><th>Weak</th><th>Mid</th><th>Strong</th></tr>
<tr><td>Dead</td><td class="good">5.1%</td><td class="good">7.8%</td><td class="good">10.0%</td></tr>
<tr><td>Dying</td><td class="good">8.1%</td><td class="good">9.7%</td><td class="good">12.6%</td></tr>
<tr><td>Sporadic</td><td class="good">10.9%</td><td class="good">15.3%</td><td class="bad">20.1%</td></tr>
<tr><td>Consistent</td><td class="good">13.2%</td><td class="bad">22.7%</td><td class="bad">28.0%</td></tr>
<tr><td>Declining</td><td class="bad">25.1%</td><td class="bad">28.3%</td><td class="bad">35.4%</td></tr>
</table>

<div class="insight">
<b>Pouze 6 z 15 segmentu prekracuje 20% cil.</b> To znamena, ze pravidla nemusime zprisnovat ploskate pro vsechny - staci cilene zasahnout
problematicke kombinace (Sporadic/Strong, Consistent/Mid+Strong, Declining/vsechny).
</div>
</div>

<!-- ========== SECTION 3: STORE STRENGTH ========== -->
<div class="section">
<h2>3. Sila prodejny</h2>

<img src="fig_findings_02.png">

<p>Sila prodejny (merena decilem prodejnosti) ma linearni vliv na obe strany redistribuce:</p>

<table>
<tr><th>Metrika</th><th>Decil 1 (Weak)</th><th>Decil 10 (Strong)</th><th>Trend</th></tr>
<tr><td>Source Reorder %</td><td>26%</td><td>44%</td><td>Linearni rust: silnejsi prodejny = vice reorderu</td></tr>
<tr><td>Target All-Sold (SUCCESS)</td><td>48%</td><td>70%</td><td>Silnejsi prodejny prodaji vsechen redistribuovany tovar</td></tr>
<tr><td>Target Nothing-Sold (PROBLEM)</td><td>32%</td><td>14%</td><td>Slabsi prodejny = vice "zaseknuteho" zbozi</td></tr>
</table>

<div class="insight">
<b>Tok redistribuci:</b> Vetsina redistribuci proudi Mid-&gt;Strong a Strong-&gt;Strong.
To znamena, ze redistributujeme prevazne mezi silnymi prodejnami, kde je vysoka sance prodeje na obou stranach.
</div>
</div>

<!-- ========== SECTION 4: MONTHLY CADENCE ========== -->
<div class="section">
<h2>4. Mesicni kadence prodeju</h2>

<p>Kolik mesicu za poslednich 24M mel produkt prodeje na dane prodejne?</p>

<img src="fig_findings_03.png">

<table>
<tr><th>Mesice s prodeji</th><th>SKU</th><th>Oversell / Reorder %</th><th>Avg MinLayer</th><th>Poznamka</th></tr>
<tr><td>0M</td><td>15,384</td><td>8.3% oversell</td><td>0.94</td><td>Zadne prodeje = nizky oversell</td></tr>
<tr><td>1M</td><td>8,022</td><td>35.5% reorder</td><td>1.00</td><td>Jediny mesic prodeju</td></tr>
<tr><td>3M</td><td>2,635</td><td>47.8% reorder</td><td>1.10</td><td>Sporadicke prodeje</td></tr>
<tr><td>6M</td><td>805</td><td>57.3% reorder</td><td>1.20</td><td>Pravidelnejsi prodeje</td></tr>
<tr><td>10M</td><td>258</td><td>67.1% reorder</td><td>1.50</td><td>Caste prodeje</td></tr>
<tr><td>16M</td><td>58</td><td>81.0% reorder</td><td>1.86</td><td>Temer stale prodeje</td></tr>
</table>

<div class="insight-bad">
<b>MinLayer roste PRILIS POMALU:</b> Produkt s 16 mesici prodeju (ze 24M) ma prumerny ML jen 1.86, ale 81% reorder!
Soucasna heuristika nedostatecne reaguje na frekvenci prodeju. Navrhujeme vyssi ML pro produkty s castymi prodeji.
</div>
</div>

<!-- ========== SECTION 5: PAIR ANALYSIS ========== -->
<div class="section">
<h2>5. Analyza redistribucnich paru</h2>

<p>Kazdy par source-target muzeme klasifikovat podle vysledku na obou stranach:</p>

<img src="fig_findings_04.png">

<table>
<tr><th>Vysledek paru</th><th>Popis</th><th>Pocet</th><th>Podil</th></tr>
<tr><td class="good">BEST</td><td>Source OK (bez reorderu) + Target vse prodal</td><td>14,896</td><td>35.1%</td></tr>
<tr><td class="good">IDEAL</td><td>Source OK + Target castecne prodal</td><td>4,923</td><td>11.6%</td></tr>
<tr><td class="warn">SRC FAIL</td><td>Source reorderoval, ale Target prodal</td><td>13,530</td><td>31.9%</td></tr>
<tr><td class="bad">WASTED</td><td>Source OK, ale Target nic neprodal</td><td>6,274</td><td>14.8%</td></tr>
<tr><td class="bad">DOUBLE FAIL</td><td>Source reorderoval + Target nic neprodal</td><td>2,781</td><td>6.6%</td></tr>
</table>

<div class="insight-good">
<b>Target success rate: 78.6%</b> - vetsina redistribucniho zbozi se proda (alespon castecne).
</div>

<h3>Tok a double-fail rate</h3>
<table>
<tr><th>Smer toku</th><th>Double Fail %</th><th>Hodnoceni</th></tr>
<tr><td>Weak -&gt; Strong</td><td class="good">2.8%</td><td>Nejlepsi smer</td></tr>
<tr><td>Mid -&gt; Strong</td><td class="good">3.9%</td><td>Dobry smer</td></tr>
<tr><td>Strong -&gt; Strong</td><td>5.1%</td><td>Prijatelny</td></tr>
<tr><td>Mid -&gt; Mid</td><td>5.8%</td><td>Prumerny</td></tr>
<tr><td>Strong -&gt; Weak</td><td class="bad">10.6%</td><td>Nejhorsi smer</td></tr>
</table>

<div class="insight">
<b>Redistribuce ze slabych do silnych prodejen funguje nejlepe</b> (2.8% double fail).
Opacny smer (Strong-&gt;Weak) ma 4x vyssi selhani. To potvrzuje, ze sila prodejny je klicovy faktor pro target.
</div>
</div>

<!-- ========== SECTION 6: PROMO/PRICE ========== -->
<div class="section">
<h2>6. Promo a cenova analyza</h2>

<h3>Promo share a oversell</h3>
<p>Klesajici prodejni vzor (Declining) <b>NENI zpusoben promakcemi</b> - podil promo akci (~30%) je stejny jako u ostatnich vzoru.</p>
<p>Ceny produktu jsou stabilni (bez poklesu), takze Declining pattern reflektuje skutecny pokles poptavky.</p>

<table>
<tr><th>Promo podil</th><th>Oversell %</th><th>Poznamka</th></tr>
<tr><td>0% (zadne promo)</td><td>14.2%</td><td>Zakladni uroven</td></tr>
<tr><td>1-20% promo</td><td class="bad">34.4%</td><td>NEJVYSSI oversell</td></tr>
<tr><td>20-50% promo</td><td>29.1%</td><td>Vyssi nez prumer</td></tr>
<tr><td>&gt;50% promo</td><td class="bad">27.8%</td><td>Vysoke, ale nizsi nez 1-20%</td></tr>
</table>

<div class="insight">
<b>Produkty s 1-20% promo poditem maji NEJVYSSI oversell (34.4%).</b> Duvod: tyto produkty se prodavaji primarne behem promo akci.
Po redistribuci (mimo promo obdobi) se prodavaji pomaleji. Produkty s &gt;50% promo (27.8%) maji paradoxne nizsi oversell,
protoze jsou jiz "znamy" jako promo zbozi a system s tim pocita.
</div>
</div>

<!-- ========== SECTION 7: CHRISTMAS ========== -->
<div class="section">
<h2>7. Vanocni analyza</h2>

<table>
<tr><th>Vanocni podil prodeju</th><th>Oversell %</th><th>Popis</th></tr>
<tr><td>0-5% (nesezonni)</td><td>16.0%</td><td>Standardni produkty</td></tr>
<tr><td>5-20% (mirne sezonni)</td><td>20.1%</td><td>Mirny vanocni efekt</td></tr>
<tr><td>20-60% (sezonni)</td><td class="bad">25-27%</td><td>Vyrazny vanocni boost</td></tr>
<tr><td>&gt;60% (ciste vanocni)</td><td>18.8%</td><td>Prodej hlavne o Vanocich</td></tr>
</table>

<div class="insight">
<b>Nejriskovejsi segment: 1-40% vanocni podil</b> - celorocni prodejci, kteri dostavaji boost o Vanocich.
Po redistribuci (mimo Vanoce) se prodavaji pomaleji nez ocekavano.
<br><br>
<b>Ciste vanocni produkty (&gt;60%)</b> maji prekvapive nizsi oversell (18.8%), protoze se po vanocni sezone neprodavaji vubec
a system je spravne identifikuje jako prebytky.
</div>
</div>

<!-- ========== SECTION 8: OTHER FACTORS ========== -->
<div class="section">
<h2>8. Dalsi faktory</h2>

<h3>Redistribucni smycka</h3>
<p>3,117 SKU (8.5%) bylo <b>znovu redistribuovano</b> (Y-STORE TRANSFER). Z nich 72% jsou zero-selleri s ML1.
To indikuje, ze nektere produkty se redistributuji opakovane bez prodeje.</p>

<h3>Koncentrace produktu</h3>
<table>
<tr><th>Pocet prodejen s produktem</th><th>Reorder %</th></tr>
<tr><td>&lt;=20 prodejen</td><td>17.0%</td></tr>
<tr><td>21-50 prodejen</td><td>28.5%</td></tr>
<tr><td>51-100 prodejen</td><td>36.2%</td></tr>
<tr><td>100+ prodejen</td><td class="bad">42.9%</td></tr>
</table>

<div class="insight">
<b>Produkty na 100+ prodejnach maji 42.9% reorder</b> vs. jen 17% u produktu na &lt;=20 prodejnach.
Sirce distribuovane produkty se prodavaji casteji a redistribuce z nich je rizikova.
</div>

<h3>SkuClass delisting</h3>
<p>Delistovane source SKU maji o <b>29 procentnich bodu nizsi reorder</b> (13.2% vs 42.7%).
Pro delistovane produkty je redistribuce bezpecna - MinLayer muze byt 0.</p>

<h3>Brand-Store fit</h3>
<table>
<tr><th>Kombinace</th><th>Reorder %</th><th>Rozdil od prumeru</th></tr>
<tr><td>Strong brand + Strong store</td><td class="bad">45.3%</td><td>+7.8pp</td></tr>
<tr><td>Weak brand + Weak store</td><td class="good">29.3%</td><td>-8.2pp</td></tr>
<tr><td>Rozdil</td><td colspan="2"><b>16 procentnich bodu!</b></td></tr>
</table>

<div class="insight">
<b>Brand-store fit je silny prediktor:</b> Silny brand na silne prodejne = 45.3% reorder.
Slaby brand na slabe prodejne = 29.3%. Rozdil 16pp ukazuje, ze brand-store fit by mel byt soucasti pravidel.
</div>
</div>

<!-- ========== SECTION 9: SUMMARY TABLE ========== -->
<div class="section">
<h2>9. Souhrn vsech faktoru a jejich dopad</h2>

<table>
<tr><th>Faktor</th><th>Dopad na oversell/reorder</th><th>Smer</th><th>Velikost</th><th>Priorita</th></tr>
<tr><td>Sales Pattern (24M)</td><td>Declining 28.3% vs Dead 7.8%</td><td>Rust</td><td class="bad">+20.5pp</td><td>1 - Primarni</td></tr>
<tr><td>Store Strength</td><td>Strong 44% vs Weak 26% reorder</td><td>Rust</td><td class="bad">+18pp</td><td>1 - Primarni</td></tr>
<tr><td>Brand-Store Fit</td><td>Strong+Strong 45.3% vs Weak+Weak 29.3%</td><td>Rust</td><td class="bad">+16pp</td><td>2 - Sekundarni</td></tr>
<tr><td>Product Concentration</td><td>100+ stores 42.9% vs &lt;=20 stores 17%</td><td>Rust</td><td class="bad">+25.9pp</td><td>2 - Sekundarni</td></tr>
<tr><td>Monthly Cadence</td><td>16M: 81% vs 0M: 8.3%</td><td>Rust</td><td class="bad">+72.7pp</td><td>1 - Primarni</td></tr>
<tr><td>SkuClass Delisting</td><td>Delisted 13.2% vs Active 42.7%</td><td>Pokles</td><td class="good">-29.5pp</td><td>1 - Override</td></tr>
<tr><td>Promo Share (1-20%)</td><td>34.4% vs 14.2% (no promo)</td><td>Rust</td><td class="bad">+20.2pp</td><td>3 - Modifier</td></tr>
<tr><td>Xmas Seasonality</td><td>20-60% share: 25-27% vs 16%</td><td>Rust</td><td class="warn">+9-11pp</td><td>3 - Modifier</td></tr>
<tr><td>Redist. Loop</td><td>8.5% SKU re-redistributed, 72% zero-sellers</td><td>Signal</td><td class="warn">Indikator</td><td>3 - Monitoring</td></tr>
</table>

<div class="insight">
<b>Hlavni 3 faktory pro pravidla:</b> (1) Prodejni vzor 24M, (2) Sila prodejny, (3) Mesicni kadence.
Tyto tri faktory vysvetluji vetsinu variability v oversell rates.
Viz <a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> pro konkretni pravidla.
</div>
</div>

<p><i>Generovano: {NOW_STR} | CalculationId=233 | EntityListId=3</i></p>
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

# ---- Chart: fig_dtree_01.png - Source ML matrix heatmap ----
src_ml_matrix = np.array([
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 2],
    [1, 2, 3],
    [2, 3, 3],
])
patterns_dt = ['Dead', 'Dying', 'Sporadic', 'Consistent', 'Declining']
stores_dt = ['Weak', 'Mid', 'Strong']

fig, ax = plt.subplots(1, 1, figsize=(8, 6))
sns.heatmap(src_ml_matrix, annot=True, fmt='d', cmap='YlOrRd',
            xticklabels=stores_dt, yticklabels=patterns_dt, ax=ax,
            vmin=0, vmax=4, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Source MinLayer'})
ax.set_title('Source MinLayer: Lookup Table\n(Sales Pattern 24M x Store Strength)', fontsize=12)
ax.set_ylabel('Sales Pattern (24M)')
ax.set_xlabel('Store Strength')
# Annotate with larger text
for i in range(len(patterns_dt)):
    for j in range(len(stores_dt)):
        val = src_ml_matrix[i][j]
        ax.text(j + 0.5, i + 0.7, f'ML={val}', ha='center', va='center',
                fontsize=9, color='#333', fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_01.png")

# ---- Chart: fig_dtree_02.png - Target ML matrix heatmap ----
tgt_ml_labels = ['Zero', 'Low (1-2)', 'Med (3+)', 'High (ML3=3)']
tgt_ml_matrix = np.array([
    [1, 1, 2],
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5],
])

fig, ax = plt.subplots(1, 1, figsize=(8, 6))
sns.heatmap(tgt_ml_matrix, annot=True, fmt='d', cmap='YlGnBu',
            xticklabels=stores_dt, yticklabels=tgt_ml_labels, ax=ax,
            vmin=0, vmax=5, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Proposed Target MinLayer'})
ax.set_title('Target MinLayer: Lookup Table\n(Sales Bucket x Store Strength)', fontsize=12)
ax.set_ylabel('Sales Bucket')
ax.set_xlabel('Store Strength')
for i in range(len(tgt_ml_labels)):
    for j in range(len(stores_dt)):
        val = tgt_ml_matrix[i][j]
        ax.text(j + 0.5, i + 0.7, f'ML={val}', ha='center', va='center',
                fontsize=9, color='#333', fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_02.png")

# ---- Chart: fig_dtree_03.png - Pseudocode flow ----
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('Decision Flow: Source MinLayer Calculation', fontsize=14, fontweight='bold', pad=20)

def draw_box(ax, x, y, w, h, text, color='#ecf0f1', border='#2c3e50', fontsize=7):
    rect = plt.Rectangle((x - w / 2, y - h / 2), w, h,
                          facecolor=color, edgecolor=border, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize, zorder=3)

def draw_conn(ax, x1, y1, x2, y2, text=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=1.5), zorder=1)
    if text:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 1, my + 1, text, fontsize=6, color='#7f8c8d')

# Root
draw_box(ax, 50, 93, 35, 5, 'START: Source SKU\n36,770 SKU', '#3498db', fontsize=8)

# Check delisting
draw_box(ax, 50, 83, 35, 5, 'SkuClass = D(3), L(4), R(5)?\nIF YES: MinLayer = 0 (DONE)', '#d4edda', fontsize=7)
draw_conn(ax, 50, 90.5, 50, 85.5)

# Sales pattern
draw_box(ax, 50, 73, 35, 5, 'Classify Sales Pattern (24M)\nDead / Dying / Sporadic / Consistent / Declining', '#f39c12', fontsize=7)
draw_conn(ax, 50, 80.5, 50, 75.5, 'Active SKU')

# Store strength
draw_box(ax, 50, 63, 35, 5, 'Classify Store Strength\nWeak (D1-3) / Mid (D4-7) / Strong (D8-10)', '#f39c12', fontsize=7)
draw_conn(ax, 50, 70.5, 50, 65.5)

# Lookup
draw_box(ax, 50, 53, 35, 5, 'LOOKUP: Pattern x Store = Base MinLayer\n(see Source ML matrix)', '#e74c3c', '#c0392b', fontsize=7)
draw_conn(ax, 50, 60.5, 50, 55.5)

# Business rules
draw_box(ax, 25, 43, 30, 5, 'Business Rules:\nA-O(9), Z-O(11): min=1\nDelisted(3,4,5): =0', '#d4edda', fontsize=7)
draw_box(ax, 75, 43, 30, 5, 'Modifiers:\nXmas seasonal(20-60%): +1\nBrand-Store Strong+Strong: +1\nProduct 100+ stores: +1', '#fff3cd', fontsize=7)
draw_conn(ax, 40, 50.5, 25, 45.5)
draw_conn(ax, 60, 50.5, 75, 45.5)

# Final
draw_box(ax, 50, 33, 35, 5, 'FINAL MinLayer = MIN(base + modifiers, 5)\nCAP at 5', '#3498db', fontsize=8)
draw_conn(ax, 25, 40.5, 40, 35.5)
draw_conn(ax, 75, 40.5, 60, 35.5)

# Note
ax.text(50, 25, 'Target MinLayer follows similar pattern using SalesBucket x Store Strength', fontsize=9, ha='center', style='italic')
ax.text(50, 21, 'Goal: send enough so product sells AND 1 remains. All-sold = success but send more next time.', fontsize=9, ha='center', style='italic')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_dtree_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_dtree_03.png")

# ---- BUILD HTML: Report 2 ----
html2 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Decision Tree: Pravidla MinLayer 0-5</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(1)}

<h1>Decision Tree: Pravidla MinLayer 0-5</h1>
<p><b>CalculationId=233</b> | Datum: 2025-07-13 | Generovano: {NOW_STR}</p>
<p>Tento report definuje konkretni pravidla pro nastaveni MinLayer na zaklade analytiky z
<a href="consolidated_findings.html">Report 1: Consolidated Findings</a>.</p>

<!-- ========== SOURCE RULES ========== -->
<div class="section">
<h2>1. Source pravidla</h2>

<p>Zdrojovy MinLayer urcuje, kolik kusu produktu musi zustat na zdrojove prodejne po redistribuci.
Vyssi MinLayer = mene kusu se odveze = nizsi oversell (ale take mene redistribucnich presunu).</p>

<h3>1.1 Lookup tabulka: Pattern x Store</h3>
<p>Primarni prediktor oversell je kombinace prodejniho vzoru (24M historie) a sily prodejny
(viz <a href="consolidated_findings.html">Findings, sekce 2 a 3</a>).</p>

<img src="fig_dtree_01.png">

<table>
<tr><th>Pattern / Store</th><th>Weak</th><th>Mid</th><th>Strong</th><th>Zduvodneni</th></tr>
<tr><td>Dead (0 prodeju 24M)</td><td>1</td><td>1</td><td>1</td><td>Zadne prodeje = nizky oversell (5-10%), ML=1 staci</td></tr>
<tr><td>Dying (stare prodeje)</td><td>1</td><td>1</td><td>1</td><td>Podobne jako Dead, 8-13% oversell, ML=1 staci</td></tr>
<tr><td>Sporadic (nepravidelne)</td><td>1</td><td>1</td><td>2</td><td>Strong stores maji 20% oversell -&gt; zvysit na ML=2</td></tr>
<tr><td>Consistent (3-4 obdobi)</td><td>1</td><td>2</td><td>3</td><td>22-28% oversell, Mid i Strong prekracuji cil</td></tr>
<tr><td>Declining (klesajici)</td><td>2</td><td>3</td><td>3</td><td>25-35% oversell! Vsechny prekracuji cil, Weak taky</td></tr>
</table>

<div class="insight">
<b>Logika:</b> Dead a Dying produkty se neprodavaji, takze redistribuce z nich je bezpecna (ML=1).
Consistent a Declining produkty se stale prodavaji, a pri redistribuci se zdrojova prodejna "vyprazdni" a musi doobjednat.
Silne prodejny maji vyssi riziko, protoze prodavaji vice.
</div>

<h3>1.2 Business rules (Overrides)</h3>
<table>
<tr><th>Pravidlo</th><th>Podminka</th><th>MinLayer</th><th>Zduvodneni</th></tr>
<tr><td>Active orderable</td><td>SkuClass = A-O(9)</td><td>MIN = 1</td><td>Aktivni zbozi nesmi mit ML=0</td></tr>
<tr><td>Z orderable</td><td>SkuClass = Z-O(11)</td><td>MIN = 1</td><td>Z zbozi stale objednavatelne</td></tr>
<tr><td>Delisted</td><td>SkuClass = D(3), L(4), R(5)</td><td>= 0</td><td>Delistovane - bezpecne odvest vse (-29pp reorder)</td></tr>
</table>

<h3>1.3 Modifikatory</h3>
<table>
<tr><th>Modifikator</th><th>Podminka</th><th>Uprava</th><th>Zduvodneni (viz Findings)</th></tr>
<tr><td>Vanocni sezonnost</td><td>Xmas share 20-60%</td><td>+1</td><td>Sekce 7: +9-11pp oversell pro sezonni produkty</td></tr>
<tr><td>Brand-Store fit</td><td>Strong brand + Strong store</td><td>+1</td><td>Sekce 8: +16pp oversell gap</td></tr>
<tr><td>Siroka distribuce</td><td>Produkt na 100+ prodejnach</td><td>+1</td><td>Sekce 8: +25.9pp reorder gap</td></tr>
</table>

<div class="insight">
<b>CAP:</b> Vysledny MinLayer je omezen na maximum 5. Modifikatory se prictou k base hodnote z lookup tabulky.
</div>
</div>

<!-- ========== TARGET RULES ========== -->
<div class="section">
<h2>2. Target pravidla (sales-based)</h2>

<p><b>Cil:</b> Poslat dostatek kusu, aby se produkt prodaval A 1 kus zustal na prodejne.
Pokud se vse proda (all-sold), je to uspech, ale priste posleme vice.</p>

<h3>2.1 Lookup tabulka: SalesBucket x Store</h3>

<img src="fig_dtree_02.png">

<table>
<tr><th>SalesBucket / Store</th><th>Weak</th><th>Mid</th><th>Strong</th><th>Zduvodneni</th></tr>
<tr><td>Zero (0 prodeju)</td><td>1</td><td>1</td><td>2</td><td>Zadne prodeje, ale Strong stores prodaji vse (66.5%)</td></tr>
<tr><td>Low (1-2 prodeje)</td><td>1</td><td>2</td><td>3</td><td>Nizke prodeje, Mid/Strong stores maji &gt;56% all-sold</td></tr>
<tr><td>Med (3+ prodeju)</td><td>2</td><td>3</td><td>4</td><td>Castejsi prodeje, vyssi ML = vice zbozi zusane</td></tr>
<tr><td>High (ML3=3)</td><td>3</td><td>4</td><td>5</td><td>Vysoke prodeje, ML3 Strong: 81.4% all-sold</td></tr>
</table>

<h3>2.2 Data podporujici target pravidla</h3>
<p>Proc navysujeme target ML pro silne prodejny? Protoze silne prodejny prodaji vse a pak nemaji zasobu:</p>

<table>
<tr><th>Segment</th><th>All-sold %</th><th>Avg extra ks potreba</th><th>Vyznam</th></tr>
<tr><td>ML1 Strong</td><td class="bad">65.6%</td><td>1.79 ks/target</td><td>65% targetu vse prodalo, kazdy potrebuje v prumeru 1.8 ks navic</td></tr>
<tr><td>ML2 Strong</td><td class="bad">61.8%</td><td>2.51 ks/target</td><td>Vyssi ML, ale stale 62% all-sold</td></tr>
<tr><td>ML3 Strong</td><td class="bad">81.4%</td><td>5.19 ks/target</td><td>81% all-sold! Tyto targety potrebuji vyrazne vice</td></tr>
</table>

<div class="insight">
<b>"Extra needed"</b> = kolik vice kusu bychom meli poslat, aby po vsech prodejich zustal alespon 1 kus.
Napr. ML3 Strong: prumerny target potrebuje 5.19 kusu navic. Pokud zvysime target MinLayer, posime vice kusu,
a je pravdepodobnejsi, ze po prodejich alespon 1 kus zustane.
</div>
</div>

<!-- ========== PSEUDOCODE ========== -->
<div class="section">
<h2>3. Pseudokod</h2>

<img src="fig_dtree_03.png">

<h3>3.1 Source MinLayer</h3>
<pre>
FUNCTION CalculateSourceMinLayer(sku, store):
    -- 1. Delisting override
    IF sku.SkuClass IN (3, 4, 5):   -- D, L, R
        RETURN 0

    -- 2. Classify sales pattern (24M)
    pattern = ClassifySalesPattern24M(sku, store)
    -- Dead: 0 sales in 24M
    -- Dying: sales only in periods A/B, nothing recent
    -- Sporadic: irregular sales, not in every period
    -- Consistent: sales in 3-4 of 4 periods
    -- Declining: B &gt; C &gt; D (each period lower)

    -- 3. Classify store strength
    strength = ClassifyStoreStrength(store.Decile)
    -- Weak: decile 1-3, Mid: 4-7, Strong: 8-10

    -- 4. Lookup base MinLayer
    base = SOURCE_LOOKUP[pattern][strength]

    -- 5. Business rules
    IF sku.SkuClass IN (9, 11):     -- A-O, Z-O
        base = MAX(base, 1)

    -- 6. Modifiers
    IF sku.XmasShare BETWEEN 0.20 AND 0.60:
        base = base + 1
    IF BrandStoreFit(sku, store) == 'Strong+Strong':
        base = base + 1
    IF sku.StoreCount &gt; 100:
        base = base + 1

    RETURN MIN(base, 5)
</pre>

<h3>3.2 Target MinLayer</h3>
<pre>
FUNCTION CalculateTargetMinLayer(sku, store):
    -- 1. Classify sales bucket
    bucket = ClassifySalesBucket(sku, store)
    -- Zero: 0 sales
    -- Low: 1-2 sales
    -- Med: 3+ sales
    -- High: current ML3 = 3

    -- 2. Classify store strength
    strength = ClassifyStoreStrength(store.Decile)

    -- 3. Lookup base MinLayer
    base = TARGET_LOOKUP[bucket][strength]

    RETURN MIN(base, 5)
</pre>
</div>

<p><i>Generovano: {NOW_STR} | CalculationId=233 | EntityListId=3 |
Viz <a href="consolidated_backtest.html">Report 3: Backtest</a> pro dopad navrhovanych pravidel.</i></p>
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

# ---- Source backtest data ----
src_bt_data = [
    ('Consistent', 'Mid', 1164, 1877, 912, 271, 271, 22.7),
    ('Consistent', 'Strong', 1693, 2898, 2522, 535, 579, 28.0),
    ('Consistent', 'Weak', 431, 641, 12, 5, 5, 13.2),
    ('Dead', 'Mid', 6967, 8633, 334, 189, 189, 7.8),
    ('Dead', 'Strong', 4061, 5143, 209, 112, 112, 10.0),
    ('Dead', 'Weak', 4597, 5461, 235, 129, 129, 5.1),
    ('Declining', 'Mid', 569, 781, 1110, 383, 427, 28.3),
    ('Declining', 'Strong', 751, 1121, 1329, 387, 423, 35.4),
    ('Declining', 'Weak', 219, 294, 223, 99, 100, 25.1),
    ('Dying', 'Mid', 2882, 3505, 170, 117, 117, 9.7),
    ('Dying', 'Strong', 1951, 2373, 82, 52, 52, 12.6),
    ('Dying', 'Weak', 1594, 1933, 113, 77, 77, 8.1),
    ('Sporadic', 'Mid', 4176, 5783, 121, 52, 52, 15.3),
    ('Sporadic', 'Strong', 3712, 5705, 2729, 835, 837, 20.1),
    ('Sporadic', 'Weak', 2003, 2606, 59, 26, 26, 10.9),
]
src_bt_cols = ['Pattern', 'Store', 'SKU', 'CurrentQty', 'ExtraKept', 'BlockedSKU', 'BlockedQty', 'OversellPct']

total_src_sku = sum(r[2] for r in src_bt_data)
total_src_qty = sum(r[3] for r in src_bt_data)
total_extra = sum(r[4] for r in src_bt_data)
total_blocked_sku = sum(r[5] for r in src_bt_data)
total_blocked_qty = sum(r[6] for r in src_bt_data)

# ---- Chart: fig_backtest_01.png - Source backtest ----
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Bar chart of extra units kept by segment
bt_labels = [f"{r[0]}\n{r[1]}" for r in src_bt_data]
bt_extra = [r[4] for r in src_bt_data]
bt_blocked = [r[5] for r in src_bt_data]
bt_oversell = [r[7] for r in src_bt_data]

colors_bt = []
for r in src_bt_data:
    if r[7] > 25:
        colors_bt.append('#e74c3c')
    elif r[7] > 15:
        colors_bt.append('#f39c12')
    else:
        colors_bt.append('#27ae60')

axes[0].barh(range(len(bt_labels)), bt_extra, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(range(len(bt_labels)))
axes[0].set_yticklabels(bt_labels, fontsize=7)
axes[0].set_xlabel('Extra Units Kept at Source')
axes[0].set_title('Source Backtest: Extra Units Kept by Segment\n(red=high oversell, green=low)')
for i, (e, o) in enumerate(zip(bt_extra, bt_oversell)):
    axes[0].text(e + 30, i, f'{e:,} kept | {o}% oversell', va='center', fontsize=7)
axes[0].invert_yaxis()

# Blocked SKU
axes[1].barh(range(len(bt_labels)), bt_blocked, color=colors_bt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(range(len(bt_labels)))
axes[1].set_yticklabels(bt_labels, fontsize=7)
axes[1].set_xlabel('Blocked SKU (would not be redistributed)')
axes[1].set_title('Source Backtest: Blocked SKU by Segment')
for i, b in enumerate(bt_blocked):
    axes[1].text(b + 10, i, f'{b:,}', va='center', fontsize=7)
axes[1].invert_yaxis()

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_01.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_01.png")

# ---- Target backtest data ----
tgt_bt_data = [
    ('ML1', 'Mid', 2095, 58.4, 39.8, 1844, 1.51),
    ('ML1', 'Strong', 1788, 65.6, 33.3, 2098, 1.79),
    ('ML1', 'Weak', 847, 51.7, 47.1, 620, 1.42),
    ('ML2', 'Mid', 12793, 53.1, 23.7, 15207, 2.24),
    ('ML2', 'Strong', 14766, 61.8, 17.6, 22934, 2.51),
    ('ML2', 'Weak', 4418, 49.6, 27.3, 4585, 2.09),
    ('ML3', 'Mid', 1866, 77.8, 4.6, 7196, 4.96),
    ('ML3', 'Strong', 2554, 81.4, 3.8, 10801, 5.19),
    ('ML3', 'Weak', 504, 76.4, 5.2, 1918, 4.98),
]
tgt_bt_cols = ['ML', 'Store', 'SKU', 'AllSoldPct', 'NothingPct', 'ExtraNeeded', 'AvgExtra']

total_tgt_extra = sum(r[5] for r in tgt_bt_data)

# ---- Chart: fig_backtest_02.png - Target backtest ----
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

tgt_labels = [f"{r[0]}\n{r[1]}" for r in tgt_bt_data]
tgt_allsold_bt = [r[3] for r in tgt_bt_data]
tgt_nothing_bt = [r[4] for r in tgt_bt_data]
tgt_extra_bt = [r[5] for r in tgt_bt_data]

colors_tgt = []
for r in tgt_bt_data:
    if r[3] > 70:
        colors_tgt.append('#e74c3c')
    elif r[3] > 55:
        colors_tgt.append('#f39c12')
    else:
        colors_tgt.append('#27ae60')

axes[0].barh(range(len(tgt_labels)), tgt_allsold_bt, color=colors_tgt, edgecolor='#333', linewidth=0.5)
axes[0].set_yticks(range(len(tgt_labels)))
axes[0].set_yticklabels(tgt_labels, fontsize=8)
axes[0].set_xlabel('All-Sold % (= need more stock)')
axes[0].set_title('Target: All-Sold Rate by Segment\n(red = high all-sold = need higher ML)')
for i, (a, n) in enumerate(zip(tgt_allsold_bt, tgt_nothing_bt)):
    axes[0].text(a + 0.5, i, f'{a}% sold | {n}% nothing', va='center', fontsize=7)
axes[0].invert_yaxis()

axes[1].barh(range(len(tgt_labels)), tgt_extra_bt, color=colors_tgt, edgecolor='#333', linewidth=0.5)
axes[1].set_yticks(range(len(tgt_labels)))
axes[1].set_yticklabels(tgt_labels, fontsize=8)
axes[1].set_xlabel('Extra pcs needed (total)')
axes[1].set_title('Target: Additional pcs needed so 1 remains after sales')
for i, (e, a) in enumerate(zip(tgt_extra_bt, [r[6] for r in tgt_bt_data])):
    axes[1].text(e + 100, i, f'{e:,} pcs (avg {a}/tgt)', va='center', fontsize=7)
axes[1].invert_yaxis()

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_02.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_02.png")

# ---- Chart: fig_backtest_03.png - Combined impact ----
fig, ax = plt.subplots(1, 1, figsize=(12, 6))

categories = ['Current\nRedist. Volume', 'Source:\nBlocked SKU', 'Source:\nExtra Kept', 'Target:\nExtra Needed', 'Net\nVolume Change']
values = [total_src_qty, -total_blocked_qty, -total_extra, total_tgt_extra, total_tgt_extra - total_extra - total_blocked_qty]
colors_impact = ['#3498db', '#e74c3c', '#e67e22', '#27ae60', '#8e44ad']

bars = ax.bar(range(len(categories)), values, color=colors_impact, edgecolor='#333', linewidth=0.5)
ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylabel('Pieces (pcs)')
ax.set_title('Combined Impact: Volume Changes with Proposed Rules')
ax.axhline(y=0, color='black', linewidth=0.5)

for i, v in enumerate(values):
    offset = 500 if v >= 0 else -1200
    ax.text(i, v + offset, f'{v:+,} pcs', ha='center', fontsize=10, fontweight='bold')

fig.tight_layout()
fig.savefig(os.path.join(REPORTS_DIR, 'fig_backtest_03.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  [OK] fig_backtest_03.png")

# ---- BUILD HTML: Report 3 ----
# Pre-calculate oversell stats for blocked SKU
total_oversell_in_blocked = sum(r[5] * r[7] / 100 for r in src_bt_data)

html3 = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Backtest: Dopad navrhovanych pravidiel</title>
<style>{CSS}</style>
</head>
<body>
{nav_bar(2)}

<h1>Backtest: Dopad navrhovanych pravidiel</h1>
<p><b>CalculationId=233</b> | Datum: 2025-07-13 | Generovano: {NOW_STR}</p>
<p>Tento report ukazuje ocekavany dopad pravidel z
<a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> na redistribucni objemy a oversell.</p>

<!-- ========== SOURCE BACKTEST ========== -->
<div class="section">
<h2>1. Source Backtest</h2>

<p>Pro kazdy segment (Pattern x Store) ukazujeme:</p>
<ul>
<li><b>Current Qty</b> = celkove redistribuovane mnozstvi v aktualni kalkulaci</li>
<li><b>Extra Kept</b> = kolik vice kusu by zustalo na source (kvuli zvysenemu MinLayer)</li>
<li><b>Blocked SKU</b> = kolik SKU by se vubec neredistribuovalo (ML vyssi nez dostupna zasoba)</li>
<li><b>Blocked Qty</b> = mnozstvi, ktere by se neredistribuovalo</li>
<li><b>Oversell %</b> = soucasna mira oversell v segmentu</li>
</ul>

<img src="fig_backtest_01.png">

<table>
<tr><th>Pattern</th><th>Store</th><th>SKU</th><th>Current Qty</th><th>Extra Kept</th><th>Blocked SKU</th><th>Blocked Qty</th><th>Oversell %</th></tr>"""

for r in src_bt_data:
    cls_os = 'bad' if r[7] > 20 else ('warn' if r[7] > 15 else 'good')
    html3 += f"""<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]:,}</td><td>{r[3]:,}</td>
    <td>{r[4]:,}</td><td>{r[5]:,}</td><td>{r[6]:,}</td>
    <td class="{cls_os}">{r[7]}%</td></tr>"""

html3 += f"""
<tr style="font-weight:bold; background:#e8e8e8;">
<td colspan="2">CELKEM</td><td>{total_src_sku:,}</td><td>{total_src_qty:,}</td>
<td>{total_extra:,}</td><td>{total_blocked_sku:,}</td><td>{total_blocked_qty:,}</td>
<td>-</td></tr>
</table>

<div class="insight">
<b>Interpretace:</b>
<ul>
<li><b>{total_blocked_sku:,} SKU</b> by se neredistribuovalo (blokovano vyssi ML).</li>
<li><b>{total_blocked_qty:,} ks</b> by se neodvezlo z techto blokovanych SKU.</li>
<li><b>{total_extra:,} ks</b> by navic zustalo na source prodejnach (mene odvezeno i u redistributed SKU).</li>
<li>Vetsina blokovanych SKU je z <b>Declining/Strong</b> (387) a <b>Sporadic/Strong</b> (835) - presne segmenty s nejvyssim oversell.</li>
</ul>
</div>

<div class="insight-good">
<b>Cileny dopad:</b> Z celkovych {total_blocked_sku:,} blokovanych SKU maji segmenty s &gt;20% oversell celkem
{sum(r[5] for r in src_bt_data if r[7]>20):,} blokovanych SKU.
To znamena, ze vetsina blokovani miri presne na problematicke segmenty.
</div>
</div>

<!-- ========== TARGET BACKTEST ========== -->
<div class="section">
<h2>2. Target Backtest</h2>

<p>Pro kazdy target segment (ML x Store) ukazujeme:</p>
<ul>
<li><b>All-sold %</b> = kolik targetu prodalo vsechny redistribuovane kusy (= uspech, ale priste posleme vice)</li>
<li><b>Nothing-sold %</b> = kolik targetu neprodalo nic (= problem)</li>
<li><b>Extra needed (pcs)</b> = kolik vice kusu bychom meli poslat, aby po prodejich zustal alespon 1 kus</li>
<li><b>Avg extra/target</b> = prumerna potreba na 1 target SKU</li>
</ul>

<img src="fig_backtest_02.png">

<table>
<tr><th>MinLayer</th><th>Store</th><th>SKU</th><th>All-sold %</th><th>Nothing %</th><th>Extra needed (pcs)</th><th>Avg extra/target</th></tr>"""

for r in tgt_bt_data:
    cls_as = 'bad' if r[3] > 70 else ('warn' if r[3] > 55 else '')
    html3 += f"""<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]:,}</td>
    <td class="{cls_as}">{r[3]}%</td><td>{r[4]}%</td>
    <td>{r[5]:,}</td><td>{r[6]}</td></tr>"""

html3 += f"""
<tr style="font-weight:bold; background:#e8e8e8;">
<td colspan="2">CELKEM</td><td>{sum(r[2] for r in tgt_bt_data):,}</td>
<td>-</td><td>-</td><td>{total_tgt_extra:,}</td><td>-</td></tr>
</table>

<div class="insight">
<b>Co znamena "extra needed":</b> Pokud je target all-sold, znamena to, ze jsme poslali PRILIS MALO kusu.
"Extra needed" ukazuje, kolik vice kusu bychom meli poslat, aby po vsech prodejich zustal alespon 1 kus.
<br><br>
Napr. ML3 Strong: 81.4% all-sold, prumerny target potrebuje 5.19 kusu navic. Pokud zvysime target MinLayer z 3 na 4-5,
posime vice kusu a je pravdepodobnejsi, ze alespon 1 kus zustane.
</div>

<div class="insight-bad">
<b>Celkem {total_tgt_extra:,} ks navic</b> by melo proudit do systemu s navrzenymi target ML zvysenimi.
To je vyrazne navyseni objemu, ale vetsina smeruje do silnych prodejen (Strong), kde je vysoka pravdepodobnost prodeje.
</div>
</div>

<!-- ========== COMBINED IMPACT ========== -->
<div class="section">
<h2>3. Celkovy dopad</h2>

<img src="fig_backtest_03.png">

<h3>3.1 Source strana</h3>
<table>
<tr><th>Metrika</th><th>Hodnota</th><th>Vyznam</th></tr>
<tr><td>Blokovane SKU</td><td class="bad">{total_blocked_sku:,}</td><td>SKU, ktere by se vubec neredistribuovaly</td></tr>
<tr><td>Blokovane ks</td><td class="bad">{total_blocked_qty:,}</td><td>Kusy, ktere by zustaly na source</td></tr>
<tr><td>Extra kept ks</td><td class="warn">{total_extra:,}</td><td>Vice kusu zustane na source i u redistributed SKU</td></tr>
<tr><td>Snizeni oversell</td><td class="good">Cilene na segmenty &gt;20%</td><td>Vetsina blokovani v Declining, Consistent/Strong</td></tr>
</table>

<h3>3.2 Target strana</h3>
<table>
<tr><th>Metrika</th><th>Hodnota</th><th>Vyznam</th></tr>
<tr><td>Extra needed ks</td><td class="good">{total_tgt_extra:,}</td><td>Vice kusu posime do targetu s vysokym all-sold</td></tr>
<tr><td>Hlavni beneficienti</td><td>Strong stores</td><td>ML2/ML3 Strong prodejny dostanou vice kusu</td></tr>
<tr><td>Ocekavany efekt</td><td>Vice "1 zustane"</td><td>Vyssi ML = mensi sance ze se vse proda</td></tr>
</table>

<h3>3.3 Celkova zmena objemu</h3>
<div class="insight">
<b>Source:</b> -{total_extra + total_blocked_qty:,} ks (mene odeslano ze source)
<br>
<b>Target:</b> +{total_tgt_extra:,} ks (vice prijato na target)
<br>
<b>Net:</b> {total_tgt_extra - total_extra - total_blocked_qty:+,} ks zmena v redistribucnim objemu
<br><br>
<b>Vysvetleni:</b> Na source strane drzime vice kusu (vyssi MinLayer = mene odvezeme). Na target strane posisme vice kusu
(vyssi MinLayer = posisme vice, aby 1 zustal). Celkovy efekt zavisna na pomeru obou stran.
</div>

<div class="insight-good">
<b>Klicovy zaver:</b>
<ul>
<li>Source pravidla <b>cilene blokuji</b> redistribuci z problematickych segmentu (Declining, Consistent/Strong)</li>
<li>Target pravidla <b>navysuji objem</b> pro silne prodejny, kde se zbozi prodava</li>
<li>Celkovy efekt: <b>mensi oversell</b> na source strane, <b>lepsi zasobeni</b> na target strane</li>
<li>Pravidla jsou <b>konzervativni</b> - Dead a Dying segmenty (22,000+ SKU) zustavaji na ML=1</li>
</ul>
</div>
</div>

<p><i>Generovano: {NOW_STR} | CalculationId=233 | EntityListId=3 |
Viz <a href="consolidated_findings.html">Report 1: Findings</a> pro kompletni analytiku,
<a href="consolidated_decision_tree.html">Report 2: Decision Tree</a> pro pravidla.</i></p>
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
print("    + fig_findings_01.png (oversell heatmap)")
print("    + fig_findings_02.png (store decile lines)")
print("    + fig_findings_03.png (monthly cadence)")
print("    + fig_findings_04.png (pair outcomes)")
print("")
print("  reports/consolidated_decision_tree.html")
print("    + fig_dtree_01.png (source ML matrix)")
print("    + fig_dtree_02.png (target ML matrix)")
print("    + fig_dtree_03.png (decision flow)")
print("")
print("  reports/consolidated_backtest.html")
print("    + fig_backtest_01.png (source backtest)")
print("    + fig_backtest_02.png (target backtest)")
print("    + fig_backtest_03.png (combined impact)")
print("")
print("Deleted old reports:")
for fname in old_reports:
    print("  " + fname)
print("")
print("Done at: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
