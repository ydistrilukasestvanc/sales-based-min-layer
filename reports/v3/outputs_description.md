# Popis vystupu analyzy SalesBased MinLayers v3

## CalculationId=233, EntityListId=3, Referencni datum: 2025-07-13

---

## Soubory a jejich ucel

### Zadani a plan
| Soubor | Ucel |
|---|---|
| `zadani.md` | Puvodni zadani od uzivatele |
| `structured_assignment.md` | Strukturovane zadani s instrukcemi, temp tabulkami, postupem |
| `outputs_description.md` | Tento soubor - popis vsech vystupu |

### Python skripty (generatory reportu)
| Soubor | Co generuje | Verze |
|---|---|---|
| `reports/v3/generate_consolidated_reports.py` | Vsechny 3 HTML reporty + 21 grafu | v3 Advanced |

### HTML reporty (3 konsolidovane)
| Report | Obsah | Klicova zjisteni |
|---|---|---|
| `consolidated_findings.html` | Kompletni analytika: 17 sekci vcetne 8 NOVYCH (phantom stock source-only + cross-store filter, volatilita, flow matice, last-sale-gap, redist ratio, cenova dynamika, SkuClass prechody, combined scoring) | 5 novych faktoru s dopadem +8-19pp na oversell |
| `consolidated_decision_tree.html` | Source (0-5) + Target (0-5) lookup tables, 4-direction framework, 7 NOVYCH modifikatoru, combined scoring model, pseudocode | v3: 10 source modifikatoru, 9 target modifikatoru |
| `consolidated_backtest.html` | Dopad pravidel: volume waterfall, segment scatter, NOVA sensitivity analyza (ML+-2), NOVY before/after comparison, doporuceni | Navrzena pravidla snizi oversell o 5-13pp v 6 rizikovych segmentech |

### Grafy (PNG) - Report 1: Findings
| Graf | Co ukazuje | Status |
|---|---|---|
| fig_findings_01 | Source: Reorder vs Oversell dual heatmap (Pattern x Store) | v2 |
| fig_findings_02 | Store decile: reorder + oversell (source) + all-sold/nothing-sold (target) + efficiency | Enhanced v3 |
| fig_findings_03 | Target: ST 4M + nothing-sold + all-sold heatmaps (Store x Sales) | v2 |
| fig_findings_04 | Target: brand-fit + price + concentration bar charts | v2 |
| fig_findings_05 | **NEW: Phantom Stock analysis** (source only, cross-store filtered) | NEW v3 |
| fig_findings_06 | **NEW: Product Volatility + Last Sale Gap** | NEW v3 |
| fig_findings_07 | **NEW: Flow Matrix heatmaps** (pairs, oversell, double-fail) | NEW v3 |
| fig_findings_08 | **NEW: Redistribution Ratio + Price Change** | NEW v3 |
| fig_findings_09 | **NEW: SkuClass Transition analysis** (source + target) | NEW v3 |
| fig_findings_10 | **NEW: Combined Score + Monthly Cadence** | NEW v3 |

### Grafy (PNG) - Report 2: Decision Tree
| Graf | Co ukazuje | Status |
|---|---|---|
| fig_dtree_01 | Source ML lookup matrix (Pattern x Store) | v2 |
| fig_dtree_02 | Target ML lookup matrix (Sales x Store) | v2 |
| fig_dtree_03 | 4-direction decision diagram (updated with v3 modifiers) | Enhanced v3 |
| fig_dtree_04 | **NEW: Modifier impact waterfall** (source + target) | NEW v3 |
| fig_dtree_05 | **NEW: Combined Score vs Proposed ML** scatter/line | NEW v3 |

### Grafy (PNG) - Report 3: Backtest
| Graf | Co ukazuje | Status |
|---|---|---|
| fig_backtest_01 | Source: volume impact + oversell prevented per segment | v2 |
| fig_backtest_02 | Target: received vs sold + extra pcs for 1-remains | v2 |
| fig_backtest_03 | Combined: volume waterfall + opportunity map | v2 |
| fig_backtest_04 | Source: segment scatter (oversell vs volume reduction) | v2 |
| fig_backtest_05 | **NEW: Sensitivity analysis** (ML+-2 impact on all metrics) | NEW v3 |
| fig_backtest_06 | **NEW: Before/After oversell comparison** per segment | NEW v3 |

### Dokumentace
| Soubor | Ucel |
|---|---|
| `findings.md` | Kompletni zjisteni v3 vcetne vsech novych analyz |
| `outputs_description.md` | Tento soubor |

---

## Nove analyzy v v3 (oproti v2)

| # | Analyza | Phase | Klicovy finding |
|---|---|---|---|
| 1 | Phantom Stock (source only, cross-store filtered) | Phase 4 | 1,800 confirmed phantom SKU (4.9%), oversell=28.5% (+19pp vs normal). Cross-store filter: pattern jen na tomto SKU, ne product-wide. Target se netyká. |
| 2 | Product Volatility (CV) | Phase 2 | CV>2.0 = +13.1pp oversell, +13.2pp nothing-sold |
| 3 | Flow Matrix (decile->decile) | Phase 3 | Strong->Weak = 10.6% double fail; Weak->Strong = 2.8% |
| 4 | Last Sale Gap | Additional | 0-30d gap = 28.7% oversell vs 365+d = 5.9% |
| 5 | Redistribution Ratio | Additional | 75-100% ratio = 24.8% oversell vs <25% = 6.4% |
| 6 | Price Dynamics | Phase 5 | Price decrease >10% = +8.4pp oversell (source), +5pp all-sold (target) |
| 7 | SkuClass Transitions | Phase 6b | A-O -> D/L = -11.1pp oversell; full transition matrix |
| 8 | Sensitivity Analysis | Backtest | Each ML step = ~6pp oversell change, ~3-5k blocked SKU |
| 9 | Combined Scoring Model | Decision Tree | 0-100 score, 6.5x difference in oversell between extremes |
| 10 | Before/After Comparison | Backtest | Proposed rules reduce oversell by 5-13pp in 6 risky segments |

---

## Jak reprodukovat analyzu

1. Zmenit CalculationId v SQL (aktualne 233)
2. Zmenit EntityListId v JSON extrakci (aktualne "3")
3. Prepocitat referencni datum (ApplicationDate z tabulky Calculation)
4. Dropnout a znovu vytvorit temp.SBM_* tabulky
5. Spustit: `python reports/v3/generate_consolidated_reports.py`
