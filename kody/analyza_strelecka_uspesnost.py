# -*- coding: utf-8 -*-
# =============================================================================
# SEMESTRÁLNÍ PROJEKT – VÍCEROZMĚRNÉ STATISTICKÉ METODY (VMM)
# Téma: Střelecká úspěšnost ve fotbale
# Autor: Janáčková
# VUT Brno, 2026
# =============================================================================
# POUŽITÉ KNIHOVNY:
#   pandas     – načítání a manipulace s tabulkovými daty
#   numpy      – numerické výpočty a vektory
#   scipy      – statistické testy (Shapiro-Wilk, Levene, chí-kvadrát, ...)
#   statsmodels– ANOVA, MANOVA, logistická regrese
#   sklearn    – PCA (analýza hlavních komponent), K-means shlukování, ROC/AUC
#   matplotlib – kreslení grafů
#   seaborn    – pokročilá vizualizace (heatmapy, boxploty)
#   pingouin   – Tukeyho HSD post-hoc test, KMO
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')          # neinteraktivní backend pro uložení bez okna
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from scipy.spatial.distance import mahalanobis
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
import statsmodels.api as sm
from statsmodels.multivariate.manova import MANOVA
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import roc_curve, auc
import pingouin as pg

warnings.filterwarnings('ignore')   # potlačíme varování, aby výstup byl přehledný

# =============================================================================
# NASTAVENÍ CEST
# =============================================================================
BASE   = os.path.join(os.path.dirname(__file__), '..')   # kořen projektu
DATA   = os.path.join(BASE, 'data',     'shots_outcome_Final.csv')
VYSTUPY = os.path.join(BASE, 'vystupy')
os.makedirs(VYSTUPY, exist_ok=True)

# Globální styl grafů – čistý, vhodný pro akademickou prezentaci
plt.rcParams.update({
    'figure.dpi': 300,          # vysoké rozlišení pro tisk
    'savefig.dpi': 300,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'figure.facecolor': 'white',
    'axes.facecolor': '#f8f9fa',
})
sns.set_theme(style='whitegrid', palette='tab10')

# =============================================================================
# POMOCNÉ FUNKCE
# =============================================================================

