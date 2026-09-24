# -*- coding: utf-8 -*-
"""Build out/report.html: self-contained (all figures base64-inline, no external CSS/JS/fonts).
Run from the job directory AFTER work/build_all.py and out/checks.py:
    python work/build_report.py
Inputs: out/provenance.json, work/fig/*.png, work/checks_output.txt, work/report_content.py
"""
import base64
import datetime as dt
import html
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import report_content as rc  # noqa: E402

P = json.load(open(os.path.join(JOB, "out", "provenance.json"), encoding="utf-8"))

# checks output: run checks.py fresh so the pasted text is what the reader can reproduce
r = subprocess.run([sys.executable, os.path.join(JOB, "out", "checks.py")], capture_output=True, text=True, encoding="utf-8", cwd=JOB)
checks_txt = r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
checks_rc = r.returncode
open(os.path.join(HERE, "checks_output.txt"), "w", encoding="utf-8").write(checks_txt)
if checks_rc != 0:
    print(checks_txt[-2000:]); sys.exit(f"out/checks.py exited {checks_rc}; report not written")


def img(name):
    path = os.path.join(HERE, "fig", name)
    b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")
    cap = rc.FIG_CAPTIONS.get(name, name)
    return f'<figure><img src="data:image/png;base64,{b64}" alt="{html.escape(name)}"><figcaption>{html.escape(cap)}</figcaption></figure>'


CSS = """
body{font-family:Georgia,'Times New Roman',serif;max-width:960px;margin:2em auto;padding:0 1.5em;line-height:1.5;color:#1c1c1c;background:#fff}
h1{font-size:1.6em;margin-bottom:.2em} h2{font-size:1.25em;border-bottom:1px solid #999;padding-bottom:.2em;margin-top:2em} h3{font-size:1.05em;margin-top:1.4em}
.sub{color:#555;font-size:.95em} code{font-family:Consolas,Menlo,monospace;font-size:.9em;background:#f3f3f3;padding:0 .2em}
sup.src{color:#999;font-family:Consolas,Menlo,monospace;font-size:.6em;margin-left:1px} .missing{color:#c00;font-weight:bold}
table{border-collapse:collapse;margin:.8em 0;font-size:.92em} th,td{border:1px solid #bbb;padding:.25em .6em;text-align:center} th{background:#f0f0f0}
figure{margin:1.2em 0;text-align:center} figure img{max-width:100%;border:1px solid #ddd} figcaption{font-size:.88em;color:#444;margin-top:.3em;text-align:left}
.eq{font-family:'Times New Roman',serif;font-style:italic;text-align:center;margin:.8em 0;padding:.5em;background:#fafafa;border-left:3px solid #ccc}
pre{background:#f7f7f7;border:1px solid #ddd;padding:.8em;font-size:.78em;overflow-x:auto;white-space:pre-wrap} .ok{color:#137a3a} .bad{color:#b00}
nav ol{columns:2;font-size:.92em} .box{border:1px solid #c9c9c9;background:#fbfbf6;padding:.6em 1em;margin:1em 0}
details summary{cursor:pointer;font-weight:bold} .prov td{text-align:left;font-size:.8em;font-family:Consolas,Menlo,monospace}
"""

secs = rc.sections(P)
missing = []
parts = []
parts.append(f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Efecto Leidenfrost — cilindros de Cu en N₂ líquido</title><style>{CSS}</style></head><body>
<h1>Efecto Leidenfrost en cilindros de cobre sumergidos en nitrógeno líquido</h1>
<p class="sub">Reproducción desde cero a partir de <code>datos/</code>, <code>guia/</code> y las dimensiones medidas por el humano — job
<code>2026-09-18_205159</code>, ronda 2, generado {dt.date.today().isoformat()}. Autocontenido: abre con <code>file://</code>, sin red.
Registro de cada número: <code>out/provenance.json</code>. Notebook interactivo con los mismos contenidos y parámetros libres: <code>out/report.py</code> (marimo).</p>
<div class="box"><strong>Fence:</strong> nadie del equipo leyó, listó ni buscó nada bajo <code>informe-original/</code>.
<strong>Checks:</strong> <code>python out/checks.py</code> → <span class="{'ok' if checks_rc == 0 else 'bad'}">{'exit 0' if checks_rc == 0 else 'exit ' + str(checks_rc)}</span>,
{html.escape([l for l in checks_txt.splitlines() if l.startswith('checks:')][0] if any(l.startswith('checks:') for l in checks_txt.splitlines()) else '(sin resumen)')}
(salida completa en §9).</div>
<nav><ol>""" + "".join(f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for s in secs) +
              '<li><a href="#checks">9. Salida de out/checks.py</a></li><li><a href="#prov">Apéndice: provenance.json</a></li></ol></nav>')

for s in secs:
    body = rc.render(s["html"], P)
    if 'class="missing"' in body:
        missing.append(s["id"])
    parts.append(f'<h2 id="{s["id"]}">{html.escape(s["title"])}</h2>{body}' + "".join(img(f) for f in s["figs"]))

parts.append(f'<h2 id="checks">9. Salida de <code>out/checks.py</code> (verbatim, exit {checks_rc})</h2><pre>{html.escape(checks_txt)}</pre>')

# appendix: provenance table (key, value, unit, origin, reproduce)
rows = []
for k in sorted(P):
    e = P[k]
    v = e.get("value", "")
    if isinstance(v, float):
        v = f"{v:.6g}"
    rows.append(f"<tr><td>{html.escape(k)}</td><td>{html.escape(str(v))}</td><td>{html.escape(str(e.get('unit', '')))}</td><td>{html.escape(str(e.get('origin', e.get('type', ''))))}</td><td>{html.escape(str(e.get('reproduce', '')))}</td></tr>")
parts.append(f'<h2 id="prov">Apéndice: <code>out/provenance.json</code> ({len(P)} entradas)</h2><details><summary>mostrar tabla</summary>'
             f'<table class="prov"><thead><tr><th>clave</th><th>valor</th><th>unidad</th><th>origen</th><th>reproduce</th></tr></thead><tbody>{"".join(rows)}</tbody></table></details>')
parts.append("</body></html>")

out = os.path.join(JOB, "out", "report.html")
open(out, "w", encoding="utf-8").write("\n".join(parts))
doc = open(out, encoding="utf-8").read()
ext = [l for l in doc.splitlines() if ('src="http' in l or 'href="http' in l or '<script' in l or '<link' in l)]
print(f"wrote {out}: {os.path.getsize(out)/1e6:.2f} MB, {len(secs)} sections, {sum(len(s['figs']) for s in secs)} figures inline, "
      f"missing placeholders in sections: {missing or 'none'}, external references: {len(ext)}, checks exit {checks_rc}")
if missing or ext:
    sys.exit(1)
