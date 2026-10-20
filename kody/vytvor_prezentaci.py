# -*- coding: utf-8 -*-
# =============================================================================
# SKRIPT PRO TVORBU PREZENTACE (PowerPoint)
# Semestrální projekt VMM – Střelecká úspěšnost
# DESIGN: Čistě bílý, minimalistický, akademický
# =============================================================================

import os
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Cesty ──────────────────────────────────────────────────────────────────
BASE     = os.path.join(os.path.dirname(__file__), '..')
VYSTUPY  = os.path.join(BASE, 'vystupy')
PPTX_OUT = os.path.join(BASE, 'prezentace', 'prezentace_strelecka_uspesnost.pptx')
os.makedirs(os.path.join(BASE, 'prezentace'), exist_ok=True)

# ── Barvy (minimalistická paleta) ──────────────────────────────────────────
CERNA      = RGBColor(0x22, 0x22, 0x22)   # nadpisy, hlavní text
TMAVA_SEDA = RGBColor(0x44, 0x44, 0x44)   # tělo textu, odrážky
STRED_SEDA = RGBColor(0x88, 0x88, 0x88)   # pomocný text, číslo slidu
SVETLA_SEDA = RGBColor(0xcc, 0xcc, 0xcc)  # oddělovací linky
BILA       = RGBColor(0xFF, 0xFF, 0xFF)
AKCENT     = RGBColor(0x1f, 0x77, 0xb4)   # modrý akcent (odrážky, linky)
CERVENA    = RGBColor(0xc0, 0x20, 0x20)   # zamítnuto H0
ZELENA     = RGBColor(0x1a, 0x7a, 0x1a)   # nezamítnuto H0

# ── Prezentace 16:9 ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]   # prázdný layout


# ════════════════════════════════════════════════════════════════════════════
# POMOCNÉ FUNKCE
# ════════════════════════════════════════════════════════════════════════════

def novy_slide():
    """Přidá nový čistě bílý slide."""
    sl = prs.slides.add_slide(BLANK)
    # Explicitně nastavíme bílé pozadí (BLANK layout může mít zděděnou barvu)
    bg = sl.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BILA
    return sl


