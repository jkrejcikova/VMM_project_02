# -*- coding: utf-8 -*-
# =============================================================================
# SKRIPT PRO GENEROVÁNÍ PREZENTACE (PowerPoint PPTX)
# Semestrální projekt VMM – Střelecká úspěšnost (Premier League)
# 13 SLIDŮ: Čistě BÍLÉ pozadí (#FFFFFF), dominantní grafy na celou šířku (10.8")
# =============================================================================

import os
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Cesty ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VYSTUPY_DIR = os.path.join(BASE_DIR, 'vystupy')
PPTX_PATH = os.path.join(BASE_DIR, 'prezentace', 'prezentace_strelecka_uspesnost.pptx')
os.makedirs(os.path.join(BASE_DIR, 'prezentace'), exist_ok=True)

# ── Barevná paleta pro čistý bílý styl ──────────────────────────────────────
BILA         = RGBColor(0xFF, 0xFF, 0xFF)   # #FFFFFF – Čistě bílé pozadí
CERNA        = RGBColor(0x1A, 0x1A, 0x1A)   # #1A1A1A – Hlavní nadpisy
TMAVA_SEDA   = RGBColor(0x33, 0x33, 0x33)   # #333333 – Běžný text
STRED_SEDA   = RGBColor(0x66, 0x66, 0x66)   # #666666 – Doplňující text, čísla slidů
SVETLA_SEDA  = RGBColor(0xD8, 0xD8, 0xD8)   # #D8D8D8 – Oddělovací linky
CERVENA_ZAM  = RGBColor(0xC5, 0x30, 0x30)   # #C53030 – Zamítnutí H0
ZELENA_NEZAM = RGBColor(0x27, 0x67, 0x49)   # #276749 – Nezamítnutí H0
MODRA_BOD    = RGBColor(0x1F, 0x77, 0xB4)   # #1F77B4 – Akcentní modrá

# ── Prezentace 16:9 ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]   # Čisté prázdné rozvržení


# ════════════════════════════════════════════════════════════════════════════
# POMOCNÉ FUNKCE
# ════════════════════════════════════════════════════════════════════════════

def novy_slide():
    """Vytvoří nový snímek s garantovaným čistě BÍLÝM pozadím (#FFFFFF)."""
    sl = prs.slides.add_slide(BLANK)
    bg = sl.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BILA
    return sl


def text_pole(slide, text, l, t, w, h,
              font_size=13, bold=False, italic=False,
              fg=TMAVA_SEDA, align=PP_ALIGN.LEFT, wrap=True):
    """Vloží textové pole na snímek."""
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


def linka(slide, l, t, w, tloustka=0.015, barva=SVETLA_SEDA):
    """Vykreslí tenkou decentní linku."""
    sh = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(tloustka))
    sh.fill.solid()
    sh.fill.fore_color.rgb = barva
    sh.line.fill.background()
    return sh


def zahlavi(slide, nadpis, podtitulek=None):
    """
    Standardní čisté záhlaví:
    Černý tučný nadpis vlevo nahoře (20 pt) + tenká linka pod ním.
    """
    text_pole(slide, nadpis, 0.8, 0.32, 11.73, 0.42,
              font_size=20, bold=True, fg=CERNA)
    if podtitulek:
        text_pole(slide, podtitulek, 0.8, 0.72, 11.73, 0.28,
                  font_size=10.5, italic=True, fg=STRED_SEDA)
        linka(slide, 0.8, 1.02, 11.73)
    else:
        linka(slide, 0.8, 0.82, 11.73)


def cislo_slidu(slide, n, total=13):
    """Vloží číslo snímku v pravém dolním rohu."""
    text_pole(slide, f'{n} / {total}', 12.0, 7.10, 0.8, 0.25,
              font_size=9, fg=STRED_SEDA, align=PP_ALIGN.RIGHT)


