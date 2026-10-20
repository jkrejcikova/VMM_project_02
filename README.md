# Semestrální projekt VMM – Střelecká úspěšnost

**Předmět:** Vícerozměrné statistické metody (VMM)  
**VUT Brno** | Akademický rok 2026/27  
**Dataset:** `shots_outcome_Final.csv` – střely z anglické Premier League (understat.com)

---

## Cíl projektu

Vícerozměrná statistická analýza faktorů střelecké úspěšnosti ve fotbale. Projekt sleduje logický metodický postup od prvotního průzkumu dat přes diagnostiku předpokladů (normalita, homoskedasticita, multikolinearita) až po pokročilé vícerozměrné metody (MANOVA, PCA, faktorová analýza s rotací Varimax, shluková analýza a binární logistická regrese).

---

## Struktura složek a výstupů

```
projekt_02/
├── data/
│   └── shots_outcome_Final.csv              # Původní datová sada střel Premier League
├── kody/
│   ├── analyza_strelecka_uspesnost.py         # Hlavní analytický skript (Fáze 1–9)
│   └── vytvor_prezentaci.py                  # Generátor výsledné PPTX prezentace (13 slidů)
├── materialy/
│   ├── VMM-1.pdf … VMM-11.pdf               # Přednáškové podklady (reference)
│   ├── VMM_Projekty2026.pdf                 # Zadání projektu
│   └── *.py                                 # Referenční skripty ze cvičení
├── vystupy/
│   ├── 01_mapa_strel.png                    # Prostorová mapa střel na celém fotbalovém hřišti (100 × 100)
│   ├── 01b_hist_xG.png                      # Histogram očekávaných gólů (xG) s pravostrannou asymetrií
│   ├── 01c_kde_hriste.png                   # 2D KDE vrstevnice hustoty střelby na hřišti (VMM-3/4)
│   ├── 02_normalita_histogramy_qq.png        # Histogram dist_m + Q-Q graf (scipy probplot) (1×2)
│   ├── 03_korelacni_heatmapa.png            # Plná Spearmanova korelační matice s velkými popiskami
│   ├── 03b_pairplot.png                     # Pair-plot klíčových proměnných s KDE křivkami na diagonále
│   ├── 04_boxploty_shottype.png             # Boxploty vzdálenosti a úhlu dle zakončení (Welch ANOVA)
│   ├── 04b_tukey_hsd.png                    # Tukeyho HSD post-hoc test (95% IS) a Wilksova lambda MANOVA
│   ├── 05_scree_plot.png                    # Samostatný Scree plot PCA s Kaiserovým pravidlem
│   ├── 05b_biplot_pca.png                   # Scree plot + 2D Biplot PCA (osa kvality střelecké pozice)
│   ├── 05c_fa_varimax_loadings.png          # Faktorová analýza FA s rotací Varimax (VMM-9)
│   ├── 06_dendrogram.png                    # Hierarchický dendrogram (Wardova metoda)
│   ├── 06b_mapa_shluku.png                  # Mapa shluků K-means (k=2) na fotbalovém hřišti
│   ├── 07_roc_krivka.png                    # ROC křivka logistické regrese (AUC = 0,784)
│   ├── 07b_logisticka_krivka.png            # Sigmoidální křivka P(gól) vs. dist_m + ROC křivka (1×2)
│   ├── tabulka_popis.csv                    # Popisná statistika sledovaných proměnných
│   ├── tabulka_hypotezy.csv                 # Souhrnná tabulka všech 12 testovaných statistických hypotéz
│   ├── tabulka_logit_koeficienty.csv        # Odhady koeficientů, Odds Ratios a p-hodnoty logistického modelu
│   └── tabulka_vif.csv                      # Diagnostika multikolinearity prediktorů (VIF < 3,0)
└── prezentace/
    └── prezentace_strelecka_uspesnost.pptx # Výsledná prezentace (13 slidů, 16:9, čistě bílý styl)
```

---

## Metodický přehled a vazba na přednášky VMM