def textbox(slide, text, l, t, w, h,
            font_size=14, bold=False, italic=False,
            fg=TMAVA_SEDA, align=PP_ALIGN.LEFT, wrap=True):
    """Přidá textové pole na bílý slide."""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(font_size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = fg
    return txb


def linka(slide, l, t, w, tloustka=0.025, barva=SVETLA_SEDA):
    """Nakreslí tenkou horizontální linku (použita jako oddělovač pod nadpisem)."""
    sh = slide.shapes.add_shape(1,
         Inches(l), Inches(t), Inches(w), Inches(tloustka))
    sh.fill.solid()
    sh.fill.fore_color.rgb = barva
    sh.line.fill.background()


def pridej_obr(slide, soubor, l, t, sirka_palce):
    """
    Vloží obrázek ze složky vystupy/.
    ZADÁVÁME POUZE ŠÍŘKU – výška se dopočítá automaticky (bez deformace).
    """
    cesta = os.path.join(VYSTUPY, soubor)
    if not os.path.exists(cesta):
        print(f'  [WARN] Obrázek nenalezen: {soubor}')
        return None
    return slide.shapes.add_picture(
        cesta, Inches(l), Inches(t), width=Inches(sirka_palce)
    )


def hlavicka(slide, nadpis, podtitulek=None):
    """
    Minimalistická záhlaví: černý tučný text + tenká šedá linka.
    Bez barevného pruhu – čisté bílé pozadí.
    """
    textbox(slide, nadpis,
            0.35, 0.18, 12.6, 0.58,
            font_size=22, bold=True, fg=CERNA)
    if podtitulek:
        textbox(slide, podtitulek,
                0.35, 0.72, 12.6, 0.32,
                font_size=11, italic=True, fg=STRED_SEDA)
    # Tenká šedá linka pod nadpisem
    linka(slide, 0.35, 0.95, 12.63)


def cislo_slidu(slide, n, total=12):
    """Číslo slidu v pravém dolním rohu."""
    textbox(slide, f'{n} / {total}',
            12.45, 7.15, 0.8, 0.28,
            font_size=9, fg=STRED_SEDA, align=PP_ALIGN.RIGHT)


def odrazy(slide, body, l, t, w, h, font_size=13, fg=TMAVA_SEDA, bullet='▸'):
    """Přidá seznam odrážek."""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, bod in enumerate(body):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(5)
        r = p.add_run()
        r.text = f'{bullet}  {bod}'
        r.font.size = Pt(font_size)
        r.font.color.rgb = fg


def hyp_box(slide, l, t, w, h, h0_text, p_val, verdikt, zamita=True):
    """
    Jemný barevný rámeček s hypotézou, p-hodnotou a verdiktem.
    Zamítnuto → jemné červené pozadí. Nezamítnuto → jemné zelené.
    Ohraničení je vždy pouze lehce šedé (žádné výrazné rámy).
    """
    bg_barva = RGBColor(0xfd, 0xee, 0xee) if zamita else RGBColor(0xee, 0xf8, 0xee)
    fg_verd  = CERVENA if zamita else ZELENA
    zn       = '✕' if zamita else '✓'

    sh = slide.shapes.add_shape(
        1, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = bg_barva
    sh.line.color.rgb = SVETLA_SEDA   # jemné šedé ohraničení

    txb = slide.shapes.add_textbox(
        Inches(l + 0.12), Inches(t + 0.07), Inches(w - 0.24), Inches(h - 0.1))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True

    radky = [
        (f'H₀: {h0_text}', 10, False, TMAVA_SEDA),
        (f'p = {p_val}   |   α = 0,05', 10, False, STRED_SEDA),
        (f'{zn}  {verdikt}', 11, True, fg_verd),
    ]
    for i, (txt, sz, bd, col) in enumerate(radky):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(2)
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(sz)
        r.font.bold = bd
        r.font.color.rgb = col


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – TITULNÍ SNÍMEK
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()

textbox(slide, 'Střelecká úspěšnost ve fotbale',
        1.0, 1.6, 11.33, 1.0,
        font_size=36, bold=True, fg=CERNA, align=PP_ALIGN.CENTER)

textbox(slide, 'Vícerozměrná statistická analýza dat střel z anglické Premier League',
        1.0, 2.6, 11.33, 0.55,
        font_size=16, italic=True, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

linka(slide, 2.5, 3.25, 8.33, barva=AKCENT)

textbox(slide, 'VUT Brno  –  Vícerozměrné statistické metody (VMM)',
        1.0, 3.45, 11.33, 0.45,
        font_size=14, fg=TMAVA_SEDA, align=PP_ALIGN.CENTER)

textbox(slide, 'Akademický rok 2026/27   |   Semestrální projekt',
        1.0, 3.9, 11.33, 0.38,
        font_size=12, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

textbox(slide, 'Dataset: shots_outcome_Final.csv   |   Zdroj: understat.com',
        1.0, 6.9, 11.33, 0.35,
        font_size=10, fg=SVETLA_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(slide, 1)
print('  [OK] Slide 1: Titulní snímek')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – POPIS DATASETU
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Popis datasetu a cíl analýzy', 'shots_outcome_Final.csv – Premier League')

odrazy(slide, [
    'Dataset: střely z anglické Premier League (sezóny 2020–2022)',
    '1 000 záznamů (po vyřazení OwnGoal: 998 střel, 734 se souřadnicemi)',
    'Cílová proměnná: Gól = 1 / ostatní výsledky = 0  (podíl gólů ≈ 9 %)',
    'Sledované proměnné: X, Y, xG, vzdálenost, úhel, minuta, typ zakončení',
    'Vyřazena metadata: id, player_id, match_id, datum, názvy týmů',
], 0.45, 1.1, 6.2, 4.5, font_size=14)

# Přehledná tabulka proměnných
var_tab = [
    ('X, Y',       'Souřadnice střely (0–100)',      'Numerická'),
    ('dist_m',     'Vzdálenost od branky (odvozená)', 'Numerická'),
    ('angle_deg',  'Střelecký úhel (odvozený)',       'Numerická'),
    ('xG',         'Očekávaná pravděpodobnost gólu',  'Numerická'),
    ('minute',     'Minuta zápasu',                   'Numerická'),
    ('shotType',   'Typ zakončení (Foot / Head)',      'Kategorická'),
    ('goal',       'Cílová proměnná (1 = gól)',        'Binární'),
]
COL_X = [6.55, 9.0, 11.35]
COL_W = [2.45, 2.4,  1.75]
HDR   = ['Proměnná', 'Popis', 'Typ']
for j, (hdr, w) in enumerate(zip(HDR, COL_W)):
    sh = slide.shapes.add_shape(1, Inches(COL_X[j]), Inches(1.12), Inches(w), Inches(0.36))
    sh.fill.solid(); sh.fill.fore_color.rgb = AKCENT; sh.line.fill.background()
    textbox(slide, hdr, COL_X[j]+0.05, 1.14, w-0.1, 0.32,
            font_size=10, bold=True, fg=BILA)

for i, (var, popis, typ) in enumerate(var_tab):
    bg = RGBColor(0xf2, 0xf6, 0xfb) if i % 2 == 0 else BILA
    for j, (val, w) in enumerate(zip([var, popis, typ], COL_W)):
        sh = slide.shapes.add_shape(1, Inches(COL_X[j]), Inches(1.48 + i*0.55),
                                    Inches(w), Inches(0.5))
        sh.fill.solid(); sh.fill.fore_color.rgb = bg; sh.line.fill.background()
        textbox(slide, val, COL_X[j]+0.06, 1.52 + i*0.55, w-0.1, 0.42,
                font_size=10, fg=TMAVA_SEDA)

cislo_slidu(slide, 2)
print('  [OK] Slide 2: Popis datasetu')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – PŘEDZPRACOVÁNÍ + MAPA STŘEL
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Předzpracování dat', 'Čistění, škálování, pravidlo 3-sigma, mapa střel')

odrazy(slide, [
    'X, Y: škálování ×100 → fotbalové hřiště 100 × 100 jednotek',
    'Odvozeny: vzdálenost od branky (dist_m)  a  střelecký úhel (angle_deg)',
    'Chybějící X, Y: řádky vynechány (imputace průměrem by vytvořila falešné střely)',
    'Kategorické NaN: nahrazeny hodnotou „Bez asistence" / „Neznamy"',
    'Pravidlo 3-sigma: 1 odlehlá střela vyřazena (|Z(dist_m)| > 3)',
    'Finální analytická sada: n = 734 střel se souřadnicemi',
], 0.45, 1.1, 5.3, 4.5, font_size=13)

# Graf – pouze šířka, výška se dopočítá automaticky
pridej_obr(slide, '01_mapa_strel.png', 5.6, 1.08, 7.55)

cislo_slidu(slide, 3)
print('  [OK] Slide 3: Předzpracování')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – DIAGNOSTIKA NORMALITY
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Diagnostika normality', 'Shapiro-Wilk, Q-Q graf, Mahalanobis D²')

# Velký graf (histogram + Q-Q) vlevo
pridej_obr(slide, '02_normalita_histogramy_qq.png', 0.35, 1.08, 8.2)

# Hypotézy vpravo
hyp_box(slide, 8.7, 1.15, 4.5, 0.88,
        'xG pochází z normálního rozdělení',
        '6,3 × 10⁻³⁹', 'H₀ ZAMÍTÁME', zamita=True)
hyp_box(slide, 8.7, 2.15, 4.5, 0.88,
        'dist_m pochází z normálního rozdělení',
        '7,2 × 10⁻⁷', 'H₀ ZAMÍTÁME', zamita=True)
hyp_box(slide, 8.7, 3.15, 4.5, 0.88,
        'angle_deg pochází z normálního rozdělení',
        '6,3 × 10⁻²⁹', 'H₀ ZAMÍTÁME', zamita=True)

# Mahal diagram
pridej_obr(slide, '02b_mahal_chisq_qq.png', 8.7, 4.1, 4.5)

textbox(slide,
        '→ Normalita porušena u všech proměnných\n   → Robustní metody: Welch ANOVA, Spearman',
        8.7, 6.15, 4.5, 1.2, font_size=11, bold=True, fg=CERVENA)

cislo_slidu(slide, 4)
print('  [OK] Slide 4: Normalita')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – KORELAČNÍ ANALÝZA
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Vztahy mezi proměnnými', 'Spearmanova korelační analýza (robustní vůči non-normalitě)')

# Spearmanova heatmapa vlevo – velká a čitelná
pridej_obr(slide, '03_korelacni_heatmapa.png', 0.35, 1.08, 8.0)

odrazy(slide, [
    'H₀: Korelace = 0   |   H₁: Korelace ≠ 0',
    'xG ↔ dist_m:   r = −0,73  (čím blíže, tím vyšší xG)',
    'xG ↔ angle_deg:   r = +0,44  (větší úhel = lepší pozice)',
    'X ↔ dist_m:   r = −0,79  (bližší k brance = kratší vzdálenost)',
    'Y a minute:  bez výrazné korelace (r < 0,1)',
    '',
    'Všechny páry: p < 0,001 → H₀ ZAMÍTÁME',
], 8.45, 1.15, 4.7, 5.5, font_size=13)

cislo_slidu(slide, 5)
print('  [OK] Slide 5: Korelace')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – ANOVA + BOXPLOTY
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Rozdíly dle typu zakončení – Welchova ANOVA',
         'Výzkumná otázka: Liší se geometrie střely pro Foot vs. Head?')

pridej_obr(slide, '04_boxploty_shottype.png', 0.35, 1.08, 8.5)

odrazy(slide, [
    'Skupiny: RightFoot (n=285), LeftFoot (n=272), Head (n=48)',
    'H₀: Střední hodnoty jsou ve skupinách shodné',
    'Welchova ANOVA – robustní vůči heteroskedasticitě',
    '',
    'dist_m:    F = 193,0,  p < 0,001  →  H₀ ZAMÍTÁME',
    'angle_deg: F = 39,1,   p < 0,001  →  H₀ ZAMÍTÁME',
    '',
    '→ Hlavičky stříleny z větší vzdálenosti a horšího úhlu',
], 8.85, 1.15, 4.3, 5.6, font_size=13)

cislo_slidu(slide, 6)
print('  [OK] Slide 6: ANOVA')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – MANOVA + TUKEY
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'MANOVA a Tukeyho post-hoc test',
         'Vícerozměrné porovnání skupin – sdružený test (dist_m + angle_deg)')

odrazy(slide, [
    'MANOVA zachycuje korelaci mezi dist_m a angle_deg → silnější test',
    'H₀: Vektory středních hodnot jsou pro všechny skupiny shodné',
    '',
    'Wilksova lambda:  p = 4,4 × 10⁻²⁷  →  H₀ ZAMÍTÁME',
], 0.45, 1.1, 7.5, 2.5, font_size=14)

hyp_box(slide, 0.45, 3.0, 7.5, 0.88,
        'Vektory středních hodnot (dist_m, angle_deg) jsou shodné (MANOVA)',
        '4,4 × 10⁻²⁷ (Wilks λ)', 'H₀ ZAMÍTÁME', zamita=True)

textbox(slide, 'Tukeyho HSD post-hoc test – konkrétní páry:', 0.45, 4.1, 7.5, 0.38,
        font_size=13, bold=True, fg=CERNA)

# Tabulka post-hoc výsledků
post_hoc = [
    ('Head  vs.  LeftFoot',  'dist_m: Δ = +10,2 j.',   'angle: Δ = −21,4°', 'p < 0,001', True),
    ('Head  vs.  RightFoot', 'dist_m: Δ = +11,1 j.',   'angle: Δ = −22,0°', 'p < 0,001', True),
    ('LeftFoot  vs.  RightFoot', 'dist_m: Δ ≈ 0,9 j.', 'angle: Δ ≈ −0,7°', 'p = 0,22 / 0,83', False),
]
for i, (par, d1, d2, pv, zam) in enumerate(post_hoc):
    bg = RGBColor(0xfd, 0xee, 0xee) if zam else RGBColor(0xee, 0xf8, 0xee)
    fg_p = CERVENA if zam else ZELENA
    sh = slide.shapes.add_shape(1, Inches(0.45), Inches(4.57 + i*0.77),
                                Inches(7.5), Inches(0.68))
    sh.fill.solid(); sh.fill.fore_color.rgb = bg; sh.line.color.rgb = SVETLA_SEDA
    textbox(slide, f'{par}   {d1}   {d2}   {pv}',
            0.6, 4.63 + i*0.77, 7.2, 0.55, font_size=11, fg=TMAVA_SEDA)

odrazy(slide, [
    'Zakončení nohou (pravou vs. levou): bez statisticky významného rozdílu',
    'Zakončení hlavou: výrazně větší vzdálenost, menší úhel → nižší šance na gól',
], 0.45, 6.95, 12.5, 0.9, font_size=12, fg=STRED_SEDA, bullet='→')

cislo_slidu(slide, 7)
print('  [OK] Slide 7: MANOVA + Tukey')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 – PCA
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Redukce dimenzionality – PCA',
         'Bartlettův test sférickosti, KMO, Scree plot, biplot')

pridej_obr(slide, '05_scree_plot.png',  0.35, 1.1, 6.2)
pridej_obr(slide, '05b_biplot_pca.png', 6.7,  1.1, 6.5)

hyp_box(slide, 0.35, 5.25, 6.2, 0.85,
        'Korelační matice je jednotková – PCA nevhodná',
        '≈ 0 (χ² = 2041, df = 15)', 'H₀ ZAMÍTÁME → PCA vhodná', zamita=True)

odrazy(slide, [
    'KMO = 0,62  (přijatelné pro PCA)',
    'Kaiserovo pravidlo (λ > 1): 2 hlavní komponenty',
    'PC1 ≈ „osa kvality pozice" (xG, dist_m, angle_deg)',
    'PC1 + PC2: vysvětlují ~ 70 % celkového rozptylu',
], 6.7, 5.2, 6.5, 2.2, font_size=12)

cislo_slidu(slide, 8)
print('  [OK] Slide 8: PCA')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 – SHLUKOVÁ ANALÝZA
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Shluková analýza',
         'Hierarchické shlukování (Ward) + K-means k = 2')

pridej_obr(slide, '06_dendrogram.png',   0.35, 1.1,  6.2)
pridej_obr(slide, '06b_mapa_shluku.png', 6.7,  1.1,  6.5)

odrazy(slide, [
    'H₀: Střely tvoří homogenní rozdělení (žádné shluky)',
    'Wardův dendrogram: přirozený řez na k = 2',
    '',
    'Shluk 1 – Blízká střela (vápno):  průměrná vzdálenost ≈ 13 j.',
    '   → Vyšší xG, větší střelecký úhel, vyšší % gólů',
    'Shluk 2 – Střelba z dálky:  průměrná vzdálenost ≈ 25 j.',
    '   → Nízká xG, malý úhel, nízké % gólů',
    '',
    '→ H₁ potvrzena: data mají přirozenou shlukovou strukturu',
], 0.35, 5.3, 12.9, 2.1, font_size=12)

cislo_slidu(slide, 9)
print('  [OK] Slide 9: Shlukování')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 – LOGISTICKÁ REGRESE
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Predikce gólu – logistická regrese',
         'Binární cíl: gól (1) / bez gólu (0)  |  Prediktory: dist_m, angle_deg, xG, minute')

