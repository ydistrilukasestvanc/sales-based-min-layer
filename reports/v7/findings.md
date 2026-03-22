# Findings v7 — Syntéza v5 + v6: Velocity-Normalized MinLayers

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13 | **ML:** 0-4
**Orderable (A-O, Z-O) → min ML=1** | **Temp prefix:** SBM_v7_

---

## 1. Co je v7

v7 kombinuje dva přístupy:
- **v5 (Codex):** Pattern klasifikace (Dead/Dying/Sporadic/Consistent/Declining) + bohatá sada modifikátorů (LastSaleGap, RedistRatio, Seasonal, ProductConcentration, PhantomStock, Loop) + bidirectionální target (growth pockets)
- **v6:** Velocity normalizace (prodeje / dny na skladě) + nové segmenty (TrueDead, SlowFull, PartialDead, ActiveSeller, SlowPartial) + "Sold After %" prediktor + target stock coverage

v7 analyzuje kde se oba přístupy shodují a kde se liší — a kombinuje silné stránky obou.

---

## 2. Validace a overview

| Parametr | Hodnota |
|---|---|
| Redistribučních párů | 42 404 |
| Redistribuovaných ks | 48 754 |
| Source SKU | 36 770 |
| Target SKU | 41 631 |
| Produktů | 5 152 |
| Prodejen | 352 (107 Weak / 140 Mid / 105 Strong) |
| v7 temp tabulek | 18 |

### SOURCE metriky

| Metrika | 4M SKU (%) | 4M Qty (%) | Total SKU (%) | Total Qty (%) |
|---|---|---|---|---|
| **Oversell** | 1 317 (3.6%) | 1 464 (3.0%) | 4 718 (12.8%) | 5 578 (11.4%) |
| **Reorder** | 7 087 (19.3%) | 7 980 (16.4%) | 13 841 (37.6%) | 16 615 (34.1%) |

Oversell 4M = 3.0% — **v cíli (5-10%).** Reorder total = 34.1% qty — **hlavní metrika k optimalizaci. Cíl: snížit o 10-15%.**

### TARGET metriky

| Metrika | 4M | Total |
|---|---|---|
| Avg Sell-Through | 45.3% | 69.2% |
| Avg ST-1pc | 58.2% | 79.6% |
| Nothing-sold | 17 552 (42.2%) | 8 872 (21.3%) |
| All-sold | 13 631 (32.7%) | 24 862 (59.7%) |

---

## 3. v5 vs v6: Reklasifikační matice

### Jak se v5 Pattern mapuje na v6 Velocity Segment

| v5 Pattern | v6 Segment | SKU | Redist | OS Tot% | RO Tot% | Sold After% | Avg Stock Days |
|---|---|---|---|---|---|---|---|
| Consistent | ActiveSeller | 644 | 1 523 | 25.7 | 50.9 | 98.3 | 337 |
| Consistent | SlowFull | 65 | 102 | 25.5 | 53.9 | 89.2 | 348 |
| Dead | TrueDead | 11 834 | 14 351 | 4.6 | 22.6 | 33.9 | 355 |
| Dead | PartialDead | 3 533 | 4 579 | 13.7 | 36.3 | 56.9 | 172 |
| Dead | BriefNoSale | 36 | 44 | 27.3 | 47.7 | 66.7 | 62 |
| Dying | TrueDead | 6 521 | 7 909 | 8.8 | 30.7 | 42.2 | 364 |
| Dying | PartialDead | 66 | 85 | 28.2 | 49.4 | 51.5 | 184 |
| Declining | SlowFull | 324 | 429 | 28.2 | 65.3 | 78.7 | 355 |
| Declining | ActiveSeller | 35 | 63 | 49.2 | 79.4 | 100.0 | 336 |
| Sporadic | SlowFull | 9 808 | 12 980 | 14.6 | 41.8 | 64.1 | 347 |
| Sporadic | SlowPartial | 1 975 | 3 030 | 12.5 | 34.5 | 76.9 | 188 |
| Sporadic | ActiveSeller | 1 856 | 3 565 | 19.4 | 43.1 | 92.1 | 276 |

**Kritické rozdíly kde v5 a v6 nesouhlasí:**

1. **Sporadic se rozpadá na 3 segmenty:** v5 dává Sporadic ML 1-2, ale v6 ukazuje:
   - SlowFull (9 808): sold after 64% → ML 1-2 je ok
   - SlowPartial (1 975): sold after 77%, krátký stock → ML 2-3 (v5 podceňuje)
   - ActiveSeller (1 856): sold after 92%! → ML 3-4 (v5 výrazně podceňuje)

