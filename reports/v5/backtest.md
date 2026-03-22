# Backtest v5 — odhad objemového dopadu

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**Metodika:** odhad po SKU podle změny `ML` vůči aktuálnímu `EntityList ML`, capped na aktuálním `redistributed/received qty`

## 1. Aktuální baseline

| Metrika | 4M Qty | Total Qty |
| --- | --- | --- |
| Oversell | 1 464 (3.0%) | 5 578 (11.4%) |
| Reorder | 7 980 (16.4%) | 16 615 (34.1%) |
| Avg ST | 45.3% | 69.2% |
| Nothing-sold | 17 552 | 8 872 |
| All-sold | 13 631 | 24 862 |

## 2. Source backtest

| Směr | SKU | Qty | Odhad qty change |
| --- | --- | --- | --- |
| UP | 13 333 | 18 533 | -14 999 |
| DOWN | 6 047 | 8 948 | +6 405 |
| SAME | 17 390 | 21 273 | 0 |

**Net source dopad:** `-8 594 ks`

### Největší source growth pockets (`DOWN`)

| Segment | SKU | Qty | Odhad qty change |
| --- | --- | --- | --- |
| Sporadic / Strong | 944 | 1 738 | +1 143 |
| Dead / Mid | 1 055 | 1 393 | +1 056 |
| Dead / Strong | 864 | 1 234 | +867 |
| Dead / Weak | 842 | 1 095 | +842 |

## 3. Target backtest

| Směr | SKU | Qty | Avg ST 4M | Nothing-sold 4M | All-sold 4M | Odhad qty change |
| --- | --- | --- | --- | --- | --- | --- |
| UP | 16 955 | 19 626 | 78.9% | 1.0% | 58.0% | +17 652 |
| DOWN | 16 035 | 19 266 | 20.5% | 74.2% | 15.8% | -18 068 |
| SAME | 8 641 | 9 862 | 25.0% | 63.5% | 14.5% | 0 |

**Net target dopad:** `-416 ks`

To je hlavní změna kalibrace: target je už téměř netto neutrální, ale zároveň výrazně větší část objemu aktivně směruje do `UP` segmentů.

### Největší target growth pockets (`UP`)

| Segment | SKU | Qty | Odhad qty change |
| --- | --- | --- | --- |
| 3-5 / Strong | 5 345 | 5 796 | +5 724 |
| 6-10 / Strong | 3 386 | 3 895 | +3 571 |
| 3-5 / Mid | 2 861 | 3 115 | +2 861 |
| 6-10 / Mid | 1 561 | 1 833 | +1 647 |
| 1-2 / Strong | 1 436 | 1 513 | +1 436 |
| 11+ / Strong | 1 057 | 1 588 | +1 085 |

### Největší target reduction pockets (`DOWN`)

| Segment | SKU | Qty | Odhad qty change |
| --- | --- | --- | --- |
| 3-5 / Mid | 3 309 | 3 786 | -3 559 |
| 1-2 / Strong | 2 436 | 2 665 | -2 577 |
| 1-2 / Mid | 2 370 | 2 599 | -2 484 |
| 3-5 / Strong | 1 958 | 2 300 | -2 236 |

## 4. Sensitivity

| Scénář | Odhad qty change |
| --- | --- |
| Source -1 | +1 122 |
| Source Base | -8 594 |
| Source +1 | -27 875 |
| Target -1 | -15 958 |
| Target Base | -416 |
| Target +1 | +17 355 |

Čtení:
- `Target Base` je už blízko neutrality, takže rozhodování se přesunulo od čisté úspory k realokaci objemu.
- `Target +1` by už byl příliš expanzní.
- `Source` zůstává opatrnější než `target`, protože právě source nese riziko `reorder` a `oversell`.

## 5. Hlavní trade-off

`v5` nyní pracuje jako realokační model:
- ubírá objem v nefunkčních target transferech
- přidává objem v silných target segmentech
- na source otevírá vybrané growth pockets, ale zároveň drží ochranu rizikových segmentů

Prakticky: cílem už není jen nižší celkový objem. Cílem je **lepší mix objemu**.
