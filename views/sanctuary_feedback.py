"""Impulsions courtes du sanctuaire : lumiere, ondes, particules et sons reverberes."""
from array import array
from dataclasses import dataclass
import math
import random
import pygame
from views.map_theme import ROOM_RECTS, room_at

DURATIONS = {'solved':2.4,'chest':1.1,'key':.9,'door':.85,'clue':.7,
             'transform':.85,'return':.85,'correct':.65,'wrong':.4}
COLORS = {'solved':(231,204,132),'chest':(242,212,147),'key':(242,215,145),
          'clue':(144,221,230),'transform':(151,203,225),'return':(214,212,172),
          'correct':(132,217,199),'wrong':(164,113,116),'door':(192,181,134)}


@dataclass
class Pulse:
    kind: str
    position: tuple
    object_id: str | None
    puzzle_id: str | None
    age: float = 0.0


class SanctuaryFeedback:
    _sound_cache = {}

    def __init__(self):
        self.pulses=[]
        self.freeze_remaining=0.0
        self.slow_remaining=0.0
        self.last_sounds={}
        self.clock=0.0
        self.sounds=self.make_sounds()

    @classmethod
    def make_sounds(cls):
        config=pygame.mixer.get_init()
        if not config or config[1] != -16: return {}
        if config in cls._sound_cache: return cls._sound_cache[config]
        rate,_,channels=config
        sounds={}
        for kind in DURATIONS:
            if kind=='solved': notes=[(0,78,.38,.7),(.20,440,.32,.35),(.29,660,.30,.32),(.39,880,.42,.28),(.62,1100,.48,.16),(.83,1320,.55,.10)]
            elif kind=='chest': notes=[(0,130,.18,.5),(.12,590,.24,.3),(.23,890,.27,.25)]
            elif kind=='key': notes=[(0,740,.22,.45),(.09,1110,.3,.25)]
            elif kind=='door': notes=[(0,95,.35,.55),(.13,190,.3,.25)]
            elif kind=='wrong': notes=[(0,120,.20,.4)]
            else:
                hz={'clue':810,'transform':220,'return':330,'correct':540}[kind]
                notes=[(0,hz,.26,.35),(.09,hz*1.5,.25,.15)]
            duration=max(t+length for t,_,length,_ in notes)+.42
            buffer=[0.0]*int(duration*rate)
            for start,hz,length,volume in notes:
                for delay,gain in [(0,1),(.11,.32),(.24,.16),(.39,.07)]:
                    offset=int((start+delay)*rate)
                    for i in range(int(length*rate)):
                        t=i/rate
                        envelope=min(1,t/.012)*math.exp(-5*t/length)*(1-t/length)
                        wave=math.sin(math.tau*hz*t)+.17*math.sin(math.tau*hz*2.01*t)
                        index=offset+i
                        if index<len(buffer):buffer[index]+=wave*envelope*volume*gain
            samples=array('h')
            for value in buffer:
                sample=round(max(-1,min(1,value)) * 11000)
                samples.extend([sample]*channels)
            sounds[kind]=pygame.mixer.Sound(buffer=samples)
        cls._sound_cache[config]=sounds
        return sounds

    def emit(self,event):
        kind=event['kind']
        self.pulses.append(Pulse(kind,event['position'],event['object_id'],event['puzzle_id']))
        # Plusieurs indices decouverts ensemble ne multiplient pas le volume.
        if self.clock-self.last_sounds.get(kind,-10)>.10:
            if kind in self.sounds:self.sounds[kind].play()
            self.last_sounds[kind]=self.clock
        if kind=='solved':
            self.freeze_remaining=.065
            self.slow_remaining=.24

    def advance(self,dt):
        self.clock+=dt
        for pulse in self.pulses:pulse.age+=dt
        self.pulses=[p for p in self.pulses if p.age<DURATIONS.get(p.kind,.7)]
        frozen=min(dt,self.freeze_remaining)
        self.freeze_remaining=max(0,self.freeze_remaining-dt)
        remaining=dt-frozen
        slow=min(remaining,self.slow_remaining)
        self.slow_remaining=max(0,self.slow_remaining-remaining)
        return remaining-slow*.65

    def age(self,kind,object_id=None,puzzle_id=None):
        for pulse in reversed(self.pulses):
            if pulse.kind==kind and (object_id is None or pulse.object_id==object_id) and (puzzle_id is None or pulse.puzzle_id==puzzle_id):
                return pulse.age
        return None

    def shake(self):
        strength=max((2.0*(1-p.age/.35) for p in self.pulses if p.kind in ('solved','door','wrong') and p.age<.35),default=0)
        return math.sin(self.clock*83)*strength,math.cos(self.clock*71)*strength*.5

    def draw(self,screen,game):
        layer=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        self.draw_constellations(layer,game)
        for pulse in self.pulses:
            duration=DURATIONS.get(pulse.kind,.7)
            progress=pulse.age/duration
            color=COLORS.get(pulse.kind,(192,204,213))
            x,y=game.point(pulse.position)
            if pulse.kind=='solved':
                self.draw_ritual(layer,game,pulse,color)
                room=ROOM_RECTS.get(room_at(*pulse.position))
                if room:
                    left,top=game.point(room.topleft)
                    alpha=round(55*math.sin(math.pi*min(1,progress*2)))*(1 if progress<.5 else 0)
                    pygame.draw.rect(layer,(*color,max(0,alpha)),(left,top,room.w,room.h))
                radius=int(8+100*progress)
                pygame.draw.circle(layer,(*color,int(190*(1-progress))),(x,y),radius,2)
                pygame.draw.circle(layer,(*color,int(85*(1-progress))),(x,y),max(1,radius-6),1)
            else:
                radius=int(4+24*progress)
                pygame.draw.circle(layer,(*color,int(160*(1-progress))),(x,y),radius,1)
            count=64 if pulse.kind=='solved' else (38 if pulse.kind=='chest' else 14)
            rng=random.Random(pulse.object_id or pulse.puzzle_id or pulse.kind)
            for i in range(count):
                angle=rng.uniform(0,math.tau)
                speed=rng.uniform(12,48)
                distance=speed*pulse.age
                px=x+math.cos(angle)*distance
                py=y+math.sin(angle)*distance*.6-18*pulse.age
                pygame.draw.rect(layer,(*color,int(220*(1-progress))),(round(px),round(py),2 if i%4==0 else 1,2))
        screen.blit(layer,(0,0))

    def draw_constellations(self,layer,game):
        objects={o.id:o for o in game.level.objects}
        for puzzle in game.level.puzzles.puzzles.values():
            if not puzzle.current_sequence or puzzle.solved:continue
            points=[game.point(game.level.center(objects[oid].cell)) for oid in puzzle.current_sequence]
            color=(125,224,210)
            for i,point in enumerate(points):
                radius=8+round(2*math.sin(self.clock*3+i))
                pygame.draw.circle(layer,(*color,110),point,radius,1)
                angle=self.clock*2+i
                spark=(round(point[0]+math.cos(angle)*radius),round(point[1]+math.sin(angle)*radius))
                pygame.draw.circle(layer,(*color,230),spark,1)
                if i:
                    previous=pygame.Vector2(points[i-1]);end=pygame.Vector2(point)
                    pygame.draw.line(layer,(*color,75),previous,end,1)
                    travel=(self.clock*.9+i*.17)%1
                    pos=previous.lerp(end,travel)
                    pygame.draw.circle(layer,(*color,230),(round(pos.x),round(pos.y)),2)

    def draw_ritual(self,layer,game,pulse,color):
        chest=next((o for o in game.level.objects if o.type=='chest' and o.puzzle_id==pulse.puzzle_id),None)
        anchor=game.level.center(chest.cell) if chest else pulse.position
        x,y=game.point(anchor)
        age=pulse.age
        envelope=min(1,age/.22)*max(0,1-age/2.4)
        # Deux anneaux contrarotatifs, graves de petits sigils geometriques.
        for ring,base in enumerate((23,37)):
            radius=base*min(1,.25+age*2)
            pygame.draw.ellipse(layer,(*color,round(150*envelope)),(round(x-radius),round(y-radius*.48),round(radius*2),round(radius*.96)),1)
            for i in range(10):
                angle=i*math.tau/10+age*(.6 if ring==0 else -.4)
                px=x+math.cos(angle)*radius;py=y+math.sin(angle)*radius*.48
                pygame.draw.lines(layer,(*color,round(230*envelope)),False,[(round(px-2),round(py+2)),(round(px),round(py-3)),(round(px+2),round(py+2))],1)
        # Colonne de lumiere en expansion puis dissolution.
        height=round(105*min(1,age*2.8))
        for width,alpha in ((24,16),(12,26),(4,72)):
            pygame.draw.polygon(layer,(*color,round(alpha*envelope)),[(x-width//2,y),(x-width,y-height),(x+width,y-height),(x+width//2,y)])
        for i in range(28):
            phase=(age*.65+i/28)%1
            angle=i*2.4+age*2
            radius=19*(1-phase)
            pos=(round(x+math.cos(angle)*radius),round(y-phase*90))
            pygame.draw.rect(layer,(*color,round(220*envelope)),(*pos,2,2))
        puzzle=game.level.puzzles.puzzles.get(pulse.puzzle_id)
        if puzzle:
            objects={o.id:o for o in game.level.objects}
            for i,oid in enumerate(puzzle.solution):
                start=game.point(game.level.center(objects[oid].cell))
                progress=max(0,min(1,(age-i*.045)/.55))
                if 0<progress<1:
                    point=pygame.Vector2(start).lerp((x,y),progress)
                    pygame.draw.line(layer,(*color,100),start,point,1)
                    pygame.draw.circle(layer,(*color,230),(round(point.x),round(point.y)),2)
