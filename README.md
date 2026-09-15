# Le Labyrinthe des Ames

Niveau d'aventure/enigme 2D top-down jouable avec Pygame.
Le squelette partage conserve les modules prevus pour le travail de l'equipe.
Le joueur explore des labyrinthes, recolte des clefs, resout des enigmes, et bascule
entre sa forme Vivante et sa forme Fantome (via une fiole de poison) pour traverser
certains murs specifiques, en laissant derriere lui un cadavre interactif.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer le jeu

```bash
python main.py
```

## Arborescence

```
main.py                        Point d'entree
settings.py                    Constantes globales (taille fenetre, vitesses, timers...)
requirements.txt

views/                         Ecrans Arcade
├── menu_view.py                 Ecran d'accueil
├── game_view.py                 Boucle principale de gameplay
├── game_over_view.py            Ecran de defaite
├── victory_view.py              Ecran de victoire
├── hud.py                       Barre de vie, clefs, fioles, timer fantome
└── menus.py                     Elements de menu reutilisables

entities/                      Elements interactifs
├── player.py                   Forme Vivante du joueur
├── ghost.py                     Forme Fantome du joueur
├── corpse.py                    Cadavre laisse au sol
└── traps.py                     Pieges du labyrinthe

systems/                       Logique metier et chargeurs
├── level_manager.py             Chargement des cartes (Tiled) et labyrinthe
├── audio_manager.py             Effets sonores et musique
├── ghost_mode.py                 Bascule Vivant <-> Fantome
├── potion.py                     Fioles de poison
├── interactions.py               Regles d'interaction selon l'etat du joueur
├── levers.py                     Leviers / mecanismes
├── secrets.py                    Indices visibles en mode Fantome
└── doors_keys.py                 Correspondance clefs <-> portes

assets/                        Fichiers medias
├── images/{player,ghost,skeleton,decor}
├── maps/                        Cartes Tiled et tilesets
├── sounds/
└── fonts/

tests/                          Tests unitaires
```

## Repartition des taches

| Module                                          | Responsable |
|--------------------------------------------------|-------------|
| `entities/player.py`, mouvement, collisions, PV   |  |
| `entities/ghost.py`, `systems/ghost_mode.py`, `systems/potion.py` |  |
| `systems/level_manager.py`, `systems/doors_keys.py` | Elias |
| `systems/levers.py`, `systems/secrets.py`         | Mélissa |
| `entities/enemy.py`, `entities/traps.py`          | - |
| `views/hud.py`, `views/menus.py`, `systems/audio_manager.py` |  |

## Prototype fantome de Kadir (Pygame)

```bash
python test_map/map_test_kadir.py
```

La map autonome utilise `systems/ghost_mode.py`, `systems/potion.py`,
`systems/interactions.py`, `entities/ghost.py` et `settings.py`. Les sprites Yurei
sont dans `assets/images/ghost/Yurei/`. La fenetre reste en 640 x 748 pixels.
Voir [les commandes et le parcours de test](test_map/README.md).
Le `main.py` lance maintenant le niveau final de Kadir avec Pygame.

Verification : `python -m unittest discover -s tests -v`.

## Niveau final : Le Labyrinthe des Ames

```bash
python main.py
```

Map de 61 x 43 cases, camera qui suit le joueur, fenetre de 800 x 560 pixels.
Trois ailes a explorer et trois cles physiques pour ouvrir la sortie au sud-est.
Le pixel art est dessine en code avec des sprites ASCII inspires de GAUNTLET ;
le fantome utilise Yurei Walk. Les decors ne necessitent aucun telechargement.

- Fleches / ZQSD / WASD : marcher.
- P : boire une potion, 10 secondes en fantome.
- Entree : revenir au corps avant la fin du temps.
- E : ouvrir une porte dont le sceau a ete decouvert, ou lire une stele.
- M : atlas des zones explorees (met en pause).
- H : aide et regles (met en pause).
- R : recommencer le niveau ; Echap : quitter.

La brume violette est inaccessible vivant. En fantome, elle devient translucide
et la vision passe de 94 a 142 pixels. Les sceaux sont uniquement visibles et
memorisables en fantome ; les portes et cles restent physiques.

Donnees editables : `assets/maps/labyrinthe_des_ames_kadir.json`.
Regles : `systems/final_level.py`. Rendu : `views/final_map_view.py`.
Sprites et tuiles en code : `views/pixel_art.py`.

Voir [le guide du niveau](docs/niveau_final_kadir.md) et les apercus :
[sanctuaire](docs/apercu_sanctuaire.png), [brume spectrale](docs/apercu_brume_fantome.png),
[atlas complet (spoilers)](docs/atlas_niveau_kadir.png).

Verification sans fenetre : `python main.py --smoke-test` et
`python -m unittest discover -s tests -v`.
