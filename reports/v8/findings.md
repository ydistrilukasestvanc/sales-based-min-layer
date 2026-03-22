# Findings v8 — Kalendárna korekcia + Velocity Segmenty + Graduovaný BrandFit

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13 | **ML:** 0-4
**Nové v8:** CalendarWeight 0.7 na polročia s Nov+Dec + BrandFit ako graduovaný modifier

---

## 1. Čo je v8

v8 rozširuje v7 o **kalendárnu korekciu**. Douglas = parfuméria → všetko je seasonal (Vianoce = darčeky). Namiesto identifikácie seasonal per SKU aplikujeme diskontný faktor na obdobia obsahujúce Nov+Dec.

### Kalibrácia faktoru
- Nov+Dec = 2 mesiace z 12 = 16.7% očakávaných predajov
- Skutočný podiel Nov+Dec: **23.7%** predajov za 12M
- Xmas lift = 23.7 / 16.7 = **1.42×**
- Discount faktor = 1 / 1.42 = **0.70**

### Aplikácia
```
H1 (Jul 2023 – Jan 2024): × 0.7  ← obsahuje Nov+Dec 2023
H2 (Jan 2024 – Jul 2024): × 1.0
H3 (Jul 2024 – Jan 2025): × 0.7  ← obsahuje Nov+Dec 2024
H4 (Jan 2025 – Jul 2025): × 1.0
Sales_12M_Adj = H3 × 0.7 + H4 × 1.0
Velocity_12M_Adj = Sales_12M_Adj / DaysInStock_12M × 30
```

---

## 2. Overview metriky (zhodné s v7)

| Metrika | 4M Qty (%) | Total Qty (%) |
|---|---|---|
| Oversell | 1 464 (3.0%) | 5 578 (11.4%) |
| Reorder | 7 980 (16.4%) | 16 615 (34.1%) |

Target: ST 45.3%/69.2%, nothing-sold 42.2%, all-sold 32.7%/59.7%.

---

## 3. Dopad kalendárnej korekcie na Pattern

| Raw Pattern | Adjusted Pattern | SKU | Zmena |
|---|---|---|---|
| Dead → Dead | 15 453 | SAME |
| Sporadic → Sporadic | 13 303 | SAME |
| Dying → Dying | 6 599 | SAME |
| Consistent → Consistent | 646 | SAME |
| Declining → Declining | 356 | SAME |
| **Sporadic → Declining** | **342** | CHANGED |
| **Consistent → Declining** | **63** | CHANGED |
| Declining → Consistent | 6 | CHANGED |
| Declining → Sporadic | 2 | CHANGED |

**413 SKU (1.1%) zmení Pattern.** Hlavne Sporadic/Consistent → Declining (po korekcii vianočného H3 sa vzorec javí ako klesajúci).

---

## 4. Dopad na Velocity Segmenty (hlavná zmena v8)

| Raw Segment | Adjusted Segment | SKU | Zmena |
|---|---|---|---|
| ActiveSeller → ActiveSeller | 1 801 | SAME |
| ActiveSeller → **SlowFull** | **678** | CHANGED |
| ActiveSeller → **SlowPartial** | **53** | CHANGED |
| ActiveSeller → SlowBrief | 3 | CHANGED |
| Všetky ostatné | — | 34 185 | SAME |

**734 SKU (29% pôvodných ActiveSeller!) sa reklasifikuje** po kalendárnej korekcii. Ich surová velocity bola tesne nad 0.5/mes (priemer 0.56), adjustovaná klesla na 0.43. Boli "ActiveSeller" len vďaka vianočnému boostu.

### Profil reklasifikovaných (ActiveSeller → SlowFull)
- 678 SKU, 1 081 ks redistrib
- Oversell total: 23.5%
- Reorder total: 52.4%
- Sold after: **91.0%** — stále sa predávajú!
- Raw velocity: 0.56 → Adjusted: 0.43

**Záver:** Tieto SKU sú na hranici. Vianočný boost ich posunul tesne nad threshold. Po korekcii sa správne klasifikujú ako SlowFull, ale sold after 91% znamená, že stále potrebujú ochranu → v decision tree SlowFull musí mať vyšší ML než v7.

---

## 5. v8 Segment × Store (adjustované)

| Segment | Store | SKU | Redist | OS 4M% | OS Tot% | RO 4M% | RO Tot% | RO SKU% | Sold After% |
|---|---|---|---|---|---|---|---|---|---|
| TrueDead | Weak | 5 227 | 6 238 | 1.0 | 4.3 | 9.6 | 21.5 | 23.7 | 32.6 |
| TrueDead | Mid | 8 206 | 10 026 | 1.3 | 6.1 | 11.4 | 26.1 | 29.0 | 37.2 |
| TrueDead | Strong | 4 922 | 5 996 | 2.1 | 8.0 | 12.7 | 28.6 | 31.5 | 40.8 |
| PartialDead | Weak | 939 | 1 124 | 2.8 | 9.9 | 16.7 | 33.8 | 36.8 | 48.8 |
| PartialDead | Mid | 1 599 | 2 056 | 4.1 | 14.1 | 19.3 | 38.1 | 41.7 | 57.8 |
| PartialDead | Strong | 1 061 | 1 484 | 5.4 | 17.0 | 18.2 | 36.5 | 40.8 | 62.2 |
| SlowPartial | Weak | 422 | 627 | 1.8 | 9.1 | 12.1 | 30.0 | 33.2 | 71.6 |
| SlowPartial | Mid | 792 | 1 175 | 3.5 | 12.1 | 16.5 | 34.4 | 39.5 | 72.6 |
| SlowPartial | Strong | 819 | 1 322 | 3.5 | 15.6 | 19.6 | 36.5 | 45.2 | 84.2 |
| SlowFull | Weak | 2 127 | 2 715 | 2.5 | 10.3 | 17.9 | 36.3 | 40.7 | 55.9 |
| SlowFull | Mid | 4 687 | 6 267 | 4.4 | 15.2 | 22.8 | 43.4 | 49.2 | 63.8 |
| SlowFull | Strong | 4 061 | 5 610 | 5.1 | 18.9 | 23.2 | 46.7 | 52.5 | 74.6 |
| ActiveSeller | Weak | 100 | 195 | 1.5 | 27.2 | 21.5 | 46.7 | 59.0 | 91.0 |
| ActiveSeller | Mid | 425 | 990 | 4.8 | 18.8 | 19.7 | 44.0 | 56.7 | 91.5 |
| ActiveSeller | Strong | 1 276 | 2 792 | 5.6 | 21.5 | 20.7 | 44.4 | 58.1 | 96.8 |

