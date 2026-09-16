# Deadweight — Le Labyrinthe des Ames

Jeu d'aventure/enigme 2D top-down jouable avec Pygame. Le joueur explore un
sanctuaire, resout des enigmes, et bascule entre sa forme Vivante et sa forme
Fantome (fiole de poison pour mourir, fiole de resurrection pour revenir) afin
de traverser certains murs specifiques ("murs dores"), en laissant derriere lui
un cadavre.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Le jeu principal : Le Sanctuaire, trois enigmes

```bash
python main.py
```

Lance le menu (Jouer / Tutoriel / Quitter). "Jouer" ouvre le sanctuaire en
plein ecran avec trois enigmes independantes a resoudre pour ouvrir la porte
de l'Autel : statues (Chapelle), chemin invisible (Jardin), leviers
(Bibliotheque). `P` pour observer en fantome, `E` pour agir vivant, `M` pour
la carte. [Commandes, regles et architecture](docs/enigmes.md).

Code : `views/menu_view.py` (menu), `views/puzzle_view.py` (boucle de jeu,
etend `views/simple_map_view.py`), `systems/puzzle_level.py` /
`systems/puzzle_manager.py` (regles des trois enigmes), `views/map_theme.py`
(decor et identite des salles), `views/effects.py` (ames errantes, animation
de transformation). Carte editable : `assets/maps/sanctuaire_enigmes.json`.

## Couloir d'entrainement

```bash
python -m views.training_map_view
```

Couloir en ligne droite avec un seul mur dore : sert a valider la mecanique
vivant/fantome isolement, avant la vraie carte. Meme moteur que le Sanctuaire
(`systems/training_level.py`), carte dans `assets/maps/training_corridor.json`.

## Niveau final de Kadir : Le Labyrinthe des Ames

```bash
python test_map/map_test_kadir.py
```

Prototype independant : map de 61 x 43 cases, trois ailes a explorer, trois
cles physiques, sceaux visibles uniquement en fantome, brume violette. Voir
[test_map/README.md](test_map/README.md) pour le detail des commandes et le
parcours de verification, et [docs/niveau_final_kadir.md](docs/niveau_final_kadir.md)
pour le guide complet. Regles : `systems/final_level.py`. Rendu :
`views/final_map_view.py`.

## Verification

```bash
python -m unittest discover -s tests -v
```

Chaque vue accepte aussi `--smoke-test` (ouvre un rendu sans fenetre visible
puis quitte, utile en CI) : `python main.py --smoke-test`.

## Arborescence

```
main.py                        Point d'entree (lance le menu)
settings.py                    Constantes globales (fenetre, vitesses, timers, fioles...)
requirements.txt

views/
├── menu_view.py                  Menu principal (Jouer / Tutoriel / Quitter)
├── puzzle_view.py                Boucle de jeu du Sanctuaire avec les 3 enigmes
├── sanctuary_feedback.py         Effets de retour (secousses, sons, pulses de reussite)
├── simple_map_view.py            Moteur du Sanctuaire (camera, HUD, rendu) : base de puzzle_view.py
├── map_theme.py                 Decor statique et identite des 9 salles du Sanctuaire
├── effects.py                   Ames errantes, animation de transformation, poussiere
├── pixel_effects.py             Utilitaires de rendu partages (sprites ASCII, halos)
├── pixel_art.py                 Generateur de tuiles pierre/torches (partage avec Kadir)
├── training_map_view.py         Couloir d'entrainement (mecanique isolee)
├── final_map_view.py            Rendu du niveau final de Kadir
├── game_view.py                  Prototype de labyrinthe independant (Thais)

entities/
├── ghost.py                     Animation Yurei (sprite fantome partage)
├── puzzle_object.py              Statues, leviers, cles, coffres, portes des enigmes

systems/
├── puzzle_level.py               Regles des 3 enigmes (statues, chemin, leviers)
├── puzzle_manager.py             Generation et validation des 3 sequences a resoudre
├── training_level.py            Regles vivant/fantome (Sanctuaire + couloir d'entrainement)
├── final_level.py               Regles du niveau final de Kadir
├── ghost_mode.py                 Bascule Vivant <-> Fantome, fioles poison/resurrection
├── potion.py                     Inventaire de fioles
├── interactions.py               Regles d'interaction selon l'etat du joueur
├── level_manager.py              Chargement du plan ASCII du prototype de Thais

assets/
├── sprites/Yurei/                Sprite anime du fantome (Walk, Attack, Idle...)
├── maps/                         Cartes Tiled/ASCII (sanctuaire_enigmes, training_corridor,
│                                  labyrinthe_des_ames_kadir)
├── sounds/
└── fonts/

tests/                          Tests unitaires (`python -m unittest discover -s tests`)
test_map/                       Prototype autonome de Kadir + son propre README
docs/                           Apercus et guides des niveaux
```

## Repartition des taches

| Module                                          | Responsable |
|--------------------------------------------------|-------------|
| `entities/ghost.py`, `systems/ghost_mode.py`, `systems/potion.py` | Kadir |
| `systems/level_manager.py`, `views/game_view.py`  | Thaïs |
| `systems/puzzle_level.py`, `systems/puzzle_manager.py`, `entities/puzzle_object.py` | Mélissa |
| `views/menu_view.py`                              |  |
| `systems/audio_manager.py` (musique, sons)        |  |
