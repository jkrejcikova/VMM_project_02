# -*- coding: utf-8 -*-
# =============================================================================
# SKRIPT PRO TVORBU PREZENTACE (PowerPoint)
# Semestrální projekt VMM – Střelecká úspěšnost
# DESIGN: Čistý, minimalistický, čistě bílé pozadí (#FFFFFF), 50/50 symetrie
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

# ── Barvy (čistá minimalistická paleta) ─────────────────────────────────────
BILA        = RGBColor(0xFF, 0xFF, 0xFF)   # #FFFFFF - čistě bílé pozadí
CERNA       = RGBColor(0x1A, 0x1A, 0x1A)   # #1A1A1A - hlavní nadpisy
TMAVA_SEDA  = RGBColor(0x33, 0x33, 0x33)   # #333333 - text odrážek
STRED_SEDA  = RGBColor(0x66, 0x66, 0x66)   # #666666 - podtitulky, doplňující text
SVETLA_SEDA = RGBColor(0xD8, 0xD8, 0xD8)   # #D8D8D8 - jemné oddělovací linky
OKRAJOVA_S  = RGBColor(0xCC, 0xCC, 0xCC)   # #CCCCCC - rámečky
CERVENA     = RGBColor(0xC5, 0x30, 0x30)   # #C53030 - zamítnutí H0
ZELENA      = RGBColor(0x27, 0x67, 0x49)   # #276749 - nezamítnutí H0
MODRA_AKCENT= RGBColor(0x1F, 0x77, 0xB4)   # #1F77B4 - odrážky, decentní akcent

# ── Rozměry snímku 16:9 ────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]   # čistý prázdný layout


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
    """Vloží jednoduché textové pole bez pozadí."""
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
    """Nakreslí tenkou decentní horizontální linku."""
    sh = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(tloustka))
    sh.fill.solid()
    sh.fill.fore_color.rgb = barva
    sh.line.fill.background()
    return sh


def hlavicka(slide, nadpis, podtitulek=None):
    """
    Standardní čisté záhlaví:
    Černý nadpis vlevo nahoře (22 pt, bold) + volitelný podtitulek + tenká šedá linka.
    Žádné barevné pruhy, pouze čistá plocha.
    """
    text_pole(slide, nadpis, 0.8, 0.45, 11.73, 0.55,
              font_size=22, bold=True, fg=CERNA)
    if podtitulek:
        text_pole(slide, podtitulek, 0.8, 0.98, 11.73, 0.3,
                  font_size=11, italic=True, fg=STRED_SEDA)
        linka(slide, 0.8, 1.30, 11.73)
    else:
        linka(slide, 0.8, 1.15, 11.73)


def cislo_slidu(slide, n, total=12):
    """Číslo slidu v pravém dolním rohu."""
    text_pole(slide, f'{n} / {total}', 11.7, 7.05, 0.8, 0.3,
              font_size=9, fg=STRED_SEDA, align=PP_ALIGN.RIGHT)


def vloz_obrazek(slide, soubor, l=0.8, t=1.45, sirka_palce=6.4):
    """
    Vloží obrázek se zachováním poměru stran:
    ZADÁVÁ POUZE ŠÍŘKU (width)! Výška je dopočítána automaticky a nedochází k deformaci.
    """
    cesta = os.path.join(VYSTUPY, soubor)
    if not os.path.exists(cesta):
        print(f'  [VAROVÁNÍ] Obrázek nenalezen: {soubor}')
        return None
    return slide.shapes.add_picture(cesta, Inches(l), Inches(t), width=Inches(sirka_palce))


def odrazky_blok(slide, body, l=7.5, t=1.45, w=5.0, h=3.0, font_size=13.5):
    """Vytvoří blok odrážek (max 3–4 stručné body v tmavě šedém textu)."""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, bod in enumerate(body):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(8)
        p.line_spacing = 1.15
        r_bullet = p.add_run()
        r_bullet.text = '•  '
        r_bullet.font.size = Pt(font_size)
        r_bullet.font.bold = True
        r_bullet.font.color.rgb = MODRA_AKCENT
        r_text = p.add_run()
        r_text.text = bod
        r_text.font.size = Pt(font_size)
        r_text.font.color.rgb = TMAVA_SEDA
    return txb


