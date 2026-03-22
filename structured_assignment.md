# Strukturované zadání: Analytika SalesBased MinLayers pro CalculationId=233

**Git repo:** git@github.com:ydistrilukasestvanc/sales-based-min-layer.git

## Základní kontext

| Parametr | Hodnota |
|---|---|
| Server | DEV |
| Databáze | ydistri-sql-db-dev-tenant-douglasde |
| Kalkulace | CalculationId = 233 |
| Datum kalkulace (ApplicationDate) | 2025-07-13 |
| Datum odeslání (shipping) | 2025-07-14 až 2025-07-29 |
| Celkem řádků redistribuce | 42 404 |
| Unikátních Source SKU | 36 770 |
| Unikátních Target SKU | 41 631 |
| Unikátních produktů | 5 152 |
| Unikátních brandů | 168 |
| Celkový přesouvaný počet kusů | 48 754 |
| Sledované období (4M) | do 2025-11-13 |
| Sledované období (do teď) | do 2026-03-22 |
| Vánoční období | 2025-11 a 2025-12 |

---

## Klíčové tabulky a sloupce

### 1. SkuRedistributionExpanded (hlavní tabulka redistribuce)
- **CalculationId** = 233 (filtr)
- **SourceSkuId** – SKU na zdrojové prodejně (POZOR: může být vícekrát – 1 source → N targets)
- **TargetSkuId** – SKU na cílové prodejně (POZOR: může být vícekrát – 1 target → N sources)
- **ProductId** – produkt (pro cross-store analýzu)
- **BrandId**, **CategoryId**, **DepartmentId** – pro segmentaci
- **SourceWarehouseId**, **TargetWarehouseId** – identifikace prodejen
- **Quantity** – skutečně přesunuté množství
- **SourceAvailableSupply** – zásoba na source v okamžiku kalkulace
- **TargetAvailableSupply** – zásoba na target v okamžiku kalkulace
- **SourceStockPrice**, **TargetStockPrice** – nákupní cena
- **SourceMinLayerListQuantity** – minimální vrstva na SOURCE (MAX přes všechny entity listy)
- **TargetMinLayerListQuantity** – minimální vrstva na TARGET (MAX přes všechny entity listy)
- **POZOR:** Skutečné MinLayer hodnoty pro naši analýzu se berou z **SkuPotential** tabulky, sloupce **SourceMinLayerLists** / **TargetMinLayerLists** (JSON formát, např. `{"3":3,"7":2}`). Nás zajímá pouze **EntityListId = 3** (klíč "3" v JSON).
- **IsSendToStockout** – zda jde do stockoutu
- ~~**SourceForecastQuantity**, **TargetForecastQuantity**~~ – IGNOROVAT (chybný údaj)
- **Distribuce Source MinLayer (EntityList 3, redistribuované SKU):** 0 (1798), **1 (36404)**, 2 (3504), 3 (698)
- **Distribuce Target MinLayer (EntityList 3, redistribuované SKU):** **1 (4774)**, **2 (32505)**, 3 (5125)

### 2. SaleTransaction (prodeje)
- **SkuId**, **Date**, **IsPromo**, **Quantity**, **Frequency**, **SalePrice**, **IsSellout**
- Rozsah dat: 2022-02-27 až 2026-03-19
- ~107M řádků celkem (budeme filtrovat na relevantní SKU)

### 3. SkuAvailableSupply (historie zásoby)
- **SkuId**, **DateFrom**, **DateTo** (NULL = platí dodnes), **AvailableSupply**
- ~138M řádků (budeme filtrovat)
- Klíčové pro zjištění stockoutů (AvailableSupply = 0)

### 4. Inbound (příjmy = "Income" v zadání)
- **SkuId**, **Date**, **InboundTypeId**, **Quantity**
- Typy: PURCHASE (4), STORE TRANSFER (2), Y-STORE TRANSFER (6), ADJUSTMENT (1), INVENTORY CHECK (3,5)
- Pro REORDER sledujeme **všechny typy příjmů** po datu redistribuce (se statistikou per typ)

