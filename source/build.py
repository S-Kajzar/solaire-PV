#!/usr/bin/env python3
"""Génère ../index.html à partir du gabarit et du contenu du sujet.

Le bloc <style>, le moteur Grading et le moteur applicatif sont repris
tels quels depuis gabarit-exercice-interactif.html ; seuls le contenu du
sujet et les paramètres de contenu du moteur (durée conseillée, DECOR,
DR_NAMES) sont fournis ici.

Usage : python3 source/build.py
"""
import base64
import html
import json
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "index.html")
GABARIT = os.path.join(ICI, "gabarit-exercice-interactif.html")

TITRE = "Le solaire photovoltaïque : alimenter une pompe de récupération d'eau de pluie"
TITRE_COURT = "Le solaire photovoltaïque"


# ---------------------------------------------------------------- images
def data_uri(nom):
    chemin = os.path.join(ICI, "img", nom)
    mime = {"jpg": "image/jpeg", "svg": "image/svg+xml"}.get(nom.rsplit(".", 1)[-1], "image/png")
    with open(chemin, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode("ascii"))


IMG = {k: data_uri(v) for k, v in {
    "synoptique": "synoptique.svg",
    "schema": "schema-principe.png",
    "chaine": "chaine-energie.png",
    "batterie": "batterie-12v.png",
}.items()}


# ---------------------------------------------------------------- unités
U_A = {"label": "A", "accept": ["a", "ampere", "amperes", "amp"]}
U_V = {"label": "V", "accept": ["v", "volt", "volts"]}
U_W = {"label": "W", "accept": ["w", "watt", "watts"]}
U_KW = {"label": "kW", "accept": ["kw", "kilowatt", "kilowatts"]}
U_WH = {"label": "W·h", "accept": ["wh", "wattheure", "wattheures"]}
U_WH_J = {"label": "W·h", "accept": ["wh", "wattheure", "wattheures", "whj", "wh/j", "wh/jour", "whjour",
                                     "wattheurejour", "wattheuresjour"]}
U_KWH = {"label": "kW·h", "accept": ["kwh", "kilowattheure", "kilowattheures"]}
U_KWH_J = {"label": "kW·h", "accept": ["kwh", "kilowattheure", "kilowattheures", "kwhj", "kwh/j",
                                       "kwh/jour", "kwhjour"]}
U_AH = {"label": "A·h", "accept": ["ah", "ampereheure", "ampereheures", "amperheure"]}
U_H = {"label": "h", "accept": ["h", "heure", "heures", "hr"]}


def num(value, tol=0.006, unit=None, variants=None):
    g = {"type": "num", "value": value, "absTol": tol}
    if unit:
        g["unit"] = unit
    if variants:
        g["variants"] = variants
    return g


def var(value, tol, unit):
    """Variante (autre unité) : retenue seulement si l'unité est écrite."""
    return {"value": value, "absTol": tol, "unit": unit, "strictUnit": True}


def kw(any_, forbid=None):
    g = {"type": "kw", "any": any_}
    if forbid:
        g["forbid"] = forbid
    return g


H_UNITE = ("Arrondir au centième. Saisis la valeur <strong>avec son unité</strong> : "
           "l'unité vaut la moitié des points de la question.")
H_UNITE_ENTIER = ("Valeur entière. Saisis la valeur <strong>avec son unité</strong> : "
                  "l'unité vaut la moitié des points de la question.")
H_ENTIER = "Réponse en nombre entier (aucune unité n'est attendue)."
H_MOT = "Un ou deux mots suffisent ; la casse et les accents sont sans importance."
H_VERBE = "Un verbe à l'infinitif."


# ---------------------------------------------------------------- documents
DOCS = [
    # clé, intitulé, nature, contenu
    ("DP1", "Synoptique de l'installation", "Dossier présentation",
     '<img class="doc-img" src="%s" width="1000" height="690" alt="Synoptique : panneaux solaires, régulateur, '
     'batteries 24 V, onduleur 230 V, réseau EDF, inverseur de source, pompe, cuve d\'eau pluviale, vanne 3 voies, '
     'eau de ville et toilettes.">'
     '<p class="doc-cap">Chaîne électrique en rouge, circuit d\'eau en bleu. En cas de manque d\'eau dans la cuve, '
     'la vanne 3 voies bascule sur l\'eau de ville.</p>' % IMG["synoptique"]),
    ("DP2", "Schéma de principe", "Dossier présentation",
     '<img class="doc-img" src="%s" width="669" height="381" alt="Schéma de principe : panneaux, élément 1, '
     'élément 2, élément 3, inverseur de source, réseau EDF et pompe.">'
     '<p class="doc-cap">Les éléments repérés <strong>1</strong>, <strong>2</strong> et <strong>3</strong> sont à '
     'identifier.</p>' % IMG["schema"]),
    ("DT1", "Chaîne d'énergie", "Dossier technique",
     '<img class="doc-img" src="%s" width="1200" height="248" alt="Chaîne d\'énergie : Produire localement, '
     'Alimenter, bloc à compléter, Convertir, Distribuer (inverseur de source), Convertir, puis eau sous pression.">'
     '<p class="doc-cap">Chaîne d\'énergie (ou chaîne de puissance) du système, à compléter : fonction du '
     '3<sup>e</sup> bloc, composant réel de chaque bloc et nature de l\'énergie entre les blocs.</p>' % IMG["chaine"]),
    ("DT2", "Caractéristiques des composants", "Dossier technique",
     '<div class="doc-text"><h3>Caractéristiques des composants</h3>'
     '<table class="t"><thead><tr><th>Composant</th><th>Caractéristiques</th></tr></thead><tbody>'
     '<tr><td>Panneau solaire</td><td>Puissance crête P = 75 W ; tension à ses bornes U = 17 V. Cellules en série '
     'dans chaque branche, branches en dérivation.</td></tr>'
     '<tr><td>Cellule photovoltaïque</td><td>U<sub>cel</sub> = 0,5 V ; I<sub>cel</sub> = 450 mA</td></tr>'
     '<tr><td>Pompe monophasée</td><td>230 V ; puissance utile 900 W ; cos φ = 0,78 ; rendement η = 0,64 ; '
     'fonctionne en moyenne 1 h par jour à pleine puissance</td></tr>'
     '<tr><td>Onduleur</td><td>24 V continu / 230 V alternatif ; rendement 98 %%</td></tr>'
     '<tr><td>Batterie élémentaire</td><td>12 V — 215 A·h</td></tr>'
     '<tr><td>Cahier des charges</td><td>Autonomie de 7 jours sans soleil</td></tr>'
     '</tbody></table>'
     '<p><img src="%s" width="181" height="102" alt="Batterie élémentaire 12 V"></p></div>' % IMG["batterie"]),
]


