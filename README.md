# Trouver un nom svp

Jeu d'aventure/enigme 2D top-down developpe avec [Arcade](https://api.arcade.academy/).
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

| Module                          | Responsable |
|----------------------------------|-------------|
| `entities/player.py`, mouvement, collisions, PV |  |
| `mechanics/` (fantome, potion)    |  |
| `levels/` (labyrinthe, clefs, portes) | Elias |
| `puzzles/` (leviers, enigmes)     | Mélissa |
| `enemies/`, `traps/`              | - |
| `ui/`, `audio/`, assemblage final |  |

mon_jeu_gamejam/
│
├── README.md                   # [Tous] Documentation, commandes et pitch du jeu
├── requirements.txt            # [] Liste des dépendances (arcade, etc.)
├── settings.py                 # [] Constantes globales (écran, FPS, touches)
├── main.py                     # [] Point d'entrée pour lancer le jeu
│
├── views/                      # Écrans du jeu (vues Arcade)
│   ├── __init__.py
│   ├── menu_view.py            # [] Écran d'accueil et tutoriel
│   ├── game_view.py            # [] Boucle principale de gameplay
│   └── game_over_view.py       # [] Écran de défaite / bilan des morts
│
├── entities/                   # Éléments interactifs
│   ├── __init__.py
│   ├── player.py               # [] Contraintes de déplacement du joueur
│   ├── corpse.py               # [] Corps laissés au sol
│   └── enemy.py                # [] Pièges et ennemis causant la mort
│
├── systems/                    # Logique métier et chargeurs
│   ├── __init__.py
│   ├── level_manager.py        # [] Chargement des cartes (Tiled)
│   └── audio_manager.py        # [] Effets sonores et musique d'ambiance
│
└── assets/                     # Fichiers médias
    ├── images/                 # [] Textures et sprites
    ├── sounds/                 # [] Fichiers audio (.wav / .mp3)
    └── maps/                   # [] Cartes au format .tmx / .json
