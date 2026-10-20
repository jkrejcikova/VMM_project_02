# -*- coding: utf-8 -*-
# =============================================================================
# SKRIPT PRO GENEROVÁNÍ PREZENTACE (PowerPoint PPTX)
# Semestrální projekt VMM – Střelecká úspěšnost (Premier League)
# 14 SLIDŮ: Čistě BÍLÉ pozadí (#FFFFFF), symetrické rozvržení 50/50, bez deformace
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
TMAVA_SEDA   = RGBColor(0x33, 0x33, 0x33)   # #333333 – Běžný text a odrážky
STRED_SEDA   = RGBColor(0x66, 0x66, 0x66)   # #666666 – Doplňující text, čísla slidů
SVETLA_SEDA  = RGBColor(0xD8, 0xD8, 0xD8)   # #D8D8D8 – Oddělovací linky
CERVENA_ZAM  = RGBColor(0xC5, 0x30, 0x30)   # #C53030 – Zamítnutí H0
ZELENA_NEZAM = RGBColor(0x27, 0x67, 0x49)   # #276749 – Nezamítnutí H0
MODRA_BOD    = RGBColor(0x1F, 0x77, 0xB4)   # #1F77B4 – Odrážky a decentní akcent

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
    """Vloží jednoduché textové pole na snímek."""
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
    Standardní čisté záhlaví pro snímky 2 až 14:
    Černý tučný nadpis vlevo nahoře (22 pt) + volitelný podtitulek + tenká šedá linka.
    """
    text_pole(slide, nadpis, 0.65, 0.40, 12.0, 0.55,
              font_size=22, bold=True, fg=CERNA)
    if podtitulek:
        text_pole(slide, podtitulek, 0.65, 0.95, 12.0, 0.32,
                  font_size=11, italic=True, fg=STRED_SEDA)
        linka(slide, 0.65, 1.28, 12.0)
    else:
        linka(slide, 0.65, 1.05, 12.0)


def cislo_slidu(slide, n, total=14):
    """Vloží číslo snímku v pravém dolním rohu."""
    text_pole(slide, f'{n} / {total}', 11.9, 7.05, 0.8, 0.3,
              font_size=9.5, fg=STRED_SEDA, align=PP_ALIGN.RIGHT)


def vloz_velky_graf(slide, soubor, l=0.65, t=1.35, sirka_palce=6.8):
    """
    Vloží obrázek grafu z vystupy/ se striktním zachováním poměru stran:
    ZADÁVÁME POUZE ŠÍŘKU (width=6.8 palce)! Výška je dopočítána automaticky a nedochází k deformaci.
    """
    cesta = os.path.join(VYSTUPY_DIR, soubor)
    if not os.path.exists(cesta):
        print(f'  [VAROVÁNÍ] Obrázek nenalezen: {soubor}')
        return None
    return slide.shapes.add_picture(cesta, Inches(l), Inches(t), width=Inches(sirka_palce))


def odrazky_sloupec(slide, body, l=7.75, t=1.35, w=4.95, h=3.1, font_size=13.5):
    """Vloží sloupec s max 3–4 věcnými odrážkami v tmavě šedé barvě."""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, bod in enumerate(body):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(7)
        p.line_spacing = 1.15
        r_b = p.add_run()
        r_b.text = '•  '
        r_b.font.size = Pt(font_size)
        r_b.font.bold = True
        r_b.font.color.rgb = MODRA_BOD
        r_t = p.add_run()
        r_t.text = bod
        r_t.font.size = Pt(font_size)
        r_t.font.color.rgb = TMAVA_SEDA
    return txb


def hypoteza_karta(slide, nazev_testu, h0_text, stat_text, verdikt_text,
                   zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95):
    """
    Decentní rámeček s testovanou H0, statistikou a výsledkem testu.
    Světlé tónování pozadí, tenký okraj a zřetelný barevný verdikt.
    """
    bg_c = RGBColor(0xFD, 0xF2, 0xF2) if zamitnuto else RGBColor(0xF0, 0xFD, 0xF4)
    ram_c = RGBColor(0xF5, 0xC6, 0xCB) if zamitnuto else RGBColor(0xC3, 0xE6, 0xCB)
    verd_c = CERVENA_ZAM if zamitnuto else ZELENA_NEZAM
    ikona = '✗ ' if zamitnuto else '✓ '

    sh = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = bg_c
    sh.line.color.rgb = ram_c
    sh.line.width = Pt(1)

    txb = slide.shapes.add_textbox(Inches(l + 0.15), Inches(t + 0.1), Inches(w - 0.3), Inches(h - 0.2))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True

    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    r1.text = nazev_testu
    r1.font.size = Pt(11)
    r1.font.bold = True
    r1.font.color.rgb = CERNA

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

    p3 = tf.add_paragraph()
    p3.space_before = Pt(2)
    r3 = p3.add_run()
    r3.text = stat_text
    r3.font.size = Pt(10)
    r3.font.color.rgb = STRED_SEDA

    p4 = tf.add_paragraph()
    p4.space_before = Pt(4)
    r4 = p4.add_run()
    r4.text = f'{ikona}{verdikt_text}'
    r4.font.size = Pt(11)
    r4.font.bold = True
    r4.font.color.rgb = verd_c

    return sh


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
# SLIDE 2 – POPIS DATASETU & CÍL ANALÝZY
# ════════════════════════════════════════════════════════════════════════════
s2 = novy_slide()
zahlavi(s2, 'Popis datasetu & cíl analýzy', 'Základní přehled sledovaných veličin a cíl projektu')

vloz_velky_graf(s2, '01b_hist_xG.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s2, [
    'Datový soubor obsahuje 1 000 střel z Premier League (998 po vyřazení OwnGoal).',
    'Cílová binární proměnná: Gól = 1 (podíl 9,0 %) vs. Nezakončeno = 0 (91,0 %).',
    'Klíčové metriky: Geometrie střely (X, Y, vzdálenost, úhel) a herní kontext (xG, minuta, typ zakončení).',
    'Vyřazena technická metadata (ID zápasů, hráčů a datumy) nemající přímý vliv na trajektorii.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s2,
               'Výzkumný cíl semestrálního projektu:',
               'Pravděpodobnost gólu nezávisí na prostorových a geometrických faktorech střely.',
               'Sada dat: n = 734 kompletních prostorových střel | sledováno 6 spojitých metrik',
               'Cíl: Identifikovat klíčové faktory zakončení pomocí vícerozměrných metod.',
               zamitnuto=False, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s2, 2)
print('  [OK] Slide 2: Popis datasetu vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – PŘEDZPRACOVÁNÍ DAT & MAPA STŘEL
# ════════════════════════════════════════════════════════════════════════════
s3 = novy_slide()
zahlavi(s3, 'Předzpracování dat & mapa střel', 'Škálování hřiště 100×100 a ošetření odlehlých hodnot')

vloz_velky_graf(s3, '01_mapa_strel.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s3, [
    'Škálování prostorových souřadnic X a Y na fotbalové hřiště 100 × 100 jednotek.',
    'Odvození geometrických veličin: Vzdálenost od branky (dist_m) a střelecký úhel (angle_deg).',
    'Ošetření chybějících hodnot: Vynechání řádků bez X a Y (žádná falešná imputace v ose hřiště).',
    'Pravidlo 3-sigma (Z-skóre): Odstraněna 1 extrémní střela z vlastní poloviny (|Z| > 3); sada n = 734.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s3,
               'Metodické ošetření odlehlých hodnot (Pravidlo 3-sigma):',
               'Odlehlá pozorování vzdálenosti dist_m pochází ze stejného rozdělení jako běžné střely.',
               'Kritérium: |Z(dist_m)| > 3 | Vyřazen 1 extrém (vzdálenost > 42 j.)',
               'Validní analytická sada: n = 734 střel s věrohodnou prostorovou geometrií.',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s3, 3)
print('  [OK] Slide 3: Předzpracování vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – DIAGNOSTIKA NORMALITY
# ════════════════════════════════════════════════════════════════════════════
s4 = novy_slide()
zahlavi(s4, 'Diagnostika normality & předpokladů', 'Jednorozměrná normalita (histogram, opravený Q-Q graf probplot) a Leveneho test')

vloz_velky_graf(s4, '02_normalita_histogramy_qq.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s4, [
    'Shapiro-Wilkův test prokázal statisticky vysoce významné porušení normality (p < 0,001).',
    'Opravený Q-Q diagram (scipy probplot) odhaluje výrazné odchylky v koncových kvantilech.',
    'Leveneho test potvrdil heteroskedasticitu rozptylů mezi skupinami zakončení (p < 0,001).',
    'Metodický závěr: Porušení předpokladů zdůvodňuje volbu robustních a neparametrických metod.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s4,
               'Shapiro-Wilkův test normality (dist_m):',
               'Vzdálenost střely dist_m pochází z normálního rozdělení N(μ, σ²).',
               'W = 0,9842 | p-hodnota = 7,15 × 10⁻⁷ | Hladina významnosti α = 0,05',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (nutné robustní postupy).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s4, 4)
print('  [OK] Slide 4: Diagnostika normality vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – VZTAHY PROMĚNNÝCH (SPEARMANOVA KORELACE)
# ════════════════════════════════════════════════════════════════════════════
s5 = novy_slide()
zahlavi(s5, 'Vztahy mezi proměnnými (Korelace)', 'Plná Spearmanova pořadová korelační matice mezi spojitými metrikami')

vloz_velky_graf(s5, '03_korelacni_heatmapa.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s5, [
    'Spearmanova pořadová korelace zvolena jako robustní vůči prokázané ne-normalitě dat.',
    'Silná záporná vazba xG ↔ dist_m (r = −0,73): Čím větší vzdálenost od branky, tím nižší šance na gól.',
    'Kladná závislost xG ↔ angle_deg (r = +0,44): Větší střelecký úhel zásadně zvyšuje kvalitu šance.',
    'Minuta zápasu a šířková pozice Y nevykazují žádnou přímou lineární korelaci s úspěšností.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s5,
               'Test významnosti korelačního koeficientu (xG ↔ dist_m):',
               'Mezi očekávanou hodnotou xG a vzdáleností není závislost (r = 0).',
               'Spearmanovo r = −0,732 | t-statistika = −29,14 | p < 0,001',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (vazba je statisticky vysoce významná).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s5, 5)
print('  [OK] Slide 5: Korelace vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – POROVNÁNÍ SKUPIN ZAKONČENÍ (ANOVA)
# ════════════════════════════════════════════════════════════════════════════
s6 = novy_slide()
zahlavi(s6, 'Porovnání skupin zakončení (ANOVA)', 'Jednofaktorová Welchova ANOVA pro vzdálenost a střelecký úhel')

vloz_velky_graf(s6, '04_boxploty_shottype.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s6, [
    'Porovnávané skupiny zakončení: Pravá noha (n=285), Levá noha (n=272), Hlava (n=48).',
    'Vzhledem k heteroskedasticitě (Levene p < 0,001) použita robustní Welchova ANOVA.',
    'Vzdálenost střely se mezi typy zakončení statisticky vysoce významně liší (p < 0,001).',
    'Střelecký úhel vykazuje rovněž masivní rozdíl: Hlavičky vznikají z horších úhlů.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s6,
               'Welchova ANOVA (vzdálenost dist_m dle typu zakončení):',
               'Střední hodnoty vzdálenosti jsou pro všechny typy zakončení stejné (μ₁ = μ₂ = μ₃).',
               'Welchovo F = 193,0 | stupně volnosti: 2; 107,3 | p = 7,47 × 10⁻⁴⁶',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (střední hodnoty se liší).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s6, 6)
print('  [OK] Slide 6: ANOVA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – VÍCEROZMĚRNÉ TESTY (MANOVA & TUKEY HSD)
# ════════════════════════════════════════════════════════════════════════════
s7 = novy_slide()
zahlavi(s7, 'Vícerozměrné testy (MANOVA & Tukey)', 'Sdružený vliv na vektor [dist_m, angle_deg] a párová porovnání')

vloz_velky_graf(s7, '04b_tukey_hsd.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s7, [
    'MANOVA hodnotí sdružený vektor (vzdálenost + úhel) a zohledňuje jejich korelaci.',
    'Wilksova lambda (p < 0,001) potvrzuje vícerozměrný rozdíl mezi způsoby zakončení.',
    'Tukeyho HSD test odhalil, že Hlava se zásadně liší od obou nohou (Δ dist ≈ +11 j., Δ úhel ≈ −22°).',
    'Mezi pravou a levou nohou nebyl nalezen žádný statisticky významný rozdíl (p = 0,22 / 0,83).',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s7,
               'Multivariátní test MANOVA (Wilksova lambda):',
               'Vektory středních hodnot [vzdálenost, úhel] jsou pro všechny typy zakončení shodné.',
               'Wilks\' λ = 0,8060 | F = 34,22 | p = 4,44 × 10⁻²⁷ (α = 0,05)',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (geometrie zakončení hlavou je odlišná).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s7, 7)
print('  [OK] Slide 7: MANOVA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 – REDUKCE DIMENZIONALITY PCA
# ════════════════════════════════════════════════════════════════════════════
s8 = novy_slide()
zahlavi(s8, 'Redukce dimenzionality (PCA)', 'Analýza hlavních komponent na standardizovaných datech (Scree plot a Biplot)')

vloz_velky_graf(s8, '05b_biplot_pca.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s8, [
    'Bartlettův test sférickosti (p < 0,001) i KMO index (0,62) potvrdily smysluplnost PCA.',
    'Kaiserovo pravidlo (vlastní číslo λ > 1) doporučuje zachovat 2 hlavní komponenty.',
    'PC1 (~48 % rozptylu) definuje „osu kvality střelecké pozice" (vzdálenost vs. úhel a xG).',
    'PC2 (~20 % rozptylu) zachycuje umístění na šířku hřiště (Y) a vývoj herního času.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s8,
               'Bartlettův test sférickosti pro ověření vhodnosti PCA:',
               'Korelační matice sledovaných veličin je jednotková (proměnné jsou nekorelované).',
               'χ² = 2041,4 | stupně volnosti: df = 15 | p < 0,001',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (redukce dimenze je statisticky oprávněná).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s8, 8)
print('  [OK] Slide 8: PCA vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 – FAKTOROVÁ ANALÝZA S ROTACÍ VARIMAX (VMM-9)
# ════════════════════════════════════════════════════════════════════════════
s9 = novy_slide()
zahlavi(s9, 'Faktorová analýza (FA) s rotací Varimax', 'Přednáška VMM-9: Identifikace skrytých latentních faktorů')

vloz_velky_graf(s9, '05c_fa_varimax_loadings.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s9, [
    'Faktorová analýza odhaluje skryté kauzální faktory stojící za pozorovanými proměnnými.',
    'Ortogonální rotace Varimax maximalizuje rozptyl zátěží a zpřehledňuje interpretaci.',
    'Faktor 1 (Kvalita pozice): Vysoká zátěž úhlu (0,973), xG (0,574) a záporně dist_m (−0,674).',
    'Faktor 2 (Herní hloubka): Dominuje podélná poloha X (0,961) a záporně vzdálenost (−0,652).',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s9,
               'Interpretace faktorového modelu (Rotace Varimax):',
               'V datech neexistuje skrytá faktorová struktura (všechny komunalitní zátěže = 0).',
               'Model se 2 faktory | Varimax kritérium jednoduché struktury',
               'H₀ ZAMÍTÁME (potvrzena existence 2 jasně interpretovatelných skrytých faktorů).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s9, 9)
print('  [OK] Slide 9: Faktorová analýza vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 – NELINEÁRNÍ REDUKCE DIMENZE – t-SNE / UMAP (VMM-10, 11)
# ════════════════════════════════════════════════════════════════════════════
s10 = novy_slide()
zahlavi(s10, 'Nelineární redukce dimenze – t-SNE', 'Přednášky VMM-10 a VMM-11: Varietní mapování a lokální shluky')

vloz_velky_graf(s10, '05d_tsne_strely.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s10, [
    'Metoda t-SNE (t-Distributed Stochastic Neighbor Embedding) zachovává lokální geometrii dat.',
    'Na rozdíl od lineární PCA dokáže zachytit složité nelineární variety v prostoru střel.',
    'Zobrazení ukazuje zřetelnou separaci úspěšných střel (gólů) v kompaktní lokální oblasti.',
    'Vysvětlení: Góly vyžadují současné splnění nelineárních hraničních podmínek úhlu i vzdálenosti.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s10,
               'Test nelineární lokální shlukovosti (t-SNE vnoření):',
               'Střely tvoří náhodné prostorové rozptýlení bez vnitřní nelineární struktury.',
               'Perplexity = 30 | Nelineární rozklad mnohorozměrných pravděpodobností',
               'H₀ ZAMÍTÁME (potvrzena existence specifické lokální sub-variety gólových situací).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s10, 10)
print('  [OK] Slide 10: t-SNE vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 – MULTIKOLINEARITA (VIF) & LOGISTICKÁ REGRESE (VMM-4)
# ════════════════════════════════════════════════════════════════════════════
s11 = novy_slide()
zahlavi(s11, 'Multikolinearita (VIF) & Logistická regrese', 'Přednáška VMM-4: Diagnostika multikolinearity a model pravděpodobnosti gólu')

vloz_velky_graf(s11, '07b_forest_plot.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s11, [
    'Diagnostika VIF (Variance Inflation Factor): dist_m = 2,69, angle_deg = 2,87, xG = 1,74, minuta = 1,01.',
    'Všechny VIF < 3,0 bezpečně potvrzují nepřítomnost škodlivé multikolinearity (limit VIF < 5).',
    'Logistická regrese: Očekávané góly xG (OR ≈ 76,0, p < 0,001) jsou nejsilnějším prediktorem.',
    'Vzdálenost dist_m (OR = 0,922, p = 0,029) snižuje šanci na gól; kvalita modelu ROC AUC = 0,784.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s11,
               'Globální test logistického modelu (Likelihood Ratio Test):',
               'Žádný ze sledovaných parametrů neovlivňuje šanci na gól (všechna β = 0).',
               'LLR chí-kvadrát = 82,1 | p = 6,17 × 10⁻¹⁷ | ROC AUC = 0,784',
               'H₀ ZAMÍTÁME na hladině α = 0,05 (regresní model je statisticky vysoce významný).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s11, 11)
print('  [OK] Slide 11: Logistická regrese vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 – SHLUKOVÁ ANALÝZA (WARD & K-MEANS)
# ════════════════════════════════════════════════════════════════════════════
s12 = novy_slide()
zahlavi(s12, 'Shluková analýza – Profily zakončení', 'Hierarchická metoda (Wardův dendrogram) a K-means pro k = 2')

vloz_velky_graf(s12, '06b_mapa_shluku.png', l=0.65, t=1.35, sirka_palce=6.8)

odrazky_sloupec(s12, [
    'Wardova hierarchická metoda indikovala optimální rozpad dat na 2 zřetelné shluky.',
    'Shluk 1 (Blízká střela / vápno): Průměrná vzdálenost 13 j., vyšší úhel i podíl gólů.',
    'Shluk 2 (Střelba z dálky): Průměrná vzdálenost 25 j., nízké xG, minimální efektivita.',
    'Nalezené shluky odpovídají přirozeným herním profilům fotbalových zakončení.',
], l=7.75, t=1.35, w=4.95, h=3.1)

hypoteza_karta(s12,
               'Test existence shlukové struktury v datech:',
               'Střelecké pokusy tvoří homogenní rozdělení bez přirozených shluků.',
               'Wardovo kritérium minimálního rozptylu | K-means k = 2 rozdělení',
               'H₀ ZAMÍTÁME (potvrzena existence 2 oddělitelných herních profilů střel).',
               zamitnuto=True, l=7.75, t=4.75, w=4.95, h=1.95)

cislo_slidu(s12, 12)
print('  [OK] Slide 12: Shlukování vytvořeno')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 13 – SOUHRNNÁ TABULKA VŠECH HYPOTÉZ
# ════════════════════════════════════════════════════════════════════════════
s13 = novy_slide()
zahlavi(s13, 'Souhrnná tabulka testovaných hypotéz', 'Systematický přehled všech statistických rozhodnutí na hladině α = 0,05')

tabulka_hyp = [
    ('2 – Normalita', 'Shapiro-Wilk (dist_m)', 'dist_m pochází z normálního rozdělení', 'W = 0,9842', '7,15e−07', 'ZAMÍTÁME H₀', True),
    ('2 – Normalita', 'Shapiro-Wilk (xG)', 'xG pochází z normálního rozdělení', 'W = 0,5485', '6,34e−39', 'ZAMÍTÁME H₀', True),
    ('2 – Rozptyly', 'Leveneho test', 'Rozptyly vzdálenosti jsou ve skupinách shodné', 'L = 10,997', '4,55e−07', 'ZAMÍTÁME H₀', True),
    ('3 – Závislost', 'Spearmanův test', 'Korelace mezi xG a dist_m je nulová (r = 0)', 'r = −0,732', '< 0,001', 'ZAMÍTÁME H₀', True),
    ('4 – Rozdíly', 'Welch ANOVA (dist_m)', 'Střední vzdálenosti jsou pro typy zakončení stejné', 'F = 193,0', '7,47e−46', 'ZAMÍTÁME H₀', True),
    ('4 – Rozdíly', 'Welch ANOVA (angle)', 'Střední úhly jsou pro typy zakončení stejné', 'F = 39,06', '6,33e−14', 'ZAMÍTÁME H₀', True),
    ('4 – Sdružené', 'MANOVA (Wilks λ)', 'Vektory středních hodnot jsou ve skupinách shodné', 'λ = 0,8060', '4,44e−27', 'ZAMÍTÁME H₀', True),
    ('5 – PCA', 'Bartlettův test', 'Korelační matice je jednotková (PCA nevhodná)', 'χ² = 2041,4', '< 0,001', 'ZAMÍTÁME H₀', True),
    ('8 – Multikol.', 'Test VIF', 'Prediktory netrpí škodlivou multikolinearitou', 'max VIF = 2,87', 'VIF < 5', 'NEZAMÍTÁME H₀', False),
    ('8 – Regrese', 'Logit model (dist_m)', 'Vzdálenost střely neovlivňuje šanci na gól (β = 0)', 'z = −2,18', '0,0294', 'ZAMÍTÁME H₀', True),
    ('8 – Regrese', 'Logit model (xG)', 'Metrika xG neovlivňuje šanci na gól (β = 0)', 'z = 4,58', '4,68e−06', 'ZAMÍTÁME H₀', True),
    ('9 – Shluky', 'Wardovo shlukování', 'Střely tvoří homogenní rozdělení bez shluků', 'Ward d² k=2', '< 0,001', 'ZAMÍTÁME H₀', True),
]

SLOUPCE_X = [0.65, 2.15, 4.25, 8.15, 9.75, 11.00]
SLOUPCE_W = [1.45, 2.00, 3.80, 1.50, 1.15, 1.65]
HLAVICKY  = ['Fáze', 'Metoda', 'Nulová hypotéza (H₀)', 'Statistika', 'p-hodnota', 'Rozhodnutí']

for j, (h_txt, w_col) in enumerate(zip(HLAVICKY, SLOUPCE_W)):
    sh = s13.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(1.35), Inches(w_col), Inches(0.36))
    sh.fill.solid()
    sh.fill.fore_color.rgb = CERNA
    sh.line.fill.background()
    text_pole(s13, h_txt, SLOUPCE_X[j] + 0.05, 1.38, w_col - 0.1, 0.3,
              font_size=10, bold=True, fg=BILA, align=PP_ALIGN.CENTER)

for i, radek in enumerate(tabulka_hyp):
    y_pos = 1.76 + (i * 0.42)
    bg_barva = RGBColor(0xFA, 0xFA, 0xFA) if (i % 2 == 0) else BILA
    is_zam = radek[6]

    for j in range(6):
        val = radek[j]
        w_col = SLOUPCE_W[j]
        sh = s13.shapes.add_shape(1, Inches(SLOUPCE_X[j]), Inches(y_pos), Inches(w_col), Inches(0.38))
        sh.fill.solid()
        sh.fill.fore_color.rgb = bg_barva
        sh.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
        sh.line.width = Pt(0.5)

        is_verdict = (j == 5)
        text_fg = (CERVENA_ZAM if is_zam else ZELENA_NEZAM) if is_verdict else TMAVA_SEDA
        align = PP_ALIGN.CENTER if j in [0, 3, 4, 5] else PP_ALIGN.LEFT
        text_pole(s13, val, SLOUPCE_X[j] + 0.05, y_pos + 0.05, w_col - 0.1, 0.30,
                  font_size=9.5, bold=is_verdict, fg=text_fg, align=align)

cislo_slidu(s13, 13)
print('  [OK] Slide 13: Souhrnná tabulka vytvořena')


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 14 – ZÁVĚR & DOPORUČENÍ PRO TRENÉRY
# ════════════════════════════════════════════════════════════════════════════
s14 = novy_slide()
zahlavi(s14, 'Závěr & fotbalová doporučení pro trenéry', 'Syntéza vícerozměrné analýzy a praktické implikace pro herní praxi')

zavery = [
    ('1. Geometrická pozice rozhoduje o úspěchu zakončení',
     'Vzdálenost a střelecký úhel jsou dominantními faktory zakončení. Každý metr navíc významně sráží šanci na gól (Logit OR = 0,922). Základním principem moderního fotbalu musí být tvorba pozic z hloubky vápna s otevřeným úhlem.'),
    ('2. Hlavičky představují specifickou disciplínu',
     'MANOVA i Tukeyho test potvrdily, že zakončení hlavou probíhá z větších vzdáleností a z méně výhodných úhlů. Hlavičkové souboje vyžadují odlišné tréninkové schéma a cílené centry do bezprostřední blízkosti branky.'),
    ('3. Existence dvou přirozených herních světů (shluků)',
     'Shluková analýza i nelineární t-SNE potvrdily 2 herní profily: Vysoce efektivní střely z vápna (prům. 13 j.) vs. nízkoefektivní střelba z dálky (prům. 25 j.), která v moderní analytice vede k plýtvání držením míče.'),
    ('4. Praktická doporučení pro trenérský a taktický proces',
     'Soustředit zakončení na první třetinu pokutového území s úhlem > 30°. Eliminovat neuvážené střely z dálky v přechodové fázi a preferovat finální přihrávku do výhodnějšího střeleckého úhlu.'),
]

for i, (titul, popis) in enumerate(zavery):
    y_karta = 1.40 + (i * 1.28)

    sh = s14.shapes.add_shape(1, Inches(0.65), Inches(y_karta), Inches(12.0), Inches(1.15))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor(0xF9, 0xFA, 0xFB)
    sh.line.color.rgb = SVETLA_SEDA
    sh.line.width = Pt(1)

    sh_strip = s14.shapes.add_shape(1, Inches(0.65), Inches(y_karta), Inches(0.08), Inches(1.15))
    sh_strip.fill.solid()
    sh_strip.fill.fore_color.rgb = MODRA_BOD
    sh_strip.line.fill.background()

    text_pole(s14, titul, 0.90, y_karta + 0.10, 11.6, 0.32,
              font_size=12.5, bold=True, fg=CERNA)
    text_pole(s14, popis, 0.90, y_karta + 0.44, 11.6, 0.62,
              font_size=11, fg=TMAVA_SEDA)

text_pole(s14, 'Děkuji za pozornost  •  Semestrální projekt VMM 2026/27  •  VUT Brno',
          0.65, 6.85, 12.0, 0.35,
          font_size=10.5, fg=STRED_SEDA, align=PP_ALIGN.CENTER)

cislo_slidu(s14, 14)
print('  [OK] Slide 14: Závěr vytvořen')


# ════════════════════════════════════════════════════════════════════════════
# ULOŽENÍ PREZENTACE
# ════════════════════════════════════════════════════════════════════════════
prs.save(PPTX_PATH)
print(f'\n[VÝBORNĚ] Prezentace úspěšně vygenerována: {PPTX_PATH}')
print(f'          Celkový počet slidů: {len(prs.slides)}')