def chips(keys):
    return " ".join('<button type="button" class="doc-chip" data-doc="%s" aria-pressed="false">%s</button>'
                    % (k, k) for k in keys)


# ---------------------------------------------------------------- sujet
PARTS = [
    {"num": "1", "title": "Présentation de l'installation", "minutes": 20, "duration": "20 min"},
    {"num": "2", "title": "Les panneaux solaires photovoltaïques", "minutes": 15, "duration": "15 min"},
    {"num": "3", "title": "Le stockage de l'énergie", "minutes": 45, "duration": "45 min"},
]

ELEM_REGUL = [[["regulateur", "regulateurs", "regulation"]]]
ELEM_BATT = [[["batterie", "batteries", "accumulateur", "accumulateurs", "accus", "accu"]]]
ELEM_OND = [[["onduleur", "onduleurs"]], [["convertisseur"], ["continu", "dc", "alternatif", "ac"]]]
ROLE_STOCKER = [[["stocker", "stockage", "stocke", "emmagasiner", "accumuler", "accumulation", "reserver"]]]

P1_INTRO = """
      <p>Une installation récupère les eaux de pluie d'un bâtiment et les envoie vers les toilettes. Le système
      utilise une <strong>pompe monophasée</strong> alimentée à partir de deux sources électriques : le
      <strong>système photovoltaïque</strong> et le <strong>réseau EDF</strong>, entre lesquelles un inverseur de
      source choisit. En cas de manque d'eau dans la cuve, les toilettes sont alimentées par le réseau d'eau public
      (<button type="button" class="doc-chip" data-doc="DP1" aria-pressed="false">DP1</button>).</p>"""

P1_FIG_SCHEMA = """
      <figure class="fig"><img src="%s" width="669" height="381" alt="Schéma de principe avec les éléments 1, 2 et 3 à identifier.">
        <figcaption>Schéma de principe (DP2) : les éléments repérés <strong>1</strong>, <strong>2</strong> et
        <strong>3</strong> sont à identifier.</figcaption></figure>""" % IMG["schema"]

P1_FIG_CHAINE = """
      <figure class="fig"><img src="%s" width="1200" height="248" alt="Chaîne d'énergie à compléter.">
        <figcaption>Chaîne d'énergie du système (DT1). Les blocs sont numérotés de 1 à 6 de gauche à droite :
        1 « Produire localement », 2 « Alimenter », 3 à compléter, 4 « Convertir », 5 « Distribuer »
        (inverseur de source), 6 « Convertir ».</figcaption></figure>""" % IMG["chaine"]

P2_INTRO = """
      <div class="data"><p class="data-title">Données</p><ul>
        <li>Panneau solaire : puissance crête <strong>P = 75 W</strong>, tension à ses bornes <strong>U = 17 V</strong>.</li>
        <li>Le panneau est constitué de cellules associées <strong>en série dans chaque branche</strong>, les branches
        étant elles-mêmes montées <strong>en dérivation</strong>.</li>
        <li>Chaque cellule délivre une tension <strong>U<sub>cel</sub> = 0,5 V</strong> et un courant
        <strong>I<sub>cel</sub> = 450 mA</strong>.</li></ul></div>"""

P3_INTRO = """
      <p>Il s'agit maintenant de déterminer la ou les batteries nécessaires au système.</p>
      <div class="data"><p class="data-title">Données techniques</p><ul>
        <li>Pompe monophasée : <strong>230 V</strong>, <strong>900 W</strong> (puissance utile),
        <strong>cos φ = 0,78</strong>, rendement <strong>η = 0,64</strong>.</li>
        <li>La pompe fonctionne en moyenne <strong>1 heure par jour</strong>, à pleine puissance.</li>
        <li>Onduleur 24 V / 230 V : rendement <strong>98 %</strong>.</li>
        <li>Batteries disponibles : <strong>12 V — 215 A·h</strong>.</li>
        <li>L'installation doit pouvoir fonctionner <strong>7 jours sans soleil</strong>.</li></ul></div>"""

