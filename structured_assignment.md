# Strukturované zadání: Analytika SalesBased MinLayers pro CalculationId=233

## GLOBÁLNE INŠTRUKCIE (platia pre všetky analýzy, nie len toto zadanie)

### Všeobecné
- **Všetky zistenia z konverzácie VŽDY zapisovať do tohto zadania.** Ak niečo zistím, okamžite to zapíšem sem – log musí byť kompletný pre rekonštrukciu.
- **Výstupy = vždy 3 reporty:** 1) Findings (zistenia + korelácie), 2) Decision tree (pravidlá), 3) Backtest (dopad pravidiel s objemami, nie len SKU count).
- **Reporty sú VERZOVANÉ** v podadresároch `reports/v1/`, `reports/v2/` atď. Každá iterácia generuje novú verziu. Staré verzie sa nemažú – slúžia na porovnanie.
- **Overview tabuľka VŽDY obsahuje celkové metriky:** oversell (SKU + qty), reorder (SKU + qty), sell-through (qty) – všetko aj v quantity, nie len percentá.
- **Business rule: A-O (9) a Z-O (11) minimum ML=1.** Len tieto triedy môžu byť target.

### Metriky – VŽDY uvádať OBE, NIKDY nemiešať
- **REORDER** = inbound po redistribúcii (objednalo sa nové zboží). Informačná metrika – ukazuje, že prodejna niečo objednala, ale nemusí to súvisieť s redistribúciou.
- **OVERSELL** = sales-based: predalo sa viac ako zostalo po redistribúcii (capped na redistrib. qty). Toto je PRIMÁRNA metrika pre vyhodnotenie source.
- Vo VŠETKÝCH štatistikách VŽDY uvádzať OBE metriky vedľa seba (reorder % + oversell %). Sú to rôzne ukazovatele a nesmú sa miešať.

### Source pravidlá
- **Cieľ OVERSELL rate:** 4M: 5-10%, 9M: <20%. Cieľom NIE JE nulový reorder – to by bolo príliš defenzívne.
- **Source ML sa môže aj ZNÍŽIŤ** (byť agresívnejší) – ak sa dá identifikovať, že produkty sa na source nepredávajú (Dead vzorec, slabá prodejna, delistované). Treba analyzovať kedy je bezpečné znížiť ML.

### Target pravidlá – ROVNAKO DÔLEŽITÉ ako source
- **Target all-sold = ÚSPECH.** Nikdy to neoznačovať ako problém. Signál na zvýšenie target ML (poslať viac).
- **Target nothing-sold = PROBLÉM.** Zbytočná redistribúcia.
- **Target SELL-THROUGH rate** = koľko z poslaného sa predalo. Ideál: predať všetko do 1 ks. Problém je aj keď sa predá MÁLO (nie nič, ale málo) a po 4M zostane príliš veľa = low sell-through. V takom prípade treba target ML ZNÍŽIŤ.
- **Target ML sa môže aj ZNÍŽIŤ** – ak sa na danej predajni/brandu/produkte predáva málo. Sem nemá zmysel posielať veľa.
- **Target ML sa ZVÝŠI** – ak sa na silných predajniach predá všetko → treba poslať viac, aby zostal 1 ks.
- **Target analytika musí byť ROVNAKO podrobná ako source:** analýza cez predaje, silu predajne, brand-store fit, cenu, sezónnosť, koncentráciu produktu. Nie len "nothing sold / all sold".

### Backtest
- **Backtest vždy na SALES (oversell)**, nie na inbound.
- **Backtest musí ukazovať zmenu OBJEMU** redistribúcie (koľko ks viac/menej), nie len počet SKU.
- **Decision tree musí obsahovať pravidlá pre ZVÝŠENIE aj ZNÍŽENIE** source ML aj target ML. 4 smery: source up, source down, target up, target down.

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
- ALL_SOLD: vše prodáno = **ÚSPĚCH** (redistribuce splnila účel, produkt se prodal). Pokud nic nezůstalo → příležitost poslat příště víc.
- NOTHING_SOLD: nic neprodáno = **JEDINÝ SKUTEČNÝ PROBLÉM** na targetu (zbytečný přesun)
- PARTIAL_SOLD + 1ks zbývá: **IDEÁLNÍ STAV** (prodalo se, 1 ks zůstal dle business rule A-O/Z-O)
- Změna SkuClass po redistribuci (z A/Z na D/L/R/C)
- **SELL-THROUGH RATE** = SalesTotal_Post / (TargetSupplyAtCalc + TotalQtyReceived). Koľko % z celkovej zásoby sa predalo.
  - Ideál: sell-through ~100% a zostane 1 ks (all sold alebo near-all sold)
  - Problém A: sell-through = 0% → nothing sold → ML ZNÍŽIŤ (nepredáva sa tu)
  - Problém B: sell-through < 30% po 4M → low sell-through → ML ZNÍŽIŤ (predáva sa pomaly)
  - Úspech: sell-through > 80% → ML OK alebo ZVÝŠIŤ (predáva sa dobre, poslať viac)
