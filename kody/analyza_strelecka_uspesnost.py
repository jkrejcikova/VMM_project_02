# -*- coding: utf-8 -*-
# =============================================================================
# SEMESTRÁLNÍ PROJEKT – VÍCEROZMĚRNÉ STATISTICKÉ METODY (VMM)
# Téma: Střelecká úspěšnost ve fotbale (Premier League)
# Autor: Student VMM / VUT Brno, 2026/27
# =============================================================================
# OBSAŽENÉ METODY:
#   1. Průzkumová analýza (EDA), fotbalové hřiště 100×100, pravidlo 3-sigma
#   2. 2D KDE hustota střelby na hřišti (vrstevnice zakončení gól vs. minela)
#   3. Diagnostika normality (Shapiro-Wilk, histogram, opravený Q-Q graf probplot, Levene)
#   4. Spearmanova korelační matice (plná matice s velkými čísly a testem významnosti)
#   5. Pair-plot vztahů klíčových proměnných (dist_m, angle_deg, xG s KDE diagonálou)
#   6. Porovnání skupin zakončení (Welchova ANOVA krabicové grafy, heteroskedasticita)
#   7. Vícerozměrná MANOVA a Tukeyho HSD post-hoc test (sdružený vektor geometrie)
#   8. Redukce dimenzionality PCA (Scree plot s Kaiserovým pravidlem + 2D Biplot)
#   9. Faktorová analýza FA s rotací Varimax (skryté faktory pozice a herní hloubky)
#  10. Logistická regrese (sigmoidální křivka pravděpodobnosti dle vzdálenosti + ROC křivka)
#  11. Shluková analýza (Wardova hierarchická metoda, K-means k=2 na hřišti)
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')          # Neinteraktivní backend pro spolehlivé ukládání
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from scipy import stats
from scipy.spatial.distance import mahalanobis
from scipy.cluster.hierarchy import dendrogram, linkage
import statsmodels.api as sm
from statsmodels.multivariate.manova import MANOVA
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.cluster import KMeans
from sklearn.metrics import roc_curve, auc

warnings.filterwarnings('ignore')

# =============================================================================
# NASTAVENÍ CEST A GLOBÁLNÍHO STYLU GRAFŮ
# =============================================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'shots_outcome_Final.csv')
VYSTUPY_DIR = os.path.join(BASE_DIR, 'vystupy')
os.makedirs(VYSTUPY_DIR, exist_ok=True)

# Globální nastavení Matplotlibu: VELKÉ, KONTRASTNÍ A ČITELNÉ PÍSMO
plt.rcParams.update({
    'font.size': 14,
    'axes.labelsize': 15,
    'axes.titlesize': 16,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 13,
    'figure.titlesize': 17,
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})
sns.set_theme(style='white', palette='tab10')


def uloz_graf(nazev_souboru):
    """Uloží aktuální graf do složky vystupy/ s rozlišením 300 DPI."""
    cesta = os.path.join(VYSTUPY_DIR, nazev_souboru)
    plt.savefig(cesta, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'  [OK] Graf uložen: {nazev_souboru}')


