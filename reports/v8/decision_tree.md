# Decision Tree v8 — Calendar-Adjusted Velocity Segments

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML:** 0-4 | **Orderable → min ML=1** | **CalendarWeight:** 0.7 pre Q4

---

## SOURCE: Segment × Store → ML (0-4)

| Segment | Weak | Mid | Strong | RO Tot% | Sold After% |
|---|---|---|---|---|---|
| **ActiveSeller** | 3 | 4 | 4 | 44-47% | 91-97% |
| **SlowFull** | 2 | 2 | 3 | 36-47% | 56-75% |
| **SlowPartial** | 2 | 2 | 3 | 30-37% | 72-84% |
| **PartialDead** | 1 | 1 | 2 | 34-38% | 49-62% |
| **TrueDead** | 1 | 1 | 1 | 22-29% | 33-41% |

> SlowFull ML zvýšené oproti v7 (Weak 1→2, Strong 2→3) kvôli absorpcii 678 borderline ActiveSeller.
> Constraint: Orderable → min ML=1. ML=0 len pre delisted.

### Source modifikátory (potvrdené v7/v8)
| Modifikátor | Podmínka | Úprava | Delta |
|---|---|---|---|
| LastSaleGap short | ≤90 dní | +1 | sold after +50pp |
| **BrandFit (TrueDead/SlowFull)** | **BrandStrong** | **+1** | **sold after +8-11pp, reorder +5-6pp** |
| BrandFit (ActiveSeller) | ignorovať | 0 | sold after >92% bez ohľadu na brand |
| Delisting | SkuClass → D/L | ML=0 | — |

> **BrandFit na source (nové v8):** BrandStrong source SKU sa predávajú o 5-11pp viac po redistribúcii. Najsilnejší efekt pri SlowFull (+10.7pp sold after) a TrueDead (+8.1pp). Ak brand je silný na tejto predajni, aj "mŕtve" SKU majú vyššiu šancu predaja → treba chrániť.

### Kalendárna korekcia (nové v8)
Namiesto seasonal modifieru sa korigujú vstupné dáta:
```
CalendarWeight = 0.7 ak polrok obsahuje Nov+Dec, inak 1.0
Velocity_Adj = Sales_12M_Adj / DaysInStock_12M × 30
```
Tým sa eliminuje potreba per-SKU seasonal flagu.

---

## TARGET: SalesBucket × Store → ML (0-4)

| Sales 12M | Weak | Mid | Strong |
|---|---|---|---|
| **0** | 1 | 1 | 1 |
| **1-2** | 1 | 1 | 2 |
| **3-5** | 1 | 2 | 3 |
| **6-10** | 2 | 3 | 3 |
| **11+** | 2 | 3 | 4 |

### Target modifikátory
| Modifikátor | Podmínka | Úprava |
|---|---|---|
| AllSold / ST1 high | AllSold4M=1 OR ST1_4M ≥85% | +1 |
| Growth pocket | Strong, Sales 3-10, ST≥45% | +1 |
| Nothing-sold / low ST | NothingSold4M=1 OR ST<20% | -1 |
| **BrandFit (0-2 sales)** | **SalesBucket 0-2: BrandWeak** | **-1** |
| **BrandFit (0-2 sales)** | **SalesBucket 0-2: BrandStrong** | **+1** |
| **BrandFit (3-5 sales)** | **SalesBucket 3-5: BrandWeak** | **-1** |
| BrandFit (6+ sales) | ignorovať | 0 (predaje dominujú) |
| Delisting | SkuClass → D/L | ML=0 |

> **BrandFit je graduovaný modifier (nové v8).** Pri 0-2 sales je delta +10-40pp ST → plný efekt.
> Pri 3-5 sales +7-9pp → penalty ale nie boost. Pri 6+ <3pp → ignorovať.
