"""Render the README motion study and its static storyboard."""

import argparse
from functools import cache
from math import atan2, cos, hypot, pi, sin
from pathlib import Path
from subprocess import check_output

from PIL import Image, ImageColor, ImageDraw, ImageFont


WIDTH, HEIGHT, SCALE, FPS = 768, 432, 2, 12


def mix(start, end, amount):
    start, end = ImageColor.getrgb(start), ImageColor.getrgb(end)
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


@cache
def font(family, size):
    path = check_output(["fc-match", "--format=%{file}", family], text=True)
    return ImageFont.truetype(path, round(size * SCALE))


class Canvas:
    def __init__(self, background):
        self.image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), background)
        self.pen = ImageDraw.Draw(self.image)

    @staticmethod
    def coords(xy):
        return tuple(round(value * SCALE) for value in xy)

    def txt(self, value, x, y, size, color, family, anchor="lt"):
        self.pen.text(self.coords((x, y)), value, fill=color, font=font(family, size), anchor=anchor)

    def rule(self, points, color, width=1):
        self.pen.line([self.coords(point) for point in points], fill=color,
                      width=max(1, round(width * SCALE)), joint="curve")

    def rect(self, rect, fill=None, outline=None, width=1, radius=0):
        if radius:
            self.pen.rounded_rectangle(self.coords(rect), round(radius * SCALE), fill=fill,
                                       outline=outline, width=max(1, round(width * SCALE)))
        else:
            self.pen.rectangle(self.coords(rect), fill=fill, outline=outline,
                               width=max(1, round(width * SCALE)))

    def disk(self, x, y, radius, fill=None, outline=None, width=1):
        self.pen.ellipse(self.coords((x-radius, y-radius, x+radius, y+radius)),
                         fill=fill, outline=outline, width=max(1, round(width * SCALE)))

    def arc(self, x, y, radius, start, end, color, width=1):
        self.pen.arc(self.coords((x-radius, y-radius, x+radius, y+radius)), start, end,
                     fill=color, width=max(1, round(width * SCALE)))

    def polygon(self, points, fill):
        self.pen.polygon([self.coords(p) for p in points], fill=fill)

    def arrow(self, start, end, color, width=2, head=8):
        self.rule([start, end], color, width)
        x, y = end
        angle = atan2(y - start[1], x - start[0])
        arms = [(x - head*cos(angle + offset), y - head*sin(angle + offset))
                for offset in (-0.55, 0.55)]
        self.polygon([end, *arms], color)

    def dashed(self, start, end, color, width=1, dash=5, gap=6):
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = hypot(dx, dy)
        for offset in range(0, round(distance), dash + gap):
            stop = min(offset + dash, distance)
            self.rule([(start[0]+dx*offset/distance, start[1]+dy*offset/distance),
                       (start[0]+dx*stop/distance, start[1]+dy*stop/distance)], color, width)

    def finish(self):
        return self.image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def export(frame, length, stills):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    panels = [frame(t) for t in stills]
    storyboard = Image.new("RGB", (WIDTH, len(panels) * HEIGHT + (len(panels)-1)*6), "#24242d")
    for index, panel in enumerate(panels):
        storyboard.paste(panel, (0, index * (HEIGHT + 6)))
    storyboard.save(args.out / "overview.png", optimize=True)

    # Keep a stable palette across frames so text and stationary areas do not shimmer.
    palette = storyboard.quantize(colors=112, method=Image.Quantize.MEDIANCUT)
    frames = [frame(i / FPS).quantize(palette=palette, dither=Image.Dither.NONE)
              for i in range(round(length * FPS))]
    frames[0].save(args.out / "overview.gif", save_all=True, append_images=frames[1:],
                   duration=round(1000/FPS), loop=0, disposal=1, optimize=True)


BG = "#102433"
WIRE = "#254859"
INK = "#e8f1ed"
MUTED = "#b0c8ce"
SEA = "#79e9cd"
GOLD = "#ffd186"
BOLD = "DejaVu Sans:style=Bold"
MONO = "DejaVu Sans Mono:style=Bold"
NORMAL = "DejaVu Sans"
HUB = (232, 269)
SOURCES = [(104, 213), (306, 173), (128, 332)]
LABELS = [(89, 174), (313, 143), (106, 359)]


