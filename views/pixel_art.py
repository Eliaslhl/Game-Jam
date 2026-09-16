"""Petits sprites ASCII et tuiles dessinees en pixels, inspires de GAUNTLET."""
import random
import pygame

PALETTE = {'.':(0,0,0,0), 'o':(24,28,37), 'w':(237,224,191), 's':(171,143,122),
           'b':(81,137,154), 'B':(45,75,95), 'g':(133,171,122), 'G':(47,93,72),
           'y':(248,208,101), 'Y':(164,113,45), 'p':(184,127,238), 'P':(96,51,147),
           'r':(216,102,93), 'R':(107,52,62), 'c':(139,234,226), 'C':(55,121,137)}
ART = {
'player': [
    ".....o.....",
    "....oPo....",
    "...oPpPo...",
    "..oPPPpPo..",
    ".oPwPPPwPo.",
    "ooooooooooo",
    ".oosssssoo.",
    "..oswwwso..",
    "..oPwwwPo..",
    ".oPPPyPPPo.",
    ".oPPPPPPPo.",
    ".o.o.o.o.o.",
],
'key': ['..yyyy...', '.yy..yy..', '.yy..yy..', '..yyyy...', '....yy...', '....yy...', '....yyy..', '....yy...', '....yyy..'],
'potion': ['...ww...', '...ss...', '...ww...', '..wppw..', '.wppppw.', '.wppppw.', '.wPPPPw.', '..wwww..'],
'stele': ['...oooo...', '..osssso..', '.oswwssso.', '.ossswsso.', '.oswwwsso.', '.ossswsso.', '.osssssso.', '.osssssso.', 'oBBBBBBBBo'],
'book': ['.YYYYYYYY.', 'YwwwwwwwwY', 'YwwYwwwYwY', 'YwwYwwwYwY', 'YYYYYYYYYY'],
'bones': ['.ww....w..', 'www...ww..', '.w..ww....', '...ww..w..', '..w...www.', '.......w..'],
'plant': ['....g.....', '.g..G..g..', '..g.G.g...', '...gGg....', '....G.....', '...YYY....', '...YYY....'],
}


def ascii_sprite(name):
    rows=ART[name]
    image=pygame.Surface((max(map(len,rows)),len(rows)), pygame.SRCALPHA)
    for y,row in enumerate(rows):
        for x,char in enumerate(row):
            image.set_at((x,y),PALETTE[char])
    return image


class PixelTiles:
    def __init__(self, level, decorate=True):
        self.level=level
        self.art={name:ascii_sprite(name) for name in ART}
        self.surface=pygame.Surface((level.width*16,level.height*16))
        self.surface.fill((9,13,20))
        self.torches=[]
        for y,row in enumerate(level.grid):
            for x,tile in enumerate(row):
                rng=random.Random(y*771+x*33)
                rect=pygame.Rect(x*16,y*16,16,16)
                if tile=='#':
                    if not any(level.tile(x+dx,y+dy)!='#' for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]):
                        continue
                    self.wall(rect,rng)
                    if level.tile(x,y+1) not in '#Y' and (x*3+y)%9==0:
                        self.torches.append((x*16+8,y*16+12))
                else:
                    variation=rng.randrange(7)
                    base=(30+variation,39+variation,58+variation)
                    pygame.draw.rect(self.surface,base,rect)
                    pygame.draw.line(self.surface,(20,27,42),rect.topleft,rect.topright)
                    pygame.draw.line(self.surface,(21,28,44),rect.topleft,rect.bottomleft)
                    pygame.draw.line(self.surface,(46,58,80),(rect.x+2,rect.y+14),(rect.x+12,rect.y+14))
                    if rng.random()<.13:
                        pygame.draw.line(self.surface,(22,30,48),(rect.x+5,rect.y+2),(rect.x+8,rect.y+7))
                    if decorate and tile=='.' and rng.random()<.08:
                        name='plant' if y>26 and x<23 else ('book' if x<23 and y<16 else 'bones')
                        self.surface.blit(self.art[name],(rect.x+3,rect.y+4))
        if decorate:
            # Torches placees a la main aux entrees : reperes visibles depuis les galeries.
            for cell in [(26,16),(30,16),(34,16),(2,12),(11,2),(18,2),
                         (40,2),(48,2),(56,2),(13,26),(18,26),(42,28),(49,28),(56,28)]:
                point=(cell[0]*16+8,cell[1]*16+12)
                if point not in self.torches:
                    self.torches.append(point)
            # Une mosaique au centre du sanctuaire.
            for radius in (26,30):
                pygame.draw.circle(self.surface,(61,79,80),(488,344),radius,1)
            for dx,dy in [(0,23),(0,-23),(23,0),(-23,0)]:
                pygame.draw.rect(self.surface,(123,143,129),(486+dx,342+dy,4,4),1)

    def wall(self,rect,rng):
        x,y=rect.topleft
        shade=rng.randrange(-6,7)
        pygame.draw.rect(self.surface,(70+shade,82+shade,112+shade),(x,y,15,15))
        pygame.draw.line(self.surface,(112+shade,126+shade,156+shade),(x+1,y),(x+13,y))
        pygame.draw.line(self.surface,(92,104,132),(x,y+1),(x,y+12))
        pygame.draw.line(self.surface,(26,32,52),(x+1,y+14),(x+14,y+14))
        pygame.draw.line(self.surface,(38,46,68),(x+14,y+1),(x+14,y+14))
        if rng.random()<.4:
            pygame.draw.lines(self.surface,(42,50,72),False,[(x+9,y+2),(x+6,y+6),(x+8,y+9)])
        if rng.random()<.24:
            for _ in range(5):
                pygame.draw.rect(self.surface,rng.choice([(53,76,62),(66,83,64)]),(x+rng.randrange(2,13),y+rng.randrange(8,15),2,2))
