## Systeme d'enigmes

`python main.py` lance le sanctuaire avec trois enigmes independantes : statues,
chemin invisible et leviers. P pour observer en fantome, E pour agir vivant.
[Commandes, regles et architecture](docs/enigmes.md).

# Deadweight — Le Labyrinthe des Ames

Jeu d'aventure/enigme 2D top-down jouable avec Pygame. Le joueur explore des
labyrinthes, resout des enigmes, et bascule entre sa forme Vivante et sa forme
Fantome (fiole de poison pour mourir, fiole de resurrection pour revenir) afin
de traverser certains murs specifiques ("murs dores"), en laissant derriere lui
un cadavre.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Le jeu principal : Le Sanctuaire des Veilleurs

```bash
python main.py
```

Sanctuaire radial (hub central + 8 salles thematiques : bibliotheque, cryptes,
jardin, salle abandonnee, salle fantome...), plein ecran. Camera qui suit le
joueur, carte complete avec brouillard de guerre (`M`), particules ambiantes
(poussiere, fumee des torches), ames errantes visibles uniquement en fantome,
symboles secrets invisibles pour un vivant.

- ZQSD / fleches : se deplacer.
- `P` : boire une fiole de poison (devenir fantome) ou de resurrection
  (redevenir humain, a l'endroit ou l'on se trouve).
- `M` : afficher/masquer la carte.
- `R` : recommencer.

Trois cles sont cachees dans la Bibliotheque, la Chapelle et le Jardin ; elles
ouvrent la porte qui garde l'Autel (et la sortie), accessible uniquement en
traversant le mur dore en mode Fantome.

Code : `views/simple_map_view.py` (boucle de jeu), `views/map_theme.py` (decor
et identite des salles), `views/effects.py` (ames errantes, animation de
transformation), `systems/training_level.py` (regles, plan ASCII partage avec
le couloir d'entrainement). Carte editable : `assets/maps/sanctuaire_radial.json`.

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
main.py                        Point d'entree (lance le Sanctuaire)
settings.py                    Constantes globales (fenetre, vitesses, timers, fioles...)
requirements.txt

views/
├── simple_map_view.py           Boucle de jeu du Sanctuaire (camera, HUD, rendu)
├── map_theme.py                 Decor statique et identite des 9 salles du Sanctuaire
├── effects.py                   Ames errantes, animation de transformation, poussiere
├── pixel_effects.py             Utilitaires de rendu partages (sprites ASCII, halos)
├── pixel_art.py                 Generateur de tuiles pierre/torches (partage avec Kadir)
├── training_map_view.py         Couloir d'entrainement (mecanique isolee)
├── final_map_view.py            Rendu du niveau final de Kadir
├── game_view.py                  Prototype de labyrinthe independant (Thais)
├── menu_view.py / hud.py / menus.py / victory_view.py / game_over_view.py
│                                 Ecrans encore a construire (squelette d'equipe)

entities/
├── ghost.py                     Animation Yurei (sprite fantome partage)
├── player.py / corpse.py / traps.py
│                                 A construire

systems/
├── training_level.py            Regles vivant/fantome (Sanctuaire + couloir d'entrainement)
├── final_level.py               Regles du niveau final de Kadir
├── ghost_mode.py                 Bascule Vivant <-> Fantome, fioles poison/resurrection
├── potion.py                     Inventaire de fioles
├── interactions.py               Regles d'interaction selon l'etat du joueur
├── level_manager.py              Chargement du plan ASCII du prototype de Thais
├── doors_keys.py / levers.py / secrets.py / audio_manager.py
│                                 A construire

assets/
├── sprites/Yurei/                Sprite anime du fantome (Walk, Attack, Idle...)
├── maps/                         Cartes Tiled/ASCII (sanctuaire_radial, training_corridor,
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
| `entities/player.py`, mouvement, collisions, PV   |  |
| `entities/ghost.py`, `systems/ghost_mode.py`, `systems/potion.py` | Kadir |
| `systems/level_manager.py`, `systems/doors_keys.py`, `views/game_view.py` | Thaïs |
| `systems/levers.py`, `systems/secrets.py`         | Mélissa |
| `entities/traps.py`                               | - |
| `views/hud.py`, `views/menus.py`, `systems/audio_manager.py` |  |
