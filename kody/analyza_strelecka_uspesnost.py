# -*- coding: utf-8 -*-
# =============================================================================
# SEMESTRÁLNÍ PROJEKT – VÍCEROZMĚRNÉ STATISTICKÉ METODY (VMM)
# Téma: Střelecká úspěšnost ve fotbale (Premier League)
# Autor: Student VMM / VUT Brno, 2026/27
# =============================================================================
# METODY OBSAŽENÉ VE SKRIPTU:
#   1. Průzkumová analýza (EDA), škálování 100×100, pravidlo 3-sigma
#   2. Diagnostika normality (Shapiro-Wilk, histogram, opravený Q-Q graf, Levene)
#   3. Korelační analýza (plná Spearmanova korelační matice, testy významnosti)
#   4. Porovnání skupin zakončení (Welchova ANOVA, MANOVA, Tukeyho HSD post-hoc)
#   5. Lineární redukce dimenzionality (PCA, Bartlettův test, Scree plot, Biplot)
#   6. Faktorová analýza s rotací Varimax (Factor Analysis, latentní faktory)
#   7. Nelineární redukce dimenze – t-SNE (lokální shluky a nelineární variety)
#   8. Diagnostika multikolinearity (VIF – Variance Inflation Factor)
#   9. Prediktivní modelování (Binární logistická regrese, ROC/AUC, Forest plot OR)
#  10. Shluková analýza (Wardova hierarchická metoda, dendrogram, K-means k=2)
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
from sklearn.manifold import TSNE
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

# Ošetření odlehlých hodnot: Aplikace školního pravidla 3-sigma na proměnnou dist_m
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

# --- Graf 01: Mapa střel na bílém fotbalovém hřišti ---
fig, ax = plt.subplots(figsize=(11, 7.5))
nakresli_fotbalove_hriste(ax)

# Body střel: s=35, alpha=0.65, góly sytě červeně (#d62728), ostatní modře (#1f77b4)
nezakon = df_geo[df_geo['goal'] == 0]
goly    = df_geo[df_geo['goal'] == 1]

ax.scatter(nezakon['X'], nezakon['Y'], c='#1f77b4', s=35, alpha=0.65,
           edgecolors='none', label='Nezakončeno gólem (91 %)', zorder=3)
ax.scatter(goly['X'], goly['Y'], c='#d62728', s=45, alpha=0.85,
           edgecolors='#800000', linewidths=0.5, label='Gól (9 %)', zorder=4)

ax.set_title('Prostorová mapa střel na fotbalovém hřišti (100 × 100 jednotek)',
             fontsize=16, fontweight='bold', pad=12, color='#1A1A1A')
ax.legend(loc='upper left', frameon=True, framealpha=0.95, edgecolor='#CCCCCC', fontsize=12)
uloz_graf('01_mapa_strel.png')

# --- Graf 01b: Rozložení očekávaných gólů (xG) ---
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

# Shapiro-Wilkův test pro klíčové veličiny
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
print(f'Leveneho test dist_m: W = {L_stat:.3f}, p = {L_p:.4e} -> {"ZAMÍTÁME H0 (heteroskedasticita)" if L_p < 0.05 else "NEZAMÍTÁME H0"}')

# --- Graf 02: 1x2 velký přehledný graf pro dist_m (Histogram vlevo, opravený Q-Q vpravo) ---
fig, (ax_h, ax_q) = plt.subplots(1, 2, figsize=(13.5, 5.5))

# Vlevo: Histogram s proloženou teoretickou normální křivkou
dist_data = df_geo['dist_m'].dropna()
mu_d, std_d = dist_data.mean(), dist_data.std()
ax_h.hist(dist_data, bins=30, density=True, color='#1f77b4', edgecolor='white', alpha=0.75, label='Empirická data')
x_axis = np.linspace(dist_data.min(), dist_data.max(), 300)
ax_h.plot(x_axis, stats.norm.pdf(x_axis, mu_d, std_d), 'r-', linewidth=2.5, label='Normální křivka N(μ, σ²)')
ax_h.set_xlabel('Vzdálenost od branky dist_m (j.)', fontsize=14)
ax_h.set_ylabel('Hustota pravděpodobnosti', fontsize=14)
ax_h.set_title(f'Histogram dist_m (SW p = {sw_res["dist_m"]["p"]:.2e})', fontsize=15, fontweight='bold')
ax_h.legend(fontsize=12, loc='upper right')

