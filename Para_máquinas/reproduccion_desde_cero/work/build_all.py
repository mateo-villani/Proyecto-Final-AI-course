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
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUTF8"] = "1"
for script in ("work/analysis.py", "work/w2/physics_numbers.py", "work/w2/merge_provenance.py", "work/w3/extensions.py"):
    cmd = [sys.executable, script]
    print(">>", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    if r.stdout:
        print(r.stdout[-600:])
    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
