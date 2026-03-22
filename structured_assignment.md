# Strukturované zadání: Analytika SalesBased MinLayers

## GLOBÁLNE INŠTRUKCIE

### Všeobecné
- **JAZYK:** Vysvetlenia a texty v reportoch VŽDY ČESKY. Parametre, premenné, termíny (source, target, sell-through, oversell, reorder, MinLayer, SKU, ...) VŽDY anglicky.
- **Výstupy = vždy 4 dokumenty:** 1) Findings (zistenia + korelácie), 2) Decision tree (pravidlá), 3) Backtest (dopad pravidiel s objemami), 4) Definitions (kompletný algoritmický popis všetkých metrík a klasifikácií).
- **Výstupy VŽDY aj GRAFICKY** — Python skript (`generate_consolidated_reports.py`) generuje HTML reporty + PNG grafy (heatmapy, bar charty, scatter ploty, waterfall). Skript používa matplotlib + seaborn, embedded dáta, generuje self-contained HTML s CSS + navigáciou medzi reportmi.
- **Reporty sú VERZOVANÉ** v podadresároch `reports/vX/`. Každá verzia je self-contained. Staré verzie sa nemažú.
- **Toto zadanie NEOBSAHUJE výsledky.** Tu sú len inštrukcie, vzorce, prístupy a pravidlá.
- **Nová verzia začína s čistým štítom.**
- **Overview tabuľka VŽDY obsahuje:** oversell (SKU + qty), reorder (SKU + qty), sell-through + ST-1pc (qty) – vždy 4M aj total.
- **MinLayer rozsah: 0-4.** 0 = odvézt/neposlať všetko. 4 = maximálna ochrana.
- **HARD CONSTRAINT:** A-O (9) a Z-O (11) = ORDERABLE → NIKDY ML=0. Minimum ML=1. ML=0 len pre delisted (D/L) alebo non-orderable. Jediná výnimka: delisting override.

---

## METRIKY — vzorce

Vo VŠETKÝCH štatistikách VŽDY uvádzať OBE source metriky (oversell + reorder) vedľa seba. Vždy 4M aj total.

### OVERSELL (primárna source metrika)
Predalo sa viac, než čo na source **zostalo** po redistribúcii. Cappované na redistrib. qty.
```
RemainingAfterRedist = SourceAvailableSupply - TotalQtyRedistributed
Oversell_Qty = LEAST(GREATEST(Sales_Post - RemainingAfterRedist, 0), TotalQtyRedistributed)
```
- Oversell nastáva IBA ak predaj prekročí zostatok. Ak predá menej než zostalo → oversell = 0.
- Cap na `TotalQtyRedistributed` = nemôže byť oversell viac ks než sme odviezli.

| Supply | Redist | Remaining | Sales Post | Oversell |
|---|---|---|---|---|
| 5 | 1 | 4 | 3 | MAX(3-4,0) = **0** |
| 2 | 1 | 1 | 2 | MIN(MAX(2-1,0), 1) = **1** |
| 3 | 2 | 1 | 5 | MIN(MAX(5-1,0), 2) = **2** (cap) |
| 3 | 1 | 2 | 0 | MAX(0-2,0) = **0** (nič sa nepredalo) |

### REORDER (source metrika)
Inbound po redistribúcii — cappované na redistrib. qty (rovnaký princíp ako oversell).
```
Reorder_Qty = LEAST(SUM(Inbound.Quantity), TotalQtyRedistributed)
```
Bežné doobjednávky prekračujúce redistribuované množstvo sa nepočítajú — tie by sa objednali aj bez redistribúcie.

### SELL-THROUGH (ST) (primárna target metrika)
```
Base = TargetAvailableSupply + TotalQtyReceived
ST = LEAST(Sold, Base) / Base × 100
```

### SELL-THROUGH-1pc (ST1) (doplnková target metrika)
Ideálny stav = zostáva presne 1 ks. ST1 = 100% pri 1 ks zvyšku.
```
Ak Sold >= Base:  ST1 = 100%
Ak Sold < Base AND Base > 1:  ST1 = LEAST(Sold, Base-1) / (Base-1) × 100
Ak Base <= 1:  ST1 = NULL
```

### NOTHING-SOLD / ALL-SOLD (target flagy)
```
NothingSold = 1 ak Sales_Post = 0
AllSold = 1 ak Sales_Post >= Base
```

---

## CIELE

### Source
- **Cieľ OVERSELL:** 4M: 5-10%, total: <20%.
- **Cieľ REORDER:** znížiť o 10-15% oproti aktuálnemu stavu. Reorder indikuje, že source bol príliš agresívne vyčerpaný.
- Source ML sa môže aj ZNÍŽIŤ — ak sa dá identifikovať, že produkty sa nepredávajú.