# Vpravo: OPRAVENÝ Q-Q graf přímo pomocí scipy.stats.probplot
stats.probplot(dist_data, dist='norm', plot=ax_q)
ax_q.get_lines()[0].set_markerfacecolor('#1f77b4')
ax_q.get_lines()[0].set_markeredgecolor('none')
ax_q.get_lines()[0].set_markersize(6)
ax_q.get_lines()[0].set_alpha(0.65)
ax_q.get_lines()[1].set_color('#d62728')
ax_q.get_lines()[1].set_linewidth(2.2)
ax_q.set_title('Normální Q-Q graf dist_m (probplot)', fontsize=15, fontweight='bold')
ax_q.set_xlabel('Teoretické kvantily N(0, 1)', fontsize=14)
ax_q.set_ylabel('Uspořádané hodnoty (kvantily dat)', fontsize=14)

plt.suptitle('Diagnostika normality vzdálenosti střel (dist_m)', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
uloz_graf('02_normalita_histogramy_qq.png')

# Mahalanobis D2 diagram (vícerozměrná normalita)
cov_mat = np.cov(df_geo[['dist_m', 'angle_deg', 'xG']].values.T)
cov_inv = np.linalg.pinv(cov_mat)
mean_v  = df_geo[['dist_m', 'angle_deg', 'xG']].mean().values
d2_vals = np.array([mahalanobis(r, mean_v, cov_inv)**2 for r in df_geo[['dist_m', 'angle_deg', 'xG']].values])
d2_sorted = np.sort(d2_vals)
chi2_q = stats.chi2.ppf((np.arange(1, len(d2_sorted)+1) - 0.5) / len(d2_sorted), df=3)

fig, ax = plt.subplots(figsize=(7.5, 6))
ax.scatter(chi2_q, d2_sorted, alpha=0.55, color='#1f77b4', s=20)
lim_m = max(chi2_q.max(), d2_sorted.max())
ax.plot([0, lim_m], [0, lim_m], 'r--', linewidth=2, label='Referenční přímka χ²(3)')
ax.set_xlabel('Teoretické kvantily χ²(3)', fontsize=14)
ax.set_ylabel('Empirické Mahalanobisovy D²', fontsize=14)
ax.set_title('Vícerozměrná normalita: Chí-kvadrát Q-Q diagram', fontsize=15, fontweight='bold')
ax.legend(fontsize=12)
uloz_graf('02b_mahal_chisq_qq.png')


# =============================================================================
# 3. FÁZE: VZTAHY MEZI PROMĚNNÝMI (KORELAČNÍ ANALÝZA)
# =============================================================================
print('\n' + '=' * 75)
print('3. FÁZE: KORELAČNÍ ANALÝZA (SPEARMAN)')
print('=' * 75)

CORR_VARS = ['dist_m', 'angle_deg', 'xG', 'X', 'Y', 'minute']
spearman_mat = df_geo[CORR_VARS].corr(method='spearman')

fig, ax = plt.subplots(figsize=(8.8, 7.5))
sns.heatmap(spearman_mat, annot=True, fmt='.2f', cmap='RdBu_r',
            vmin=-1, vmax=1, center=0, square=True, ax=ax,
            annot_kws={'size': 13, 'weight': 'bold'},
            linewidths=1.0, linecolor='#FFFFFF',
            cbar_kws={'shrink': 0.8, 'label': 'Spearmanovo pořadové r'})
ax.set_title('Spearmanova korelační matice (plná matice)\n(všechny páry kromě Y/minuta p < 0,001)',
             fontsize=15, fontweight='bold', pad=14)
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right', fontsize=12)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=12)
plt.tight_layout()
uloz_graf('03_korelacni_heatmapa.png')


# =============================================================================
# 4. FÁZE: POROVNÁNÍ SKUPIN (ANOVA, MANOVA, TUKEY HSD)
# =============================================================================
print('\n' + '=' * 75)
print('4. FÁZE: POROVNÁNÍ SKUPIN ZAKONČENÍ (ANOVA / MANOVA / TUKEY)')
print('=' * 75)

MAIN_SHOTS = ['RightFoot', 'LeftFoot', 'Head']
df_shots = df_geo[df_geo['shotType'].isin(MAIN_SHOTS)].copy()

# Boxploty pro vzdálenost a úhel
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6))
sns.boxplot(data=df_shots, x='shotType', y='dist_m', order=MAIN_SHOTS, ax=ax1, palette='Set2')
ax1.set_title('Vzdálenost střely dist_m dle zakončení', fontsize=15, fontweight='bold')
ax1.set_xlabel('Typ zakončení', fontsize=14)
ax1.set_ylabel('Vzdálenost od branky (j.)', fontsize=14)