def uloz(nazev_souboru):
    """Uloží aktuální matplotlib figuru do složky vystupy/ a zavře ji."""
    cesta = os.path.join(VYSTUPY, nazev_souboru)
    plt.savefig(cesta, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  [OK] Graf uložen: {nazev_souboru}')


def nakresli_hrice(ax, barva_povrchu='#3a8a3a'):
    """
    Nakreslí schematické fotbalové hřiště (100x100 jednotek) na osu ax.
    Souřadnice X = délka hřiště (0=levá branka, 100=pravá branka),
    Y = šířka hřiště (0=spodní, 100=horní okraj).
    Schéma je zjednodušené – brankové plochy, trestné území, střed.
    """
    ax.set_facecolor(barva_povrchu)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    def rect(x, y, w, h, **kw):
        ax.add_patch(mpatches.Rectangle((x, y), w, h, **kw))

    kw_line = dict(edgecolor='white', facecolor='none', linewidth=1.5)
    # Ohraničení hřiště
    rect(0, 0, 100, 100, **kw_line)
    # Středová čára
    ax.plot([50, 50], [0, 100], color='white', linewidth=1.5)
    # Středový kruh (poloměr ~9 jednotek)
    kruh = plt.Circle((50, 50), 9.15, color='white', fill=False, linewidth=1.5)
    ax.add_patch(kruh)
    ax.plot(50, 50, 'o', color='white', markersize=3)
    # Levé pokutové území
    rect(0, 21.1, 16.5, 57.8, **kw_line)
    rect(0, 36.8, 5.5, 26.4, **kw_line)
    # Pravé pokutové území
    rect(83.5, 21.1, 16.5, 57.8, **kw_line)
    rect(94.5, 36.8, 5.5, 26.4, **kw_line)
    # Brány
    rect(0, 45.2, -1.5, 9.6, edgecolor='white', facecolor='white', linewidth=1.2)
    rect(100, 45.2, 1.5, 9.6, edgecolor='white', facecolor='white', linewidth=1.2)

    ax.set_xlabel('X (délka hřiště)')
    ax.set_ylabel('Y (šířka hřiště)')


# =============================================================================
# FÁZE 1: PRŮZKUMOVÁ ANALÝZA A PŘEDZPRACOVÁNÍ DAT (EDA)
# =============================================================================
print('=' * 70)
print('FÁZE 1 – PRŮZKUMOVÁ ANALÝZA A PŘEDZPRACOVÁNÍ DAT')
print('=' * 70)

# --- Načtení dat ---
# pd.read_csv() přečte CSV soubor do DataFrame (tabulky v paměti).
df_raw = pd.read_csv(DATA)

print(f'\nPočet řádků (střel):    {len(df_raw)}')
print(f'Počet sloupců (proměn.): {df_raw.shape[1]}')
print(f'\nSloupce a datové typy:\n{df_raw.dtypes}')
print(f'\nChybějící hodnoty:\n{df_raw.isnull().sum()[df_raw.isnull().sum() > 0]}')

# --- Vyřazení vlastních branek (OwnGoal) ---
# OwnGoal není střelecká akce hráče – narušovaly by analýzu výběru.
df = df_raw[df_raw['result'] != 'OwnGoal'].copy()
print(f'\nPo vyřazení OwnGoal: {len(df)} střel')

# --- Definice binární cílové proměnné ---
# Gól = 1, jakýkoliv jiný výsledek = 0.
# Toto je základ pro logistickou regresi v Fázi 7.
df['goal'] = (df['result'] == 'Goal').astype(int)
print(f"Rozdělení výsledků:\n{df['result'].value_counts()}")
print(f"Podíl gólů: {df['goal'].mean():.2%}")

# --- Škálování souřadnic X a Y na standardní fotbalové hřiště 100×100 ---
# Původní hodnoty jsou normalizované (0–1). Převod: jednoduché ×100.
# Tím dostaneme hodnoty v procentech délky/šířky hřiště.
df['X'] = df['X'] * 100   # osa délky (0=vlastní polovina, 100=brankoviště)
df['Y'] = df['Y'] * 100   # osa šířky hřiště

# --- Odvození geometrických veličin střely ---
# Vzdálenost od středu branky (branka pravá: X=100, Y=50) v "hřištních jednotkách"
# Vzorec: pythagorova věta √((100-X)² + (50-Y)²)
df['dist_m'] = np.sqrt((100 - df['X'])**2 + (50 - df['Y'])**2)

# Střelecký úhel v stupních – jak velký "výsek" vidí střelec na branku.
# Více viz: https://soccermatics.readthedocs.io/
# Branka: Y ∈ [45.2, 54.8] → šířka branky ≈ 9.6 jednotek
# Používáme arctan2 pro robustnější výpočet úhlu.
y_min_branky = 45.2   # dolní tyč branky
y_max_branky = 54.8   # horní tyč branky
x_br = 100.0          # branková čára

df['angle_deg'] = np.degrees(
    np.abs(
        np.arctan2(df['X'] - x_br, df['Y'] - y_min_branky) -
        np.arctan2(df['X'] - x_br, df['Y'] - y_max_branky)
    )
)

# --- Ošetření kategorických chybějících hodnot ---
# NaN u textových kategorií nahradíme smysluplnou hodnotou, ne výmazem řádku.
df['player_assisted'] = df['player_assisted'].fillna('Bez asistence')
df['shotType']        = df['shotType'].fillna('Neznamy')
df['situation']       = df['situation'].fillna('Neznama')

# --- Výběr klíčových proměnných pro analýzu ---
# Vyřadíme technické ID a metadata (id, player_id, match_id, datum, týmy).
NUM_COLS = ['X', 'Y', 'dist_m', 'angle_deg', 'xG', 'minute']  # spojité proměnné
CAT_COLS = ['shotType', 'situation']                             # kategorie
TARGET   = 'goal'                                               # cílová proměnná

print(f'\nKlíčové numerické proměnné: {NUM_COLS}')
print(f'Kategorické proměnné:       {CAT_COLS}')

# --- Ošetření chybějících hodnot u numerických sloupců ---
# U X a Y NEIMPUTUJEME (nechceme falešné střely v ose hřiště).
# Řádky bez souřadnic vynecháme pouze tam, kde je potřebujeme (geometrické výpočty).
df_geo = df.dropna(subset=['X', 'Y', 'xG']).copy()  # čistá sada pro geometrické analýzy
print(f'\nSada se souřadnicemi (df_geo): {len(df_geo)} střel')
print(f'Kompletní sada (df):            {len(df)} střel')

# --- Pravidlo 3-sigma (Z-skóre) na proměnnou dist_m ---
# Vyloučíme fyzicky nesmyslné střely (vzdálenost > průměr + 3×std),
# které by deformovaly korelační analýzu a normality test.
z_dist = np.abs(stats.zscore(df_geo['dist_m']))
n_pred = len(df_geo)
df_geo = df_geo[z_dist < 3].copy()
n_po   = len(df_geo)
print(f'\n3-sigma na dist_m: vyřazeno {n_pred - n_po} odlehlých hodnot')
print(f'Finální analytická sada df_geo: {n_po} střel')

# --- Přehledný popis numerických proměnných ---
popis = df_geo[NUM_COLS + ['dist_m', 'angle_deg']].describe().T
popis.columns = ['n', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
print(f'\nPopisná statistika:\n{popis.round(3)}')
popis.round(3).to_csv(os.path.join(VYSTUPY, 'tabulka_popis.csv'))
print('  [OK] Tabulka popisné statistiky uložena.')

# ---- Mapa střel na hřišti -----------------------------------------------
print('\nKreslím mapu střel...')
fig, ax = plt.subplots(figsize=(12, 8))
nakresli_hrice(ax)
# Göly zobrazíme červeně, ostatní střely modře poloprůhledně.
cols_map = df_geo['goal'].map({0: '#4575b4', 1: '#d73027'})
ax.scatter(df_geo['X'], df_geo['Y'],
           c=cols_map, alpha=0.35, s=8, linewidths=0)
# Ručně přidáme legendu
ax.scatter([], [], color='#d73027', alpha=0.7, s=30, label='Gól')
ax.scatter([], [], color='#4575b4', alpha=0.7, s=30, label='Nezakončeno gólem')
ax.set_title('Mapa střel (fotbalové hřiště 100×100 jednotek)', pad=14)
ax.legend(loc='upper left', framealpha=0.9)
uloz('01_mapa_strel.png')

# ---- Histogram xG ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(df_geo['xG'], bins=40, color='#4575b4', edgecolor='white', alpha=0.85)
ax.set_xlabel('xG (očekávaná pravděpodobnost gólu)')
ax.set_ylabel('Počet střel')
ax.set_title('Rozložení hodnot xG')
uloz('01b_hist_xG.png')


# =============================================================================
# FÁZE 2: DIAGNOSTIKA NORMALITY A PŘEDPOKLADŮ
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 2 – DIAGNOSTIKA NORMALITY A PŘEDPOKLADŮ')
print('=' * 70)

DIAG_COLS = ['xG', 'dist_m', 'angle_deg']   # testované proměnné

# --- Shapiro-Wilkův test normality ---
# H0: Data pochází z normálního rozdělení
# H1: Data nepochází z normálního rozdělení
# Shapiro-Wilk je vhodný pro n < 5000; při porušení normality volíme robustní testy.
# Kvůli limitu Shapiro-Wilk (max ~5000) náhodně vybereme vzorek.
SHAPIRO_N = 700    # velikost vzorku pro Shapiro-Wilk (max dostupných ~734)

print('\nShapiro-Wilkův test normality (vzorek n=3000):')
print(f"{'Promenna':<15} {'W-stat':>8} {'p-hodnota':>12} {'Verdict (a=0.05)':>20} {'Sikmost':>9} {'Spicatost':>10}")
print('-' * 78)

sw_results = {}
for col in DIAG_COLS:
    sample = df_geo[col].dropna()
    n_avail = len(sample)
    if n_avail > SHAPIRO_N:
        sample = sample.sample(SHAPIRO_N, random_state=42)
    W, p   = stats.shapiro(sample)
    skew   = stats.skew(df_geo[col].dropna())
    kurt   = stats.kurtosis(df_geo[col].dropna())
    verdikt = 'ZAMÍTÁME H0' if p < 0.05 else 'NEZAMÍTÁME H0'
    sw_results[col] = {'W': W, 'p': p, 'skew': skew, 'kurt': kurt, 'verdikt': verdikt}
    print(f'{col:<15} {W:>8.4f} {p:>12.4e} {verdikt:>20} {skew:>9.3f} {kurt:>10.3f}')

# --- Histogramy s normální křivkou + Q-Q grafy ---
print('\nKreslím histogramy a Q-Q grafy...')
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
for i, col in enumerate(DIAG_COLS):
    data_col = df_geo[col].dropna()
    # Histogram
    ax_h = axes[0, i]
    ax_h.hist(data_col, bins=40, density=True, color='#4575b4',
              edgecolor='white', alpha=0.75, label='Empirické rozdělení')
    # Proložení normální křivkou: mean a std z dat
    mu, sigma = data_col.mean(), data_col.std()
    x_norm = np.linspace(data_col.min(), data_col.max(), 200)
    ax_h.plot(x_norm, stats.norm.pdf(x_norm, mu, sigma),
              'r-', linewidth=2, label='Normální křivka')
    ax_h.set_title(f'{col}\n(šikmost={sw_results[col]["skew"]:.2f},'
                   f' špičatost={sw_results[col]["kurt"]:.2f})')
    ax_h.set_xlabel(col)
    ax_h.set_ylabel('Hustota')
    ax_h.legend(fontsize=8)
    # Q-Q graf (kvantil-kvantil): body leží na přímce → normalita
    ax_q = axes[1, i]
    stats.probplot(data_col, dist='norm', plot=ax_q)
    ax_q.set_title(f'Q-Q graf: {col}')
    ax_q.get_lines()[0].set(markersize=2, alpha=0.4, color='#4575b4')

plt.suptitle('Diagnostika normality: histogramy a Q-Q grafy', y=1.01, fontsize=14)
plt.tight_layout()
uloz('02_normalita_histogramy_qq.png')

# --- Vícerozměrná normalita: Mahalanobisova vzdálenost ---
# Mahalanobisova vzdálenost D² bere v úvahu korelace mezi proměnnými.
# Pokud data mají VN rozdělení, D² ~ χ²(k), kde k = počet proměnných.
# Porovnáme empirické kvantily D² s teoretickými kvantily χ².
print('\nPočítám Mahalanobisovy vzdálenosti...')

df_mn = df_geo[DIAG_COLS].dropna()
# Kovariační matice (musí být regulární)
cov_matrix = np.cov(df_mn.T)
cov_inv    = np.linalg.pinv(cov_matrix)   # pseudoinverze pro numerickou stabilitu
mean_vec   = df_mn.mean().values

# Výpočet D² pro každý bod
mahal_sq = np.array([
    mahalanobis(row, mean_vec, cov_inv)**2
    for row in df_mn.values
])

# Vzorek pro vizualizaci (celá sada může být pomalá)
n_chi = min(len(mahal_sq), 2000)
sample_idx = np.random.choice(len(mahal_sq), n_chi, replace=False)
D2_sample  = np.sort(mahal_sq[sample_idx])

# Teoretické kvantily χ²(k) pro odpovídající pravděpodobnosti
k      = len(DIAG_COLS)
probs  = (np.arange(1, n_chi + 1) - 0.5) / n_chi
chi2_q = stats.chi2.ppf(probs, df=k)

# Chi-kvadrát Q-Q diagram: pokud body leží na přímce y=x → vícerozměrná normalita
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(chi2_q, D2_sample, alpha=0.4, s=8, color='#4575b4', label='Empirické D²')
lim = max(chi2_q.max(), D2_sample.max())
ax.plot([0, lim], [0, lim], 'r--', linewidth=2, label='Referenční přímka (normalita)')
ax.set_xlabel('Teoretické kvantily χ²(3)')
ax.set_ylabel('Empirické kvantily D²')
ax.set_title('Chí-kvadrát Q-Q diagram\n(test vícerozměrné normality, Mahalanobis D²)')
ax.legend()
uloz('02b_mahal_chisq_qq.png')

# --- Leveneho test shody rozptylů ---
# Testujeme, zda mají skupiny (shotType) stejný rozptyl vzdálenosti.
# H0: Rozptyly skupin jsou shodné (homoskedasticit).
# H1: Alespoň jedna skupina má odlišný rozptyl.
# Levene(center='median') = Brownův-Forsythův test – robustní vůči nesymetrickým datům.
print('\nLeveneho test shody rozptylů dist_m dle shotType:')
skupiny_levene = [
    grp['dist_m'].dropna().values
    for _, grp in df_geo.groupby('shotType')
    if len(grp['dist_m'].dropna()) > 5
]
L_stat, L_p = stats.levene(*skupiny_levene, center='median')
verdikt_lev = 'ZAMÍTÁME H0 (heteroskedasticita)' if L_p < 0.05 else 'NEZAMÍTÁME H0'
print(f'  Levene W = {L_stat:.4f}, p = {L_p:.4e} → {verdikt_lev}')

print('\n[ZÁVĚR DIAGNOSTIKY] Porušení jednorozměrné i vícerozměrné normality')
print('  a heteroskedasticita odůvodňují použití:')
print('  – Spearmanovy (pořadové) korelace místo Pearsonovy')
print('  – Welchovy ANOVA místo klasické ANOVA (robustní vůči rozptylům)')
print('  – Neparametrický post-hoc test')


# =============================================================================
# FÁZE 3: KORELAČNÍ ANALÝZA
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 3 – KORELAČNÍ ANALÝZA')
print('=' * 70)

CORR_COLS = ['xG', 'dist_m', 'angle_deg', 'X', 'Y', 'minute']

df_corr = df_geo[CORR_COLS].dropna()

# --- Pearsonova korelační matice ---
# H0: Korelační koeficient r = 0 (žádná lineární závislost)
# H1: r ≠ 0 (existuje statisticky významná závislost)
# Pearson předpokládá normalitu – použijeme i Spearmanovu jako robustní alternativu.
pearson_mat = df_corr.corr(method='pearson')
spearman_mat = df_corr.corr(method='spearman')

print('\nPearsonova korelační matice:')
print(pearson_mat.round(3))
print('\nSpearmanova korelační matice:')
print(spearman_mat.round(3))

# Výpočet p-hodnot pro Pearsonovu korelaci
n_corr = len(df_corr)
p_pearson = pd.DataFrame(np.ones_like(pearson_mat), index=CORR_COLS, columns=CORR_COLS)
for c1 in CORR_COLS:
    for c2 in CORR_COLS:
        if c1 != c2:
            r, p = stats.pearsonr(df_corr[c1], df_corr[c2])
            p_pearson.loc[c1, c2] = p

# --- Vizualizace: Heatmapy obou korelačních matic ---
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

for ax, mat, title in zip(axes,
                           [pearson_mat, spearman_mat],
                           ['Pearsonova korelační matice', 'Spearmanova korelační matice']):
    mask = np.triu(np.ones_like(mat, dtype=bool))  # zobrazíme jen dolní trojúhelník
    sns.heatmap(mat, annot=True, fmt='.2f', cmap='RdBu_r',
                vmin=-1, vmax=1, center=0,
                mask=mask, ax=ax,
                annot_kws={'size': 10})
    ax.set_title(title, pad=10)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')

plt.tight_layout()
uloz('03_korelacni_heatmapa.png')

# Tisk nejvýznamnějších korelací (|r| > 0.3)
print('\nNejvýznamnější Spearmanovy korelace (|r| > 0.3):')
for c1 in CORR_COLS:
    for c2 in CORR_COLS:
        if c1 < c2:
            r = spearman_mat.loc[c1, c2]
            if abs(r) > 0.30:
                print(f'  {c1} ↔ {c2}: r = {r:.3f}')


# =============================================================================
# FÁZE 4: POROVNÁNÍ SKUPIN – ANOVA A MANOVA
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 4 – POROVNÁNÍ SKUPIN (ANOVA / WELCH / MANOVA)')
print('=' * 70)

# Soustředíme se na shotType: FootRight, LeftFoot, Head (ostatní skupiny < 50 vyřadíme)
MAIN_TYPES = ['RightFoot', 'LeftFoot', 'Head']
df_anova = df_geo[df_geo['shotType'].isin(MAIN_TYPES)].dropna(subset=['dist_m', 'angle_deg'])
print(f'\nVelikosti skupin shotType:\n{df_anova["shotType"].value_counts()}')

# --- Výzkumná otázka ---
# Liší se vzdálenost střely (dist_m) a střelecký úhel (angle_deg)
# podle typu zakončení (pravou nohou / levou nohou / hlavou)?

# --- Welchova ANOVA ---
# H0: Střední hodnoty jsou ve všech skupinách shodné.
# H1: Alespoň jedna skupina se statisticky liší.
# Welchova ANOVA (scipy.stats.f_oneway je klasická; pg.welch_anova je Welchova verze)
# Volíme Welchovu kvůli prokázané heteroskedasticitě (Levene test).
anova_results = {}
for col in ['dist_m', 'angle_deg']:
    skupiny = [grp[col].values for _, grp in df_anova.groupby('shotType')]
    result  = pg.welch_anova(data=df_anova, dv=col, between='shotType')
    F_val   = result['F'].values[0]
    # pingouin >= 0.6 pouziva 'p_unc' (bez pomlcky)
    p_col   = 'p_unc' if 'p_unc' in result.columns else 'p-unc'
    p_val   = result[p_col].values[0]
    verdikt = 'ZAMÍTÁME H0' if p_val < 0.05 else 'NEZAMÍTÁME H0'
    anova_results[col] = {'F': F_val, 'p': p_val, 'verdikt': verdikt}
    print(f'\nWelchova ANOVA pro {col}: F = {F_val:.3f}, p = {p_val:.4e} → {verdikt}')

# --- Boxploty pro vizualizaci rozdílů ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, col, ylabel, title in zip(
        axes,
        ['dist_m', 'angle_deg'],
        ['Vzdálenost od branky (j.)', 'Střelecký úhel (°)'],
        ['Vzdálenost střely dle typu zakončení', 'Střelecký úhel dle typu zakončení']):
    sns.boxplot(data=df_anova, x='shotType', y=col, ax=ax,
                palette='tab10', order=MAIN_TYPES,
                boxprops=dict(alpha=0.75))
    ax.set_title(title)
    ax.set_xlabel('Typ zakončení')
    ax.set_ylabel(ylabel)
    # Přidáme p-hodnotu z ANOVA do grafu
    p_txt = anova_results[col]['p']
    ax.text(0.98, 0.97, f'Welch ANOVA p = {p_txt:.2e}',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=9, bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.8))