def hypoteza_karta(slide, nazev_testu, h0_text, stat_text, verdikt_text,
                   zamitnuto=True, l=7.5, t=4.8, w=5.0, h=1.85):
    """
    Decentní rámeček s H0/H1 a výsledkem testu:
    Jemný světlý podklad, tenký rámeček, jasné a čitelné typografické členění.
    """
    bg_barva = RGBColor(0xFD, 0xF2, 0xF2) if zamitnuto else RGBColor(0xF0, 0xFD, 0xF4)
    ram_barva = RGBColor(0xF5, 0xC6, 0xCB) if zamitnuto else RGBColor(0xC3, 0xE6, 0xCB)
    verdikt_barva = CERVENA if zamitnuto else ZELENA
    ikona = '✗ ' if zamitnuto else '✓ '

    sh = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = bg_barva
    sh.line.color.rgb = ram_barva
    sh.line.width = Pt(1)

    txb = slide.shapes.add_textbox(Inches(l + 0.15), Inches(t + 0.1), Inches(w - 0.3), Inches(h - 0.2))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True

    # Řádek 1: Název testu
    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = nazev_testu
    r1.font.size = Pt(11)
    r1.font.bold = True
    r1.font.color.rgb = CERNA

    # Řádek 2: H0
    p2 = tf.add_paragraph()
    p2.space_before = Pt(3)
    r2_tag = p2.add_run()
    r2_tag.text = 'H₀: '
    r2_tag.font.bold = True
    r2_tag.font.size = Pt(10.5)
    r2_tag.font.color.rgb = CERNA
    r2_txt = p2.add_run()
    r2_txt.text = h0_text
    r2_txt.font.size = Pt(10.5)
    r2_txt.font.color.rgb = TMAVA_SEDA

    # Řádek 3: Statistika a p-hodnota
    p3 = tf.add_paragraph()
    p3.space_before = Pt(2)
    r3 = p3.add_run()
    r3.text = stat_text
    r3.font.size = Pt(10)
    r3.font.color.rgb = STRED_SEDA

    # Řádek 4: Verdikt
    p4 = tf.add_paragraph()
    p4.space_before = Pt(4)
    r4 = p4.add_run()
    r4.text = f'{ikona}{verdikt_text}'
    r4.font.size = Pt(11)
    r4.font.bold = True
    r4.font.color.rgb = verdikt_barva

    return sh


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – TITULNÍ SNÍMEK
# ════════════════════════════════════════════════════════════════════════════
slide1 = novy_slide()

text_pole(slide1, 'Střelecká úspěšnost ve fotbale',
          0.8, 1.8, 11.73, 1.1,
          font_size=36, bold=True, fg=CERNA, align=PP_ALIGN.CENTER)