2. **Dead → PartialDead (3 533 SKU):** v5 dává ML 0-1, ale PartialDead má oversell 13.7%, reorder 36.3%, sold after 57%. Krátký stock = nový produkt, ne mrtvý. ML by mělo být 1-2.

3. **Declining → ActiveSeller (35 SKU):** malé, ale extrémní — oversell 49.2%, sold after 100%. v5 dává ML 1-3, potřebuje ML 4.

**Kde se v5 a v6 shodují:**
- TrueDead = Dead/Dying s plným stockem → bezpečné, nízké ML
- ActiveSeller = Consistent/Declining s vysokou velocity → vysoké ML
- Silnější prodejna vždy = vyšší riziko

---

## 4. Velocity Segment × Store Strength (hlavní rozhodovací matice)

| Segment | Store | SKU | Redist | OS 4M% | OS Tot% | RO 4M% | RO Tot% | RO SKU% | Sold After% |
|---|---|---|---|---|---|---|---|---|---|
| TrueDead | Weak | 5 227 | 6 238 | 1.0 | 4.3 | 9.6 | 21.5 | 23.7 | 32.6 |
| TrueDead | Mid | 8 206 | 10 026 | 1.3 | 6.1 | 11.4 | 26.1 | 29.0 | 37.2 |
| TrueDead | Strong | 4 922 | 5 996 | 2.1 | 8.0 | 12.7 | 28.6 | 31.5 | 40.8 |
| PartialDead | Weak | 939 | 1 124 | 2.8 | 9.9 | 16.7 | 33.8 | 36.8 | 48.8 |
| PartialDead | Mid | 1 599 | 2 056 | 4.1 | 14.1 | 19.3 | 38.1 | 41.7 | 57.8 |
| PartialDead | Strong | 1 061 | 1 484 | 5.4 | 17.0 | 18.2 | 36.5 | 40.8 | 62.2 |
| SlowPartial | Weak | 415 | 617 | 1.5 | 8.8 | 11.8 | 29.7 | 32.8 | 71.1 |
| SlowPartial | Mid | 773 | 1 151 | 3.3 | 11.7 | 16.2 | 34.1 | 39.3 | 72.6 |
| SlowPartial | Strong | 792 | 1 267 | 3.4 | 15.4 | 20.3 | 37.3 | 46.1 | 84.2 |
| SlowFull | Weak | 2 060 | 2 614 | 2.5 | 10.2 | 17.9 | 36.4 | 40.6 | 54.9 |
| SlowFull | Mid | 4 468 | 5 927 | 4.4 | 14.6 | 22.3 | 42.5 | 48.3 | 62.8 |
| SlowFull | Strong | 3 669 | 4 970 | 4.9 | 18.3 | 22.8 | 46.0 | 51.4 | 72.6 |
| ActiveSeller | Weak | 176 | 308 | 2.3 | 22.1 | 21.1 | 42.9 | 52.8 | 90.3 |
| ActiveSeller | Mid | 664 | 1 356 | 5.2 | 20.9 | 23.1 | 47.5 | 59.8 | 89.0 |
| ActiveSeller | Strong | 1 695 | 3 487 | 5.7 | 21.9 | 21.4 | 45.5 | 58.3 | 96.0 |

**Doplňkové signály v segmentech:**
- ActiveSeller: 62-65% seasonal, avg gap 75-101 dní, avg concentration 14-16%
- SlowPartial: 17-36% seasonal, avg concentration 17-24%, avg gap 107-135 dní
- TrueDead: 0% seasonal, avg gap 500+ dní, avg concentration 7-9%

---

## 5. Doplňkové signály (z v5)

### LastSaleGap

| Gap | SKU | OS Tot% | RO Tot% | Sold After% |
|---|---|---|---|---|
| 0-30d (recent) | 1 472 | 13.1 | 35.2 | 90.0 |
| 31-90d | 2 280 | 14.8 | 39.4 | 85.2 |
| 91-180d | 3 116 | 15.6 | 45.5 | 76.4 |
| 181-365d | 7 850 | 18.1 | 44.0 | 61.8 |
| 365-730d | 6 588 | 9.0 | 30.9 | 42.4 |
| Never/730d+ | 15 464 | 6.9 | 26.1 | 39.4 |

LastSaleGap ≤90d: sold after 85-90%. Silný modifier.

### ProductConcentration