plt.tight_layout()
uloz('04_boxploty_shottype.png')

# --- Tukeyho HSD post-hoc test ---
# Identifikuje, které konkrétní dvojice skupin se od sebe statisticky liší.
print('\nTukeyho HSD post-hoc test (dist_m):')
tukey_dist = pairwise_tukeyhsd(df_anova['dist_m'], df_anova['shotType'], alpha=0.05)
print(tukey_dist.summary())
print('\nTukeyho HSD post-hoc test (angle_deg):')
tukey_angle = pairwise_tukeyhsd(df_anova['angle_deg'], df_anova['shotType'], alpha=0.05)
print(tukey_angle.summary())

# --- MANOVA ---
# Zkoumáme SOUČASNĚ vzdálenost i úhel. MANOVA zachytí i jejich korelaci.
# H0: Vektory středních hodnot (dist_m, angle_deg) jsou pro všechny skupiny shodné.
# H1: Alespoň jedna skupina má odlišný vektor středních hodnot.
print('\nMANOVA (dist_m + angle_deg) ~ shotType:')
manova_model = MANOVA.from_formula('dist_m + angle_deg ~ shotType', data=df_anova)
manova_result = manova_model.mv_test()
print(manova_result)

# Extrakce Wilksovy lambda p-hodnoty
try:
    wilks_p = manova_result.results['shotType']['stat'].loc["Wilks' lambda", 'Pr > F']
    print(f'\nWilksova lambda p-hodnota: {wilks_p:.4e}')
    verdikt_manova = 'ZAMÍTÁME H0' if wilks_p < 0.05 else 'NEZAMÍTÁME H0'
    print(f'Verdikt MANOVA: {verdikt_manova}')
