"""Sanctuaire jouable avec indices spectraux et interactions physiques."""
import math
import os
import sys
import pygame
from systems.puzzle_level import PuzzleLevel
from views.pixel_effects import DANGER_COLOR, lerp_color
from views.sanctuary_feedback import SanctuaryFeedback
from views.simple_map_view import (
    SimpleMapGame,
    SIZE,
    VIEW,
    SIDEBAR,
    SIDEBAR_W,
    GOLD,
    INK,
    WHITE,
    PANEL_BG,
    RESURRECTION_COUNT,
    STATUS_ALIVE_BG,
    STATUS_GHOST_BG,
    STATUS_DEAD_BG,
    DEAD_STATUS,
    TEXT_DIM,
    DIVIDER,
    GHOST_STATUS,
    GHOST_BAR_BG,
    GHOST_BAR_FILL,
    POTION_COUNT,
)

COLORS = {'blue':(105,193,255),'red':(245,120,119),'green':(133,226,162)}

# Parchemin des messages (voir PuzzleGame.draw_parchment).
PARCHMENT_BODY = (216, 192, 149)
PARCHMENT_LIGHT = (236, 217, 180)
PARCHMENT_EDGE = (120, 94, 61)
PARCHMENT_ROLL = (170, 134, 86)
PARCHMENT_INK = (58, 42, 30)


