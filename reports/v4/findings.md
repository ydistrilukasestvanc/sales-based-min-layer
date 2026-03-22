# Findings v4 — SalesBased MinLayers Analytika

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13 | **ML rozsah:** 0-4
**Orderable (A-O, Z-O) → min ML=1**

---

## 1. Přehled dat

| Parametr | Hodnota |
|---|---|
| Redistribučních párů | 42 404 |
| Redistribuovaných ks | 48 754 |
| Source SKU | 36 770 |
| Target SKU | 41 631 |
| Produktů | 5 152 |
| Prodejen | 352 (107 Weak / 140 Mid / 105 Strong) |

---

## 2. Základní metriky

### SOURCE (36 770 SKU, 48 754 ks redistribuováno)

| Metrika | 4M SKU (%) | 4M Qty (%) | Total SKU (%) | Total Qty (%) |
|---|---|---|---|---|
| **Oversell** | 1 317 (3.6%) | 1 464 (3.0%) | 4 718 (12.8%) | 5 578 (11.4%) |
| **Reorder** | 7 087 (19.3%) | 7 980 (16.4%) | 13 841 (37.6%) | 16 615 (34.1%) |

Oversell 4M = 3.0% — **v cíli** (target 5-10%). Reorder total = 34.1% qty — **cíl snížit o 10-15%.**

### TARGET (41 631 SKU, 48 754 ks přijato)

| Metrika | 4M | Total |
|---|---|---|
| **Avg Sell-Through** | 45.3% | 69.2% |
| **Avg ST-1pc** | 58.2% | 79.6% |
| **Nothing-sold** | 17 552 (42.2%) | 8 872 (21.3%) |
| **All-sold** | 13 631 (32.7%) | 24 862 (59.7%) |

---

## 3. Prodejní vzorce × Store Strength

| Pattern | Store | SKU | Redist | OS 4M% | OS Tot% | RO 4M% | RO Tot% |
|---|---|---|---|---|---|---|---|
| Dead | Weak | 4 557 | 5 418 | 1.0 | 4.6 | 10.1 | 22.4 |
| Dead | Mid | 6 884 | 8 533 | 1.6 | 6.9 | 12.0 | 26.9 |
| Dead | Strong | 4 012 | 5 086 | 2.7 | 9.4 | 13.1 | 28.7 |
| Dying | Weak | 1 634 | 1 976 | 2.2 | 6.9 | 12.7 | 26.7 |
| Dying | Mid | 2 965 | 3 605 | 2.3 | 8.8 | 14.9 | 31.5 |
| Dying | Strong | 2 000 | 2 430 | 3.1 | 11.1 | 15.9 | 33.6 |
| Sporadic | Weak | 2 559 | 3 389 | 2.1 | 10.0 | 16.7 | 34.8 |
| Sporadic | Mid | 5 606 | 7 848 | 4.1 | 14.4 | 21.2 | 40.9 |
| Sporadic | Strong | 5 480 | 8 347 | 4.5 | 17.9 | 21.1 | 43.3 |
| Consistent | Weak | 31 | 62 | 0.0 | 21.0 | 17.7 | 43.5 |
| Consistent | Mid | 162 | 404 | 7.2 | 23.0 | 21.3 | 52.2 |
| Consistent | Strong | 516 | 1 159 | 8.2 | 26.8 | 26.1 | 51.1 |
| Declining | Weak | 63 | 90 | 11.1 | 41.1 | 32.2 | 67.8 |
| Declining | Mid | 141 | 189 | 9.5 | 31.7 | 37.0 | 74.1 |
| Declining | Strong | 160 | 218 | 9.2 | 27.1 | 33.9 | 61.0 |

**Klíčové:** Consistent/Declining mají reorder 43-74%. Sporadic/Mid-Strong 40-43%. Dead/Weak jen 22%.

---

## 4. Cross-product

### Redistribuční ratio

| Ratio | SKU | OS 4M% | OS Tot% | RO 4M% | RO Tot% | RO Tot SKU% |
|---|---|---|---|---|---|---|
| 0-25% | 7 304 | 1.4 | 7.4 | 13.3 | 32.8 | 35.1 |
| 25-50% | 24 490 | 3.4 | 12.6 | 18.4 | 36.8 | 38.9 |
| 50-75% | 3 774 | 3.7 | 12.9 | 15.1 | 31.4 | 42.8 |
| 75-100% | 1 202 | 1.8 | 4.9 | 5.4 | 11.4 | 10.7 |

### Product Volatility

| Volatilita | SKU | OS 4M% | OS Tot% | RO 4M% | RO Tot% |
|---|---|---|---|---|---|
| Low (<1) | 19 366 | 3.7 | 14.0 | 19.1 | 39.4 |
| Med (1-2) | 17 163 | 2.1 | 8.1 | 12.9 | 27.3 |
| High (2-3) | 114 | 0.7 | 2.0 | 2.7 | 7.4 |
| VHigh (3+) | 65 | 0.0 | 1.5 | 4.4 | 10.3 |

---

## 5. Sezónnost

| Flag | SKU | OS 4M% | OS Tot% | RO 4M% | RO Tot% | RO Tot SKU% |
|---|---|---|---|---|---|---|
| Non-seasonal | 29 298 | 2.3 | 9.3 | 14.4 | 30.8 | 33.9 |
| Seasonal | 7 472 | 5.3 | 18.8 | 23.1 | 45.3 | 52.2 |

Sezónní: 2× vyšší oversell i reorder.

---

## 6. Redistribuční smyčka

| Transfery | SKU | OS 4M% | OS Tot% | RO 4M% | RO Tot% |
|---|---|---|---|---|---|
| Žádný | 35 599 | 3.0 | 11.4 | 16.4 | 34.1 |
| 1 | 1 014 | 3.6 | 12.0 | 16.1 | 33.5 |
| 2 | 132 | 2.3 | 8.7 | 14.2 | 40.2 |
| 3+ | 25 | 1.3 | 7.9 | 10.5 | 34.2 |

---

## 7. SkuClass změny

| Změna | SKU | OS Tot% | RO Tot% | RO Tot SKU% |
|---|---|---|---|---|
| Unchanged | 29 322 | 13.0 | 39.8 | 43.2 |
| Delisted | 6 049 | 4.9 | 10.9 | 13.2 |
| Other | 1 399 | 10.1 | 26.3 | 27.2 |

---

## 8. Párová analýza (opravený oversell)

| Outcome | Pairs | % |
|---|---|---|
| **Win-Win** (no oversell + good ST) | 28 179 | 66.5% |
| **Win-Lose** (no oversell + bad ST) | 8 565 | 20.2% |
| **Lose-Win** (oversell + good ST) | 4 794 | 11.3% |
| **Lose-Lose** | 866 | 2.0% |

66.5% párů je Win-Win. Hlavní příležitost: Win-Lose (20.2%) — target neprodá.