pridej_obr(slide, '07_roc_krivka.png',   0.35, 1.1, 5.8)
pridej_obr(slide, '07b_forest_plot.png', 6.3,  1.1, 6.9)

hyp_box(slide, 0.35, 5.5, 12.6, 0.85,
        'Žádný parametr neovlivňuje šanci na gól (všechna β = 0)',
        '< 0,001 (LRT)', 'H₀ ZAMÍTÁME', zamita=True)

odrazy(slide, [
    'AUC = 0,78  →  model výrazně lepší než náhodný odhad (0,50)',
    'xG (OR ≈ 76):  nejsilnější prediktor – jak se fyzikálně očekávalo',
    'dist_m (OR ≈ 0,92):  větší vzdálenost → nižší šance na gól  (p = 0,029)',
    'minute (OR ≈ 1,01):  gól mírně pravděpodobnější v pozdějších minutách (p = 0,022)',
], 0.35, 6.45, 12.6, 0.95, font_size=11)

cislo_slidu(slide, 10)
print('  [OK] Slide 10: Logistická regrese')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 – SOUHRNNÁ TABULKA HYPOTÉZ
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Souhrnná tabulka testovaných hypotéz',
         'Přehled všech statistických testů  |  α = 0,05')

rows = [
    ('Shapiro-Wilk',         'xG ~ N(μ,σ²)',                   '6,3e−39', '0,05', 'ZAMÍTÁME',    True),
    ('Shapiro-Wilk',         'dist_m ~ N(μ,σ²)',               '7,2e−7',  '0,05', 'ZAMÍTÁME',    True),
    ('Shapiro-Wilk',         'angle_deg ~ N(μ,σ²)',            '6,3e−29', '0,05', 'ZAMÍTÁME',    True),
    ('Levene',               'Rozptyly dist_m jsou shodné',    '4,5e−7',  '0,05', 'ZAMÍTÁME',    True),
    ('Spearman r',           'r(xG, dist_m) = 0',              '< 0,001', '0,05', 'ZAMÍTÁME',    True),
    ('Welch ANOVA (dist_m)', 'Střed. vzdálenosti jsou shodné', '7,5e−46', '0,05', 'ZAMÍTÁME',    True),
    ('Welch ANOVA (angle)',  'Střed. úhly jsou shodné',        '6,3e−14', '0,05', 'ZAMÍTÁME',    True),
    ('MANOVA (Wilks λ)',     'Vektory středních = shodné',     '4,4e−27', '0,05', 'ZAMÍTÁME',    True),
    ('Bartlettův test',      'Kor. matice = I (PCA nevhodná)', '≈ 0',     '0,05', 'ZAMÍTÁME',    True),
    ('Logit (dist_m)',       'β_dist = 0',                     '0,029',   '0,05', 'ZAMÍTÁME',    True),
    ('Logit (xG)',           'β_xG = 0',                       '4,7e−6',  '0,05', 'ZAMÍTÁME',    True),
]

