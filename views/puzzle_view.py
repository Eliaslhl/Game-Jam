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

COLORS = {'blue':(105,193,255),'red':(245,120,119),'green':(133,226,162),'silver':(218,230,244)}

class PuzzleGame(SimpleMapGame):
    def __init__(self):
        super().__init__(PuzzleLevel())
        self.special_tiles = [t for t in self.special_tiles if t[2] != 'D']
        self.feedback_fx = SanctuaryFeedback()
        self.music_paused = False
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
        silent = self.level.trial_room is not None
        if pygame.mixer.get_init() and silent != self.music_paused:
            if silent: pygame.mixer.music.pause()
            else: pygame.mixer.music.unpause()
            self.music_paused = silent
        dx,dy=self.feedback_fx.shake()
        self.camera.x+=dx
        self.camera.y+=dy

    def event(self,key):
        if key in (pygame.K_r, pygame.K_n):
            if pygame.mixer.get_init(): pygame.mixer.music.unpause()
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
        if not self.map_open and not self.level.won:
            success=next((p for p in reversed(self.feedback_fx.pulses) if p.kind=='solved' and .3<p.age<1.9),None)
            if success:
                title={'tomb':'LE SECRET DES TOMBES','statue':'LE GARDIEN SE REVEILLE','wall':'LA PIERRE SE DECHIRE'}.get(success.puzzle_id,'LE SANCTUAIRE REPOND')
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
        for obj in sorted(level.objects,key=lambda o: 0 if o.type=='chest' else (2 if o.type=='key' else 1)):
            if not obj.visible_to(level): continue
            if obj.type in ('clue','footprint') and level.center(obj.cell).distance_to(level.position)>52: continue
            x,y=self.point(level.center(obj.cell))
            if obj.type in ('tomb','statue','wall','socket'):
                spectral = level.ghost and (
                    (obj.type=='tomb' and obj.id=='tomb_'+str(level.targets['tomb'])) or
                    (obj.type=='wall' and obj.id=='wall_'+str(level.targets['wall'])) or
                    (obj.type=='socket' and obj.cell==level.targets['statue']))
                if obj.type=='statue':
                    if level.statue_motion:
                        start,end,when=level.statue_motion
                        t=min(1,max(0,(level.time-when)/.22))
                        x,y=self.point(level.center(start).lerp(level.center(end),t*t*(3-2*t)))
                    pygame.draw.ellipse(screen,(35,40,48),(x-7,y+3,14,5))
                    pygame.draw.rect(screen,(108,117,133),(x-5,y-5,10,11))
                    pygame.draw.circle(screen,(184,192,199),(x,y-9),5)
                    pygame.draw.line(screen,GOLD,(x-3,y-10),(x+3,y-10),2)
                elif obj.type=='socket':
                    pygame.draw.rect(screen,(133,125,104),(x-6,y-6,12,12),1)
                elif obj.type=='tomb':
                    pygame.draw.rect(screen,(49,49,61),(x-6,y-7,12,15),border_radius=3)
                    pygame.draw.rect(screen,(148,151,163),(x-5,y-8,10,12),1,border_radius=3)
                    pygame.draw.line(screen,(185,179,160),(x,y-6),(x,y+1))
                    pygame.draw.line(screen,(185,179,160),(x-2,y-3),(x+2,y-3))
                    if obj.state=='open': pygame.draw.ellipse(screen,(9,13,21),(x-4,y+1,8,5))
                elif obj.state=='broken':
                    for i in range(5):
                        pygame.draw.rect(screen,(131,126,118),(x-6+i*3,y+3+(i%2)*2,3,2))
                else:
                    pygame.draw.rect(screen,(109,108,113),(x-8,y-8,16,16))
                    for offset in (-7,0,7): pygame.draw.line(screen,(53,56,65),(x-8,y+offset),(x+7,y+offset))
                    pygame.draw.line(screen,(53,56,65),(x,y-7),(x,y+7))
                    if obj.id=='wall_'+str(level.targets['wall']) and level.wall_hits:
                        pygame.draw.lines(screen,(22,24,31),False,[(x-1,y-7),(x+2,y-2),(x-2,y+2),(x+2,y+6)],level.wall_hits)
                if spectral:
                    color=(147,242,239)
                    radius=9+round(2*math.sin(self.elapsed*4))
                    pygame.draw.ellipse(screen,color,(x-radius,y-5,radius*2,10),1)
                    for i in range(7):
                        angle=self.elapsed*2+i*math.tau/7
                        pygame.draw.circle(screen,color,(round(x+math.cos(angle)*radius),round(y-9+math.sin(angle)*7)),1)
                    self.label(screen,'*',(x-3,y-23-round(math.sin(self.elapsed*3)*3)),color,self.small)
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
                frame=pygame.mask.from_surface(self.tiles.art['key']).to_surface(
                    setcolor=(*COLORS.get(obj.key_id,GOLD),255),unsetcolor=(0,0,0,0))
                pygame.draw.circle(screen,COLORS.get(obj.key_id,GOLD),(x,y-10+bob),9,1)
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
        # Les messages courts restent sous les controles ; le parchemin est
        # reserve aux futures epreuves speciales.
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
        for i, key in enumerate(sorted(level.keys)):
            name={'blue':'Bleue','red':'Rouge','green':'Verte','silver':'Argent'}[key]
            self.label(screen,name,(x+i*40,pos['keys_y']+13),COLORS[key],self.tiny)

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
        message=level.message if level.message_time>0 else 'M : zones jaunes. P : observer. E : agir.'
        lines=[]
        current=''
        for word in message.split():
            candidate=(current+' '+word).strip()
            if current and self.tiny.size(candidate)[0]>w:
                lines.append(current)
                current=word
            else:
                current=candidate
        if current: lines.append(current)
        for i,line in enumerate(lines[:6]):
            self.label(screen,line,(x,pos['controls_y']+78+i*10),WHITE,self.tiny)


    def draw_map(self,screen):
        # L'atlas montre la geometrie mais jamais les solutions des enigmes.
        self._text_commands.clear()
        super().draw_map(screen)
        box=pygame.Rect(15,15,SIZE[0]-30,SIZE[1]-30)
        scale=min((box.w-10)/self.map_w,(box.h-10)/self.map_h)
        origin=(box.centerx-round(self.map_w*scale)//2,box.centery-round(self.map_h*scale)//2)
        unit=self.level.tile_size*scale
        for pid,room in self.level.rooms.items():
            rect=pygame.Rect(round(origin[0]+room.x*unit),round(origin[1]+room.y*unit),round(room.w*unit),round(room.h*unit))
            veil=pygame.Surface(rect.size,pygame.SRCALPHA); veil.fill((255,207,42,85))
            screen.blit(veil,rect)
            pygame.draw.rect(screen,(255,219,72),rect,2)
            self.label(screen,'OK' if self.level.puzzles.puzzles[pid].solved else '?',(rect.centerx-3,rect.centery-5),(255,239,136))
            door=next(o for o in self.level.objects if o.id=='entry_'+pid)
            dx=round(origin[0]+(door.cell[0]+.5)*unit);dy=round(origin[1]+(door.cell[1]+.5)*unit)
            pygame.draw.circle(screen,COLORS.get(door.required_keys[0],GOLD) if door.required_keys else WHITE,(dx,dy),3,1 if door.state=='open' else 0)
        self.label(screen,'Jaune ? : epreuve | Points colores : portes',(box.x+10,box.bottom-13),GOLD,self.small)

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
        if pygame.mixer.get_init(): pygame.mixer.music.unpause()
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