| Fáze | Přednáška VMM | Aplikovaná metoda | Klíčový výstup / Artefakt |
| :--- | :--- | :--- | :--- |
| **1 – EDA & Prostor** | VMM-1, 2 | Čištění dat, eliminace vlastních branek, škálování hřiště 100×100, 3-sigma | `01_mapa_strel.png`, `01b_hist_xG.png` |
| **2 – 2D KDE Hustota** | VMM-3, 4 | Dvourozměrný odhad hustoty jádrovým vyhlazováním (2D KDE vrstevnice) | `01c_kde_hriste.png` |
| **3 – Normalita & Rozptyly** | VMM-3 | Shapiro-Wilkův test normality, empirický Q-Q diagram (`probplot`), Leveneho test | `02_normalita_histogramy_qq.png` |
| **4 – Korelace & Vztahy** | VMM-4 | Spearmanova pořadová korelační matice, párové scatter ploty s KDE diagonálou | `03_korelacni_heatmapa.png`, `03b_pairplot.png` |
| **5 – ANOVA & MANOVA** | VMM-5, 6 | Welchova ANOVA pro heteroskedastická data, Wilksova lambda MANOVA, Tukeyho HSD | `04_boxploty_shottype.png`, `04b_tukey_hsd.png` |
| **6 – PCA** | VMM-7, 8 | Bartlettův test sférickosti, Scree plot (Kaiserovo pravidlo), 2D Biplot | `05b_biplot_pca.png` |
| **7 – Faktorová analýza** | VMM-9 | Faktorová analýza s ortogonální rotací Varimax, identifikace skrytých faktorů | `05c_fa_varimax_loadings.png` |
| **8 – Logistická regrese** | VMM-4, 5 | Test multikolinearity VIF, sigmoidální logistická křivka, ROC křivka (AUC) | `07b_logisticka_krivka.png`, `tabulka_vif.csv` |
| **9 – Shluková analýza** | VMM-11 | Wardovo aglomerativní hierarchické shlukování, K-means ($k=2$) na hřišti | `06_dendrogram.png`, `06b_mapa_shluku.png` |

---

## Struktura prezentace (13 snímků, poměr 16:9)

1. **Slide 1 – Titulní snímek:** Čistý minimalistický design na bílém podkladu (`#FFFFFF`), název práce, autor, předmět VMM.
2. **Slide 2 – Představení dat a proměnných (Čistě textový slide):** Popis vzorku ($n=998$ / $n=734$ střel po vyřazení chybějících souřadnic a odlehlých hodnot), cíle výzkumu a přehledná tabulka sledovaných veličin.
3. **Slide 3 – Mapa střel:** Celé fotbalové hřiště (0 až 100 jednotek), kontrastní body (góly červeně, neproměněné modře, $s=45$, $\alpha=0.7$).
4. **Slide 4 – 2D KDE hustota střelby na hřišti:** Plynulé vrstevnice hustoty střelby demonstrující ohnisko gólů přímo před brankou.
5. **Slide 5 – Diagnostika normality:** 1 řádek se 2 velkými grafy (histogram `dist_m` s proloženou normální křivkou a Q-Q graf `scipy.stats.probplot`).
6. **Slide 6 – Spearmanova korelační analýza:** Plná korelační matice s velkými čitelnými koeficienty a testem $r=0$.
7. **Slide 7 – Pair-plot s KDE křivkami:** Párové vztahy `dist_m`, `angle_deg` a `xG` barevně rozlišené dle proměnné `goal`.
8. **Slide 8 – Welchova ANOVA:** Porovnání vzdálenosti a úhlu podle typu zakončení s vyčíslenou Welchovou statistikou a $p$-hodnotou.
9. **Slide 9 – MANOVA & Tukeyho HSD:** Sdružené vícerozměrné posouzení (Wilksova $\lambda$) a post-hoc párové porovnání s 95% intervaly spolehlivosti.
10. **Slide 10 – Redukce dimenze PCA:** Scree plot a 2D Biplot s dominantní první hlavní komponentou (osa kvality pozice).
11. **Slide 11 – Faktorová analýza (Varimax):** Heatmapa faktorových zátěží se 2 latentními dimenzemi (F1 = Geometrická kvalita, F2 = Herní hloubka).
12. **Slide 12 – Logistická regrese:** Sigmoidální křivka pravděpodobnosti $P(\text{gól})$ v závislosti na vzdálenosti s kalibračními body a ROC křivka ($\text{AUC} = 0,784$).
13. **Slide 13 – Souhrnná tabulka hypotéz & trenérská doporučení:** Přehled všech 12 testovaných hypotéz a 4 praktická herní doporučení pro trenéry.

---

## Spuštění projektu

