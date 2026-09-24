"""Fold work/w2/provenance_physics.json into out/provenance.json.

Keys already present in out/provenance.json (worker 1's numerical pipeline) are never
overwritten; only missing keys are added. Run from the job directory:
    python work/w2/physics_numbers.py && python work/w2/merge_provenance.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(JOB, "out", "provenance.json")
MINE = os.path.join(HERE, "provenance_physics.json")

with open(MINE, encoding="utf-8") as fh:
    mine = json.load(fh)
existing = {}
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as fh:
        txt = fh.read().strip()
        existing = json.loads(txt) if txt else {}
if not isinstance(existing, dict):
    raise SystemExit(f"{OUT} is not a JSON object; refusing to merge")

added, kept = [], []
for k, v in mine.items():
    if k in existing:
        kept.append(k)
    else:
        existing[k] = v
        added.append(k)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(existing, fh, indent=1, ensure_ascii=False)
print(f"merged into {OUT}: {len(added)} added, {len(kept)} already present (kept worker-1 value): {kept}")
print(f"total entries now: {len(existing)}")