# Chaque partie : liste de blocs ("html", texte) | ("qbar", numéro, titre, docs) | ("q", question)
CONTENT = {
    "1": [
        ("html", P1_INTRO),
        ("qbar", "Q1.1 à Q1.6", "Identifier les constituants de la chaîne électrique", ["DP1", "DP2"]),
        ("html", P1_FIG_SCHEMA),
        ("q", {"id": "q1_1", "label": "Q1.1", "stem": "Donner le nom de l'élément repéré 1 sur le schéma de principe.",
               "hint": H_MOT, "grader": kw(ELEM_REGUL), "expected": "le régulateur (de charge)",
               "why": "<p>On suit l'énergie depuis les panneaux : le premier bloc rencontré, placé entre la production "
                      "et le stockage, est le <strong>régulateur de charge</strong> (« RÉGULATEUR » sur le synoptique DP1).</p>"}),
        ("q", {"id": "q1_2", "label": "Q1.2", "stem": "Donner le nom de l'élément repéré 2.",
               "hint": H_MOT, "grader": kw(ELEM_BATT), "expected": "les batteries (accumulateurs)",
               "why": "<p>Le symbole formé de traits longs et courts alternés est celui d'un <strong>accumulateur</strong>. "
                      "Les <strong>batteries</strong> sont raccordées en dérivation sur le bus continu 24 V "
                      "(« BATTERIES (24 V) » sur DP1).</p>"}),
        ("q", {"id": "q1_3", "label": "Q1.3", "stem": "Donner le nom de l'élément repéré 3.",
               "hint": H_MOT, "grader": kw(ELEM_OND), "expected": "l'onduleur (convertisseur continu → alternatif)",
               "why": "<p>Le carré barré portant un trait continu « ⎓ » d'un côté et une sinusoïde « ∿ » de l'autre est "
                      "le symbole d'un convertisseur continu → alternatif : l'<strong>onduleur</strong>. Il précède "
                      "l'inverseur de source et le réseau EDF, tous deux en 230 V alternatif.</p>"}),
        ("q", {"id": "q1_4", "label": "Q1.4", "stem": "Donner, en un seul verbe, le rôle de l'élément 1.",
               "hint": H_VERBE,
               "grader": kw([[["reguler", "regulation", "regule", "reguller"]],
                             [["controler", "gerer", "surveiller", "limiter"], ["charge", "charger"]],
                             [["proteger", "protection"]]]),
               "expected": "réguler (la charge des batteries)",
               "why": "<p><strong>Réguler</strong> : le régulateur contrôle la charge des batteries à partir de la tension "
                      "fournie par les panneaux. Il évite la surcharge et la décharge profonde, qui détruiraient les "
                      "accumulateurs. « Protéger les batteries » ou « contrôler la charge » sont acceptés.</p>"}),
        ("q", {"id": "q1_5", "label": "Q1.5", "stem": "Donner, en un seul verbe, le rôle de l'élément 2.",
               "hint": H_VERBE, "grader": kw(ROLE_STOCKER), "expected": "stocker (l'énergie électrique)",
               "why": "<p><strong>Stocker</strong> : les batteries emmagasinent l'énergie produite le jour pour la restituer "
                      "la nuit ou par temps couvert ; c'est ce qui donne au système son autonomie.</p>"}),
        ("q", {"id": "q1_6", "label": "Q1.6", "stem": "Donner, en un seul verbe, le rôle de l'élément 3.",
               "hint": H_VERBE,
               "grader": kw([[["convertir", "conversion", "onduler", "transformer", "converti"]]]),
               "expected": "convertir (le continu en alternatif)",
               "why": "<p><strong>Convertir</strong> : l'onduleur convertit la tension continue 24 V du bus batteries en "
                      "tension alternative 230 V, la seule utilisable par la pompe monophasée.</p>"}),

        ("qbar", "Q1.7 à Q1.12", "Compléter la chaîne d'énergie", ["DT1", "DP1"]),
        ("html", P1_FIG_CHAINE),
        ("q", {"id": "q1_7", "label": "Q1.7", "stem": "Donner la fonction (verbe) du 3e bloc de la chaîne d'énergie.",
               "hint": H_VERBE, "grader": kw(ROLE_STOCKER), "expected": "STOCKER",
               "why": "<p>Le 3<sup>e</sup> bloc est encadré par « Alimenter » (régulateur) et « Convertir » (onduleur) : "
                      "entre les deux se trouvent les batteries, donc la fonction <strong>STOCKER</strong>.</p>"}),
        ("q", {"id": "q1_8", "label": "Q1.8", "stem": "Quel composant réel assure le bloc 1 « Produire localement » ?",
               "hint": H_MOT,
               "grader": kw([[["panneau", "panneaux", "module", "modules", "capteur", "capteurs", "cellule", "cellules",
                               "photovoltaique", "photovoltaiques"]]]),
               "expected": "les panneaux (solaires) photovoltaïques",
               "why": "<p>Les <strong>panneaux photovoltaïques</strong> sont les seuls éléments qui produisent de l'énergie "
                      "électrique sur le site (le réseau EDF, lui, la fournit de l'extérieur).</p>"}),
        ("q", {"id": "q1_9", "label": "Q1.9", "stem": "Quel composant réel assure le bloc 2 « Alimenter » ?",
               "hint": H_MOT, "grader": kw(ELEM_REGUL), "expected": "le régulateur",
               "why": "<p>Juste après les panneaux, le <strong>régulateur</strong> dose l'énergie envoyée vers les batteries "
                      "et vers l'onduleur : il « alimente » la suite de la chaîne.</p>"}),
        ("q", {"id": "q1_10", "label": "Q1.10", "stem": "Quel composant réel assure le bloc 3, dont tu as trouvé la fonction ?",
               "hint": H_MOT, "grader": kw(ELEM_BATT), "expected": "les batteries",
               "why": "<p>La fonction « stocker » est assurée par les <strong>batteries</strong> (accumulateurs).</p>"}),
        ("q", {"id": "q1_11", "label": "Q1.11", "stem": "Quel composant réel assure le bloc 4 « Convertir » ?",
               "hint": H_MOT, "grader": kw(ELEM_OND), "expected": "l'onduleur",
               "why": "<p>L'<strong>onduleur</strong> convertit le continu 24 V en alternatif 230 V. Le bloc 5 "
                      "« Distribuer » est l'inverseur de source, déjà indiqué : il choisit entre l'onduleur et le "
                      "réseau EDF.</p>"}),
        ("q", {"id": "q1_12", "label": "Q1.12", "stem": "Quel composant réel assure le bloc 6 « Convertir » ?",
               "hint": H_MOT,
               "grader": kw([[["pompe", "motopompe", "electropompe"]], [["moteur"]]], forbid=["onduleur"]),
               "expected": "la pompe (son moteur)",
               "why": "<p>Le dernier bloc fournit « eau sous pression » : c'est la <strong>pompe</strong>, dont le moteur "
                      "convertit l'énergie électrique en énergie hydraulique.</p>"}),

        ("qbar", "Q1.13 à Q1.16", "Nature de l'énergie le long de la chaîne", ["DT1"]),
        ("q", {"id": "q1_13", "label": "Q1.13", "stem": "Quelle est la nature de l'énergie qui entre dans le bloc « Produire localement » ?",
               "hint": "Deux mots au maximum.",
               "grader": kw([[["solaire", "lumineuse", "lumiere", "rayonnement", "rayonnante", "radiative", "photons"]]]),
               "expected": "énergie solaire (rayonnement lumineux)",
               "why": "<p>En entrée de la chaîne, les panneaux reçoivent l'<strong>énergie solaire</strong>, c'est-à-dire le "
                      "rayonnement lumineux du Soleil.</p>"}),
        ("q", {"id": "q1_14", "label": "Q1.14", "stem": "Quelle est la nature de l'énergie entre le régulateur et l'onduleur ?",
               "hint": "Deux mots au maximum : précise la forme du courant.",
               "grader": kw([[["electrique"], ["continue", "continu", "dc"]]],
                            forbid=["alternative", "alternatif", "ac"]),
               "expected": "énergie électrique continue",
               "why": "<p>Des panneaux jusqu'à l'onduleur, tout fonctionne en <strong>courant continu</strong> (bus 24 V des "
                      "batteries) : l'énergie est <strong>électrique continue</strong>. Répondre seulement « électrique » "
                      "ne suffit pas, puisque la même chaîne transporte aussi de l'énergie électrique alternative.</p>"}),
        ("q", {"id": "q1_15", "label": "Q1.15", "stem": "Quelle est la nature de l'énergie en sortie de l'onduleur ?",
               "hint": "Deux mots au maximum : précise la forme du courant.",
               "grader": kw([[["electrique"], ["alternative", "alternatif", "ac"]]],
                            forbid=["continue", "continu", "dc"]),
               "expected": "énergie électrique alternative",
               "why": "<p>L'onduleur délivre du 230 V, 50 Hz : l'énergie est <strong>électrique alternative</strong>, "
                      "compatible avec le réseau EDF et avec la pompe monophasée.</p>"}),
        ("q", {"id": "q1_16", "label": "Q1.16", "stem": "Quelle est la nature de l'énergie en sortie de la pompe ?",
               "hint": "Deux mots au maximum.",
               "grader": kw([[["hydraulique"]], [["pression"]]], forbid=["electrique"]),
               "expected": "énergie hydraulique",
               "why": "<p>La pompe met l'eau sous pression (indiqué en sortie de la chaîne) : c'est de l'<strong>énergie "
                      "hydraulique</strong>. L'énergie mécanique est celle de l'arbre du moteur, <em>à l'intérieur</em> du "
                      "bloc pompe ; elle n'est pas ce qui sort de la chaîne.</p>"}),
    ],

    "2": [
        ("html", P2_INTRO),
        ("qbar", "Q2.1 à Q2.4", "Dimensionner l'association des cellules", ["DT2"]),
        ("q", {"id": "q2_1", "label": "Q2.1", "stem": "Calculer le nombre de cellules associées en série dans une branche.",
               "hint": H_ENTIER, "grader": num(34, 0), "expected": "34 cellules",
               "why": "<p>Dans une branche, les cellules sont en série : leurs tensions s'additionnent et la tension de la "
                      "branche est celle du panneau.</p><p><strong>n = U ÷ U<sub>cel</sub> = 17 ÷ 0,5 = 34 cellules</strong>.</p>"}),
        ("q", {"id": "q2_2", "label": "Q2.2", "stem": "Calculer l'intensité du courant débité par le panneau.",
               "hint": H_UNITE, "grader": num(75 / 17, 0.006, U_A), "expected": "I = 4,41 A",
               "why": "<p>Le panneau fonctionne en continu, donc P = U × I, d'où :</p>"
                      "<p><strong>I = P ÷ U = 75 ÷ 17 = 4,411… ≈ 4,41 A</strong>.</p>"}),
        ("q", {"id": "q2_3", "label": "Q2.3", "stem": "En déduire le nombre de branches du panneau.",
               "hint": H_ENTIER, "grader": num(10, 0), "expected": "10 branches",
               "why": "<p>Les branches sont en dérivation : leurs courants s'additionnent, chaque branche débitant le courant "
                      "d'une cellule, soit 450 mA = 0,45 A.</p>"
                      "<p>N = I ÷ I<sub>cel</sub> = 4,41 ÷ 0,45 = 9,8.</p>"
                      "<p>On ne peut pas installer 9,8 branches : on arrondit <em>à l'entier supérieur</em> pour atteindre au "
                      "moins la puissance crête annoncée, soit <strong>10 branches</strong> (le panneau délivre alors "
                      "17 × 4,5 = 76,5 W, légèrement plus que les 75 W annoncés).</p>"}),
        ("q", {"id": "q2_4", "label": "Q2.4", "stem": "Déterminer le nombre total de cellules du panneau.",
               "hint": H_ENTIER, "grader": num(340, 0), "expected": "340 cellules",
               "why": "<p>Toutes les branches contiennent le même nombre de cellules :</p>"
                      "<p><strong>N<sub>total</sub> = 34 × 10 = 340 cellules</strong>.</p>"}),
        ("qbar", "Q2.5 et Q2.6", "Type d'association", ["DT2"]),
        ("q", {"id": "q2_5", "label": "Q2.5", "stem": "Comment les cellules sont-elles associées à l'intérieur d'une branche ?",
               "hint": "Un mot : série ou dérivation (parallèle).",
               "grader": kw([[["serie"]]], forbid=["parallele", "derivation"]), "expected": "en série",
               "why": "<p>Pour obtenir 17 V à partir de cellules de 0,5 V, il faut <strong>additionner les tensions</strong> : "
                      "les 34 cellules d'une branche sont montées <strong>en série</strong>.</p>"}),
        ("q", {"id": "q2_6", "label": "Q2.6", "stem": "Comment les branches sont-elles associées entre elles ?",
               "hint": "Un mot : série ou dérivation (parallèle).",
               "grader": kw([[["parallele", "derivation"]]], forbid=["serie"]), "expected": "en dérivation (parallèle)",
               "why": "<p>Pour obtenir 4,41 A à partir de branches de 0,45 A, il faut <strong>additionner les courants</strong> : "
                      "les 10 branches sont montées <strong>en dérivation (parallèle)</strong>.</p>"
                      "<p>Bilan : 10 branches en parallèle × 34 cellules en série chacune = 340 cellules.</p>"}),
    ],

    "3": [
        ("html", P3_INTRO),
        ("qbar", "Q3.1 à Q3.3", "Énergie à stocker", ["DT2"]),
        ("q", {"id": "q3_1", "label": "Q3.1", "stem": "Calculer la puissance consommée (absorbée) par la pompe.",
               "hint": H_UNITE, "grader": num(1406.25, 0.006, U_W, [var(1.40625, 0.006, U_KW)]),
               "expected": "P<sub>a</sub> = 1 406,25 W",
               "why": "<p>Les 900 W sont la puissance <em>utile</em> (mécanique) de la pompe ; le rendement permet de remonter "
                      "à la puissance <em>absorbée</em> :</p>"
                      "<p><strong>P<sub>a</sub> = P<sub>u</sub> ÷ η = 900 ÷ 0,64 = 1 406,25 W</strong>.</p>"
                      "<p>Vérification : cette valeur est confirmée par la mesure du courant (Q3.13).</p>"}),
        ("q", {"id": "q3_2", "label": "Q3.2", "stem": "En déduire l'énergie consommée chaque jour par la pompe.",
               "hint": H_UNITE, "grader": num(1406.25, 0.006, U_WH_J, [var(1.40625, 0.006, U_KWH_J)]),
               "expected": "E = 1 406,25 W·h par jour",
               "why": "<p>La pompe tourne 1 h par jour à pleine puissance :</p>"
                      "<p><strong>E = P<sub>a</sub> × t = 1 406,25 × 1 = 1 406,25 W·h</strong> par jour.</p>"
                      "<p>Le watt-heure (W·h) est l'unité attendue : une énergie n'est pas une puissance (W).</p>"}),
        ("q", {"id": "q3_3", "label": "Q3.3", "stem": "Calculer l'énergie qu'il est nécessaire de stocker dans les batteries.",
               "hint": H_UNITE, "grader": num(1406.25 * 7 / 0.98, 0.01, U_WH, [var(1406.25 * 7 / 0.98 / 1000, 0.006, U_KWH)]),
               "expected": "E<sub>stockée</sub> = 10 044,64 W·h (≈ 10,04 kW·h)",
               "why": "<p>Les batteries doivent couvrir <strong>7 jours</strong> de fonctionnement, et l'énergie transite par "
                      "l'onduleur, qui en perd 2 % au passage : il faut donc <em>diviser</em> par son rendement.</p>"
                      "<p>E<sub>7 jours</sub> = 1 406,25 × 7 = 9 843,75 W·h</p>"
                      "<p><strong>E<sub>stockée</sub> = 9 843,75 ÷ 0,98 = 10 044,64 W·h</strong></p>"
                      "<p>Attention au sens : l'onduleur prélève <em>plus</em> qu'il ne restitue, donc le résultat est "
                      "supérieur à 9 843,75 W·h (multiplier par 0,98 donnerait 9 646,88 W·h, valeur fausse).</p>"}),

        ("qbar", "Q3.4 à Q3.6", "Associer les batteries 12 V", ["DT2", "DP1"]),
        ("q", {"id": "q3_4", "label": "Q3.4", "stem": "Combien de batteries 12 V faut-il associer en série pour alimenter correctement l'onduleur ?",
               "hint": H_ENTIER, "grader": num(2, 0), "expected": "2 batteries en série",
               "why": "<p>L'onduleur est un modèle <strong>24 V</strong> / 230 V : il doit être alimenté sous 24 V. Les "
                      "batteries ne délivrent que 12 V ; pour <em>additionner les tensions</em>, on les monte en série :</p>"
                      "<p><strong>24 ÷ 12 = 2 batteries en série</strong>.</p>"}),
        ("q", {"id": "q3_5", "label": "Q3.5", "stem": "Quelle tension cet ensemble de batteries délivre-t-il ?",
               "hint": H_UNITE_ENTIER, "grader": num(24, 0, U_V), "expected": "U = 24 V",
               "why": "<p>En série, les tensions s'additionnent : <strong>12 + 12 = 24 V</strong>. Cet ensemble de "
                      "2 batteries constitue le « module » de base de l'installation.</p>"}),
        ("q", {"id": "q3_6", "label": "Q3.6", "stem": "Calculer l'énergie stockée par cet ensemble lorsqu'il est totalement chargé.",
               "hint": H_UNITE, "grader": num(5160, 0.006, U_WH, [var(5.16, 0.006, U_KWH)]),
               "expected": "E = 5 160 W·h",
               "why": "<p>En série, la capacité <em>ne change pas</em> : elle reste celle d'une batterie, 215 A·h. Seule la "
                      "tension double.</p><p><strong>E = U × Q = 24 × 215 = 5 160 W·h</strong>.</p>"
                      "<p>Erreur fréquente : doubler aussi la capacité (on trouverait 10 320 W·h). En série, on additionne "
                      "les tensions, jamais les capacités.</p>"}),

        ("qbar", "Q3.7 à Q3.12", "Nombre d'ensembles et batterie équivalente", ["DT2"]),
        ("q", {"id": "q3_7", "label": "Q3.7", "stem": "Calculer le quotient « énergie à stocker ÷ énergie stockée par un ensemble ».",
               "hint": "Arrondir au centième (grandeur sans unité).",
               "grader": num(1406.25 * 7 / 0.98 / 5160, 0.006), "expected": "1,95",
               "why": "<p>On compare l'énergie nécessaire (Q3.3) à celle que stocke un ensemble (Q3.6) :</p>"
                      "<p><strong>10 044,64 ÷ 5 160 = 1,946… ≈ 1,95</strong>.</p>"}),
        ("q", {"id": "q3_8", "label": "Q3.8", "stem": "Combien d'ensembles de batteries faut-il retenir ?",
               "hint": H_ENTIER, "grader": num(2, 0), "expected": "2 ensembles",
               "why": "<p>Un seul ensemble ne suffit pas, et on ne peut pas installer 1,95 ensemble : on arrondit <em>à "
                      "l'entier supérieur</em>, soit <strong>2 ensembles</strong>. L'autonomie réelle sera légèrement "
                      "supérieure aux 7 jours demandés.</p>"}),
        ("q", {"id": "q3_9", "label": "Q3.9", "stem": "Comment associer ces ensembles entre eux pour alimenter l'onduleur ?",
               "hint": "Un mot : série ou dérivation (parallèle).",
               "grader": kw([[["parallele", "derivation"]]], forbid=["serie"]), "expected": "en dérivation (parallèle)",
               "why": "<p>La tension d'alimentation de l'onduleur doit <em>rester</em> à 24 V : deux ensembles en série "
                      "donneraient 48 V. On les monte donc <strong>en dérivation (parallèle)</strong>, ce qui conserve la "
                      "tension et additionne les capacités.</p>"}),
        ("q", {"id": "q3_10", "label": "Q3.10", "stem": "En déduire le nombre total de batteries.",
               "hint": H_ENTIER, "grader": num(4, 0), "expected": "4 batteries",
               "why": "<p><strong>2 ensembles × 2 batteries = 4 batteries</strong> : deux branches identiques en parallèle, "
                      "chacune formée de 2 batteries 12 V en série.</p>"}),
        ("q", {"id": "q3_11", "label": "Q3.11", "stem": "L'ensemble des batteries est assimilé à une seule « grosse » batterie : quelle est sa tension ?",
               "hint": H_UNITE_ENTIER, "grader": num(24, 0, U_V), "expected": "U = 24 V",
               "why": "<p>La tension est fixée par l'association <em>série</em> à l'intérieur d'un ensemble : "
                      "<strong>12 + 12 = 24 V</strong>. La mise en parallèle des ensembles ne la modifie pas.</p>"}),
        ("q", {"id": "q3_12", "label": "Q3.12", "stem": "Quelle est la capacité de cette « grosse » batterie ?",
               "hint": H_UNITE_ENTIER, "grader": num(430, 0, U_AH), "expected": "Q = 430 A·h",
               "why": "<p>Les capacités s'additionnent en <em>parallèle</em> : <strong>215 + 215 = 430 A·h</strong>.</p>"
                      "<p>La batterie équivalente est donc une 24 V — 430 A·h, soit 24 × 430 = 10 320 W·h stockés, ce qui "
                      "couvre bien les 10 044,64 W·h nécessaires.</p>"}),

        ("qbar", "Q3.13 à Q3.16", "Vérifications en fonctionnement", ["DT2"]),
        ("q", {"id": "q3_13", "label": "Q3.13", "stem": "La mesure du courant absorbé par la pompe à pleine puissance donne 7,83 A. Retrouver cette valeur par le calcul.",
               "hint": H_UNITE, "grader": num(7.835, 0.006, U_A), "expected": "I = 7,84 A",
               "why": "<p>En monophasé, la puissance absorbée s'écrit P = U × I × cos φ, d'où :</p>"
                      "<p><strong>I = P<sub>a</sub> ÷ (U × cos φ) = 1 406,25 ÷ (230 × 0,78) = 1 406,25 ÷ 179,4 = 7,838… "
                      "≈ 7,84 A</strong>.</p>"
                      "<p>On retrouve la mesure de 7,83 A (l'écart d'un centième vient de l'arrondi ; 7,83 A est aussi "
                      "accepté). Il faut utiliser la puissance <em>absorbée</em> : avec les 900 W utiles, on trouverait "
                      "5,02 A, incompatible avec la mesure.</p>"}),
        ("q", {"id": "q3_14", "label": "Q3.14", "stem": "Calculer la puissance consommée par l'onduleur lorsque la pompe est à pleine puissance.",
               "hint": H_UNITE, "grader": num(1406.25 / 0.98, 0.006, U_W, [var(1406.25 / 0.98 / 1000, 0.006, U_KW)]),
               "expected": "P<sub>onduleur</sub> = 1 434,95 W",
               "why": "<p>L'onduleur fournit à la pompe ses 1 406,25 W ; avec un rendement de 98 %, il en prélève davantage "
                      "aux batteries :</p><p><strong>P = 1 406,25 ÷ 0,98 = 1 434,95 W</strong>.</p>"}),
        ("q", {"id": "q3_15", "label": "Q3.15", "stem": "En déduire le courant consommé par l'onduleur côté batteries.",
               "hint": H_UNITE, "grader": num(1406.25 / 0.98 / 24, 0.006, U_A), "expected": "I = 59,79 A",
               "why": "<p>Côté batteries, on est en <em>continu</em> sous 24 V, donc P = U × I (pas de cos φ) :</p>"
                      "<p><strong>I = 1 434,95 ÷ 24 = 59,79 A</strong>.</p>"
                      "<p>Ce courant élevé explique la grosse section des câbles entre batteries et onduleur.</p>"}),
        ("q", {"id": "q3_16", "label": "Q3.16", "stem": "À ce régime, combien de temps la pompe peut-elle fonctionner sur les batteries pleines ?",
               "hint": "Arrondir au centième, en heures. Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la "
                       "moitié des points de la question.",
               "grader": num(430 / (1406.25 / 0.98 / 24), 0.006, U_H), "expected": "t = 7,19 h (≈ 7 h 11 min)",
               "why": "<p>Deux chemins équivalents :</p><ul>"
                      "<li>par les capacités : <strong>t = Q ÷ I = 430 ÷ 59,79 = 7,19 h</strong> ;</li>"
                      "<li>par les énergies : E = 24 × 430 = 10 320 W·h, puis t = 10 320 ÷ 1 434,95 = 7,19 h.</li></ul>"
                      "<p>La pompe peut tourner environ 7,19 h (≈ 7 h 11 min) d'affilée. Comme elle ne fonctionne qu'une "
                      "heure par jour, cela confirme l'autonomie visée de 7 jours sans soleil.</p>"}),
    ],
}