| Concentration | SKU | OS Tot% | RO Tot% |
|---|---|---|---|
| <10% | 20 722 | 11.2 | 32.3 |
| 10-25% | 12 790 | 12.3 | 37.2 |
| 25-50% | 3 118 | 10.7 | 35.4 |
| 50%+ | 140 | 0.3 | 3.5 |

Nízký dopad na metriky, ale v5 používá <10% jako source UP modifier. V v7 data to nepotvrzují — oversell/reorder jsou si podobné napříč buckety.

### Redistribuční smyčka

| Loop | SKU | OS Tot% | RO Tot% |
|---|---|---|---|
| None | 35 599 | 11.4 | 34.1 |
| 1 | 1 014 | 12.0 | 33.5 |
| 2-3 | 150 | 9.5 | 41.1 |
| 4+ | 7 | 2.4 | 23.8 |

Velmi malá skupina (7 SKU s 4+ loop). Statisticky nevýznamné pro modifier.

### Phantom Stock

Se správným oversell vzorcem: **1 potvrzený phantom stock SKU.** Minimální dopad. Phantom stock jako modifier je v v7 irelevantní.

### Sezónnost

| Flag | SKU | OS Tot% | RO Tot% |
|---|---|---|---|
| Non-seasonal | 29 298 | 9.3 | 30.8 |
| Seasonal | 7 472 | 18.8 | 45.3 |

Silný signál: seasonal má 2× vyšší obě metriky. V v7 je 62-65% ActiveSeller seasonal — to vysvětluje proč mají vysoký reorder.

### SkuClass změny

| Změna | SKU | OS Tot% | RO Tot% | RO SKU% |
|---|---|---|---|---|
| Unchanged | 29 322 | 13.0 | 39.8 | 43.2 |
| Delisted | 6 049 | 4.9 | 10.9 | 13.2 |
| Other | 1 399 | 10.1 | 26.3 | 27.2 |

Delisted = bezpečné → ML=0.

---

## 6. Target analýza

### SalesBucket × StoreStrength

| Sales | Store | SKU | ST 4M | ST Tot | ST1 Tot | NS 4M% | AS 4M% | AS Tot% |
|---|---|---|---|---|---|---|---|---|
| 0 | Weak | 137 | 23.1 | 34.7 | 16.1 | 73.7 | 21.2 | 31.4 |
| 0 | Mid | 334 | 23.4 | 41.5 | 22.4 | 73.7 | 21.3 | 37.7 |
| 0 | Strong | 252 | 36.4 | 53.6 | 22.2 | 61.1 | 34.9 | 51.6 |
| 1-2 | Weak | 1 966 | 26.3 | 47.2 | 59.5 | 65.5 | 18.1 | 38.0 |
| 1-2 | Mid | 4 493 | 28.6 | 51.2 | 63.7 | 62.0 | 19.3 | 40.9 |
| 1-2 | Strong | 3 622 | 32.1 | 56.4 | 68.1 | 58.0 | 22.1 | 47.0 |
| 3-5 | Weak | 2 601 | 41.5 | 65.8 | 76.7 | 45.1 | 28.1 | 54.4 |
| 3-5 | Mid | 7 765 | 40.8 | 66.0 | 77.1 | 45.5 | 27.3 | 54.6 |
| 3-5 | Strong | 9 017 | 45.3 | 71.7 | 82.1 | 40.8 | 31.5 | 61.0 |
| 6-10 | Weak | 886 | 58.6 | 82.2 | 87.5 | 28.1 | 45.4 | 74.3 |
| 6-10 | Mid | 3 347 | 59.3 | 84.3 | 90.6 | 26.8 | 45.6 | 76.2 |
| 6-10 | Strong | 4 859 | 63.1 | 86.2 | 92.3 | 22.3 | 48.9 | 78.8 |
| 11+ | Weak | 179 | 73.8 | 92.0 | 95.5 | 12.3 | 56.4 | 84.9 |
| 11+ | Mid | 815 | 72.7 | 93.4 | 95.7 | 11.9 | 55.8 | 87.9 |
| 11+ | Strong | 1 358 | 77.0 | 93.9 | 96.4 | 10.8 | 64.4 | 89.5 |

### Target stock coverage efekt (z v6)

