from __future__ import annotations

from pathlib import Path
import html

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parent
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 140
plt.rcParams["savefig.bbox"] = "tight"

DATA = {
    "validation": [
        ("Redistribucnich paru", "42 404"),
        ("Redistribuovanych ks", "48 754"),
        ("Source SKU", "36 770"),
        ("Target SKU", "41 631"),
        ("Dotcenych SKU celkem", "78 401"),
        ("Dotcenych produktu", "5 152"),
        ("Prodejen v analytice", "353"),
        ("Duplicity paru", "0"),
        ("Source = Target", "0"),
        ("Non-positive qty", "0"),
        ("SKU bez supply historie", "0"),
        ("Missing calc/current snapshot", "0 / 0"),
        ("Missing SourceEntityMinLayer", "1 798 (ML=0, JSON NULL)"),
    ],
    "overview_source": [
        ("Oversell", "1 317 (3.6%)", "1 464 (3.0%)", "4 718 (12.8%)", "5 578 (11.4%)"),
        ("Reorder", "7 087 (19.3%)", "7 980 (16.4%)", "13 841 (37.6%)", "16 615 (34.1%)"),
    ],
    "overview_target": [
        ("Avg Sell-Through", "45.3%", "69.2%"),
        ("Avg ST-1pc", "58.2%", "79.6%"),
        ("Nothing-sold", "17 552 (42.2%)", "8 872 (21.3%)"),
        ("All-sold", "13 631 (32.7%)", "24 862 (59.7%)"),
    ],
    "source_pattern": [
        ("Dead", "Weak", 4987, 6009, 4.6, 22.4),
        ("Dead", "Mid", 6003, 7398, 7.2, 27.2),
        ("Dead", "Strong", 4523, 5732, 9.1, 28.6),
        ("Dying", "Weak", 1757, 2135, 6.6, 26.1),
        ("Dying", "Mid", 2346, 2860, 8.8, 31.6),
        ("Dying", "Strong", 2085, 2536, 10.6, 33.4),
        ("Sporadic", "Weak", 2819, 3715, 10.8, 36.4),
        ("Sporadic", "Mid", 4437, 6048, 15.4, 40.7),
        ("Sporadic", "Strong", 5289, 7820, 18.0, 43.4),
        ("Consistent", "Weak", 33, 72, 5.6, 25.0),
        ("Consistent", "Mid", 44, 91, 15.4, 49.5),
        ("Consistent", "Strong", 214, 433, 13.6, 36.7),
        ("Declining", "Weak", 283, 459, 13.3, 41.0),
        ("Declining", "Mid", 598, 1025, 15.8, 46.9),
        ("Declining", "Strong", 1352, 2421, 22.6, 49.8),
    ],
    "target_bucket": [
        ("0", "Weak", 186, 19.3, 77.4, 17.2),
        ("0", "Mid", 259, 26.6, 70.3, 24.3),
        ("0", "Strong", 278, 34.8, 62.9, 33.5),
        ("1-2", "Weak", 1935, 26.7, 65.0, 18.4),
        ("1-2", "Mid", 3893, 27.4, 63.6, 18.3),
        ("1-2", "Strong", 4253, 32.5, 57.4, 22.5),
        ("3-5", "Weak", 2562, 39.3, 47.0, 25.7),
        ("3-5", "Mid", 6395, 41.4, 45.1, 28.0),
        ("3-5", "Strong", 10426, 44.8, 41.2, 31.0),
        ("6-10", "Weak", 980, 58.9, 26.6, 44.6),
        ("6-10", "Mid", 2733, 59.0, 27.0, 45.0),
        ("6-10", "Strong", 5379, 62.9, 22.8, 49.0),
        ("11+", "Weak", 229, 71.7, 14.8, 54.6),
        ("11+", "Mid", 695, 72.5, 11.9, 55.8),
        ("11+", "Strong", 1428, 77.2, 10.4, 64.2),
    ],
    "ratio_bucket": [("0-25%", 4297, 6.1, 29.7), ("25-50%", 10825, 9.8, 35.9), ("50-75%", 20091, 13.8, 35.8), ("75-100%+", 1557, 8.4, 18.8)],
    "seasonal": [("Non-seasonal", 29298, 37815, 9.3, 30.8), ("Seasonal", 7472, 10939, 18.8, 45.3)],
    "loop_bucket": [("None", 36534, 11.4, 34.0), ("1", 65, 0.0, 2.5), ("2-3", 60, 4.0, 36.4), ("4+", 111, 28.3, 62.0)],
    "phantom": [("Phantom=1", 115, 84.9, 79.9), ("Phantom=0", 36655, 11.2, 33.9)],
    "pair_outcomes": [("Win-Lose", 17409), ("Win-Win", 13243), ("Lose-Lose", 11078), ("Lose-Win", 674)],
    "concentration_target": [("<10%", 12.5, 85.7, 10.7), ("10-25%", 20.0, 71.0, 11.2), ("25-50%", 30.3, 59.6, 20.3), ("50%+", 46.4, 40.9, 33.7)],
    "source_lookup": [("Dead", [1, 1, 1]), ("Dying", [1, 1, 2]), ("Sporadic", [1, 2, 2]), ("Consistent", [2, 3, 4]), ("Declining", [2, 2, 3])],
    "target_lookup": [("0", [1, 1, 1]), ("1-2", [1, 1, 2]), ("3-5", [1, 2, 2]), ("6-10", [2, 2, 3]), ("11+", [2, 3, 3])],
    "source_backtest": [("UP", 11833, 16812, 2955, 7616, -13537), ("DOWN", 6030, 8909, 470, 1114, 6387), ("SAME", 18907, 23033, 2153, 7885, 0)],
    "target_backtest": [("UP", 12146, 13611, 80.3, 0.1, 59.9, 12345), ("DOWN", 21142, 25350, 22.0, 71.7, 16.1, -23299), ("SAME", 8343, 9793, 53.2, 28.5, 35.4, 0)],
    "sensitivity_source": [("Source -1", 932), ("Source Base", -7150), ("Source +1", -27659)],
    "sensitivity_target": [("Target -1", -27236), ("Target Base", -10954), ("Target +1", 11706)],
    "source_up_top": [("Sporadic / Strong", 3791, 5207, -4363), ("Sporadic / Mid", 3389, 4423, -3794), ("Declining / Strong", 1183, 2097, -1569), ("Sporadic / Weak", 1190, 1513, -1221)],
    "target_down_top": [("3-5 / Strong", 5079, 5674, -5380), ("3-5 / Mid", 3380, 3887, -3630), ("1-2 / Mid", 2984, 3279, -3098), ("1-2 / Strong", 2436, 2665, -2577)],
    "target_up_top": [("3-5 / Strong", 4613, 4961, 4613), ("6-10 / Strong", 3344, 3830, 3512), ("1-2 / Strong", 1294, 1365, 1294), ("3-5 / Mid", 996, 1069, 996)],
}