- **POZOR: "all sold" NENÍ problém! Je to signál, že MinLayer na target by mohol být i vyšší (poslat víc kusů, aby 1 zůstal).**

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

**TARGET výsledky (4 kategorie podľa sell-through):**
- **ALL SOLD (sell-through ~100%) = ÚSPECH:** Redistribúcia splnila účel. ML ZVÝŠIŤ (poslať viac, aby zostal 1 ks).
- **HIGH SELL-THROUGH (>80%) + zostáva 1+ ks = IDEÁLNY STAV.** ML ponechať.
- **LOW SELL-THROUGH (<30% po 4M) = PROBLÉM:** Predáva sa pomaly, príliš veľa zostáva. ML ZNÍŽIŤ. Príčiny:
  1. **Slabá prodejna** – nízke tržby, produkt sa tam prirodzene nepredáva
  2. **Brand-store mismatch** – predajňa nie je silná v danom brande
  3. **Koncentrovaný produkt** – predáva sa len na pár predajniach
  4. **Sezónny produkt** – predával sa v sezóne, teraz nie
- **NOTHING SOLD (sell-through = 0%) = NAJVÄČŠÍ PROBLÉM:** Zbytočná redistribúcia. ML výrazne ZNÍŽIŤ alebo neposielať.
  1. **SkuClass zmena** – produkt delistovaný po redistribúcii
  2. **Slabá prodejna + slabý brand** – kombinácia

**Analýza target musí byť ROVNAKO podrobná ako source:** rovnaké dimenzie (sila predajne, brand-store fit, cena, predajný vzorec, sezónnosť, koncentrácia).

### FÁZE 8: Souhrnný report
Pro každou skupinu:
- Počet SKU / řádků redistribuce / celková hodnota (Quantity × StockPrice)
- Úspěšnost SOURCE (% bez oversell) – za 4M a celkově
- Úspěšnost TARGET: % all-sold (ÚSPĚCH), % partial+1ks (IDEÁLNÍ), % nothing-sold (PROBLÉM)
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
- **BUSINESS RULE: SkuClass A-O (9) a Z-O (11) MUSÍ mít na skladě minimálně 1 ks.** Jen tyto třídy mohou být Target. Navrhovaný MinLayer nesmí být 0 pro tyto třídy – minimum je vždy 1.
- **BACKTEST KOREKCE: Vyhodnocovat úspěšnost redistribuce podľa realizovaných SALES (SaleTransaction), NIE podľa Inbound.** Inbound mohol a nemusel prebehnúť nezávisle na redistribúcii. Oversell (predaje > zostávajúca zásoba) je správna metrika.
- **CIEĽOVÉ OVERSELL RATE:** 4M po redistribúcii: 5-10%. 9M (~teraz): <20%. Cieľom NIE JE nulový reorder – to by vyžadovalo extrémnu defenzívu. Cieľom je rozumné zníženie.
- **DÔLEŽITÉ:** Aktuálny oversell (4M) pre ML0=1.1%, ML1=3.6% sú UŽ TERAZ v cieli! Problém je len ML2 (22.2% total) a špecifické segmenty (Declining+Strong: 35.4%).
- **VIANOČNÉ PREDAJE:** Treba overiť, či sú štatisticky relevantné pre decision tree. Ak kalkulácia prebieha v júli, posledných 6M (jan-júl) neobsahuje Vianoce. Ale 6M pred tým (júl-jan) ÁNO obsahuje november+december. Otázka: mal by mať 6M perióda s Vianocami inú váhu? Predaje v Nov+Dec môžu byť nafúknuté sezónnosťou.
- **6M vs 24M:** 6-mesačná analýza NIE JE irelevantná – je dôležitá pre aktuálnu frekvenciu. Ale 24M analýza (vzorec) zachytáva dlhodobé správanie. Obe majú rôznu váhu: 6M = aktuálny stav, 24M = historický vzorec. Pre decision tree sú komplementárne.
- **VÁHA VIANOČNÝCH MESIACOV:** Ak je v 6M okne Nov+Dec, predaje sú pravdepodobne vyššie (sezónnosť). Toto treba zohľadniť – buď váhou alebo separate Xmas flagom.
- **Target all-sold = ÚSPECH.** Nie je to problém. Ak sa predá všetko → príležitosť poslať viac. Jediný target problém = nothing-sold.
- **Cieľom NIE JE nulový reorder** – to by bolo príliš defenzívne. Cieľ: 4M oversell 5-10%, 9M oversell <20%.

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
- **Target MinLayer3=3, Med+ sales, Strong store**: 81.4% all-sold → SKVĚLÝ výsledek! Příležitost poslat i víc kusů, aby 1 zůstal.
- **Target MinLayer3=1, Zero sales, Weak store**: 43.7% nothing-sold → PROBLÉM, sem nemá smysl posílat.

