"""Animated escape finale, rendered through the game's crisp text pipeline."""
import math
import pygame
from settings import TITLE_FONT_FILE


class SanctuaryVictory:
    def __init__(self):
        self.started = None
        self.title_font = None

    def draw(self, screen, game):
        if self.started is None:
            self.started = game.elapsed
        if self.title_font is None:
            self.title_font = pygame.font.Font(str(TITLE_FONT_FILE), 25)
            game._font_specs[id(self.title_font)] = (TITLE_FONT_FILE, 25)
        age=max(0,game.elapsed-self.started)
        w,h=screen.get_size()
        cx,cy=w//2,h//2
        game._text_commands.clear()
        game._veil=(None,0)
        screen.set_clip(None)
        screen.fill((7,12,20))
        # A monumental door slowly parts onto dawn. The darkness stays behind.
        opening=min(1,age/2.6)
        opening=opening*opening*(3-2*opening)
        arch=pygame.Rect(cx-54,37,108,h-100)
        for i in range(12,0,-1):
            glow=pygame.Surface((w,h),pygame.SRCALPHA)
            pygame.draw.rect(glow,(143,166,171,3),arch.inflate(i*12,i*4),border_radius=38)
            screen.blit(glow,(0,0))
        pygame.draw.rect(screen,(69,87,100),arch.inflate(16,12),border_radius=40)
        pygame.draw.rect(screen,(16,27,39),arch.inflate(8,6),border_radius=37)
        pygame.draw.rect(screen,(195,194,160),arch,border_radius=34)
        for row in range(arch.top+32,arch.bottom,16):
            shade=round(160+60*(row-arch.top)/arch.h)
            pygame.draw.rect(screen,(shade,min(225,shade+5),min(205,shade-12)),(arch.x+3,row,arch.w-6,16))
        leaf=round(arch.w/2*(1-opening))
        for x in (arch.left,arch.right-leaf):
            if leaf:
                pygame.draw.rect(screen,(28,36,46),(x,arch.top,leaf,arch.h),border_radius=4)
                for offset in (22,arch.h-30):
                    pygame.draw.rect(screen,(101,100,86),(x,arch.top+offset,leaf,4))
        # Long perspective shadows and wandering flecks replace a static panel.
        floor=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.polygon(floor,(198,187,143,round(42*opening)),[(cx-35,arch.bottom),(cx+35,arch.bottom),(cx+170,h),(cx-170,h)])
        screen.blit(floor,(0,0))
        for i in range(48):
            x=round((i*67+math.sin(age*.4+i)*13)%w)
            y=round((i*41-age*(5+i%4))%h)
            color=(116+i%5*17,120+i%4*16,106+i%3*20)
            pygame.draw.rect(screen,color,(x,y,1,2))
        # One small survivor at the threshold gives the architecture its scale.
        sy=arch.bottom-8-round(min(1,age/4)*10)
        pygame.draw.ellipse(screen,(19,26,33),(cx-9,sy+12,18,5))
        pygame.draw.polygon(screen,(31,40,51),[(cx,sy-9),(cx-7,sy+12),(cx+7,sy+12)])
        pygame.draw.circle(screen,(49,57,63),(cx,sy-10),4)
        # Cinematic bars carry readable text above every decorative effect.
        shade=pygame.Surface((w,100),pygame.SRCALPHA);shade.fill((5,10,17,224))
        screen.blit(shade,(0,0))
        screen.blit(shade,(0,h-94))
        pygame.draw.line(screen,(125,119,87),(30,99),(w-30,99))
        game.label(screen,'LE SANCTUAIRE VOUS A LAISSE SORTIR',(cx,13),(154,166,174),game.small,align='center')
        title='VOUS AVEZ SURVECU' if age>.7 else 'LA PORTE S\'OUVRE'
        game.label(screen,title,(cx,36),(235,217,157),self.title_font,align='center')
        game.label(screen,'Mais quelque chose se souvient de vous.',(cx,77),(186,197,201),game.small,align='center')
        solved=sum(p.solved for p in game.level.puzzles.puzzles.values())
        duration=int(game.level.time)
        game.label(screen,f'{solved} EPREUVES SURMONTEES   /   {duration//60:02d}:{duration%60:02d}',(cx,h-77),(217,206,165),game.font,align='center')
        game.label(screen,'Vous connaissez les lieux. Leurs secrets ont deja change.',(cx,h-52),(157,174,184),game.small,align='center')
        game.label(screen,'N : nouvelle partie     Echap : menu',(cx,h-28),(231,230,215),game.font,align='center')