def table(headers, rows):
    thead = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def page(title, intro, sections):
    nav = '<nav><a href="consolidated_findings.html">Findings</a><a href="consolidated_decision_tree.html">Decision tree</a><a href="consolidated_backtest.html">Backtest</a></nav>'
    body = "".join(f"<section><h2>{html.escape(h)}</h2>{content}</section>" for h, content in sections)
    return f'''<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
:root {{--bg:#f5f1e8;--panel:#fffaf2;--ink:#1f2421;--muted:#5f665f;--line:#d8cfbf;--accent:#9f4f2f;--accent2:#2c6e62;}}
body {{margin:0;font-family:Georgia,"Times New Roman",serif;background:radial-gradient(circle at top left,#fff7ea,var(--bg) 55%);color:var(--ink);}}
.wrap {{max-width:1180px;margin:0 auto;padding:28px 20px 40px;}}
nav {{display:flex;gap:14px;margin-bottom:22px;font-size:15px;}}
nav a {{color:var(--accent);text-decoration:none;}}
header {{background:linear-gradient(135deg,rgba(159,79,47,.12),rgba(44,110,98,.08));border:1px solid var(--line);border-radius:18px;padding:24px;margin-bottom:22px;}}
h1 {{font-size:38px;line-height:1.05;letter-spacing:-.02em;margin:0 0 12px;}}
h2,h3 {{margin:0 0 12px;}} p,li {{line-height:1.55;color:var(--muted);font-size:16px;}}
section {{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 18px 20px;margin-bottom:18px;box-shadow:0 8px 24px rgba(40,32,18,.04);}}
.grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px;}}
table {{width:100%;border-collapse:collapse;font-size:14px;background:white;}}
th,td {{padding:9px 10px;border-bottom:1px solid #eee7db;text-align:left;}}
th {{background:#f2e9da;color:#443b34;}}
img {{width:100%;border-radius:12px;border:1px solid var(--line);background:white;}}
.callout {{padding:12px 14px;border-left:4px solid var(--accent2);background:rgba(44,110,98,.08);margin:8px 0 0;}}
</style>
</head>
<body><div class="wrap">{nav}<header><h1>{html.escape(title)}</h1><p>{html.escape(intro)}</p></header>{body}</div></body></html>'''