class PuzzleGame(SimpleMapGame):
    def __init__(self):
        super().__init__(PuzzleLevel())
        self.special_tiles = [t for t in self.special_tiles if t[2] != 'D']
        self.feedback_fx = SanctuaryFeedback()
        # Le texte passe par la file `_text_commands` et le present() de
        # SimpleMapGame (voir views/simple_map_view.py) : meme police que le
        # menu (MedievalSharp) et meme rendu net, plutot qu'une police par
        # defaut et un rendu separe rien que pour ce mode.

    def drain_events(self):
        while self.level.events:
            self.feedback_fx.emit(self.level.events.pop(0))

    def update(self,dt,direction):
        if self.map_open:
            return
        self.drain_events()
        simulation_dt=self.feedback_fx.advance(dt)
        super().update(simulation_dt,direction)
        self.drain_events()
        dx,dy=self.feedback_fx.shake()
        self.camera.x+=dx
        self.camera.y+=dy

    def event(self,key):
        if key == pygame.K_r:
            self.__init__()
            return
        if self.feedback_fx.freeze_remaining>0 and key not in (pygame.K_m,pygame.K_r):
            return
        super().event(key)

    def draw_lighting(self,screen,torch_points,px,py,is_ghost):
        super().draw_lighting(screen,torch_points,px,py,is_ghost)
        self.feedback_fx.draw(screen,self)
        if is_ghost:
            aura=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
            for i in range(7):
                angle=self.elapsed*.7+i*math.tau/7
                radius=16+4*math.sin(self.elapsed*2+i)
                pygame.draw.circle(aura,(139,211,226,95),(round(px+math.cos(angle)*radius),round(py-5+math.sin(angle)*radius*.6)),1)
            screen.blit(aura,(0,0))

    def draw(self,screen):
        self._text_commands.clear()
        super().draw(screen)
        # Ni sur la carte ni sur les ecrans de fin : ceux-ci effacent la file de
        # textes pour n'afficher qu'eux, et le dernier message y ferait doublon.
        if not self.map_open and not self.level.won and not self.level.lost:
            self.draw_parchment(screen)
        if not self.map_open and not self.level.won:
            success=next((p for p in reversed(self.feedback_fx.pulses) if p.kind=='solved' and .3<p.age<1.9),None)
            if success:
                title={'statues_blue':'LE SERMENT DES VEILLEURS','levers_red':'LES VOIX S ACCORDENT','path_green':'LE CHEMIN SE SOUVIENT'}.get(success.puzzle_id,'LE SANCTUAIRE REPOND')
                width=self.small.size(title)[0]+20
                rect=pygame.Rect((VIEW.w-width)//2,VIEW.y+10,width,22)
                veil=pygame.Surface(rect.size,pygame.SRCALPHA);veil.fill((12,18,27,210))
                screen.blit(veil,rect)
                pygame.draw.line(screen,GOLD,rect.bottomleft,rect.bottomright)
                self.label(screen,title,(rect.centerx,rect.centery),GOLD,self.small,align="center",valign="middle")
            for pulse in self.feedback_fx.pulses:
                if pulse.kind=='key':
                    start=pygame.Vector2(self.point(pulse.position))
                    end=pygame.Vector2(SIDEBAR.x+18,107)
                    t=min(1,pulse.age/.8)
                    pos=start.lerp(end,1-(1-t)**3)
                    frame=self.tiles.art['key']
                    screen.blit(frame,frame.get_rect(center=(round(pos.x),round(pos.y))))

    def draw_special_tiles(self,screen,level):
        super().draw_special_tiles(screen,level)
        # Le vivant ne distingue pas les cases sures des pieges.
        danger=pygame.Rect(level.data['danger_room']['rect'])
        for y in range(danger.top,danger.bottom):
            for x in range(danger.left,danger.right):
                px,py=self.point(level.center((x,y)))
                pygame.draw.rect(screen,(65,71,73),(px-7,py-7,14,14))
                pygame.draw.rect(screen,(114,119,111),(px-6,py-6,12,12),1)
        for obj in sorted(level.objects,key=lambda o: 0 if o.type=='chest' else (2 if o.type=='key' else 1)):
            if not obj.visible_to(level): continue
            if obj.type in ('clue','footprint') and level.center(obj.cell).distance_to(level.position)>52: continue
            x,y=self.point(level.center(obj.cell))
            if obj.type in ('statue','lever'):
                active=obj.state=='active'
                age=self.feedback_fx.age('solved',puzzle_id=obj.puzzle_id)
                sequence=level.puzzles.puzzles[obj.puzzle_id].solution
                glowing=active and (age is None or age>=sequence.index(obj.id)*.10)
                color=(132,224,207) if glowing else (147,142,133)
                if glowing:
                    pygame.draw.circle(screen,(48,91,87),(x,y),8,1)
                pygame.draw.rect(screen,(47,52,57),(x-5,y-4,10,10))
                if obj.type=='statue':
                    pygame.draw.circle(screen,color,(x,y-6),4)
                else:
                    pygame.draw.line(screen,color,(x,y+2),(x+(4 if active else -4),y-5),2)
                self.label(screen,obj.text,(x,y+5),GOLD,self.small,align="center")
            elif obj.type=='clue':
                # L'inscription se dechiffre en approchant ; pas de code expose au loin.
                angle=self.elapsed*1.2
                pygame.draw.circle(screen,(90,157,170),(x,y),5,1)
                for i in range(3):
                    px=x+round(math.cos(angle+i*math.tau/3)*4)
                    py=y+round(math.sin(angle+i*math.tau/3)*4)
                    pygame.draw.rect(screen,(162,235,231),(px,py,1,1))
            elif obj.type=='footprint':
                sequence=level.puzzles.puzzles[obj.puzzle_id].solution
                index=sequence.index(obj.id)
                pygame.draw.ellipse(screen,(134,225,215),(x-4,y-2,3,5))
                pygame.draw.ellipse(screen,(134,225,215),(x+1,y-3,3,5))
                if index+1<len(sequence):
                    next_obj=next(o for o in level.objects if o.id==sequence[index+1])
                    direction=pygame.Vector2(next_obj.cell)-obj.cell
                    phase=(self.elapsed*1.3)%1
                    pos=pygame.Vector2(x,y)+direction*(phase*12)
                    pygame.draw.circle(screen,(201,255,234),(round(pos.x),round(pos.y)),1)
            elif obj.type=='chest':
                if obj.state=='hidden':continue
                self.draw_chest(screen,obj,x,y)
            elif obj.type=='key':
                if obj.state=='collected' or obj.id not in level.key_ready_at:continue
                # Sprite strictement identique a celui du sanctuaire d'origine.
                bob=round(math.sin(self.elapsed*3+obj.cell[0]*1.7+obj.cell[1]*2.3)*2)
                age=.65-(level.key_ready_at[obj.id]-level.time)
                lift=round(10*min(1,max(0,age/.65)))
                screen.blit(self.key_glow,(x-14,y-14+bob-lift),special_flags=pygame.BLEND_RGBA_ADD)
                frame=self.tiles.art['key']
                screen.blit(frame,(x-frame.get_width()//2,y-frame.get_height()//2+bob-lift))
            elif obj.type=='door':
                color=COLORS.get(obj.required_keys[0],GOLD) if len(obj.required_keys)==1 else GOLD
                pygame.draw.rect(screen,color,(x-7,y-7,14,14),1)
                age=self.feedback_fx.age('door',object_id=obj.id)
                opening=min(1,(age or 0)/.6) if obj.state=='open' and age is not None else (1 if obj.state=='open' else 0)
                if opening<1:
                    for offset in (-4,0,4):
                        pygame.draw.line(screen,color,(x+offset,y-6),(x+offset,y+6-round(12*opening)))
            elif obj.type=='sign':
                pygame.draw.rect(screen,(112,94,66),(x-5,y-5,10,8))
                self.label(screen,'?',(x,y-1),WHITE,self.small,align="center",valign="middle")

    def draw_chest(self,screen,obj,x,y):
        age=self.feedback_fx.age('solved',puzzle_id=obj.puzzle_id)
        scale=min(1,max(0,((age-.28)/.45))) if age is not None else 1
        if scale<=0:return
        surface=pygame.Surface((24,28),pygame.SRCALPHA)
        opening_age=self.feedback_fx.age('chest',object_id=obj.id)
        opening=min(1,(opening_age or 0)/.5) if obj.state=='open' and opening_age is not None else (1 if obj.state=='open' else 0)
        # Bois sombre, ferrures de laiton : palette des portes et des torches.
        pygame.draw.rect(surface,(40,29,26),(3,15,18,10))
        pygame.draw.rect(surface,(110,77,45),(4,16,16,8))
        pygame.draw.line(surface,(163,124,72),(4,16),(19,16))
        for offset in (6,16):pygame.draw.rect(surface,(187,150,80),(offset,16,2,8))
        lid_y=11-round(opening*7)
        pygame.draw.rect(surface,(60,42,30),(3,lid_y,18,6))
        pygame.draw.rect(surface,(139,101,55),(4,lid_y+1,16,4))
        pygame.draw.line(surface,(217,177,95),(4,lid_y+1),(19,lid_y+1))
        if opening:
            pygame.draw.rect(surface,(238,205,124),(6,15,12,2))
        else:pygame.draw.rect(surface,(237,196,102),(11,16,3,3))
        sprite=pygame.transform.scale(surface,(max(1,round(24*scale)),max(1,round(28*scale))))
        screen.blit(sprite,sprite.get_rect(midbottom=(x,y+6)))

    def draw_top_bar(self,screen):
        pygame.draw.rect(screen,INK,(0,0,VIEW.w,VIEW.y))
        pygame.draw.line(screen,DIVIDER,(0,VIEW.y-1),(VIEW.w,VIEW.y-1))
        self.label(screen,'LE SANCTUAIRE - TROIS ENIGMES',(8,3),GOLD,self.font)
        self.label(screen,'Observer en fantome, agir en vivant',(8,19),(139,156,163),self.small)

    def _puzzle_sidebar_layout(self):
        """Meme esprit que SimpleMapGame._sidebar_layout() (positions partagees,
        badges/icones/pips) mais avec le contenu propre au mode enigmes :
        recharge du poison, cles sur 3, indice courant, controles."""
        level = self.level
        x = SIDEBAR.x + 10
        w = SIDEBAR_W - 20
        y = 12
        pos = {"x": x, "w": w, "title_y": y}
        y += 14
        pos["div1_y"] = y
        y += 8
        badge_h = 16
        pos["badge"] = (x, y, w, badge_h)
        y += badge_h + 8
        pos["poison_y"] = y
        y += 13
        pos["resurrection_y"] = y
        y += 13
        y += 4
        pos["cooldown_y"] = y
        y += 12
        if level.ghost:
            pos["ghost_timer_y"] = y
            y += 12
            pos["ghost_bar"] = (x, y, w, 5)
            y += 13
            # Place reservee des l'entree en fantome pour l'alerte de fin de
            # temps : la colonne ne sursaute pas quand elle apparait.
            pos["danger_y"] = y
            y += 12
        else:
            pos["ghost_timer_y"] = None
            pos["ghost_bar"] = None
            pos["danger_y"] = None
        y += 4
        pos["div2_y"] = y
        y += 8
        pos["keys_label_y"] = y
        y += 12
        pos["keys_y"] = y
        y += 24
        y += 4
        # Les messages ne sont plus ici mais sur le parchemin (draw_parchment) :
        # la colonne ne garde que ce qui doit rester lisible en permanence.
        pos["div3_y"] = y
        y += 8
        pos["controls_label_y"] = y
        y += 12
        pos["controls_y"] = y
        return pos

    def draw_sidebar(self,screen):
        level = self.level
        pos = self._puzzle_sidebar_layout()
        x, w = pos["x"], pos["w"]
        pygame.draw.rect(screen, PANEL_BG, SIDEBAR)
        pygame.draw.line(screen, GOLD, (SIDEBAR.x, 0), (SIDEBAR.x, SIDEBAR.h), 1)
        self.label(screen, "ENIGMES", (x, pos["title_y"]), GOLD, self.small)
        pygame.draw.line(screen, DIVIDER, (x, pos["div1_y"]), (x + w, pos["div1_y"]))

        # Trois etats, pas deux : vivant, fantome, mort (voir le meme choix dans
        # SimpleMapGame.draw_sidebar). En fantome, tout ce qui touche au compte a
        # rebours vire progressivement au rouge quand la resurrection devient
        # urgente : meme signal que la vignette et les secousses.
        danger = self.danger_intensity
        if level.dead or level.lost:
            status, badge_bg, badge_fg = "MORT", STATUS_DEAD_BG, DEAD_STATUS
        elif level.ghost:
            status, badge_bg = "FANTOME", STATUS_GHOST_BG
            badge_fg = lerp_color(GHOST_STATUS, DANGER_COLOR, danger)
        else:
            status, badge_bg, badge_fg = "VIVANT", STATUS_ALIVE_BG, WHITE
        bx, by, bw, bh = pos["badge"]
        pygame.draw.rect(screen, badge_bg, pos["badge"], border_radius=4)
        pygame.draw.rect(screen, badge_fg, pos["badge"], width=1, border_radius=4)
        self.label(
            screen, status, (bx + bw / 2, by + bh / 2), badge_fg, self.small,
            align="center", valign="middle",
        )

        self._draw_potion_row(screen, x, w, pos["poison_y"], POTION_COUNT, "Poison", level.mode.poison_potions.count)
        self._draw_potion_row(
            screen, x, w, pos["resurrection_y"], RESURRECTION_COUNT, "Resurrection", level.mode.resurrection_potions.count
        )

        cooldown_text = f"Recharge {level.cooldown:.1f}s" if level.cooldown else "Poison pret"
        cooldown_color = TEXT_DIM if level.cooldown else (150, 210, 160)
        self.label(screen, cooldown_text, (x, pos["cooldown_y"]), cooldown_color, self.tiny)

        if pos["ghost_bar"] is not None:
            bar_color = lerp_color(GHOST_BAR_FILL, DANGER_COLOR, danger)
            bar = pygame.Rect(*pos["ghost_bar"])
            pygame.draw.rect(screen, GHOST_BAR_BG, bar, border_radius=2)
            fill_w = max(0, int(bar.w * level.mode.time_remaining / level.mode.duration))
            if fill_w > 0:
                pygame.draw.rect(screen, bar_color, (bar.x, bar.y, fill_w, bar.h), border_radius=2)
            self.label(screen, f"Retour dans {level.mode.time_remaining:.1f}s", (x, pos["ghost_timer_y"]), badge_fg, self.tiny)
            if danger:
                self.label(screen, "REVENEZ VITE !", (x, pos["danger_y"]), bar_color, self.tiny)

        pygame.draw.line(screen, DIVIDER, (x, pos["div2_y"]), (x + w, pos["div2_y"]))
        self.label(screen, "CLES", (x, pos["keys_label_y"]), TEXT_DIM, self.tiny)
        self._draw_key_pips(screen, x, pos["keys_y"], len(level.keys), 3)

        pygame.draw.line(screen, DIVIDER, (x, pos["div3_y"]), (x + w, pos["div3_y"]))
        self.label(screen, "CONTROLES", (x, pos["controls_label_y"]), TEXT_DIM, self.tiny)
        for i, line in enumerate([
            "P : fantome / retour",
            "Entree : retour",
            "E : interagir",
            "M : carte / pause",
            "R : recommencer",
            "F11 : ecran",
        ]):
            self.label(screen, line, (x, pos["controls_y"] + i * 12), (180, 192, 200), self.tiny)

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

    def draw_map(self,screen):
        # L'atlas montre la geometrie mais jamais les solutions des enigmes.
        self._text_commands.clear()
        super().draw_map(screen)

    def draw_win(self,screen):
        # Plus de clear() ici : comme sur l'ecran de mort, le HUD reste visible
        # mais passe au second plan sous le voile pose par present().
        super().draw_win(screen)


def run(window):
    """Partie dans la fenetre du menu ; le menu reste proprietaire de Pygame."""
    fullscreen=bool(window.get_flags() & pygame.FULLSCREEN)
    canvas=pygame.Surface(SIZE)
    game=PuzzleGame()
    clock=pygame.time.Clock()
    try:
        while True:
            dt=min(clock.tick(60)/1000,.05)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    return 'quit'
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        return 'menu'
                    if event.key==pygame.K_F11:
                        fullscreen=not fullscreen
                        window=pygame.display.set_mode((0,0) if fullscreen else (940,724), pygame.FULLSCREEN if fullscreen else 0)
                    else:
                        game.event(event.key)
            k=pygame.key.get_pressed()
            direction=(int(k[pygame.K_d] or k[pygame.K_RIGHT])-int(k[pygame.K_q] or k[pygame.K_a] or k[pygame.K_LEFT]),int(k[pygame.K_s] or k[pygame.K_DOWN])-int(k[pygame.K_z] or k[pygame.K_w] or k[pygame.K_UP]))
            game.update(dt,direction)
            game.draw(canvas)
            game.present(canvas,window)
            pygame.display.flip()
            if '--smoke-test' in sys.argv:
                return 'menu'
    finally:
        # Ne pas laisser la reverberation de la partie jouer sur le menu.
        for sound in game.feedback_fx.sounds.values():
            sound.stop()


def main():
    if '--smoke-test' in sys.argv:
        os.environ.setdefault('SDL_VIDEODRIVER','dummy')
        os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    pygame.init()
    try:
        fullscreen='--windowed' not in sys.argv and '--smoke-test' not in sys.argv
        window=pygame.display.set_mode((0,0) if fullscreen else (940,724), pygame.FULLSCREEN if fullscreen else 0)
        pygame.display.set_caption('Le Sanctuaire - Enigmes')
        run(window)
    finally:
        pygame.quit()


if __name__=='__main__':
    main()
