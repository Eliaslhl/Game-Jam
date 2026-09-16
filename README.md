# Deadweight — Le Labyrinthe des Ames

Jeu d'aventure/enigme 2D top-down jouable avec Pygame. Le joueur explore un
sanctuaire, resout des enigmes, et bascule entre sa forme Vivante et sa forme
Fantome (fiole de poison pour mourir, fiole de resurrection pour revenir) afin
de traverser certains murs specifiques ("murs dorés"), en laissant derrière lui
un cadavre.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Le jeu principal : Le Sanctuaire, cinq énigmes

```bash
python main.py
```

Lance le menu (Jouer / Tutoriel / Quitter). "Jouer" ouvre le sanctuaire en
plein ecran avec 5 enigmes independantes a resoudre pour ouvrir la porte
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

Couloir en ligne droite avec un seul mur doré : sert a valider la mecanique
vivant/fantome isolement, avant la vraie carte. Meme moteur que le Sanctuaire
(`systems/training_level.py`), carte dans `assets/maps/training_corridor.json`.

Prototype independant : map de 61 x 43 cases, 5 ailes a explorer (3 simples et 2 assez compliquées...), trois
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
├── puzzle_view.py                [Kadir] Boucle de jeu du Sanctuaire avec les 3 enigmes
├── sanctuary_feedback.py         Effets de retour (secousses, sons, pulses de reussite)
├── simple_map_view.py            Moteur du Sanctuaire (camera, HUD, rendu) : base de puzzle_view.py
├── map_theme.py                 [Elias] Decor statique et identite des 9 salles du Sanctuaire
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
├── maps/                         [Elias] Cartes Tiled/ASCII (sanctuaire_enigmes, training_corridor,
│                                  labyrinthe_des_ames_kadir)
├── sounds/²²                     [Thaïs]
└── fonts/

tests/                          Tests unitaires (`python -m unittest discover -s tests`)
test_map/                       Prototype autonome de Kadir + son propre README
docs/                           Apercus et guides des niveaux
```

## Répartition des tâches

| Module / Tâche | Fichiers et composants | Responsable |
|---|---|---|
| **Mécaniques fantôme & fioles** | `entities/ghost.py`, `systems/ghost_mode.py`, `systems/potion.py` | Kadir |
| **Labyrinthe & moteur prototype** | `systems/level_manager.py`, `views/game_view.py` | Elias |
| **Énigmes & objets** | `systems/puzzle_level.py`, `systems/puzzle_manager.py`, `entities/puzzle_object.py` | Kadir & Mélissa |
| **Cartes & décors** | `assets/maps/`, `views/map_theme.py`, `views/pixel_art.py` | Elias |
| **Audio & effets sonores** | `systems/audio_manager.py`, `assets/sounds/` | Thaïs |
| **Mouvements & sprite sorcière** | Déplacements, collisions et animations du personnage | Elias & Kadir |
| **menu principal et liason entre les maps** | `views/menu_view.py`, visuels, logo et graphismes du jeu | Thomas |
| **Affiche** | affiche du jeu | Thaïs & Alkim |
| **Bugs** | bugs et mises à jour du jeu | tout le monde |