def save(fig, name):
    fig.savefig(BASE_DIR / name)
    plt.close(fig)
    return name


def matrix(rows, row_order, col_order, idx):
    out = np.zeros((len(row_order), len(col_order)))
    for item in rows:
        out[row_order.index(item[0]), col_order.index(item[1])] = item[idx]
    return out


def plot_findings():
    files = []
    patterns = ["Dead", "Dying", "Sporadic", "Consistent", "Declining"]
    stores = ["Weak", "Mid", "Strong"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.heatmap(matrix(DATA["source_pattern"], patterns, stores, 5), annot=True, fmt=".1f", cmap="YlOrBr", xticklabels=stores, yticklabels=patterns, ax=axes[0])
    axes[0].set_title("Source RO Tot Qty%")
    sns.heatmap(matrix(DATA["source_pattern"], patterns, stores, 4), annot=True, fmt=".1f", cmap="Reds", xticklabels=stores, yticklabels=patterns, ax=axes[1])
    axes[1].set_title("Source OS Tot Qty%")
    files.append(save(fig, "fig_findings_01.png"))

    buckets = ["0", "1-2", "3-5", "6-10", "11+"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.heatmap(matrix(DATA["target_bucket"], buckets, stores, 3), annot=True, fmt=".1f", cmap="crest", xticklabels=stores, yticklabels=buckets, ax=axes[0])
    axes[0].set_title("Target ST 4M")
    sns.heatmap(matrix(DATA["target_bucket"], buckets, stores, 4), annot=True, fmt=".1f", cmap="rocket_r", xticklabels=stores, yticklabels=buckets, ax=axes[1])
    axes[1].set_title("Target Nothing-sold 4M")
    files.append(save(fig, "fig_findings_02.png"))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    labels = [x[0] for x in DATA["ratio_bucket"]]
    x = np.arange(len(labels))
    axes[0].bar(x - 0.18, [x[2] for x in DATA["ratio_bucket"]], 0.36, label="OS Tot Qty%", color="#c95d3a")
    axes[0].bar(x + 0.18, [x[3] for x in DATA["ratio_bucket"]], 0.36, label="RO Tot Qty%", color="#466c67")
    axes[0].set_xticks(x, labels)
    axes[0].set_title("RedistributionRatio")
    axes[0].legend()
    s_labels = [x[0] for x in DATA["seasonal"]]
    x2 = np.arange(len(s_labels))
    axes[1].bar(x2 - 0.18, [x[3] for x in DATA["seasonal"]], 0.36, label="OS Tot Qty%", color="#c95d3a")
    axes[1].bar(x2 + 0.18, [x[4] for x in DATA["seasonal"]], 0.36, label="RO Tot Qty%", color="#466c67")
    axes[1].set_xticks(x2, s_labels)
    axes[1].set_title("Seasonality")
    axes[1].legend()
    files.append(save(fig, "fig_findings_03.png"))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    axes[0].bar([x[0] for x in DATA["pair_outcomes"]], [x[1] for x in DATA["pair_outcomes"]], color=["#b55d3f", "#2c6e62", "#834a9b", "#d1a34a"])
    axes[0].set_title("Pair outcomes 4M")
    axes[1].bar([x[0] for x in DATA["loop_bucket"]], [x[2] for x in DATA["loop_bucket"]], color="#9f4f2f")
    axes[1].set_title("Loop vs OS Tot Qty%")
    axes[2].bar([x[0] for x in DATA["phantom"]], [x[2] for x in DATA["phantom"]], color=["#a02d2d", "#cbbba2"])
    axes[2].set_title("Phantom stock vs OS Tot Qty%")
    files.append(save(fig, "fig_findings_04.png"))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    conc = [x[0] for x in DATA["concentration_target"]]
    axes[0].plot(conc, [x[1] for x in DATA["concentration_target"]], marker="o", linewidth=2.5, color="#2c6e62")
    axes[0].set_title("Target ST 4M podle concentration")
    axes[1].plot(conc, [x[2] for x in DATA["concentration_target"]], marker="o", linewidth=2.5, color="#9f4f2f")
    axes[1].set_title("Target Nothing-sold 4M podle concentration")
    files.append(save(fig, "fig_findings_05.png"))
    return files


def plot_decision():
    files = []
    stores = ["Weak", "Mid", "Strong"]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    sns.heatmap(np.array([x[1] for x in DATA["source_lookup"]], dtype=float), annot=True, fmt=".0f", cmap="YlOrRd", xticklabels=stores, yticklabels=[x[0] for x in DATA["source_lookup"]], ax=ax)
    ax.set_title("Source base lookup")
    files.append(save(fig, "fig_dtree_01.png"))
    fig, ax = plt.subplots(figsize=(7, 4.8))
    sns.heatmap(np.array([x[1] for x in DATA["target_lookup"]], dtype=float), annot=True, fmt=".0f", cmap="crest", xticklabels=stores, yticklabels=[x[0] for x in DATA["target_lookup"]], ax=ax)
    ax.set_title("Target base lookup")
    files.append(save(fig, "fig_dtree_02.png"))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5))
    axes[0].bar([x[0] for x in DATA["source_backtest"]], [x[5] for x in DATA["source_backtest"]], color=["#9f4f2f", "#2c6e62", "#bfb29a"])
    axes[0].axhline(0, color="#333", linewidth=1)
    axes[0].set_title("Source estimated qty change")
    axes[1].bar([x[0] for x in DATA["target_backtest"]], [x[6] for x in DATA["target_backtest"]], color=["#2c6e62", "#9f4f2f", "#bfb29a"])
    axes[1].axhline(0, color="#333", linewidth=1)
    axes[1].set_title("Target estimated qty change")
    files.append(save(fig, "fig_dtree_03.png"))
    return files


