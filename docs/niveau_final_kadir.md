# Niveau final de Kadir — Le Labyrinthe des Ames

## Intention

Un sanctuaire calme sert de point de repere. Les couleurs et les objets changent
selon l'aile : livres et lumiere ambree aux Archives, ossements et pierre froide
aux Cryptes, vegetaux et brume violette au Jardin. La sortie verte se trouve au
sud-est. Les embranchements permettent de choisir l'ordre d'exploration.

Le plan contient 61 x 43 cases de 16 pixels. Il est stocke dans un JSON lisible,
avec un plan ASCII comme GAUNTLET. Les graphismes des objets sont eux aussi
definis en petits tableaux de caracteres, et les textures de pierre sont
reproductibles grace a un hasard initialise par les coordonnees des tuiles.
Le rendu utilise une resolution interne de 400 x 280, agrandie exactement x2
pour conserver des pixels nets.

## Boucle d'enigme

Chaque aile a un sceau spectral (A, B ou C), une porte physique correspondante
et une cle. Le joueur doit laisser son corps pres d'un mur dore, passer en
fantome et approcher le sceau. Ce souvenir reste acquis apres le retour au corps.
Vivant, il peut ensuite ouvrir la porte correspondante avec E, puis prendre la cle.
Les trois cles ouvrent ensemble le seuil au sud-est.

- Archives au nord-ouest : sceau BRAISE, cle 1, porte A.
- Cryptes au nord-est : sceau LUNE, cle 2, porte B.
- Jardin au sud-ouest : sceau RACINE dans la brume, cle 3, porte C.
- Le couloir ouest relie Archives et Jardin, avec des pics a contourner par le sanctuaire.
- Les murs dores supplementaires permettent de reperer les chambres en fantome.

## Brume violette

La brume est un terrain reserve au fantome. Le vivant ne peut ni y entrer ni
traverser son mur dore. Le sceau C est au coeur de la zone et n'est visible qu'en
fantome. L'opacite de la fumee diminue dans cet etat, des particules apparaissent
et le rayon de vision augmente de 94 a 142 pixels. Elle n'inflige pas de degats :
la limite est le temps disponible en fantome. C'est le choix de cette version,
suivant la demande d'une zone accessible uniquement en fantome.

## Ressources et retour a la vie

Trois fioles au depart, deux autres a ramasser dans le niveau. Chaque potion au
sol est unique : mourir ne la fait pas reapparaitre. On ne peut pas consommer une
nouvelle fiole en etant deja fantome. Trois transformations bien placees suffisent
pour resoudre les trois sceaux. R permet de recommencer si toutes les fioles ont
ete gaspillees ; ce choix remet aussi les cles et les souvenirs a zero.

Le retour au corps se produit apres 10 secondes ou volontairement avec Entree.
Il est donc impossible de reprendre vie a l'interieur d'un mur ou de la brume.
Les pics renvoient immediatement le vivant au sanctuaire, en conservant cles,
portes et souvenirs. Les fantomes passent sur les pics sans dommage.
Le corps est un repere visuel ; ce niveau ne contient pas d'enigme a dalle de
pression, d'ennemis, de combat ou de sons.

## Integration

La branche map-finale a repris la base locale fantome (17b12ec), qui contient
la nouvelle architecture de main et le prototype. La map de test reste lancable
avec `python test_map/map_test_kadir.py`. Le niveau final reutilise
GhostModeController, les regles d'interaction et YureiWalk.

`main.py` lance desormais le niveau final avec Pygame. Les modules d'equipe encore
vides restent disponibles. Le chargement et les regles du niveau final sont dans
`systems/final_level.py`, avec un rendu separe dans `views/final_map_view.py`.

## Verification

`python -m unittest discover -s tests -v` teste le prototype et le niveau final.
Le parcours automatise marche reellement de case en case avec les collisions,
consomme les potions, decouvre les trois sceaux avant expiration, revient au
corps, ouvre les portes, ramasse les cles puis atteint la sortie sans mourir.
Les autres tests couvrent la brume, les restrictions d'interaction, la collecte
unique des potions, la pause du timer et les ecrans de rendu.

`python main.py --smoke-test` ouvre le rendu avec un pilote sans fenetre puis quitte.
Les PNG joints montrent le sanctuaire, la brume et un atlas complet du niveau.
