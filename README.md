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