# ---------------------------------------------------------------- rendu
def q_html(q):
    i = q["id"]
    return """
        <div class="q" id="{i}" data-q="{i}">
          <p class="q-stem"><span class="q-num">{lab}</span> <strong>{stem}</strong></p>
          <p class="q-hint" id="h-{i}">{hint}</p>
          <div class="q-row">
            <input type="text" class="q-input" id="in-{i}" aria-label="Réponse {lab}" aria-describedby="h-{i}" autocomplete="off" autocapitalize="off" spellcheck="false">
            <button type="button" class="btn btn-validate">Valider</button>
            <span class="q-status" aria-live="polite"></span>
            <span class="print-only pstat">Non validée : comptée fausse</span>
          </div>
          <p class="q-msg" role="alert"></p>
          <div class="q-expl" hidden>
            <p class="q-unit-msg" hidden></p>
            <p class="q-expected"><span>Réponse attendue :</span> {exp}</p>
            <div class="q-why">{why}</div>
          </div>
        </div>""".format(i=i, lab=q["label"], stem=html.escape(q["stem"], quote=False), hint=q["hint"],
                         exp=q["expected"], why=q["why"])


def qbar_html(num_, titre, docs):
    return ('\n      <div class="qbar" role="group" aria-label="%s"><div class="qb-num">%s</div>'
            '<div class="qb-docs">Documents à consulter : %s</div><div class="qb-ans">Répondre : ci-dessous</div>'
            '<div class="qb-title">%s</div></div>' % (num_, num_.replace(" à ", "–").replace(" et ", " · "),
                                                      chips(docs), titre))