CX  = [0.30, 3.00, 6.90, 8.60, 10.10, 12.0]
CW  = [2.65, 3.85, 1.65, 1.45,  1.85,  1.0]
HDR2 = ['Test', 'H₀', 'p-hodnota', 'α', 'Verdikt', '']

# Záhlaví tabulky
for j, (hdr, w) in enumerate(zip(HDR2, CW)):
    sh = slide.shapes.add_shape(1, Inches(CX[j]), Inches(1.1), Inches(w), Inches(0.35))
    sh.fill.solid(); sh.fill.fore_color.rgb = CERNA; sh.line.fill.background()
    textbox(slide, hdr, CX[j]+0.04, 1.12, w-0.08, 0.3,
            font_size=9, bold=True, fg=BILA, align=PP_ALIGN.CENTER)

# Řádky
for i, (test, h0, pv, al, verd, zam) in enumerate(rows):
    bg = RGBColor(0xfd, 0xf0, 0xf0) if zam else RGBColor(0xf0, 0xfb, 0xf0)
    fg_v = CERVENA if zam else ZELENA
    bg_alt = RGBColor(0xfa, 0xf0, 0xf0) if (zam and i % 2 == 1) else \
             (RGBColor(0xf5, 0xf5, 0xf5) if not zam and i % 2 == 1 else bg)
    vals = [test, h0, pv, al, f'✕ {verd}' if zam else f'✓ {verd}', '']
    for j, (val, w) in enumerate(zip(vals, CW)):
        sh = slide.shapes.add_shape(1, Inches(CX[j]), Inches(1.45 + i*0.52),
                                    Inches(w), Inches(0.48))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg_alt
        sh.line.fill.background()
        fgc = fg_v if j == 4 else TMAVA_SEDA
        textbox(slide, val, CX[j]+0.05, 1.5 + i*0.52, w-0.08, 0.38,
                font_size=9, fg=fgc)