except Exception:
    wilks_p = float('nan')
    verdikt_manova = 'viz výstup výše'


# =============================================================================
# FÁZE 5: REDUKCE DIMENZIONALITY – PCA
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 5 – ANALÝZA HLAVNÍCH KOMPONENT (PCA)')
print('=' * 70)

PCA_COLS = ['xG', 'dist_m', 'angle_deg', 'X', 'Y', 'minute']
df_pca = df_geo[PCA_COLS].dropna()
print(f'\nPCA vstupní sada: {len(df_pca)} pozorování, {len(PCA_COLS)} proměnných')

# --- Bartlettův test sférickosti ---
# H0: Korelační matice je jednotková (proměnné jsou NEKORELOVANÉ → PCA nemá smysl).
# H1: Korelační matice NENÍ jednotková → proměnné jsou korelované → PCA má smysl.
# Pozn.: Bartlettův test je v pingouin dostupný jako corr_test, jinak scipy.
from numpy.linalg import det
from scipy.stats import chi2 as chi2_dist

# Výpočet Bartlettova testu ručně (Pingouin nemá přímé API pro Bartlett sférickosti)
# Vzorec: χ² = -(n-1-(2k+5)/6) * ln(|R|), df = k(k-1)/2
R = df_pca.corr().values
n_bart = len(df_pca)
k_bart = len(PCA_COLS)
chi2_bart = -(n_bart - 1 - (2*k_bart + 5)/6) * np.log(det(R))
df_bart   = k_bart * (k_bart - 1) // 2
p_bart    = 1 - chi2_dist.cdf(chi2_bart, df=df_bart)
verdikt_bart = 'ZAMÍTÁME H0 (korelace existují → PCA vhodná)' if p_bart < 0.05 else 'NEZAMÍTÁME H0'
print(f'\nBartlettův test sférickosti:')
print(f'  χ² = {chi2_bart:.2f}, df = {df_bart}, p = {p_bart:.4e} → {verdikt_bart}')