### 5. Outbound (výdaje)
- **SkuId**, **Date**, **OutboundTypeId**, **Quantity**
- Typy: Y-STORE TRANSFER (5), STORE TRANSFER (2), ADJUSTMENT (4), INVENTORY CHECK (3,7), OTHER TRANSFER (1), TRANSFER (6), DELIVERY (8)

### 6. SkuAttributeValue (historický snapshot SKU atributů)
- **SkuId**, **AttributeValueId**, **SkuClassId**, + mnoho dalších metrik
- AttributeValueId → mapuje na datum přes tabulku AttributeValue
- **SkuClassId**: 1=Active (A), 2=Competence (C), 3=De-listed Douglas (D), 4=De-listed supplier (L), 5=Cleared (R). Sledujeme změny v čase – vliv na úspěšnost redistribuce.
- **Frequency6Month**, **Frequency12Month** – frekvence prodejů (historická z DB + vlastní výpočet ze SaleTransaction)
- **SalePrice** – prodejní cena

### 7. Warehouse (prodejny)
- **WarehouseId**, **Name**, **RegionId**, **WarehouseTypeId**
- WarehouseId=300 → online/ecomm (VYLOUČIT z percentilové analýzy)

### 8. AttributeValue (mapování na datum)
- **AttributeValueId** → **ApplicationDate**

---

## Postup práce – fáze

### FÁZE 0: Příprava dat (temp tabulky)
Vytvořit a naindexovat v temp schématu:

1. **temp.SBM_RedistSkus** – všechna unikátní SourceSkuId a TargetSkuId z kalkulace 233 + jejich ProductId, BrandId, WarehouseId
2. **temp.SBM_Sales** – prodeje (SaleTransaction) pro všechna relevantní SKU (source + target + všechna SKU stejných ProductId) za období min. 12 měsíců před redistribucí a 9 měsíců po ní (2024-07-01 až 2026-03-22)
3. **temp.SBM_Supply** – zásoby (SkuAvailableSupply) pro relevantní SKU, intervaly překrývající se s naším obdobím
4. **temp.SBM_Inbound** – příjmy pro source SKU po datu redistribuce
5. **temp.SBM_Outbound** – výdaje pro source/target SKU kolem období redistribuce
6. **temp.SBM_SkuSnapshot** – SkuAttributeValue snapshot k datu kalkulace (AttributeValueId=134) + aktuální stav
7. **temp.SBM_StoreStrength** – percentilové hodnocení síly prodejen (celkově + per brand) 

### FÁZE 1: Základní metriky redistribuce
Pro každý source/target SKU spočítat:

**SOURCE metriky:**
- Prodeje 6M před redistribucí (Frequency6M_pre)
- Prodeje 4M po redistribuci (Sales_4M_post)
- Prodeje celkem po redistribuci do teď (Sales_total_post)
- Prodeje v prosinci 2025 (Sales_dec)
- REORDER: příjmy typu PURCHASE po redistribuci (capped na Quantity)
- REORDER_4M: totéž do 4 měsíců
- OVERSELL: prodeje po redistribuci převyšující zásobu (capped na Quantity)
- OVERSELL_4M: totéž do 4 měsíců

**TARGET metriky:**
- Prodeje 6M před redistribucí
- Prodeje 4M po redistribuci
- Prodeje celkem po redistribuci do teď
- Prodeje v prosinci 2025
- NOT_SOLD: zásoba (pre + přidané) - prodané po redistribuci; pokud > 0, kolik zůstalo neprodáno
- Zda zůstal alespoň 1 kus (cíl)
- Změna SkuClass po redistribuci (z A/Z na D/L/R/C)

### FÁZE 1b: Prodejní vzorce (NOVÉ – navržené na základě dat)
Na základě prvních výsledků přidávám tyto metriky, které se ukázaly jako důležité:

**Distribuce prodejů v čase (Sales Pattern):**
- **Koeficient variace (CV) prodejů** – rozptyl mezi měsíci. Sporadický prodej (CV>2) vs. pravidelný (CV<0.5)
- **Longest gap** – nejdelší mezera bez prodeje (v dnech) za posledních 12M. Indikátor sporadičnosti.
- **Poměr Sales6M_Pre vs Sales12M_Pre** – zda se prodeje zrychlují nebo zpomalují
- **Trend prodejů produktu** – srovnání sales 6M pre-redistr. vs 6M ještě před tím (2024-07 až 2025-01). Celoplošný pokles/nárůst produktu.
- **Days-to-first-sale po redistribuci** – na source: jak rychle se prodalo po odvezení? Na target: jak rychle se začalo prodávat?

