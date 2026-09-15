import os
from PIL import Image, ImageDraw

OUTPUT_DIR = "assets/images/decor"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_sprite(filename, draw_func, size=(32, 32)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, size)
    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    print(f"Asset généré : {path}")

def draw_lever_off(draw, s):
    draw.rectangle([8, 22, 24, 28], fill=(100, 100, 100, 255))
    draw.line([(16, 22), (8, 10)], fill=(180, 180, 180, 255), width=3)
    draw.ellipse([5, 7, 11, 13], fill=(220, 50, 50, 255))

def draw_lever_on(draw, s):
    draw.rectangle([8, 22, 24, 28], fill=(100, 100, 100, 255))
    draw.line([(16, 22), (24, 10)], fill=(180, 180, 180, 255), width=3)
    draw.ellipse([21, 7, 27, 13], fill=(50, 220, 50, 255))

def draw_door_closed(draw, s):
    draw.rectangle([4, 2, 28, 30], fill=(120, 70, 30, 255))
    draw.rectangle([6, 4, 26, 28], fill=(90, 50, 20, 255))
    draw.ellipse([21, 15, 24, 18], fill=(220, 180, 50, 255))

def draw_door_open(draw, s):
    draw.rectangle([4, 2, 28, 30], fill=(40, 40, 40, 255))
    draw.rectangle([4, 2, 8, 30], fill=(120, 70, 30, 255))
    draw.rectangle([24, 2, 28, 30], fill=(120, 70, 30, 255))

def draw_pad_off(draw, s):
    draw.rectangle([4, 8, 28, 24], fill=(80, 80, 90, 255))
    draw.rectangle([8, 12, 24, 20], fill=(180, 60, 60, 255))

def draw_pad_on(draw, s):
    draw.rectangle([4, 8, 28, 24], fill=(80, 80, 90, 255))
    draw.rectangle([8, 12, 24, 20], fill=(60, 180, 60, 255))

def draw_digicode(draw, s):
    draw.rectangle([6, 4, 26, 28], fill=(50, 50, 60, 255))
    draw.rectangle([9, 7, 23, 12], fill=(100, 220, 100, 255))
    for x in [9, 14, 19]:
        for y in [15, 19, 23]:
            draw.rectangle([x, y, x+3, y+2], fill=(200, 200, 200, 255))

def draw_clue(draw, s):
    draw.rectangle([6, 6, 26, 26], fill=(40, 180, 220, 150))
    draw.text((10, 8), "4 8", fill=(255, 255, 255, 240))
    draw.text((10, 16), "1 2", fill=(255, 255, 255, 240))

create_sprite("lever_off.png", draw_lever_off)
create_sprite("lever_on.png", draw_lever_on)
create_sprite("door_closed.png", draw_door_closed)
create_sprite("door_open.png", draw_door_open)
create_sprite("pressure_pad_off.png", draw_pad_off)
create_sprite("pressure_pad_on.png", draw_pad_on)
create_sprite("digicode.png", draw_digicode)
create_sprite("spectral_clue.png", draw_clue)