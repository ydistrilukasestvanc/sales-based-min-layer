# Strukturované zadání: Analytika SalesBased MinLayers

## GLOBÁLNE INŠTRUKCIE (platia pre všetky analýzy a kalkulácie)

### Všeobecné
- **JAZYK: Vysvetlenia a texty v reportoch VŽDY ČESKY.** Parametre, premenné, termíny (source, target, sell-through, oversell, reorder, MinLayer, SKU, ...) VŽDY anglicky. Toto je MUST.
- **Všetky zistenia z konverzácie VŽDY zapisovať do tohto zadania** (ak sú to nápady/prístupy) alebo do `reports/vX/findings.md` (ak sú to výsledky).
- **Výstupy = vždy 3 reporty:** 1) Findings (zistenia + korelácie), 2) Decision tree (pravidlá), 3) Backtest (dopad pravidiel s objemami).
- **Reporty sú VERZOVANÉ** v podadresároch `reports/v1/`, `reports/v2/` atď. Každá verzia je self-contained (skript + popis + reporty + grafy + findings.md). Staré verzie sa nemažú.
- **Toto zadanie NEOBSAHUJE výsledky.** Výsledky sú vždy v `reports/vX/findings.md`. Tu sú len: inštrukcie, nápady, prístupy, hypotézy, brainstorming.
- **Nová verzia začína s čistým štítom** – žiadne predpoklady z predchádzajúcej verzie.
- **Overview tabuľka VŽDY obsahuje celkové metriky:** oversell (SKU + qty), reorder (SKU + qty), sell-through + ST-1pc (qty) – všetko aj v quantity, nie len percentá. Vždy 4M aj total.
- **Business rule: A-O (9) a Z-O (11) minimum ML=1.** Len tieto triedy môžu byť target.

### Metriky – VŽDY uvádať OBE, NIKDY nemiešať
- **REORDER** = inbound po redistribúcii. Informačná metrika – nemusí súvisieť s redistribúciou.
- **OVERSELL** = sales-based: predalo sa viac ako zostalo po redistribúcii (capped na redistrib. qty). PRIMÁRNA metrika pre source.
- Vo VŠETKÝCH štatistikách VŽDY uvádzať OBE metriky vedľa seba. Sú to rôzne ukazovatele.
- Vždy uvádzať **4M aj total** verziu oboch metrík.

### Source pravidlá
- **Cieľ OVERSELL rate:** 4M: 5-10%, 9M: <20%. Cieľom NIE JE nulový reorder.
- **Source ML sa môže aj ZNÍŽIŤ** – ak sa dá identifikovať, že produkty sa na source nepredávajú. Analyzovať kedy je bezpečné byť agresívnejší.

### Target pravidlá – ROVNAKO DÔLEŽITÉ ako source
- **Target all-sold = ÚSPECH.** Signál na zvýšenie target ML.
- **Target nothing-sold = PROBLÉM.** Zbytočná redistribúcia.
- **SELL-THROUGH (ST)** = LEAST(Sold, Base) / Base, kde Base = TargetSupplyAtCalc + TotalQtyReceived. Cappované na 100%.
- **SELL-THROUGH-1pc (ST1):** Ak Sold >= Base: ST1 = ST. Ak Sold < Base: ST1 = LEAST(Sold, Base-1)/(Base-1). ST1 = 100% keď zostáva presne 1 ks = IDEÁLNY STAV.
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

---

## Klíčové tabulky

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

## Postup práce – fáze

### FÁZE 0: Príprava dát
Vytvoriť a naindexovať v temp schéme (prefix SBM_):
1. Redistribučné páry s MinLayer3 z JSON
2. Všetky SKU dotčených produktov (excl ecomm) – pre cross-product analýzu
3. Predaje 12M pred + 9M po redistribúcii (+ rozšírené 24M pre vzorce)
4. Zásoby (SkuAvailableSupply) pre source+target
5. Inbound/Outbound po redistribúcii
6. SkuAttributeValue snapshot k dátumu kalkulácie + aktuálny
7. Sila predajní (decily podľa tržieb 6M) + per brand (kvintily)