**Efektivita redistribuce (Redistribution Efficiency):**
- **Source Redistribution Ratio** = Quantity / SourceAvailableSupply – kolik % zásoby jsme odvezli
- **Target Fill Ratio** = Quantity / (TargetAvailableSupply + Quantity) – kolik % finální zásoby tvoří redistribuce
- **Reorder Speed** – za kolik dní po redistribuci přišel první inbound na source
- **Time-to-stockout na target** – kolik dní po redistribuci klesla zásoba na 0

**Párová analýza Source↔Target:**
- **Decile Flow** – z jakého decilu (síla prodejny) do jakého posíláme. Matice: strong→weak, strong→strong, weak→strong
- **Brand-Store Fit Score** – percentilové pořadí prodejny v daném brandu vs. celkově. Mismatch = prodejna celkově silná, ale v tomto brandu slabá
- **Price Ratio** – SourceStockPrice vs TargetStockPrice – jsou tam velké rozdíly?

### FÁZE 2: Cross-product analýza
- Pro každý ProductId spočítat prodeje na VŠECH prodejnách (kromě ecomm)
- Detekce celoplošného poklesu/nárůstu prodejů → indikátor externích faktorů (cena, sezónnost, konkurence)
- Porovnání trendu na source vs. celý produkt
- **NOVÉ: Product Volatility Score** – jak moc kolísají prodeje produktu mezi prodejnami a měsíci. Vysoce volatilní produkty = redistribuce riskantnější.
- **NOVÉ: Product Concentration** – Gini koeficient prodejů produktu napříč prodejnami. Pokud je produkt koncentrovaný (prodává se jen na pár prodejnách), redistribuce na jiné je riskantnější.

### FÁZE 3: Analýza síly prodejen
- Percentily prodejen dle tržeb za 6M před redistribucí (bez WarehouseId=300)
- Percentily per brand
- Klasifikace decily (1-10), seskupení: SLABÁ (1-3), PRŮMĚRNÁ (4-7), SILNÁ (8-10)
- **Klíčový nález z dat:** Reorder rate roste lineárně se sílou prodejny: decil 1 → 26%, decil 10 → 44%. Silné prodejny reorderují víc! → MinLayer musí zohledňovat sílu.
- **Klíčový nález:** Target all-sold rate: decil 1 → 48%, decil 10 → 70%. Na silné prodejny posíláme víc, ale ty prodají vše → spouštějí reorder.
- Matice přetoku (odkud kam): decil source × decil target

### FÁZE 4: Stockout analýza
- Zjistit stockouty na source/target před a po redistribuci
- Korelace stockoutů s REORDER/OVERSELL
- Phantom stock indikátory: dlouhý stockout před redistribucí → náhlý prodej po redistribuci
- **NOVÉ: Stockout Days Ratio** – kolik % období po redistribuci byl source/target ve stockoutu

### FÁZE 5: Cenová analýza
- Distribuce problémů dle cenových pásem (kvartily ceny)
- Korelace ceny s úspěšností redistribuce
- **NOVÉ: Cena vs. frekvence** – drahé produkty s nízkou frekvencí = jiné chování než levné s vysokou

### FÁZE 6: Sezónní analýza (Vánoce)
- Rozdělit úspěšnost na období: pre-4M (do 2025-11-12), Xmas (2025-11 + 2025-12), post-Xmas (2026-01+)
- Kolik REORDERů/OVERSELLů padlo do vánočního období
- **NOVÉ: Xmas Lift** – poměr měsíčních prodejů v 11-12/2025 vs. průměr ostatních měsíců. Produkty s vysokým Xmas liftem = sezónní