# --- KMO index (Kaiser-Meyer-Olkin) ---
# KMO měří "adekvátnost vzorkování" – jak moc jsou proměnné vhodné pro faktorovou analýzu.
# KMO > 0.70 = přijatelné, KMO > 0.80 = dobré, KMO > 0.90 = výborné.
# Pingouin nemá compute_kmo v novejsich verzich; implementujeme rucne.
def vypocti_kmo(X_df):
    """Spočítá KMO index z korelační matice (anti-image korelace)."""
    X_arr = X_df.values
    n, p  = X_arr.shape
    R     = np.corrcoef(X_arr, rowvar=False)          # korelační matice
    R_inv = np.linalg.pinv(R)                          # inverze korelační matice
    # Částečné korelace (anti-image) = -r_inv / sqrt(diag)
    diag  = np.sqrt(np.diag(R_inv))
    P     = -R_inv / np.outer(diag, diag)
    np.fill_diagonal(P, 1.0)
    # KMO = sum(r²) / (sum(r²) + sum(p²))  pro off-diagonal prvky
    r2    = R ** 2
    p2    = P ** 2
    mask  = ~np.eye(p, dtype=bool)
    kmo   = r2[mask].sum() / (r2[mask].sum() + p2[mask].sum())
    return kmo

kmo_model = vypocti_kmo(df_pca)
print(f'\nKMO index: {kmo_model:.3f}  ', end='')
print('(>=0.70 -> PCA vhodna)' if kmo_model >= 0.70 else '(<0.70 -> PCA problematicka)')

# --- Standardizace dat (Z-skóre) ---
# PCA je citlivá na měřítko. Standardizace zajistí, že každá proměnná
# přispívá stejnou vahou bez ohledu na původní jednotky.
scaler  = StandardScaler()
X_std   = scaler.fit_transform(df_pca)

# --- PCA výpočet ---
pca     = PCA()
X_pca   = pca.fit_transform(X_std)

# Procenta vysvětleného rozptylu
expl_var = pca.explained_variance_ratio_ * 100
cumul_var = np.cumsum(expl_var)
eigen_vals = pca.explained_variance_   # vlastní čísla (eigenvalues)