### Delisting analýza
- **Source**: 6,047 SKU delistováno po redistribuci → jen 13.2% reorder (vs 42.7% u aktivních). Delisting = -29pp reorder.
- **Target**: 7,108 delistovaných. 24.5% nothing-sold (vs 20.7%), 61.8% all-sold (vs 59.3%) – delistované se vyprodávají (clearance).

### Redistribuční ratio
- **76-100% zásoby odvezeno**: jen 10.7% reorder! Tyto SKU mají velkou zásobu a nízký prodej – bezpečné.
- **51-75% odvezeno**: 42.8% reorder – nebezpečné, zbylá zásoba nestačí.
- **26-50%** (hlavní skupina 24.5k): 38.9% reorder.

### FÁZE 1b – Prodejní vzorce (24M historie) – KLÍČOVÝ NÁLEZ
Klasifikace 36,770 source SKU do 5 vzorců (4 půlroční periody):
- **Dead (0 prodejů 24M)**: 15,625 SKU (43%), 28.5% reorder, 26.1% qty – nejbezpečnější
- **Dying (prodeje jen staré)**: 6,427 SKU, 34.5% reorder – umírající ale 1/3 se vrací
- **Sporadic (nepravidelné)**: ~9,900 SKU, 45.4% reorder – vysoké riziko
- **Consistent (3-4 periody)**: 3,288 SKU, 55.5% reorder – nesmí se odvézt moc
- **Declining (B>C>D)**: 1,539 SKU, **65.0% reorder, 56.8% qty** – NEJHORŠÍ! Aktuální ML=1.1 je drasticky nedostatečný

### Doba od posledního prodeje – paradox
- **91-180 dní**: NEJVYŠŠÍ reorder (51.1%) – "spící" produkty
- **Nikdy neprodané**: 31.9% – nejnižší ale stále třetina

### Dead SKU + Stockout analýza
- Dead bez stockoutu: 28.0% reorder (12,304 SKU)
- Dead + stockout >90d v D periodě: **52.1% reorder** (48 SKU) – phantom stock indikátor

### Decision Tree – navrženo
- **Source MinLayer** závisí primárně na prodejním vzorci (24M) + síla prodejny. Rozsah 0-5.
- **Target MinLayer** závisí primárně na frekvenci prodejů (6M) + síla prodejny. Rozsah 0-5.
- Source a Target pravidla jsou ODLIŠNÁ.
- **Business rule:** A-O (SkuClassId=9) a Z-O (SkuClassId=11) MUSÍ mít ML minimálně 1. Jen tyto mohou být target.
- Backtest verze V2 korigován na SALES-based metriku (oversell), ne inbound.

### Rozšířené analýzy (nové)

#### 1. Redistribuční smyčka (Y-STORE TRANSFER loop)
- **3,117 SKU (8.5%)** dostalo novou Y-ST redistribuci po redistribuci calc 233
- 71.6% z nich jsou ML3=1 zero-sellers → cyklické přesouvání bez přidané hodnoty
- Průměr 160 dní do smyčky, loop ratio ~100% (vrátí se co se odvezlo)
- **Doporučení:** SKU redistribuované v posledních 6-12M: ML +2