### FÁZE 6b: SkuClass změny (NOVÉ)
- SkuClass hodnoty: 9=A-O(Active Orderable), 11=Z-O(Z Orderable), 8=Z, 1=A, 3=D(Delisted Douglas), 4=L(Delisted supplier)
- **Zjištění:** 7,448 source SKU a 8,236 target SKU změnilo SkuClass od redistribuce
- Hlavní přesuny: A-O(9)→L(4) [2408 src, 2803 tgt], A-O(9)→D(3) [1362 src, 1607 tgt]
- Analýza: jaký vliv má delisting na úspěšnost? Pokud bylo SKU delistováno po redistribuci, je reorder/not-sold "omluvitelný"?

### FÁZE 7: Klasifikace problémových skupin

Každý redistribuční řádek klasifikovat do skupin:

**SOURCE problémy (REORDER/OVERSELL):**
1. **Sporadický prodejce** – Sales6M_pre = 0, ale prodal se po redistribuci → statistická náhoda
2. **Sezónní efekt** – prodej celoplošně vzrostl (cross-product analýza potvrzuje)
3. **Phantom stock** – dlouhý stockout před redistribucí, pak náhlý prodej
4. **Cenový efekt** – korelace s cenou produktu
5. **Slabá prodejna** – source je slabá prodejna, náhodný prodej ji ovlivní víc
6. **Silná prodejna oslabená** – source silná, ale MinLayer příliš nízký
7. **NOVÉ: Delisted po redistribuci** – SKU změnilo class na D/L → reorder je logický (prodejna si objedná náhradu)
8. **NOVÉ: Vysoká volatilita produktu** – produkt má velké výkyvy, redistribuce je riskantnější

**TARGET problémy (NOT SOLD):**
1. **Slabá prodejna** – nízké tržby, produkt se tam přirozeně neprodává
2. **SkuClass změna** – produkt delisted po redistribuci → neprodá se
3. **Přesycení** – příliš mnoho dovezeno, víc než prodejna uměla prodat
4. **Sezónní výkyv** – cíl měl dobré prodeje jen v sezóně, pak pokles
5. **Brand-store mismatch** – prodejna není silná v daném brandu
6. **NOVÉ: Vysoko-obrátkový target** – prodejně se prodalo VŠE a objednala znovu → redistribuce selhala v cíli "udržet zásobu 1ks"
7. **NOVÉ: Koncentrovaný produkt** – produkt se přirozeně prodává jen na pár prodejnách

### FÁZE 8: Souhrnný report
Pro každou skupinu:
- Počet SKU / řádků redistribuce / celková hodnota (Quantity × StockPrice)
- Úspěšnost SOURCE (% bez reorderu / oversell) – za 4M a celkově
- Úspěšnost TARGET (% kde se prodalo / zůstal 1 ks) – za 4M a celkově
- Podíl vánočního období na výsledcích
- **NOVÉ: Průměrný MinLayer3 v každé skupině** – aby bylo jasné, zda vyšší/nižší vrstva koreluje s problémem
- **NOVÉ: Doporučený MinLayer rozsah** – na základě analýzy, jaký MinLayer by zabránil problému
- Doporučení pro úpravu MinLayer pravidel

### FÁZE 9: Prediktivní model pravidel (NOVÉ)
- Na základě všech zjištění navrhnout **rozhodovací strom** pro MinLayer:
  - vstup: Sales6M, Sales12M, Frequency, store decile, brand-store fit, price, product volatility, Xmas lift
  - výstup: doporučený MinLayer (source i target)
- Backtest: jak by se výsledky změnily s novými pravidly?
- Kvantifikace: kolik reorderů/oversellů bychom ušetřili

---

## Očekávané výstupy
1. **structured_assignment.md** (tento soubor) – průběžně aktualizovaný o nové zjištění
2. **SQL temp tabulky** (temp.SBM_*) – mezivýsledky pro rychlé dotazy
3. **Python analytické skripty** – statistické výpočty, vizualizace
4. **Finální report** – podrobná analytika s klasifikací problémů a doporučeními

---

## Potvrzené odpovědi (zapracováno)