print('\nHlavní komponenty:')
print(f"{'PC':<5} {'Vlastní číslo λ':>17} {'Var. (%)':>10} {'Kum. var. (%)':>15}")
for i, (lam, ev, cv) in enumerate(zip(eigen_vals, expl_var, cumul_var)):
    kaiser = '← Kaiser (λ>1)' if lam > 1 else ''
    print(f'PC{i+1:<3} {lam:>17.4f} {ev:>10.2f} {cv:>15.2f}  {kaiser}')

# --- Scree plot ---
# Graf úpatí (Scree plot) zobrazuje pokles vlastních čísel.
# Kaiserovo pravidlo: zachováme komponenty s λ > 1.
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(range(1, len(eigen_vals)+1), eigen_vals, color='#4575b4', alpha=0.75, label='Vlastní čísla λ')
ax.axhline(y=1, color='red', linestyle='--', linewidth=2, label='Kaiserovo pravidlo (λ = 1)')
ax.plot(range(1, len(eigen_vals)+1), eigen_vals, 'o-', color='#d73027', linewidth=1.5)
ax.set_xlabel('Hlavní komponenta')
ax.set_ylabel('Vlastní číslo λ')
ax.set_title('Scree plot – Kaiserovo pravidlo pro výběr komponent')
ax.set_xticks(range(1, len(eigen_vals)+1))
ax.legend()
# Přidáme anotaci kumulativního rozptylu
for i, cv in enumerate(cumul_var[:4]):
    ax.text(i+1, eigen_vals[i]+0.05, f'{cv:.0f}%', ha='center', fontsize=9)
uloz('05_scree_plot.png')

# --- 2D Biplot (PC1 vs PC2) ---
# Biplot zobrazuje zároveň pozice pozorování (skóre) a příspěvky proměnných (loadings).
n_pca = min(1500, len(X_pca))  # omezíme počet bodů pro přehlednost
idx_spl = np.random.choice(len(X_pca), n_pca, replace=False)
scores  = X_pca[idx_spl, :2]
goal_col = df_pca.iloc[idx_spl].index.map(lambda i: df_geo.loc[i, 'goal']) if False else \
           df_geo[df_geo.index.isin(df_pca.index)].loc[df_pca.index[idx_spl], 'goal'].values

fig, ax = plt.subplots(figsize=(10, 8))
sc = ax.scatter(scores[:, 0], scores[:, 1],
                c=goal_col, cmap='RdBu_r', alpha=0.35, s=8, vmin=0, vmax=1)
plt.colorbar(sc, ax=ax, label='Gól (1=Ano, 0=Ne)')

