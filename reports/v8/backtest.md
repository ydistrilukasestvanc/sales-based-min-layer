# Backtest v8 — Dopad kalendárnej korekcie

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML:** 0-4 | **Orderable → min ML=1**

---

## Baseline

| Metrika | 4M Qty (%) | Total Qty (%) |
|---|---|---|
| Oversell | 1 464 (3.0%) | 5 578 (11.4%) |
| Reorder | 7 980 (16.4%) | 16 615 (34.1%) |

---

## Hlavná zmena v8 vs v7

| Aspekt | v7 | v8 | Dopad |
|---|---|---|---|
| ActiveSeller | 2 535 SKU | 1 801 SKU | -734 SKU (-29%) |
| SlowFull ML | Weak=1, Mid=2, Strong=2 | **Weak=2, Mid=2, Strong=3** | Vyšší ochrana |
| Seasonal modifier | +1 per SKU | ODSTRANĚNÝ | Nahradený CalendarWeight |
| Celkový source UP | ~15 435 SKU | ~16 000 SKU | Mierne viac kvôli SlowFull UP |

## Odhad dopadu

### Source
- ActiveSeller (1 801 SKU): ML 3-4 → blokuje ~2 500-3 500 ks redistribuce
- SlowFull (10 875 SKU): ML 2-3 (vyšší než v7) → blokuje ~3 000-5 000 ks
- Celkový odhad: **-5 500 až -8 500 ks redistribuce** z source
- Odhad snížení reorderu: -3 000 až -5 000 ks (z 16 615 = 18-30%)

### Target (bidirectionální, rovnaký ako v7)
- Growth pockets (11+, 6-10, 3-5/Strong): +10 000-15 000 ks
- Reduction (0, 1-2): -10 000-15 000 ks
- Net target: ~netto neutrálny

---

## Doporučení

1. **SlowFull je v8 najdôležitejšia zmena.** Obsahuje 678 borderline SKU s 91% sold after. ML Weak=2, Strong=3.
2. **ActiveSeller je teraz čistejšia skupina** (1 801 SKU namiesto 2 535). ML 3-4 je justified.
3. **Seasonal modifier je zbytočný** — CalendarWeight na vstupných dátach ho nahrádza systémovo.
4. **Target ostáva bidirectionálny** — growth pockets + reduction, net ~neutrálny.