1. **MinLayer** – používáme EntityListId=3 z JSON v SkuPotential (SourceMinLayerLists/TargetMinLayerLists). Ověřujeme správnost pravidel.
2. **Inbound = všechny typy příjmů** (ne jen PURCHASE). Statistika per typ bude součástí.
3. **Referenční datum redistribuce** = globálně **2025-07-13**.
4. **OVERSELL** = MIN(prodeje_po_redistribuci - (zásoba_pred - quantity), quantity). Tj. kolik z redistribuce by se i tak prodalo, capped na redistribuované množství.
5. **SkuClass** – sledujeme změny z A na cokoliv jiného. Vliv na statistiku.
6. **Stockout** = AvailableSupply = 0.
7. **Percentily** – určím na základě reálných dat, průběžně upravím.
8. **Cross-product** = prodeje všech SKU daného ProductId na všech prodejnách (kromě ecomm WarehouseId=300).

## Poznámky k postupu (pro opakování na jiné kalkulace)

- Analýza bude parametrizovatelná na jiné CalculationId a jiné EntityListId
- Python analýzy na vzorku SKU, ověření v DB (výkonnější)
- Všechny slepé uličky a neočekávané zjištění logovat do "Log zjištění"
- Všechny tabulky v temp schématu mají prefix **SBM_**
- Pokud v průběhu analýz objevím statisticky významnou věc, zařadím ji do analýz, ověřím a přidám do postupu
- Všechny instrukce průběžně zapisuji do tohoto souboru
- **DŮLEŽITÉ: Reorder/Oversell vždy reportovat ve dvou dimenzích:** (1) počet SKU, (2) množství kusů. Reorder 1ks z 10 redistribuovaných NENÍ neúspěch. Klíčový je poměr ReorderQty/RedistributedQty (= "míra zbytečnosti"). Časové hledisko taktéž důležité.

---

## Vytvořené temp tabulky (FÁZE 0)

| Tabulka | Řádků | Popis | Indexy |
|---|---|---|---|
| temp.SBM_RedistSkus | 42 404 | Redistribuční páry s MinLayer3 z JSON | SourceSkuId, TargetSkuId, ProductId |
| temp.SBM_AllSkuIds | 1 148 386 | Všechna SKU pro dotčené produkty (excl ecomm) | SkuId, ProductId |
| temp.SBM_Sales | 6 325 193 | Prodeje 2024-07 až 2026-03 | SkuId+Date |
| temp.SBM_Supply | 812 650 | Historie zásoby source+target SKU | SkuId+DateFrom+DateTo |
| temp.SBM_Inbound | 27 054 | Příjmy source SKU po redistribuci | SkuId+Date |
| temp.SBM_Outbound | 67 599 | Výdaje source+target po 2025-07 | SkuId+Date |
| temp.SBM_SkuSnapshotCalc | 78 401 | Snapshot atributů k datu kalkulace (AV=134) | SkuId |
| temp.SBM_SkuSnapshotNow | 78 401 | Aktuální snapshot atributů (AV=385) | SkuId |
| temp.SBM_StoreStrength | 352 | Síla prodejen (decily dle tržeb 6M) | WarehouseId |
| temp.SBM_StoreBrandStrength | 37 858 | Síla prodejen per brand (kvintily) | WarehouseId+BrandId |
| temp.SBM_SourceMetrics | 36 770 | Agregované metriky per source SKU | SourceSkuId |
| temp.SBM_TargetMetrics | 41 631 | Agregované metriky per target SKU | TargetSkuId |
| temp.SBM_SourceProblems | 36 770 | REORDER/OVERSELL výpočty | SourceSkuId |
| temp.SBM_TargetProblems | 41 631 | NOT_SOLD/ALL_SOLD výpočty | TargetSkuId |
| temp.SBM_SourceFull | 36 770 | Kompletní source metriky + timing + ratio | SourceSkuId |
| temp.SBM_TargetFull | 41 631 | Kompletní target metriky + timing | TargetSkuId |

---

## Log zjištění (průběžně doplňovaný)