### Target — ROVNAKO DÔLEŽITÉ ako source
- **All-sold = ÚSPECH** → signál na zvýšenie ML.
- **Nothing-sold = PROBLÉM** → zbytočná redistribúcia.
- **Low ST (<30% po 4M)** → ML znížiť.
- Target analytika musí byť ROVNAKO podrobná ako source.
- **Bidirectionálny prístup:** nielen znižovať (reduction pockets), ale aj zvyšovať (growth pockets) tam, kde target preukázateľne absorbuje.

### Backtest
- Backtest vždy na SALES (oversell + reorder), nie na inbound.
- Musí ukazovať zmenu OBJEMU redistribúcie (koľko ks viac/menej).
- **Decision tree: 4 smery:** source up, source down, target up, target down.

---

## PARAMETRE ANALÝZY

| Parametr | Hodnota |
|---|---|
| Server | DEV |
| Databáze | ydistri-sql-db-dev-tenant-douglasde |
| CalculationId | 233 |
| EntityListId | 3 (kľúč v JSON SourceMinLayerLists/TargetMinLayerLists) |
| Referenčný dátum | ApplicationDate z tabulky Calculation |
| Ecomm (vylúčiť) | WarehouseId = 300 |
| MinLayer JSON | SkuPotential.SourceMinLayerLists / TargetMinLayerLists |
| ForecastQuantity | IGNOROVAŤ (chybný údaj) |
| Temp schéma prefix | SBM_[version]_ |
| DB pripojenie | MCP server `ydistri-kb` → tool `mcp__ydistri-kb__query_database` |

---

## KLÍČOVÉ TABULKY

| Tabulka | Účel | Kľúčové stĺpce |
|---|---|---|
| SkuRedistributionExpanded | Redistribučné páry | SourceSkuId, TargetSkuId, Quantity, *MinLayerListQuantity |
| SkuPotential | MinLayer JSON detaily | SourceMinLayerLists, TargetMinLayerLists (JSON) |
| SaleTransaction | Predaje | SkuId, Date, IsPromo, Quantity, SalePrice |
| SkuAvailableSupply | História zásoby | SkuId, DateFrom, DateTo, AvailableSupply |
| Inbound | Príjmy (reorder) | SkuId, Date, InboundTypeId, Quantity |
| Outbound | Výdaje | SkuId, Date, OutboundTypeId, Quantity |
| SkuAttributeValue | Historický snapshot | SkuId, AttributeValueId, SkuClassId, Frequency*, SalePrice |
| AttributeValue | Mapovanie na dátum | AttributeValueId → ApplicationDate |
| Warehouse | Predajne | WarehouseId, RegionId, WarehouseTypeId |
| SkuClass | Triedy SKU | 9=A-O, 11=Z-O (orderable), 3=D, 4=L (delisted) |

---

## POSTUP PRÁCE — FÁZE

### FÁZE 0: Príprava dát
Vytvoriť a naindexovať v temp schéme:
1. Redistribučné páry s MinLayer z JSON (EntityListId)
2. Všetky SKU dotčených produktov (excl ecomm) — pre cross-product analýzu
3. Predaje 12M pred + 9M po redistribúcii (+ 24M pre vzorce)
4. Zásoby (SkuAvailableSupply) pre source+target — potrebné pre DaysInStock výpočet
5. Inbound/Outbound po redistribúcii
6. SkuAttributeValue snapshot k dátumu kalkulácie + aktuálny
7. Sila predajní: decily podľa tržieb 6M (StoreStrength: Weak/Mid/Strong)
8. Brand sila: kvintily per brand (BrandFit: BrandWeak/BrandMid/BrandStrong)
9. **DaysInStock** per source SKU per obdobie (z SkuAvailableSupply — koľko dní mal SKU stock > 0)

### FÁZE 1: Validácia dát
- Distribúcia Quantity (min/max/median/percentily)
- Pokrytie predajov: koľko source/target SKU má aspoň 1 predaj za 12M
- Zásoby: pokrytie AvailableSupply záznamov
- Sanity checks: negatívne qty, duplicity, source=target
- Výstup: report s flagmi PRED pokračovaním

### FÁZE 2: Základné metriky
**Source:** predaje 6M/12M pred, 4M/total po, reorder (4M + total), oversell (4M + total)
**Target:** predaje 6M/12M pred, 4M/total po, sell-through (ST + ST-1pc, 4M + total), nothing-sold, all-sold

Výstup: overview tabuľka (SKU count + qty pre každú metriku, 4M + total).

### FÁZE 3: Source klasifikácia — Velocity Segmenty