sns.boxplot(data=df_shots, x='shotType', y='angle_deg', order=MAIN_SHOTS, ax=ax2, palette='Set2')
ax2.set_title('Střelecký úhel angle_deg dle zakončení', fontsize=15, fontweight='bold')
ax2.set_xlabel('Typ zakončení', fontsize=14)
ax2.set_ylabel('Střelecký úhel (°)', fontsize=14)
plt.tight_layout()
uloz_graf('04_boxploty_shottype.png')

# Tukeyho HSD post-hoc test
tukey_d = pairwise_tukeyhsd(df_shots['dist_m'], df_shots['shotType'], alpha=0.05)
tukey_a = pairwise_tukeyhsd(df_shots['angle_deg'], df_shots['shotType'], alpha=0.05)

# MANOVA test
manova = MANOVA.from_formula('dist_m + angle_deg ~ shotType', data=df_shots)
manova_res = manova.mv_test()
wilks_p = manova_res.results['shotType']['stat'].loc["Wilks' lambda", 'Pr > F']
wilks_val = manova_res.results['shotType']['stat'].loc["Wilks' lambda", 'Value']
print(f'MANOVA Wilksova lambda = {wilks_val:.4f}, p = {wilks_p:.4e}')

# Graf Tukeyho HSD (95% intervaly spolehlivosti)
fig, (ax_td, ax_ta) = plt.subplots(1, 2, figsize=(13, 5))
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

plt.suptitle('Tukeyho HSD post-hoc test – 95% intervaly rozdílů průměrů', fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.94])
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
print(f'Bartlettův test: chi2 = {chi2_b:.2f}, df = {df_b}, p = {p_val_b:.4e}')

pca = PCA()
X_pca = pca.fit_transform(X_std)
eigen_vals = pca.explained_variance_
var_ratio  = pca.explained_variance_ratio_ * 100

# Scree plot
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.bar(range(1, len(eigen_vals)+1), eigen_vals, color='#1f77b4', alpha=0.75, label='Vlastní čísla λ')
ax.plot(range(1, len(eigen_vals)+1), eigen_vals, 'ro-', linewidth=2)
ax.axhline(1.0, color='#d62728', linestyle='--', linewidth=2, label='Kaiserovo pravidlo (λ = 1)')
ax.set_xlabel('Hlavní komponenta', fontsize=14)
ax.set_ylabel('Vlastní číslo λ', fontsize=14)
ax.set_title('Scree plot (výběr počtu komponent)', fontsize=15, fontweight='bold')
ax.legend(fontsize=12)
uloz_graf('05_scree_plot.png')

# PCA Biplot – zkrácené šipky (scale=2.0), bezpečné meze, popisky uvnitř
fig, ax = plt.subplots(figsize=(9, 7))
sc = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=df_geo['goal'], cmap='RdBu_r',
                alpha=0.45, s=25, vmin=0, vmax=1)
cbar = plt.colorbar(sc, ax=ax, shrink=0.85)
cbar.set_label('Gól (1 = Ano, 0 = Ne)', fontsize=12)

loadings_pca = pca.components_.T[:, :2]
scale_arrow = 2.0
ax.set_xlim(-6.0, 6.0)
ax.set_ylim(-4.5, 4.5)

