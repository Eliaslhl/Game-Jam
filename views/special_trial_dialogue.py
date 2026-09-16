"""Parchemin conserve pour les futures epreuves speciales.

Mixin optionnel : appeler draw_parchment(screen) depuis leur vue.
Necessite level, font et label() fournis par la vue de jeu.
Source conservee depuis main, commit 2312f4f.
"""
import pygame
from views.simple_map_view import VIEW

PARCHMENT_BODY = (216, 192, 149)
PARCHMENT_LIGHT = (236, 217, 180)
PARCHMENT_EDGE = (120, 94, 61)
PARCHMENT_ROLL = (170, 134, 86)
PARCHMENT_INK = (58, 42, 30)


class SpecialTrialDialogue:
    def _wrap_to_width(self, text, font, width):
        """Coupe le texte en lignes qui tiennent dans `width` (repere du canevas),
        en mesurant vraiment la police : la MedievalSharp est a chasse variable,
        compter les caracteres donnerait des lignes trop courtes ou qui debordent."""
        lines, current = [], ""
        for word in str(text).split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def draw_parchment(self, screen):
        """Tous les messages du sanctuaire s'affichent ici, sur un parchemin
        deroule en bas de la zone de jeu, plutot que tasses dans la colonne de
        droite : les indices des enigmes sont des phrases entieres, il leur faut
        de la place pour etre lus. Le parchemin ne met pas le jeu en pause (on
        reste libre de bouger) et il est pose sous le joueur, jamais dessus."""
        level = self.level
        if level.message_time <= 0 or not level.message:
            return

        margin, roll_w, padding, line_h = 12, 6, 11, 16
        text_w = VIEW.w - 2 * (margin + roll_w + padding)
        lines = self._wrap_to_width(level.message, self.font, text_w)[:4]
        body = pygame.Rect(0, 0, VIEW.w - 2 * (margin + roll_w), len(lines) * line_h + 2 * padding)
        body.bottomleft = (margin + roll_w, VIEW.bottom - margin)

        # Feuille : fond clair, lisere sombre, et une ligne claire en haut pour
        # donner l'impression d'un papier legerement bombe.
        pygame.draw.rect(screen, PARCHMENT_BODY, body)
        pygame.draw.rect(screen, PARCHMENT_EDGE, body, 1)
        pygame.draw.line(screen, PARCHMENT_LIGHT, (body.x + 1, body.y + 1), (body.right - 2, body.y + 1))

        # Les deux rouleaux, aux extremites, debordent un peu en hauteur.
        for roll_x in (body.x - roll_w, body.right):
            roll = pygame.Rect(roll_x, body.y - 3, roll_w, body.h + 6)
            pygame.draw.rect(screen, PARCHMENT_ROLL, roll, border_radius=3)
            pygame.draw.rect(screen, PARCHMENT_EDGE, roll, 1, border_radius=3)

        for i, line in enumerate(lines):
            self.label(
                screen, line, (body.centerx, body.y + padding + i * line_h),
                PARCHMENT_INK, self.font, align="center",
            )
