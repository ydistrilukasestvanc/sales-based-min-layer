# Findings v2 - CalculationId=233, EntityListId=3

## Kontext
- Server: DEV, DB: ydistri-sql-db-dev-tenant-douglasde
- ApplicationDate: 2025-07-13, Shipping: 2025-07-14-2025-07-29
- AttributeValueId: kalkulace=134, aktualni=385 (2026-03-20)
- 42,404 paru, 36,770 source SKU, 41,631 target SKU, 48,754 ks

## Temp tabulky (prefix SBM_)
RedistSkus(42k), AllSkuIds(1.1M), Sales(6.3M), SalesExtended(159k), Supply(813k), Inbound(27k), Outbound(68k), SkuSnapshotCalc(78k), SkuSnapshotNow(78k), StoreStrength(352), StoreBrandStrength(38k), SourceMetrics(37k), TargetMetrics(42k), SourceProblems(37k), TargetProblems(42k), SourceFull(37k), TargetFull(42k), SourceSalesPattern(37k), SourceFeatures(37k), TargetFeatures(42k), RedistLoop(3.1k), PairAnalysis(42k), BacktestV2(37k)

## Source celkove metriky
| Metrika | 4M SKU | 4M qty | Total SKU | Total qty |
|---|---|---|---|---|
| Reorder | 7,087 (19.3%) | 7,980 | 13,841 (37.6%) | 16,615 |
| Oversell | 1,317 (3.6%) | 1,464 | 4,718 (12.8%) | 5,578 |

## Target celkove metriky
| Metrika | 4M | Total |
|---|---|---|
| ST | 46.3% | 70.1% |
| ST-1pc | 70.6% | 88.4% |
| All sold | 13,631 (32.7%) | 24,862 (59.7%) |
| 1 ks zbyva | - | 9,731 (23.4%) |
| Nothing sold | 17,552 (42.2%) | 8,872 (21.3%) |

## Source: 15 segmentu (Pattern x Store)
Dead+Weak: 4597, reorder=24.5%, oversell=5.1% -> lze snizit ML
Dead+Mid: 6967, 29.5%, 7.8% -> lze snizit ML
Dead+Strong: 4061, 31.4%, 10.0% -> OK
Dying+Weak: 1594, 29.7%, 8.1% -> lze snizit ML
Dying+Mid: 2882, 35.4%, 9.7% -> lze snizit ML
Dying+Strong: 1951, 37.1%, 12.6% -> OK
Sporadic+Weak: 2003, 37.2%, 10.9% -> OK
Sporadic+Mid: 4176, 44.1%, 15.3% -> OK
Sporadic+Strong: 3712, 47.8%, 20.1% -> zvysit ML
Consistent+Weak: 431, 46.4%, 13.2% -> OK
Consistent+Mid: 1164, 56.0%, 22.7% -> zvysit ML
Consistent+Strong: 1693, 56.5%, 28.0% -> zvysit ML
Declining+Weak: 219, 55.3%, 25.1% -> zvysit ML
Declining+Mid: 569, 64.7%, 28.3% -> zvysit ML
Declining+Strong: 751, 68.0%, 35.4% -> zvysit ML

## Target: ST/ST1 podla Store x Sales6M
Weak+Zero: ST=44.6%, ST1=68.6%, nothing=43.7%
Weak+Low: ST=54.6%, ST1=79.0%, nothing=34.6%
Weak+Med+: ST=78.3%, ST1=91.5%, nothing=12.6%
Mid+Zero: ST=49.4%, ST1=74.4%, nothing=39.3%
Mid+Low: ST=59.3%, ST1=82.7%, nothing=28.8%
Mid+Med+: ST=80.0%, ST1=92.4%, nothing=12.5%
Strong+Zero: ST=61.5%, ST1=87.6%, nothing=31.8%
Strong+Low: ST=66.9%, ST1=87.3%, nothing=22.3%
Strong+Med+: ST=83.4%, ST1=94.2%, nothing=9.0%

## Dalsie findings (detaily v HTML reportoch)
- Predajne vzorce: Dead(15.6k), Dying(6.4k), Sporadic(9.9k), Consistent(3.3k), Declining(1.5k)
- Sila predajne: reorder linearne D1=26%->D10=44%
- Brand-store fit: Strong+Strong 45.3% vs Weak+Weak 29.3% (16pp)
- Mesacna kadencia: 0M=28.5%->16M=81%, ML len 0.94->1.86
- Vianoce: 20-60% Xmas podiel = 25-27% oversell
- Promo: Declining NIE JE sposobeny promo
- Redistribucna slucka: 3,117 SKU (8.5%), 72% zero-sellers ML1
- Product concentration: <=20 predajni 17% reorder, 100+ 42.9%
- SkuClass delisting: -29pp reorder
- Parova: BEST 35.1%, IDEAL 11.6%, WASTED 14.8%, DOUBLE FAIL 6.6%
