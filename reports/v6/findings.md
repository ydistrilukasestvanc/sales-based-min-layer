# Findings v6 — Stock-Normalized Analytika

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13 | **ML:** 0-4
**Nový přístup:** Normalizace prodejů na dobu dostupnosti zásob (velocity)

---

## 1. Klíčový problém předchozích verzí

V v4 se Pattern klasifikace (Dead/Dying/Sporadic/Consistent/Declining) opírala o **surový počet prodejů za 24M** bez ohledu na to, jak dlouho bylo SKU na skladě. To vedlo k chybné klasifikaci:

- SKU s 0 prodeji za 24M, ale na skladě jen 3 měsíce → klasifikováno jako "Dead", ale ve skutečnosti nemělo šanci prodávat
- SKU s 2 prodeji za 24M, ale na skladě 24 měsíců → klasifikováno jako "Sporadic", ale ve skutečnosti téměř mrtvé (0.08/měsíc)

## 2. Stock availability distribuce (source)

| Zásoby 24M | SKU | % |
|---|---|---|
| <90 dní | 30 | 0.1% |
| 90-180 dní | 4 646 | 12.7% |
| 180-365 dní | 6 304 | 17.2% |
| 365-545 dní | 8 121 | 22.1% |
| 545+ dní (plný) | 17 619 | 48.0% |

**12.8% source SKU mělo zásobu méně než 180 dní z 24M.** Jejich prodejní metriky nelze srovnávat s plně stocked SKU.

---

## 3. Nová segmentace (velocity-based)

### Definice

```
Velocity = Sales_12M / DaysInStock_12M × 30  (prodeje za měsíc na skladě)
```

| Segment | Definice | SKU | % | Redist Qty |
|---|---|---|---|---|
| **TrueDead** | 0 prodejů, stock ≥270 dní | 18 355 | 50.0% | 22 260 |
| **SlowFull** | Velocity <0.5/měs, stock ≥270d | 10 197 | 27.8% | 13 511 |
| **PartialDead** | 0 prodejů, stock 90-270 dní | 3 599 | 9.8% | 4 664 |
| **ActiveSeller** | Velocity ≥0.5/měs | 2 535 | 6.9% | 5 151 |
| **SlowPartial** | Velocity <0.5/měs, stock 90-270d | 1 980 | 5.4% | 3 035 |
| **BriefNoSale** | 0 prodejů, stock <90 dní | 48 | 0.1% | 61 |

### Metriky podle segmentu

| Segment | OS Tot% | RO Tot% | RO Tot SKU% | Prodalo se po redist% |
|---|---|---|---|---|
| **TrueDead** | 6.1 | 25.5 | 28.2 | 36.9 |
| **SlowFull** | 15.1 | 42.6 | 47.9 | 64.7 |
| **PartialDead** | 14.0 | 36.6 | 40.2 | 56.8 |
| **ActiveSeller** | 21.6 | 45.9 | 58.3 | 93.8 |
| **SlowPartial** | 12.7 | 34.5 | 40.7 | 76.9 |
| **BriefNoSale** | 27.9 | 50.8 | 52.1 | 70.8 |

**Klíčové zjištění:**
1. **TrueDead (50%)** — nejbezpečnější skupina. RO 25.5%, oversell 6.1%. Jen 36.9% se prodalo po redistribuci.
2. **ActiveSeller (6.9%)** — nejrizikovější. RO 45.9%, OS 21.6%, **93.8% se prodalo po redistribuci!** Musí mít vysoké ML.
3. **SlowPartial** — překvapení: 76.9% se prodalo po redistribuci, přestože mají nízkou velocity. Krátký stock = nový produkt, který se rozjíždí.
4. **BriefNoSale (48 SKU)** — malá skupina, ale 70.8% se prodalo po redistribuci! Špatní kandidáti na redistribuci.

---

## 4. Segment × Store Strength (zdroj pro Decision Tree)

| Segment | Store | SKU | Redist | OS Tot% | RO Tot% | RO SKU% | Sold After% |
|---|---|---|---|---|---|---|---|
| TrueDead | Weak | 5 227 | 6 238 | 4.3 | 21.5 | 23.7 | 32.6 |
| TrueDead | Mid | 8 206 | 10 026 | 6.1 | 26.1 | 29.0 | 37.2 |
| TrueDead | Strong | 4 922 | 5 996 | 8.0 | 28.6 | 31.5 | 40.8 |
| PartialDead | Weak | 939 | 1 124 | 9.9 | 33.8 | 36.8 | 48.8 |
| PartialDead | Mid | 1 599 | 2 056 | 14.1 | 38.1 | 41.7 | 57.8 |
| PartialDead | Strong | 1 061 | 1 484 | 17.0 | 36.5 | 40.8 | 62.2 |
| SlowPartial | Weak | 415 | 617 | 8.8 | 29.7 | 32.8 | 71.1 |
| SlowPartial | Mid | 773 | 1 151 | 11.7 | 34.1 | 39.3 | 72.6 |
| SlowPartial | Strong | 792 | 1 267 | 15.4 | 37.3 | 46.1 | 84.2 |
| SlowFull | Weak | 2 060 | 2 614 | 10.2 | 36.4 | 40.6 | 54.9 |
| SlowFull | Mid | 4 468 | 5 927 | 14.6 | 42.5 | 48.3 | 62.8 |
| SlowFull | Strong | 3 669 | 4 970 | 18.3 | 46.0 | 51.4 | 72.6 |
| ActiveSeller | Weak | 176 | 308 | 22.1 | 42.9 | 52.8 | 90.3 |
| ActiveSeller | Mid | 664 | 1 356 | 20.9 | 47.5 | 59.8 | 89.0 |
| ActiveSeller | Strong | 1 695 | 3 487 | 21.9 | 45.5 | 58.3 | 96.0 |

