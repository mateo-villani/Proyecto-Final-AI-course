"""Rebuild out/provenance.json from scratch and regenerate figures/results.
Run from the job directory:  python work/build_all.py
Order matters: analysis.py writes its keys, physics_numbers.py writes work/w2/provenance_physics.json,
merge_provenance.py folds the latter in without overwriting analysis.py keys."""
import os, subprocess, sys
JOB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(JOB)
prov = os.path.join("out", "provenance.json")
if os.path.exists(prov):
    os.remove(prov)
for cmd in (["python", "work/analysis.py"], ["python", "work/w2/physics_numbers.py"], ["python", "work/w2/merge_provenance.py"], ["python", "work/w3/extensions.py"]):
    print(">>", " ".join(cmd)); r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(r.stdout[-600:]); 
    if r.returncode: print(r.stderr); sys.exit(r.returncode)
