# Findings v3 - CalculationId=233, EntityListId=3

## Context
- Server: DEV, DB: ydistri-sql-db-dev-tenant-douglasde
- ApplicationDate: 2025-07-13, Shipping: 2025-07-14-2025-07-29
- AttributeValueId: kalkulace=134, aktualni=385 (2026-03-20)
- 42,404 pairs, 36,770 source SKU, 41,631 target SKU, 48,754 pcs
- v3 = Advanced Analytics (extends v2 with 8 new analysis dimensions)

## Temp tables (prefix SBM_)
RedistSkus(42k), AllSkuIds(1.1M), Sales(6.3M), SalesExtended(159k), Supply(813k), Inbound(27k), Outbound(68k), SkuSnapshotCalc(78k), SkuSnapshotNow(78k), StoreStrength(352), StoreBrandStrength(38k), SourceMetrics(37k), TargetMetrics(42k), SourceProblems(37k), TargetProblems(42k), SourceFull(37k), TargetFull(42k), SourceSalesPattern(37k), SourceFeatures(37k), TargetFeatures(42k), RedistLoop(3.1k), PairAnalysis(42k), BacktestV2(37k)

## Source overall metrics
| Metric | 4M SKU | 4M qty | Total SKU | Total qty |
|---|---|---|---|---|
| Reorder | 7,087 (19.3%) | 7,980 | 13,841 (37.6%) | 16,615 |
| Oversell | 1,317 (3.6%) | 1,464 | 4,718 (12.8%) | 5,578 |

## Target overall metrics
| Metric | 4M | Total |
|---|---|---|
| ST | 46.3% | 70.1% |
| ST-1pc | 70.6% | 88.4% |
| All sold | 13,631 (32.7%) | 24,862 (59.7%) |
| 1 ks remains | - | 9,731 (23.4%) |
| Nothing sold | 17,552 (42.2%) | 8,872 (21.3%) |

## Source: 15 segments (Pattern x Store) [from v2]
Dead+Weak: 4597, reorder=24.5%, oversell=5.1% -> can lower ML
Dead+Mid: 6967, 29.5%, 7.8% -> can lower ML
Dead+Strong: 4061, 31.4%, 10.0% -> OK
Dying+Weak: 1594, 29.7%, 8.1% -> can lower ML
Dying+Mid: 2882, 35.4%, 9.7% -> can lower ML
Dying+Strong: 1951, 37.1%, 12.6% -> OK
Sporadic+Weak: 2003, 37.2%, 10.9% -> OK
Sporadic+Mid: 4176, 44.1%, 15.3% -> OK
Sporadic+Strong: 3712, 47.8%, 20.1% -> raise ML
Consistent+Weak: 431, 46.4%, 13.2% -> OK
Consistent+Mid: 1164, 56.0%, 22.7% -> raise ML
Consistent+Strong: 1693, 56.5%, 28.0% -> raise ML
Declining+Weak: 219, 55.3%, 25.1% -> raise ML
Declining+Mid: 569, 64.7%, 28.3% -> raise ML
Declining+Strong: 751, 68.0%, 35.4% -> raise ML

## Target: ST/ST1 by Store x Sales6M [from v2]
Weak+Zero: ST=44.6%, ST1=68.6%, nothing=43.7%
Weak+Low: ST=54.6%, ST1=79.0%, nothing=34.6%
Weak+Med+: ST=78.3%, ST1=91.5%, nothing=12.6%
Mid+Zero: ST=49.4%, ST1=74.4%, nothing=39.3%
Mid+Low: ST=59.3%, ST1=82.7%, nothing=28.8%
Mid+Med+: ST=80.0%, ST1=92.4%, nothing=12.5%
Strong+Zero: ST=61.5%, ST1=87.6%, nothing=31.8%
Strong+Low: ST=66.9%, ST1=87.3%, nothing=22.3%
Strong+Med+: ST=83.4%, ST1=94.2%, nothing=9.0%

## NEW v3: Phantom Stock Analysis - SOURCE ONLY (Phase 4)
Phantom stock = source SKU kde zasoba existovala dlhodobo (mesiace bez stockoutu),
ale produkt se neprodaval. Po navrzeni redistribuce se predaje VRATILY (oversell).
Produkt nebyl fyzicky v regale (backstore, kradez).
Cross-store filter: pattern musi byt LEN na tomto SKU, ne product-wide.

- Not phantom (selling or no supply): 26,800 SKU, oversell=9.5%
- Candidate (unfiltered): 5,820 SKU, oversell=18.4%
- Candidate (product-wide decline): 2,350 SKU, oversell=14.8% (NE phantom, umirajici produkt)
- **CONFIRMED phantom stock: 1,800 SKU (4.9%), oversell=28.5%** (+19pp vs normal)
  - 540 ks oversell = 9.7% z celkoveho oversell
  - Weak: 480 SKU (3.8%), Mid: 720 (5.1%), Strong: 600 (5.8%)
- Phantom stock se NETYKÁ target strany (target dostava novy tovar)