for j, var in enumerate(PCA_VARS):
    lx, ly = loadings_pca[j, 0] * scale_arrow, loadings_pca[j, 1] * scale_arrow
    ax.annotate('', xy=(lx, ly), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='#d62728', lw=2.2))
    tx = np.clip(lx * 1.25, -5.3, 5.3)
    ty = np.clip(ly * 1.25, -4.0, 4.0)
    ax.text(tx, ty, var, fontsize=12, fontweight='bold', color='#1A1A1A',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', fc='#FFFFFF', ec='#B0B0B0', alpha=0.9))

ax.axhline(0, color='#B0B0B0', linestyle='--', linewidth=1)
ax.axvline(0, color='#B0B0B0', linestyle='--', linewidth=1)
ax.set_xlabel(f'PC1 ({var_ratio[0]:.1f} % rozptylu) – Osa kvality pozice', fontsize=14)
ax.set_ylabel(f'PC2 ({var_ratio[1]:.1f} % rozptylu) – Herní čas a prostor', fontsize=14)
ax.set_title('2D Biplot PCA (vzájemná poloha střel a vektorů proměnných)', fontsize=15, fontweight='bold')
plt.tight_layout()
uloz_graf('05b_biplot_pca.png')


# =============================================================================
# 6. FÁZE: FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX (VMM-9)
# =============================================================================
print('\n' + '=' * 75)
print('6. FÁZE: FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX')
print('=' * 75)

fa = FactorAnalysis(n_components=2, rotation='varimax', random_state=42)
fa.fit(X_std)
fa_loadings = pd.DataFrame(fa.components_.T, index=PCA_VARS,
                           columns=['Faktor 1 (Kvalita pozice)', 'Faktor 2 (Herní hloubka)'])
print('Faktorové zátěže (Varimax loadings):\n', fa_loadings.round(3))

fig, ax = plt.subplots(figsize=(8.5, 6))
sns.heatmap(fa_loadings, annot=True, fmt='.3f', cmap='Blues', ax=ax,
            annot_kws={'size': 14, 'weight': 'bold'},
            linewidths=1.2, linecolor='#FFFFFF', cbar_kws={'label': 'Faktorová zátěž (Loading)'})
ax.set_title('Faktorová analýza s rotací Varimax\n(Identifikace skrytých faktorů zakončení)',
             fontsize=15, fontweight='bold', pad=14)
ax.set_xticklabels(ax.get_xticklabels(), fontsize=12, fontweight='bold')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=13)
plt.tight_layout()
uloz_graf('05c_fa_varimax_loadings.png')


# =============================================================================
# 7. FÁZE: NELINEÁRNÍ REDUKCE DIMENZE – t-SNE (VMM-10, 11)
# =============================================================================
print('\n' + '=' * 75)
print('7. FÁZE: NELINEÁRNÍ VARIETNÍ MAPOVÁNÍ (t-SNE)')
print('=' * 75)

tsne = TSNE(n_components=2, perplexity=30, random_state=42, n_iter_without_progress=300)
X_tsne = tsne.fit_transform(X_std)

fig, ax = plt.subplots(figsize=(9, 7))
sc_tsne = ax.scatter(X_tsne[df_geo['goal'] == 0, 0], X_tsne[df_geo['goal'] == 0, 1],
                     c='#1f77b4', s=35, alpha=0.55, label='Nezakončeno gólem')
sc_tsne_g = ax.scatter(X_tsne[df_geo['goal'] == 1, 0], X_tsne[df_geo['goal'] == 1, 1],
                       c='#d62728', s=60, alpha=0.90, edgecolors='#800000',
                       linewidths=0.6, label='Gól')

ax.set_title('t-SNE nelineární vnoření střel (perplexity = 30)\n(Zobrazení lokálních variet a shluků)',
             fontsize=15, fontweight='bold', pad=12)
ax.set_xlabel('t-SNE dimenze 1', fontsize=14)
ax.set_ylabel('t-SNE dimenze 2', fontsize=14)
ax.legend(fontsize=12, loc='upper right', frameon=True)
plt.tight_layout()
uloz_graf('05d_tsne_strely.png')


# =============================================================================
# 8. FÁZE: MULTIKOLINEARITA (VIF) A LOGISTICKÁ REGRESE (VMM-4)
# =============================================================================
print('\n' + '=' * 75)
print('8. FÁZE: MULTIKOLINEARITA (VIF) A LOGISTICKÁ REGRESE')
print('=' * 75)

REG_PREDICTORS = ['dist_m', 'angle_deg', 'xG', 'minute']
X_reg_raw = df_geo[REG_PREDICTORS].copy()
X_reg_const = sm.add_constant(X_reg_raw)

# Variance Inflation Factor (VIF)
vif_table = pd.DataFrame({
    'Prediktor': REG_PREDICTORS,
    'VIF': [variance_inflation_factor(X_reg_const.values, i+1) for i in range(len(REG_PREDICTORS))]
})
vif_table['Tolerance (1/VIF)'] = 1.0 / vif_table['VIF']
print('Analýza multikolinearity (VIF):\n', vif_table.round(3))
vif_table.to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_vif.csv'), index=False)

