"""
Master report regenerator with CORRECTED reasoning:
- Target all-sold = SUCCESS (not a problem!)
- Target nothing-sold = the ONLY real target problem
- All-sold + 0 remaining = opportunity to send MORE next time
- Business rule: A-O/Z-O must have min 1 on stock

Regenerates: full_analysis_report.html, combined_segmentation_report.html,
decision_tree_report.html, extended_analysis_report.html
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

GENERATED = datetime.now().strftime('%Y-%m-%d %H:%M')

# ============================================================
# REGENERATE: Target charts with corrected colors/labels
# ============================================================

# Target by MinLayer3
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
tgt_ml['pct_partial_sold'] = 100 - tgt_ml['pct_nothing_sold'] - tgt_ml['pct_all_sold']

# Fig02 corrected: store decile
src_decile = pd.DataFrame({
    'Decile': list(range(1, 11)),
    'pct_reorder': [26.0, 30.7, 31.6, 34.2, 37.2, 38.8, 39.9, 41.4, 43.7, 44.1],
    'pct_oversell': [6.6, 7.1, 9.1, 9.1, 11.0, 12.7, 14.5, 15.6, 17.6, 19.6],
})
tgt_decile = pd.DataFrame({
    'Decile': list(range(1, 11)),
    'pct_all_sold': [48.3, 52.8, 53.3, 52.9, 55.7, 56.2, 59.1, 60.5, 63.0, 70.1],
    'pct_nothing_sold': [32.1, 27.9, 27.1, 26.4, 24.6, 24.2, 21.1, 20.1, 18.3, 13.7],
})

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(src_decile['Decile'], src_decile['pct_reorder'], 'o-', color='#e74c3c', label='Reorder %', linewidth=2)
axes[0].plot(src_decile['Decile'], src_decile['pct_oversell'], 's-', color='#8e44ad', label='Oversell %', linewidth=2)
axes[0].set_xlabel('Decil prodejny (1=slabá, 10=silná)'); axes[0].set_ylabel('%')
axes[0].set_title('SOURCE: Reorder/Oversell dle síly prodejny'); axes[0].legend()
axes[0].set_xticks(range(1,11))

# CORRECTED: green for all-sold (=success), red for nothing-sold (=problem)
axes[1].plot(tgt_decile['Decile'], tgt_decile['pct_all_sold'], 'o-', color='#27ae60', label='Vše prodáno % (ÚSPĚCH)', linewidth=2)
axes[1].plot(tgt_decile['Decile'], tgt_decile['pct_nothing_sold'], 's-', color='#e74c3c', label='Nic neprodáno % (PROBLÉM)', linewidth=2)
axes[1].set_xlabel('Decil prodejny (1=slabá, 10=silná)'); axes[1].set_ylabel('%')
axes[1].set_title('TARGET: Výsledek dle síly prodejny'); axes[1].legend()
axes[1].set_xticks(range(1,11))
axes[1].fill_between(tgt_decile['Decile'], tgt_decile['pct_all_sold'], alpha=0.1, color='green')
axes[1].fill_between(tgt_decile['Decile'], tgt_decile['pct_nothing_sold'], alpha=0.1, color='red')
fig.tight_layout(); fig.savefig('reports/fig02_store_decile.png', dpi=150, bbox_inches='tight'); plt.close()

# Corrected target chart
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
x = np.arange(len(tgt_ml))
w = 0.5
# CORRECTED: all-sold = green (success), partial = yellow, nothing = red (problem)
axes[0].bar(x, tgt_ml['pct_all_sold'], w, label='Vše prodáno (ÚSPĚCH)', color='#27ae60', alpha=0.8)
axes[0].bar(x, tgt_ml['pct_partial_sold'], w, bottom=tgt_ml['pct_all_sold'], label='Částečně prodáno', color='#f39c12', alpha=0.8)
axes[0].bar(x, tgt_ml['pct_nothing_sold'], w, bottom=tgt_ml['pct_all_sold'] + tgt_ml['pct_partial_sold'], label='Nic neprodáno (PROBLÉM)', color='#e74c3c', alpha=0.8)
axes[0].set_xlabel('Target MinLayer3'); axes[0].set_ylabel('% Target SKU')
axes[0].set_title('TARGET: Výsledek redistribuce (OPRAVENÝ pohled)')
axes[0].legend(loc='upper left', fontsize=8)
axes[0].set_xticks(x); axes[0].set_xticklabels(tgt_ml['MinLayer3'])
for i, row in tgt_ml.iterrows():
    axes[0].text(x[i], -5, f'n={row["total_skus"]:,}', ha='center', fontsize=8, color='gray')

# Nothing-sold rate (the only real problem)
w2 = 0.5
bars = axes[1].bar(x, tgt_ml['pct_nothing_sold'], w2, color='#e74c3c', alpha=0.8)
axes[1].set_xlabel('Target MinLayer3'); axes[1].set_ylabel('% Target SKU')
axes[1].set_title('TARGET: "Nic neprodáno" rate (JEDINÝ problém)')
axes[1].set_xticks(x); axes[1].set_xticklabels(tgt_ml['MinLayer3'])
for bar, row in zip(bars, tgt_ml.iterrows()):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{row[1]["pct_nothing_sold"]}%', ha='center', fontsize=10, fontweight='bold')
fig.tight_layout()
fig.savefig('reports/fig01b_target_corrected.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# Corrected Pair analysis chart
# ============================================================
pairs_corrected = pd.DataFrame({
    'Outcome': ['BEST\nsrc OK + tgt all sold', 'SRC FAIL\ntgt all sold',
                'IDEAL\nsrc OK + tgt partial', 'SRC FAIL\ntgt partial',
                'WASTED\nsrc OK + tgt nothing', 'DOUBLE FAIL\nboth fail'],
    'pairs': [14896, 10390, 4923, 3140, 6274, 2781],
    'color': ['#27ae60', '#f39c12', '#2ecc71', '#e67e22', '#e74c3c', '#8e44ad']
})
pairs_corrected['pct'] = pairs_corrected['pairs'] / pairs_corrected['pairs'].sum() * 100

fig, ax = plt.subplots(1, 1, figsize=(12, 5))
bottom = 0
for _, row in pairs_corrected.iterrows():
    ax.barh(0, row['pct'], left=bottom, color=row['color'], height=0.6)
    if row['pct'] > 5:
        ax.text(bottom + row['pct']/2, 0, f"{row['pct']:.1f}%\n{row['Outcome']}",
                ha='center', va='center', fontsize=7, color='white', fontweight='bold')
    bottom += row['pct']
ax.set_xlim(0, 100); ax.set_yticks([])
ax.set_xlabel('% redistribučních párů')
ax.set_title('Párové výsledky redistribuce (OPRAVENÝ pohled: all-sold = ÚSPĚCH)')

# Success bracket
ax.annotate('', xy=(0, 0.55), xytext=(pairs_corrected['pct'].iloc[0]+pairs_corrected['pct'].iloc[1], 0.55),
           arrowprops=dict(arrowstyle='<->', color='green', lw=2))
success_pct = pairs_corrected['pct'].iloc[0] + pairs_corrected['pct'].iloc[1]
ax.text(success_pct/2, 0.7, f'Target ÚSPĚCH: {success_pct:.0f}%', ha='center', fontsize=9, color='green', fontweight='bold')

fig.tight_layout()
fig.savefig('reports/fig14_pair_outcomes.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# Corrected Target MinLayer proposal
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(10, 5))
# Target goal: send ENOUGH so 1 remains. All-sold = good but send more!
tgt_pivot = pd.DataFrame({
    'Weak': [1, 1, 2, 3],
    'Mid': [1, 2, 3, 4],
    'Strong': [2, 3, 4, 5],
}, index=['Zero sales', 'Low (1-2)', 'Med (3+)', 'High freq (ML3=3)'])

sns.heatmap(tgt_pivot, annot=True, fmt='.0f', cmap='YlGn', ax=ax,
            vmin=0, vmax=5, linewidths=1, cbar_kws={'label': 'Navrhovaný MinLayer'})
ax.set_title('TARGET: Navrhovaný MinLayer (0-5)\nCíl: poslat DOST aby se prodalo A zůstal 1 ks\n(Vyšší ML na silných prodejnách = prodá se víc → potřeba víc)')
ax.set_ylabel('Frekvence prodejů 6M'); ax.set_xlabel('Síla prodejny')
fig.tight_layout()
fig.savefig('reports/fig12_proposed_target_minlayer.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# Summary stats for the report
# ============================================================
total_pairs = 42404
target_success = 14896 + 10390 + 4923 + 3140  # all where target sold something
target_success_pct = target_success / total_pairs * 100
target_fail = 6274 + 2781  # nothing sold
target_fail_pct = target_fail / total_pairs * 100

source_ok = 14896 + 6274 + 4923  # source no reorder
source_ok_pct = source_ok / total_pairs * 100
source_fail = 10390 + 3140 + 2781  # source had reorder
source_fail_pct = source_fail / total_pairs * 100

print(f"=== CORRECTED SUMMARY ===")
print(f"Target SUCCESS (sold something): {target_success:,} ({target_success_pct:.1f}%)")
print(f"Target FAIL (nothing sold): {target_fail:,} ({target_fail_pct:.1f}%)")
print(f"Source OK (no reorder): {source_ok:,} ({source_ok_pct:.1f}%)")
print(f"Source FAIL (had reorder): {source_fail:,} ({source_fail_pct:.1f}%)")
print(f"BEST pairs (src OK + tgt sold): {14896+4923} ({(14896+4923)/total_pairs*100:.1f}%)")
print(f"WORST pairs (wasted + double fail): {6274+2781} ({(6274+2781)/total_pairs*100:.1f}%)")
print(f"\nCharts regenerated with corrected reasoning.")
print(f"  fig01b_target_corrected.png")
print(f"  fig02_store_decile.png (corrected colors)")
print(f"  fig12_proposed_target_minlayer.png (corrected)")
print(f"  fig14_pair_outcomes.png (corrected)")
