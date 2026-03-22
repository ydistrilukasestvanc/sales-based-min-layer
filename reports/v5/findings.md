# Findings v5 — SalesBased MinLayers analytika

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13 | **ML rozsah:** 0-4
**Orderable (A-O, Z-O) → min ML=1, nikdy ML=0**

## 1. Validace vstupu

| Kontrola | Výsledek |
| --- | --- |
| Redistribučních párů | 42 404 |
| Redistribuovaných ks | 48 754 |
| Source SKU | 36 770 |
| Target SKU | 41 631 |
| Dotčených SKU celkem | 78 401 |
| Dotčených produktů | 5 152 |
| Prodejen v analytice | 353 |
| Duplicity párů | 0 |
| Source = Target | 0 |
| Non-positive qty | 0 |
| SKU bez supply historie | 0 |
| Missing calc/current snapshot | 0 / 0 |

Poznámka: 1 798 source párů nemá `SourceEntityMinLayer` v JSON. Ve všech těchto případech je `SourceMinLayerListQuantityRaw=0` a `SourceMinLayerLists=NULL`, proto jsou v `v5` brány jako aktuální `ML=0`.

## 2. Pokrytí prodeji před redistribucí

| Strana | SKU s alespoň 1 sale za 12M pre | Všechna SKU | Pokrytí |
| --- | --- | --- | --- |
| Source | 15 069 | 36 770 | 41.0% |
| Target | 40 457 | 41 631 | 97.2% |

Source strana je výrazně řidší než target. To potvrzuje, že část source ochrany musí stát víc na `pattern`, `last sale gap`, `stock presence` a `cross-product` signálech než jen na prosté frekvenci.

## 3. Overview metrik

### SOURCE

| Metrika | 4M SKU | 4M Qty | Total SKU | Total Qty |
| --- | --- | --- | --- | --- |
| Oversell | 1 317 (3.6%) | 1 464 (3.0%) | 4 718 (12.8%) | 5 578 (11.4%) |
| Reorder | 7 087 (19.3%) | 7 980 (16.4%) | 13 841 (37.6%) | 16 615 (34.1%) |

Čtení: `Oversell 4M` je pod cílem, ale `Reorder total` je stále vysoký. `v5` proto cílí hlavně na snížení zbytečně agresivního source odvozu, ne na další plošné zpřísnění všeho.

### TARGET

| Metrika | 4M | Total |
| --- | --- | --- |
| Avg Sell-Through | 45.3% | 69.2% |
| Avg ST-1pc | 58.2% | 79.6% |
| Nothing-sold | 17 552 (42.2%) | 8 872 (21.3%) |
| All-sold | 13 631 (32.7%) | 24 862 (59.7%) |

Čtení: target není jednostranně slabý. Vedle velké skupiny `nothing-sold` existuje i silná skupina `all-sold`, takže target pravidla musí jít oběma směry, ne jen ML snižovat.

## 4. Source segmentace: Pattern × StoreStrength

| Pattern | Store | SKU | Qty | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- | --- | --- |
| Dead | Weak | 4 987 | 6 009 | 4.6 | 22.4 |
| Dead | Mid | 6 003 | 7 398 | 7.2 | 27.2 |
| Dead | Strong | 4 523 | 5 732 | 9.1 | 28.6 |
| Dying | Weak | 1 757 | 2 135 | 6.6 | 26.1 |
| Dying | Mid | 2 346 | 2 860 | 8.8 | 31.6 |
| Dying | Strong | 2 085 | 2 536 | 10.6 | 33.4 |
| Sporadic | Weak | 2 819 | 3 715 | 10.8 | 36.4 |
| Sporadic | Mid | 4 437 | 6 048 | 15.4 | 40.7 |
| Sporadic | Strong | 5 289 | 7 820 | 18.0 | 43.4 |
| Consistent | Weak | 33 | 72 | 5.6 | 25.0 |
| Consistent | Mid | 44 | 91 | 15.4 | 49.5 |
| Consistent | Strong | 214 | 433 | 13.6 | 36.7 |
| Declining | Weak | 283 | 459 | 13.3 | 41.0 |
| Declining | Mid | 598 | 1 025 | 15.8 | 46.9 |
| Declining | Strong | 1 352 | 2 421 | 22.6 | 49.8 |

