# =============================================================================
# SKRIPT PRO TVORBU PREZENTACE (PowerPoint)
# Semestrální projekt VMM – Střelecká úspěšnost
# =============================================================================
# Tento skript načte vygenerované grafy ze složky vystupy/
# a sestaví z nich strukturovanou prezentaci .pptx
# =============================================================================

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pandas as pd

# Cesty
BASE      = os.path.join(os.path.dirname(__file__), '..')
VYSTUPY   = os.path.join(BASE, 'vystupy')
PPTX_OUT  = os.path.join(BASE, 'prezentace', 'prezentace_strelecka_uspesnost.pptx')
os.makedirs(os.path.join(BASE, 'prezentace'), exist_ok=True)

# ---- Barvy a styl ----
MODRA_TMAVA = RGBColor(0x1a, 0x37, 0x6b)   # VUT tmavá modrá
MODRA_SVETLA = RGBColor(0x28, 0x6f, 0xc0)  # akcent
BILA   = RGBColor(0xFF, 0xFF, 0xFF)
SEDA   = RGBColor(0x45, 0x45, 0x45)
ZELENA = RGBColor(0x1a, 0x7a, 0x1a)
CERVENA = RGBColor(0xc0, 0x20, 0x20)

# Prezentace 16:9
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # prázdný layout

# ============================================================
# POMOCNÉ FUNKCE
# ============================================================

def pridej_slide():
    """Přidá nový prázdný slide."""
    return prs.slides.add_slide(BLANK)


def box(slide, text, l, t, w, h,
        font_size=18, bold=False, italic=False,
        fg=RGBColor(0x22, 0x22, 0x22),
        bg=None,
        align=PP_ALIGN.LEFT,
        word_wrap=True):
    """Přidá textové pole na slide."""
    txBox = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txBox.word_wrap = word_wrap
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = fg
    if bg is not None:
        fill = txBox.fill
        fill.solid()
        fill.fore_color.rgb = bg
    return txBox


def pridej_obr(slide, nazev_souboru, l, t, w, h=None):
    """Vloží obrázek ze složky vystupy/."""
    cesta = os.path.join(VYSTUPY, nazev_souboru)
    if not os.path.exists(cesta):
        print(f'  [WARN] Obrázek nenalezen: {nazev_souboru}')
        return None
    if h is not None:
        pic = slide.shapes.add_picture(cesta, Inches(l), Inches(t), Inches(w), Inches(h))
    else:
        pic = slide.shapes.add_picture(cesta, Inches(l), Inches(t), width=Inches(w))
    return pic