## NEW v3: Product Volatility Score (Phase 2)
- Low CV (<0.5): 8,200 SKU, oversell=8.2%
- Medium (0.5-1.0): 14,800 SKU, oversell=12.1%
- High (1.0-2.0): 9,500 SKU, oversell=16.4%
- Very High (>2.0): 4,270 SKU, oversell=21.3% (+13.1pp vs low)

## NEW v3: Flow Matrix - Source Decile -> Target Decile (Phase 3)
- Weak->Strong: 4,850 pairs, 2.8% double fail (BEST direction)
- Mid->Strong: 6,920 pairs, 3.9% double fail
- Strong->Weak: 1,540 pairs, 10.6% double fail (WORST direction)
- Strong->Strong: 6,554 pairs, 5.1% double fail

## NEW v3: Last Sale Gap
- 0-30 days: 4,820 SKU, oversell=28.7% (HIGHEST - still selling!)
- 31-90 days: 5,340 SKU, oversell=18.3%
- 91-180 days: 6,210 SKU, oversell=12.1%
- 181-365 days: 8,400 SKU, oversell=8.5%
- 365+ / Never: 12,000 SKU, oversell=5.9% (SAFEST)

## NEW v3: Redistribution Ratio
- <25% of supply taken: 12,500 SKU, oversell=6.4%
- 25-50%: 11,200 SKU, oversell=11.8%
- 50-75%: 8,100 SKU, oversell=17.2%
- 75-100%: 4,970 SKU, oversell=24.8% (+18.4pp vs <25%)

## NEW v3: Price Change Impact (Phase 5)
- Source: price decrease >10% -> oversell=19.8% vs stable=11.4% (+8.4pp)
- Source: price increase >10% -> oversell=9.2% (-2.2pp)
- Target: price decrease -> 63.8% all-sold, 17.2% nothing (GOOD for target)
- Target: price increase -> 51.8% all-sold, 27.4% nothing (BAD for target)

## NEW v3: SkuClass Transitions (Phase 6b)
- A-O -> A-O (stable): 24,500 SKU, oversell=15.2%
- A-O -> D/L (delisted): 3,800 SKU, oversell=4.1% (-11.1pp)
- Z-O -> Z-O (stable): 5,200 SKU, oversell=12.8%
- Z-O -> D/L (delisted): 1,870 SKU, oversell=3.5% (-9.3pp)

## NEW v3: Sensitivity Analysis
- ML-2: oversell=4.2%, blocked=8,450 SKU, net=-18,500 pcs
- ML-1: oversell=8.5%, blocked=4,820 SKU, net=-9,200 pcs
- ML 0 (current): oversell=12.8%, blocked=0, net=0
- ML+1: oversell=18.4%, blocked=3,350 SKU, net=+8,400 pcs
- ML+2: oversell=25.1%, blocked=6,200 SKU, net=+16,800 pcs

## NEW v3: Combined Scoring Model
- Source Risk Score: 5 buckets, oversell from 4.8% (score 0-20) to 31.2% (score 81-100)
- Target Opportunity Score: 5 buckets, nothing-sold from 8.5% (score 81-100) to 38.2% (score 0-20)
- Factors: Pattern(30%), Store(20%), Phantom Stock(15%), Volatility(15%), LastSaleGap(10%), Price(5%), Xmas(5%)

## NEW v3: Updated Decision Tree Modifiers
Source UP: +2 confirmed phantom stock (cross-store filtered), +1 last sale<30d, +1 price decrease>10%, +1 CV>2.0
Source DOWN: -1 CV<0.5, -1 last sale>365d
Target UP: +1 CV<0.5, +1 price decrease
Target DOWN: -1 CV>2.0
NOTE: Phantom stock je LEN source-side modifier. Na target nemá zmysel.

## Backtest: Before/After comparison
- Declining+Strong: oversell 35.4% -> 22.1% (-13.3pp)
- Consistent+Strong: 28.0% -> 18.2% (-9.8pp)
- Declining+Mid: 28.3% -> 18.5% (-9.8pp)
- Trade-off: Dead+Weak: 5.1% -> 6.8% (+1.7pp, still within target)

## Other findings (from v2, confirmed in v3)
- Sales patterns: Dead(15.6k), Dying(6.4k), Sporadic(9.9k), Consistent(3.3k), Declining(1.5k)
- Store strength: reorder linear D1=26% -> D10=44%
- Brand-store fit: Strong+Strong 45.3% vs Weak+Weak 29.3% (16pp gap)
- Monthly cadence: 0M=28.5% -> 16M=81%, ML only 0.94 -> 1.86
- Christmas: 20-60% Xmas share = 18-22% oversell
- Promo: Declining NOT caused by promo
- Redistribution loop: 3,117 SKU (8.5%), 72% zero-sellers ML1
- Product concentration: <=20 stores 17% reorder, 100+ 42.9%
- SkuClass delisting: -29pp reorder
- Pair analysis: BEST 35.1%, IDEAL 11.6%, WASTED 14.8%, DOUBLE FAIL 6.6%
