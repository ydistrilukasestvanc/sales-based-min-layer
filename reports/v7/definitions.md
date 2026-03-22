# Definitions v7 — Kompletní algoritmický popis všech metrik a klasifikací

**Kalkulace:** 233 (Douglas DE) | **ApplicationDate:** 2025-07-13

---

## A. VSTUPNÉ PARAMETRE

```
ApplicationDate       = 2025-07-13                    -- z tabulky Calculation
Period_4M             = [2025-07-13, 2025-11-13)      -- 4 mesiace po redistribúcii
Period_Total          = [2025-07-13, today)            -- celé obdobie po redistribúcii (~9M)
Period_6M_Before      = [2025-01-13, 2025-07-13)
Period_12M_Before     = [2024-07-13, 2025-07-13)
Period_24M_Before     = [2023-07-13, 2025-07-13)
EntityListId          = 3                              -- kľúč v JSON MinLayerLists
Ecomm_Exclude         = WarehouseId = 300
ML_Range              = [0, 4]
Orderable_SkuClassId  = {9 (A-O), 11 (Z-O)}
Delisted_SkuClassId   = {3 (D), 4 (L)}
```

---

## B. SOURCE METRIKY

### B1. Oversell (PRIMÁRNA source metrika)
```
RemainingAfterRedist = SourceAvailableSupply - TotalQtyRedistributed
Oversell_Qty         = LEAST(GREATEST(Sales_Post - RemainingAfterRedist, 0), TotalQtyRedistributed)
Oversell_SKU         = 1 ak Oversell_Qty > 0
```
Prodalo sa viac, než čo zostalo na source. Cap na redistrib qty.

### B2. Reorder (source metrika)
```
Raw_Inbound  = SUM(Inbound.Quantity) za obdobie po ApplicationDate
Reorder_Qty  = LEAST(Raw_Inbound, TotalQtyRedistributed)
Reorder_SKU  = 1 ak Reorder_Qty > 0
```
Inbound po redistribúcii, cappovaný na redistrib qty. Nad tento cap by sa objednalo aj bez redistribúcie.

### B3. TotalQtyRedistributed (per source SKU)
```
TotalQtyRedistributed = SUM(SkuRedistributionExpanded.Quantity)
                        WHERE SourceSkuId = X AND CalculationId = 233
```

### B4. Sales_Post (per SKU, per obdobie)
```
Sales_Post = SUM(SaleTransaction.Quantity) WHERE SkuId = X AND Date IN period
```

---

## C. TARGET METRIKY

### C1. Sell-Through (ST)
```
Base = TargetAvailableSupply + TotalQtyReceived
Sold = SUM(SaleTransaction.Quantity) za obdobie
ST   = LEAST(Sold, Base) / Base × 100
```

### C2. Sell-Through-1pc (ST1)
```
Ak Sold >= Base:  ST1 = ST = 100%
Ak Sold < Base AND Base > 1:  ST1 = LEAST(Sold, Base - 1) / (Base - 1) × 100
Ak Base <= 1:  ST1 = NULL
```
ST1 = 100% keď zostáva presne 1 ks.

### C3. Nothing-Sold
```
NothingSold = 1 ak SUM(Sales_Post) = 0
```

### C4. All-Sold
```
AllSold = 1 ak SUM(Sales_Post) >= Base
```

### C5. TotalQtyReceived (per target SKU)
```
TotalQtyReceived = SUM(SkuRedistributionExpanded.Quantity)
                   WHERE TargetSkuId = X AND CalculationId = 233
```

---

## D. STOCK AVAILABILITY

### D1. DaysInStock (per SKU, per obdobie)
```
Pre každý záznam v SkuAvailableSupply:
    Ak AvailableSupply > 0:
        clip_start = MAX(record.DateFrom, period_start)
        clip_end   = MIN(COALESCE(record.DateTo, period_end), period_end)
        days       = DATEDIFF(DAY, clip_start, clip_end)
    Else: days = 0

DaysInStock = SUM(days) cez všetky záznamy v období
```

Počítajú sa DaysInStock_6M, DaysInStock_12M, DaysInStock_24M.

### D2. Velocity (mesačná predajná rýchlosť normalizovaná na dostupnosť)
```
Velocity_12M = CASE
    WHEN DaysInStock_12M > 0: Sales_12M / DaysInStock_12M × 30
    ELSE: NULL
END
```
Interpretácia: koľko kusov sa predá za 30 dní, keď je produkt na sklade. Eliminuje skreslenie krátkym stockom.

---

## E. SOURCE KLASIFIKÁCIE