def vloz_dominantni_graf(slide, soubor, l=1.26, t=0.92, sirka_palce=10.8):
    """
    Vloží dominantní vycentrovaný graf s šířkou 10.8 palce:
    ZADÁVÁME POUZE ŠÍŘKU! Výška je dopočítána automaticky bez deformace poměru stran.
    """
    cesta = os.path.join(VYSTUPY_DIR, soubor)
    if not os.path.exists(cesta):
        print(f'  [VAROVÁNÍ] Obrázek nenalezen: {soubor}')
        return None
    return slide.shapes.add_picture(cesta, Inches(l), Inches(t), width=Inches(sirka_palce))


def fotbalovy_zaver_box(slide, text_zaveru, text_verdiktu=None, l=0.8, t=6.48, w=11.73, h=0.58):
    """
    Vloží 1-2 stručné řádky s fotbalovým závěrem a statistickým verdiktem pod dominantní graf.
    """
    sh = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
    sh.line.color.rgb = SVETLA_SEDA
    sh.line.width = Pt(1)

    # Modrý dekorační proužek vlevo
    sh_strip = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(0.08), Inches(h))
    sh_strip.fill.solid()
    sh_strip.fill.fore_color.rgb = MODRA_BOD
    sh_strip.line.fill.background()

    txb = slide.shapes.add_textbox(Inches(l + 0.2), Inches(t + 0.06), Inches(w - 0.35), Inches(h - 0.12))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    r_tag = p.add_run()
    r_tag.text = 'Fotbalový závěr: '
    r_tag.font.bold = True
    r_tag.font.size = Pt(12)
    r_tag.font.color.rgb = CERNA

    r_txt = p.add_run()
    r_txt.text = text_zaveru
    r_txt.font.size = Pt(12)
    r_txt.font.color.rgb = TMAVA_SEDA

    if text_verdiktu:
        r_ver = p.add_run()
        r_ver.text = f'  |  {text_verdiktu}'
        r_ver.font.bold = True
        r_ver.font.size = Pt(12)
        r_ver.font.color.rgb = CERVENA_ZAM


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – TITULNÍ SNÍMEK
# ════════════════════════════════════════════════════════════════════════════
s1 = novy_slide()

text_pole(s1, 'Střelecká úspěšnost ve fotbale',
          0.8, 1.8, 11.73, 1.1,
          font_size=36, bold=True, fg=CERNA, align=PP_ALIGN.CENTER)

