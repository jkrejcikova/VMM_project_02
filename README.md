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
│   ├── 01_mapa_strel.png             # Mapa střel na hřišti
│   ├── 01b_hist_xG.png               # Histogram xG
│   ├── 02_normalita_histogramy_qq.png # Histogramy + Q-Q grafy (Fáze 2)
│   ├── 02b_mahal_chisq_qq.png        # Mahalanobis D² diagram
│   ├── 03_korelacni_heatmapa.png     # Plná Spearmanova korelační heatmapa
│   ├── 04_boxploty_shottype.png      # Boxploty dle typu zakončení
│   ├── 04b_tukey_hsd.png             # Tukeyho HSD post-hoc test (95% IS)
│   ├── 05_scree_plot.png             # Scree plot PCA
│   ├── 05b_biplot_pca.png            # 2D biplot PCA
│   ├── 06_dendrogram.png             # Hierarchický dendrogram
│   ├── 06b_mapa_shluku.png           # Mapa shluků na hřišti
│   ├── 07_roc_krivka.png             # ROC křivka logistické regrese
│   ├── 07b_forest_plot.png           # Forest plot Odds Ratios
│   ├── tabulka_popis.csv             # Popisná statistika
│   ├── tabulka_hypotezy.csv          # Souhrnná tabulka hypotéz
│   └── tabulka_logit_koeficienty.csv # Koeficienty logistické regrese
└── prezentace/
    └── prezentace_strelecka_uspesnost.pptx  # Výsledná prezentace (12 slidů)
```

## Metodický postup

| Fáze | Metoda | Výstup |
|------|--------|--------|
| 1 – EDA | Průzkum dat, škálování, pravidlo 3-sigma | Mapa střel, histogram xG |
| 2 – Normalita | Shapiro-Wilk, Q-Q grafy, Mahalanobis D², Levene | Histogramy + diagnostické grafy |
| 3 – Korelace | Pearson, Spearman, test významnosti | Korelační heatmapa |
| 4 – ANOVA/MANOVA | Welchova ANOVA, MANOVA, Tukey HSD | Boxploty |
| 5 – PCA | Bartlettův test, KMO, Scree plot, biplot | Scree plot, biplot |
| 6 – Shlukování | Hierarchické (Ward), K-means k=2 | Dendrogram, mapa shluků |
| 7 – Logit | Logistická regrese, ROC/AUC | ROC křivka, forest plot |

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

- **Normalita** (Shapiro-Wilk): Porušena pro xG, dist_m i angle_deg → robustní metody
- **Levene test**: Heteroskedasticita → Welchova ANOVA místo klasické ANOVA  
- **Korelace**: Silná záporná Spearmanovo korelace xG ↔ dist_m (r = −0.73)
- **Welchova ANOVA** + **MANOVA**: Typ zakončení (Foot/Head) statisticky významně ovlivňuje geometrii střely (p < 0,001)
- **PCA**: 2 komponenty vysvětlují ~70 % rozptylu; PC1 = „osa kvality střelecké pozice"
- **K-means k=2**: Dva přirozené profily – střely z vápna vs. střelba z dálky
- **Logistická regrese**: AUC = 0.78, dist_m a xG jsou statisticky významné prediktory gólu