### Požadavky na prostředí
Python 3.10+ se standardními vědeckými balíčky:
```bash
pip install pandas numpy scipy statsmodels scikit-learn seaborn matplotlib pingouin python-pptx
```

### Krok 1 – Spuštění statistické analýzy a přegenerování grafů
```bash
cd kody
# Na Linuxu/macOS:
PYTHONUTF8=1 python analyza_strelecka_uspesnost.py

# Na Windows (PowerShell):
$env:PYTHONUTF8=1; py analyza_strelecka_uspesnost.py
```

### Krok 2 – Vygenerování PowerPointové prezentace
```bash
# Na Linuxu/macOS:
PYTHONUTF8=1 python vytvor_prezentaci.py

# Na Windows (PowerShell):
$env:PYTHONUTF8=1; py vytvor_prezentaci.py
```

Výsledná prezentace se uloží do `prezentace/prezentace_strelecka_uspesnost.pptx`.

---

## Hlavní statistické výsledky

1. **Normalita & Homoskedasticita (VMM-3):**
   - Shapiro-Wilkův test prokázal signifikantní porušení normality pro `dist_m` ($W = 0,984$, $p < 0,001$), `xG` ($W = 0,543$, $p < 0,001$) i `angle_deg` ($W = 0,794$, $p < 0,001$).
   - Leveneho test potvrdil heteroskedasticitu rozptylů ($L = 11,00$, $p < 0,001$), což odůvodnilo nasazení Welchovy ANOVA namísto klasické jednofaktorové ANOVA.

2. **Korelace & Párové vazby (VMM-4):**
   - Silná záporná Spearmanova korelace mezi `xG` a `dist_m` ($r = -0,732$, $p < 0,001$) a pozitivní vazba mezi `xG` a `angle_deg` ($r = +0,436$, $p < 0,001$).
   - Pair-plot s KDE křivkami na diagonále jasně separuje góly do zóny krátkých vzdáleností ($< 15\text{ m}$) a tupých zorných úhlů ($> 30^\circ$).

3. **Vícerozměrné srovnání skupin zakončení (VMM-5, 6):**
   - Wilksova lambda MANOVA potvrdila vysoce významný sdružený rozdíl v geometrii střely dle typu zakončení ($\lambda = 0,806$, $F = 42,03$, $p = 4,44 \times 10^{-27}$).
   - Tukeyho HSD post-hoc test ukázal, že hlavičky se zásadně liší od střelby nohou ($\Delta \text{dist} \approx +11\text{ j.}$, $\Delta \text{úhel} \approx -22^\circ$, obojí $p < 0,001$). Mezi levou a pravou nohou nebyl zjištěn statisticky významný rozdíl ($p = 0,22$).

4. **PCA & Faktorová analýza Varimax (VMM-7, 8, 9):**
   - Bartlettův test sférickosti ($\chi^2 = 2041,4$, $p < 0,001$) potvrdil vhodnost faktorového zkoumání.
   - PCA zachycuje v prvních 2 komponentách $67,8\,\%$ rozptylu; PC1 představuje osu kvality střelecké pozice.
   - Faktorová analýza s rotací Varimax odhalila 2 ortogonální faktory: $F_1$ (Kvalita střeleckého úhlu a xG) a $F_2$ (Herní hloubka a postup po hřišti).

5. **Multikolinearita & Logistická regrese (VMM-4, 5):**
   - Všechny hodnoty VIF jsou hluboko pod kritickou hranicí $5,0$ (`dist_m`: 2,69; `angle_deg`: 2,87; `xG`: 1,74; `minute`: 1,01), multikolinearita nepředstavuje riziko.
   - Logistická regresní křivka názorně demonstruje prudký propad šance na gól se vzdáleností: při $10\text{ m}$ činí šance $\sim 25\,\%$, na $25\text{ m}$ klesá pod $3\,\%$ ($\text{OR} = 0,922$ na metr, $p = 0,029$). Model dosahuje vysoké diskriminační schopnosti ($\text{ROC AUC} = 0,784$).

6. **Segmentace střel (VMM-11):**
   - K-means shlukování ($k=2$) rozděluje střely na efektivní zakončení z prostoru velkého vápna (průměrná vzdálenost $13\text{ j.}$, konverze $12,7\,\%$) a nebezpečné neefektivní pokusy z dálky (průměrná vzdálenost $25\text{ j.}$, konverze pod $3\,\%$).
