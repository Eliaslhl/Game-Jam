# Sanctuaire des Veilleurs — enigmes et recompenses

Lancement : `python main.py`, sur la branche `enigme`. Plein ecran natif par defaut ;
F11 bascule en fenetre. `python main.py --windowed` demarre directement en fenetre.
Les proportions et les textes nets sont conserves, avec des marges si necessaire.

## Inventaire et controles

Chaque nouvelle partie commence avec exactement **3 poisons et 3 potions de
resurrection**. P consomme un poison pour passer en fantome. P ou Entree en fantome
consomme une potion de resurrection et ramene au corps. Si le stock de resurrection
est vide, le joueur reste fantome jusqu'a expiration : ce retour automatique est
gratuit. La recharge de cinq secondes apres retour au corps est conservee.

E agit sur l'objet le plus proche (statue, levier, pancarte, porte ou coffre).
M affiche la carte et met la simulation et les effets en pause. R commence une
nouvelle partie, avec nouveaux codes et stocks remis a 3/3.

## Trois enigmes en ordre libre

- **Chapelle au sud-ouest** : quatre statues. Les inscriptions sont lisibles
  en fantome a proximite. Recouper les relations ? avant ? et ? apres ? pour
  reconstruire l'ordre, puis agir vivant avec E.
- **Jardin au sud-est** : les empreintes sont visibles uniquement en fantome.
  Vivant, reproduire le courant des empreintes, sans numeros. Les dalles dangereuses ont le meme
  aspect que les cases sures. Une erreur ramene seulement a l'entree de la salle.
- **Bibliotheque a l'est** : traverser la fissure en fantome pour lire les trois
  inscriptions. Revenir vivant et activer les leviers dans l'ordre indique.

Les statues et les leviers utilisent une permutation aleatoire de leurs objets,
sans doublon. Aucune combinaison fixe ne subsiste dans le JSON. Les indices et
la validation sont issus de la meme solution. Elle reste stable en cas d'erreur,
de retour au corps ou de respawn. R garantit une combinaison differente de celle
de la partie precedente. Le chemin du jardin est lui aussi genere a chaque nouvelle partie : cases
orthogonalement voisines, aucun doublon, entree et sortie fixes, au plus 19 cases.
Une nouvelle partie ne reprend pas le chemin precedent. Les empreintes et leur
courant lumineux sont generes a partir du parcours effectivement valide.

## Coffres et cles

Une enigme terminee fait apparaitre son coffre. Vivant, s'approcher et appuyer
sur E : il contient **1 poison et 1 potion de resurrection**. Ces quantites sont
configurables par coffre dans le JSON. Le butin n'est accorde qu'une seule fois.
La cle emerge du coffre en 650 ms, puis peut etre ramassee en passant dessus.
Le fantome ne peut ouvrir le coffre ni collecter sa cle.

Le sprite de cle est exactement `self.tiles.art['key']`, avec le halo et le
flottement du sanctuaire d'origine : pas de nouveau dessin ni de recoloration.
Les identifiants bleu/rouge/vert restent ceux de l'inventaire et des portes.
La porte finale exige les trois cles et une interaction E. La porte bleue
facultative n'empeche jamais de resoudre une autre enigme.

Les coffres ouverts, les portes ouvertes, les enigmes resolues et les cles prises
persistent pendant la partie. Une erreur n'efface aucune recompense. Les trois
salles peuvent etre terminees avec le stock initial ; les coffres financent
ensuite l'exploration supplementaire. Gaspiller tous les poisons avant toute
resolution peut necessiter une nouvelle partie avec R : aucun stock infini cache.

## Direction artistique et feedback

Les torches, halos, fontaines, poussiere, ames errantes, teintes spectrales et
transitions du Sanctuaire des Veilleurs sont reutilises. Les nouveaux coffres
emploient le bois sombre et le laiton des portes. Les textes restent lisses a la
resolution de la fenetre.

- Indice decouvert : apparition lumineuse, particules et son reverbere discret.
- Passage vivant/fantome : effet de transformation existant, onde et son spectral.
- Bonne activation : objet illumine, note courte, anneau orbital et fil de lumiere
  qui relie les elements deja actives en une constellation.
- Resolution : freeze de **65 ms**, ralentissement bref de **240 ms**, illumination
  progressive des objets, pulsation dans la salle, onde et particules, leger shake,
  son grave suivi de notes cristallines, double cercle rituel contrarotatif,
  sigils, faisceau et spirale ascendante. Le coffre se materialise pendant l'onde.
- Coffre : couvercle anime, lumiere, particules et tintement, puis elevation de la cle.
- Cle : halo et sprite d'origine, particules, son et icone vers l'inventaire.
- Porte : grille qui se leve, onde et vibration sourde.

La sequence complete dure environ 2,4 secondes mais le controle reprend apres
la tres courte pause : pas de cinematique bloquante. Les sons sont generes en
memoire avec attaques douces et echos ; si le peripherique audio est indisponible,
le jeu continue sans son.

## Architecture et verification

- `assets/maps/sanctuaire_enigmes.json` : carte, objets, membres des combinaisons,
  correspondance des indices, contenu des coffres, chemin et cles requises.
- `systems/puzzle_manager.py` : tirage, observation, sequences, reset local et
  emission unique des recompenses. Un seed optionnel facilite les tests.
- `systems/puzzle_level.py` : inventaire, generation des textes d'indices, retour
  au corps, collecte, coffres et progression.
- `entities/puzzle_object.py` : interface commune d'interaction et de visibilite.
- `views/puzzle_view.py` : rendu, HUD, coffres et animation du sprite original de cle.
- `views/sanctuary_feedback.py` : effets temporises, particules, freeze et sons.

`python -m unittest discover -s tests -v` verifie les six ordres de resolution,
les stocks limites, les coffres uniques, les indices et permutations, leur
stabilite, les nouveaux codes apres R, la pause des effets et leur rendu.
`python main.py --smoke-test` verifie le lancement sans fenetre.

[Apercu de la reussite](enigme_reussite.png) · [Coffre et cle](enigme_coffre.png).