Klíčové závěry:
- Nejsilnější source riziko není `Dead`, ale `Declining` a `Sporadic` ve středních a silných prodejnách.
- `Declining/Strong` je nejhorší kombinace: vysoký `oversell` i `reorder`, tedy zjevně příliš agresivní source odvoz.
- `Dead/Weak` zůstává nejbezpečnější segment pro nízký source ML.

## 5. Target segmentace: SalesBucket × StoreStrength

| Sales 12M pre | Store | SKU | Avg ST 4M | Nothing-sold 4M | All-sold 4M |
| --- | --- | --- | --- | --- | --- |
| 0 | Weak | 186 | 19.3% | 77.4% | 17.2% |
| 0 | Mid | 259 | 26.6% | 70.3% | 24.3% |
| 0 | Strong | 278 | 34.8% | 62.9% | 33.5% |
| 1-2 | Weak | 1 935 | 26.7% | 65.0% | 18.4% |
| 1-2 | Mid | 3 893 | 27.4% | 63.6% | 18.3% |
| 1-2 | Strong | 4 253 | 32.5% | 57.4% | 22.5% |
| 3-5 | Weak | 2 562 | 39.3% | 47.0% | 25.7% |
| 3-5 | Mid | 6 395 | 41.4% | 45.1% | 28.0% |
| 3-5 | Strong | 10 426 | 44.8% | 41.2% | 31.0% |
| 6-10 | Weak | 980 | 58.9% | 26.6% | 44.6% |
| 6-10 | Mid | 2 733 | 59.0% | 27.0% | 45.0% |
| 6-10 | Strong | 5 379 | 62.9% | 22.8% | 49.0% |
| 11+ | Weak | 229 | 71.7% | 14.8% | 54.6% |
| 11+ | Mid | 695 | 72.5% | 11.9% | 55.8% |
| 11+ | Strong | 1 428 | 77.2% | 10.4% | 64.2% |

Klíčové závěry:
- Target problém je koncentrovaný hlavně v `0-2 sales` bucketu.
- `6+ sales` bucket už dává smysl brát jako kandidát na vyšší target ML.
- Silná prodejna pomáhá, ale sama o sobě nezachrání `0-2` bucket.

## 6. Cross-product a doplňkové signály

### RedistributionRatio

| Ratio | SKU | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- |
| 0-25% | 4 297 | 6.1 | 29.7 |
| 25-50% | 10 825 | 9.8 | 35.9 |
| 50-75% | 20 091 | 13.8 | 35.8 |
| 75-100%+ | 1 557 | 8.4 | 18.8 |

Interpretace: kritický není extrém `75-100%+`, ale široká skupina `50-75%`. Tam odvážíme dost na to, aby riziko citelně rostlo, ale ne tak málo případů jako v úplném extrému.

### ProductVolatilityScore

| Volatilita | SKU | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- |
| Low (<1) | 13 939 | 12.9 | 35.5 |
| Med (1-2) | 21 421 | 10.7 | 33.6 |
| High (2-3) | 1 327 | 5.9 | 23.1 |
| VHigh (3+) | 83 | 2.2 | 20.4 |

Tohle jde proti původní intuici. V `v5` volatilita není hlavní varovný source signál. Vyšší riziko nesou spíš produkty se stabilním, široce rozloženým demandem.

### Seasonal flag

| Skupina | SKU | Qty | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- | --- |
| Non-seasonal | 29 298 | 37 815 | 9.3 | 30.8 |
| Seasonal | 7 472 | 10 939 | 18.8 | 45.3 |

Seasonal SKU mají téměř dvojnásobný `oversell` i `reorder`. Ve `v5` jsou proto explicitní source modifikátor.

## 7. Redistribuční loop, SkuClass změny, phantom stock

### Loop

| Loop 24M | SKU | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- |
| None | 36 534 | 11.4 | 34.0 |
| 1 | 65 | 0.0 | 2.5 |
| 2-3 | 60 | 4.0 | 36.4 |
| 4+ | 111 | 28.3 | 62.0 |

`4+` loop je malá, ale extrémně riziková skupina. Není to plošný driver objemu, ale je to silný penalizační signál pro opatrnější source ML.

### SkuClass transition

| Změna | SKU | OS Tot Qty% | RO Tot Qty% | RO Tot SKU% |
| --- | --- | --- | --- | --- |
| Unchanged | 29 322 | 13.0 | 39.8 | 43.2 |
| Became delisted | 6 049 | 4.9 | 10.9 | 13.2 |
| Other change | 1 399 | 10.1 | 26.3 | 27.2 |

