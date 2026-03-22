# Strukturované zadání: Analytika SalesBased MinLayers (v4)

## GLOBÁLNE INŠTRUKCIE (platia pre všetky analýzy a kalkulácie)

### Všeobecné
- **JAZYK: Vysvetlenia a texty v reportoch VŽDY ČESKY.** Parametre, premenné, termíny (source, target, sell-through, oversell, reorder, MinLayer, SKU, ...) VŽDY anglicky. Toto je MUST.
- **Všetky zistenia z konverzácie VŽDY zapisovať do tohto zadania** (ak sú to nápady/prístupy) alebo do `reports/vX/findings.md` (ak sú to výsledky).
- **Výstupy = vždy 3 reporty:** 1) Findings (zistenia + korelácie), 2) Decision tree (pravidlá), 3) Backtest (dopad pravidiel s objemami).
- **Výstupy VŽDY aj GRAFICKY** — Python skript (`generate_consolidated_reports.py`) generuje 3 HTML reporty + PNG grafy (heatmapy, bar charty, scatter ploty, waterfall). Grafy sú POVINNÁ súčasť každej verzie. Skript používa matplotlib + seaborn, embedded dáta, a generuje self-contained HTML s CSS + navigáciou medzi reportmi.
- **Reporty sú VERZOVANÉ** v podadresároch `reports/v1/`, `reports/v2/` atď. Každá verzia je self-contained (skript + popis + reporty + grafy + findings.md). Staré verzie sa nemažú.
- **Toto zadanie NEOBSAHUJE výsledky.** Výsledky sú vždy v `reports/vX/findings.md`. Tu sú len: inštrukcie, nápady, prístupy, hypotézy, brainstorming.
- **Nová verzia začína s čistým štítom** – žiadne predpoklady z predchádzajúcej verzie.
- **Overview tabuľka VŽDY obsahuje celkové metriky:** overprosim  (SKU + qty), reorder (SKU + qty), sell-through + ST-1pc (qty) – všetko aj v quantity, nie len percentá. Vždy 4M aj total.
- **MinLayer rozsah: 0-4.** Hodnota 0 = odvézt/neposlať nič (resp. všetko). Hodnota 4 = maximálna ochrana.
- **Business rule: A-O (9) a Z-O (11) = ORDERABLE → NIKDY ML=0.** Minimum ML=1 pre orderable SKU. ML=0 len pre delisted (D/L) alebo non-orderable triedy. Toto je HARD CONSTRAINT, nie odporúčanie.

### Metriky – VŽDY uvádať OBE, NIKDY nemiešať
- Vo VŠETKÝCH štatistikách VŽDY uvádzať OBE metriky vedľa seba. Sú to rôzne ukazovatele.
- Vždy uvádzať **4M aj total** verziu oboch metrík.

#### REORDER (metrika, source)
Inbound po redistribúcii — cappované na redistrib. qty (rovnaký princíp ako oversell).
Bežné doobjednávky prekračujúce redistribuované množstvo sa nepočítajú — tie by sa objednali aj bez redistribúcie.
```
Reorder_SKU  = 1 ak SkuId má aspoň 1 záznam v Inbound po ApplicationDate
Raw_Inbound  = SUM(Inbound.Quantity) pre dané obdobie (4M / total)
Reorder_Qty  = LEAST(Raw_Inbound, TotalQtyRedistributed)
Reorder_Rate = Reorder_SKU_count / Total_Source_SKU × 100
```
- Cap na `TotalQtyRedistributed` = nemôže byť reorder viac ks, než sme odviezli.
- Ak source dostal 5 ks inboundu, ale redistribuoval sa len 1 ks → reorder = 1 (nie 5).

#### OVERSELL (PRIMÁRNA metrika, source)
Predalo sa viac, než čo na source **zostalo** po redistribúcii. Cappované na redistrib. qty.
```
RemainingAfterRedist = SourceAvailableSupply - TotalQtyRedistributed
Oversell_Qty = LEAST(
    GREATEST(Sales_Post - RemainingAfterRedist, 0),
    TotalQtyRedistributed
)
```
- `SourceAvailableSupply` = zásoba na source v momente kalkulácie
- `TotalQtyRedistributed` = SUM(Quantity) zo všetkých párov pre daný SourceSkuId
- `Sales_Post` = SUM(SaleTransaction.Quantity) za obdobie po ApplicationDate (4M / total)
- `RemainingAfterRedist` = koľko ks zostane na source po odvezení
- Oversell nastáva IBA ak predaj prekročí zostatok. Ak source predá menej než zostalo → oversell = 0.
- Cap na `TotalQtyRedistributed` = nemôže byť oversell viac ks než sme odviezli.