#### 2. Párová analýza Source↔Target
- **BEST (src OK + tgt all sold):** 35.1% (14,896) – NEJLEPŠÍ výsledek! Source nepotřebuje reorder a target vše prodal.
- **IDEAL (src OK + tgt partial + 1ks zbývá):** 11.6% párů (4,923) – perfektní stav s 1ks na skladě.
- **SRC FAIL + tgt sold:** 24.5% (10,390) + 7.4% (3,140) – source problém, ale target je v pořádku (prodal).
- **WASTED (src OK + tgt nothing):** 14.8% (6,274) – zbytečný přesun, target neprodal.
- **DOUBLE FAIL (src reorder + tgt nothing):** 6.6% (2,781) – kompletní selhání obou stran.
- **Celkový target ÚSPĚCH (all sold + partial):** 78.6% párů → redistribuce na targetu funguje v 4 z 5 případů!
- **Nejlepší tok:** Weak→Strong (2.8% double fail)
- **Nejhorší tok:** Strong→Weak (10.6% double fail), *→Weak (17-19% wasted)

#### 3. Backtest V2 (OVERSELL-based, s business rule)
- **5,762 SKU by se neredistribuovalo** → z nich 1,563 (27.1%) mělo oversell
- **Ušetřeno:** 1,670 ks oversell (redistribuované kusy by se prodaly i tak)
- **Ztraceno:** 4,496 ks úspěšných redistribucí (false positive)
- SkuClass enforcement: A-O a Z-O nikdy nemají ML=0 (31,773 + 3,288 SKU)
- KOREKCE: Inbound-based reorder (předchozí verze) ukazoval 53.9% problém, oversell-based jen 27.1% → inbound zkresloval

#### 4. Měsíční kadence (24M)
- Reorder roste lineárně: 0 měsíců → 28.5%, 6M → 57.3%, 10M → 67.1%, 16M → 81%
- Ale MinLayer roste pomalu: 0M→ML0.94, 10M→ML1.50, 16M→ML1.86
- **Počet aktivních měsíců je LEPŠÍ prediktor než 6M frekvence**
- Navrhovaná tabulka: 0M→0, 1-2M→1, 3-5M→2, 6-9M→3, 10-15M→4, 16+→5

#### Vianočná analýza (NOVÉ ZISTENIE)
- **Vianoce SÚ štatisticky relevantné!** SKU so sezónnym Xmas liftom: **29.1% oversell** vs 17-19% bez Xmas.
- Pre calc 233 (júl 2025): posledných 6M (jan-júl) NEOBSAHUJE Vianoce. Ale predchádzajúcich 6M (júl-dec 2024) ÁNO.
- **Xmas podiel z 12M predajov vs oversell:** 0% Xmas→15.9%, 21-40%→26.5%, 41-60%→25.4%, 61-100%→18.8%
- Paradox: 61-100% Xmas má NIŽŠÍ oversell (18.8%) než 21-60% (25-27%). Dôvod: čisto sezónne produkty (>60% Xmas) majú nízky ML (0.99) a po Vianociach sa nepredávajú → menej oversell.
- **Najrizikovejšie: 1-40% Xmas podiel** (26-27% oversell) = produkty, ktoré sa predávajú celoročne AJ cez Vianoce. Xmas nafukuje frekvenciu → MinLayer je príliš nízky.
- **Doporučenie pre decision tree:** Ak >=20% predajov spadá do Nov+Dec → "seasonal flag" → znížiť váhu Xmas mesiacov v frekvencii alebo pridať +1 ML pre sezónne produkty.

#### 5. Product concentration
- <=20 prodejen: 16-17% reorder. 100+ prodejen: **42.9% reorder** (2.5×)
- Široce distribuované produkty = vyšší riziko na source
- Target: 100+ prodejen = 63.2% all-sold vs 44.3% u 6-20

