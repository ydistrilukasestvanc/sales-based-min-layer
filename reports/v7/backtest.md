# Backtest v7 — Velocity-Normalized Dopad

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML:** 0-4 | **Orderable → min ML=1**

---

## Aktuální baseline

| Metrika | 4M Qty (%) | Total Qty (%) |
|---|---|---|
| Oversell | 1 464 (3.0%) | 5 578 (11.4%) |
| Reorder | 7 980 (16.4%) | 16 615 (34.1%) |
| Avg ST | 45.3% | 69.2% |
| Nothing-sold 4M | 17 552 (42.2%) | 8 872 (21.3%) |
| All-sold | 13 631 (32.7%) | 24 862 (59.7%) |

---

## v7 vs v5 porovnání přístupů

| Aspekt | v5 (Pattern) | v6 (Velocity) | v7 (Syntéza) |
|---|---|---|---|
| Source klasifikace | Pattern × Store | Velocity Segment × Store | Velocity Segment × Store |
| Source modifikátory | 9 (LastSaleGap, RedistRatio, Seasonal, ProductConc, Phantom, Growth pockets, Delisting) | 3 (Seasonal, Delisting, SoldAfter) | 3 potvrzené (LastSaleGap, Seasonal, Delisting) |
| Target přístup | Bidirectionální (UP + DOWN) | Jednosměrný | Bidirectionální z v5 |
| Nová metrika | — | Sold After %, Stock Coverage | Obojí |
| Phantom Stock | 115 SKU (cross-store) | 1 SKU (correct oversell) | 1 SKU → VYPADÁ |
| Loop | 4+ = extrémní risk | — | 7 SKU → VYPADÁ |
| ProductConc | Silný signál | — | Nepotvrzeno → VYPADÁ |

---

## Source dopad odhad

### Podle velocity segmentu

| Segment | SKU | Redist Qty | Navrhované ML | Aktuální ML avg | Směr |
|---|---|---|---|---|---|
| ActiveSeller | 2 535 | 5 151 | 3-4 | ~1.3 | UP (+2-3) |
| SlowFull | 10 197 | 13 511 | 1-2 | ~1.1 | UP (+0-1) |
| SlowPartial | 1 980 | 3 035 | 2-3 | ~1.1 | UP (+1-2) |
| PartialDead | 3 599 | 4 664 | 1-2 | ~1.0 | SAME/UP |
| TrueDead | 18 355 | 22 260 | 1 | ~1.0 | SAME |
| BriefNoSale | 48 | 61 | 2 | ~1.0 | UP (+1) |

**Hlavní source UP skupiny:** ActiveSeller (2 535 SKU, +2-3 ML) a SlowPartial (1 980 SKU, +1-2 ML).

### Odhad dopadu na reorder
- ActiveSeller: 2 535 SKU s RO 45.9% → ML UP by snížilo redistribuci o ~2-3 ks/SKU → odhad -3 000 až -5 000 ks reorder
- SlowPartial: 1 980 SKU s RO 34.5% → ML UP o 1-2 → odhad -1 000 až -2 000 ks
- **Celkový odhad snížení reorderu: -4 000 až -7 000 ks (z 16 615 = 24-42%)**
- To přesahuje cíl 10-15%, ale je konzervativnější v source DOWN (TrueDead zůstává ML=1 kvůli orderable)

---

## Target dopad odhad (bidirectionální z v5)

### Growth pockets (target UP)

| Segment | SKU | Qty | AS 4M% | ST 4M | Odhad +ks |
|---|---|---|---|---|---|
| 11+ / Strong | 1 358 | — | 64.4% | 77.0% | +1 358 |
| 11+ / Mid | 815 | — | 55.8% | 72.7% | +815 |
| 6-10 / Strong | 4 859 | — | 48.9% | 63.1% | +4 859 |
| 6-10 / Mid | 3 347 | — | 45.6% | 59.3% | +3 347 |
| 3-5 / Strong (sel.) | ~4 500 | — | 31.5% | 45.3% | +4 500 |

### Reduction pockets (target DOWN)

| Segment | SKU | Qty | NS 4M% | ST 4M | Odhad -ks |
|---|---|---|---|---|---|
| 0 / all | 723 | — | 62-74% | 23-36% | -723 |
| 1-2 / Weak | 1 966 | — | 65.5% | 26.3% | -1 966 |
| 1-2 / Mid | 4 493 | — | 62.0% | 28.6% | -4 493 |
| 3-5 / Weak (sel.) | ~1 300 | — | 45.1% | 41.5% | -1 300 |

**Odhad target net: přibližně netto neutrální** (z v5 přístupu) — realokace objemu z nefunkčních do funkčních transferů.

---

## Celkový souhrn v7

| Metrika | Aktuální | Odhad po v7 | Změna |
|---|---|---|---|
| Reorder total qty | 16 615 | ~10 000-12 500 | -25 až -40% |
| Oversell total qty | 5 578 | ~5 000-5 500 | mírný pokles |
| Target net volume | 48 754 | ~48 000-49 000 | přibližně neutrální |
| Target quality | 42.2% NS | ~35-38% NS | zlepšení mixu |

---

## Doporučení pro implementaci

1. **Priorita 1 — Source UP: ActiveSeller** (2 535 SKU). ML z ~1 na 3-4. Největší dopad na reorder.
2. **Priorita 2 — Source UP: SlowPartial/Strong** (792 SKU). ML z 1 na 3. Sold after 84%.
3. **Priorita 3 — Target realokace:** DOWN pro 0-2 sales, UP pro 6+ sales / Strong.
4. **Priorita 4 — Modifikátory:** Seasonal +1 na source. LastSaleGap ≤90d +1 na source.
5. **ML=0 jen pro delisted** (6 049 SKU). Orderable constraint drží zbytek na min ML=1.
