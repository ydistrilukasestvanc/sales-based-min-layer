Poterbujem urobit analytiku nad projektom:
Server: DEV
databaza: ydistri-sql-db-dev-tenant-douglasde
NIKDY SA V RAMCI TEJTO SESSION NEPRIPOJUJ NIEKDE INDE


Ide mi o redistribuciu CalculationId=233 -> vsetky udaje su v SkuRedistributionExpanded. Pozor v tejto tabulke moze byt SourceSkuId viac krat (ak ma viac TargetSKuId) a takisto aj TargetSkuId viac krat (ak ma viac SourceSKuId)

V ramci vypoctov pouzivame heuristiku SalesBased minimum layers. Toto su vypocitane minimalne vrstvy na zaklade pravidiel:
napriklad, ak je v planograme -> moze byt ako Target -> Potom to ma urcite aspon 1
Ak sa predal aspon jeden krat za poslednych 6 mesiacov -> moze mat medzi 1 a 2
Ak sa predal aspon 4 krat, moze mat 3
Toto su len priklady pravidiel, rozlisujeme medzi sales cez vianoce (mesiace 11,12) a ostatnymi a tak dalej
Zaroven pravidla mozu byt ine pre SOURCE a pre TARGET

Natavujeme to takto agresivnejsie preto, lebo redistribucie prebiehaju 1x za mesiac. A ak by sme na target nechali len 1 kus, tak on sa preda v priebehu mesiaca -> system ho objedna automaticky a my nemame sancu tento produkt zazasobit redistribuciou



Minimalna vrstva pre SourceSkuId je v tejto tabulke v stlpceku: SourceMinLayerListQuantity
Minimalna vrstva pre TargetSkuId je v tejto tabulke v stlpceku: TargetMinLayerListQuantity


Pravidla su jednoduche, ale zda sa nam, ze nie  vzdy funguju spravne. V com mame problem:
SOURCE - predaje sa po redistribucii ZVYSIA (co je nelogicke, lebo odvazame prec):
- stava sa, ze produkt sa nepredal 6-10 mesiacov, ale potom sa zacne predavat (po odvezeni). Toto moze mat 
-- ak sa predtym predaval rovnako sporadicky, tak proste len prebehla jeho casova perioda a predal sa
-- ak sa predal za poslednych 6 mesiacov 0, tak sa vzdy moze predaj len zvysit, lebo statistiky nie je mozne ho znizit
-- ak sa predaval predtym OK a teraz sa nepredava, mohol to byt phantom stock - to znamena, ze on tam nebol fyziciky, len v systeme. A ked prisla obsluha ho poslat prec, zistila,z e tam nie je, objednala ho a zacala ho predavat. alebo bol v backstore a oni ho vystavili. Takze realne riesenie. 
--- nahodne zyvsenie / znizenie predajov sa daju overit cez cele ProductId (SkuId na vsetkych predajniach). Ak existuje statisticka pravdepodobnost, ze sa vsetky predaje znizili a potom znova po redistri zvysili, tak je pravdepodobne, ze tam bola medzitym horsia cena, akcia na konkurencne produkty a tak a toto by sme mali zistit

TARGET - predaje sa znizia
- toto je takisto statisticky podlozitelne - my redistribuujeme tam, kde v poslednej dobe prebehol vysoky predaj. Toto ma nasledne 2 dosledky
-- 1) zvysil sa forecast, lebo reaguje na zmenu (a nemusel to vyhodnotit ako extrm)
-- 2) zvysenym predajom prudko klesla zasoba a potrebujeme ju doplnit


Dalsie nezrovnalosti nastavaju, ked posielame zo silneho obchodu do slabeho.
Par nahodnych predajov na slabom obchode sposobi pokles zasoby a my to tam agresivne doplnime zo silenjsieho, kde sa zhodou okolnosti par mesiacov nepredal.
Toto je sice spravne, takto to chceme, ale chceli by sme silnejsie obchody TROSKU viac ochranovat a slabsie TROSKU menej doplnovat.

Silu  obchod mozeme posudzovat celkovymi trzbami za posledne obdobie par mesiacov, ale aj rezom cez znacku (nejaky slaby obchod moze by specializovane na nejaky BrandId a preto je v tomto konkretnom silny).

Silu obchodu by som riesil cez Percentil (napr top 10% obchodov - silne, potom priemer a potom slabe). Hranice si skus urcite sam, ako nastavit percentily.
Nepocitaj z obhocom online /ecomm - warehouseId = 300

Dalsia vec su STOCKOUTS - ak tam nie je zasoba, tak nemozeme ocakavat, ze sa bude predavat. Hostiru zasoby vies zistit z SkuAvailableSupply. Ak je DateTo NULL tak to znamena, ze zasoba stale plati do "dnes". Inak su tam intervaly. Prvy datum pre dane SKU Je prva evidencia toho, ze Sku bolo na sklade. 

