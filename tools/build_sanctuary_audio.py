"""Original procedural score. Run once to rebuild the shipped stereo WAV assets.

No downloads, third-party samples or extra dependencies. Never runs in gameplay.
"""
from array import array
import math
from pathlib import Path
import random
import sys
import wave

RATE = 22050
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'sounds' / 'sanctuary'
TAU = math.tau


def save(name, data, peak=.78, loop=False):
    # Stereo reflections: circular for seamless beds, trailing silence for hits.
    delay = int(.173 * RATE)
    if not loop:
        data.extend([0.] * int(.7 * RATE))
    # Two high-pass stages remove the room rumble from every generated layer.
    # The existing medieval music lives outside this folder and is untouched.
    alpha = 1 / (1 + TAU * 240 / RATE)
    for stage in range(2):
        previous_input = previous_output = 0.
        for lap in range(2 if loop else 1):
            filtered=[]
            for value in data:
                previous_output=alpha*(previous_output+value-previous_input)
                previous_input=value
                filtered.append(previous_output)
        data=filtered
    # Soften noise and metallic upper harmonics, keeping distant details warm.
    coefficient = 1 - math.exp(-TAU * 2300 / RATE)
    previous = 0.
    for lap in range(2 if loop else 1):
        softened=[]
        for value in data:
            previous += coefficient*(value-previous)
            softened.append(previous)
    data=softened
    maximum = max(max(abs(v) for v in data), .001)
    pcm = array('h')
    for i, value in enumerate(data):
        reflected = data[(i-delay) % len(data)] if loop or i >= delay else 0
        left = (value + .22 * reflected) / maximum * peak / 1.22
        right = (.88 * value + .32 * reflected) / maximum * peak / 1.22
        pcm.extend((round(left*32767), round(right*32767)))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(OUT / (name + '.wav')), 'wb') as wav:
        wav.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
        wav.writeframes(pcm.tobytes())


def bed(name, root, shimmer):
    duration = 8
    data = []
    # All oscillators complete whole cycles: no click at the loop boundary.
    frequencies = [round(root * ratio * duration) / duration for ratio in (1, 1.5, 2, 2.004, 3)]
    for i in range(RATE * duration):
        t = i / RATE
        swell = .65 + .22 * math.sin(TAU*t/duration)
        # Thin bowed harmonics and air: no bass oscillator or rhythmic drone.
        value = sum(math.sin(TAU*f*8*t + .22*math.sin(TAU*t/duration))*amp
                    for f,amp in zip(frequencies,(.14,.07,.03,.035,.012)))*swell
        value += shimmer*math.sin(TAU*frequencies[0]*12*t)*(.5+.5*math.cos(TAU*t/2))**12
        data.append(value)
    save(name, data, peak=.48, loop=True)


def effect(name, notes=(), impact=0, sweep=0, length=2):
    rng = random.Random(name)
    data = [0.] * int(length*RATE)
    low = 0
    for i in range(len(data)):
        t = i/RATE
        noise = rng.uniform(-1, 1)
        low += .08*(noise-low)
        attack = min(1, t/.006)
        data[i] = impact * attack * (math.sin(TAU*(72*t+15*(1-math.exp(-12*t))))*math.exp(-6*t)
                                    + .65*low*math.exp(-3*t)+.20*noise*math.exp(-24*t))
        if sweep:
            env = math.sin(math.pi*min(1,t/length))**2
            data[i] += sweep*env*(.12*noise+.22*math.sin(TAU*(150*t+210*t*t)))
    for start, hz, gain, decay in notes:
        for echo, attenuation in ((0, 1), (.13, .32), (.29, .17), (.47, .08)):
            offset = int((start+echo)*RATE)
            for i in range(max(0, len(data)-offset)):
                t=i/RATE
                env=min(1,t/.012)*math.exp(-decay*t)
                tone=math.sin(TAU*hz*t)+.25*math.sin(TAU*hz*2.003*t)+.09*math.sin(TAU*hz*3.97*t)
                data[offset+i] += gain*attenuation*env*tone
    # Smooth the tail, including the long resonances.
    for i in range(min(len(data), int(.1*RATE))):
        data[-i-1] *= i/(.1*RATE)
    save(name, data)