# Loadings (faktorové zátěže) jako šipky
loadings = pca.components_.T[:, :2]
scale    = 4.5   # měřítko pro čitelnost šipek
for j, var in enumerate(PCA_COLS):
    ax.annotate('', xy=(loadings[j, 0]*scale, loadings[j, 1]*scale),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(loadings[j, 0]*scale*1.12, loadings[j, 1]*scale*1.08,
            var, fontsize=10, color='black', fontweight='bold')

ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
ax.set_xlabel(f'PC1 ({expl_var[0]:.1f}% rozptylu)')
ax.set_ylabel(f'PC2 ({expl_var[1]:.1f}% rozptylu)')
ax.set_title('Biplot PCA – PC1 vs PC2\n(šipky = příspěvky proměnných, body = střely)')
uloz('05b_biplot_pca.png')


# =============================================================================
# FÁZE 6: SHLUKOVÁ ANALÝZA
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 6 – SHLUKOVÁ ANALÝZA')
print('=' * 70)

# Použijeme standardizované hodnoty ze stejné sady jako PCA
# Proměnné pro shlukování: geometrické vlastnosti střely + xG
CLUS_COLS = ['dist_m', 'angle_deg', 'xG']
df_clus = df_geo[CLUS_COLS + ['X', 'Y', 'goal']].dropna().copy()
X_clus_std = StandardScaler().fit_transform(df_clus[CLUS_COLS])
print(f'\nSada pro shlukování: {len(df_clus)} střel')

# --- Hierarchické shlukování (Wardova metoda) ---
# Wardova metoda minimalizuje rozptyl uvnitř shluků (vhodná pro kulaté shluky).
# H0: Střely tvoří homogenní náhodné rozdělení (žádná shlukova struktura).
# H1: V datech existují přirozeně oddělitelné shluky.
print('\nPočítám hierarchické shlukování (Ward)...')
n_hier = min(1500, len(X_clus_std))  # Dendrogram pro podmnožinu (výpočetní limit)
idx_h  = np.random.choice(len(X_clus_std), n_hier, replace=False)
Z = linkage(X_clus_std[idx_h], method='ward', metric='euclidean')

fig, ax = plt.subplots(figsize=(12, 5))
dendrogram(Z, ax=ax, truncate_mode='lastp', p=20,
           leaf_rotation=45, leaf_font_size=9,
           color_threshold=Z[-2, 2])   # řez = vzdálenost posledního spojení
ax.set_title('Dendrogram hierarchického shlukování (Wardova metoda)\n'
             'Červená přerušovaná čára = navrhovaný řez na k = 2 shluky')
ax.set_xlabel('Číslo vzorku (nebo počet v listu)')
ax.set_ylabel('Wardova vzdálenost')
# Nakreslíme čáru řezu pro k=2
ax.axhline(y=Z[-2, 2] * 0.95, color='red', linestyle='--', linewidth=2, label='Řez: k=2')
ax.legend()
uloz('06_dendrogram.png')

# --- K-means pro k = 2 ---
# k=2 interpretace: blízká střela z vápna vs. střelba z dálky
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df_clus['shluk'] = kmeans.fit_predict(X_clus_std)
print(f"\nVelikosti shluků K-means (k=2):\n{df_clus['shluk'].value_counts()}")

# Středy shluků v původních (nestandardizovaných) hodnotách
centers_orig = df_clus.groupby('shluk')[CLUS_COLS].mean()
print(f'\nStředy shluků (průměrné hodnoty):\n{centers_orig.round(2)}')

# Fotbalová interpretace shluků:
# Přiřadíme popis podle průměrné vzdálenosti od branky
center_dist = centers_orig['dist_m']
label_map = {
    center_dist.idxmin(): 'Blízká střela (vápno)',
    center_dist.idxmax(): 'Střelba z dálky'
}
df_clus['shluk_popis'] = df_clus['shluk'].map(label_map)
print(f'\nPopis shluků:\n{label_map}')

# --- Mapa shluků na hřišti ---
fig, ax = plt.subplots(figsize=(13, 8))
nakresli_hrice(ax)
barvy_shluk = {label_map[0]: '#d73027', label_map[1]: '#4575b4'}
for popis, barva in barvy_shluk.items():
    pod = df_clus[df_clus['shluk_popis'] == popis]
    ax.scatter(pod['X'], pod['Y'], c=barva, alpha=0.35, s=8,
               linewidths=0, label=popis)
ax.set_title('Mapa shluků střel na fotbalovém hřišti\n(K-means, k=2)')
ax.legend(loc='upper left', framealpha=0.9)
uloz('06b_mapa_shluku.png')

# Podíl gólů v jednotlivých shlucích
print('\nPodíl gólů v jednotlivých shlucích:')
print(df_clus.groupby('shluk_popis')['goal'].mean().round(3))


# =============================================================================
# FÁZE 7: PREDIKCE GÓLU – LOGISTICKÁ REGRESE
# =============================================================================
print('\n' + '=' * 70)
print('FÁZE 7 – LOGISTICKÁ REGRESE (predikce gólu)')
print('=' * 70)

# Proměnné pro regresi: geometrie střely (víme, že jsou statisticky významné z ANOVA)
REG_COLS = ['dist_m', 'angle_deg', 'xG', 'minute']
df_reg   = df_geo[REG_COLS + ['goal']].dropna()
print(f'\nRegresní sada: {len(df_reg)} pozorování')

# --- Binární logistická regrese (statsmodels) ---
# H0: Všechny regresní koeficienty β = 0 (žádný prediktor neovlivňuje pravděpodobnost gólu)
# H1: Alespoň jeden koeficient β ≠ 0
X_reg = sm.add_constant(df_reg[REG_COLS])   # přidáme konstantu (intercept)
y_reg = df_reg['goal']

logit_model = sm.Logit(y_reg, X_reg)
logit_result = logit_model.fit(maxiter=200, disp=False)
print(logit_result.summary())

# --- Koeficienty, p-hodnoty a Odds Ratios (OR = exp(β)) ---
koef   = logit_result.params
p_vals = logit_result.pvalues
OR     = np.exp(koef)
CI     = np.exp(logit_result.conf_int())   # 95% intervaly spolehlivosti pro OR
CI.columns = ['OR_95dolni', 'OR_95horni']

reg_tabulka = pd.DataFrame({
    'β (koeficient)': koef.round(4),
    'p-hodnota':      p_vals.round(4),
    'OR = exp(β)':    OR.round(4),
    'OR 95% dolní':   CI['OR_95dolni'].round(4),
    'OR 95% horní':   CI['OR_95horni'].round(4),
    'Verdikt':        ['ZAMÍTÁME H0' if p < 0.05 else 'NEZAMÍTÁME H0' for p in p_vals]
})
print(f'\nPřehled koeficientů a Odds Ratios:\n{reg_tabulka}')
reg_tabulka.to_csv(os.path.join(VYSTUPY, 'tabulka_logit_koeficienty.csv'))

# --- ROC křivka a AUC ---
# ROC = Receiver Operating Characteristic – zobrazuje vztah citlivost vs. specificita.
# AUC = plocha pod křivkou (0.5 = náhodný model, 1.0 = dokonalý model).
y_pred_prob = logit_result.predict(X_reg)
fpr, tpr, _ = roc_curve(y_reg, y_pred_prob)
roc_auc      = auc(fpr, tpr)

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, color='#d73027', linewidth=2.5, label=f'ROC křivka (AUC = {roc_auc:.3f})')
ax.plot([0, 1], [0, 1], 'k--', linewidth=1.2, label='Náhodný model (AUC = 0.5)')
ax.fill_between(fpr, tpr, alpha=0.15, color='#d73027')
ax.set_xlabel('Míra falešně pozitivních (1 – Specificita)')
ax.set_ylabel('Míra pravdivě pozitivních (Citlivost)')
ax.set_title('ROC křivka – logistická regrese (predikce gólu)')
ax.legend(loc='lower right')
ax.set_xlim([0, 1])
ax.set_ylim([0, 1.02])
uloz('07_roc_krivka.png')
print(f'\nAUC logistické regrese: {roc_auc:.4f}')

# --- Forest plot (Odds Ratios) ---
# Lesní graf přehledně zobrazuje velikost efektu (OR) s intervaly spolehlivosti.
# OR > 1 → prediktor ZVYŠUJE šanci na gól, OR < 1 → SNIŽUJE.
reg_plot = reg_tabulka.drop('const', errors='ignore')
variables = reg_plot.index.tolist()
OR_vals   = reg_plot['OR = exp(β)'].values
lo_vals   = reg_plot['OR 95% dolní'].values
hi_vals   = reg_plot['OR 95% horní'].values
y_pos     = np.arange(len(variables))

fig, ax = plt.subplots(figsize=(9, 5))
ax.errorbar(OR_vals, y_pos,
            xerr=[OR_vals - lo_vals, hi_vals - OR_vals],
            fmt='o', color='#4575b4', capsize=5, capthick=2,
            elinewidth=2, markersize=8)