cislo_slidu(slide, 11)
print('  [OK] Slide 11: Souhrnná tabulka hypotéz')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 – ZÁVĚR A INTERPRETACE
# ════════════════════════════════════════════════════════════════════════════
slide = novy_slide()
hlavicka(slide, 'Závěr a fotbalová interpretace',
         'Co analýza říká trenérům a analytikům?')

zaver = [
    'Vzdálenost a úhel střely jsou klíčové prediktory úspěšnosti – potvrzen statistický vliv (ANOVA, MANOVA, Logit)',
    'Typ zakončení (noha vs. hlava) statisticky významně ovlivňuje geometrii střely – hlavičky z horšíche pozic',
    'PCA: „osa kvality střelecké pozice" (PC1 = xG, dist_m, angle_deg) vysvětluje ~ 50 % variability',
    'Shluková analýza potvrdila dva herní profily: střely z vápna (xG > 15 %) vs. střelba z dálky (xG < 5 %)',
    'Logistická regrese: AUC = 0,78 – spolehlivá predikce gólu z fyzikálních parametrů střely',
    'Doporučení pro trenéry: soustřeďte zakončení na střely z I. třetiny vápna s úhlem > 30° → výrazně vyšší xG',
]

for i, bod in enumerate(zaver):
    # Střídající se světlé pruhy pro lepší čitelnost
    bg_c = RGBColor(0xf2, 0xf6, 0xfb) if i % 2 == 0 else BILA
    sh = slide.shapes.add_shape(1, Inches(0.35), Inches(1.1 + i*0.92),
                                Inches(12.63), Inches(0.83))
    sh.fill.solid(); sh.fill.fore_color.rgb = bg_c; sh.line.fill.background()
    # Modrý akcent vlevo
    sh2 = slide.shapes.add_shape(1, Inches(0.35), Inches(1.1 + i*0.92),
                                 Inches(0.07), Inches(0.83))
    sh2.fill.solid(); sh2.fill.fore_color.rgb = AKCENT; sh2.line.fill.background()
    textbox(slide, bod, 0.55, 1.16 + i*0.92, 12.2, 0.7, font_size=12, fg=TMAVA_SEDA)

textbox(slide, 'Děkuji za pozornost   |   MPC VMM 2026/27   |   VUT Brno',
        0.35, 6.95, 12.63, 0.38,
        font_size=10, fg=SVETLA_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(slide, 12)
print('  [OK] Slide 12: Závěr')


# ════════════════════════════════════════════════════════════════════════════
# ULOŽENÍ
# ════════════════════════════════════════════════════════════════════════════
prs.save(PPTX_OUT)
print(f'\n[OK] Prezentace uložena: {PPTX_OUT}')
print(f'     Počet slidů: {len(prs.slides)}')