def haunting(name, kind):
    """Breathy formants, bowed metal and distant drips, with long echoes."""
    rng=random.Random(name)
    duration=3.2
    data=[]
    low=0.
    for i in range(int(RATE*duration)):
        t=i/RATE
        noise=rng.uniform(-1,1)
        low += .12*(noise-low)
        env=math.sin(math.pi*t/duration)**2
        if kind == 'whisper':
            root=370
            breath=(noise-low)*(.5+.5*math.sin(TAU*3*t))
            value=env*(.12*breath+sum(.13/n*math.sin(TAU*(root*n*t+.07*math.sin(TAU*.7*t))) for n in (1,2,3,5)))
        elif kind in ('chains','ice'):
            value=0.
            for start in (0,.31,.9,1.7):
                age=t-start
                if age>=0:
                    root=310 if kind=='chains' else 960
                    value += min(1,age/.008)*math.exp(-4*age)*sum(.16*math.sin(TAU*root*r*age) for r in (1,1.43,2.71))
        elif kind=='drip':
            value=0.
            for start in (0,.47,1.45):
                age=t-start
                if age>=0:
                    value += .5*min(1,age/.004)*math.exp(-13*age)*math.sin(TAU*(780*age+40*(1-math.exp(-18*age))))
        else:
            value=env*(low*.9+.14*math.sin(TAU*(340*t+32*t*t)))*(.6+.4*math.sin(TAU*7*t))
        data.append(value*min(1,(duration-t)/.12))
    original=data[:]
    for delay,gain in ((.23,.33),(.51,.18),(.83,.09)):
        offset=int(delay*RATE)
        for i in range(offset,len(data)):
            data[i]+=original[i-offset]*gain
    save(name,data,peak=.65)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, root, shimmer in [('tomb', 55, .045), ('statue', 73.416, .075),
                                 ('wall', 46.25, .025), ('statues_sp', 82.407, .12),
                                 ('path_sp', 65.406, .10), ('gold', 98, .16),
                                 ('spectral', 110, .10)]:
        bed('amb_'+name, root, shimmer)
    effect('enter', [(0, 110, .25, 3), (.18, 164.81, .15, 2)], impact=.7, sweep=.15)
    effect('solved', [(t, f, .3, 2) for t,f in [(0.08,220),(.18,329.63),(.3,440),(.44,659.25),(.62,880),(.84,1108.73)]], impact=1, length=3.5)
    effect('chest', [( .12,440,.3,3),(.26,659.25,.25,3),(.4,880,.2,2)], impact=.55)
    effect('key', [(0,880,.3,4),(.10,1318.51,.2,3),(.22,1760,.12,3)])
    effect('door', [(0,55,.25,4),(.12,82.4,.2,4)], impact=1, length=1.5)
    effect('stone', [(0,62,.2,7)], impact=1, length=1)
    effect('wrong', [(0,110,.3,7),(0,116.54,.22,7)], impact=.5, length=.9)
    effect('clue', [(0,659.25,.25,3),(.16,987.77,.16,3)], sweep=.12)
    effect('transform', [(0,110,.25,2),(.3,220,.22,2),(.5,440,.14,2)], sweep=.5)
    effect('return', [(0,440,.15,4),(.10,220,.22,3),(.2,110,.3,4)], impact=.6)
    for n, hz in enumerate((329.63,392,440,523.25,659.25)):
        effect('correct_'+str(n), [(0,hz,.35,5),(.08,hz*2,.12,5)], impact=.15, length=.9)
    effect('heartbeat', [(0,920,.25,38),(.18,740,.2,40)], length=.5)
    effect('step', [(0,130,.1,45)], impact=.3, length=.15)
    for kind in ('whisper','roots','chains','wood','ice','drip'):
        haunting('haunt_'+kind,kind)
    effect('stone_slide', [(0,370,.18,7),(.13,440,.12,9)], sweep=.35, length=.7)
    for n,hz in enumerate((587.33,659.25,783.99,880,1174.66)):
        effect('path_'+str(n), [(0,hz,.28,8),(.07,hz*1.5,.12,9)], length=.65)
    obsolete=OUT/'haunt_choir.wav'
    if obsolete.exists(): obsolete.unlink()
    print('Built', len(list(OUT.glob('*.wav'))), 'original stereo sounds in', OUT)


if __name__ == '__main__':
    main()