**Príklad:**
| Supply | Redist | Remaining | Sales Post | Oversell |
|---|---|---|---|---|
| 5 | 1 | 4 | 3 | MAX(3-4,0) = **0** (zásoba stačila) |
| 2 | 1 | 1 | 2 | MIN(MAX(2-1,0), 1) = **1** |
| 3 | 2 | 1 | 5 | MIN(MAX(5-1,0), 2) = **2** (cap na redistrib qty) |
| 3 | 1 | 2 | 0 | MAX(0-2,0) = **0** (nič sa nepredalo) |

#### SELL-THROUGH (ST) (PRIMÁRNA metrika, target)
Koľko z prijatého + existujúceho sa predalo. Cappované na 100%.
```
Base = TargetAvailableSupply + TotalQtyReceived
Sold = SUM(SaleTransaction.Quantity) za obdobie po ApplicationDate (4M / total)
ST = LEAST(Sold, Base) / Base × 100
```
- `TargetAvailableSupply` = zásoba na target v momente kalkulácie
- `TotalQtyReceived` = SUM(Quantity) zo všetkých párov pre daný TargetSkuId
- ST = 100% keď sa predalo všetko alebo viac

#### SELL-THROUGH-1pc (ST1) (doplnková metrika, target)
Ideálny stav = zostáva presne 1 ks (nie stockout, ale minimum). ST1 = 100% pri 1 ks zvyšku.
```
Ak Sold >= Base:
    ST1 = ST (= 100%)
Ak Sold < Base AND Base > 1:
    ST1 = LEAST(Sold, Base - 1) / (Base - 1) × 100
Ak Base <= 1:
    ST1 = NULL (nemá zmysel)
```

#### NOTHING-SOLD (flag, target)
```
NothingSold = 1 ak SUM(Sales_Post) = 0 za dané obdobie
```

#### ALL-SOLD (flag, target)
```
AllSold = 1 ak SUM(Sales_Post) >= Base (predalo sa všetko)
```

### Source pravidlá
- **Cieľ OVERSELL rate:** 4M: 5-10%, 9M: <20%.
- **Cieľ REORDER rate:** znížiť o 10-15% oproti aktuálnemu stavu na total období. Reorder je tiež dôležitá metrika — indikuje, že source bol príliš agresívne vyčerpaný a musel sa znova doplniť.
- **Source ML sa môže aj ZNÍŽIŤ** – ak sa dá identifikovať, že produkty sa na source nepredávajú. Analyzovať kedy je bezpečné byť agresívnejší.

### Target pravidlá – ROVNAKO DÔLEŽITÉ ako source
- **Target all-sold = ÚSPECH.** Signál na zvýšenie target ML.
- **Target nothing-sold = PROBLÉM.** Zbytočná redistribúcia.
- **Low sell-through (<30% po 4M) = PROBLÉM:** predáva sa pomaly → ML ZNÍŽIŤ.
- **Target ML sa môže aj ZNÍŽIŤ** – ak sell-through je nízky.
- **Target ML sa ZVÝŠI** – ak silné predajne predajú všetko.
- **Target analytika musí byť ROVNAKO podrobná ako source.**

### Backtest
- **Backtest vždy na SALES (oversell)**, nie na inbound.
- **Backtest musí ukazovať zmenu OBJEMU** redistribúcie (koľko ks viac/menej).
- **Decision tree: 4 smery:** source up, source down, target up, target down.

---

## Parametre analýzy (zmeniť pre inú kalkuláciu)

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
| Git repo | git@github.com:ydistrilukasestvanc/sales-based-min-layer.git |
| Temp schéma prefix | SBM_[version]_ (napr. SBM_v4_ pre verziu 4) |
| DB pripojenie | MCP server `ydistri-kb` → tool `mcp__ydistri-kb__query_database` |

---

## Klíčové tabulky

