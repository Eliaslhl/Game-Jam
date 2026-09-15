"""Rendu et lancement du Labyrinthe des Ames, niveau final de Kadir."""
import math
import os
import sys
import textwrap
from pathlib import Path
import pygame
from entities.ghost import YureiWalk
from systems.final_level import FinalLevel
from views.pixel_art import PixelTiles

SIZE=(400,280)
WINDOW=(800,560)
VIEW=pygame.Rect(0,34,400,190)
GOLD=(224,191,119)
INK=(12,17,25)
WHITE=(222,225,216)


class FinalGame:
    def __init__(self):
        self.level=FinalLevel()
        self.tiles=PixelTiles(self.level)
        self.font=pygame.font.Font(None,14)
        self.small=pygame.font.Font(None,12)
        self.title=pygame.font.Font(None,24)
        self.yurei=YureiWalk()
        self.ghost_frames=[pygame.transform.scale(frame,(13,23)) for frame in self.yurei.frames]
        self.elapsed=0.0
        self.facing_left=False
        self.moving=False
        self.map_open=False
        self.help_open=False
        self.camera=pygame.Vector2()
        self.smoke=pygame.Surface(VIEW.size,pygame.SRCALPHA)
        self.shade=pygame.Surface(VIEW.size,pygame.SRCALPHA)
        self.lights={}
        self.zone_name=''
        self.zone_timer=0.0
        self.update_camera()

    def label(self,screen,text,position,color=WHITE,font=None):
        screen.blit((font or self.font).render(text,False,color),position)

    def update_camera(self):
        p=self.level.position
        self.camera.update(max(0,min(p.x-200,self.level.width*16-400)),max(0,min(p.y-95,self.level.height*16-190)))
        self.camera.update(round(self.camera.x),round(self.camera.y))

    def update(self,dt,direction):
        if self.map_open or self.help_open:
            return
        old=self.level.position.copy()
        self.level.update(dt,direction)
        self.moving=old.distance_to(self.level.position)>.01
        if direction[0]: self.facing_left=direction[0]<0
        self.elapsed+=dt
        self.update_camera()
        zone=self.level.zone()['name']
        if zone!=self.zone_name:
            self.zone_name=zone
            self.zone_timer=3.0
        self.zone_timer=max(0,self.zone_timer-dt)

    def event(self,key):
        if key==pygame.K_m:
            self.map_open=not self.map_open
        elif key==pygame.K_h:
            self.help_open=not self.help_open
        elif key==pygame.K_r:
            self.__init__()
        elif not self.map_open and not self.help_open:
            self.level.action(key)

    def point(self,world):
        return round(world[0]-self.camera.x),round(world[1]-self.camera.y+VIEW.y)

    def glow(self,radius,strength):
        key=(radius,strength)
        if key not in self.lights:
            light=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
            for r in range(radius,0,-2):
                alpha=int(strength*(1-r/radius)**.55)
                pygame.draw.circle(light,(0,0,0,alpha),(radius,radius),r)
            self.lights[key]=light
        return self.lights[key]

    def draw(self,screen):
        level=self.level
        screen.fill(INK)
        screen.set_clip(VIEW)
        screen.blit(self.tiles.surface,(-self.camera.x,VIEW.y-self.camera.y))
        for y in range(max(0,int(self.camera.y/16)),min(level.height,int((self.camera.y+VIEW.h)/16)+1)):
            for x in range(max(0,int(self.camera.x/16)),min(level.width,int((self.camera.x+VIEW.w)/16)+1)):
                tile=level.tile(x,y)
                px,py=self.point(level.center((x,y)))
                rect=pygame.Rect(px-8,py-8,16,16)
                if tile=='Y':
                    pygame.draw.rect(screen,(64,62,63),rect.inflate(-1,-1))
                    pygame.draw.rect(screen,(129,108,58),rect.inflate(-4,-2),1)
                    for offset in (-4,4):
                        pygame.draw.line(screen,(245,209,110),(px+offset,py-5),(px+offset,py+5))
                    if level.ghost:
                        pygame.draw.line(screen,(155,239,226),(px-2,py-3),(px+2,py+3))
                elif tile in 'ABC' and tile not in level.doors:
                    pygame.draw.rect(screen,(65,43,40),rect.inflate(-2,0))
                    pygame.draw.rect(screen,(153,97,65),rect.inflate(-2,0),1)
                    for ox in (-4,0,4): pygame.draw.line(screen,(111,71,48),(px+ox,py-7),(px+ox,py+7))
                    self.label(screen,tile,(px-3,py-4),GOLD,self.small)
                elif tile in '123' and tile not in level.keys:
                    pygame.draw.ellipse(screen,(70,62,39),(px-6,py+4,12,4))
                    screen.blit(self.tiles.art['key'],(px-4,py-6+round(math.sin(self.elapsed*3)*1)))
                elif tile=='P' and (x,y) not in level.picked:
                    screen.blit(self.tiles.art['potion'],(px-4,py-5))
                elif tile in 'abc' and level.ghost:
                    color=(173,245,231) if tile!='c' else (237,197,255)
                    pygame.draw.circle(screen,color,(px,py),6,1)
                    self.label(screen,tile.upper(),(px-3,py-4),color,self.small)
                    pygame.draw.circle(screen,color,(px,py),9+int(math.sin(self.elapsed*3)*2),1)
                elif tile=='O':
                    screen.blit(self.tiles.art['stele'],(px-5,py-7))
                elif tile=='F':
                    pygame.draw.ellipse(screen,(84,106,112),(px-13,py-7,26,15))
                    pygame.draw.ellipse(screen,(34,73,90),(px-10,py-5,20,10))
                    pygame.draw.line(screen,(107,197,194),(px-5,py),(px+4,py))
                    pygame.draw.rect(screen,(112,144,142),(px-2,py-10,4,9))
                elif tile=='^':
                    color=(200,108,98) if not level.ghost else (89,106,112)
                    for ox in (-6,0,6):
                        pygame.draw.polygon(screen,color,[(px+ox-2,py+4),(px+ox,py-3),(px+ox+2,py+4)])
                elif tile=='E':
                    color=(119,232,155) if len(level.keys)==3 else (64,122,98)
                    pygame.draw.rect(screen,(29,55,49),(px-10,py-14,20,25))
                    pygame.draw.rect(screen,color,(px-10,py-14,20,25),2,border_radius=8)
                    pygame.draw.rect(screen,(14,30,30),(px-5,py-6,10,16))
                    for i in range(3): pygame.draw.rect(screen,GOLD if str(i+1) in level.keys else (81,84,68),(px-7+i*6,py-17,3,3))
        # Fumigene : dense pour le vivant, transparent et ponctue de lucioles pour l'ame.
        self.smoke.fill((0,0,0,0))
        for cell in level.cells('~c'):
            px,py=self.point(level.center(cell)); py-=VIEW.y
            if -25<px<425 and -25<py<215:
                alpha=32 if level.ghost else 165
                pygame.draw.rect(self.smoke,(94,43,135,alpha),(px-8,py-8,16,16))
                phase=self.elapsed*.75+cell[0]*1.9+cell[1]*2.3
                pygame.draw.circle(self.smoke,(144,77,181,alpha),(round(px+math.sin(phase)*5),round(py+math.cos(phase)*4)),10)
                if level.ghost:
                    pygame.draw.rect(self.smoke,(227,182,252,210),(px+round(math.sin(phase)*6),py,1,1))
        screen.blit(self.smoke,VIEW.topleft)
        for wx,wy in self.tiles.torches:
            px,py=self.point((wx,wy))
            pygame.draw.rect(screen,(93,60,39),(px-2,py,4,6))
            flame=4+int(math.sin(self.elapsed*11+wx)*1.5)
            pygame.draw.polygon(screen,(205,112,47),[(px-3,py),(px,py-flame-3),(px+3,py)])
            pygame.draw.line(screen,(255,223,131),(px,py),(px,py-flame))
        if level.ghost:
            cx,cy=self.point(level.mode.corpse_position)
            pygame.draw.ellipse(screen,(118,105,109),(cx-6,cy-2,12,5))
        px,py=self.point(level.position)
        pygame.draw.ellipse(screen,(12,19,27),(px-6,py+2,12,5))
        if level.ghost:
            index=int(self.elapsed/.14)%5 if self.moving else 0
            frame=self.ghost_frames[index]
            if self.facing_left: frame=pygame.transform.flip(frame,True,False)
            screen.blit(frame,(px-6,py-19))
        else:
            frame=self.tiles.art['player']
            if self.facing_left: frame=pygame.transform.flip(frame,True,False)
            screen.blit(frame,(px-5,py-8-(int(self.elapsed*8)%2 if self.moving else 0)))
        # Eclairage soustractif : les torches et le joueur percent l'obscurite.
        self.shade.fill((4,7,15,210))
        radius=level.vision
        self.shade.blit(self.glow(radius,235),(px-radius,py-VIEW.y-radius),special_flags=pygame.BLEND_RGBA_SUB)
        for wx,wy in self.tiles.torches:
            tx,ty=self.point((wx,wy))
            if -45<tx<445 and -45<ty-VIEW.y<235:
                self.shade.blit(self.glow(43,120),(tx-43,ty-VIEW.y-43),special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(self.shade,VIEW.topleft)
        screen.set_clip(None)
        self.draw_hud(screen)
        if self.map_open: self.draw_map(screen)
        if self.help_open: self.draw_help(screen)
        if level.won: self.draw_win(screen)

    def draw_hud(self,screen):
        level=self.level
        pygame.draw.rect(screen,INK,(0,0,400,34))
        self.label(screen,'LE LABYRINTHE DES AMES',(10,6),GOLD)
        self.label(screen,level.zone()['name'],(10,21),(139,156,163),self.small)
        self.label(screen,f'CLES {len(level.keys)}/3',(268,7),GOLD)
        self.label(screen,f'FIOLES {level.mode.potions.count}',(332,7),(192,150,228))
        self.label(screen,' '.join(f'{s.upper()}' if s in level.seals else '-' for s in 'abc'),(333,21),(132,210,195),self.small)
        pygame.draw.line(screen,(61,65,64),(10,32),(390,32))
        pygame.draw.rect(screen,INK,(0,224,400,56))
        pygame.draw.line(screen,(61,65,64),(10,225),(390,225))
        status='AME ERRANTE' if level.ghost else 'VIVANT'
        self.label(screen,status,(10,231),(154,222,211) if level.ghost else WHITE,self.small)
        if level.ghost:
            pygame.draw.rect(screen,(43,48,63),(83,231,99,4))
            pygame.draw.rect(screen,(172,136,223),(83,231,int(99*level.mode.time_remaining/level.mode.duration),4))
            self.label(screen,f'{level.mode.time_remaining:.1f}s',(187,229),(199,166,233),self.small)
        else:
            self.label(screen,'Trouvez les 3 cles, puis le seuil au sud-est.',(82,231),(133,153,161),self.small)
        message=level.message if level.message_time>0 else 'Explorez les ailes. Les lueurs dorees signalent un passage pour les ames.'
        for i,line in enumerate(textwrap.wrap(message,82)):
            self.label(screen,line,(10,243+i*9),WHITE,self.small)
        self.label(screen,'ZQSD / fleches : bouger   P : potion   E : agir   M : carte   H : aide',(10,268),(136,149,157),self.small)
        if self.zone_timer>0:
            zone=level.zone()
            image=self.font.render(zone['subtitle'],False,(202,202,183))
            bg=pygame.Surface((image.get_width()+16,19),pygame.SRCALPHA); bg.fill((12,17,25,195))
            screen.blit(bg,((400-bg.get_width())//2,40))
            screen.blit(image,((400-image.get_width())//2,45))

    def draw_map(self,screen,reveal_all=False):
        pygame.draw.rect(screen,(12,18,27),(25,6,350,268))
        pygame.draw.rect(screen,(100,96,77),(25,6,350,268),1)
        self.label(screen,'ATLAS DES AMES',(43,14),GOLD)
        self.label(screen,'M : reprendre',(293,15),(145,161,166),self.small)
        level=self.level
        for y,row in enumerate(level.grid):
            for x,t in enumerate(row):
                if not reveal_all and (x,y) not in level.explored: continue
                color=(47,58,67) if t=='#' else (98,112,111)
                if t=='Y': color=(215,180,94)
                if t in '~c': color=(112,66,152)
                if t in '123' and t not in level.keys: color=GOLD
                if t=='E': color=(84,184,117)
                if t in 'ABC' and t not in level.doors: color=(179,91,68)
                pygame.draw.rect(screen,color,(47+x*5,34+y*5,4,4))
        x,y=level.cell
        pygame.draw.rect(screen,(230,246,232),(46+x*5,33+y*5,6,6),1)
        self.label(screen,'Or : passage spectral   Violet : brume   Vert : sortie',(45,254),(178,188,182),self.small)

    def draw_help(self,screen):
        pygame.draw.rect(screen,(13,20,30),(27,28,346,224))
        pygame.draw.rect(screen,(97,97,81),(27,28,346,224),1)
        self.label(screen,'CE QUE LES MORTS NOUS APPRENNENT',(43,42),GOLD)
        lines=['Explorez les trois ailes et retrouvez leurs trois cles.',
               '1. Approchez un mur aux lueurs dorees.',
               '2. P : buvez une fiole. Votre corps reste sur place.',
               '3. Traversez et approchez le sceau lumineux.',
               '4. Entree : revenez au corps (ou attendez 10 secondes).',
               '5. Vivant, E pres de la porte marquee A, B ou C.',
               '6. Prenez la cle puis cherchez la prochaine aile.',
               '',
               'La brume violette accueille seulement les fantomes.',
               'Votre vision y est plus claire et porte plus loin.',
               'Les pics vous renvoient au sanctuaire sans perdre les cles.',
               'Les potions au sol ne se ramassent qu une seule fois.',
               'M : atlas / pause     R : recommencer     Echap : quitter',
               '', 'H : reprendre l exploration']
        for i,line in enumerate(lines): self.label(screen,line,(43,63+i*12),WHITE,self.small)

    def draw_win(self,screen):
        veil=pygame.Surface(SIZE,pygame.SRCALPHA); veil.fill((6,16,22,220)); screen.blit(veil,(0,0))
        self.label(screen,'LES AMES SONT LIBRES',(103,91),GOLD,self.title)
        self.label(screen,'Vous avez retrouve les trois cles du labyrinthe.',(91,124),WHITE,self.small)
        self.label(screen,f'{int(self.level.time)//60} min {int(self.level.time)%60:02d} s   |   {len(self.level.discoveries)}/4 steles decouvertes',(110,143),(143,189,173))
        self.label(screen,'R : explorer a nouveau    Echap : quitter',(105,172),WHITE,self.small)


def main():
    if '--smoke-test' in sys.argv:
        os.environ.setdefault('SDL_VIDEODRIVER','dummy')
        os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    pygame.init()
    try:
        window=pygame.display.set_mode(WINDOW)
        pygame.display.set_caption('Le Labyrinthe des Ames - Kadir')
        canvas=pygame.Surface(SIZE)
        game=FinalGame()
        clock=pygame.time.Clock()
        running=True
        while running:
            dt=min(clock.tick(60)/1000,.05)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: running=False
                    else: game.event(event.key)
            keys=pygame.key.get_pressed()
            direction=(int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_q] or keys[pygame.K_LEFT]),int(keys[pygame.K_s] or keys[pygame.K_DOWN])-int(keys[pygame.K_w] or keys[pygame.K_z] or keys[pygame.K_UP]))
            game.update(dt,direction)
            game.draw(canvas)
            pygame.transform.scale(canvas,WINDOW,window)
            pygame.display.flip()
            if '--smoke-test' in sys.argv: running=False
    finally:
        pygame.quit()


if __name__=='__main__':
    main()
