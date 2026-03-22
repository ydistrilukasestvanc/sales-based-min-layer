# Decision Tree v7 — Velocity-Normalized Source + Bidirectional Target

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML:** 0-4 | **Orderable (A-O, Z-O) → min ML=1**

---

## Principy v7

- Source klasifikace: **Velocity Segment** (z v6) namísto Pattern (z v5)
- Modifikátory: jen **potvrzené** signály (LastSaleGap, Seasonal, Delisting)
- Target: **bidirectionální** (z v5) — growth pockets + reduction pockets
- Kontrolní metrika: **Sold After %** — pokud segment má > 80% sold after, ML nesmí být nízké

---

## SOURCE lookup: Segment × Store → ML (0-4)

| Segment | Weak | Mid | Strong | RO Tot% | Sold After% | Důvod |
|---|---|---|---|---|---|---|
| **ActiveSeller** | 3 | 4 | 4 | 43-48% | 89-96% | Nejvyšší riziko. 94% se prodá po redistribuci. |
| **SlowFull** | 1 | 2 | 2 | 36-46% | 55-73% | Pomalé ale stabilní. Strong potřebuje víc. |
| **SlowPartial** | 2 | 2 | 3 | 30-37% | 71-84% | Překvapivě aktivní! Krátký stock = rozjíždí se. |
| **PartialDead** | 1 | 1 | 2 | 34-38% | 49-62% | Krátký stock, nejisté. Strong opatrnější. |
| **TrueDead** | 1 | 1 | 1 | 22-29% | 33-41% | Plný stock, žádné prodeje. Bezpečné. |
| **BriefNoSale** | 2 | 2 | 2 | ~51% | 71% | Velmi nové, opatrnost. |

> **Constraint:** Orderable → min ML=1. ML=0 jen pro delisted.

### Source modifikátory

| Modifikátor | Podmínka | Úprava | v7 validace |
|---|---|---|---|
| **LastSaleGap short** | ≤90 dní | +1 | Potvrzeno: sold after 85-90% |
| **Seasonal** | XmasLift ≥20% | +1 | Potvrzeno: OS 2× vyšší, RO 1.5× |
| **Delisting** | SkuClass → D/L | ML=0 | Potvrzeno: RO jen 10.9% |
| ~~PhantomStock~~ | — | — | VYPADÁ: jen 1 SKU |
| ~~ProductConc <10%~~ | — | — | VYPADÁ: žádný gradient |
| ~~Loop 4+~~ | — | — | VYPADÁ: 7 SKU, nevýznamné |

### Source clamp
- Výsledek clamp na 0-4
- Orderable (A-O, Z-O) → minimum 1
- ML=0 jen pro delisted / non-orderable

---

## TARGET lookup: SalesBucket × Store → ML (0-4)

| Sales 12M | Weak | Mid | Strong | NS 4M% | AS Tot% |
|---|---|---|---|---|---|
| **0** | 1 | 1 | 1 | 62-74% | 31-52% |
| **1-2** | 1 | 1 | 2 | 58-66% | 38-47% |
| **3-5** | 1 | 2 | 3 | 41-46% | 54-61% |
| **6-10** | 2 | 3 | 3 | 22-28% | 74-79% |
| **11+** | 2 | 3 | 4 | 11-12% | 85-90% |

### Target modifikátory

| Modifikátor | Podmínka | Úprava |
|---|---|---|
| **All-sold / ST-1pc high** | AllSold4M=1 OR ST1_4M ≥85% | +1 |
| **Growth pocket** | Store=Strong, Sales 3-10, ST4M ≥45% | +1 |
| **Strong absorber** | Store Mid/Strong, Sales ≥6, ST4M ≥55% | +1 |
| **Nothing-sold / low ST** | NothingSold4M=1 OR ST4M <20% | -1 |
| **Brand-store mismatch** | BrandWeak + ST4M <35% | -1 |
| **Delisting** | SkuClass → D/L | ML=0 |

### Target clamp
- Výsledek clamp na 0-4
- Orderable → minimum 1

---

## 4 směry

### Source UP (ochrana)
- ActiveSeller: všechny store strength → ML 3-4
- SlowFull/Strong → ML 2
- SlowPartial/Strong → ML 3
- + LastSaleGap ≤90d, Seasonal

### Source DOWN (growth pockets)
- TrueDead/Weak → ML 1 (orderable constraint)
- TrueDead/Mid → ML 1
- Delisted → ML 0

### Target UP (growth pockets)
- 11+ / Mid-Strong → ML 3-4
- 6-10 / Mid-Strong → ML 3
- 3-5 / Strong s potvrzeným ST → ML 3
- AllSold + vysoký ST-1pc → +1

### Target DOWN (reduction)
- 0 / all stores → ML 1
- 1-2 / Weak-Mid → ML 1
- NothingSold + nízký ST → -1
- BrandWeak mismatch → -1