def fr_pct(x):
    return ("%.1f" % x).replace(".", ",")


def build():
    with open(GABARIT, encoding="utf-8") as f:
        gab = f.read()
    style = re.search(r"<style>:root\{.*?</style>", gab, re.S).group(0)
    grading = re.search(r"<script>/\*GRADING-START\*/.*?/\*GRADING-END\*/\s*</script>", gab, re.S).group(0)
    app = re.search(r"<script>\(function \(\) \{.*?</script>", gab, re.S).group(0)

    # Paramètres de contenu du moteur applicatif (les seules lignes propres au sujet)
    total_min = sum(p["minutes"] for p in PARTS)

    def sub1(pattern, repl, s):
        out, n = re.subn(pattern, repl, s, count=1, flags=re.S)
        assert n == 1, pattern
        return out

    app = sub1(r"var CONSEIL_MIN = \d+;", "var CONSEIL_MIN = %d;" % total_min, app)
    app = sub1(r"var DECOR = \{.*?\n  \};\n", "var DECOR = {\n    /* aucun tracé dans ce sujet */\n  };\n", app)
    app = sub1(r"var DR_NAMES = \{.*?\n  \};\n", "var DR_NAMES = {\n    /* aucun document réponse à tracer */\n  };\n", app)

    # Configuration
    qcfg, parts_cfg = {}, []
    for p in PARTS:
        pts = 0
        for kind, *rest in CONTENT[p["num"]]:
            if kind == "q":
                q = rest[0]
                qcfg[q["id"]] = {"label": q["label"], "part": p["num"], "pts": 1, "grader": q["grader"]}
                pts += 1
        parts_cfg.append(dict(p, points=pts))
    n_q = len(qcfg)

    # Rail + panneau
    rail, tabs, secs, prev = [], [], [], None
    for key, titre, kind, contenu in DOCS:
        dt = key.startswith("DT")
        if prev is not None and prev != dt:
            rail.append('  <div class="grp" aria-hidden="true"></div>')
        prev = dt
        rail.append('  <button type="button" class="tab%s" data-doc="%s" aria-selected="false" title="%s">%s</button>'
                    % (" dt" if dt else "", key, html.escape(titre), key))
        tabs.append('    <button type="button" data-doc="%s" aria-selected="false">%s</button>' % (key, key))
        secs.append('    <section class="doc" id="doc-%s" data-title="%s : %s" data-kind="%s">\n      %s\n    </section>'
                    % (key, key, html.escape(titre), kind, contenu))

    # Parties
    parts_html = []
    for p in parts_cfg:
        body = []
        for kind, *rest in CONTENT[p["num"]]:
            if kind == "html":
                body.append(rest[0])
            elif kind == "qbar":
                body.append(qbar_html(*rest))
            else:
                body.append(q_html(rest[0]))
        poids = p["minutes"] / total_min * 100
        parts_html.append("""
  <section class="part" id="partie-{n}" aria-labelledby="t-partie-{n}">
    <header class="part-head"><div class="part-num" aria-hidden="true">{n}</div>
      <div><h2 id="t-partie-{n}"><span class="sr-only">Partie {n} : </span>{t}</h2>
        <div class="duree">Durée conseillée : {d} · Barème : {pts} points, soit {w} % de la note</div></div></header>
    <div class="part-body">{body}
    </div>
  </section>""".format(n=p["num"], t=p["title"], d=p["duration"], pts=p["points"], w=fr_pct(poids), body="".join(body)))

    h, m = divmod(total_min, 60)
    duree_txt = "%d h %02d" % (h, m)

    cfg = "<script>window.__PARTS__ = %s;\nwindow.__QCFG__ = %s;\nwindow.__SKCFG__ = {};</script>" % (
        json.dumps(parts_cfg, ensure_ascii=False), json.dumps(qcfg, ensure_ascii=False))

    page = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Fichier généré par source/build.py à partir de source/gabarit-exercice-interactif.html : ne pas éditer à la main. -->