def frame(t):
    c = Canvas(BG)
    c.txt("RHO OBSERVER", 34, 24, 20, SEA, MONO)
    c.txt("Evidence before a read", 32, 63, 41, INK, BOLD)
    c.rule([(34, 120), (734, 120)], WIRE)

    for radius in (39, 71, 103, 134):
        c.disk(*HUB, radius, outline=WIRE)
    for i in range(36):
        angle = i * pi / 18
        inset = 127 if i % 3 == 0 else 131
        c.rule([(HUB[0] + inset*cos(angle), HUB[1] + inset*sin(angle)),
                (HUB[0] + 134*cos(angle), HUB[1] + 134*sin(angle))], WIRE)
    heading = (23 + 52*t) % 360
    for j in range(3):
        c.arc(*HUB, 134-j*1.5, heading-37+j, heading, mix(WIRE, SEA, 0.35-j*0.10))

    received = [t >= 0.49, t >= 0.89, t >= 4.83]
    proof = t >= 6.19
    arrival = [0.0, 0.32, 4.28]
    for i, (socket, label_xy) in enumerate(zip(SOURCES, LABELS)):
        x, y = socket
        age = t-arrival[i]
        c.dashed(socket, HUB, WIRE, width=2, dash=5, gap=6)
        if 0 <= age < 0.54:
            amount = ease(age / 0.54)
            sx = x + (HUB[0]-x)*amount
            sy = y + (HUB[1]-y)*amount
            c.disk(sx, sy, 6, SEA)
        if received[i]:
            pulse = max(0, 1-(age-0.49)*2.1) * 12
            if pulse > 0:
                c.disk(x, y, 20+pulse, outline=SEA)
            c.disk(x, y, 16, BG, SEA, width=2)
            c.disk(x, y, 6, SEA)
            label = ("A  842", "B  842", "C  841")[i]
            color = INK
        else:
            color = GOLD if i == 2 and t >= 0.9 else MUTED
            c.disk(x, y, 16, BG, color, width=2)
            c.rule([(x-5,y), (x+5,y)], color, 2)
            label = "C  offline" if color == GOLD else f"{'ABC'[i]}  …"
        c.txt(label, *label_xy, 23, color, MONO, "mt" if i != 1 else "lt")

    reticle = SEA if proof else MUTED
    c.disk(*HUB, 29, BG, reticle, width=2)
    c.disk(*HUB, 17, outline=WIRE)
    if proof:
        c.rule([(224,269),(230,275),(242,262)], reticle, 3)
    else:
        c.disk(*HUB, 4, reticle)
    c.rule([(405, 145), (405, 370)], WIRE)

    if not all(received[:2]):
        c.txt("Collecting reports", 431, 194, 29, INK, BOLD)
        c.txt(f"{sum(received)} of 3 covered", 431, 247, 24, MUTED, NORMAL)
    elif not received[2]:
        c.txt("2 of 2 agree", 431, 166, 30, INK, BOLD)
        c.txt("2 of 3 covered", 431, 207, 26, MUTED, NORMAL)
        c.rule([(431, 254), (728, 254)], WIRE)
        c.txt("Anchor withheld", 431, 278, 31, GOLD, BOLD)
        c.txt("A source is offline", 431, 322, 25, MUTED, NORMAL)
    else:
        c.txt("3 of 3 covered", 431, 157, 28, INK, BOLD)
        c.txt("842", 432, 208, 26, INK, MONO)
        c.txt("841", 559, 208, 26, INK, MONO)
        c.arrow((491, 221), (542, 221), SEA if proof else MUTED, 2, 8)
        c.txt("Verified path" if proof else "Checking raw path", 431, 249, 23, MUTED, NORMAL)
        c.txt("Anchor 841" if proof else "Anchor withheld", 431, 295, 35, SEA if proof else GOLD, BOLD)

    c.rule([(34, 392), (734, 392)], WIRE)
    c.txt("GET /v1/read-anchor", 34, 405, 19, MUTED, MONO)
    if all(received[:2]):
        c.txt("HTTP 200" if proof else "HTTP 503", 734, 403, 22,
              SEA if proof else GOLD, MONO, "rt")
    return c.finish()


if __name__ == "__main__":
    export(frame, 9.2, (2.7, 7.8))
