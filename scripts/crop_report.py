#!/usr/bin/env python3
"""Create a local, private visual audit of every automatically cropped photo."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/image-registry.json').read_text())
rows = []
for entry in registry.values():
    if entry['crop'] == [0, 0, *entry['originalSize']]:
        continue
    original = (ROOT / entry['backup']).as_uri()
    current = (ROOT / entry['src']).as_uri()
    title = html.escape(entry['original'])
    crop = html.escape(str(entry['crop']))
    rows.append(f'<section><h2>{title}</h2><p>ID {entry["id"]} · Crop: {crop}</p><div><figure><img loading="lazy" src="{html.escape(original, quote=True)}" alt="Original"><figcaption>Original</figcaption></figure><figure><img loading="lazy" src="{html.escape(current, quote=True)}" alt="Processed"><figcaption>Processed</figcaption></figure></div></section>')
page = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Crop review — Arjun Sarkar</title><style>body{background:#333;color:#eee;font:14px system-ui;margin:40px}section{padding:30px 0;border-top:1px solid #666}h2{font-size:16px}section>div{display:flex;gap:24px}figure{margin:0;width:48%}img{max-width:100%;max-height:420px}figcaption{padding-top:10px}</style><h1>Automatic crop review</h1><p>Originals on the left; processed photographs on the right. Private local report.</p>' + ''.join(rows) + '</html>'
out = ROOT / 'output/crop-review.html'
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f'{len(rows)} cropped photos. Open {out}')