### E1. Pattern (v5 prístup — raw predaje za 4 polročné obdobia)
```
H1 = SUM(Sales) za [2023-07-13, 2024-01-13)
H2 = SUM(Sales) za [2024-01-13, 2024-07-13)
H3 = SUM(Sales) za [2024-07-13, 2025-01-13)
H4 = SUM(Sales) za [2025-01-13, 2025-07-13)

ActiveMonths_24M = COUNT(DISTINCT year-month s aspoň 1 predajom) za 24M

Pattern:
    Ak ActiveMonths_24M = 0:                                    → Dead
    Ak H3 + H4 = 0 AND H1 + H2 > 0:                           → Dying
    Ak ActiveMonths_24M <= 4:                                   → Sporadic
    Ak H4 < H3 × 0.5 AND H3 < H2 × 0.5:                      → Declining
    Ak ActiveMonths_24M >= 12:                                  → Consistent
    Else:                                                       → Sporadic
```
**Problém:** Neberie do úvahy DaysInStock. SKU s 0 predajmi ale len 2 mesiacmi stocku = "Dead" aj keď to je nový produkt.

### E2. Velocity Segment (v6/v7 prístup — normalizované na stock)
```
Velocity_12M = (viď D2)

Segment:
    Ak DaysInStock_12M = 0:                                     → NoStock
    Ak Sales_12M = 0 AND DaysInStock_12M >= 270:                → TrueDead
    Ak Sales_12M = 0 AND DaysInStock_12M >= 90:                 → PartialDead
    Ak Sales_12M = 0 AND DaysInStock_12M < 90:                  → BriefNoSale
    Ak Velocity_12M >= 0.5:                                     → ActiveSeller
    Ak DaysInStock_12M >= 270:                                  → SlowFull
    Ak DaysInStock_12M >= 90:                                   → SlowPartial
    Else:                                                       → SlowBrief
```

### E3. SoldAfter (post-redistribučný prediktor)
```
SoldAfter = 1 ak SUM(SaleTransaction.Quantity) > 0 za obdobie po ApplicationDate
SoldAfter% = per segment AVG(SoldAfter) × 100
```

---

## F. STORE KLASIFIKÁCIE

### F1. StoreStrength (celková sila predajne)
```
Revenue_6M = SUM(SaleTransaction.Quantity × SaleTransaction.SalePrice)
             za [2025-01-13, 2025-07-13)
             pre všetky SKU daného WarehouseId (excl ecomm)

StoreDecile = NTILE(10) OVER (ORDER BY Revenue_6M)

StoreStrength:
    Decile 1-3:   → Weak
    Decile 4-7:   → Mid
    Decile 8-10:  → Strong
```

### F2. BrandQuintile (sila predajne v danom brande)
```
BrandRevenue_6M = SUM(Quantity × SalePrice) za 6M pred
                  filtrované na SKU daného BrandId + WarehouseId

BrandQuintile = NTILE(5) OVER (PARTITION BY BrandId ORDER BY BrandRevenue_6M)
```

### F3. BrandStoreFit (kombinácia celkovej sily a brand sily)
```
BrandFit:
    BrandQuintile <= 2:  → BrandWeak
    BrandQuintile = 3:   → BrandMid
    BrandQuintile >= 4:  → BrandStrong
```
Použitie: kombinácia StoreStrength × BrandFit → 3×3 matice. Silný prediktor target sell-through (~12pp rozdiel medzi BrandWeak a BrandStrong pri rovnakej StoreStrength).

---

## G. SOURCE MODIFIKÁTORY

### G1. LastSaleGap
```
LastSaleDate = MAX(SaleTransaction.Date) WHERE SkuId = X AND Date < ApplicationDate
LastSaleGapDays = DATEDIFF(DAY, LastSaleDate, ApplicationDate)
Ak žiadny predaj: LastSaleGapDays = NULL
```
Modifier: LastSaleGapDays ≤ 90 → source ML +1 (sold after 85-90%).

### G2. Seasonal (Xmas flag)
```
Sales_NovDec = SUM(Quantity) WHERE MONTH(Date) IN (11, 12) AND Date IN Period_12M_Before
Sales_12M    = SUM(Quantity) WHERE Date IN Period_12M_Before
XmasLift     = Sales_NovDec / Sales_12M × 100

SeasonalFlag = 1 ak XmasLift >= 20
```
Modifier: SeasonalFlag = 1 → source ML +1 (OS 2×, RO 1.5× oproti non-seasonal).

### G3. RedistRatio
```
RedistRatio = TotalQtyRedistributed / SourceAvailableSupply
```
Aký % zásoby odvážame. Modifier: RedistRatio >= 0.75 → source ML +1 (slabý, ale safeguard).

### G4. Delisting (SkuClass transition)
```
CalcSkuClassId    = SkuAttributeValue.SkuClassId WHERE AttributeValueId = 134 (calc date)
CurrentSkuClassId = SkuAttributeValue.SkuClassId WHERE AttributeValueId = 385 (current)

IsDelisted = 1 ak CurrentSkuClassId IN (3, 4) AND CalcSkuClassId NOT IN (3, 4)
```
Modifier: IsDelisted = 1 → ML = 0 (OVERRIDE, jediná cesta k ML=0 aj pre orderable).