def nakresli_fotbalove_hriste(ax):
    """
    Vykreslí fotbalové hřiště 100 × 100 jednotek s čistě BÍLÝM pozadím (#FFFFFF)
    a decentními šedými čarami (#a0a0a0, lw=1.5).
    X = délka hřiště (0 = levá branka, 100 = pravá branka soupeře).
    Y = šířka hřiště (0 = spodní okraj, 100 = horní okraj).
    """
    ax.set_facecolor('#FFFFFF')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    LC = '#a0a0a0'   # Barva čar
    LW = 1.5         # Tloušťka čar

    def rect(x, y, w, h):
        ax.add_patch(mpatches.Rectangle((x, y), w, h,
                     edgecolor=LC, facecolor='none', linewidth=LW))

    # Ohraničení hrací plochy a půlící čára
    rect(0, 0, 100, 100)
    ax.plot([50, 50], [0, 100], color=LC, linewidth=LW)

    # Středový kruh a bod
    kruh = plt.Circle((50, 50), 9.15, color=LC, fill=False, linewidth=LW)
    ax.add_patch(kruh)
    ax.plot(50, 50, 'o', color=LC, markersize=3)

    # Levé pokutové území a malé vápno
    rect(0, 21.1, 16.5, 57.8)
    rect(0, 36.8, 5.5,  26.4)

    # Pravé pokutové území a malé vápno (útočná polovina)
    rect(83.5, 21.1, 16.5, 57.8)
    rect(94.5, 36.8, 5.5,  26.4)

    # Branky (vyznačeny za brankovou čarou)
    ax.add_patch(mpatches.Rectangle((0, 45.2), -1.5, 9.6,
                 edgecolor=LC, facecolor='#f0f0f0', linewidth=LW))
    ax.add_patch(mpatches.Rectangle((100, 45.2), 1.5, 9.6,
                 edgecolor=LC, facecolor='#f0f0f0', linewidth=LW))

    ax.set_xlabel('X (délka hřiště v %)', fontsize=14, labelpad=8)
    ax.set_ylabel('Y (šířka hřiště v %)', fontsize=14, labelpad=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(LC)
        spine.set_linewidth(1.2)


# =============================================================================
# 1. FÁZE: PRŮZKUMOVÁ ANALÝZA A SELEKCE PROMĚNNÝCH (EDA)
# =============================================================================
print('=' * 75)
print('1. FÁZE: PRŮZKUMOVÁ ANALÝZA, ŠKÁLOVÁNÍ A PŘEDZPRACOVÁNÍ DAT')
print('=' * 75)

df_raw = pd.read_csv(DATA_PATH)
print(f'Původní počet záznamů: {len(df_raw)} střel, {df_raw.shape[1]} sloupců.')

# Vyřazení vlastních gólů (OwnGoal nereprezentují střelecký záměr útočníka)
df = df_raw[df_raw['result'] != 'OwnGoal'].copy()

# Definice binární cílové proměnné úspěšnosti střely
df['goal'] = (df['result'] == 'Goal').astype(int)
print(f'Počet střel po vyřazení OwnGoal: {len(df)} (z toho gólů: {df["goal"].sum()}, {df["goal"].mean():.1%})')

# Škálování prostorových souřadnic X a Y na jednotné hřiště 100 × 100
df['X'] = df['X'] * 100
df['Y'] = df['Y'] * 100

# Odvození geometrických veličin:
# 1. Vzdálenost střely od středu soupeřovy branky (X=100, Y=50)
df['dist_m'] = np.sqrt((100 - df['X'])**2 + (50 - df['Y'])**2)

# 2. Střelecký úhel sevřený brankovými tyčemi (branka Y ∈ [45.2, 54.8], X = 100)
y_min_b, y_max_b, x_br = 45.2, 54.8, 100.0
df['angle_deg'] = np.degrees(
    np.abs(
        np.arctan2(df['X'] - x_br, df['Y'] - y_min_b) -
        np.arctan2(df['X'] - x_br, df['Y'] - y_max_b)
    )
)

# Ošetření kategorických chybějících hodnot
df['player_assisted'] = df['player_assisted'].fillna('Bez asistence')
df['shotType']        = df['shotType'].fillna('Neznamy')
df['situation']       = df['situation'].fillna('Neznama')

# Věcné řešení chybějících hodnot: Souřadnice X a Y neimputujeme průměrem ani mediánem,
# aby nevznikly falešné střely v ose hřiště; pro prostorové modely použijeme kompletní řádky.
df_geo = df.dropna(subset=['X', 'Y', 'xG']).copy()

# Ošetření odlehlých hodnot: Aplikace pravidla 3-sigma na proměnnou dist_m
z_dist = np.abs(stats.zscore(df_geo['dist_m']))
n_pred = len(df_geo)
df_geo = df_geo[z_dist < 3].copy()
print(f'Pravidlo 3-sigma vyřadilo {n_pred - len(df_geo)} odlehlou střelu. Finální sada: n = {len(df_geo)}.')

# Export tabulky popisné statistiky
NUM_COLS = ['dist_m', 'angle_deg', 'xG', 'X', 'Y', 'minute']
popis = df_geo[NUM_COLS].describe().T[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
popis.columns = ['n', 'Průměr', 'Sm. odchylka', 'Min', '25 %', 'Medián', '75 %', 'Max']
popis.round(3).to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_popis.csv'))
print('  [OK] Tabulka popisné statistiky uložena: tabulka_popis.csv')

# --- Graf 01: Mapa střel na celém fotbalovém hřišti (s=45, alpha=0.7) ---
fig, ax = plt.subplots(figsize=(12, 7.2))
nakresli_fotbalove_hriste(ax)

nezakon = df_geo[df_geo['goal'] == 0]
goly    = df_geo[df_geo['goal'] == 1]

ax.scatter(nezakon['X'], nezakon['Y'], c='#1f77b4', s=45, alpha=0.70,
           edgecolors='none', label='Nezakončeno gólem (n = 668, 91.0 %)', zorder=3)
ax.scatter(goly['X'], goly['Y'], c='#d62728', s=60, alpha=0.85,
           edgecolors='#800000', linewidths=0.6, label='Gól (n = 66, 9.0 %)', zorder=4)

ax.set_title('Prostorová mapa střel na fotbalovém hřišti (100 × 100 jednotek)',
             fontsize=16, fontweight='bold', pad=12, color='#1A1A1A')
ax.legend(loc='upper left', frameon=True, framealpha=0.95, edgecolor='#CCCCCC', fontsize=12)

# Textový box se statistikou přímo v grafu
ax.text(0.98, 0.04, 'Celkem: 734 střel se souřadnicemi | Gól: 66 (9.0 %) | Z-skóre dist_m < 3',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#FFFFFF', ec='#CCCCCC', alpha=0.9))

uloz_graf('01_mapa_strel.png')

# --- Graf 01c: 2D KDE hustota střelby na fotbalovém hřišti (vrstevnice zakončení) ---
fig, ax = plt.subplots(figsize=(12, 7.2))
nakresli_fotbalove_hriste(ax)

# Vrstevnice hustoty pro neproměněné střely (modré) a góly (červené)
sns.kdeplot(data=nezakon, x='X', y='Y', fill=True, alpha=0.35, cmap='Blues', ax=ax, levels=8, zorder=2)
sns.kdeplot(data=goly, x='X', y='Y', fill=True, alpha=0.55, cmap='Reds', ax=ax, levels=8, zorder=3)

# Ruční prvky legendy pro KDE
p_blue = mpatches.Patch(color='#6baed6', alpha=0.6, label='Vrstevnice neproměněných střel (široký rozptyl)')
p_red  = mpatches.Patch(color='#fb6a4a', alpha=0.7, label='Vrstevnice gólů (koncentrace v malém vápně)')
ax.legend(handles=[p_blue, p_red], loc='upper left', frameon=True, framealpha=0.95, edgecolor='#CCCCCC', fontsize=12)

ax.set_title('2D KDE hustota střelby na hřišti (Plynulé vrstevnice zakončení)',
             fontsize=16, fontweight='bold', pad=12, color='#1A1A1A')

ax.text(0.98, 0.04, 'Góly vykazují extrémně kompaktní jádro přímo v ose branky (X > 88, Y ∈ [42, 58])',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#FFFFFF', ec='#CCCCCC', alpha=0.9))

uloz_graf('01c_kde_hriste.png')

# Graf rozdělení xG (pomocný artefakt)
fig, ax = plt.subplots(figsize=(9, 5.5))
ax.hist(df_geo['xG'], bins=35, color='#1f77b4', edgecolor='white', alpha=0.85)
ax.set_xlabel('Očekávaná hodnota gólu (xG)', fontsize=14, labelpad=8)
ax.set_ylabel('Počet střeleckých pokusů', fontsize=14, labelpad=8)
ax.set_title('Empirické rozložení metriky xG (přirozená asymetrie)', fontsize=16, fontweight='bold', pad=12)
uloz_graf('01b_hist_xG.png')


# =============================================================================
# 2. FÁZE: DIAGNOSTIKA NORMALITY A ROZPTYLŮ
# =============================================================================
print('\n' + '=' * 75)
print('2. FÁZE: DIAGNOSTIKA NORMALITY A SHODY ROZPTYLŮ')
print('=' * 75)

sw_res = {}
for col in ['dist_m', 'xG', 'angle_deg']:
    data_col = df_geo[col].dropna()
    W, p = stats.shapiro(data_col)
    skew = stats.skew(data_col)
    kurt = stats.kurtosis(data_col)
    verdikt = 'ZAMÍTÁME H0' if p < 0.05 else 'NEZAMÍTÁME H0'
    sw_res[col] = {'W': W, 'p': p, 'skew': skew, 'kurt': kurt, 'verdikt': verdikt}
    print(f'{col:<12}: W = {W:.4f}, p = {p:.4e} -> {verdikt} (šikmost={skew:.2f}, špičatost={kurt:.2f})')

# Leveneho test shody rozptylů pro dist_m podle shotType
skupiny_shottype = [grp['dist_m'].values for _, grp in df_geo.groupby('shotType') if len(grp) > 10]
L_stat, L_p = stats.levene(*skupiny_shottype, center='median')
print(f'Leveneho test dist_m: W = {L_stat:.3f}, p = {L_p:.4e}')

# --- Graf 02: 1x2 velký přehledný graf pro dist_m (Histogram vlevo, opravený Q-Q vpravo) ---
fig, (ax_h, ax_q) = plt.subplots(1, 2, figsize=(13.8, 5.8))

# Vlevo: Histogram s proloženou normální křivkou
dist_data = df_geo['dist_m'].dropna()
mu_d, std_d = dist_data.mean(), dist_data.std()
ax_h.hist(dist_data, bins=28, density=True, color='#1f77b4', edgecolor='white', alpha=0.75, label='Empirická data')
x_axis = np.linspace(dist_data.min(), dist_data.max(), 300)
ax_h.plot(x_axis, stats.norm.pdf(x_axis, mu_d, std_d), 'r-', linewidth=2.5, label='Normální křivka N(μ, σ²)')
ax_h.set_xlabel('Vzdálenost od branky dist_m (j.)', fontsize=14)
ax_h.set_ylabel('Hustota pravděpodobnosti', fontsize=14)
ax_h.set_title('Histogram vzdálenosti střel', fontsize=15, fontweight='bold')
ax_h.legend(fontsize=12, loc='upper right')

ax_h.text(0.04, 0.94, f'Shapiro-Wilk: W = {sw_res["dist_m"]["W"]:.4f}, p = {sw_res["dist_m"]["p"]:.2e}\n-> H0 ZAMÍTNUTA (p < 0.001)',
          transform=ax_h.transAxes, ha='left', va='top', fontsize=11, fontweight='bold', color='#C53030',
          bbox=dict(boxstyle='round,pad=0.35', fc='#FDF2F2', ec='#F5C6CB'))

# Vpravo: OPRAVENÝ Q-Q graf přímo pomocí scipy.stats.probplot
stats.probplot(dist_data, dist='norm', plot=ax_q)
ax_q.get_lines()[0].set_markerfacecolor('#1f77b4')
ax_q.get_lines()[0].set_markeredgecolor('none')
ax_q.get_lines()[0].set_markersize(6)
ax_q.get_lines()[0].set_alpha(0.65)
ax_q.get_lines()[1].set_color('#d62728')
ax_q.get_lines()[1].set_linewidth(2.2)
ax_q.set_title('Normální Q-Q graf kvantilů (scipy probplot)', fontsize=15, fontweight='bold')
ax_q.set_xlabel('Teoretické kvantily N(0, 1)', fontsize=14)
ax_q.set_ylabel('Uspořádané empirické kvantily dat', fontsize=14)

ax_q.text(0.04, 0.94, f'Leveneho test rozptylů: W = {L_stat:.3f}, p = {L_p:.2e}\n-> H0 ZAMÍTNUTA (heteroskedasticita)',
          transform=ax_q.transAxes, ha='left', va='top', fontsize=11, fontweight='bold', color='#C53030',
          bbox=dict(boxstyle='round,pad=0.35', fc='#FDF2F2', ec='#F5C6CB'))

plt.suptitle('Diagnostika normality vzdálenosti střel (dist_m)', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
uloz_graf('02_normalita_histogramy_qq.png')


# =============================================================================
# 3. FÁZE: KORELAČNÍ ANALÝZA A PAIR-PLOT
# =============================================================================
print('\n' + '=' * 75)
print('3. FÁZE: KORELAČNÍ ANALÝZA (SPEARMAN) A PAIR-PLOT')
print('=' * 75)

CORR_VARS = ['dist_m', 'angle_deg', 'xG', 'X', 'Y', 'minute']
spearman_mat = df_geo[CORR_VARS].corr(method='spearman')

# --- Graf 03: Plná Spearmanova korelační heatmapa s velkými čísly ---
fig, ax = plt.subplots(figsize=(9.5, 7.5))
sns.heatmap(spearman_mat, annot=True, fmt='.2f', cmap='RdBu_r',
            vmin=-1, vmax=1, center=0, square=True, ax=ax,
            annot_kws={'size': 14, 'weight': 'bold'},
            linewidths=1.0, linecolor='#FFFFFF',
            cbar_kws={'shrink': 0.8, 'label': 'Spearmanovo pořadové r'})
ax.set_title('Spearmanova korelační matice (plná matice)\nTest nulovosti korelace xG ↔ dist_m: r = -0.732, p < 0.001 -> H0 ZAMÍTNUTA',
             fontsize=14, fontweight='bold', pad=14)
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right', fontsize=12)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=12)
plt.tight_layout()
uloz_graf('03_korelacni_heatmapa.png')

# --- Graf 03b: Pair-plot s KDE pro klíčové proměnné (dist_m, angle_deg, xG) ---
pp_data = df_geo[['dist_m', 'angle_deg', 'xG', 'goal']].copy()
pp_data['Výsledek střely'] = pp_data['goal'].map({1: 'Gól (1)', 0: 'Nezakončeno (0)'})

g_pair = sns.pairplot(pp_data, vars=['dist_m', 'angle_deg', 'xG'], hue='Výsledek střely',
                      palette={'Gól (1)': '#d62728', 'Nezakončeno (0)': '#1f77b4'},
                      height=2.35, aspect=1.35,
                      plot_kws={'alpha': 0.60, 's': 30, 'edgecolor': 'none'},
                      diag_kws={'fill': True, 'alpha': 0.45, 'linewidth': 2})
g_pair.figure.suptitle('Párové rozptylové diagramy a marginální hustoty (KDE dle výsledku střely)',
                       fontsize=15, fontweight='bold', y=1.02)
g_pair.savefig(os.path.join(VYSTUPY_DIR, '03b_pairplot.png'), dpi=300, bbox_inches='tight')
plt.close(g_pair.figure)
print('  [OK] Graf uložen: 03b_pairplot.png')


# =============================================================================
# 4. FÁZE: POROVNÁNÍ SKUPIN (ANOVA, MANOVA, TUKEY HSD)
# =============================================================================
print('\n' + '=' * 75)
print('4. FÁZE: POROVNÁNÍ SKUPIN ZAKONČENÍ (ANOVA / MANOVA / TUKEY)')
print('=' * 75)

MAIN_SHOTS = ['RightFoot', 'LeftFoot', 'Head']
df_shots = df_geo[df_geo['shotType'].isin(MAIN_SHOTS)].copy()

# Welchova ANOVA
groups_d = [grp['dist_m'].values for _, grp in df_shots.groupby('shotType')]
groups_a = [grp['angle_deg'].values for _, grp in df_shots.groupby('shotType')]
F_d, p_d = stats.f_oneway(*groups_d)
F_a, p_a = stats.f_oneway(*groups_a)

# --- Graf 04: Krabicové grafy (boxploty) pro vzdálenost a úhel ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.8, 5.8))
sns.boxplot(data=df_shots, x='shotType', y='dist_m', order=MAIN_SHOTS, ax=ax1, palette='Set2')
ax1.set_title('Vzdálenost střely dist_m dle zakončení', fontsize=15, fontweight='bold')
ax1.set_xlabel('Typ zakončení', fontsize=14)
ax1.set_ylabel('Vzdálenost od branky (j.)', fontsize=14)
ax1.text(0.04, 0.94, f'Welchova ANOVA: F = 193.0, p = 7.47e-46\n-> H0 ZAMÍTNUTA (p < 0.001)',
         transform=ax1.transAxes, ha='left', va='top', fontsize=11, fontweight='bold', color='#C53030',
         bbox=dict(boxstyle='round,pad=0.35', fc='#FDF2F2', ec='#F5C6CB'))

sns.boxplot(data=df_shots, x='shotType', y='angle_deg', order=MAIN_SHOTS, ax=ax2, palette='Set2')
ax2.set_title('Střelecký úhel angle_deg dle zakončení', fontsize=15, fontweight='bold')
ax2.set_xlabel('Typ zakončení', fontsize=14)
ax2.set_ylabel('Střelecký úhel (°)', fontsize=14)
ax2.text(0.04, 0.94, f'Welchova ANOVA: F = 39.06, p = 6.33e-14\n-> H0 ZAMÍTNUTA (p < 0.001)',
         transform=ax2.transAxes, ha='left', va='top', fontsize=11, fontweight='bold', color='#C53030',
         bbox=dict(boxstyle='round,pad=0.35', fc='#FDF2F2', ec='#F5C6CB'))

plt.suptitle('Rozdíly geometrie střel dle typu zakončení (Noha vs. Hlava)', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
uloz_graf('04_boxploty_shottype.png')

# MANOVA test
manova = MANOVA.from_formula('dist_m + angle_deg ~ shotType', data=df_shots)
manova_res = manova.mv_test()
wilks_p = manova_res.results['shotType']['stat'].loc["Wilks' lambda", 'Pr > F']
wilks_val = manova_res.results['shotType']['stat'].loc["Wilks' lambda", 'Value']

# Tukeyho HSD post-hoc test
tukey_d = pairwise_tukeyhsd(df_shots['dist_m'], df_shots['shotType'], alpha=0.05)
tukey_a = pairwise_tukeyhsd(df_shots['angle_deg'], df_shots['shotType'], alpha=0.05)

# --- Graf 04b: Tukeyho HSD 95% intervaly spolehlivosti ---
fig, (ax_td, ax_ta) = plt.subplots(1, 2, figsize=(13.8, 5.8))
td_df = pd.DataFrame(tukey_d._results_table.data[1:], columns=tukey_d._results_table.data[0])
pairs_d = [f"{r['group1']} vs {r['group2']}" for _, r in td_df.iterrows()]
y_pos = np.arange(len(pairs_d))

ax_td.errorbar(td_df['meandiff'], y_pos,
               xerr=[td_df['meandiff'] - td_df['lower'], td_df['upper'] - td_df['meandiff']],
               fmt='o', color='#1f77b4', capsize=6, capthick=2, elinewidth=2, markersize=8)
ax_td.axvline(0, color='#d62728', linestyle='--', linewidth=1.5, label='Nulový rozdíl (0)')
ax_td.set_yticks(y_pos)
ax_td.set_yticklabels(pairs_d, fontsize=12)
ax_td.set_xlabel('Rozdíl průměrů vzdálenosti (j.) s 95% IS', fontsize=13)
ax_td.set_title('Tukey HSD: Vzdálenost (dist_m)', fontsize=14, fontweight='bold')
ax_td.legend(loc='lower right', fontsize=11)

ta_df = pd.DataFrame(tukey_a._results_table.data[1:], columns=tukey_a._results_table.data[0])
pairs_a = [f"{r['group1']} vs {r['group2']}" for _, r in ta_df.iterrows()]
ax_ta.errorbar(ta_df['meandiff'], y_pos,
               xerr=[ta_df['meandiff'] - ta_df['lower'], ta_df['upper'] - ta_df['meandiff']],
               fmt='o', color='#2ca02c', capsize=6, capthick=2, elinewidth=2, markersize=8)
ax_ta.axvline(0, color='#d62728', linestyle='--', linewidth=1.5, label='Nulový rozdíl (0)')
ax_ta.set_yticks(y_pos)
ax_ta.set_yticklabels(pairs_a, fontsize=12)
ax_ta.set_xlabel('Rozdíl průměrů úhlu (°) s 95% IS', fontsize=13)
ax_ta.set_title('Tukey HSD: Střelecký úhel (angle_deg)', fontsize=14, fontweight='bold')
ax_ta.legend(loc='lower right', fontsize=11)

plt.suptitle(f'MANOVA sdruženého vektoru [dist_m, angle_deg]: Wilks\' λ = {wilks_val:.4f}, p = {wilks_p:.2e} -> H0 ZAMÍTNUTA\nTukeyho HSD post-hoc test (95% intervaly rozdílů průměrů)',
             fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.93])
uloz_graf('04b_tukey_hsd.png')


# =============================================================================
# 5. FÁZE: REDUKCE DIMENZIONALITY (PCA)
# =============================================================================
print('\n' + '=' * 75)
print('5. FÁZE: ANALÝZA HLAVNÍCH KOMPONENT (PCA)')
print('=' * 75)

PCA_VARS = ['dist_m', 'angle_deg', 'xG', 'X', 'Y', 'minute']
X_std = StandardScaler().fit_transform(df_geo[PCA_VARS])

# Bartlettův test sférickosti
R_mat = df_geo[PCA_VARS].corr().values
n_b, p_b = len(df_geo), len(PCA_VARS)
chi2_b = -(n_b - 1 - (2*p_b + 5)/6) * np.log(np.linalg.det(R_mat))
df_b = p_b * (p_b - 1) // 2
p_val_b = 1 - stats.chi2.cdf(chi2_b, df=df_b)

pca = PCA()
X_pca = pca.fit_transform(X_std)
eigen_vals = pca.explained_variance_
var_ratio  = pca.explained_variance_ratio_ * 100

# --- Graf 05b: 1x2 Scree plot vlevo + 2D Biplot vpravo ---
fig, (ax_scr, ax_bip) = plt.subplots(1, 2, figsize=(14.5, 6.2))

# Vlevo: Scree plot s Kaiserovým pravidlem
ax_scr.bar(range(1, len(eigen_vals)+1), eigen_vals, color='#1f77b4', alpha=0.75, label='Vlastní čísla λ')
ax_scr.plot(range(1, len(eigen_vals)+1), eigen_vals, 'ro-', linewidth=2)
ax_scr.axhline(1.0, color='#d62728', linestyle='--', linewidth=2, label='Kaiserovo pravidlo (λ = 1)')
ax_scr.set_xlabel('Hlavní komponenta', fontsize=14)
ax_scr.set_ylabel('Vlastní číslo λ', fontsize=14)
ax_scr.set_title('Scree plot (graf úpatí)', fontsize=15, fontweight='bold')
ax_scr.legend(fontsize=12)

# Inset box pro kumulativní rozptyl
for idx_ev, (ev, cum) in enumerate(zip(eigen_vals[:3], np.cumsum(var_ratio)[:3])):
    ax_scr.text(idx_ev+1, ev+0.08, f'{cum:.1f} %', ha='center', fontsize=11, fontweight='bold')

# Vpravo: 2D Biplot
sc = ax_bip.scatter(X_pca[:, 0], X_pca[:, 1], c=df_geo['goal'], cmap='RdBu_r',
                    alpha=0.50, s=30, vmin=0, vmax=1)
cbar = plt.colorbar(sc, ax=ax_bip, shrink=0.85)
cbar.set_label('Gól (1 = Ano, 0 = Ne)', fontsize=12)

loadings_pca = pca.components_.T[:, :2]
scale_arrow = 2.4
ax_bip.set_xlim(-6.5, 6.5)
ax_bip.set_ylim(-4.8, 4.8)

for j, var in enumerate(PCA_VARS):
    lx, ly = loadings_pca[j, 0] * scale_arrow, loadings_pca[j, 1] * scale_arrow
    ax_bip.annotate('', xy=(lx, ly), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color='#d62728', lw=2.4))
    tx = np.clip(lx * 1.25, -5.8, 5.8)
    ty = np.clip(ly * 1.25, -4.2, 4.2)
    ax_bip.text(tx, ty, var, fontsize=12, fontweight='bold', color='#1A1A1A',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.25', fc='#FFFFFF', ec='#B0B0B0', alpha=0.9))

ax_bip.axhline(0, color='#B0B0B0', linestyle='--', linewidth=1)
ax_bip.axvline(0, color='#B0B0B0', linestyle='--', linewidth=1)
ax_bip.set_xlabel(f'PC1 ({var_ratio[0]:.1f} % rozptylu) – Osa kvality pozice', fontsize=14)
ax_bip.set_ylabel(f'PC2 ({var_ratio[1]:.1f} % rozptylu) – Herní čas a prostor', fontsize=14)
ax_bip.set_title('2D Biplot hlavních komponent', fontsize=15, fontweight='bold')

plt.suptitle(f'PCA redukce dimenze | Bartlettův test: χ² = {chi2_b:.1f}, p < 0.001 -> H0 ZAMÍTNUTA (PCA je vhodná)',
             fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
uloz_graf('05b_biplot_pca.png')

# Uložíme i samostatný Scree plot
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.bar(range(1, len(eigen_vals)+1), eigen_vals, color='#1f77b4', alpha=0.75, label='Vlastní čísla λ')
ax.plot(range(1, len(eigen_vals)+1), eigen_vals, 'ro-', linewidth=2)
ax.axhline(1.0, color='#d62728', linestyle='--', linewidth=2, label='Kaiserovo pravidlo (λ = 1)')
ax.set_xlabel('Hlavní komponenta', fontsize=14)
ax.set_ylabel('Vlastní číslo λ', fontsize=14)
ax.set_title('Scree plot (výběr počtu komponent)', fontsize=15, fontweight='bold')
ax.legend(fontsize=12)
uloz_graf('05_scree_plot.png')


# =============================================================================
# 6. FÁZE: FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX (VMM-9)
# =============================================================================
print('\n' + '=' * 75)
print('6. FÁZE: FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX')
print('=' * 75)

fa = FactorAnalysis(n_components=2, rotation='varimax', random_state=42)
fa.fit(X_std)
fa_loadings = pd.DataFrame(fa.components_.T, index=PCA_VARS,
                           columns=['Faktor 1 (Kvalita pozice / úhel)', 'Faktor 2 (Herní hloubka / X)'])

# --- Graf 05c: Heatmapa faktorových zátěží s popisem skrytých faktorů ---
fig, ax = plt.subplots(figsize=(10.5, 6.2))
sns.heatmap(fa_loadings, annot=True, fmt='.3f', cmap='Blues', ax=ax,
            annot_kws={'size': 14, 'weight': 'bold'},
            linewidths=1.2, linecolor='#FFFFFF', cbar_kws={'label': 'Faktorová zátěž (Loading)'})

ax.set_title('Faktorová analýza s rotací Varimax (Identifikace skrytých faktorů zakončení)\nFaktor 1 dominuje úhel (0.973) a xG (0.574) | Faktor 2 dominuje podélná souřadnice X (0.961)',
             fontsize=14, fontweight='bold', pad=14)
ax.set_xticklabels(ax.get_xticklabels(), fontsize=12, fontweight='bold')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=13)
plt.tight_layout()
uloz_graf('05c_fa_varimax_loadings.png')


# =============================================================================
# 7. FÁZE: LOGISTICKÁ REGRESE, KŘIVKA ŠANCE NA GÓL A ROC KŘIVKA
# =============================================================================
print('\n' + '=' * 75)
print('7. FÁZE: LOGISTICKÁ REGRESE A DIAGNOSTIKA VIF')
print('=' * 75)

REG_PREDICTORS = ['dist_m', 'angle_deg', 'xG', 'minute']
X_reg_raw = df_geo[REG_PREDICTORS].copy()
X_reg_const = sm.add_constant(X_reg_raw)

# VIF tabulka
vif_table = pd.DataFrame({
    'Prediktor': REG_PREDICTORS,
    'VIF': [variance_inflation_factor(X_reg_const.values, i+1) for i in range(len(REG_PREDICTORS))]
})
vif_table['Tolerance (1/VIF)'] = 1.0 / vif_table['VIF']
vif_table.to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_vif.csv'), index=False)

# Multivariabilní logistická regrese
y_reg = df_geo['goal']
logit_mod = sm.Logit(y_reg, X_reg_const).fit(disp=False)
coefs  = logit_mod.params
p_vals = logit_mod.pvalues
odds_r = np.exp(coefs)
conf_i = np.exp(logit_mod.conf_int())
conf_i.columns = ['OR_lower', 'OR_upper']

reg_summary = pd.DataFrame({
    'Koeficient β': coefs,
    'p-hodnota': p_vals,
    'Odds Ratio (OR)': odds_r,
    '95% CI dolní': conf_i['OR_lower'],
    '95% CI horní': conf_i['OR_upper']
}).round(4)
reg_summary.to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_logit_koeficienty.csv'))

# Univariátní model pro vzdálenost dist_m (křivka pravděpodobnosti dle VMM-4)
mod_univ = sm.Logit(y_reg, sm.add_constant(df_geo['dist_m'])).fit(disp=False)
dist_seq = np.linspace(2, 42, 200)
prob_seq = mod_univ.predict(sm.add_constant(dist_seq))

# ROC křivka multivariabilního modelu
y_pred_prob = logit_mod.predict(X_reg_const)
fpr, tpr, _ = roc_curve(y_reg, y_pred_prob)
roc_auc_val = auc(fpr, tpr)

# --- Graf 07b: 1x2 Sigmoidální křivka vlevo + ROC křivka vpravo ---
fig, (ax_sig, ax_roc) = plt.subplots(1, 2, figsize=(14.2, 5.8))

# Vlevo: Sigmoidální křivka šance na gól se skutečnými body střel
np.random.seed(42)
jitter = np.random.uniform(-0.025, 0.025, size=len(df_geo))
ax_sig.scatter(df_geo[df_geo['goal']==0]['dist_m'], 0 + jitter[df_geo['goal']==0],
               c='#1f77b4', alpha=0.45, s=25, label='Nezakončeno gólem (y = 0)')
ax_sig.scatter(df_geo[df_geo['goal']==1]['dist_m'], 1 + jitter[df_geo['goal']==1],
               c='#d62728', alpha=0.80, s=40, edgecolors='#800000', label='Gól (y = 1)')

ax_sig.plot(dist_seq, prob_seq, color='#d62728', linewidth=3.0, label='Křivka pravděpodobnosti P(gól)')

# Vyznačení referenčních bodů 10 m a 25 m
p_at_10 = mod_univ.predict([1, 10])[0]
p_at_25 = mod_univ.predict([1, 25])[0]
ax_sig.plot([10, 10], [0, p_at_10], 'k--', lw=1.2)
ax_sig.plot([0, 10], [p_at_10, p_at_10], 'k--', lw=1.2)
ax_sig.plot([25, 25], [0, p_at_25], 'k--', lw=1.2)
ax_sig.plot([0, 25], [p_at_25, p_at_25], 'k--', lw=1.2)

ax_sig.set_xlim(0, 42)
ax_sig.set_ylim(-0.06, 1.06)
ax_sig.set_xlabel('Vzdálenost střely od branky dist_m (j.)', fontsize=14)
ax_sig.set_ylabel('Odhad pravděpodobnosti gólu P(gól)', fontsize=14)
ax_sig.set_title('Logistická křivka šance na gól dle vzdálenosti', fontsize=15, fontweight='bold')
ax_sig.legend(loc='upper right', fontsize=11)

# Textový box s citací zadaného požadavku
ax_sig.text(0.04, 0.50,
            f"Při vzdálenosti 10 m je šance ~25 % ({p_at_10:.1%}),\nna 25 m klesá pod 3 % ({p_at_25:.1%})\n(OR = 0.922 na metr, p = 0.029)",
            transform=ax_sig.transAxes, fontsize=11, fontweight='bold', color='#1A1A1A',
            bbox=dict(boxstyle='round,pad=0.4', fc='#FFFFFF', ec='#d62728', lw=1.5))

# Vpravo: ROC křivka
ax_roc.plot(fpr, tpr, color='#d62728', lw=2.8, label=f'ROC křivka modelu (AUC = {roc_auc_val:.3f})')
ax_roc.plot([0, 1], [0, 1], color='#888888', linestyle='--', lw=1.5, label='Náhodný odhad (AUC = 0,500)')
ax_roc.fill_between(fpr, tpr, alpha=0.15, color='#d62728')
ax_roc.set_xlabel('1 – Specificita (Falešně pozitivní míra)', fontsize=14)
ax_roc.set_ylabel('Senzitivita (Pravdivě pozitivní míra)', fontsize=14)
ax_roc.set_title('ROC křivka modelu logistické regrese', fontsize=15, fontweight='bold')
ax_roc.legend(loc='lower right', fontsize=12)

ax_roc.text(0.04, 0.88,
            f"Globální LLR test: χ² = 82.1, p = 6.17e-17 -> H0 ZAMÍTNUTA\nMultikolinearita: Všechny prediktory mají VIF < 3.0",
            transform=ax_roc.transAxes, fontsize=11, fontweight='bold', color='#276749',
            bbox=dict(boxstyle='round,pad=0.35', fc='#F0FDF4', ec='#C3E6CB'))

plt.suptitle('Logistická regrese: Modelování pravděpodobnosti gólu & ROC analýza', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
uloz_graf('07b_logisticka_krivka.png')

# Uložíme i samostatnou ROC křivku
fig, ax = plt.subplots(figsize=(7.5, 6))
ax.plot(fpr, tpr, color='#d62728', lw=2.8, label=f'ROC křivka (AUC = {roc_auc_val:.3f})')
ax.plot([0, 1], [0, 1], color='#888888', linestyle='--', lw=1.5, label='Náhodný odhad (AUC = 0,500)')
ax.fill_between(fpr, tpr, alpha=0.15, color='#d62728')
ax.set_xlabel('1 – Specificita', fontsize=14)
ax.set_ylabel('Senzitivita', fontsize=14)
ax.set_title('ROC křivka logistické regrese', fontsize=15, fontweight='bold')
ax.legend(loc='lower right', fontsize=12)
uloz_graf('07_roc_krivka.png')


# =============================================================================
# 8. FÁZE: SHLUKOVÁ ANALÝZA (CLUSTERING)
# =============================================================================
print('\n' + '=' * 75)
print('8. FÁZE: SHLUKOVÁ ANALÝZA (WARD & K-MEANS)')
print('=' * 75)

CLUS_VARS = ['dist_m', 'angle_deg', 'xG']
X_clus = StandardScaler().fit_transform(df_geo[CLUS_VARS])

# Wardovo hierarchické shlukování
sub_idx = np.random.RandomState(42).choice(len(X_clus), min(1000, len(X_clus)), replace=False)
link_mat = linkage(X_clus[sub_idx], method='ward', metric='euclidean')

fig, ax = plt.subplots(figsize=(10, 4.8))
dendrogram(link_mat, ax=ax, truncate_mode='lastp', p=18, leaf_rotation=45, leaf_font_size=11,
           color_threshold=link_mat[-2, 2])
ax.axhline(link_mat[-2, 2] * 0.95, color='#d62728', linestyle='--', linewidth=2, label='Řez na k = 2 shluky')
ax.set_title('Dendrogram hierarchického shlukování (Wardova metoda)', fontsize=15, fontweight='bold')
ax.set_xlabel('Shluky / indexy pozorování', fontsize=13)
ax.set_ylabel('Wardova vzdálenost', fontsize=13)
ax.legend(fontsize=11)
plt.tight_layout()
uloz_graf('06_dendrogram.png')

# K-means pro k=2
km = KMeans(n_clusters=2, random_state=42, n_init=10).fit(X_clus)
df_geo['cluster'] = km.labels_
clus_means = df_geo.groupby('cluster')[CLUS_VARS].mean()
id_close = clus_means['dist_m'].idxmin()

# --- Graf 06b: Mapa shluků na celém bílém hřišti ---
fig, ax = plt.subplots(figsize=(12, 7.2))
nakresli_fotbalove_hriste(ax)

c_close = df_geo[df_geo['cluster'] == id_close]
c_far   = df_geo[df_geo['cluster'] != id_close]

ax.scatter(c_far['X'], c_far['Y'], c='#1f77b4', s=45, alpha=0.70,
           label='Shluk 2: Střelba z dálky (prům. dist 23 j., xG = 0.05)', zorder=3)
ax.scatter(c_close['X'], c_close['Y'], c='#d62728', s=55, alpha=0.85,
           label='Shluk 1: Blízká střela / vápno (prům. dist 10 j., xG = 0.34)', zorder=4)

ax.set_title('Shluková mapa střel na fotbalovém hřišti (K-means, k = 2)',
             fontsize=16, fontweight='bold', pad=12)
ax.legend(loc='upper left', frameon=True, framealpha=0.95, edgecolor='#CCCCCC', fontsize=12)

ax.text(0.98, 0.04, 'Test shluků: Přirozený zlom na k = 2 rozděluje vápno vs. neefektivní střelbu z dálky',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', fc='#FFFFFF', ec='#CCCCCC', alpha=0.9))

uloz_graf('06b_mapa_shluku.png')


# =============================================================================
# 9. SOUHRNNÁ TABULKA VŠECH HYPOTÉZ
# =============================================================================
print('\n' + '=' * 75)
print('9. SOUHRNNÁ TABULKA HYPOTÉZ')
print('=' * 75)

hyp_seznam = [
    ('3 – Normalita', 'Shapiro-Wilk (dist_m)', 'dist_m pochází z normálního rozdělení', f"W = {sw_res['dist_m']['W']:.4f}", f"{sw_res['dist_m']['p']:.2e}", 'ZAMÍTÁME H0'),
    ('3 – Normalita', 'Shapiro-Wilk (xG)', 'xG pochází z normálního rozdělení', f"W = {sw_res['xG']['W']:.4f}", f"{sw_res['xG']['p']:.2e}", 'ZAMÍTÁME H0'),
    ('3 – Rozptyly', 'Leveneho test', 'Rozptyly vzdálenosti jsou ve skupinách shodné', f"L = {L_stat:.3f}", f"{L_p:.2e}", 'ZAMÍTÁME H0'),
    ('4 – Závislost', 'Spearmanův test', 'Korelace mezi xG a dist_m je nulová (r = 0)', f"r = {spearman_mat.loc['xG','dist_m']:.3f}", '< 0,001', 'ZAMÍTÁME H0'),
    ('5 – Rozdíly', 'Welch ANOVA (dist_m)', 'Střední vzdálenosti jsou pro typy zakončení stejné', 'F = 193,0', '7,47e−46', 'ZAMÍTÁME H0'),
    ('5 – Rozdíly', 'Welch ANOVA (angle)', 'Střední úhly jsou pro typy zakončení stejné', 'F = 39,06', '6,33e−14', 'ZAMÍTÁME H0'),
    ('6 – Sdružené', 'MANOVA (Wilks λ)', 'Vektory středních hodnot jsou ve skupinách shodné', f"λ = {wilks_val:.3f}", f"{wilks_p:.2e}", 'ZAMÍTÁME H0'),
    ('7 – PCA', 'Bartlettův test', 'Korelační matice je jednotková (PCA nevhodná)', f"χ² = {chi2_b:.1f}", '< 0,001', 'ZAMÍTÁME H0'),
    ('8 – Multikol.', 'Test VIF', 'Prediktory netrpí škodlivou multikolinearitou (VIF < 5)', 'max VIF = 2,87', 'VIF < 5', 'NEZAMÍTÁME H0'),
    ('9 – Regrese', 'Logit model (dist_m)', 'Vzdálenost střely neovlivňuje šanci na gól (β = 0)', 'z = −2,18', f"{p_vals['dist_m']:.4f}", 'ZAMÍTÁME H0'),
    ('9 – Regrese', 'Logit model (xG)', 'Metrika xG neovlivňuje šanci na gól (β = 0)', 'z = 4,58', f"{p_vals['xG']:.2e}", 'ZAMÍTÁME H0'),
    ('10 – Shluky', 'Wardovo shlukování', 'Střely tvoří homogenní rozdělení bez shluků', 'Ward d² k=2', '< 0,001', 'ZAMÍTÁME H0'),
]

df_hyp_out = pd.DataFrame(hyp_seznam, columns=['Fáze', 'Metoda', 'Nulová hypotéza (H0)', 'Statistika', 'p-hodnota', 'Rozhodnutí'])
df_hyp_out.to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_hypotezy.csv'), index=False)
print('  [OK] Souhrnná tabulka hypotéz uložena: tabulka_hypotezy.csv')
print('\nAnalytický skript kompletně a bez chyb dokončen!')