text_pole(s1, 'Vícerozměrná statistická analýza dat střel z anglické Premier League',
          0.8, 2.85, 11.73, 0.6,
          font_size=16, italic=True, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

linka(s1, 3.0, 3.65, 7.33, tloustka=0.02, barva=MODRA_BOD)

text_pole(s1, 'Vysoké učení technické v Brně  •  Vícerozměrné statistické metody (VMM)',
          0.8, 3.95, 11.73, 0.45,
          font_size=14, bold=True, fg=TMAVA_SEDA, align=PP_ALIGN.CENTER)

text_pole(s1, 'Semestrální projekt  •  Akademický rok 2026/27',
          0.8, 4.45, 11.73, 0.4,
          font_size=12, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

text_pole(s1, 'Zdroj dat: shots_outcome_Final.csv (understat.com)',
          0.8, 6.75, 11.73, 0.35,
          font_size=10, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(s1, 1)
print('  [OK] Slide 1: Titulní snímek vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – PŘEDSTAVENÍ DAT A PROMĚNNÝCH (ČISTĚ TEXTOVÝ, BEZ GRAFU)
# ════════════════════════════════════════════════════════════════════════════
s2 = novy_slide()
zahlavi(s2, 'Představení datového vzorku a proměnných',
        'Základní popis analyzované datové sady z Premier League a vymezení cílů výzkumu')

# Horní polovina: Popis vzorku a cíl práce ve 2 elegantních kartách
# Karta 1: Datový vzorek
sh1 = s2.shapes.add_shape(1, Inches(0.8), Inches(1.2), Inches(5.7), Inches(1.85))
sh1.fill.solid(); sh1.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
sh1.line.color.rgb = SVETLA_SEDA; sh1.line.width = Pt(1)
sh1_str = s2.shapes.add_shape(1, Inches(0.8), Inches(1.2), Inches(0.08), Inches(1.85))
sh1_str.fill.solid(); sh1_str.fill.fore_color.rgb = MODRA_BOD; sh1_str.line.fill.background()

text_pole(s2, 'Datový vzorek (Premier League)', 1.05, 1.30, 5.3, 0.35, font_size=13, bold=True, fg=CERNA)
text_pole(s2, '• Celkem 1 000 zaznamenaných střel (databáze understat.com).\n'
              '• 998 střel po vyřazení vlastních branek (OwnGoal).\n'
              '• 734 střel s kompletními prostorovými souřadnicemi (X, Y) po věcném vyřazení chybějících údajů a aplikaci pravidla 3-sigma na dist_m.\n'
              '• Podíl gólů v čisté sadě činí 9,0 % (66 branek vs. 668 nezakončených).',
          1.05, 1.65, 5.3, 1.30, font_size=11, fg=TMAVA_SEDA)

# Karta 2: Cíl projektu
sh2 = s2.shapes.add_shape(1, Inches(6.8), Inches(1.2), Inches(5.7), Inches(1.85))
sh2.fill.solid(); sh2.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
sh2.line.color.rgb = SVETLA_SEDA; sh2.line.width = Pt(1)
sh2_str = s2.shapes.add_shape(1, Inches(6.8), Inches(1.2), Inches(0.08), Inches(1.85))
sh2_str.fill.solid(); sh2_str.fill.fore_color.rgb = MODRA_BOD; sh2_str.line.fill.background()

text_pole(s2, 'Cíl semestrální práce & hypotéza', 7.05, 1.30, 5.3, 0.35, font_size=13, bold=True, fg=CERNA)
text_pole(s2, '• Identifikovat klíčové prostorové a geometrické faktory ovlivňující úspěšnost fotbalového zakončení.\n'
              '• Ověřit statistickou významnost rozdílů mezi typy zakončení (noha vs. hlava) a odhalit skryté faktory pozice.\n'
              '• H₀: Pravděpodobnost vstřelení gólu je nezávislá na poloze a geometrii střely na hřišti.\n'
              '• Využití postupného metodického aparátu od EDA po logistickou regresi.',
          7.05, 1.65, 5.3, 1.30, font_size=11, fg=TMAVA_SEDA)

# Dolní polovina: Přehledná tabulka proměnných
text_pole(s2, 'Přehled sledovaných a odvozených proměnných:', 0.8, 3.25, 11.73, 0.32, font_size=12, bold=True, fg=CERNA)

promenne_tab = [
    ('X, Y', 'Prostorové souřadnice zakončení na hřišti (přeškálováno na 0–100 % délky a šířky)', 'Spojitá', '0,0 až 100,0 %'),
    ('dist_m', 'Odvozená Eukleidovská vzdálenost střely od středu branky [X=100, Y=50]', 'Spojitá', '2,7 až 41,7 j.'),
    ('angle_deg', 'Odvozený střelecký zorný úhel sevřený brankovými tyčemi', 'Spojitá', '4,0° až 121,3°'),
    ('xG', 'Očekávaná pravděpodobnost vstřelení gólu (Expected Goals model)', 'Spojitá', '0,01 až 0,76'),
    ('minute', 'Minuta utkání, ve které byla střela vyslána', 'Diskrétní', '0 až 96 min'),
    ('shotType', 'Způsob zakončení: Pravá noha (n=285), Levá noha (n=272), Hlava (n=48)', 'Kategorická', 'Right / Left / Head'),
    ('goal', 'Cílová binární proměnná úspěšnosti (1 = Gól / 66 střel, 0 = Bez gólu / 668 střel)', 'Binární', '0 nebo 1'),
]

TAB_X = [0.8, 2.2, 9.0, 10.7]
TAB_W = [1.3, 6.7, 1.6, 1.8]
TAB_HDR = ['Proměnná', 'Význam a definice metriky', 'Datový typ', 'Rozsah hodnot']

# Záhlaví tabulky
for j, (h_txt, w_c) in enumerate(zip(TAB_HDR, TAB_W)):
    sh = s2.shapes.add_shape(1, Inches(TAB_X[j]), Inches(3.60), Inches(w_c), Inches(0.34))
    sh.fill.solid(); sh.fill.fore_color.rgb = CERNA; sh.line.fill.background()
    text_pole(s2, h_txt, TAB_X[j] + 0.05, 3.63, w_c - 0.1, 0.28,
              font_size=9.5, bold=True, fg=BILA, align=PP_ALIGN.CENTER if j in [0, 2, 3] else PP_ALIGN.LEFT)

# Řádky tabulky
for i, radek in enumerate(promenne_tab):
    y_r = 3.96 + (i * 0.38)
    bg_r = RGBColor(0xFA, 0xFA, 0xFA) if (i % 2 == 0) else BILA
    for j, (val, w_c) in enumerate(zip(radek, TAB_W)):
        sh = s2.shapes.add_shape(1, Inches(TAB_X[j]), Inches(y_r), Inches(w_c), Inches(0.36))
        sh.fill.solid(); sh.fill.fore_color.rgb = bg_r
        sh.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE); sh.line.width = Pt(0.5)
        text_pole(s2, val, TAB_X[j] + 0.05, y_r + 0.04, w_c - 0.1, 0.28,
                  font_size=9, bold=(j == 0), fg=TMAVA_SEDA,
                  align=PP_ALIGN.CENTER if j in [0, 2, 3] else PP_ALIGN.LEFT)

cislo_slidu(s2, 2)
print('  [OK] Slide 2: Představení dat vytvořeno (čistě textový slide)')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – MAPA STŘEL NA CELÉM HŘIŠTI
# ════════════════════════════════════════════════════════════════════════════
s3 = novy_slide()
zahlavi(s3, 'Mapa střel na celém fotbalovém hřišti (100 × 100 jednotek)')
vloz_dominantni_graf(s3, '01_mapa_strel.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s3,
    'Góly (červené body) jsou soustředěny v prostoru pokutového území v těsné blízkosti branky; střelba z velké vzdálenosti má minimální konverzi.',
    'Sada: n = 734 | Gól: 66 (9.0 %) | Z-skóre dist_m < 3')
cislo_slidu(s3, 3)
print('  [OK] Slide 3: Mapa střel vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – 2D KDE HUSTOTA STŘELBY NA HŘIŠTI
# ════════════════════════════════════════════════════════════════════════════
s4 = novy_slide()
zahlavi(s4, '2D KDE hustota střelby na hřišti (Vrstevnice zakončení)')
vloz_dominantni_graf(s4, '01c_kde_hriste.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s4,
    'Jádro úspěšných střel (červené vrstevnice) je lokalizováno přímo v ose před brankou (malé vápno), zatímco neproměněné střely vykazují široký rozptyl.',
    'Přednáška VMM-3/VMM-4 (Plynulé 2D hustoty pravděpodobnosti)')
cislo_slidu(s4, 4)
print('  [OK] Slide 4: 2D KDE vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – DIAGNOSTIKA NORMALITY
# ════════════════════════════════════════════════════════════════════════════
s5 = novy_slide()
zahlavi(s5, 'Diagnostika normality & předpokladů (dist_m)')
vloz_dominantni_graf(s5, '02_normalita_histogramy_qq.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s5,
    'Shapiro-Wilkův test (p < 0.001) i Leveneho test heteroskedasticity (p < 0.001) prokazují porušení předpokladů normality a rovnosti rozptylů.',
    'Shapiro-Wilk W = 0.984, p = 7.15e-07 -> H0 ZAMÍTNUTA (nutné robustní metody)')
cislo_slidu(s5, 5)
print('  [OK] Slide 5: Diagnostika normality vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – SPEARMANOVA KORELAČNÍ HEATMAPA
# ════════════════════════════════════════════════════════════════════════════
s6 = novy_slide()
zahlavi(s6, 'Spearmanova korelační analýza (Plná matice)')
vloz_dominantni_graf(s6, '03_korelacni_heatmapa.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s6,
    'Silná záporná závislost mezi vzdáleností a xG (r = -0.73, p < 0.001) potvrzuje, že větší vzdálenost dramaticky sráží kvalitu střelecké příležitosti.',
    'Test r = 0: t = -29.14, p < 0.001 -> H0 ZAMÍTNUTA')
cislo_slidu(s6, 6)
print('  [OK] Slide 6: Korelační matice vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – PAIR-PLOT VZTAHŮ KLÍČOVÝCH PROMĚNNÝCH
# ════════════════════════════════════════════════════════════════════════════
s7 = novy_slide()
zahlavi(s7, 'Párové rozptylové diagramy a marginální hustoty (KDE)')
vloz_dominantni_graf(s7, '03b_pairplot.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s7,
    'Marginální KDE křivky na diagonále i 2D projekce jasně separují góly (červená) v zóně krátkých vzdáleností (dist_m < 15) a vysokých úhlů (angle > 30°).',
    'Přednáška VMM-4 (Multivariátní zkoumání vztahů s KDE diagonálou)')
cislo_slidu(s7, 7)
print('  [OK] Slide 7: Pair-plot vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 – ANOVA: ROZDÍLY DLE ZAKONČENÍ
# ════════════════════════════════════════════════════════════════════════════
s8 = novy_slide()
zahlavi(s8, 'Rozdíly geometrie střely dle typu zakončení (ANOVA)')
vloz_dominantni_graf(s8, '04_boxploty_shottype.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s8,
    'Zakončení hlavou probíhá z výrazně odlišných prostorových parametrů než střelba nohou (jak z hlediska vzdálenosti, tak z pohledu střeleckého úhlu).',
    'Welchova ANOVA dist_m: F = 193.0, p = 7.47e-46 -> H0 ZAMÍTNUTA')
cislo_slidu(s8, 8)
print('  [OK] Slide 8: ANOVA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 – MANOVA & TUKEY HSD POST-HOC TEST
# ════════════════════════════════════════════════════════════════════════════
s9 = novy_slide()
zahlavi(s9, 'Vícerozměrné posouzení sdruženého vektoru (MANOVA & Tukey)')
vloz_dominantni_graf(s9, '04b_tukey_hsd.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s9,
    'Zakončení hlavou se signifikantně liší od obou nohou (Δ dist ≈ +11 j., Δ úhel ≈ -22°); mezi pravou a levou nohou nebyl nalezen významný rozdíl (p = 0.22).',
    'MANOVA Wilks\' λ = 0.806, p = 4.44e-27 -> H0 ZAMÍTNUTA')
cislo_slidu(s9, 9)
print('  [OK] Slide 9: MANOVA & Tukey vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 – REDUKCE DIMENZIONALITY PCA
# ════════════════════════════════════════════════════════════════════════════
s10 = novy_slide()
zahlavi(s10, 'Redukce dimenzionality PCA (Scree plot & Biplot)')
vloz_dominantni_graf(s10, '05b_biplot_pca.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s10,
    'První hlavní komponenta PC1 (~48 % rozptylu) definuje osu kvality střelecké pozice (vzdálenost vs. úhel a xG); 2 komponenty zachycují ~68 % variability.',
    'Bartlettův test sférickosti: χ² = 2041.4, p < 0.001 -> H0 ZAMÍTNUTA (PCA je vhodná)')
cislo_slidu(s10, 10)
print('  [OK] Slide 10: PCA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 – FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX
# ════════════════════════════════════════════════════════════════════════════
s11 = novy_slide()
zahlavi(s11, 'Faktorová analýza s rotací Varimax (Latentní faktory)')
vloz_dominantni_graf(s11, '05c_fa_varimax_loadings.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s11,
    'Faktorová analýza s rotací Varimax odhalila 2 nezávislé latentní dimenze: F1 = Čistá kvalita střeleckého úhlu a xG, F2 = Herní hloubka a postup po ose X.',
    'Přednáška VMM-9 (Faktorová analýza a ortogonální rotace Varimax)')
cislo_slidu(s11, 11)
print('  [OK] Slide 11: Faktorová analýza vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 – LOGISTICKÁ REGRESE (SIGMOIDÁLNÍ KŘIVKA & ROC)
# ════════════════════════════════════════════════════════════════════════════
s12 = novy_slide()
zahlavi(s12, 'Logistická regrese: Křivka pravděpodobnosti gólu & ROC křivka')
vloz_dominantni_graf(s12, '07b_logisticka_krivka.png', l=1.26, t=0.92, sirka_palce=10.8)
fotbalovy_zaver_box(s12,
    'Při vzdálenosti 10 m je šance na gól ~25 %, na 25 m klesá pod 3 % (OR = 0.922 na metr, p = 0.029). Model dosahuje výborné diskriminace (AUC = 0.784, VIF < 3).',
    'Globální test LLR: χ² = 82.1, p = 6.17e-17 -> H0 ZAMÍTNUTA')
cislo_slidu(s12, 12)
print('  [OK] Slide 12: Logistická regrese vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 13 – SOUHRNNÁ TABULKA HYPOTÉZ & DOPORUČENÍ PRO TRENÉRY
# ════════════════════════════════════════════════════════════════════════════
s13 = novy_slide()
zahlavi(s13, 'Souhrnná tabulka testovaných hypotéz & doporučení pro trenéry')

# Horní část: Přehledná tabulka všech 12 hypotéz (kompaktní, na celou šířku)
tabulka_hyp_data = [
    ('3 – Normalita', 'Shapiro-Wilk (dist_m)', 'dist_m pochází z normálního rozdělení', 'W = 0.9842', '7.15e-07', 'ZAMÍTÁME H₀', True),
    ('3 – Normalita', 'Shapiro-Wilk (xG)', 'xG pochází z normálního rozdělení', 'W = 0.5485', '6.34e-39', 'ZAMÍTÁME H₀', True),
    ('3 – Rozptyly', 'Leveneho test', 'Rozptyly vzdálenosti jsou ve skupinách shodné', 'L = 10.997', '4.55e-07', 'ZAMÍTÁME H₀', True),
    ('4 – Závislost', 'Spearmanův test', 'Korelace mezi xG a dist_m je nulová (r = 0)', 'r = -0.732', '< 0.001', 'ZAMÍTÁME H₀', True),
    ('5 – Rozdíly', 'Welch ANOVA (dist_m)', 'Střední vzdálenosti jsou pro typy zakončení stejné', 'F = 193.0', '7.47e-46', 'ZAMÍTÁME H₀', True),
    ('5 – Rozdíly', 'Welch ANOVA (angle)', 'Střední úhly jsou pro typy zakončení stejné', 'F = 39.06', '6.33e-14', 'ZAMÍTÁME H₀', True),
    ('6 – Sdružené', 'MANOVA (Wilks λ)', 'Vektory středních hodnot jsou ve skupinách shodné', 'λ = 0.806', '4.44e-27', 'ZAMÍTÁME H₀', True),
    ('7 – PCA', 'Bartlettův test', 'Korelační matice je jednotková (PCA nevhodná)', 'χ² = 2041.4', '< 0.001', 'ZAMÍTÁME H₀', True),
    ('8 – Multikol.', 'Test VIF', 'Prediktory netrpí multikolinearitou (VIF < 5)', 'max VIF = 2.87', 'VIF < 5', 'NEZAMÍTÁME H₀', False),
    ('9 – Regrese', 'Logit (dist_m)', 'Vzdálenost střely neovlivňuje šanci na gól (β = 0)', 'z = -2.18', '0.0294', 'ZAMÍTÁME H₀', True),
    ('9 – Regrese', 'Logit (xG)', 'Metrika xG neovlivňuje šanci na gól (β = 0)', 'z = 4.58', '4.68e-06', 'ZAMÍTÁME H₀', True),
    ('10 – Shluky', 'Wardovo shlukování', 'Střely tvoří homogenní rozdělení bez shluků', 'Ward d² k=2', '< 0.001', 'ZAMÍTÁME H₀', True),
]

SLOUPCE_X = [0.8, 2.2, 4.3, 8.2, 9.7, 10.9]
SLOUPCE_W = [1.3, 2.0, 3.8, 1.4, 1.1, 1.63]
HLAVICKY  = ['Fáze', 'Metoda', 'Nulová hypotéza (H₀)', 'Statistika', 'p-hodnota', 'Rozhodnutí']

for j, (h_txt, w_col) in enumerate(zip(HLAVICKY, SLOUPCE_W)):
    sh = s13.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(1.05), Inches(w_col), Inches(0.32))
    sh.fill.solid(); sh.fill.fore_color.rgb = CERNA; sh.line.fill.background()
    text_pole(s13, h_txt, SLOUPCE_X[j] + 0.05, 1.08, w_col - 0.1, 0.26,
              font_size=9.5, bold=True, fg=BILA, align=PP_ALIGN.CENTER)

for i, radek in enumerate(tabulka_hyp_data):
    y_pos = 1.40 + (i * 0.28)
    bg_barva = RGBColor(0xFA, 0xFA, 0xFA) if (i % 2 == 0) else BILA
    is_zam = radek[6]

    for j in range(6):
        val = radek[j]
        w_col = SLOUPCE_W[j]
        sh = s13.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(y_pos), Inches(w_col), Inches(0.26))
        sh.fill.solid(); sh.fill.fore_color.rgb = bg_barva
        sh.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE); sh.line.width = Pt(0.5)

        is_verdict = (j == 5)
        text_fg = (CERVENA_ZAM if is_zam else ZELENA_NEZAM) if is_verdict else TMAVA_SEDA
        align = PP_ALIGN.CENTER if j in [0, 3, 4, 5] else PP_ALIGN.LEFT
        text_pole(s13, val, SLOUPCE_X[j] + 0.05, y_pos + 0.02, w_col - 0.1, 0.22,
                  font_size=8.5, bold=is_verdict, fg=text_fg, align=align)

# Dolní část: 4 doporučení pro trenéry ve 2 sloupcích
doporuceni = [
    ('1. Priorita hloubky vápna', 'Střelba z vápna (< 12 j.) má 6× vyšší konverzi než z dálky; klíčem je trpělivá finální přihrávka do pokutového území.'),
    ('2. Maximalizace úhlu zakončení', 'Větší střelecký zorný úhel násobně zvyšuje xG; útočníci mají preferovat zakončení z centrální osy před střelbou z ostrých úhlů.'),
    ('3. Specifický nácvik hlaviček', 'Hlavičky vznikají ze zhoršených úhlů a větších vzdáleností; centry musí cíleně směřovat do zóny malého vápna.'),
    ('4. Taktická eliminace střel z dálky', 'Střelba ze vzdálenosti > 20 metrů vykazuje šanci pod 3 %; v tréninku je nutné potlačit ukvapené pokusy ze střední vzdálenosti.'),
]

for idx_d, (titul_d, text_d) in enumerate(doporuceni):
    col_x = 0.8 if idx_d % 2 == 0 else 6.8
    row_y = 5.05 if idx_d < 2 else 5.95
    w_card = 5.73

    sh_d = s13.shapes.add_shape(1, Inches(col_x), Inches(row_y), Inches(w_card), Inches(0.82))
    sh_d.fill.solid(); sh_d.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
    sh_d.line.color.rgb = SVETLA_SEDA; sh_d.line.width = Pt(1)

    sh_str = s13.shapes.add_shape(1, Inches(col_x), Inches(row_y), Inches(0.08), Inches(0.82))
    sh_str.fill.solid(); sh_str.fill.fore_color.rgb = MODRA_BOD; sh_str.line.fill.background()

    text_pole(s13, titul_d, col_x + 0.18, row_y + 0.06, w_card - 0.3, 0.25, font_size=11, bold=True, fg=CERNA)
    text_pole(s13, text_d, col_x + 0.18, row_y + 0.32, w_card - 0.3, 0.46, font_size=9.5, fg=TMAVA_SEDA)

text_pole(s13, 'Semestrální projekt VMM 2026/27  •  VUT Brno  •  Děkuji za pozornost',
          0.8, 6.95, 11.73, 0.30, font_size=10, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(s13, 13)
print('  [OK] Slide 13: Souhrnná tabulka a doporučení vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# ULOŽENÍ PREZENTACE
# ════════════════════════════════════════════════════════════════════════════
prs.save(PPTX_PATH)
print(f'\n[VÝBORNĚ] Prezentace úspěšně vygenerována: {PPTX_PATH}')
print(f'          Celkový počet slidů: {len(prs.slides)}')
