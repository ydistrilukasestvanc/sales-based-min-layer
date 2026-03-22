# Decision tree v5 — Source & Target MinLayer pravidla

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13
**ML rozsah:** 0-4 | **Orderable (A-O, Z-O) → min ML=1**

## 1. Princip v5

`v5` nevychází z dřívějších verzí, ale z nově postavené feature vrstvy v `temp.SBM_v5_*`. Základní logika:

- `source` chrání před zbytečně agresivním odvozem tam, kde rostou zároveň `oversell` i `reorder`
- `target` snižuje ML tam, kde se opakovaně nepotvrdí `sell-through`, ale zároveň aktivně hledá growth pockets
- obě strany mají samostatný lookup a až potom modifikátory
- `D/L` je jediná tvrdá cesta k `ML=0`
- `orderable` SKU nikdy nesmí skončit pod `ML=1`

## 2. SOURCE lookup

### Base lookup: Pattern × StoreStrength

| Pattern | Weak | Mid | Strong |
| --- | --- | --- | --- |
| Dead | 0 | 1 | 1 |
| Dying | 1 | 1 | 2 |
| Sporadic | 1 | 2 | 2 |
| Consistent | 2 | 3 | 4 |
| Declining | 1 | 2 | 3 |

### Source modifikátory

| Modifikátor | Podmínka | Úprava |
| --- | --- | --- |
| LastSaleGap short | `LastSaleGapDays <= 30` | `+1` |
| RedistributionRatio high | `RedistributionRatio >= 0.75` | `+1` |
| Seasonal | `XmasLift >= 20%` | `+1` |
| Product concentration low | `ProductConcentrationShare < 10%` | `+1` |
| Phantom stock | `PhantomStockFlag = 1` | `-1` |
| Dead / Weak growth pocket | `Pattern='Dead' AND Store='Weak'` | `-1` |
| Dead / Mid growth pocket | `Pattern='Dead' AND Store='Mid' AND RedistributionRatio < 50%` | `-1` |
| Dying / Weak growth pocket | `Pattern='Dying' AND Store='Weak' AND LastSaleGapDays >= 365` | `-1` |
| Became delisted | `CurrentSkuClassId in (3,4) AND CalcSkuClassId not in (3,4)` | `ML=0` |

### Source clamp pravidla

- výsledek clamp na `0-4`
- pokud `IsOrderableCalc=1`, minimum je vždy `1`
- `ML=0` jen pro delisted / non-orderable situace

## 3. TARGET lookup

### Base lookup: SalesBucket × StoreStrength

| Sales 12M pre | Weak | Mid | Strong |
| --- | --- | --- | --- |
| 0 | 1 | 1 | 1 |
| 1-2 | 1 | 1 | 2 |
| 3-5 | 1 | 2 | 3 |
| 6-10 | 2 | 3 | 3 |
| 11+ | 2 | 3 | 4 |

### Target modifikátory

| Modifikátor | Podmínka | Úprava |
| --- | --- | --- |
| All-sold / ST-1pc high | `AllSold4M = 1 OR ST1_4M >= 85%` | `+1` |
| 3-10 sales growth pocket | `Store='Strong' AND Sales 3-10 AND ST4M >= 45%` | `+1` |
| 6+ sales strong absorber | `Store in (Mid,Strong) AND Sales>=6 AND ST4M >= 55%` | `+1` |
| Nothing-sold / very low ST | `NothingSold4M = 1 OR ST4M < 20%` | `-1` |
| Brand-store mismatch | `BrandStoreMismatch = 1 AND ST4M < 35%` | `-1` |
| Very low concentration | `ProductConcentrationShare < 10% AND ST4M < 35%` | `-1` |
| Became delisted | `CurrentSkuClassId in (3,4) AND CalcSkuClassId not in (3,4)` | `ML=0` |

### Target clamp pravidla

- výsledek clamp na `0-4`
- pokud `IsOrderableCalc=1`, minimum je vždy `1`
- `ML=0` jen pro delisted / non-orderable situace

## 4. Jak číst 4 směry

### Source up

Použít tam, kde chceme na source ponechat víc kusů. Hlavní kandidáti:
- `Sporadic/Mid-Strong`
- `Declining/Strong`
- `Consistent/Mid-Strong`
- seasonal nebo short `LastSaleGap`

### Source down

Použít tam, kde je source riziko nízké a je prostor růst objemu:
- `Dead/Weak`
- `Dead/Mid` s nižším `RedistributionRatio`
- `Dying/Weak` s dlouhým `LastSaleGap`
- část `Sporadic` segmentů s nízkou současnou ochranou

### Target up

Použít tam, kde target opakovaně prodá skoro vše nebo rychle absorbuje větší objem:
- `11+ / Strong`
- `11+ / Mid`
- `6-10 / Strong`
- `6-10 / Mid`
- `3-5 / Strong`
- část `3-5 / Mid`

### Target down

Použít tam, kde redistribuce často nic neprodá:
- `0 / all stores`
- `1-2 / all stores`
- slabší část `3-5 / Weak-Mid`
- `BrandStoreMismatch`
- nízká `ProductConcentrationShare`

## 5. Proč je v5 obousměrné

`v5` už není jen defenzivní:
- source stále chrání rizikové segmenty proti vysokému `reorder`
- target už není nastavené na plošné `DOWN`, ale je téměř netto neutrální
- pravidla aktivně přesouvají objem z nefunkčních transferů do growth pockets s vyšší absorpcí

## 6. Priority zavedení

1. Nasadit `target UP` pro `11+ / Mid-Strong`, `6-10 / Mid-Strong`, `3-5 / Strong` s potvrzeným `ST`.
2. Nasadit `source DOWN` pro `Dead / Weak`, `Dead / Mid`, `Dying / Weak` jako growth pockets.
3. Držet `source UP` pro `Sporadic/Strong`, `Sporadic/Mid`, `Declining/Strong`.
4. Nasadit tvrdé `ML=0` jen pro potvrzené `D/L`.