#### Promo/cenová analýza pre Declining vzorec (NOVÉ)
- **Declining SKU promo podiel:** 30.8% C-perioda vs 24.1% D-perioda → promo KLESÁ v D, nie rastie
- **Priemerná cena stála stabilne:** C=68.28 vs D=69.60 EUR → žiadny cenový prepad
- **Cross-store promo analýza:** 1-20% promo produkty majú NAJVYŠŠÍ oversell (34.4%), >50% promo = 27.8%
- **Cenové zmeny produktu:** Stabilná cena (1,185 SKU) = 31.7% oversell, pokles >15% (7 SKU) = 28.6%
- **ZÁVER:** Declining vzorec NIE JE spôsobený promo akciami ani cenovými zmenami! Promo podiel je rovnaký ako u iných vzorov (~30%). Problém je v tom, že produkt sa stále predáva (klesajúco ale konzistentne) a MinLayer to podceňuje.
- **Zaujímavosť:** Produkty s malým promo podielom (1-20%) majú vyšší oversell než tie s veľkým (>50%). Možné vysvetlenie: produkty s veľa promo sa predávajú hlavne v promo → po redistribúcii (mimo promo) sa toľko nepredajú.
#### 6. Ověření product trend analýzy
- POTVRZENO: Sales_Older (2024-07 až 2025-01) a Sales_Recent (2025-01 až 2025-07) jsou OBĚ PRE-redistribuce
- Trend je validní vstup pro decision tree

#### 7. SOURCE: Reorder vs Oversell vedľa seba (15 segmentov)
Segmenty kde je BEZPEČNÉ ZNÍŽIŤ source ML (oversell <10%):
- Dead+Weak: reorder=24.5%, **oversell=5.1%** → CAN LOWER ML
- Dead+Mid: reorder=29.5%, **oversell=7.8%** → CAN LOWER ML
- Dying+Weak: reorder=29.7%, **oversell=8.1%** → CAN LOWER ML
- Dying+Mid: reorder=35.4%, **oversell=9.7%** → CAN LOWER ML

Segmenty kde TREBA ZVÝŠIŤ source ML (oversell >20%):
- Declining+Strong: reorder=68.0%, **oversell=35.4%** → MUST RAISE
- Declining+Mid: reorder=64.7%, **oversell=28.3%** → MUST RAISE
- Declining+Weak: reorder=55.3%, **oversell=25.1%** → MUST RAISE
- Consistent+Strong: reorder=56.5%, **oversell=28.0%** → MUST RAISE
- Consistent+Mid: reorder=56.0%, **oversell=22.7%** → MUST RAISE
- Sporadic+Strong: reorder=47.8%, **oversell=20.1%** → MUST RAISE

OK segmenty (oversell 10-20%): Dead+Strong, Dying+Strong, Sporadic+Mid, Sporadic+Weak, Consistent+Weak

#### 8. TARGET: Sell-through analýza (NOVÉ – rovnako podrobné ako source)
**Sell-through distribúcia:**
- Nothing sold (0%): 8,872 SKU (21.3%) → PROBLÉM, ML znížiť
- Low (<30%): 35 SKU (0.1%) → zanedbateľné
- Medium (30-80%): 7,843 SKU (18.8%) → OK
- High (80-99%): 19 SKU (0.05%) → zanedbateľné
- All sold (100%+): 24,862 SKU (59.7%) → ÚSPECH, ML zvýšiť

**Sell-through podľa Store × Sales6M (4M a total):**
- Weak+Zero: ST_4M=0.49, ST_total=0.76, 43.7% nothing → ML ZNÍŽIŤ
- Weak+Low: ST_4M=0.37, ST_total=0.77, 34.6% nothing → ML ZNÍŽIŤ
- Strong+Med+: ST_4M=0.89, ST_total=1.83, 9.0% nothing → ML ZVÝŠIŤ (sell-through >100% = predá sa viac ako zásoby)
- Strong+Low: ST_4M=0.51, ST_total=1.09, 22.3% nothing → ML OK

**Sell-through podľa Brand-store fit:**
- Strong+Strong brand: ST_total=1.43, 16.5% nothing, 65.7% all-sold → NAJLEPŠÍ. ML ZVÝŠIŤ.
- Weak+Weak brand: ST_total=0.90, 30.7% nothing, 50.3% all-sold → NAJHORŠÍ. ML ZNÍŽIŤ.

**Sell-through podľa ceny:**
- <15 EUR: ST_total=2.10, 1.5% nothing → levné sa predajú vždy, ML ZVÝŠIŤ
- 30-60 EUR: ST_total=1.10, 25.1% nothing → stredné najhoršie
- 60+ EUR: ST_total=1.32, 18.5% nothing → drahé OK

**Sell-through podľa koncentrácie produktu:**
- <=20 predajní: ST_total=0.89, 38.6% nothing → ML ZNÍŽIŤ (produkt sa tu nepredáva)
- 100+ predajní: ST_total=1.32, 17.5% nothing → ML ZVÝŠIŤ