---

## 5. Srovnání starých vzorců vs nové segmenty

### Reklasifikace: Old Pattern → New Segment

| Starý Pattern | → TrueDead | → PartialDead | → SlowFull | → SlowPartial | → ActiveSeller |
|---|---|---|---|---|---|
| Dead (15 403) | 15 367 | 36 | — | — | — |
| Dying (6 599) | 6 587 | 12 | — | — | — |
| Sporadic (13 645) | — | — | 10 197 | 1 980 | 1 856 |
| Consistent (709) | — | — | — | — | 644 |
| Declining (364) | — | — | — | — | 35 |

**Dead a Dying se téměř kompletně mapují na TrueDead** (jen 48 výjimek). Ale **Sporadic se rozpadá na 3 segmenty** s dramaticky odlišným chováním:
- SlowFull (10 197): stále pomalé, i s plným stockem
- SlowPartial (1 980): pomalé, ale krátký stock → 76.9% prodá po redistribuci
- ActiveSeller (1 856): aktivně se prodávající, RO 46%, OS 21%

---

## 6. "Sold After" metrika — nový prediktor

Metrika "kolik % source SKU se prodalo po navržení redistribuce" je silný prediktor rizika:

| Sold After% | Interpretace | Akce |
|---|---|---|
| >90% | Produkt je aktivní, odvoz je rizikový | ML ↑↑ (3-4) |
| 60-90% | Produkt se stále prodává | ML ↑ (2-3) |
| 30-60% | Smíšené | ML = (1-2) |
| <30% | Produkt je mrtvý, bezpečné odvézt | ML ↓ (1) |

---

## 7. Target strana: Stock coverage efekt

| Target stock 6M | SKU | Avg ST Tot | Nothing-sold 4M% | All-sold Tot% |
|---|---|---|---|---|
| 0 dní (nový) | 1 699 | 67.2% | 52.0% | 67.0% |
| 1-89 dní | 2 370 | 74.2% | 38.8% | 70.2% |
| 90-149 dní | 9 376 | 74.7% | 35.5% | 65.6% |
| 150+ dní (zavedený) | 28 186 | 67.1% | 44.0% | 56.4% |

**Překvapení:** Nové a krátkodobé target SKU (1-149 dní) mají LEPŠÍ sell-through než zavedené (150+ dní). Vysvětlení: zavedené SKU už mají zásobu a redistribuce přidává "zbytečně" navíc.

---

## 8. Navrhovaný Decision Tree v6 (Source)

### Segment × Store → ML (0-4)

| Segment | Weak | Mid | Strong | Důvod |
|---|---|---|---|---|
| **ActiveSeller** | 3 | 4 | 4 | RO 43-48%, sold 89-96%. Musí chránit. |
| **SlowFull** | 1 | 2 | 2 | RO 36-46%, sold 55-73%. Prodává se, ale pomalu. |
| **SlowPartial** | 2 | 2 | 3 | RO 30-37%, sold 71-84%. Překvapivě aktivní! |
| **PartialDead** | 1 | 1 | 2 | RO 34-38%, sold 49-62%. Krátký stock, nejisté. |
| **TrueDead** | 1 | 1 | 1 | RO 22-29%, sold 33-41%. Bezpečné. |
| **BriefNoSale** | 2 | 2 | 2 | Sold 71% — nový produkt? Opatrnost. |

> Constraint: Orderable → min ML=1.

---

## 9. Závěry a doporučení

1. **Velocity normalizace odhaluje skryté riziko:** 2 535 ActiveSeller SKU (6.9%) generuje nepřiměřené množství reorderu a oversell. V4 je částečně chytala jako Consistent/Sporadic+Strong, ale nepřesně.

2. **SlowPartial je nová kategorie:** 1 980 SKU s krátkou historií zásob a nízkou velocity, ale 76.9% se prodá po redistribuci. V4 je řadila pod Dead/Sporadic a navrhovala nízké ML — chyba.

3. **TrueDead je skutečně mrtvý:** 18 355 SKU s plným stockem a žádnými prodeji. Zde je redistribuce bezpečná (sold after jen 37%).

4. **Target: nové/krátkodobé SKU mají lepší ST** — redistribuce na "fresh" target je účinnější než na zavedený.