text_pole(slide1, 'Vícerozměrná statistická analýza dat střel z anglické Premier League',
          0.8, 2.85, 11.73, 0.6,
          font_size=16, italic=True, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

linka(slide1, 3.0, 3.65, 7.33, tloustka=0.02, barva=MODRA_AKCENT)

text_pole(slide1, 'Vysoké učení technické v Brně  •  Vícerozměrné statistické metody (VMM)',
          0.8, 3.95, 11.73, 0.45,
          font_size=14, bold=True, fg=TMAVA_SEDA, align=PP_ALIGN.CENTER)

text_pole(slide1, 'Semestrální projekt  •  Akademický rok 2026/27',
          0.8, 4.45, 11.73, 0.4,
          font_size=12, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

text_pole(slide1, 'Zdroj dat: shots_outcome_Final.csv (understat.com)',
          0.8, 6.75, 11.73, 0.35,
          font_size=10, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(slide1, 1)
print('  [OK] Slide 1: Titulní snímek vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – POPIS DATASETU A CÍL
# ════════════════════════════════════════════════════════════════════════════
slide2 = novy_slide()
hlavicka(slide2, 'Popis datasetu a cíl analýzy', 'Základní přehled datové sady a sledovaných proměnných')

# Vlevo graf xG (width=6.4)
vloz_obrazek(slide2, '01b_hist_xG.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide2, [
    'Datový soubor obsahuje 1 000 střel z Premier League (po vyřazení OwnGoal 998 střel).',
    'Cílová proměnná: Binární výsledek střely (Gól = 1 s podílem 9,0 %, Nezakončeno = 0).',
    'Klíčové metriky: Geometrie střely (X, Y, vzdálenost, úhel) a herní kontext (xG, minuta, shotType).',
    'Vyřazena technická metadata (ID zápasů, hráčů a datumy) nemající přímý vliv na trajektorii.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo decentní rámeček s cílem projektu
hypoteza_karta(slide2,
               'Výzkumný cíl semestrálního projektu:',
               'Pravděpodobnost gólu nezávisí na prostorových a geometrických faktorech střely.',
               'Sada dat: n = 734 kompletních prostorových střel | sledováno 6 spojitých metrik',
               'Cíl: Identifikovat klíčové faktory zakončení pomocí vícerozměrných metod.',
               zamitnuto=False, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide2, 2)
print('  [OK] Slide 2: Popis datasetu vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – PŘEDZPRACOVÁNÍ A PROSTOROVÉ SOUŘADNICE
# ════════════════════════════════════════════════════════════════════════════
slide3 = novy_slide()
hlavicka(slide3, 'Předzpracování dat a mapa střel', 'Čištění, škálování hřiště 100×100 a ošetření odlehlých hodnot')

# Vlevo mapa střel na bílém hřišti (width=6.4)
vloz_obrazek(slide3, '01_mapa_strel.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide3, [
    'Škálování souřadnic X a Y na jednotné fotbalové hřiště 100 × 100 jednotek.',
    'Odvození geometrických veličin: Vzdálenost od branky (dist_m) a střelecký úhel (angle_deg).',
    'Ošetření chybějících hodnot: Vynechání řádků bez X a Y (žádná falešná imputace v ose).',
    'Pravidlo 3-sigma (Z-skóre): Odstraněna 1 extrémní střela z vlastní poloviny (|Z| > 3).',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo rámeček
hypoteza_karta(slide3,
               'Metodické ošetření odlehlých hodnot:',
               'Odlehlá pozorování vzdálenosti dist_m pochází ze stejného rozdělení jako běžné střely.',
               'Kritérium 3-sigma: |Z(dist_m)| > 3 | Vyřazen 1 extrém (vzdálenost > 42 j.)',
               'Čistá analytická sada: n = 734 střel s validními prostorovými souřadnicemi.',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide3, 3)
print('  [OK] Slide 3: Předzpracování vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – DIAGNOSTIKA NORMALITY
# ════════════════════════════════════════════════════════════════════════════
slide4 = novy_slide()
hlavicka(slide4, 'Diagnostika normality a předpokladů', 'Testování jednorozměrné normality klíčové veličiny dist_m')

# Vlevo 1x2 graf histogram + Q-Q (width=6.4)
vloz_obrazek(slide4, '02_normalita_histogramy_qq.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide4, [
    'Shapiro-Wilkův test prokázal statisticky vysoce významné porušení normality (p < 0,001).',
    'Q-Q diagram i empirický histogram vykazují zřetelné asymetrické odchylky v koncových kvantilech.',
    'Leveneho test potvrdil heteroskedasticitu rozptylů mezi skupinami zakončení (p < 0,001).',
    'Metodický závěr: Porušení předpokladů formálně zdůvodňuje volbu robustních metod.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide4,
               'Shapiro-Wilkův test normality (dist_m):',
               'Vzdálenost střely dist_m pochází z normálního rozdělení N(μ, σ²).',
               'W = 0,9842 | p = 7,15 × 10⁻⁷ | Hladina významnosti α = 0,05',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (nutné robustní postupy).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide4, 4)
print('  [OK] Slide 4: Diagnostika normality vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – KORELAČNÍ ANALÝZA
# ════════════════════════════════════════════════════════════════════════════
slide5 = novy_slide()
hlavicka(slide5, 'Vztahy mezi proměnnými (Korelace)', 'Plná Spearmanova korelační matice mezi spojitými metrikami')

# Vlevo plná Spearmanova heatmapa (width=6.2)
vloz_obrazek(slide5, '03_korelacni_heatmapa.png', l=0.8, t=1.45, sirka_palce=6.2)

# Vpravo odrážky
odrazky_blok(slide5, [
    'Spearmanova pořadová korelace zvolena jako robustní vůči prokázané ne-normalitě dat.',
    'Silná záporná vazba xG ↔ dist_m (r = −0,73): Čím větší vzdálenost od branky, tím nižší xG.',
    'Kladná závislost xG ↔ angle_deg (r = +0,44): Větší střelecký úhel zásadně zvyšuje kvalitu šance.',
    'Minuta zápasu a šířková pozice Y nevykazují žádnou přímou lineární korelaci s úspěšností.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide5,
               'Test významnosti korelačního koeficientu (xG ↔ dist_m):',
               'Mezi očekávanou hodnotou xG a vzdáleností není závislost (r = 0).',
               'Spearmanovo r = −0,732 | t-statistika = −29,1 | p < 0,001',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (vazba je statisticky významná).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide5, 5)
print('  [OK] Slide 5: Korelační analýza vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – ANOVA (ROZDÍLY DLE ZAKONČENÍ)
# ════════════════════════════════════════════════════════════════════════════
slide6 = novy_slide()
hlavicka(slide6, 'Rozdíly dle typu zakončení (ANOVA)', 'Jednofaktorová Welchova ANOVA pro vzdálenost a střelecký úhel')

# Vlevo boxploty (width=6.4)
vloz_obrazek(slide6, '04_boxploty_shottype.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide6, [
    'Porovnávané skupiny zakončení: Pravá noha (n=285), Levá noha (n=272), Hlava (n=48).',
    'Vzhledem k heteroskedasticitě (Levene p < 0,001) použita robustní Welchova ANOVA.',
    'Vzdálenost střely se mezi typy zakončení statisticky vysoce významně liší (p < 0,001).',
    'Střelecký úhel vykazuje rovněž masivní rozdíl: Hlavičky vznikají z horších úhlů.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide6,
               'Welchova ANOVA (vzdálenost dist_m dle typu zakončení):',
               'Střední hodnoty vzdálenosti jsou pro všechny typy zakončení stejné (μ₁ = μ₂ = μ₃).',
               'Welchovo F = 193,0 | stupně volnosti: 2; 107,3 | p = 7,47 × 10⁻⁴⁶',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (střední hodnoty se liší).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide6, 6)
print('  [OK] Slide 6: ANOVA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – VÍCEROZMĚRNÁ MANOVA A TUKEY HSD
# ════════════════════════════════════════════════════════════════════════════
slide7 = novy_slide()
hlavicka(slide7, 'Vícerozměrné porovnání (MANOVA a Tukey)', 'Sdružený vliv na vektor [dist_m, angle_deg] a párová porovnání')

# Vlevo graf Tukeyho HSD (width=6.4)
vloz_obrazek(slide7, '04b_tukey_hsd.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide7, [
    'MANOVA hodnotí sdružený vektor (vzdálenost + úhel) a zohledňuje jejich korelaci.',
    'Wilksova lambda (p < 0,001) potvrzuje vícerozměrný rozdíl mezi způsoby zakončení.',
    'Tukeyho HSD test odhalil, že Hlava se zásadně liší od obou nohou (Δ dist ≈ +11 j., Δ úhel ≈ −22°).',
    'Mezi pravou a levou nohou nebyl nalezen žádný statisticky významný rozdíl (p = 0,22).',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide7,
               'Multivariátní test MANOVA (Wilksova lambda):',
               'Vektory středních hodnot [vzdálenost, úhel] jsou pro všechny typy zakončení shodné.',
               'Wilks\' λ = 0,8060 | F = 34,22 | p = 4,44 × 10⁻²⁷ (α = 0,05)',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (geometrie zakončení hlavou je odlišná).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide7, 7)
print('  [OK] Slide 7: MANOVA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 – REDUKCE DIMENZIONALITY (PCA)
# ════════════════════════════════════════════════════════════════════════════
slide8 = novy_slide()
hlavicka(slide8, 'Redukce dimenzionality (PCA)', 'Analýza hlavních komponent na standardizovaných datech (Z-skóre)')

# Vlevo biplot (width=6.4)
vloz_obrazek(slide8, '05b_biplot_pca.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide8, [
    'Bartlettův test sférickosti (p < 0,001) i KMO index (0,62) potvrdily smysluplnost PCA.',
    'Kaiserovo pravidlo (vlastní číslo λ > 1) doporučuje zachovat 2 hlavní komponenty.',
    'PC1 (~48 % rozptylu) definuje „osu kvality střelecké pozice" (vzdálenost vs. úhel a xG).',
    'PC2 (~20 % rozptylu) zachycuje umístění na šířku hřiště (Y) a vývoj herního času.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide8,
               'Bartlettův test sférickosti pro ověření vhodnosti PCA:',
               'Korelační matice sledovaných veličin je jednotková matice (proměnné jsou nekorelované).',
               'χ² = 2041,4 | stupně volnosti: df = 15 | p < 0,001',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (redukce dimenze je statisticky oprávněná).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide8, 8)
print('  [OK] Slide 8: PCA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 – SHLUKOVÁ ANALÝZA (CLUSTERING)
# ════════════════════════════════════════════════════════════════════════════
slide9 = novy_slide()
hlavicka(slide9, 'Shluková analýza – Profily střel', 'Hierarchické shlukování (Ward) a K-means pro k = 2')

# Vlevo mapa shluků na bílém hřišti (width=6.4)
vloz_obrazek(slide9, '06b_mapa_shluku.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide9, [
    'Wardova hierarchická metoda indikovala optimální rozpad dat na 2 zřetelné shluky.',
    'Shluk 1 (Blízká střela / vápno): Průměrná vzdálenost 13 j., vyšší úhel i podíl gólů.',
    'Shluk 2 (Střelba z dálky): Průměrná vzdálenost 25 j., nízké xG, minimální efektivita.',
    'Nalezené shluky odpovídají přirozeným herním profilům fotbalových zakončení.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide9,
               'Test existence shlukové struktury v datech:',
               'Střelecké pokusy tvoří homogenní rozdělení bez přirozených shluků.',
               'Wardovo kritérium minimálního rozptylu | K-means k = 2 rozdělení',
               'H₀ ZAMÍTÁME (potvrzena existence 2 oddělitelných herních profilů střel).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide9, 9)
print('  [OK] Slide 9: Shlukování vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 – PREDIKCE GÓLU (LOGISTICKÁ REGRESE)
# ════════════════════════════════════════════════════════════════════════════
slide10 = novy_slide()
hlavicka(slide10, 'Predikce gólu – Logistická regrese', 'Binární model šance na vstřelení branky a poměry šancí (Odds Ratios)')

# Vlevo Forest plot na logaritmické ose X (width=6.4)
vloz_obrazek(slide10, '07b_forest_plot.png', l=0.8, t=1.45, sirka_palce=6.4)

# Vpravo odrážky
odrazky_blok(slide10, [
    'Binární logistická regrese spolehlivě odhaduje pravděpodobnost gólu (LRT p < 0,001).',
    'Očekávané góly xG (OR ≈ 76,0, p < 0,001) představují dominantní pozitivní faktor.',
    'Vzdálenost dist_m (OR = 0,922, p = 0,029) statisticky významně snižuje šanci na gól.',
    'Klasifikační schopnost modelu je vysoká: Plocha pod ROC křivkou dosahuje AUC = 0,784.',
], l=7.5, t=1.45, w=5.0, h=3.0)

# Vpravo hypotéza
hypoteza_karta(slide10,
               'Globální test logistického modelu (Likelihood Ratio Test):',
               'Žádný ze sledovaných parametrů neovlivňuje šanci na gól (všechna β = 0).',
               'LLR chí-kvadrát = 82,1 | p = 6,17 × 10⁻¹⁷ | ROC AUC = 0,784',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (regresní model je statisticky významný).',
               zamitnuto=True, l=7.5, t=4.85, w=5.0, h=1.85)

cislo_slidu(slide10, 10)
print('  [OK] Slide 10: Logistická regrese vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 – SOUHRNNÁ TABULKA HYPOTÉZ
# ════════════════════════════════════════════════════════════════════════════
slide11 = novy_slide()
hlavicka(slide11, 'Souhrnná tabulka testovaných hypotéz', 'Systematický přehled všech statistických rozhodnutí na hladině α = 0,05')

# Definice řádků tabulky
tabulka_data = [
    ('2 – Normalita', 'Shapiro-Wilk (dist_m)', 'dist_m pochází z normálního rozdělení', 'W = 0,984', '7,15e−07', 'ZAMÍTÁME H₀'),
    ('2 – Normalita', 'Shapiro-Wilk (xG)', 'xG pochází z normálního rozdělení', 'W = 0,549', '6,34e−39', 'ZAMÍTÁME H₀'),
    ('2 – Rozptyly', 'Leveneho test', 'Rozptyly vzdálenosti jsou ve skupinách shodné', 'L = 10,997', '4,55e−07', 'ZAMÍTÁME H₀'),
    ('3 – Závislost', 'Spearmanův test', 'Korelace mezi xG a dist_m je nulová (r = 0)', 'r = −0,732', '< 0,001', 'ZAMÍTÁME H₀'),
    ('4 – Rozdíly', 'Welch ANOVA (dist_m)', 'Střední vzdálenosti jsou pro typy zakončení stejné', 'F = 193,0', '7,47e−46', 'ZAMÍTÁME H₀'),
    ('4 – Rozdíly', 'Welch ANOVA (angle)', 'Střední úhly jsou pro typy zakončení stejné', 'F = 39,06', '6,33e−14', 'ZAMÍTÁME H₀'),
    ('4 – Sdružené', 'MANOVA (Wilks λ)', 'Vektory středních hodnot jsou ve skupinách shodné', 'λ = 0,806', '4,44e−27', 'ZAMÍTÁME H₀'),
    ('5 – PCA', 'Bartlettův test', 'Korelační matice je jednotková (PCA nevhodná)', 'χ² = 2041,4', '< 0,001', 'ZAMÍTÁME H₀'),
    ('6 – Shluky', 'Wardovo shlukování', 'Střely tvoří homogenní náhodné rozdělení', 'Ward d² k=2', '< 0,001', 'ZAMÍTÁME H₀'),
    ('7 – Regrese', 'Logit model (dist_m)', 'Vzdálenost střely neovlivňuje šanci na gól (β = 0)', 'z = −2,18', '0,029', 'ZAMÍTÁME H₀'),
    ('7 – Regrese', 'Logit model (xG)', 'Metrika xG neovlivňuje šanci na gól (β = 0)', 'z = 4,58', '4,68e−06', 'ZAMÍTÁME H₀'),
]

# Geometrie tabulky
SLOUPCE_X = [0.8, 2.3, 4.3, 8.1, 9.7, 10.9]
SLOUPCE_W = [1.4, 1.9, 3.7, 1.5, 1.1, 1.63]
HLAVICKY  = ['Fáze', 'Metoda', 'Nulová hypotéza (H₀)', 'Statistika', 'p-hodnota', 'Rozhodnutí']

# Záhlaví tabulky
for j, (h_txt, w_col) in enumerate(zip(HLAVICKY, SLOUPCE_W)):
    sh = slide11.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(1.4), Inches(w_col), Inches(0.38))
    sh.fill.solid()
    sh.fill.fore_color.rgb = CERNA
    sh.line.fill.background()
    text_pole(slide11, h_txt, SLOUPCE_X[j] + 0.05, 1.44, w_col - 0.1, 0.3,
              font_size=10, bold=True, fg=BILA, align=PP_ALIGN.CENTER)

# Řádky tabulky
for i, radek in enumerate(tabulka_data):
    y_pos = 1.82 + (i * 0.44)
    bg_barva = RGBColor(0xFA, 0xFA, 0xFA) if (i % 2 == 0) else BILA
    for j, (val, w_col) in enumerate(zip(radek, SLOUPCE_W)):
        sh = slide11.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(y_pos), Inches(w_col), Inches(0.40))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg_barva
        sh.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
        sh.line.width = Pt(0.5)

        is_verdict = (j == 5)
        text_fg = CERVENA if is_verdict else TMAVA_SEDA
        align = PP_ALIGN.CENTER if j in [0, 3, 4, 5] else PP_ALIGN.LEFT
        text_pole(slide11, val, SLOUPCE_X[j] + 0.05, y_pos + 0.06, w_col - 0.1, 0.32,
                  font_size=9.5, bold=is_verdict, fg=text_fg, align=align)

cislo_slidu(slide11, 11)
print('  [OK] Slide 11: Souhrnná tabulka vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 – ZÁVĚR A DOPORUČENÍ
# ════════════════════════════════════════════════════════════════════════════
slide12 = novy_slide()
hlavicka(slide12, 'Závěr a doporučení pro praxi', 'Klíčové analytické poznatky pro trenéry a datové analytiky fotbalu')

zavery = [
    ('1. Geometrická pozice rozhoduje o úspěchu',
     'Vzdálenost a střelecký úhel jsou dominantními faktory zakončení. Každý metr navíc významně sráží šanci na gól (Logit OR = 0,922). Základním principem moderního fotbalu musí být tvorba pozic z hloubky vápna.'),
    ('2. Hlavičky představují specifickou disciplínu',
     'MANOVA i Tukeyho test potvrdily, že zakončení hlavou probíhá z větších vzdáleností a z méně výhodných úhlů. Hlavičkové souboje vyžadují odlišné tréninkové schéma a cílené centry do bezprostřední blízkosti branky.'),
    ('3. Existence dvou přirozených herních světů',
     'Shluková analýza jednoznačně potvrdila 2 herní profily: Vysoce efektivní střely z vápna (prům. 13 j.) vs. nízkoefektivní střelba z dálky (prům. 25 j.), která v moderní analytice vede k plýtvání držením míče.'),
    ('4. Praktická doporučení pro tréninkový proces',
     'Soustředit zakončení na první třetinu pokutového území s úhlem > 30°. Zakázat neuvážené střely z dálky v přechodové fázi a preferovat finální přihrávku do výhodnějšího střeleckého úhlu.'),
]

for i, (titul, popis) in enumerate(zavery):
    y_karta = 1.45 + (i * 1.25)

    # Karta
    sh = slide12.shapes.add_shape(1, Inches(0.8), Inches(y_karta), Inches(11.73), Inches(1.12))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
    sh.line.color.rgb = SVETLA_SEDA
    sh.line.width = Pt(1)

    # Modrý dekorační proužek vlevo
    sh_strip = slide12.shapes.add_shape(1, Inches(0.8), Inches(y_karta), Inches(0.08), Inches(1.12))
    sh_strip.fill.solid()
    sh_strip.fill.fore_color.rgb = MODRA_AKCENT
    sh_strip.line.fill.background()

    # Titul karty
    text_pole(slide12, titul, 1.05, y_karta + 0.10, 11.3, 0.32,
              font_size=12.5, bold=True, fg=CERNA)

    # Popis karty
    text_pole(slide12, popis, 1.05, y_karta + 0.44, 11.3, 0.60,
              font_size=11, fg=TMAVA_SEDA)

text_pole(slide12, 'Děkuji za pozornost  •  Semestrální projekt VMM 2026/27  •  VUT Brno',
          0.8, 6.85, 11.73, 0.35,
          font_size=10.5, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(slide12, 12)
print('  [OK] Slide 12: Závěr vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# ULOŽENÍ PREZENTACE
# ════════════════════════════════════════════════════════════════════════════
prs.save(PPTX_OUT)
print(f'\n[VÝBORNĚ] Prezentace úspěšně uložena: {PPTX_OUT}')
print(f'          Počet vygenerovaných slidů: {len(prs.slides)}')
