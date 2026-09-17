"""Six pixel-art environments. Decorations never encode puzzle solutions."""
import math
import random
import pygame

# Special-room identities follow geography, never the random golden reward.
THEMES = {
    'tomb': ('LA CRYPTE DES MURMURES', (29, 36, 48), (122, 168, 195), 'bones'),
    'statue': ('LE JARDIN PUTREFIE', (26, 43, 33), (116, 175, 78), 'roots'),
    'wall': ('LA FORGE ENSEVELIE', (49, 29, 26), (232, 113, 54), 'embers'),
    'NW': ('LE THEATRE DES OUBLIES', (43, 28, 34), (189, 133, 103), 'theatre'),
    'NE': ('LE CACHOT DU GIVRE', (24, 39, 52), (113, 192, 219), 'ice'),
    'W': ('LES EAUX MAUDITES', (29, 43, 37), (129, 175, 91), 'water'),
}


class RoomAtmosphere:
    def __init__(self, level):
        self.rooms = {**level.rooms, **level.special_rooms}
        self.tiles = {}
        self.ghost_tiles = {}
        self.unit = level.tile_size
        for name, rect in self.rooms.items():
            surface = self.build(name, rect, level)
            self.tiles[name] = surface
            ghost = surface.copy()
            ghost.fill((145, 185, 225, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.ghost_tiles[name] = ghost

    def build(self, name, rect, level):
        _, base, accent, motif = THEMES[name]
        unit = self.unit
        surface = pygame.Surface((rect.w*unit, rect.h*unit), pygame.SRCALPHA)
        rng = random.Random(name)
        w, h = surface.get_size()
        for y in range(rect.h):
            for x in range(rect.w):
                if level.tile(rect.x+x, rect.y+y) == '#':
                    continue
                shade = rng.randrange(-6, 7)
                color = tuple(max(0, c+shade) for c in base)
                tile = pygame.Rect(x*unit,y*unit,unit,unit)
                pygame.draw.rect(surface,color,tile)
                pygame.draw.line(surface,tuple(c+11 for c in color),tile.topleft,tile.topright)
                pygame.draw.line(surface,tuple(max(0,c-9) for c in color),tile.bottomleft,tile.bottomright)
                if rng.random() < .5:
                    px,py=tile.x+4,tile.y+5
                    pygame.draw.lines(surface,(*accent,40),False,[(px,py),(px+3,py+3),(px+1,py+6)],1)
        # A border anchors each room without obscuring its interactive objects.
        pygame.draw.rect(surface,(*accent,90),(2,2,w-4,h-4),1)
        for i in range(12):
            x = 6 + (i*19) % (w-12)
            y = 5 if i%2 else h-9
            if motif == 'bones':
                pygame.draw.line(surface,(153,155,139),(x,y),(x+5,y+3),2)
                for dx,dy in ((0,0),(5,3)):
                    pygame.draw.circle(surface,(180,179,158),(x+dx,y+dy),2)
            elif motif == 'roots':
                pygame.draw.lines(surface,(64,92,48),False,[(x,y),(x+4,y+5),(x-2,y+11)],2)
                pygame.draw.ellipse(surface,(98,136,58),(x-3,y+4,6,3))
            elif motif == 'embers':
                pygame.draw.lines(surface,(156,66,32),False,[(x,y),(x+3,y+3),(x-2,y+6)],2)
                pygame.draw.line(surface,accent,(x,y),(x+2,y+2))
            elif motif == 'theatre':
                pygame.draw.rect(surface,(156,128,109),(x,y,2,6))
                pygame.draw.circle(surface,(247,162,112),(x,y-1),1)
                pygame.draw.line(surface,(113,38,57),(x,y+7),(x+7,y+10),2)
            elif motif == 'ice':
                pygame.draw.polygon(surface,(81,129,154),[(x-2,y+8),(x,y-2),(x+3,y+7)])
                pygame.draw.line(surface,accent,(x,y),(x,y+5))
            else:
                pygame.draw.ellipse(surface,(34,74,57),(x-4,y,12,6))
                pygame.draw.arc(surface,(91,127,74),(x-2,y+1,8,3),0,math.pi,1)
        self.draw_props(surface, motif, accent)
        # Keep solid wall cells untouched by the ornamental floor.
        for cy in range(rect.h):
            for cx in range(rect.w):
                if level.tile(rect.x+cx,rect.y+cy)=='#':
                    surface.fill((0,0,0,0),(cx*unit,cy*unit,unit,unit))
        return surface

    def draw_props(self, surface, motif, accent):
        """Architectural props hug the edges; they never masquerade as clues."""
        w,h=surface.get_size()
        # Cobwebs, cracked masonry and iron brackets frame the playable floor.
        for flip in (False,True):
            x=w-3 if flip else 3
            sign=-1 if flip else 1
            for length in (7,12,17):
                pygame.draw.line(surface,(77,80,82),(x,3),(x+sign*length,3+length),1)
                pygame.draw.line(surface,(77,80,82),(x,3+length),(x+sign*length,3),1)
        if motif=='bones':
            # Burial niches and a sealed coffin, away from the five puzzle tombs.
            for x in (6,w-17):
                pygame.draw.rect(surface,(12,17,23),(x,h-30,11,22),border_radius=4)
                pygame.draw.rect(surface,(78,86,92),(x,h-30,11,22),1,border_radius=4)
                pygame.draw.ellipse(surface,(171,167,143),(x+3,h-25,6,6))
                for dx in (4,7): pygame.draw.rect(surface,(22,26,30),(x+dx,h-23,1,2))
                for j in range(4): pygame.draw.line(surface,(126,128,117),(x+3,h-16+j*2),(x+8,h-16+j*2))
        elif motif=='roots':
            for x in (3,w-8):
                pygame.draw.lines(surface,(69,69,41),False,[(x,h-5),(x+3,h-23),(x,h-40),(x+4,h-52)],3)
                for j in range(5):
                    y=h-10-j*9
                    pygame.draw.line(surface,(79,99,52),(x+2,y),(x+7,y-6),2)
                    pygame.draw.ellipse(surface,(96,128,63),(x+3,y-8,6,3))
            for x in (15,w-22):
                pygame.draw.rect(surface,(96,81,57),(x,h-13,8,7))
                pygame.draw.line(surface,(30,37,28),(x+3,h-13),(x+5,h-6))
        elif motif=='embers':
            for x in (5,w-14):
                pygame.draw.rect(surface,(21,19,22),(x,h-26,9,20))
                pygame.draw.rect(surface,(99,73,59),(x,h-26,9,20),1)
                for j in range(3):
                    pygame.draw.line(surface,(168,94,46),(x+2,h-22+j*5),(x+6,h-22+j*5))
            pygame.draw.polygon(surface,(104,106,113),[(w//2-10,h-13),(w//2+10,h-13),(w//2+5,h-8),(w//2-5,h-8)])
            pygame.draw.rect(surface,(66,68,76),(w//2-3,h-8,6,5))
        elif motif=='theatre':
            # Torn velvet curtains and empty picture frames, no occult imagery.
            for x in (3,w-13):
                for j in range(4):
                    pygame.draw.rect(surface,(73+j*8,34,42),(x+j*2,4,2,25-j%2*6))
            for x in (w//2-18,w//2+6):
                pygame.draw.rect(surface,(132,104,70),(x,4,12,15),2)
                pygame.draw.rect(surface,(15,18,24),(x+2,6,8,11))
                pygame.draw.ellipse(surface,(54,53,59),(x+5,8,3,4))
                pygame.draw.line(surface,(64,49,45),(x+3,16),(x+9,7))
        elif motif=='ice':
            for x in (5,w-14):
                pygame.draw.rect(surface,(11,23,33),(x,12,9,22))
                for j in range(3): pygame.draw.line(surface,(90,130,151),(x+2+j*3,12),(x+2+j*3,32))
                pygame.draw.polygon(surface,(135,191,209),[(x,10),(x+10,10),(x+6,22),(x+4,14)])
            pygame.draw.lines(surface,(85,124,150),False,[(w//2-12,h-5),(w//2,h-14),(w//2+8,h-10)],1)
        else:
            for x in (3,w-10):
                pygame.draw.rect(surface,(45,66,60),(x,5,7,h-10))
                for y in range(9,h-8,13): pygame.draw.rect(surface,(95,106,78),(x-1,y,9,3))
            for x in (17,w-29):
                pygame.draw.rect(surface,(12,26,25),(x,h-16,12,10))
                for j in range(4): pygame.draw.line(surface,(82,102,80),(x+j*3,h-16),(x+j*3,h-6))

    def active(self, level):
        return level.special_room or level.trial_room

    def draw_floor(self, screen, game):
        for name, rect in self.rooms.items():
            if name in game.level.special_rooms and name != game.level.special_room:
                continue
            pos = game.point((rect.x*self.unit,rect.y*self.unit))
            screen.blit((self.ghost_tiles if game.level.ghost else self.tiles)[name],pos)

    def draw_creatures(self, screen, game):
        """Visual-only inhabitants: no entities, hitboxes, damage or clue logic."""
        name=game.level.trial_room
        if name is None: return
        rect=self.rooms[name]
        w,h=rect.w*self.unit,rect.h*self.unit
        layer=pygame.Surface((w,h),pygame.SRCALPHA)
        t=game.elapsed
        solved=game.level.puzzles.puzzles[name].solved
        alpha=85 if solved else 185
        accent=THEMES[name][2]
        for i in range(2):
            phase=t*.65+i*3.1
            # Independent patrols along the sides, away from puzzle targets.
            x=round(12 if i==0 else w-12)
            y=round(h*.56+math.sin(phase*.55)*h*.13)
            bob=round(math.sin(phase*2)*2)
            pygame.draw.ellipse(layer,(2,6,12,80),(x-10,y+8,20,6))
            if name=='tomb':
                # Hollow-faced shrouds with dragging, breathing fabric.
                outline=[(x-5,y-10+bob),(x,y-15+bob),(x+5,y-10+bob),
                         (x+7,y+10),(x+3,y+7),(x,y+12),(x-3,y+8),(x-7,y+11)]
                pygame.draw.polygon(layer,(85,109,128,alpha),outline)
                pygame.draw.ellipse(layer,(13,24,36,alpha),(x-4,y-10+bob,8,9))
                for dx in (-2,2): pygame.draw.circle(layer,(*accent,alpha),(x+dx,y-7+bob),1)
                for dx in (-4,3):
                    pygame.draw.line(layer,(136,155,163,alpha//2),(x+dx,y),(x+dx+round(math.sin(phase)*2),y+8))
            elif name=='statue':
                # An insect-like root creature unfolds its long jointed legs.
                for side in (-1,1):
                    for leg in range(3):
                        joint=(x+side*(7+round(math.sin(phase+leg)*2)),y-5+leg*5)
                        foot=(x+side*10,y+leg*4+round(math.sin(phase*2+leg)*2))
                        pygame.draw.lines(layer,(111,127,78,alpha),False,[(x,y+leg*2),joint,foot],1)
                pygame.draw.ellipse(layer,(57,78,55,alpha),(x-4,y-7,8,17))
                pygame.draw.ellipse(layer,(104,120,77,alpha),(x-3,y-8+bob,6,7))
                for dx in (-2,2): pygame.draw.circle(layer,(192,211,133,alpha),(x+dx,y-6+bob),1)
            else:
                # A soot-coated foundry prisoner, restrained by slack chains.
                pygame.draw.line(layer,(102,102,108,alpha),(x,0),(x+round(math.sin(phase)*3),y-12),1)
                pygame.draw.polygon(layer,(52,49,53,alpha),[(x-4,y-8+bob),(x+4,y-8+bob),(x+6,y+6),(x-6,y+6)])
                pygame.draw.circle(layer,(110,94,85,alpha),(x,y-10+bob),4)
                pygame.draw.line(layer,(226,153,93,alpha),(x-2,y-10+bob),(x+2,y-10+bob))
                for side in (-1,1):
                    sway=round(math.sin(phase)*3)
                    pygame.draw.lines(layer,(90,81,78,alpha),False,[(x+side*4,y-5),(x+side*8,y+sway),(x+side*6,y+5+sway)],2)
                    pygame.draw.line(layer,(82,75,74,alpha),(x+side*3,y+4),(x+side*5,y+11+bob),2)
        screen.blit(layer,game.point((rect.x*self.unit,rect.y*self.unit)))

    def draw_air(self, screen, game):
        name = self.active(game.level)
        if name is None:
            return
        rect = self.rooms[name]
        _, _, accent, motif = THEMES[name]
        w,h=rect.w*self.unit,rect.h*self.unit
        layer=pygame.Surface((w,h),pygame.SRCALPHA)
        t=game.elapsed
        # Moving low fog, falling ash, bubbles or ice dust, confined to the room.
        for i in range(24):
            x=(i*37+math.sin(t*.4+i)*8)%w
            y=(i*23-t*(8 if motif=='embers' else 3))%h
            alpha=round(45+35*math.sin(t+i)**2)
            if motif in ('bones','roots'):
                pygame.draw.ellipse(layer,(*accent,12),(x-18,y,36,7))
            elif motif == 'water':
                pygame.draw.circle(layer,(*accent,alpha),(round(x),round(y)),2,1)
            else:
                pygame.draw.rect(layer,(*accent,alpha),(round(x),round(y),1,2))
        if motif in ('theatre','ice','embers'):
            for anchor in (12,w-12):
                tip=anchor+round(math.sin(t*.9+anchor)*3)
                pygame.draw.line(layer,(117,132,140,160),(anchor,0),(tip,18),1)
                pygame.draw.ellipse(layer,(133,145,151,150),(tip-2,17,4,5),1)
        if motif=='water':
            for i in range(3):
                radius=1+int((t*4+i*3)%10)
                pygame.draw.ellipse(layer,(*accent,75),(12+i*25-radius,h-19-radius//2,radius*2,radius),1)
        if name in ('tomb','statue','wall'):
            for band in range(3):
                y=round((t*4+band*h/3)%h)
                pygame.draw.ellipse(layer,(*accent,13),(-12,y-5,w+24,12))
            if name=='wall':
                for i in range(10):
                    x=round((i*17+math.sin(t+i)*3)%w)
                    y=round(h-(t*13+i*9)%h)
                    pygame.draw.line(layer,(219,139,79,100),(x,y),(x+1,y+3))
        # Breathing color on the perimeter leaves the center and clues clear.
        for inset in range(6):
            alpha=round((6-inset)*(5+2*math.sin(t*1.3)))
            pygame.draw.rect(layer,(*accent,alpha),(inset,inset,w-2*inset,h-2*inset),1)
        screen.blit(layer,game.point((rect.x*self.unit,rect.y*self.unit)))