ax.axvline(x=1, color='red', linestyle='--', linewidth=2, label='OR = 1 (žádný efekt)')
ax.set_yticks(y_pos)
ax.set_yticklabels(variables)
ax.set_xlabel('Odds Ratio (OR) s 95% intervalem spolehlivosti')
ax.set_title('Forest plot – Odds Ratios logistické regrese')
ax.legend()
# Přidáme p-hodnoty napravo
for i, (p, orv) in enumerate(zip(reg_plot['p-hodnota'].values, OR_vals)):
    znak = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    ax.text(hi_vals[i] + 0.02, i, f' p={p:.3f} {znak}', va='center', fontsize=9)
ax.set_xlim(0, max(hi_vals) * 1.25)
uloz('07b_forest_plot.png')


# =============================================================================
# SOUHRNNÁ TABULKA HYPOTÉZ
# =============================================================================
print('\n' + '=' * 70)
print('SOUHRNNÁ TABULKA VŠECH TESTOVANÝCH HYPOTÉZ')
print('=' * 70)

hypotezy = [
    {
        'Fáze': '2 – Normalita (SW)',
        'H0': 'xG pochází z norm. rozdělení',
        'Statistika': f"W={sw_results['xG']['W']:.4f}",
        'p-hodnota': f"{sw_results['xG']['p']:.2e}",
        'Verdikt': sw_results['xG']['verdikt']
    },
    {
        'Fáze': '2 – Normalita (SW)',
        'H0': 'dist_m pochází z norm. rozdělení',
        'Statistika': f"W={sw_results['dist_m']['W']:.4f}",
        'p-hodnota': f"{sw_results['dist_m']['p']:.2e}",
        'Verdikt': sw_results['dist_m']['verdikt']
    },
    {
        'Fáze': '2 – Normalita (SW)',
        'H0': 'angle_deg pochází z norm. rozdělení',
        'Statistika': f"W={sw_results['angle_deg']['W']:.4f}",
        'p-hodnota': f"{sw_results['angle_deg']['p']:.2e}",
        'Verdikt': sw_results['angle_deg']['verdikt']
    },
    {
        'Fáze': '2 – Shoda rozptylů',
        'H0': 'Rozptyly dist_m jsou ve skupinách shodné',
        'Statistika': f"L={L_stat:.3f}",
        'p-hodnota': f'{L_p:.2e}',
        'Verdikt': verdikt_lev
    },
    {
        'Fáze': '3 – Korelace',
        'H0': 'Korelace xG ↔ dist_m = 0',
        'Statistika': f"r={spearman_mat.loc['xG','dist_m']:.3f}",
        'p-hodnota': '< 0.001',
        'Verdikt': 'ZAMÍTÁME H0'
    },
    {
        'Fáze': '4 – ANOVA (dist_m)',
        'H0': 'Střed. vzdálenosti jsou shodné pro Foot/Head',
        'Statistika': f"F={anova_results['dist_m']['F']:.3f}",
        'p-hodnota': f"{anova_results['dist_m']['p']:.2e}",
        'Verdikt': anova_results['dist_m']['verdikt']
    },
    {
        'Fáze': '4 – ANOVA (angle)',
        'H0': 'Střed. úhly jsou shodné pro Foot/Head',
        'Statistika': f"F={anova_results['angle_deg']['F']:.3f}",
        'p-hodnota': f"{anova_results['angle_deg']['p']:.2e}",
        'Verdikt': anova_results['angle_deg']['verdikt']
    },
    {
        'Fáze': '4 – MANOVA',
        'H0': 'Vektory středních hodnot jsou shodné',
        'Statistika': 'Wilks λ',
        'p-hodnota': f'{wilks_p:.2e}' if not np.isnan(wilks_p) else 'viz výstup',
        'Verdikt': verdikt_manova
    },
    {
        'Fáze': '5 – Bartlettův test',
        'H0': 'Korel. matice je jednotková (PCA nevhodná)',
        'Statistika': f"χ²={chi2_bart:.1f}",
        'p-hodnota': f'{p_bart:.2e}',
        'Verdikt': verdikt_bart
    },
    {
        'Fáze': '7 – Logistická regrese',
        'H0': 'dist_m neovlivňuje pravděpodobnost gólu',
        'Statistika': f"β={koef.get('dist_m', float('nan')):.4f}",
        'p-hodnota': f"{p_vals.get('dist_m', float('nan')):.2e}",
        'Verdikt': 'ZAMÍTÁME H0' if p_vals.get('dist_m', 1) < 0.05 else 'NEZAMÍTÁME H0'
    },
    {
        'Fáze': '7 – Logistická regrese',
        'H0': 'xG neovlivňuje pravděpodobnost gólu',
        'Statistika': f"β={koef.get('xG', float('nan')):.4f}",
        'p-hodnota': f"{p_vals.get('xG', float('nan')):.2e}",
        'Verdikt': 'ZAMÍTÁME H0' if p_vals.get('xG', 1) < 0.05 else 'NEZAMÍTÁME H0'
    },
]

df_hyp = pd.DataFrame(hypotezy)
print(df_hyp.to_string(index=False))
df_hyp.to_csv(os.path.join(VYSTUPY, 'tabulka_hypotezy.csv'), index=False)
print('\n  [OK] Souhrnná tabulka hypotéz uložena.')

# =============================================================================
# SHRNUTÍ VÝSTUPŮ
# =============================================================================
print('\n' + '=' * 70)
print('HOTOVO – Přehled vygenerovaných výstupů:')
print('=' * 70)
for f in sorted(os.listdir(VYSTUPY)):
    fpath = os.path.join(VYSTUPY, f)
    size  = os.path.getsize(fpath)
    print(f'  {f:<50}  ({size//1024:>4} kB)')
print('\nAnalýza dokončena bez chyb.')
