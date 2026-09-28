#!/usr/bin/env python3
"""Run the numerical pipeline twice and require byte-identical scientific products."""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build_all.py")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def product_hashes():
    paths = [
        os.path.join(JOB, "out", "provenance.json"),
        os.path.join(HERE, "results.json"),
    ]
    fig_dir = os.path.join(HERE, "fig")
    paths.extend(os.path.join(fig_dir, name) for name in sorted(os.listdir(fig_dir)) if name.endswith(".png"))
    return {os.path.relpath(path, JOB).replace("\\", "/"): sha256(path) for path in paths}


def run_build():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([sys.executable, BUILD], cwd=JOB, env=env, capture_output=True,
                            text=True, encoding="utf-8")
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main():
    run_build()
    first = product_hashes()
    run_build()
    second = product_hashes()
    changed = [name for name in sorted(first) if first[name] != second.get(name)]
    added_or_removed = sorted(set(first) ^ set(second))
    if changed or added_or_removed:
        print(f"[FAIL] deterministic rebuild: changed={changed}, added_or_removed={added_or_removed}")
        return 1
    print(f"[PASS] deterministic rebuild: {len(first)} products are byte-identical across two clean rebuilds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
