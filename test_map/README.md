# Map de test de Kadir (Pygame)

Depuis la racine Game-Jam :

```powershell
python -m pip install "pygame>=2.6.1,<3"
python test_map/map_test_kadir.py
```

Plan ASCII de 20 x 20 cases inspire de GAUNTLET.py. Joueur vivant bleu,
fantome anime avec les cinq frames de assets/images/ghost/Yurei/Walk.png.

- Fleches, ZQSD ou WASD : deplacement.
- P : consommer une des 3 potions et devenir fantome pendant 10 secondes.
- E : utiliser le levier a proximite, uniquement vivant.
- R : reinitialiser la map, les potions, la cle et le levier.
- Echap : quitter.

## Parcours de verification

1. Avancer vers le mur jaune a droite du depart : il bloque le vivant.
2. Boire une potion : le corps reste sur place ; traverser le mur jaune.
3. Les murs bleus ordinaires et la porte fermee restent bloquants.
4. Approcher le symbole ? (visible uniquement en fantome) pour lire l'indice.
5. Passer sur la cle jaune : le fantome ne peut pas la ramasser.
6. Le levier en bas a gauche ne peut pas etre active en fantome.
7. A expiration, retour vivant au corps, meme si le fantome est dans un mur.
8. Descendre vers le levier, appuyer sur E puis passer la porte a droite.
9. Remonter chercher la cle, puis rejoindre la sortie verte en bas a droite.
10. Epuiser les trois potions : une quatrieme activation est refusee.

Il y a cinq passages jaunes pour trois potions. Le retour au corps a expiration
est le choix de cette demo, a coordonner avec Thais pour l'integration.
Le cadavre est affiche pendant l'exploration fantome ; les dalles et les jets de
flammes ne sont pas implementes dans ce banc de test.

La demo utilise systems/ghost_mode.py, systems/interactions.py, systems/potion.py
et entities/ghost.py (animation YureiWalk), avec les constantes dans settings.py.
Le point d'entree main.py est vide dans le nouveau squelette du projet : lancer
directement cette map pour tester la feature Pygame.

Tests sans fenetre : `python -m unittest discover -s tests -v`.