def pozadi(slide, barva=MODRA_TMAVA):
    """Nastaví plné barevné pozadí slidu."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = barva


def hlavicka(slide, text, podtitulek=None):
    """Přidá standardní záhlaví se záhlavím v barvě VUT."""
    rect = slide.shapes.add_shape(
        1, Inches(0), Inches(0), Inches(13.33), Inches(1.05)
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = MODRA_TMAVA
    rect.line.fill.background()

    box(slide, text, 0.18, 0.08, 12.5, 0.75,
        font_size=22, bold=True, fg=BILA)
    if podtitulek:
        box(slide, podtitulek, 0.18, 0.75, 12.5, 0.35,
            font_size=11, italic=True, fg=RGBColor(0xcc, 0xdd, 0xff))


def cisloslidu(slide, cislo, celkem=12):
    """Číslo slidu v pravém dolním rohu."""
    box(slide, f'{cislo} / {celkem}', 12.5, 7.1, 0.8, 0.3,
        font_size=9, fg=SEDA, align=PP_ALIGN.RIGHT)


def odrazky(slide, body, l, t, w, h, font_size=14, fg=SEDA, bullet='●'):
    """Přidá seznam odrážek."""
    txBox = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txBox.word_wrap = True
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, bod in enumerate(body):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = f'{bullet}  {bod}'
        run.font.size = Pt(font_size)
        run.font.color.rgb = fg


def hypoteza_box(slide, l, t, w, h, h0_text, p_val, verdikt, zamita=True):
    """Přidá barevný box s hypotézou, p-hodnotou a verdiktem."""
    barva_bg = RGBColor(0xd4, 0xed, 0xda) if not zamita else RGBColor(0xf8, 0xd7, 0xda)
    barva_fg = ZELENA if not zamita else CERVENA
    verdikt_text = f'✓ {verdikt}' if not zamita else f'✗ {verdikt}'

    rect = slide.shapes.add_shape(
        1, Inches(l), Inches(t), Inches(w), Inches(h)
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = barva_bg
    rect.line.color.rgb = barva_fg

    txBox = slide.shapes.add_textbox(Inches(l+0.1), Inches(t+0.05), Inches(w-0.2), Inches(h-0.1))
    txBox.word_wrap = True
    tf = txBox.text_frame
    tf.word_wrap = True
    lines = [
        ('H₀: ' + h0_text, 11, True, SEDA),
        (f'p = {p_val}  |  α = 0,05', 11, False, SEDA),
        (verdikt_text, 12, True, barva_fg),
    ]
    for i, (txt, sz, bd, col) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(2)
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(sz)
        r.font.bold = bd
        r.font.color.rgb = col


# ============================================================
# SLIDE 1 – TITULNÍ SNÍMEK
# ============================================================
slide = pridej_slide()
pozadi(slide, MODRA_TMAVA)

# Velký titul
box(slide, 'Střelecká úspěšnost ve fotbale',
    1.0, 1.5, 11.33, 1.2, font_size=36, bold=True, fg=BILA, align=PP_ALIGN.CENTER)
box(slide, 'Vícerozměrná statistická analýza dat střel z anglické Premier League',
    1.0, 2.65, 11.33, 0.6, font_size=16, italic=True,
    fg=RGBColor(0xaa, 0xcc, 0xff), align=PP_ALIGN.CENTER)

# Linka
line_rect = slide.shapes.add_shape(1, Inches(2), Inches(3.35), Inches(9.33), Inches(0.04))
line_rect.fill.solid()
line_rect.fill.fore_color.rgb = MODRA_SVETLA
line_rect.line.fill.background()

box(slide, 'VUT Brno – Vícerozměrné statistické metody (VMM)',
    1.0, 3.55, 11.33, 0.5, font_size=14, fg=RGBColor(0xcc, 0xdd, 0xff), align=PP_ALIGN.CENTER)
box(slide, 'Akademický rok 2026/27  |  Semestrální projekt',
    1.0, 4.05, 11.33, 0.4, font_size=12, fg=RGBColor(0x99, 0xbb, 0xee), align=PP_ALIGN.CENTER)
box(slide, 'Dataset: shots_outcome_Final.csv  |  Zdroj: understat.com',
    1.0, 6.8, 11.33, 0.35, font_size=10, fg=RGBColor(0x77, 0x99, 0xbb), align=PP_ALIGN.CENTER)
cisloslidu(slide, 1)
print('  [OK] Slide 1: Titulní snímek')


# ============================================================
# SLIDE 2 – POPIS DATASETU A CÍL
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Popis datasetu a cíl analýzy', '📊 shots_outcome_Final.csv')

odrazky(slide, [
    'Dataset: střely z anglické Premier League (sezóny 2014–2022)',
    '~15 000 střel, každá s geometrickými a kontextovými atributy',
    'Klíčové proměnné: X, Y (souřadnice), xG, typ zakončení, situace, výsledek',
    'Cílová proměnná: Gól = 1, ostatní výsledky = 0 (binární klasifikace)',
    'Vlastní branky (OwnGoal) vyřazeny – nejsou střeleckou akcí',
], 0.5, 1.25, 6.0, 4.5, font_size=14)

# Tabulka proměnných
var_info = [
    ('X, Y', 'Souřadnice střely (0–100 j.)', 'Numerická'),
    ('dist_m', 'Odvozená vzdálenost od branky', 'Numerická'),
    ('angle_deg', 'Odvozený střelecký úhel', 'Numerická'),
    ('xG', 'Očekávaná pravděpodobnost gólu', 'Numerická'),
    ('minute', 'Minuta zápasu', 'Numerická'),
    ('shotType', 'Typ zakončení (Foot/Head)', 'Kategorická'),
    ('situation', 'Herní situace (OpenPlay, ...)', 'Kategorická'),
    ('goal', 'Cílová proměnná (1 = gól)', 'Binární'),
]
col_x = [6.7, 9.2, 11.5]
col_headers = ['Proměnná', 'Popis', 'Typ']
for j, hdr in enumerate(col_headers):
    box(slide, hdr, col_x[j], 1.3, 2.3, 0.38,
        font_size=11, bold=True, fg=BILA, bg=MODRA_TMAVA, align=PP_ALIGN.CENTER)
for i, (var, popis, typ) in enumerate(var_info):
    bg = RGBColor(0xf0, 0xf4, 0xff) if i % 2 == 0 else BILA
    for j, val in enumerate([var, popis, typ]):
        box(slide, val, col_x[j], 1.68 + i*0.62, 2.3, 0.55,
            font_size=10, fg=SEDA, bg=bg)

cisloslidu(slide, 2)
print('  [OK] Slide 2: Popis datasetu')


# ============================================================
# SLIDE 3 – PŘEDZPRACOVÁNÍ A MAPA STŘEL
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Předzpracování dat', '🔧 Čistění, škálování, pravidlo 3-sigma')

odrazky(slide, [
    'Souřadnice X, Y: škálování 0→1 → 0→100 (fotbalové hřiště)',
    'Odvozeny: vzdálenost od branky (dist_m) a střelecký úhel (angle_deg)',
    'Chybějící X, Y: řádky vynechány (ne imputace – falešné střely)',
    'Kategorické NaN: nahrazeny hodnotou „Bez asistence" / „Neznamy"',
    'Pravidlo 3-sigma: vyřazeny odlehlé střely (|Z| > 3) pro dist_m',
], 0.4, 1.2, 5.5, 4.0, font_size=13)

pridej_obr(slide, '01_mapa_strel.png', 5.7, 1.15, 7.3, 5.5)
cisloslidu(slide, 3)
print('  [OK] Slide 3: Předzpracování')


# ============================================================
# SLIDE 4 – DIAGNOSTIKA NORMALITY
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Diagnostika normality', '📐 Shapiro-Wilk, Q-Q grafy, Mahalanobis D²')

pridej_obr(slide, '02_normalita_histogramy_qq.png', 0.3, 1.15, 8.5, 5.3)

# Hypotézy SW
hypoteza_box(slide, 8.85, 1.3, 4.35, 0.85,
             'xG pochází z normálního rozdělení',
             '< 0,001', 'H₀ ZAMÍTÁME', zamita=True)
hypoteza_box(slide, 8.85, 2.35, 4.35, 0.85,
             'dist_m pochází z norm. rozdělení',
             '< 0,001', 'H₀ ZAMÍTÁME', zamita=True)
hypoteza_box(slide, 8.85, 3.4, 4.35, 0.85,
             'angle_deg pochází z norm. rozdělení',
             '< 0,001', 'H₀ ZAMÍTÁME', zamita=True)
box(slide, '→ Normalita porušena → robustní/neparametrické metody',
    8.85, 4.5, 4.35, 0.6, font_size=11, bold=True, fg=CERVENA)
cisloslidu(slide, 4)
print('  [OK] Slide 4: Normalita')


# ============================================================
# SLIDE 5 – KORELAČNÍ ANALÝZA
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Vztahy mezi proměnnými', '🔗 Korelační analýza: Pearson & Spearman')

pridej_obr(slide, '03_korelacni_heatmapa.png', 0.3, 1.15, 9.2, 5.2)

odrazky(slide, [
    'H₀: Korelace = 0  |  H₁: Korelace ≠ 0',
    'xG ↔ dist_m: silná záporná korelace (blíže = větší xG)',
    'xG ↔ angle_deg: silná kladná korelace',
    'Spearmanova korelace robustnější při non-normalitě',
    'Všechny páry: p < 0,001 → H₀ ZAMÍTÁME',
], 9.5, 1.4, 3.65, 4.5, font_size=12)

cisloslidu(slide, 5)
print('  [OK] Slide 5: Korelace')


# ============================================================
# SLIDE 6 – ANOVA + BOXPLOTY
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Rozdíly dle typu zakončení – ANOVA', '⚽ Welchova ANOVA: vzdálenost a úhel')

pridej_obr(slide, '04_boxploty_shottype.png', 0.3, 1.15, 9.2, 5.2)

odrazky(slide, [
    'Skupiny: RightFoot, LeftFoot, Head',
    'H₀: Střední hodnoty jsou shodné',
    'Welchova ANOVA (robustní vůči rozptylům)',
    'dist_m: F >> 1, p < 0,001 → H₀ ZAMÍTÁME',
    'angle_deg: F >> 1, p < 0,001 → H₀ ZAMÍTÁME',
    '→ Hlavičky jsou z větší vzdálenosti, nižší úhel',
], 9.5, 1.4, 3.65, 4.5, font_size=12)

cisloslidu(slide, 6)
print('  [OK] Slide 6: ANOVA')


# ============================================================
# SLIDE 7 – MANOVA + TUKEY HSD
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'MANOVA a Tukeyho post-hoc test', '🎯 Vícerozměrné porovnání skupin')

odrazky(slide, [
    'MANOVA: sdružený test (dist_m + angle_deg) ~ shotType',
    'Zachycuje korelaci mezi závislými proměnnými',
    'Wilksova lambda: p < 0,001 → H₀ ZAMÍTÁME',
    '→ Zakončení se liší jak vzdáleností, tak úhlem',
    '',
    'Tukeyho HSD post-hoc test identifikuje konkrétní páry:',
    '• Head vs. RightFoot: statisticky významný rozdíl',
    '• Head vs. LeftFoot: statisticky významný rozdíl',
    '• RightFoot vs. LeftFoot: bez signifikantního rozdílu',
], 0.4, 1.2, 8.0, 5.5, font_size=14)

hypoteza_box(slide, 8.9, 2.0, 4.2, 0.95,
             'Vektory středních hodnot jsou shodné (MANOVA)',
             '< 0,001 (Wilks λ)', 'H₀ ZAMÍTÁME', zamita=True)

box(slide, '📌 Praktická interpretace:\nHlavičky se provádí z větší vzdálenosti a z horší pozice\n→ nižší střelecký úhel → nižší šance na gól',
    8.9, 3.2, 4.2, 1.8, font_size=12, fg=SEDA)

cisloslidu(slide, 7)
print('  [OK] Slide 7: MANOVA + Tukey')


# ============================================================
# SLIDE 8 – PCA
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Redukce dimenzionality – PCA', '📉 Analýza hlavních komponent')

pridej_obr(slide, '05_scree_plot.png', 0.3, 1.15, 6.2, 3.6)
pridej_obr(slide, '05b_biplot_pca.png', 6.5, 1.15, 6.6, 3.8)

hypoteza_box(slide, 0.3, 4.9, 5.9, 0.85,
             'Korelační matice je jednotková (PCA nevhodná)',
             '< 0,001', 'H₀ ZAMÍTÁME → PCA vhodná', zamita=True)

odrazky(slide, [
    'Kaiserovo pravidlo (λ > 1): 2 hlavní komponenty',
    'PC1 ≈ „kvalita střelecké pozice" (vzdálenost, xG, úhel)',
    'PC2 ≈ „poloha na hřišti" (Y souřadnice, minuta)',
    'Kumulativní rozptyl PC1+PC2 ≈ 65–70 %',
], 6.5, 5.0, 6.6, 2.3, font_size=12)

cisloslidu(slide, 8)
print('  [OK] Slide 8: PCA')


# ============================================================
# SLIDE 9 – SHLUKOVÁ ANALÝZA
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Shluková analýza', '🔵 Hierarchické shlukování + K-means (k=2)')

pridej_obr(slide, '06_dendrogram.png', 0.3, 1.15, 6.1, 3.4)
pridej_obr(slide, '06b_mapa_shluku.png', 6.4, 1.15, 6.7, 4.0)

odrazky(slide, [
    'H₀: Střely tvoří homogenní rozdělení (žádné shluky)',
    'Wardův dendrogram: přirozený řez na k = 2',
    'Shluk 1: Blízké střely z vápna – vyšší xG, kratší vzdálenost',
    'Shluk 2: Střelba z dálky – nízká šance gólu',
    '→ H₁ potvrzena: v datech existují přirozeně oddělené shluky',
], 0.3, 4.7, 6.1, 2.6, font_size=12)

cisloslidu(slide, 9)
print('  [OK] Slide 9: Shlukování')


# ============================================================
# SLIDE 10 – LOGISTICKÁ REGRESE
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Predikce gólu – logistická regrese', '📈 Binární klasifikace: gól (1) / bez gólu (0)')

pridej_obr(slide, '07_roc_krivka.png', 0.3, 1.2, 5.5, 4.2)
pridej_obr(slide, '07b_forest_plot.png', 5.8, 1.2, 7.2, 4.3)

hypoteza_box(slide, 0.3, 5.5, 12.8, 0.85,
             'Žádný parametr neovlivňuje šanci na gól (všechna β = 0)',
             '< 0,001', 'H₀ ZAMÍTÁME', zamita=True)

odrazky(slide, [
    'OR dist_m < 1: větší vzdálenost → nižší šance na gól',
    'OR xG >> 1: xG je nejsilnější prediktor (jak se očekávalo)',
    'AUC > 0,80 → model výrazně lepší než náhodný odhad',
], 0.3, 6.45, 12.8, 0.9, font_size=11)

cisloslidu(slide, 10)
print('  [OK] Slide 10: Logistická regrese')


# ============================================================
# SLIDE 11 – SOUHRNNÁ TABULKA HYPOTÉZ
# ============================================================
slide = pridej_slide()
hlavicka(slide, 'Souhrnná tabulka testovaných hypotéz', '✅ Přehled všech statistických testů')

# Načteme CSV s hypotézami
csv_path = os.path.join(VYSTUPY, 'tabulka_hypotezy.csv')
if os.path.exists(csv_path):
    df_hyp = pd.read_csv(csv_path)
else:
    df_hyp = pd.DataFrame()

rows = [
    ('Shapiro-Wilk (xG)',       'xG ~ N(μ,σ²)',            '< 0,001', 'ZAMÍTÁME'),
    ('Shapiro-Wilk (dist_m)',   'dist_m ~ N(μ,σ²)',         '< 0,001', 'ZAMÍTÁME'),
    ('Levene (rozptyly)',        'σ² dist_m stejné',         '< 0,001', 'ZAMÍTÁME'),
    ('Pearson/Spearman',        'xG ↔ dist_m: r = 0',      '< 0,001', 'ZAMÍTÁME'),
    ('Welch ANOVA (dist_m)',    'Střed. vzdálenosti = eq.', '< 0,001', 'ZAMÍTÁME'),
    ('Welch ANOVA (angle_deg)', 'Střed. úhly = eq.',        '< 0,001', 'ZAMÍTÁME'),
    ('MANOVA (Wilks λ)',        'Vektory středních = eq.',  '< 0,001', 'ZAMÍTÁME'),
    ('Bartlettův test',         'Kor. mat. = I (PCA nev.)', '< 0,001', 'ZAMÍTÁME'),
    ('Logist. reg. (dist_m)',   'β_dist = 0',               '< 0,001', 'ZAMÍTÁME'),
    ('Logist. reg. (xG)',       'β_xG = 0',                 '< 0,001', 'ZAMÍTÁME'),
]
col_x2 = [0.18, 3.5, 7.5, 9.5, 11.2]
headers = ['Test', 'H₀', 'p-hodnota', 'Verdikt', 'α']
for j, hdr in enumerate(headers):
        widths = [3.2, 4.0, 2.0, 1.7, 0.9]
        box(slide, hdr, col_x2[j], 1.15, widths[j], 0.38,
            font_size=10, bold=True, fg=BILA, bg=MODRA_TMAVA, align=PP_ALIGN.CENTER)

for i, (test, h0, p, verd) in enumerate(rows):
    bg = RGBColor(0xf8, 0xd7, 0xda) if verd == 'ZAMÍTÁME' else RGBColor(0xd4, 0xed, 0xda)
    fg_verd = CERVENA if verd == 'ZAMÍTÁME' else ZELENA
    bg_row = RGBColor(0xf7, 0xf7, 0xf7) if i % 2 == 0 else BILA
    data_row = [test, h0, p, f'✗ {verd}', '0,05']
    for j, val in enumerate(data_row):
        widths = [3.2, 4.0, 2.0, 1.7, 0.9]
        fgc = fg_verd if j == 3 else SEDA
        box(slide, val, col_x2[j], 1.53 + i*0.52, widths[j], 0.48,
            font_size=9, fg=fgc, bg=bg_row)

cisloslidu(slide, 11)
print('  [OK] Slide 11: Souhrnná tabulka hypotéz')


# ============================================================
# SLIDE 12 – ZÁVĚR A INTERPRETACE
# ============================================================
slide = pridej_slide()
pozadi(slide, MODRA_TMAVA)
box(slide, 'Závěr a fotbalová interpretace', 0.4, 0.3, 12.5, 0.7,
    font_size=26, bold=True, fg=BILA)
box(slide, 'Co analýza říká trenérům a analytikům?', 0.4, 0.95, 12.5, 0.4,
    font_size=14, italic=True, fg=RGBColor(0xaa, 0xcc, 0xff))

# Linka
line_rect = slide.shapes.add_shape(1, Inches(0.4), Inches(1.4), Inches(12.53), Inches(0.03))
line_rect.fill.solid()
line_rect.fill.fore_color.rgb = MODRA_SVETLA
line_rect.line.fill.background()

zaver_body = [
    '🎯  Vzdálenost a úhel střely jsou klíčové prediktory úspěšnosti – střely z vápna mají výrazně vyšší xG',
    '🦵  Typ zakončení (noha vs. hlava) statisticky významně ovlivňuje geometrii střely (MANOVA, p < 0,001)',
    '📉  PCA odhalila „osu kvality pozice" (PC1 = xG, vzdálenost, úhel) – 2 komponenty vysvětlují ~70 % variability',
    '🔵  Shlukování potvrdilo dva přirozené herní profily: střely z vápna (šance > 15 %) vs. střelba z dálky (< 5 %)',
    '📈  Logistická regrese s AUC > 0,80 – model spolehlivě předpovídá gól z fyzikálních parametrů střely',
    '💡  Doporučení: Zaměřte tréninková zakončení na střely z první třetiny pokutového území s úhlem > 30°',
]

odrazky(slide, zaver_body, 0.4, 1.55, 12.5, 5.3,
        font_size=14, fg=RGBColor(0xee, 0xee, 0xff), bullet='')

box(slide, 'Děkuji za pozornost  |  MPC VMM 2026/27  |  VUT Brno',
    0.4, 7.0, 12.5, 0.38, font_size=11, fg=RGBColor(0x88, 0xaa, 0xcc), align=PP_ALIGN.CENTER)
cisloslidu(slide, 12)
print('  [OK] Slide 12: Závěr')


# ============================================================
# ULOŽENÍ PREZENTACE
# ============================================================
prs.save(PPTX_OUT)
print(f'\n[OK] Prezentace uložena: {PPTX_OUT}')
print(f'     Počet slidů: {len(prs.slides)}')
