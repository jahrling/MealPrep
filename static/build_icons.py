#!/usr/bin/env python3
"""Render icon.svg into the PNG sizes the web-app manifest and iOS need.
Needs cairosvg (dev-time only; the PNGs are committed):
  python3 -m venv /tmp/v && /tmp/v/bin/pip install cairosvg && /tmp/v/bin/python static/build_icons.py
"""
import os
import re
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
svg = open(os.path.join(HERE, 'icon.svg'), encoding='utf-8').read()

# Maskable variant: keep the background full-bleed, shrink the artwork into
# the central 80% "safe zone" so Android's adaptive-icon masks can't clip it.
m = re.search(r'(</defs>\s*<rect[^>]*/>)(.*)</svg>', svg, re.S)
maskable = svg[:m.start()] + m.group(1) + \
    '<g transform="translate(51.2 51.2) scale(.8)">' + m.group(2) + '</g></svg>'

for name, source, size in [
    ('icon-512.png', svg, 512),
    ('icon-192.png', svg, 192),
    ('icon-maskable-512.png', maskable, 512),
    ('apple-touch-icon.png', svg, 180),
    ('favicon-32.png', svg, 32),
]:
    cairosvg.svg2png(bytestring=source.encode(), write_to=os.path.join(HERE, name),
                     output_width=size, output_height=size)
    print('wrote', name)