| Tabulka | Účel | Kľúčové stĺpce |
|---|---|---|
| SkuRedistributionExpanded | Redistribučné páry | SourceSkuId, TargetSkuId, Quantity, *MinLayerListQuantity |
| SkuPotential | MinLayer JSON detaily | SourceMinLayerLists, TargetMinLayerLists (JSON) |
| SaleTransaction | Predaje | SkuId, Date, IsPromo, Quantity, SalePrice |
| SkuAvailableSupply | História zásoby | SkuId, DateFrom, DateTo, AvailableSupply. DateFrom = NULL → platí do dnes. DateFrom prvý záznam = začiatok histórie SKU |
| Inbound | Príjmy (reorder) | SkuId, Date, InboundTypeId, Quantity |
| Outbound | Výdaje | SkuId, Date, OutboundTypeId, Quantity |
| SkuAttributeValue | Historický snapshot | SkuId, AttributeValueId, SkuClassId, Frequency*, SalePrice |
| AttributeValue | Mapovanie na dátum | AttributeValueId → ApplicationDate |
| Warehouse | Predajne | WarehouseId, RegionId, WarehouseTypeId |
| SkuClass | Triedy SKU | 9=A-O, 11=Z-O (orderable), 3=D, 4=L (delisted) |

---

## Postup práce – fáze

### FÁZE 0: Príprava dát
Vytvoriť a naindexovať v temp schéme (prefix SBM_[version]_):
1. Redistribučné páry s MinLayer3 z JSON
2. Všetky SKU dotčených produktov (excl ecomm) – pre cross-product analýzu
3. Predaje 12M pred + 9M po redistribúcii (+ rozšírené 24M pre vzorce)
4. Zásoby (SkuAvailableSupply) pre source+target
5. Inbound/Outbound po redistribúcii
6. SkuAttributeValue snapshot k dátumu kalkulácie + aktuálny
7. Sila predajní (decily podľa tržieb 6M) + per brand (kvintily)

### FÁZE 1: Validácia dát
Pred analýzou overiť kvalitu vstupov:
- Počet redistribučných párov, distribúcia Quantity (min/max/median/percentily)
- Pokrytie predajov: koľko source/target SKU má aspoň 1 predaj za 12M pred
- Zásoby: koľko SKU má AvailableSupply záznam, koľko má medzery
- Sanity checks: negatívne quantity, duplicitné páry, source=target
- Výstup: krátky report s flagmi ak niečo nesedí, PREDTÝM než sa pokračuje ďalej

### FÁZE 2: Základné metriky
**Source:** predaje 6M/12M pred, 4M/total po, reorder (4M + total), oversell (4M + total)
**Target:** predaje 6M/12M pred, 4M/total po, sell-through (ST + ST-1pc, 4M + total), nothing-sold, all-sold

Výstup: overview tabuľka podľa globálnych inštrukcií (SKU count + qty pre každú metriku, 4M + total).

### FÁZE 3: Predajné vzorce (24M história)
Klasifikácia source SKU do vzorov podľa 4 polročných periód:
- Dead / Dying / Sporadic / Consistent / Declining
- Hypotéza: vzorec predajov je silnejší prediktor ako 6M frekvencia
- Kombinovať s silou predajne (Weak/Mid/Strong)

**Doplnkové signály:**
- **Mesačná kadencia** = počet aktívnych mesiacov z 24M (alternatívny vstup pre ML)
- **Last sale gap** = doba od posledného predaja k dátumu kalkulácie (prediktor: čím dlhšie, tým menej rizikový odvoz)

### FÁZE 4: Cross-product analýza
- Predaje produktu na VŠETKÝCH predajniach (okrem ecomm) – celoplošný trend
- Product Volatility Score – variabilita predajov medzi predajňami/mesiacmi
- Product Concentration – Gini koeficient, na koľkých predajniach sa produkt predáva
- **Redistribučný ratio** = Quantity / AvailableSupply na source → aký % zásoby odvážame. Korelácia s oversell.

### FÁZE 5: Sila predajní
- Decily podľa tržieb za 6M pred redistribúciou
- Per brand (kvintily)
- Brand-store fit: celková sila vs sila v danom brande → mismatch analýza
- Matice prietoku (odkiaľ kam): decil source × decil target

### FÁZE 6: Phantom Stock analýza (LEN SOURCE)
**Phantom stock** = source SKU kde:
1. Zásoby existovali dlhodobo (mesiace bez stockoutu = AvailableSupply > 0 kontinuálne)
2. Žiadne alebo minimálne predaje počas tejto doby
3. Po navrhnutí redistribúcie sa predaje VRÁTILI (oversell)

Vysvetlenie: produkt fyzicky nebol v regáli (backstore, krádež), systém videl zásobu, ale zákazník produkt nemohol kúpiť. Keď sme navrhli odvoz, produkt sa vrátil do regálu a začal sa predávať.