| Target Stock 6M | Sales Bucket | SKU | Avg ST Tot | NS 4M% | AS Tot% |
|---|---|---|---|---|---|
| New (0d) | 0 | 497 | 58.1 | 61.8 | 57.7 |
| New (0d) | 3-5 | 351 | 80.2 | 39.0 | 80.1 |
| New (0d) | 11+ | 81 | 93.8 | 25.9 | 93.8 |
| Brief (1-89d) | 1-2 | 788 | 55.7 | 63.2 | 52.7 |
| Brief (1-89d) | 3-5 | 772 | 79.8 | 35.1 | 74.9 |
| Brief (1-89d) | 11+ | 265 | 95.0 | 9.4 | 90.9 |
| Partial (90-149d) | 1-2 | 1 912 | 58.8 | 55.4 | 49.7 |
| Partial (90-149d) | 3-5 | 4 206 | 72.1 | 38.8 | 61.6 |
| Partial (90-149d) | 11+ | 577 | 94.2 | 6.6 | 88.7 |
| Established (150d+) | 1-2 | 6 847 | 50.2 | 62.1 | 38.8 |
| Established (150d+) | 3-5 | 14 054 | 66.6 | 45.1 | 54.8 |
| Established (150d+) | 11+ | 1 429 | 93.1 | 12.7 | 87.8 |

**Zjištění:** U SalesBucket 3-5 je ST výrazně lepší pro nové/brief target (80% vs 67% u established). Redistribuce na nové target pozice je efektivnější.

### Brand-Store Fit

| Store | BrandWeak | BrandMid | BrandStrong |
|---|---|---|---|
| Weak | ST 55.3%, NS 54.9% | ST 63.7%, NS 49.3% | ST 68.4%, NS 42.4% |
| Mid | ST 59.1%, NS 53.2% | ST 64.3%, NS 47.6% | ST 70.0%, NS 41.1% |
| Strong | ST 63.9%, NS 47.3% | ST 69.5%, NS 42.2% | ST 75.8%, NS 35.4% |

---

## 7. Párová analýza (opravený oversell)

| Outcome | Pairs | % |
|---|---|---|
| Win-Win (no OS + good ST) | 28 179 | 66.5% |
| Win-Lose (no OS + bad ST) | 8 565 | 20.2% |
| Lose-Win (OS + good ST) | 4 794 | 11.3% |
| Lose-Lose | 866 | 2.0% |

66.5% párů je Win-Win. Hlavní příležitost: Win-Lose (20.2%) — optimalizovat target stranu.

---

## 8. Kde se v5 a v6 modifikátory potvrzují / nepotvrzují

| Modifier (z v5) | v7 validace | Závěr |
|---|---|---|
| **LastSaleGap ≤30d → +1** | Potvrzeno: sold after 90%, OS 13.1%, RO 35.2% | PLATÍ — silný signál |
| **Seasonal → +1** | Potvrzeno: OS 18.8% vs 9.3%, RO 45.3% vs 30.8% | PLATÍ — silný signál |
| **RedistRatio ≥75% → +1** | Částečně: RO je nízký (11.4%), ale RO_SKU jen 10.7% | SLABÝ — nízký objem, ale funguje jako safeguard |
| **ProductConc <10% → +1** | Nepotvrzeno: OS 11.2% vs 12.3% pro 10-25% — žádný jasný gradient | VYPADÁ z v7 |
| **PhantomStock → -1** | Nepotvrzeno: jen 1 SKU s correct oversell | VYPADÁ z v7 |
| **Loop 4+ → +1** | Nepotvrzeno: jen 7 SKU. Statisticky nevýznamné. | VYPADÁ z v7 |
| **v6 Sold After ≥80%** | Nový: silný prediktor (ActiveSeller 94%, SlowPartial/Strong 84%) | PŘIDÁNO do v7 |
| **v6 Target Stock Coverage** | Nový: brief/new target má lepší ST (80% vs 67% u 3-5 bucket) | PŘIDÁNO do v7 jako informace |

---

## 9. Flow Matrix

| Source→Target | Weak | Mid | Strong |
|---|---|---|---|
| Weak | 2.8% | 9.8% | 10.9% |
| Mid | 5.6% | 17.2% | 19.6% |
| Strong | 5.4% | 13.3% | 15.4% |

---

## 10. Shrnutí pro v7 Decision Tree

**Source:** Velocity Segment × Store jako base, LastSaleGap a Seasonal jako modifikátory. PhantomStock, ProductConcentration a Loop VYPADÁVAJÍ (nepotvrzeny na v7 datech).

**Target:** SalesBucket × Store jako base (z v5), bidirectionální (growth pockets + reduction). Brand-Store fit a AllSold/NothingSold jako modifikátory.

**Nové v7 přístupy:**
1. Velocity segment namísto Pattern (lepší predikce díky stock normalizaci)
2. "Sold After %" jako kontrolní metrika — pokud > 80%, ML musí být vysoké
3. Bidirectionální target z v5 — nejen snižovat, ale i growth pockets