#### 3a. Kalendárna korekcia (PRED klasifikáciou)
Douglas = parfuméria → VŠETKY produkty sú seasonal (Vianoce = darčeky). Neidentifikovať seasonal per SKU — namiesto toho korigovať vstupné dáta:
```
CalendarWeight = 0.7 ak polročné obdobie obsahuje Nov+Dec, inak 1.0
Adjusted_Sales(period) = Raw_Sales(period) × CalendarWeight(period)
```
Dôvod: Nov+Dec generujú ~24% ročných predajov namiesto očakávaných ~17% (lift 1.42×). Bez korekcie Velocity a Pattern sú skreslené.

#### 3b. Velocity normalizácia (PREFEROVANÁ klasifikácia)
```
Velocity_12M = Adjusted_Sales_12M / DaysInStock_12M × 30
```
DaysInStock = počet dní s AvailableSupply > 0 v danom období (z SkuAvailableSupply). Eliminuje skreslenie krátkym stockom — SKU na sklade 2 mesiace s 1 predajom ≠ mŕtve.

**Segmenty:**
| Segment | Definícia | Typické chovanie |
|---|---|---|
| **TrueDead** | 0 predajov, stock ≥270 dní | Naozaj mŕtve. Bezpečné na redistribúciu. |
| **PartialDead** | 0 predajov, stock 90-270 dní | Krátky stock, neisté. Opatrnosť. |
| **BriefNoSale** | 0 predajov, stock <90 dní | Príliš nové na záver. |
| **ActiveSeller** | Velocity ≥0.5/mesiac | Aktívne sa predáva! Chrániť. |
| **SlowFull** | Velocity <0.5, stock ≥270 dní | Pomalé, ale dlhodobo na sklade. |
| **SlowPartial** | Velocity <0.5, stock 90-270 dní | Krátky stock, rozjíždí sa. Prekvapivo aktívne. |

#### 3c. SoldAfter% (post-redistribučný prediktor)
```
SoldAfter = 1 ak source SKU malo aspoň 1 predaj po ApplicationDate
```
Silný prediktor rizika redistribúcie. Per-segment priemer určuje, či je bezpečné odvážať.

#### 3d. LastSaleGap
```
LastSaleGapDays = DATEDIFF(DAY, MAX(SaleDate pred ApplicationDate), ApplicationDate)
```
Krátky gap (≤90 dní) = produkt sa nedávno predal = rizikovejšie odvážať.

### FÁZE 4: Cross-product analýza
- Product Volatility Score — CV (StdDev/Mean) predajov medzi predajňami/mesiacmi
- Product Concentration — na koľkých predajniach sa produkt predáva (% stores s prodejem)
- **Redistribučný ratio** = TotalQtyRedistributed / SourceAvailableSupply

### FÁZE 5: Sila predajní a Brand-Store Fit

#### StoreStrength
```
Revenue_6M = SUM(SaleTransaction.Quantity × SalePrice) za 6M pred redistribúciou
StoreDecile = NTILE(10) OVER (ORDER BY Revenue_6M)
Weak = Decile 1-3, Mid = 4-7, Strong = 8-10
```

