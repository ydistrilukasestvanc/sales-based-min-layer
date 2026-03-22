# Popis výstupů analýzy SalesBased MinLayers

## CalculationId=233, EntityListId=3, Referenční datum: 2025-07-13

---

## Soubory a jejich účel

### Zadání a plán
| Soubor | Účel |
|---|---|
| `zadani.md` | Původní zadání od uživatele |
| `structured_assignment.md` | Strukturované zadání s logem zjištění, temp tabulkami, postupem |
| `outputs_description.md` | Tento soubor – popis všech výstupů |

### Python skripty (generátory reportů)
| Soubor | Co generuje | Kdy spustit znovu |
|---|---|---|
| `generate_full_report.py` | `reports/full_analysis_report.html` + fig01-05 | Po změně základních metrik |
| `generate_combined_report.py` | `reports/combined_segmentation_report.html` + fig06-09 | Po změně segmentace |
| `analysis_decision_tree.py` | `reports/decision_tree_report.html` + fig10-13 | Po změně pravidel |
| `analysis_extended.py` | `reports/extended_analysis_report.html` + fig14+ | Nové analýzy (loop, páry, backtest...) |

### HTML reporty
| Report | Obsah | Klíčová zjištění |
|---|---|---|
| `full_analysis_report.html` | 10 sekcí: MinLayer distribuce, store decile, zero-sellers, redistr. ratio, SkuClass, cena, trend, stockout, timing, inbound typy | Source reorder 37.6%, lineární závislost na store decile, bimodální reorder (all-or-nothing) |
| `combined_segmentation_report.html` | Kombinované heatmapy (MinLayer × Sales × Store), brand-store fit, decision tree vizualizace | Brand-store fit = 16pp rozdíl, kritické segmenty identifikovány |
| `decision_tree_report.html` | Prodejní vzorce (24M), navržená pravidla Source (0-5) i Target (0-5) | Declining vzorec = 65% reorder, Source≠Target pravidla |
| `extended_analysis_report.html` | Redistribuční smyčka, párová analýza, backtest, měsíční kadence, product concentration | TBD |

### Grafy (PNG)
| Graf | Co ukazuje |
|---|---|
| fig01 | Source reorder: SKU% vs QTY% + rozložení míry reorderu per MinLayer3 |
| fig02 | Store decile vs reorder/oversell (source) a all-sold/nothing-sold (target) |
| fig03 | Decile flow heatmap: z jakého decilu do jakého posíláme |
| fig04 | Zero-sellers: co se stalo po redistribuci + reorder rate |
| fig05 | Redistribuční ratio (% zásoby odvezeno) vs reorder |
| fig06 | Kombinovaná source heatmapa: MinLayer1 × Sales × Store |
| fig07 | Kombinovaná target heatmapa: MinLayer2 × Sales × Store |
| fig08 | Brand-store fit vs reorder |
| fig09 | Decision tree vizualizace (schéma) |
| fig10 | Prodejní vzorce (24M) × Store heatmapa |
| fig11 | Navrhovaný Source MinLayer matice |
| fig12 | Navrhovaný Target MinLayer matice |
| fig13 | Doba od posledního prodeje vs reorder |
| fig14+ | Rozšířené analýzy (TBD) |

### Temp tabulky v DB (prefix SBM_)
Viz `structured_assignment.md` sekce "Vytvořené temp tabulky".

---

## Jak reprodukovat analýzu pro jinou kalkulaci

1. Změnit CalculationId v SQL dotazech (aktuálně 233)
2. Změnit EntityListId v JSON extrakci (aktuálně "3")
3. Přepočítat referenční datum (ApplicationDate z tabulky Calculation)
4. Dropnout a znovu vytvořit temp.SBM_* tabulky
5. Spustit Python skripty v pořadí: generate_full_report → generate_combined_report → analysis_decision_tree → analysis_extended