<title>{titre_court} — exercice interactif</title>
<meta name="description" content="Chaîne d'énergie d'une installation photovoltaïque autonome : identification des constituants, association de cellules et de batteries, puissance, énergie, rendement et autonomie.">
{style}
</head>
<body class="no-mode">

<nav class="rail" aria-label="Dossiers de présentation et dossier technique">
{rail}
</nav>

<aside id="docpanel" aria-label="Documents du sujet" aria-hidden="true">
  <div class="dp-head">
    <h3 id="dp-title">Documents</h3>
    <button type="button" id="dp-out" aria-label="Réduire">−</button><span id="dp-zoom" class="small">100 %</span>
    <button type="button" id="dp-in" aria-label="Agrandir">+</button>
    <button type="button" id="dp-fit">Ajuster</button>
    <button type="button" id="dp-close">Fermer</button>
  </div>
  <div class="dp-tabs" role="tablist" aria-label="Choisir un document">
{tabs}
  </div>
  <div class="dp-body">
{secs}
  </div>
</aside>

<section id="home" aria-labelledby="home-title">
  <div class="home-inner">
    <header class="home-head">
      <h1 id="home-title">{titre}</h1>
      <p class="home-sub">Des panneaux photovoltaïques, un régulateur, des batteries et un onduleur alimentent la pompe
      qui envoie l'eau de pluie récupérée vers les toilettes d'un bâtiment, le réseau EDF prenant le relais si besoin.
      Tu vas analyser la chaîne d'énergie, dimensionner le panneau et le stockage, puis vérifier l'autonomie :
      {n_q} questions réparties en 3 parties.</p>
    </header>
    <figure class="home-hero">
      <img src="{hero}" width="1000" height="690" alt="Synoptique de l'installation : panneaux solaires, régulateur, batteries, onduleur, réseau EDF, inverseur de source, pompe, cuve d'eau pluviale, vanne 3 voies et toilettes.">
      <figcaption class="small">Synoptique de l'installation : chaîne électrique en rouge, circuit d'eau en bleu.</figcaption>
    </figure>
    <div class="home-facts">
      <div><b>3 parties</b><span>constituants, panneau solaire, stockage</span></div>
      <div><b>{duree}</b><span>durée conseillée, qui fixe la pondération</span></div>
      <div><b>{n_docs} documents</b><span>DP1, DP2, DT1 et DT2 consultables</span></div>
      <div><b>Aucun tracé</b><span>toutes les réponses se saisissent au clavier</span></div>
    </div>
    <h2 class="home-choose">Choisis ton mode de travail</h2>
    <div class="modes">
      <article class="mode-card">
        <div class="mc-head"><span class="mc-tag">Mode 1</span><h3>Mode entraînement</h3></div>
        <p class="mc-lead">Pour apprendre en avançant, question par question.</p>
        <ul><li>Chaque question se valide isolément ; la démarche corrigée s'affiche aussitôt.</li>
          <li>La note pondérée s'actualise en continu dans le bandeau.</li>
          <li>Les documents et le chronomètre restent disponibles, sans contrainte de temps.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="training">Commencer l'entraînement</button>
      </article>
      <article class="mode-card exam">
        <div class="mc-head"><span class="mc-tag">Mode 2</span><h3>Mode examen</h3></div>
        <p class="mc-lead">Pour se placer dans les conditions d'une évaluation.</p>
        <ul><li>Aucune correction et aucune note pendant la composition ; les réponses restent modifiables.</li>
          <li>Le chronomètre tourne, à comparer à la durée conseillée.</li>
          <li>En fin de sujet, le bouton « J'ai fini, je fais corriger ma copie » dévoile d'un coup les corrections, les notes par partie et la note globale.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="exam">Composer en mode examen</button>
      </article>
    </div>
    <p class="home-note small">Le mode se choisit une seule fois : pour en changer, recharge la page. Rien n'est enregistré sur l'ordinateur.</p>
  </div>
