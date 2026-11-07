"""Textures for VIDEO_003 props (cardboard sign, phone screen).  python3 VIDEOS/VIDEO_003/gfx/make_gfx.py"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, '..', '..', '..', 'ASSETS', 'fonts', 'Montserrat-800.ttf')
# cardboard sign, marker handwriting look
im = Image.new('RGB', (1024, 700), (196, 150, 98))
d = ImageDraw.Draw(im)
for i in range(0, 1024, 23):
    d.line([(i, 0), (i, 700)], fill=(186, 141, 90), width=6)
f = ImageFont.truetype(F, 120)
for k, line in enumerate(('WILL SELL', 'OREGANO', '4 FOOD')):
    w = d.textlength(line, font=f)
    d.text(((1024 - w) / 2 + (k - 1) * 14, 70 + k * 190), line, font=f, fill=(25, 22, 30))
im.filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(HERE, 'sign.png'))
# phone screen: a vertical video feed (hearts, play, progress) in loud colours
im = Image.new('RGB', (540, 1080), (255, 60, 150))
d = ImageDraw.Draw(im)
for y in range(1080):
    t = y / 1080
    d.line([(0, y), (540, y)], fill=(int(255 - 120 * t), int(60 + 40 * t), int(150 + 100 * t)))
d.polygon([(200, 420), (200, 660), (380, 540)], fill=(255, 255, 255))
for i, y in enumerate((620, 740, 860)):
    d.ellipse((450, y, 510, y + 60), fill=(255, 255, 255))
d.rectangle((0, 1040, 540, 1056), fill=(255, 255, 255))
d.rectangle((0, 1040, 380, 1056), fill=(255, 220, 60))
im.save(os.path.join(HERE, 'phone_screen.png'))
print('GFX_OK')