Přechod do `D/L` dramaticky snižuje source riziko. Proto je ve `v5` jediná tvrdá cesta k `ML=0`.

### Phantom stock

| Flag | SKU | OS Tot Qty% | RO Tot Qty% |
| --- | --- | --- | --- |
| 1 | 115 | 84.9 | 79.9 |
| 0 | 36 655 | 11.2 | 33.9 |

`Phantom stock` je malý objem, ale extrémní outlier. Filtr je přísný: dlouhá stock presence, skoro žádné sales, oversell po redistribuci a zároveň normální prodeje stejného produktu v jiných prodejnách.

## 8. Párové outcome

| Outcome 4M | Pairs | Podíl |
| --- | --- | --- |
| Win-Lose | 17 409 | 41.1% |
| Win-Win | 13 243 | 31.2% |
| Lose-Lose | 11 078 | 26.1% |
| Lose-Win | 674 | 1.6% |

Ve `v5` je hlavní opportunity `Win-Lose`, ale finální kalibrace už nejde jen směrem `target DOWN`. Výsledkem je obousměrný model: slabé transfery omezit a současně otevřít growth pockets tam, kde target potvrzuje vysokou absorpci.

## 9. Další target signály

| Signál | Skupina | Avg ST 4M | Nothing-sold 4M | All-sold 4M |
| --- | --- | --- | --- | --- |
| BrandStoreMismatch | 1 | 43.2% | 44.4% | 30.8% |
| BrandStoreMismatch | 0 | 46.2% | 41.1% | 33.7% |
| ProductConcentration | <10% | 12.5% | 85.7% | 10.7% |
| ProductConcentration | 10-25% | 20.0% | 71.0% | 11.2% |
| ProductConcentration | 25-50% | 30.3% | 59.6% | 20.3% |
| ProductConcentration | 50%+ | 46.4% | 40.9% | 33.7% |

`BrandStoreMismatch` je slabší, ale konzistentní negativní modifikátor. Silnější je nízká `ProductConcentrationShare`, kde target výsledky padají výrazně.

## 10. Shrnutí pro decision vrstvu

`v5` staví source rozhodování hlavně na:
- `Pattern`
- `StoreStrength`
- `LastSaleGap`
- `RedistributionRatio`
- `SeasonalFlag`
- `ProductConcentrationShare`
- `PhantomStock`
- `SkuClass transition`

`v5` staví target rozhodování hlavně na:
- `SalesBucket`
- `StoreStrength`
- `SellThrough`
- `ST-1pc`
- `NothingSold`
- `AllSold`
- `BrandStoreMismatch`
- `ProductConcentrationShare`
- `SkuClass transition`

## 11. Growth pockets pro vyšší objem

`v5` neříká jen kde ubrat. Z nových dat vychází i jasné kapsy, kde je prostor být agresivnější.

### Source: kde lze jít `ML DOWN`

| Segment | Qty | OS Tot Qty% | RO Tot Qty% | Interpretace |
| --- | --- | --- | --- | --- |
| Dead / Weak | 6 009 | 4.6 | 22.4 | Nejbezpečnější velký source segment. |
| Dead / Mid | 7 398 | 7.2 | 27.2 | Stále pod průměrem source rizika. |
| Dying / Weak | 2 135 | 6.6 | 26.1 | Dlouhý `LastSaleGap`, ale ještě ne kritický oversell. |

### Target: kde lze jít `ML UP`

| Segment | Qty | Avg ST 4M | All-sold 4M | Interpretace |
| --- | --- | --- | --- | --- |
| 11+ / Strong | 2 257 | 77.2% | 64.2% | Nejčistší kandidát na vyšší absorpci. |
| 11+ / Mid | 1 520 | 72.5% | 55.8% | Stabilně silný target. |
| 6-10 / Strong | 6 394 | 62.9% | 49.0% | Velký objem se slušnou absorpcí. |
| 6-10 / Mid | 3 399 | 59.0% | 45.0% | Druhá vlna expanze po strong stores. |
| 3-5 / Strong | 11 460 | 44.8% | 31.0% | Jen selektivně přes `AllSold` a `ST-1pc`, ne plošně. |

Praktický závěr: finální kalibrace `v5` už není čistě defenzivní. Target strana je skoro netto neutrální a report explicitně odlišuje reduction pockets od growth pockets.