### G5. Loop (redistribučná slučka)
```
LoopCount = COUNT(*) z Outbound WHERE OutboundTypeId IN (2, 5)
            AND Date IN Period_24M_Before AND SkuId = X
```
OutboundTypeId 2 = STORE TRANSFER, 5 = Y-STORE TRANSFER.
**Poznámka v7:** Na dátach CalculationId=233 len 7 SKU s loop 4+ → štatisticky nevýznamné. NEPOUŽÍVA SA ako modifier.

### G6. PhantomStock
```
PhantomFlag = 1 ak:
    Sales_6M = 0 alebo 1  AND
    Oversell_Total > 0  AND
    DaysInStock_6M >= 90  AND
    ProductHealthy = 1 (rovnaký product predáva na ≥50% ostatných predajní)
```
**Poznámka v7:** So správnym oversell vzorcom len 1 SKU spĺňa kritériá → NEPOUŽÍVA SA.

---

## H. TARGET MODIFIKÁTORY

### H1. AllSold / ST1 high
```
Modifier +1 ak: AllSold_4M = 1 OR ST1_4M >= 85%
```

### H2. Growth pocket
```
Modifier +1 ak: StoreStrength = 'Strong' AND Sales_12M IN [3, 10] AND ST_4M >= 45%
```

### H3. Strong absorber
```
Modifier +1 ak: StoreStrength IN ('Mid', 'Strong') AND Sales_12M >= 6 AND ST_4M >= 55%
```

### H4. Nothing-sold / low ST
```
Modifier -1 ak: NothingSold_4M = 1 OR ST_4M < 20%
```

### H5. BrandStoreMismatch
```
Modifier -1 ak: BrandFit = 'BrandWeak' AND ST_4M < 35%
```
**Poznámka v7:** BrandStoreFit má ~12pp dopad na ST a je konzistentný. V budúcich verziách zvážiť ako tretiu dimenziu target lookup tabuľky (SalesBucket × Store × BrandFit) namiesto jednoduchého modifieru.

### H6. Delisting
```
Modifier → ML = 0 ak IsDelisted = 1 (viď G4)
```

---

## I. CROSS-PRODUCT SIGNÁLY

### I1. ProductVolatilityScore
```
Pre každý ProductId:
    MonthlySalesPerStore = predaje per warehouse per mesiac za 12M
    AvgSales  = AVG(MonthlySalesPerStore)
    StdDev    = STDEV(MonthlySalesPerStore)
    CV        = StdDev / AvgSales  (Coefficient of Variation)

Buckety: Low (<1), Med (1-2), High (2-3), VHigh (3+)
```

### I2. ProductConcentrationShare
```
StoresWithSales_12M = COUNT(DISTINCT WarehouseId) kde SUM(Sales_12M) > 0
TotalStoresWithSku  = COUNT(DISTINCT WarehouseId) kde SKU existuje
ConcentrationShare  = StoresWithSales_12M / TotalStoresWithSku × 100
```
Na koľkých predajniach sa produkt predáva. **Poznámka v7:** Žiadny jasný gradient v oversell/reorder → nepoužíva sa ako modifier.

---

## J. TARGET STOCK COVERAGE

### J1. TargetStockCoverage
```
DaysInStock_6M_Target = (viď D1, ale pre TargetSkuId a Period_6M_Before)

Bucket:
    0 dní:        → New (nikdy nebol na tejto predajni)
    1-89 dní:     → Brief
    90-149 dní:   → Partial
    150+ dní:     → Established
```
**Zistenie v7:** Brief/New target má lepší ST (80% vs 67% u SalesBucket 3-5). Redistribúcia na "fresh" target je efektívnejšia.

---

## K. PÁROVÁ ANALÝZA

### K1. PairOutcome
```
Ak Oversell_Total = 0 AND ST_Total >= 50%: → Win-Win
Ak Oversell_Total = 0 AND ST_Total < 50%:  → Win-Lose
Ak Oversell_Total > 0 AND ST_Total >= 50%: → Lose-Win
Ak Oversell_Total > 0 AND ST_Total < 50%:  → Lose-Lose
```

---

## L. FLOW MATRIX

```
Pre každý redistribučný pár:
    SourceStrength = StoreStrength(SourceWarehouseId)
    TargetStrength = StoreStrength(TargetWarehouseId)

Matice: COUNT(pairs) GROUP BY SourceStrength, TargetStrength
```

---

## M. CLAMP PRAVIDLÁ

```
Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)

Ak IsOrderable = 1 (SkuClassId IN (9, 11)):
    Final_ML = MAX(Final_ML, 1)    -- NIKDY pod 1

Ak IsDelisted = 1:
    Final_ML = 0                   -- OVERRIDE všetkého
```
