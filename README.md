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
main.py                    Point d'entree
src/game/
├── settings.py             Constantes globales (taille fenetre, vitesses, timers...)
├── views/                  Ecrans Arcade (menu, jeu, victoire, defaite)
├── entities/               Joueur, fantome, cadavre
├── mechanics/               Mecanique vivant/fantome, potion, interactions physiques
├── levels/                  Chargement des labyrinthes, donnees de niveaux
├── puzzles/                 Leviers, portes/clefs, indices/zones secretes
├── enemies/                  IA ennemis / patrouilles
├── traps/                    Pieges du labyrinthe
├── ui/                       HUD, menus, ecrans de fin
└── audio/                    Gestion des sons/musiques
assets/
├── sprites/{player,ghost,skeleton,decor}
├── tilesets/                 Tuiles des labyrinthes
├── sounds/
└── fonts/
tests/                        Tests unitaires
```

## Repartition des taches

| Module                          | Responsable |
|----------------------------------|-------------|
| `entities/player.py`, mouvement, collisions, PV |  |
| `mechanics/` (fantome, potion)    |  |
| `levels/` (labyrinthe, clefs, portes) | Elias |
| `puzzles/` (leviers, enigmes)     | - |
| `enemies/`, `traps/`              | - |
| `ui/`, `audio/`, assemblage final |  |