**DÔLEŽITÉ: Očistenie od šumu (false positives):**
- Ak sa produkt nepredával predtým, štatisticky je logické, že potom bude predaj vyšší → to samo o sebe NIE JE phantom stock
- **Cross-store filter:** Phantom stock vzorec musí byť prítomný LEN na tomto konkrétnom SKU (store), NIE naprieč všetkými predajňami rovnakého product_id. Ak rovnaký product_id nepredáva na VŠETKÝCH predajniach → nie je to phantom stock, ale product-level trend (zomierajúci produkt)
- Teda: porovnať predaje pred redistribúciou na TOMTO SKU vs ostatné SKU rovnakého product_id. Ak ostatné predajne predávajú normálne a len TOTO SKU nie → phantom stock kandidát

**Phantom stock sa NETÝKA target strany** – na target nemá zmysel (target dostáva nový tovar).

### FÁZE 7: Redistribučná slučka (Y-STORE TRANSFER loop)
Detekcia SKU ktoré boli redistribuované opakovane:
- Identifikácia cez Inbound/Outbound s OutboundTypeId / InboundTypeId pre Y-STORE TRANSFER
- Koľko krát bolo SKU redistribuované v posledných 12M/24M
- Korelácia: opakovaná redistribúcia × oversell rate / sell-through
- Hypotéza: SKU v slučke sú špatní kandidáti (nestabilná situácia)

### FÁZE 8: Cenová a sezónna analýza
**Cenová:**
- Cenové pásma vs oversell/sell-through
- Promo analýza: IsPromo podiel cross-store (overenie či declining vzorec je spôsobený promo)
- Cenové zmeny produktu medzi periódami

**Sezónna (Vianoce):**
- Xmas Lift: podiel Nov+Dec predajov z 12M
- Ak >=20% predajov v Nov+Dec → seasonal flag
- Problém: 6M okno s Vianocami nafukuje frekvenciu

**SkuClass zmeny:**
- Sledovať zmeny SkuClass po redistribúcii (delisting)
- Vplyv na oversell/sell-through

### FÁZE 9: Klasifikácia skupín
**Source:** segmenty podľa Pattern × Store → reorder + oversell rate
- Identifikovať kde je bezpečné ZNÍŽIŤ ML (oversell <10%)
- Identifikovať kde TREBA ZVÝŠIŤ ML (oversell >20%)

**Target:** segmenty podľa Sales × Store → sell-through + ST-1pc rate
- Low sell-through = ML ZNÍŽIŤ
- High sell-through + all-sold = ML ZVÝŠIŤ

**Párová analýza source↔target:**
- Combined outcome: source oversell × target sell-through matice
- Identifikácia "win-win" (low oversell + high ST) a "lose-lose" (high oversell + low ST) segmentov
- Čo majú spoločné win-win páry? (sila predajní, product type, cena, ...)

### FÁZE 10: Decision tree
Rozhodovací strom s 4 smermi: source up/down, target up/down

**Source lookup:** Pattern × Store Strength → ML 0-4
- Vstupné signály: predajný vzorec, mesačná kadencia, last sale gap, phantom stock flag, redistribučný ratio
- Výstup: navrhovaná source ML pre každý segment
- **CONSTRAINT: A-O / Z-O (orderable) → MIN ML=1, NIKDY 0**

**Target lookup:** SalesBucket × Store Strength → ML 0-4
- Vstupné signály: sell-through, ST-1pc, nothing-sold flag, brand-store fit
- Výstup: navrhovaná target ML pre každý segment
- **CONSTRAINT: A-O / Z-O (orderable) → MIN ML=1, NIKDY 0**

**Modifikátory (úprava base ML, výsledok cappovaný na 0-4):**
- Xmas seasonal flag → +1 / -1 podľa smeru
- Brand-store mismatch → -1 na target
- Vysoká product concentration (Gini) → opatrnosť na source
- Delisting (SkuClass zmena) → ML=0 (jediný prípad keď orderable môže ísť na 0)
- Redistribučná slučka → penalizácia

### FÁZE 11: Backtest
- Aplikácia navrhovaných pravidiel na aktuálne dáta
- **Objemový dopad:** koľko ks viac/menej redistribuovaných (celkovo + per segment)
- **Trade-off analýza:** ušetrený oversell (qty) vs stratené úspešné redistribúcie (qty)
- **Target dopad:** extra ks potrebné aby zostal 1 ks (ST-1pc optimalizácia)
- **Sensitivity:** čo ak posunieme thresholdy o ±1 ML level → ako sa zmení objem a oversell

---

## Ďalšie nápady na preskúmanie
- Warehouse clustering (RegionId vzorce) – regionálne rozdiely v úspešnosti
- Doba na poličke (days since last inbound) ako prediktor pre target
- Multi-product bundling – ak source má viacero produktov na redistribúciu, interakcia medzi nimi
