# Semestrální projekt VMM – Střelecká úspěšnost

**Předmět:** Vícerozměrné statistické metody (VMM)  
**VUT Brno** | Akademický rok 2026/27  
**Dataset:** `shots_outcome_Final.csv` – střely z anglické Premier League (understat.com)

---

## Cíl projektu

Vícerozměrná statistická analýza střelecké úspěšnosti ve fotbale. Projekt sleduje logický metodický postup od průzkumové analýzy přes diagnostiku předpokladů až po prediktivní modelování.

## Struktura složek

```
projekt_02/
├── data/
│   └── shots_outcome_Final.csv       # Vstupní data
├── kody/
│   ├── analyza_strelecka_uspesnost.py  # Hlavní analytický skript (Fáze 1–7)
│   └── vytvor_prezentaci.py           # Skript pro generování PPTX prezentace
├── materialy/
│   ├── VMM-1.pdf … VMM-11.pdf        # Přednáškové materiály (pouze reference)
│   ├── VMM_Projekty2026.pdf          # Zadání projektu
│   └── *.py                          # Skripty ze cvičení (pouze reference)
├── vystupy/
│   ├── 01_mapa_strel.png             # Prostorová mapa střel na bílém fotbalovém hřišti
│   ├── 01b_hist_xG.png               # Histogram očekávaných gólů (xG)
│   ├── 02_normalita_histogramy_qq.png # Histogram dist_m + opravený Q-Q graf (scipy probplot)
│   ├── 02b_mahal_chisq_qq.png        # Mahalanobis D² chí-kvadrát diagram
│   ├── 03_korelacni_heatmapa.png     # Plná Spearmanova korelační heatmapa
│   ├── 04_boxploty_shottype.png      # Boxploty vzdálenosti a úhlu dle typu zakončení
│   ├── 04b_tukey_hsd.png             # Tukeyho HSD post-hoc test (95% intervaly)
│   ├── 05_scree_plot.png             # Scree plot PCA s Kaiserovým pravidlem
│   ├── 05b_biplot_pca.png            # 2D biplot PCA (osa kvality střelecké pozice)
│   ├── 05c_fa_varimax_loadings.png   # Faktorová analýza FA s rotací Varimax (VMM-9)
│   ├── 05d_tsne_strely.png           # Nelineární redukce dimenze t-SNE (VMM-10, 11)
│   ├── 06_dendrogram.png             # Wardův hierarchický dendrogram
│   ├── 06b_mapa_shluku.png           # Mapa shluků K-means (k=2) na fotbalovém hřišti
│   ├── 07_roc_krivka.png             # ROC křivka logistické regrese (AUC = 0,784)
│   ├── 07b_forest_plot.png           # Forest plot Odds Ratios (logaritmická osa X)
│   ├── tabulka_popis.csv             # Popisná statistika
│   ├── tabulka_hypotezy.csv          # Souhrnná tabulka všech testovaných hypotéz
│   ├── tabulka_logit_koeficienty.csv # Koeficienty logistické regrese a Odds Ratios
│   └── tabulka_vif.csv               # Diagnostika multikolinearity (VIF < 3,0)
└── prezentace/
    └── prezentace_strelecka_uspesnost.pptx  # Výsledná prezentace (14 slidů, 16:9)
```

## Metodický postup a přednášky VMM

| Fáze | Přednáška VMM | Metoda | Výstupní artefakt |
|------|---------------|--------|-------------------|
| 1 – EDA | VMM-1, 2 | Průzkum dat, škálování 100×100, 3-sigma | Mapa střel, histogram xG |
| 2 – Normalita | VMM-3 | Shapiro-Wilk, Q-Q graf (probplot), Levene, Mahalanobis D² | Histogram + Q-Q graf 1×2 |
| 3 – Korelace | VMM-4 | Spearmanova pořadová korelace, test r = 0 | Plná korelační heatmapa |
| 4 – ANOVA/MANOVA | VMM-5, 6 | Welchova ANOVA, Wilksova lambda MANOVA, Tukey HSD | Boxploty, diagram 95% IS |
| 5 – PCA | VMM-7, 8 | Bartlettův test, Scree plot, Kaiserovo pravidlo, Biplot | Scree plot, 2D Biplot |
| 6 – FA Varimax | VMM-9 | Faktorová analýza, rotace Varimax, skryté faktory | Heatmapa faktorových zátěží |
| 7 – t-SNE | VMM-10, 11 | Nelineární varietní mapování, lokální shluky střel | 2D rozptylový diagram t-SNE |
| 8 – Multikol. & Logit | VMM-4, 5 | Test VIF, Binární logistická regrese, ROC/AUC, Forest plot | Forest plot (log osa), ROC |
| 9 – Shlukování | VMM-11 | Wardovo hierarchické shlukování, K-means (k=2) | Dendrogram, mapa shluků |

## Spuštění

### Požadavky
Python 3.10+ a knihovny:
```bash
pip install pandas numpy scipy statsmodels scikit-learn seaborn matplotlib pingouin python-pptx
```

### Krok 1 – Analýza a generování grafů
```bash
cd kody
PYTHONUTF8=1 python analyza_strelecka_uspesnost.py
# Windows PowerShell:
# $env:PYTHONUTF8=1; py analyza_strelecka_uspesnost.py
```

### Krok 2 – Generování prezentace
```bash
PYTHONUTF8=1 python vytvor_prezentaci.py
# Windows PowerShell:
# $env:PYTHONUTF8=1; py vytvor_prezentaci.py
```

Výstupy se ukládají do složek `vystupy/` a `prezentace/`.

## Klíčové výsledky

- **Normalita** (Shapiro-Wilk): Porušena pro dist_m, xG i angle_deg (p < 0,001) → formální zdůvodnění robustních a neparametrických metod.
- **Leveneho test**: Prokázaná heteroskedasticita (p < 0,001) → nutnost Welchovy ANOVA namísto klasické.
- **Korelační analýza**: Silná záporná Spearmanova korelace xG ↔ dist_m (r = −0,73, p < 0,001) a kladná xG ↔ angle_deg (r = +0,44).
- **Welchova ANOVA & MANOVA**: Způsob zakončení (noha vs. hlava) statisticky vysoce významně ovlivňuje geometrii střely (Wilks λ = 0,806, p = 4,44 × 10⁻²⁷).
- **Tukeyho HSD**: Hlava se zásadně liší od střelby nohou (Δ dist ≈ +11 j., Δ úhel ≈ −22°); mezi levou a pravou nohou není signifikantní rozdíl.
- **PCA**: 2 hlavní komponenty vysvětlují ~68 % rozptylu; PC1 představuje „osu kvality střelecké pozice".
- **Faktorová analýza (Varimax)**: Identifikovány 2 latentní faktory – F1 (geometrická kvalita pozice) a F2 (herní hloubka zakončení).
- **Nelineární t-SNE**: Úspěšné góly tvoří kompaktní sub-varietu v prostoru nelineárního mapování.
- **Multikolinearita (VIF)**: Všechny hodnoty VIF < 3,0 (dist_m: 2,69; angle_deg: 2,87; xG: 1,74; minuta: 1,01), model netrpí škodlivou kolinearitou.
- **Logistická regrese**: Model dosahuje diskriminační schopnosti ROC AUC = 0,784; xG je nejsilnějším pozitivním prediktorem (OR ≈ 76,0), vzdálenost dist_m šanci na gól sráží (OR = 0,922).
- **Shluková analýza (Ward & K-means k=2)**: Dva přirozené herní profily – efektivní střely z vápna (prům. dist 13 j.) vs. neefektivní střelba z dálky (prům. dist 25 j.).