### Porovnání v7 vs v8 kľúčových segmentov

| Segment | v7 SKU | v8 SKU | Zmena | Dopad na ML |
|---|---|---|---|---|
| ActiveSeller | 2 535 | **1 801** | -734 (-29%) | Menšia skupina, ale skutočne aktívna |
| SlowFull | 10 197 | **10 875** | +678 (+7%) | Väčšia, obsahuje borderline SKU s 91% sold after |
| SlowPartial | 1 980 | **2 033** | +53 (+3%) | Mierne väčšia |

---

## 6. v8 Decision Tree (Source) — adjustovaný

| Segment | Weak | Mid | Strong | Zmena vs v7 |
|---|---|---|---|---|
| **ActiveSeller** | 3 | 4 | 4 | SAME — menšia ale čistejšia skupina |
| **SlowFull** | 2 | 2 | 3 | **UP** (1→2 Weak, 2→3 Strong) kvôli absorbovaným borderline SKU |
| **SlowPartial** | 2 | 2 | 3 | SAME |
| **PartialDead** | 1 | 1 | 2 | SAME |
| **TrueDead** | 1 | 1 | 1 | SAME |

**Hlavná zmena v8 source:** SlowFull dostáva vyšší ML (Weak 1→2, Strong 2→3), pretože teraz obsahuje 678 borderline SKU s 91% sold after a 52.4% reorder.

---

## 7. BrandStoreFit — graduovaný modifier (nové v8)

### Efekt BrandFit závisí od SalesBucket

| SalesBucket | BrandWeak ST | BrandStrong ST | Delta ST | Delta NS | Modifier |
|---|---|---|---|---|---|
| **0 (no sales)** | 19-27% | 44-59% | **+18 až +40pp** | -17 až -21pp | BW -1, BS +1 |
| **1-2** | 43-49% | 53-58% | **+9 až +10pp** | -6 až -9pp | BW -1, BS +1 |
| **3-5** | 62-64% | 69-73% | **+7 až +9pp** | -6 až -9pp | BW -1, BS 0 |
| **6-10** | 81-85% | 83-86% | +2 až +3pp | ~0 | Bez modifieru |
| **11+** | 83-96% | 94% | <2pp | ~0 | Bez modifieru |

### Príklady extrémov

**Najhorší target (v8 → ML by mal byť 1):**
- SalesBucket=0 + Weak + BrandWeak: ST 26.1%, NS 79.8%, AS 21.3%
- SalesBucket=0 + Strong + BrandWeak: ST 19.7%, NS 80.0%, AS 16.0%

**Najlepší target (v8 → ML by mal byť vyšší):**
- SalesBucket=0 + Strong + BrandStrong: ST 59.4%, NS 59.4%, AS 58.7%
- SalesBucket=1-2 + Strong + BrandStrong: ST 58.0%, NS 56.5%, AS 48.4%

**Záver:** BrandFit je najsilnejší prediktor pri nízkom SalesBucket (0-2). Keď nemáte predajnú históriu, brand fit je najlepší signál. Pri 6+ sales sú predaje dostatočným signálom samy o sebe.

### Aktualizovaný target modifier

| Modifikátor | Podmínka | Úprava |
|---|---|---|
| **BrandFit (0-2 sales)** | SalesBucket 0-2 + BrandWeak | -1 |
| **BrandFit (0-2 sales)** | SalesBucket 0-2 + BrandStrong | +1 |
| **BrandFit (3-5 sales)** | SalesBucket 3-5 + BrandWeak | -1 |
| BrandFit (6+ sales) | ignorovať | 0 |

---

## 8. BrandFit na SOURCE strane (nové v8)

BrandFit neovplyvňuje len target — aj na source strane majú BrandStrong SKU vyššiu šancu predaja po redistribúcii:

| Segment | BW Sold After | BS Sold After | Delta | BW Reorder | BS Reorder | Delta |
|---|---|---|---|---|---|---|
| **TrueDead** | 35.3% | 43.4% | **+8.1pp** | 23.4% | 29.3% | +5.9pp |
| **SlowFull** | 64.0% | 74.7% | **+10.7pp** | 38.0% | 43.5% | +5.5pp |
| **SlowPartial** | 72.3% | 82.1% | **+9.8pp** | 29.9% | 29.5% | ~0 |
| PartialDead | 55.4% | 60.7% | +5.3pp | 34.1% | 37.6% | +3.5pp |
| ActiveSeller | 92.2% | 96.8% | +4.6pp | 38.5% | 37.0% | ~0 |

**Záver:** TrueDead/SlowFull/SlowPartial + BrandStrong → source ML +1. Ak brand je silný na tejto predajni, aj "mŕtve" SKU majú vyššiu šancu predaja (8-11pp) → treba chrániť pred redistribúciou. ActiveSeller: ignorovať — sold after >92% bez ohľadu na brand.
