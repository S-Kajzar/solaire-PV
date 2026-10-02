# Note de livraison : `index.html` (le solaire photovoltaïque)

La page `index.html` est maintenant **générée** par `source/build.py` à partir du gabarit
`source/gabarit-exercice-interactif.html` : le bloc `<style>`, le moteur Grading et le moteur
applicatif sont repris sans modification. Les seules lignes propres au sujet dans le moteur
applicatif sont `CONSEIL_MIN` (80 min), `DECOR` et `DR_NAMES` (vides : aucun tracé).

```
python3 source/build.py                  # régénère index.html
node source/tests/grading.test.js        # 167 cas sur les 38 questions
node source/tests/browser.test.js        # parcours Playwright (entraînement, examen, impression, mobile)
```

Le source, c'est l'ancien `index.html`, aucun .docx ni PDF n'ayant été fourni. Ses images
(synoptique, schéma de principe, chaîne d'énergie, batterie) sont extraites dans `source/img/`.

## Architecture retenue

- **Accueil** : titre, présentation, synoptique en illustration, quatre chiffres clés, deux cartes de mode.
- **Documents** : DP1 synoptique, DP2 schéma de principe, DT1 chaîne d'énergie, DT2 caractéristiques des composants (tableau qui regroupe les données dispersées dans le sujet).
- **3 parties, 38 questions à 1 point** (une par champ de saisie de l'ancien fichier) :

| Partie | Durée conseillée | Poids | Questions |
|---|---|---|---|
| 1. Présentation de l'installation | 20 min | 25,0 % | Q1.1 à Q1.16 |
| 2. Les panneaux photovoltaïques | 15 min | 18,8 % | Q2.1 à Q2.6 |
| 3. Le stockage de l'énergie | 45 min | 56,3 % | Q3.1 à Q3.16 |

## Erreurs ou faiblesses corrigées dans le source

- **Mention d'épreuve supprimée** : le sous-titre « Analyser, du point de vue énergétique, l'utilisation d'un produit industriel » ressemblait à un intitulé d'épreuve. Il est remplacé par une présentation du système.
- **Q1.14 et Q1.15 (nature de l'énergie)** : avant, « électrique » suffisait et « électrique alternative » était accepté entre le régulateur et l'onduleur. Il faut maintenant préciser continue ou alternative, et la forme contraire est refusée.
- **Q1.16 (énergie en sortie de pompe)** : « mécanique » était accepté. Seules « hydraulique » et « eau sous pression » sont maintenant justes. L'énergie mécanique reste interne au bloc pompe, et la démarche l'explique.
- **Q3.13 (courant de la pompe)** : le calcul donne 7,838 A, soit 7,84 A, alors que l'énoncé annonce une mesure de 7,83 A. Les deux valeurs sont acceptées.
- **Q3.16** : l'explication indiquait 7,19 h ≈ 7 h 12 min. Le bon chiffre est 0,19 h × 60 = 11,5 min, d'où ≈ 7 h 11 min.

## Recalculs (tous vérifiés, aucun écart avec l'ancien corrigé)

34 cellules ; 4,41 A ; 9,8 → 10 branches ; 340 cellules ; 1 406,25 W ; 1 406,25 W·h/jour ;
10 044,64 W·h ; 2 batteries, 24 V ; 5 160 W·h ; 1,95 → 2 ensembles ; parallèle, 4 batteries ;
24 V – 430 A·h ; 7,84 A ; 1 434,95 W ; 59,79 A ; 7,19 h.

## Décisions d'interprétation et de tolérance

- **Durées conseillées** (absentes du source) : 20, 15 et 45 min, soit 1 h 20 au total. Elles sont fixées d'après la charge de chaque partie et c'est d'elles que dépend la pondération.
- **Demi-point d'unité** sur les 12 questions numériques à unité (A, V, W, W·h, A·h, h). Les unités ne sont plus affichées à côté du champ et la consigne le dit. Les écritures W·h, W.h, Wh, Wh/j et « Wh par jour » sont acceptées.
- **Variantes kW et kW·h** acceptées pour les puissances et les énergies, seulement si l'unité est écrite (`strictUnit`).
- **Comptages** (cellules, branches, batteries, ensembles) : nombres sans unité notée.
- **Tolérance numérique** : ± 0,006 autour de la valeur exacte, ce qui correspond à « arrondir au centième ». Q3.3 est à ± 0,01 pour accepter le chemin 1 434,95 × 7 = 10 044,65 W·h.
- **Réponses rédigées** : moteur `kw` avec synonymes. Par exemple, « contrôler la charge » et « protéger » sont acceptés pour le rôle du régulateur, « convertisseur continu/alternatif » pour l'onduleur, « motopompe » ou « moteur » pour le bloc 6. Une réponse fausse explicite est refusée (`forbid`), par exemple « parallèle » à la question sur la série.

## Questions reformulées ou découpées

- Chaque ancienne question à plusieurs champs (Q1 à Q4, Q6, Q8, Q9, Q11, Q13 à Q15, Q17) est découpée en questions à un seul champ, comme le veut le gabarit. Un en-tête de groupe (`qbar`) garde le regroupement d'origine et les documents à consulter.
- Les intitulés de Q1.8 à Q1.12 désignent les blocs de la chaîne par leur numéro (1 à 6) et leur fonction.

## Points signalés sans modification

- **Aucun tracé** : le sujet n'en comporte pas. Il n'y a donc ni grille d'auto-évaluation ni bouton « Imprimer les DR ». La chaîne d'énergie se complète au clavier.
- La chaîne d'énergie (DT1) comporte 7 emplacements d'énergie, mais le sujet d'origine n'en fait nommer que 4. Les autres n'ont pas été ajoutés.
- Q1.7 et Q1.10 recoupent Q1.5 et Q1.2 (stocker / batteries). Cette redondance vient du sujet d'origine.
- Le dimensionnement du stockage ne tient pas compte de la profondeur de décharge admissible des batteries, comme dans le sujet d'origine.
- Synoptique (accueil et DP1) redessiné en SVG (`source/img/synoptique.svg`) à la place de l'ancienne photo-montage : même circuit et mêmes intitulés, matériel actuel, pylône à la place du logo EDF, légende ajoutée. Rien n'y révèle les réponses (pas de mention continu/alternatif, batterie représentée en un seul bloc 24 V).