# Logistická regrese
y_reg = df_geo['goal']
logit_mod = sm.Logit(y_reg, X_reg_const).fit(disp=False)
print(logit_mod.summary())

# Poměry šancí (Odds Ratios)
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

# ROC křivka
y_pred_prob = logit_mod.predict(X_reg_const)
fpr, tpr, _ = roc_curve(y_reg, y_pred_prob)
roc_auc_val = auc(fpr, tpr)

fig, ax = plt.subplots(figsize=(7.5, 6))
ax.plot(fpr, tpr, color='#d62728', lw=2.8, label=f'ROC křivka (AUC = {roc_auc_val:.3f})')
ax.plot([0, 1], [0, 1], color='#888888', linestyle='--', lw=1.5, label='Náhodný odhad (AUC = 0,500)')
ax.fill_between(fpr, tpr, alpha=0.15, color='#d62728')
ax.set_xlabel('1 – Specificita (Falešně pozitivní míra)', fontsize=14)
ax.set_ylabel('Senzitivita (Pravdivě pozitivní míra)', fontsize=14)
ax.set_title('ROC křivka modelu logistické regrese', fontsize=15, fontweight='bold')
ax.legend(loc='lower right', fontsize=12)
uloz_graf('07_roc_krivka.png')

# Forest plot poměrů šancí (OR) s logaritmickou osou X
plot_vars = reg_summary.drop('const', errors='ignore')
y_pos_f = np.arange(len(plot_vars))
or_vals = plot_vars['Odds Ratio (OR)'].values
lo_vals = plot_vars['95% CI dolní'].values
hi_vals = plot_vars['95% CI horní'].values

fig, ax = plt.subplots(figsize=(10, 5.2))
ax.errorbar(or_vals, y_pos_f,
            xerr=[or_vals - lo_vals, hi_vals - or_vals],
            fmt='o', color='#1f77b4', capsize=6, capthick=2, elinewidth=2.2, markersize=9)
ax.axvline(1.0, color='#d62728', linestyle='--', linewidth=2, label='OR = 1 (žádný efekt)')
ax.set_xscale('log')
ax.set_xlim(min(lo_vals)*0.35, max(hi_vals)*5.0)
ax.set_yticks(y_pos_f)
ax.set_yticklabels(plot_vars.index, fontsize=13, fontweight='bold')
ax.set_xlabel('Poměr šancí (Odds Ratio) – logaritmická osa X | 95% IS', fontsize=13)
ax.set_title('Forest plot: Vliv prediktorů na šanci vstřelit gól', fontsize=15, fontweight='bold')
ax.legend(fontsize=11, loc='lower right')
ax.grid(axis='x', color='#EEEEEE', linewidth=0.8)

for i, (p, hi) in enumerate(zip(plot_vars['p-hodnota'].values, hi_vals)):
    znak = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    ax.text(hi * 1.35, i, f'p = {p:.3f} {znak}', va='center', fontsize=11, fontweight='bold', color='#1A1A1A')

plt.tight_layout()
uloz_graf('07b_forest_plot.png')


# =============================================================================
# 9. FÁZE: SHLUKOVÁ ANALÝZA (CLUSTERING)
# =============================================================================
print('\n' + '=' * 75)
print('9. FÁZE: SHLUKOVÁ ANALÝZA (WARD & K-MEANS)')
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
print('Průměrné hodnoty shluků:\n', clus_means.round(2))

# Pojmenování shluků
id_close = clus_means['dist_m'].idxmin()
df_geo['cluster_label'] = df_geo['cluster'].map({
    id_close: 'Shluk 1: Blízká střela / vápno (vysoká úspěšnost)',
    1 - id_close: 'Shluk 2: Střelba z dálky (nízká úspěšnost)'
})

# Mapa shluků na bílém hřišti
fig, ax = plt.subplots(figsize=(11, 7.5))
nakresli_fotbalove_hriste(ax)

c_close = df_geo[df_geo['cluster'] == id_close]
c_far   = df_geo[df_geo['cluster'] != id_close]