def plot_backtest():
    files = []
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].barh([x[0] for x in DATA["source_up_top"]], [abs(x[3]) for x in DATA["source_up_top"]], color="#9f4f2f")
    axes[0].set_title("Top source UP segments")
    axes[1].barh([x[0] for x in DATA["target_down_top"]], [abs(x[3]) for x in DATA["target_down_top"]], color="#466c67")
    axes[1].set_title("Top target DOWN segments")
    files.append(save(fig, "fig_backtest_01.png"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].barh([x[0] for x in DATA["target_up_top"]], [x[3] for x in DATA["target_up_top"]], color="#2c6e62")
    axes[0].set_title("Top target UP segments")
    src_dirs = [x[0] for x in DATA["source_backtest"]]
    src_qty = [x[2] for x in DATA["source_backtest"]]
    src_os = [x[3] for x in DATA["source_backtest"]]
    axes[1].scatter(src_qty, src_os, s=[max(v / 10, 40) for v in src_qty], c=["#9f4f2f", "#2c6e62", "#c5b59b"])
    for label, x, y in zip(src_dirs, src_qty, src_os):
        axes[1].annotate(label, (x, y), textcoords="offset points", xytext=(5, 5))
    axes[1].set_xlabel("Qty")
    axes[1].set_ylabel("OS Tot Qty")
    axes[1].set_title("Source direction map")
    files.append(save(fig, "fig_backtest_02.png"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot([x[0] for x in DATA["sensitivity_source"]], [x[1] for x in DATA["sensitivity_source"]], marker="o", linewidth=2.5, color="#9f4f2f")
    axes[0].axhline(0, color="#333", linewidth=1)
    axes[0].set_title("Source sensitivity")
    axes[1].plot([x[0] for x in DATA["sensitivity_target"]], [x[1] for x in DATA["sensitivity_target"]], marker="o", linewidth=2.5, color="#2c6e62")
    axes[1].axhline(0, color="#333", linewidth=1)
    axes[1].set_title("Target sensitivity")
    files.append(save(fig, "fig_backtest_03.png"))
    return files


def findings_html(figs):
    sections = [
        ("Validace a overview", f'<div class="grid"><div>{table(["Kontrola", "Vysledek"], DATA["validation"])}</div><div><h3>Source</h3>{table(["Metrika", "4M SKU", "4M Qty", "Total SKU", "Total Qty"], DATA["overview_source"])}<h3 style="margin-top:14px;">Target</h3>{table(["Metrika", "4M", "Total"], DATA["overview_target"])}<p class="callout">Vstup je cisty. Jedina zvlastnost jsou source JSON NULL pripady s aktualnim ML=0.</p></div></div>'),
        ("Segmentace source a target", f'<div class="grid"><div>{table(["Pattern", "Store", "SKU", "Qty", "OS Tot Qty%", "RO Tot Qty%"], DATA["source_pattern"])}</div><div>{table(["SalesBucket", "Store", "SKU", "Avg ST 4M", "Nothing-sold 4M", "All-sold 4M"], DATA["target_bucket"])}</div></div><div class="grid"><div><img src="{figs[0]}" alt="source"></div><div><img src="{figs[1]}" alt="target"></div></div>'),
        ("Cross-product a outcome", f'<div class="grid"><div>{table(["Ratio", "SKU", "OS Tot Qty%", "RO Tot Qty%"], DATA["ratio_bucket"])}</div><div>{table(["Outcome", "Pairs"], DATA["pair_outcomes"])}</div></div><div class="grid"><div><img src="{figs[2]}" alt="ratio"></div><div><img src="{figs[3]}" alt="pair"></div></div><p class="callout">Nejvetsi opportunity je presun objemu: od Win-Lose transferu k growth pockets, kde target potvrzuje vysokou absorpci a model uz neni netto silne defenzivni.</p><img src="{figs[4]}" alt="concentration">'),
    ]
    return page("Findings v5", "Kompletni v5 findings nad novou SBM_v5 vrstvou a bez prevzeti predchozi analyticke logiky.", sections)


def decision_html(figs):
    source_mods = [("LastSaleGap short", "LastSaleGapDays <= 30", "+1"), ("RedistributionRatio high", "RedistributionRatio >= 0.75", "+1"), ("Seasonal", "XmasLift >= 20%", "+1"), ("Product concentration low", "ProductConcentrationShare < 10%", "+1"), ("Phantom stock", "PhantomStockFlag = 1", "-1"), ("Deep inactivity", "LastSaleGapDays >= 365 a SalesQty12MPre = 0", "-1"), ("Became delisted", "SkuClass -> D/L", "ML=0")]
    target_mods = [("All-sold / ST-1pc high", "AllSold4M = 1 nebo ST1_4M >= 90%", "+1"), ("Nothing-sold / very low ST", "NothingSold4M = 1 nebo ST4M < 25%", "-1"), ("Brand-store mismatch", "BrandStoreMismatch = 1", "-1"), ("Very low concentration", "ProductConcentrationShare < 10%", "-1"), ("Became delisted", "SkuClass -> D/L", "ML=0")]
    sections = [
        ("Base lookup", f'<div class="grid"><div><h3>Source</h3>{table(["Pattern", "Weak", "Mid", "Strong"], [(x[0], *x[1]) for x in DATA["source_lookup"]])}<img src="{figs[0]}" alt="source lookup"></div><div><h3>Target</h3>{table(["SalesBucket", "Weak", "Mid", "Strong"], [(x[0], *x[1]) for x in DATA["target_lookup"]])}<img src="{figs[1]}" alt="target lookup"></div></div>'),
        ("Modifikatory", f'<div class="grid"><div>{table(["Modifikator", "Podminka", "Uprava"], source_mods)}</div><div>{table(["Modifikator", "Podminka", "Uprava"], target_mods)}</div></div><p class="callout">Lookup urcuje zaklad. Realny ProposedML ve v5 vznikne az po modifikatorech a clamp pravidlech 0-4.</p>'),
        ("Smery zasahu", f'<img src="{figs[2]}" alt="directions"><ul><li><strong>Source UP</strong> miri hlavne na Sporadic/Strong, Sporadic/Mid a Declining/Strong.</li><li><strong>Source DOWN</strong> zustava omezeny na nizkorizikove a neaktivni skupiny.</li><li><strong>Target DOWN</strong> je zamerne sirsi, protoze tam lezi nejvetsi objem Win-Lose redistribuci.</li><li><strong>Target UP</strong> se drzi jen u segmentu s vysokym ST nebo ST-1pc.</li></ul>'),
    ]
    return page("Decision tree v5", "Decision tree v5 pouziva samostatny source a target lookup, pak modifikatory a nakonec tvrde clamp podminky. Cilem je realokovat objem mezi reduction pockets a growth pockets.", sections)


def backtest_html(figs):
    sens = DATA["sensitivity_source"] + DATA["sensitivity_target"]
    sections = [
        ("Source a target dopad", f'<div class="grid"><div>{table(["Smer", "SKU", "Qty", "OS Tot", "RO Tot", "Odhad qty change"], DATA["source_backtest"])}<p class="callout">Net source dopad: -8 594 ks, ale zaroven odemyka nove source growth pockets.</p></div><div>{table(["Smer", "SKU", "Qty", "Avg ST 4M", "Nothing-sold 4M", "All-sold 4M", "Odhad qty change"], DATA["target_backtest"])}<p class="callout">Net target dopad: -416 ks, tedy skoro neutralni target strana s velkym UP i DOWN ramenem.</p></div></div>'),
        ("Top segmenty", f'<div class="grid"><div><img src="{figs[0]}" alt="top down"></div><div><img src="{figs[1]}" alt="up and map"></div></div>'),
        ("Sensitivity", f'<div class="grid"><div>{table(["Scenar", "Odhad qty change"], sens)}</div><div><img src="{figs[2]}" alt="sensitivity"></div></div><p class="callout">Base v5 je stredni varianta. Plosny posun o jeden level na kterekoli strane uz vede k mnohem agresivnejsimu objemovemu zasahu.</p>'),
    ]
    return page("Backtest v5", "Backtest v5 je objemovy odhad po SKU podle zmeny ML levelu proti aktualnimu EntityList ML. Cte se obousmerne: kde ubrat i kde pridat, s temer neutralnim target netto dopadem.", sections)


def main():
    findings = plot_findings()
    decision = plot_decision()
    backtest = plot_backtest()
    (BASE_DIR / "consolidated_findings.html").write_text(findings_html(findings), encoding="utf-8")
    (BASE_DIR / "consolidated_decision_tree.html").write_text(decision_html(decision), encoding="utf-8")
    (BASE_DIR / "consolidated_backtest.html").write_text(backtest_html(backtest), encoding="utf-8")


if __name__ == "__main__":
    main()


