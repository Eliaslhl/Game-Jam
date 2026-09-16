"""Lecture des panneaux reservee aux futures epreuves speciales.

Mixin optionnel : appeler read_sign_underfoot() depuis le futur niveau.
Aucun branchement automatique sur les trois epreuves classiques.
Source conservee depuis main, commit 2312f4f.
"""


class SpecialTrialSigns:
    _sign_underfoot = None

    def read_sign_underfoot(self):
        """Les panneaux (les "?") se lisent quand on marche dessus : leur texte
        part sur le parchemin sans avoir a appuyer sur E. Il faut etre sur la
        case du panneau, pas seulement a cote : passer devant sans s'arreter ne
        declenche rien.

        Le texte reste affiche tant qu'on ne quitte pas la case, mais ne
        recouvre jamais un message qui vient d'arriver (cle ramassee, coffre
        ouvert, mauvaise sequence) : ce message-la passe d'abord, et
        l'inscription revient quand il s'efface. Un panneau peut en revanche
        remplacer un autre panneau tout de suite."""
        sign = next(
            (obj for obj in self.objects
             if obj.type == 'sign' and obj.cell == self.cell and obj.visible_to(self)),
            None,
        )
        if sign is None:
            # On vient de quitter la case : l'inscription s'efface immediatement,
            # au lieu de trainer le temps que son compte a rebours expire. On ne
            # coupe que l'inscription elle-meme : un message de jeu affiche
            # entre-temps garde ses secondes.
            if self._sign_underfoot is not None and self.message == self._sign_underfoot:
                self.message_time = 0
            self._sign_underfoot = None
            return False

        self._sign_underfoot = sign.text
        sign_texts = {obj.text for obj in self.objects if obj.type == 'sign'}
        if self.message_time <= 0 or self.message in sign_texts:
            self.say(sign.text)
        return True
