# Backtest v4 — Objemový dopad

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML rozsah:** 0-4 | **Orderable → min ML=1**

---

## Aktuální stav

| Metrika | 4M Qty (%) | Total Qty (%) |
|---|---|---|
| **Oversell** | 1 464 (3.0%) | 5 578 (11.4%) |
| **Reorder** | 7 980 (16.4%) | 16 615 (34.1%) |

---

## Source: Dopad podle směru

| Směr | SKU | Redist Qty | OS 4M | OS Tot | RO 4M | RO Tot | RO Tot SKU% | RO Tot Qty% |
|---|---|---|---|---|---|---|---|---|
| **ML UP** | 15 435 | 21 688 | 962 | 3 501 | 4 592 | 9 038 | 47.3% | 41.7% |
| **ML DOWN** | 310 | 506 | 6 | 39 | 35 | 99 | 10.0% | 19.6% |
| **Beze změny** | 21 025 | 26 560 | 496 | 2 038 | 3 353 | 7 478 | 31.0% | 28.2% |

ML UP skupina má RO 47.3% SKU — nejvyšší. Zvýšení ML by mělo snížit reorder u těchto SKU.

---

## Odhad dopadu na reorder

- ML UP skupina: 15 435 SKU s reorder 9 038 ks (41.7% qty)
- Zvýšení ML o 1-3 stupně → odhad snížení reorderu ~20-30%
- Odhad ušetřeného reorderu: ~1 800-2 700 ks
- Celkový reorder: 16 615 → ~13 900-14 800 ks (pokles ~11-16%)
- **To odpovídá cíli snížit reorder o 10-15%**

---

## Doporučení

1. **Consistent (709 SKU) → ML 3-4:** Reorder 44-52% qty. Nejvyšší priorita.
2. **Declining (364 SKU) → ML 3-4:** Reorder 61-74% qty.
3. **Sporadic/Strong (5 480 SKU) → ML 3:** Reorder 43% qty.
4. **Dying/Strong (2 000 SKU) → ML 2:** Reorder 34% qty.
5. **Target ML DOWN pro 0-2 sales + Weak:** Nothing-sold 65%+.
6. **Target ML UP pro 11+ sales:** All-sold 85-90%.