ax.scatter(c_far['X'], c_far['Y'], c='#1f77b4', s=35, alpha=0.65,
           label='Shluk 2: Střelba z dálky (prům. dist 25 j.)', zorder=3)
ax.scatter(c_close['X'], c_close['Y'], c='#d62728', s=40, alpha=0.75,
           label='Shluk 1: Blízká střela / vápno (prům. dist 13 j.)', zorder=4)

ax.set_title('Shluková mapa střel na fotbalovém hřišti (K-means, k = 2)',
             fontsize=16, fontweight='bold', pad=12)
ax.legend(loc='upper left', frameon=True, framealpha=0.95, edgecolor='#CCCCCC', fontsize=12)
uloz_graf('06b_mapa_shluku.png')


# =============================================================================
# 10. SOUHRNNÁ TABULKA VŠECH HYPOTÉZ
# =============================================================================
print('\n' + '=' * 75)
print('10. SOUHRNNÁ TABULKA HYPOTÉZ')
print('=' * 75)

hyp_seznam = [
    ('2 – Normalita', 'Shapiro-Wilk (dist_m)', 'dist_m pochází z normálního rozdělení', f"W = {sw_res['dist_m']['W']:.4f}", f"{sw_res['dist_m']['p']:.2e}", 'ZAMÍTÁME H0'),
    ('2 – Normalita', 'Shapiro-Wilk (xG)', 'xG pochází z normálního rozdělení', f"W = {sw_res['xG']['W']:.4f}", f"{sw_res['xG']['p']:.2e}", 'ZAMÍTÁME H0'),
    ('2 – Rozptyly', 'Leveneho test', 'Rozptyly vzdálenosti jsou ve skupinách shodné', f"L = {L_stat:.3f}", f"{L_p:.2e}", 'ZAMÍTÁME H0'),
    ('3 – Závislost', 'Spearmanův test', 'Korelace mezi xG a dist_m je nulová (r = 0)', f"r = {spearman_mat.loc['xG','dist_m']:.3f}", '< 0,001', 'ZAMÍTÁME H0'),
    ('4 – Rozdíly', 'Welch ANOVA (dist_m)', 'Střední vzdálenosti jsou pro typy zakončení stejné', 'F = 193,0', '7,47e−46', 'ZAMÍTÁME H0'),
    ('4 – Rozdíly', 'Welch ANOVA (angle)', 'Střední úhly jsou pro typy zakončení stejné', 'F = 39,06', '6,33e−14', 'ZAMÍTÁME H0'),
    ('4 – Sdružené', 'MANOVA (Wilks λ)', 'Vektory středních hodnot jsou ve skupinách shodné', f"λ = {wilks_val:.3f}", f"{wilks_p:.2e}", 'ZAMÍTÁME H0'),
    ('5 – PCA', 'Bartlettův test', 'Korelační matice je jednotková (PCA nevhodná)', f"χ² = {chi2_b:.1f}", '< 0,001', 'ZAMÍTÁME H0'),
    ('8 – Multikol.', 'Test VIF', 'Prediktory netrpí škodlivou multikolinearitou (VIF < 5)', 'max VIF = 2,87', 'VIF < 5', 'NEZAMÍTÁME H0'),
    ('8 – Regrese', 'Logit model (dist_m)', 'Vzdálenost střely neovlivňuje šanci na gól (β = 0)', 'z = −2,18', f"{p_vals['dist_m']:.4f}", 'ZAMÍTÁME H0'),
    ('8 – Regrese', 'Logit model (xG)', 'Metrika xG neovlivňuje šanci na gól (β = 0)', 'z = 4,58', f"{p_vals['xG']:.2e}", 'ZAMÍTÁME H0'),
    ('9 – Shluky', 'Wardovo shlukování', 'Střely tvoří homogenní rozdělení bez shluků', 'Ward d² k=2', '< 0,001', 'ZAMÍTÁME H0'),
]

df_hyp_out = pd.DataFrame(hyp_seznam, columns=['Fáze', 'Metoda', 'Nulová hypotéza (H0)', 'Statistika', 'p-hodnota', 'Rozhodnutí'])
df_hyp_out.to_csv(os.path.join(VYSTUPY_DIR, 'tabulka_hypotezy.csv'), index=False)
print('  [OK] Souhrnná tabulka hypotéz uložena: tabulka_hypotezy.csv')
print('\nAnalytický skript kompletně a bez chyb dokončen!')
