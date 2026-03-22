# Decision Tree v4 — Source & Target MinLayer pravidla

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML rozsah:** 0-4 | **Orderable (A-O, Z-O) → min ML=1**

---

## Stav metrik

| Metrika | 4M Qty% | Total Qty% | Stav |
|---|---|---|---|
| **Oversell** | 3.0% | 11.4% | V cíli (5-10% / <20%) |
| **Reorder** | 16.4% | 34.1% | Cíl: snížit o 10-15% |

---

## SOURCE: Pattern × Store Strength → ML (0-4)

| Pattern | Weak | Mid | Strong | RO Tot Qty% | Důvod |
|---|---|---|---|---|---|
| **Consistent** | 3 | 4 | 4 | 44-52% | Nejvyšší reorder. Max ochrana. |
| **Declining** | 3 | 3 | 4 | 61-74% | Velmi vysoký reorder. |
| **Sporadic** | 2 | 2 | 3 | 35-43% | Mid reorder. Strong potřebuje víc. |
| **Dying** | 1 | 1 | 2 | 27-34% | Nízký reorder. Strong mírně zvýšit. |
| **Dead** | 1 | 1 | 1 | 22-29% | Nejnižší reorder. |

> Orderable (A-O, Z-O) → min ML=1. Pouze non-orderable/delisted může ML=0.

### Modifikátory

| Modifikátor | Podmínka | Úprava | Důvod |
|---|---|---|---|
| Sezónnost | XmasLift ≥ 20% | +1 | RO 45.3% vs 30.8% |
| Nízká volatilita | CV < 1 | +1 | RO 39.4% |
| Delisting | SkuClass → D/L | ML=0 | RO jen 10.9% |

---

## TARGET: Sales Bucket × Store Strength → ML (0-4)

| Sales 12M | Weak | Mid | Strong |
|---|---|---|---|
| **0** | 1 | 1 | 2 |
| **1-2** | 1 | 2 | 2 |
| **3-5** | 2 | 2 | 2 |
| **6-10** | 2 | 2 | 2 |
| **11+** | 3 | 3 | 3 |

### Modifikátory

| Modifikátor | Podmínka | Úprava |
|---|---|---|
| Brand-store mismatch | BrandWeak+StoreWeak | -1 |
| Delisting | SkuClass → D/L | ML=0 |
| All-sold trend | ≥70% prodejen | +1 |

---

## Souhrn dopadu

| Směr | SKU | Redist Qty | RO Tot Qty | RO Tot SKU% |
|---|---|---|---|---|
| **Source ML UP** | 15 435 | 21 688 | 9 038 | 47.3% |
| **Source ML DOWN** | 310 | 506 | 99 | 10.0% |
| Source beze změny | 21 025 | 26 560 | 7 478 | 31.0% |