### FÁZE 0 – Příprava dat
- **MinLayer EntityList 3 vs. celkový**: SourceMinLayerAll je MAX přes listy (3,5,7...), SourceMinLayer3 je jen pro list 3. Distribuce se liší – List 3 source: 0(1798), 1(36404), 2(3504), 3(698). Celkový source: 0(1798), 1(31778), 2(7969), 3+(858) → list 7 a 5 přidávají vyšší hodnoty.
- **Income tabulka = Inbound** (v zadání "Income", v DB "Inbound")
- **DB tool** – po fixu autocommit funguje CREATE TABLE, INSERT, CREATE INDEX v temp schématu
- **Ecomm WarehouseId=300** vyloučen z cross-product analýzy i percentilů
- **Redistribuce proběhla 2025-07-14 až 2025-07-29**, referenční datum globálně 2025-07-13
- **AttributeValueId**: kalkulace=134 (2025-07-13), aktuální=385 (2026-03-20)
- **SkuClass rozšířené**: 9=A-O(Active Orderable), 11=Z-O(Z Orderable), 8=Z, 1=A → "dobré". 3=D, 4=L, 5=R → "špatné"

### FÁZE 1 – Základní metriky
- **Source reorder rate**: 37.6% SKU, 34.1% qty. MinLayer3=2 nejhorší (52.3% SKU, 43.5% qty).
- **Source reorder je bimodální**: 89% reorderů je 75-100% qty. Buď se reorderuje vše, nebo nic.
- **Target all-sold**: 59.8% SKU. MinLayer3=3 nejhorší (79.5% all-sold).
- **Hlavní inbound typ**: PURCHASE 72% (23k ks), Y-STORE TRANSFER 12.5% (4k ks), STORE TRANSFER 13% (4.2k ks).
- **Časování reorderu**: 51.6% do 4M (90.7% qty ratio), 18.5% v Xmas, 29.6% po novém roce.

### FÁZE 2-3 – Store + Brand + Trend
- **Source reorder lineárně roste se sílou prodejny**: decil 1→26%, decil 10→44%.
- **Target all-sold lineárně roste**: decil 1→48%, decil 10→70%.
- **Brand-store fit**: "Strong store + strong brand" = 45.3% reorder (40.3% qty). "Weak store + weak brand" = 29.3% (26.4% qty). Rozdíl 16pp!
- **Product trend**: Klesající produkty mají nejnižší reorder (31.3%), rostoucí nejvyšší (39.6%).

### FÁZE 4 – Stockout
- **Stockout korelace**: 0 dní stockoutu → 37.3% reorder. 91-150 dní → 53.6%. Ale jen 497 SKU (1.4%) mělo 31+ dní.

### FÁZE 5 – Cena
- **Levné (<15 EUR)**: 55.6% reorder SKU, ale malý vzorek (63 SKU). Target: 80.3% all-sold.
- **30-60 EUR**: nejnižší reorder (34.8%), nejvyšší target nothing-sold (25.1%).
- **60+ EUR**: 40.2% reorder – drahé se reorderují víc.

### Kombinovaná segmentace (klíčový nález)
- **Zero-sellers na silných prodejnách** (MinLayer3=1, Sales6M=0, Store 8-10): 41% reorder, 37.2% qty ratio → VELKÝ problém.
- **Zero-sellers na slabých prodejnách** (MinLayer3=1, Sales6M=0, Store 1-3): 30.7% reorder → STÁLE vysoké.
- **Low-sellers (1-2) na silných prodejnách** (MinLayer3=1): 53.2% reorder → KRITICKÉ.
- **Target MinLayer3=3, Med+ sales, Strong store**: 81.4% all-sold → redistribuce tu selhává v udržení zásoby.
- **Target MinLayer3=1, Zero sales, Weak store**: 43.7% nothing-sold → sem nemá smysl posílat.

### Delisting analýza
- **Source**: 6,047 SKU delistováno po redistribuci → jen 13.2% reorder (vs 42.7% u aktivních). Delisting = -29pp reorder.
- **Target**: 7,108 delistovaných. 24.5% nothing-sold (vs 20.7%), 61.8% all-sold (vs 59.3%) – delistované se vyprodávají (clearance).

### Redistribuční ratio
- **76-100% zásoby odvezeno**: jen 10.7% reorder! Tyto SKU mají velkou zásobu a nízký prodej – bezpečné.
- **51-75% odvezeno**: 42.8% reorder – nebezpečné, zbylá zásoba nestačí.
- **26-50%** (hlavní skupina 24.5k): 38.9% reorder.