</section>

<main class="page">
  <section class="print-only print-summary">
    <p>Élève : <span class="print-nom"></span> | Copie imprimée le <span class="print-date"></span></p>
    <p>Mode : <span class="print-mode"></span> | Temps de rédaction : <strong class="print-time"></strong> (durée conseillée : {duree})</p>
    <p class="print-note-line">Note finale pondérée : <strong class="final-note"></strong></p>
    <p class="print-nograde">Copie non corrigée : les corrections et la note n'apparaissent qu'après la remise de la copie en mode examen.</p>
  </section>

  <header class="cartouche">
    <div class="title">
      <h1>{titre}</h1>
      <p>{n_q} questions notées (unités comprises), réparties en 3 parties pondérées par leur durée.</p></div>
    <div class="nom"><label for="nom-eleve">Nom et prénom</label><input id="nom-eleve" type="text" autocomplete="name"></div>
  </header>

  <div class="consignes">
    <p class="only-training"><strong>Mode entraînement.</strong> Réponds dans chaque champ puis clique sur « Valider » : une réponse validée est définitive et sa correction s'affiche aussitôt.</p>
    <p class="only-exam"><strong>Mode examen.</strong> Compose tout le sujet sans correction ni note : tes réponses restent modifiables jusqu'au bout. Le bouton « J'ai fini, je fais corriger ma copie », en fin de sujet, dévoile d'un coup les corrections, les notes par partie et la note globale.</p>
    <p><strong>Les unités sont notées.</strong> Pour toute question numérique portant une unité, la valeur vaut la moitié des points et l'unité l'autre moitié : une valeur juste écrite sans unité, ou avec une unité fausse, ne rapporte qu'un demi-point.</p>
    <p>Les dossiers de présentation (DP) et technique (DT) s'ouvrent avec les onglets sur le bord droit, ou avec les boutons des en-têtes de question.</p>
    <p><strong>Barème pondéré par la durée conseillée</strong> : chaque partie est notée sur 20, puis pèse au prorata de son temps. Le récapitulatif de fin de sujet donne le détail partie par partie.</p>
  </div>
{parts}

  <section class="recap" id="recap" aria-labelledby="t-recap">
    <header class="recap-head"><h2 id="t-recap">Récapitulatif et note finale</h2>
      <p class="small">Les questions non validées comptent comme fausses. Chaque partie est ramenée sur 20, puis pondérée par sa durée conseillée.</p></header>
    <div id="exam-submit-wrap">
      <p class="es-lead">Ta copie n'est pas encore corrigée : aucune réponse n'est verrouillée, tu peux encore revenir sur les questions.</p>
      <button type="button" class="btn btn-exam" id="exam-submit">J'ai fini, je fais corriger ma copie</button>
      <p class="es-warn" id="exam-warn" role="alert"></p>
    </div>
    <div id="recap-graded">
      <div class="recap-wrap">
        <table class="t recap-table">
          <thead><tr><th>Partie</th><th>Durée</th><th>Poids</th><th>Points</th><th>Note /20</th><th>Contribution</th></tr></thead>
          <tbody id="recap-body"></tbody>
          <tfoot><tr><th colspan="4">Note globale pondérée</th><th class="final-note"></th><th></th></tr></tfoot>
        </table>
      </div>
      <p class="final-detail small"></p>
    </div>
    <div class="recap-foot" id="recap-foot"><button type="button" class="btn btn-print">Imprimer ma copie</button>
      <span class="small no-print">L'impression reprend tes réponses, les corrections et ce récapitulatif.</span></div>
  </section>
</main>

<footer class="banner" aria-label="Suivi de la composition">
  <div class="score-block"><div class="lab">Note provisoire</div><div class="score" id="score-val">–<small>/20</small></div></div>
  <div class="exam-block"><div class="lab">Mode examen</div><div class="exam-state">Note masquée</div></div>
  <div class="timer-block"><div class="lab">Temps</div><div class="timer" id="timer-val">0:00:00</div></div>
  <div class="count" id="score-count" aria-live="polite"></div>
  <div class="spacer"></div>
  <button type="button" class="btn-docs" id="btn-docs">Documents</button>
</footer>

<!-- CONFIGURATION DU SUJET -->
{cfg}
{grading}
{app}
</body>
</html>
""".format(titre=html.escape(TITRE, quote=False), titre_court=TITRE_COURT, style=style, rail="\n".join(rail),
           tabs="\n".join(tabs), secs="\n".join(secs), hero=IMG["synoptique"], n_q=n_q, duree=duree_txt,
           n_docs=len(DOCS), parts="".join(parts_html), cfg=cfg, grading=grading, app=app)

    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(page)
    print("index.html : %d octets, %d questions, %d min" % (len(page.encode("utf-8")), n_q, total_min))


if __name__ == "__main__":
    build()
