"""Sanctuaire jouable avec indices spectraux et interactions physiques."""
import math
import os
import sys
import textwrap
import pygame
from systems.puzzle_level import PuzzleLevel
from views.pixel_effects import DANGER_COLOR, lerp_color
from views.sanctuary_feedback import SanctuaryFeedback
from views.simple_map_view import SimpleMapGame, SIZE, VIEW, SIDEBAR, SIDEBAR_W, GOLD, INK, WHITE

COLORS = {'blue':(105,193,255),'red':(245,120,119),'green':(133,226,162)}


class PuzzleGame(SimpleMapGame):
    def __init__(self):
        super().__init__(PuzzleLevel())
        self.special_tiles = [t for t in self.special_tiles if t[2] != 'D']
        self.feedback_fx = SanctuaryFeedback()
        self.text_commands=[]
        self.display_fonts={}

    def label(self,screen,text,position,color=WHITE,font=None):
        self.text_commands.append((str(text),position,color,font or self.font,screen.get_clip().copy()))

    def present(self,canvas,window):
        size=(window.get_width(),window.get_height())
        origin=(0,0)
        window.blit(pygame.transform.scale(canvas,size),origin)
        sx,sy=size[0]/SIZE[0],size[1]/SIZE[1]
        for text,pos,color,font,clip in self.text_commands:
            key=(font,sy)
            if key not in self.display_fonts:
                self.display_fonts[key]=pygame.font.Font(None,max(12,round((14 if font==self.small else 18)*sy)))
            window.set_clip(pygame.Rect(origin[0]+round(clip.x*sx),origin[1]+round(clip.y*sy),round(clip.w*sx),round(clip.h*sy)))
            window.blit(self.display_fonts[key].render(text,True,color),(origin[0]+round(pos[0]*sx),origin[1]+round(pos[1]*sy)))
        window.set_clip(None)

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
        self.text_commands.clear()
        super().draw(screen)
        if not self.map_open and not self.level.won:
            success=next((p for p in reversed(self.feedback_fx.pulses) if p.kind=='solved' and .3<p.age<1.9),None)
            if success:
                title={'statues_blue':'LE SERMENT DES VEILLEURS','levers_red':'LES VOIX S ACCORDENT','path_green':'LE CHEMIN SE SOUVIENT'}.get(success.puzzle_id,'LE SANCTUAIRE REPOND')
                width=self.small.size(title)[0]+20
                rect=pygame.Rect((VIEW.w-width)//2,VIEW.y+10,width,22)
                veil=pygame.Surface(rect.size,pygame.SRCALPHA);veil.fill((12,18,27,210))
                screen.blit(veil,rect)
                pygame.draw.line(screen,GOLD,rect.bottomleft,rect.bottomright)
                self.label(screen,title,(rect.x+10,rect.y+6),GOLD,self.small)
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
                self.label(screen,obj.text,(x-3,y+5),GOLD,self.small)
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
                self.label(screen,'?',(x-3,y-5),WHITE,self.small)

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
        self.label(screen,'LE SANCTUAIRE - TROIS ENIGMES',(8,2),GOLD)
        self.label(screen,'Observer en fantome, agir en vivant',(8,19),WHITE,self.small)

    def draw_sidebar(self,screen):
        pygame.draw.rect(screen,INK,SIDEBAR)
        x=SIDEBAR.x+8
        level=self.level
        status_color=lerp_color((170,231,221),DANGER_COLOR,self.danger_intensity) if level.ghost else WHITE
        lines=[('ENIGMES',GOLD),('FANTOME' if level.ghost else 'VIVANT',status_color),
               (f'Poison : {level.mode.poison_potions.count}',(195,151,231)),
               (f'Resurrection : {level.mode.resurrection_potions.count}',(150,200,228)),
               (f'Recharge : {level.cooldown:.1f}s' if level.cooldown else 'Poison pret',WHITE),
               (f'Cles : {len(level.keys)}/3',GOLD)]
        for i,(text,color) in enumerate(lines):self.label(screen,text,(x,14+i*16),color,self.small)
        message=level.message if level.message_time>0 else 'Chapelle : statues. Jardin : chemin. Bibliotheque : leviers.'
        for i,line in enumerate(textwrap.wrap(message,23)[:6]):
            self.label(screen,line,(x,172+i*12),WHITE,self.small)
        for i,line in enumerate(['P : fantome / retour','Entree : retour','E : interagir','M : carte / pause','R : tout recommencer','F11 : fenetre / ecran']):
            self.label(screen,line,(x,274+i*14),(180,192,200),self.small)
        if level.ghost:
            bar_color=lerp_color((172,136,223),DANGER_COLOR,self.danger_intensity)
            pygame.draw.rect(screen,(43,48,63),(x,238,SIDEBAR_W-16,4))
            pygame.draw.rect(screen,bar_color,(x,238,int((SIDEBAR_W-16)*level.mode.time_remaining/level.mode.duration),4))
            self.label(screen,f'{level.mode.time_remaining:.1f} s',(x,251),bar_color if self.danger_intensity else (170,231,221),self.small)
            if self.danger_intensity:
                self.label(screen,'REVENEZ VITE !',(x,263),bar_color,self.small)

    def draw_map(self,screen):
        # L'atlas montre la geometrie mais jamais les solutions des enigmes.
        self.text_commands.clear()
        super().draw_map(screen)

    def draw_win(self,screen):
        self.text_commands.clear()
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