### FÁZE 1: Základné metriky
**Source:** predaje 6M/12M pred, 4M/total po, reorder (4M + total), oversell (4M + total)
**Target:** predaje 6M/12M pred, 4M/total po, sell-through (ST + ST-1pc, 4M + total), nothing-sold, all-sold

### FÁZE 1b: Predajné vzorce (24M história)
Klasifikácia source SKU do vzorov podľa 4 polročných periód:
- Dead / Dying / Sporadic / Consistent / Declining
- Hypotéza: vzorec predajov je silnejší prediktor ako 6M frekvencia
- Kombinovať s silou predajne (Weak/Mid/Strong)

### FÁZE 2: Cross-product analýza
- Prodeje produktu na VŠETKÝCH predajniach (okrem ecomm) – celoplošný trend
- Product Volatility Score – variabilita predajov medzi predajňami/mesiacmi
- Product Concentration – Gini koeficient, na koľkých predajniach sa produkt predáva

### FÁZE 3: Sila predajní
- Decily podľa tržieb za 6M pred redistribúciou
- Per brand (kvintily)
- Brand-store fit: celková sila vs sila v danom brande → mismatch analýza
- Matice prietoku (odkiaľ kam): decil source × decil target

### FÁZE 4: Stockout analýza
- Stockouty pred redistribúciou (indikátor phantom stocku)
- Korelácia dĺžky stockoutu s oversell/reorder

### FÁZE 5: Cenová analýza
- Cenové pásma vs oversell/sell-through
- Promo analýza: IsPromo podiel cross-store (overenie či declining vzorec je spôsobený promo)
- Cenové zmeny produktu medzi periódami

### FÁZE 6: Sezónna analýza (Vianoce)
- Xmas Lift: podiel Nov+Dec predajov z 12M
- Ak >=20% predajov v Nov+Dec → seasonal flag
- Problém: 6M okno s Vianocami nafukuje frekvenciu

### FÁZE 6b: SkuClass zmeny
- Sledovať zmeny SkuClass po redistribúcii (delisting)
- Vplyv na oversell/sell-through

### FÁZE 7: Klasifikácia skupín
**Source:** segmenty podľa Pattern × Store → reorder + oversell rate
- Identifikovať kde je bezpečné ZNÍŽIŤ ML (oversell <10%)
- Identifikovať kde TREBA ZVÝŠIŤ ML (oversell >20%)

**Target:** segmenty podľa Sales × Store → sell-through + ST-1pc rate
- Low sell-through = ML ZNÍŽIŤ
- High sell-through + all-sold = ML ZVÝŠIŤ

### FÁZE 8: Decision tree
Rozhodovací strom s 4 smermi: source up/down, target up/down
- Source: lookup Pattern × Store → ML 0-5
- Target: lookup SalesBucket × Store → ML 0-5
- Modifikátory: Xmas, brand-store fit, koncentrácia, delisting, redistrib. slučka

### FÁZE 9: Backtest
- Aplikácia navrhovaných pravidiel na aktuálne dáta
- Objemový dopad (ks viac/menej redistribuovaných)
- Trade-off: ušetrený oversell vs stratené úspešné redistribúcie
- Target: extra ks potrebné aby zostal 1 ks

---

## Ďalšie nápady na preskúmanie
- Redistribučná slučka (Y-STORE TRANSFER loop) – SKU redistribuované opakovane
- Mesačná kadencia (počet aktívnych mesiacov z 24M) ako alternatívny vstup pre ML
- Doba od posledného predaja (last sale gap) ako prediktor
- Párová analýza source↔target (combined outcome)
- Redistribučný ratio (koľko % zásoby odvezieme) vs výsledky