#### BrandFit
Meria, ako dobre daný **obchod** predáva danú **značku** v porovnaní s ostatnými obchodmi predávajúcimi tú istú značku. Nejde o porovnanie značiek medzi sebou (napr. L'Oréal vs Hugo Boss), ale o to, ktoré obchody sú pre konkrétnu značku silné/slabé.
```
-- Granularita: jeden riadok = (WarehouseId, BrandId)
BrandRevenue_6M = SUM(Quantity × SalePrice) za 6M, GROUP BY WarehouseId, BrandId
BrandQuintile = NTILE(5) OVER (PARTITION BY BrandId ORDER BY BrandRevenue_6M)
BrandWeak = Q1-2, BrandMid = Q3, BrandStrong = Q4-5
```
Príklad: Ak obchod A predáva L'Oréal za 10 000€ (Q5 = BrandStrong) a obchod B za 500€ (Q1 = BrandWeak), redistribúcia L'Oréal produktov do obchodu A má vyššiu šancu na úspech.

**BrandStoreFit je silný prediktor (~12pp dopad na ST).** Efekt je graduovaný:
- **Na target strane:** Najsilnejší pri nízkom SalesBucket (0-2 sales: delta +10-40pp ST). Pri 6+ sales irelevantný — predaje hovoria samy za seba.
- **Na source strane:** BrandStrong source SKU sa predávajú o 5-11pp viac po redistribúcii. Najsilnejší efekt pri SlowFull a TrueDead. Redistribúcia z BrandStrong source je rizikovejšia.

#### Matice prietoku
Odkiaľ kam tečie redistribúcia: StoreStrength(source) × StoreStrength(target).

### FÁZE 6: Phantom Stock (LEN SOURCE)
Phantom stock = source SKU kde zásoby existovali dlhodobo, žiadne predaje, ale po redistribúcii sa predaje vrátili. Cross-store filter: vzorec musí byť len na tomto SKU, nie celoplošne.

**Poznámka:** So správnym oversell vzorcom (RemainingAfterRedist) je phantom stock typicky minimálny (<10 SKU). Analyzovať, ale neočakávať veľký objem.

### FÁZE 7: Redistribučná slučka
Detekcia cez Outbound s OutboundTypeId pre Y-STORE TRANSFER / STORE TRANSFER. Korelovat s oversell/reorder.

**Poznámka:** Typicky veľmi malá skupina (<200 SKU s 2+ loop). Analyzovať, ale neočakávať štatistickú signifikantnosť.

### FÁZE 8: Cenová a sezónna analýza
**Cenová:** pásma vs oversell/sell-through, cenové zmeny, promo podiel.
**Sezónna:** Riešená cez CalendarWeight (FÁZE 3a), nie per-SKU flag.
**SkuClass zmeny:** Delisting po redistribúcii → dopad na oversell/sell-through. Delisted = bezpečné.

### FÁZE 9: Klasifikácia a párová analýza

**Source:** Velocity Segment × StoreStrength → oversell + reorder + SoldAfter%
**Target:** SalesBucket × StoreStrength × BrandFit → sell-through + nothing-sold + all-sold

**Párová analýza source↔target:**
- Win-Win (no oversell + good ST), Win-Lose, Lose-Win, Lose-Lose
- Identifikácia kde sú growth pockets a kde reduction pockets

### FÁZE 10: Decision tree

Rozhodovací strom s 4 smermi: source up/down, target up/down.

#### Source lookup: Velocity Segment × StoreStrength → ML 0-4
Vstupné signály: Velocity segment (po kalendárnej korekcii), StoreStrength, SoldAfter%.
CONSTRAINT: Orderable → min ML=1.

#### Source modifikátory (potvrdené)
| Modifikátor | Podmínka | Úprava |
|---|---|---|
| LastSaleGap krátky | ≤90 dní | +1 |
| BrandFit source | TrueDead/SlowFull/SlowPartial + BrandStrong | +1 |
| BrandFit source | ActiveSeller | ignorovať (sold after >92%) |
| Delisting | SkuClass → D/L | ML=0 (override) |

#### Target lookup: SalesBucket × StoreStrength → ML 0-4
Vstupné signály: predaje 12M pred, StoreStrength, BrandFit.
CONSTRAINT: Orderable → min ML=1.

#### Target modifikátory (potvrdené)
| Modifikátor | Podmínka | Úprava |
|---|---|---|
| AllSold / ST1 high | AllSold4M=1 OR ST1_4M ≥85% | +1 |
| Growth pocket | Strong, Sales 3-10, ST≥45% | +1 |
| Nothing-sold / low ST | NothingSold4M=1 OR ST4M <20% | -1 |
| **BrandFit (0-2 sales)** | BrandWeak | -1 |
| **BrandFit (0-2 sales)** | BrandStrong | +1 |
| **BrandFit (3-5 sales)** | BrandWeak | -1 |
| BrandFit (6+ sales) | — | ignorovať (predaje dominujú) |
| Delisting | SkuClass → D/L | ML=0 (override) |

#### Nepotvrdené modifikátory (analyzovať, ale neočakávať signifikantnosť)
- PhantomStock — typicky <10 SKU so správnym oversell vzorcom
- ProductConcentration <10% — žiadny gradient v oversell/reorder
- Redistribučná slučka 4+ — typicky <10 SKU
- Xmas seasonal flag per SKU — nahradené CalendarWeight

#### Clamp pravidlá
```
Final_ML = CLAMP(Base_ML + SUM(modifiers), 0, 4)
Ak IsOrderable: Final_ML = MAX(Final_ML, 1)
Ak IsDelisted: Final_ML = 0
```

### FÁZE 11: Backtest
- Aplikácia navrhovaných pravidiel na aktuálne dáta
- **Objemový dopad:** koľko ks viac/menej redistribuovaných (celkovo + per segment)
- **Trade-off:** ušetrený oversell/reorder vs stratené úspešné redistribúcie
- **Target:** bidirectionálny — growth pockets (kam posílať viac) + reduction pockets (kam posílať menej). Cieľ je lepší mix, nie len nižší objem.
- **Sensitivity:** ±1 ML level → dopad na objem a metriky

---

## ĎALŠIE NÁPADY
- Warehouse clustering (RegionId) — regionálne rozdiely
- Doba na poličke (days since last inbound) ako prediktor pre target
- Multi-product bundling — interakcia medzi produktmi na redistribúciu z jedného source
- BrandFit ako tretia dimenzia target lookup tabuľky (SalesBucket × Store × BrandFit = 45 buniek) namiesto modifieru