Dalsia vec je cena - problemy mozu byt sposobene len pre produkty s nejakou cenou

Problem:
- problemom v redistribucii volame to, ze sme produkt odviezli a on sa musel v nejakom case objednat (pripadne sa predal). potrebujeme sledovat cas 4 mesiace a celkovy cas (od redistribucie az po teraz)
-- pre toto mame 2 terminy. 
--- REORDER - objednal sa - znamena to, ze v tabulke Income je zaznam pre dane Sku po termine redistribucie
--- OVERSELL - objedna sa a predal sa. to znamena, ze v tabulke SaleTransaciton je viac predajov po datume redistribucie, ako bola zasoba. To znamena, ze to co sa REORDEROVALO sa aj predalo
-- oba problemy "resp. velkost problemu" musi byt ohranicena velkostou redistribucie. takze ak sme odviezli 2 kusy, musime zacapovat aj reorder/oversell na 2 kusy

- problem je takisto to, ze sme ho niekam priviezli - bol target - a nepredal sa.
-- to znamena, ze zasoba, ktora tam bola na sklade pred dovezenim + to co je dovezene este nie je predane. 
-- cielom je, aby na cielovej predajni ostal 1 kus - nie predalo sa vsetko - TOTO JE KRITICKE - lebo keby bola 0, oni to objednaju  a my chceme tieto target - lepsie predajne predajne zasobovat z nadzasob
-- v nejakom case na Targete moze byt aj problem, ze zasobe sa zmenila SkuClass na iny hodnotu ako "A", alebo "Z" a potom je to uz neziaduci produkt. Stav je mozne zistit historicky z tabulky SkuAttributeValue -> datum pre ktory toto plati je v tabulke AttributeValue


Ako by som chcel aby si pracoval
- vytvor mi strukturovane zadanie, kde mi popises co vsetko budes skusat, testovat. ako budes postupovat
- rozanalyzuj si tabulky SkuRedistributionExpanded, SaleTransaction, SkuAvailableSupply, AttributeValue, SkuClass, ... Zisti si ich velkosti, stlpce a zisti, co vsetko bdues z nich potrebovat. Vysvetli mi podrobne vsetky slpce, ktore si myslis ze budes potrebovat a ja ti potvrdim v zadani ci je to pravda
- odporucam ti do temp vytvorit a naindexovat subsety tabuliek len pre SKu ktore budes potrebovat (source/target) -> plus asi vsetky ProductId danych Sku -> ak budes robit analytiku cez produkt
- po potvrdeni predchadzajucich budov (v novom zadanie - structured_assignment.md) mozes zacat pracovat. Zadanie structured_assignment mi napis v cestine
- v priebehu implementacie zadania urcite prides na mnozstvo zaujimavosti. budes bezat celu noc - sam - takze ak najdes zaujimavost - mozes pridavat do zadania dalsie body a pridavat si dalsie testy a analytiky
- mozes pouzivat python na datovu analytiku. mozes pouzivat plne SQL a vytvarat si tabulky v temp scheme. takisto si ich tam mozes indexovat. bude to velmi vhodne, lebo si mozes ukladat medzivysledky
- pozri sa na to z roznych uhlov pohladu, aj to co tu nie je, urcite ta napadne vsetko mozne

Co ma byt vysledkom:
- vysledkom by mala byt podrobna analytika, kde sme sa pomylili na zaklade minimalnej vrstvy a tvoj odhad preco. Toto strukturovane rozdelit do roznych skupin podla pravidiel (ceny, velkosti predajni, typovo predaje - predtym silne,teraz slabe. predaje blizko po sebe -> velka nahoda. nerovnomerne rozlozenie predajov - slabne znacky na predajni, nahoda ze sa nepredalo / predalo. Pre vsetky problemy ktore najdes je potrebne povedat -> ok, v tejto skupine sme boli takto uspesny / neuspesny na source (reorder, oversell) a uspesny / neuspesny na target (not sold). To vsetko pre intervaly 4 mesiacoch a do teraz. Zaroven ked sa bavime "do teraz" tak tam pada obdobie vianoc a kolko z toho uspechu a neuspechu bolo pokrytych v 12 mesiaci.


- tato cela analyza sluzi na to, aby sme vedeli systematicky specifikovat - strojovo! pravidla pre minimalne vrstvy na zaklade frekvencnej vzorky predaja za obdobie a dalsich parametrov - brand, obchod, cena, znacka, struktura za nejake obdobia, struktura cez vianoce. Nejde tu o FORECAST, ide to o pravdepodobnostne nastavenie predaja.

-












