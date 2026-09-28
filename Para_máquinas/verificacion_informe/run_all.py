#!/usr/bin/env python3
"""Pipeline reproducible para la verificación numérica del informe.

Ejecutar desde cualquier directorio con: python run_all.py
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import pymupdf
except ImportError as exc:
    raise SystemExit(
        "Falta PyMuPDF. Instalalo con: python -m pip install -r requirements.txt"
    ) from exc


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PAGES = OUT / "pages"
CONFIG_PATH = HERE / "config.json"


def configure_utf8_output() -> None:
    """Avoid Windows legacy-console failures when printing symbols such as σ."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_pdf(pdf_path: Path, dpi: int) -> int:
    PAGES.mkdir(parents=True, exist_ok=True)
    for previous_page in PAGES.glob("page-*.png"):
        previous_page.unlink()
    document = pymupdf.open(pdf_path)
    for number, page in enumerate(document, start=1):
        target = PAGES / f"page-{number:02d}.png"
        page.get_pixmap(dpi=dpi, alpha=False).save(target)
    return document.page_count


def calculate(config: dict) -> tuple[dict, dict]:
    results: dict = {"cylinders": {}, "balance": {}, "einstein": {}}
    provenance: dict = {}
    molar_mass = config["copper_molar_mass_g_mol"]["value"]

    for name, data in config["cylinders"].items():
        radius = data["diameter_cm"] / 2.0
        lateral = math.pi * data["diameter_cm"] * data["height_cm"]
        caps = 2.0 * math.pi * radius**2
        area = lateral + caps
        moles = data["mass_g"] / molar_mass
        p_from_reported_area = data["mass_g"] / data["area_reported_cm2"]
        results["cylinders"][name] = {
            "area_lateral_cm2": lateral,
            "area_caps_cm2": caps,
            "area_calculated_cm2": area,
            "moles_calculated": moles,
            "p_calculated_g_cm2": p_from_reported_area,
            "tc_s": data["tc_s"],
        }
        base = f"cylinders.{name}"
        for field in (
            "height_cm", "diameter_cm", "mass_g", "area_reported_cm2",
            "area_uncertainty_cm2", "moles_reported", "p_reported_g_cm2",
            "p_uncertainty_g_cm2", "tc_s",
        ):
            provenance[f"{base}.{field}"] = {
                "value": data[field], "type": "extracted",
                "source": data["source"], "extraction": "manual_visual_transcription"
            }
        for field, value, formula in (
            ("area_calculated_cm2", area, "pi*D*h + 2*pi*(D/2)^2"),
            ("moles_calculated", moles, "mass_g / molar_mass_g_mol"),
            ("p_calculated_g_cm2", p_from_reported_area, "mass_g / area_reported_cm2"),
        ):
            provenance[f"{base}.{field}"] = {
                "value": value, "type": "calculated", "script": "run_all.py::calculate",
                "formula": formula
            }

    balance = config["balance"]
    difference = abs(balance["slope_3_g_s"] - balance["slope_1_g_s"])
    combined_uncertainty = math.hypot(
        balance["slope_1_uncertainty_g_s"], balance["slope_3_uncertainty_g_s"]
    )
    percent_difference = difference / abs(balance["slope_1_g_s"]) * 100.0
    compatibility_sigma = difference / combined_uncertainty
    residual_power = difference * balance["latent_heat_j_g"]
    results["balance"] = {
        "absolute_slope_difference_g_s": difference,
        "percent_difference": percent_difference,
        "combined_uncertainty_g_s": combined_uncertainty,
        "compatibility_sigma": compatibility_sigma,
        "residual_power_w": residual_power,
    }
    for field, value in balance.items():
        provenance[f"balance.{field}"] = {
            "value": value, "type": "extracted", "source": balance["source"],
            "extraction": "manual_visual_transcription"
        }
    for field, value in results["balance"].items():
        provenance[f"balance.{field}"] = {
            "value": value, "type": "calculated", "script": "run_all.py::calculate"
        }

    einstein = config["einstein"]
    for temperature in einstein["temperatures_k"]:
        exponent = math.exp(-einstein["c"] * temperature / einstein["theta_d_k"])
        theta_e = einstein["theta_d_k"] * (einstein["a"] + einstein["b"] * exponent)
        difference_pct = (theta_e / einstein["theta_d_k"] - 1.0) * 100.0
        key = str(int(temperature))
        results["einstein"][key] = {
            "temperature_k": temperature,
            "exp_term": exponent,
            "theta_e_k": theta_e,
            "difference_from_theta_d_pct": difference_pct,
        }
        provenance[f"einstein.theta_e_{key}_k"] = {
            "value": theta_e, "type": "calculated", "script": "run_all.py::calculate",
            "formula": "theta_D * (a + b * exp(-c*T/theta_D))",
            "source": einstein["source"]
        }
    return results, provenance


def run_checks(config: dict, pdf_path: Path, page_count: int, results: dict) -> list[dict]:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"status": "PASS" if condition else "FAIL", "name": name, "detail": detail})

    actual_hash = sha256(pdf_path)
    check("pdf.sha256", actual_hash == config["pdf"]["sha256"], f"SHA-256={actual_hash}")
    check("pdf.page_count", page_count == config["pdf"]["pages"], f"páginas={page_count}")
    check(
        "pdf.rendered_pages",
        len(list(PAGES.glob("page-*.png"))) == page_count,
        f"PNG generados={len(list(PAGES.glob('page-*.png')))}",
    )

    for name, data in config["cylinders"].items():
        calculated = results["cylinders"][name]
        area_delta = abs(calculated["area_calculated_cm2"] - data["area_reported_cm2"])
        check(
            f"cylinder.{name}.area",
            area_delta <= data["area_uncertainty_cm2"],
            f"calculada={calculated['area_calculated_cm2']:.2f}, reportada={data['area_reported_cm2']:.1f}±{data['area_uncertainty_cm2']:.1f} cm²",
        )
        check(
            f"cylinder.{name}.moles",
            abs(calculated["moles_calculated"] - data["moles_reported"]) <= 0.002,
            f"calculados={calculated['moles_calculated']:.4f}, reportados={data['moles_reported']:.3f} mol",
        )
        check(
            f"cylinder.{name}.p",
            abs(calculated["p_calculated_g_cm2"] - data["p_reported_g_cm2"]) <= data["p_uncertainty_g_cm2"],
            f"calculado={calculated['p_calculated_g_cm2']:.3f}, reportado={data['p_reported_g_cm2']:.1f}±{data['p_uncertainty_g_cm2']:.1f} g/cm²",
        )

    ordered_by_p = sorted(config["cylinders"], key=lambda key: config["cylinders"][key]["p_reported_g_cm2"])
    ordered_by_tc = sorted(config["cylinders"], key=lambda key: config["cylinders"][key]["tc_s"])
    check("relation.p_vs_tc", ordered_by_p == ordered_by_tc, f"orden p={ordered_by_p}; orden t_c={ordered_by_tc}")

    bal = results["balance"]
    check("balance.percent_difference", abs(bal["percent_difference"] - 37.6) < 0.2, f"diferencia={bal['percent_difference']:.2f}%")
    check("balance.not_compatible", bal["compatibility_sigma"] > 10.0, f"separación={bal['compatibility_sigma']:.2f}σ")
    check("balance.residual_power", abs(bal["residual_power_w"] - 7.12) < 0.05, f"potencia={bal['residual_power_w']:.3f} W")
    check("einstein.theta_e_77", abs(results["einstein"]["77"]["theta_e_k"] - 251.3) < 0.1, f"θE={results['einstein']['77']['theta_e_k']:.2f} K")
    check("einstein.theta_e_300", abs(results["einstein"]["300"]["theta_e_k"] - 242.6) < 0.1, f"θE={results['einstein']['300']['theta_e_k']:.2f} K")
    return checks


def build_report(pdf_path: Path, results: dict, checks: list[dict]) -> str:
    rows = []
    for name, values in results["cylinders"].items():
        rows.append(
            f"<tr><td>{name}</td><td>{values['area_calculated_cm2']:.2f}</td>"
            f"<td>{values['moles_calculated']:.4f}</td>"
            f"<td>{values['p_calculated_g_cm2']:.3f}</td><td>{values['tc_s']:.1f}</td></tr>"
        )
    check_rows = "\n".join(
        f"<tr class='{item['status'].lower()}'><td>{item['status']}</td>"
        f"<td>{html.escape(item['name'])}</td><td>{html.escape(item['detail'])}</td></tr>"
        for item in checks
    )
    passes = sum(item["status"] == "PASS" for item in checks)
    failures = sum(item["status"] == "FAIL" for item in checks)
    bal = results["balance"]
    ein = results["einstein"]
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Verificación automatizada del informe Leidenfrost</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#222}}table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border:1px solid #ccc;padding:.45rem;text-align:left}}th{{background:#eee}}.pass td:first-child{{color:#176b2c;font-weight:700}}.fail td:first-child{{color:#a11;font-weight:700}}code{{background:#eee;padding:.1rem .3rem}}</style></head><body>
<h1>Verificación automatizada del informe Leidenfrost</h1>
<p>Este reporte reproduce las cuentas numéricas auditables del informe. La interpretación física completa permanece en <code>Para_humanos/verificacion-informe-leidenfrost.html</code> y no se presenta como automatizada.</p>
<p><strong>Input:</strong> {html.escape(pdf_path.name)} ({sha256(pdf_path)}, 13 páginas).</p>
<h2>Geometría, moles y p</h2>
<table><tr><th>Cilindro</th><th>Área calculada [cm²]</th><th>Moles</th><th>p [g/cm²]</th><th>t<sub>c</sub> [s]</th></tr>{''.join(rows)}</table>
<p>El orden creciente de <em>p</em> y de <em>t<sub>c</sub></em> es B &lt; C &lt; A.</p>
<h2>Balanza</h2>
<ul><li>Diferencia de pendientes: {bal['absolute_slope_difference_g_s']:.4f} g/s ({bal['percent_difference']:.2f}%).</li>
<li>Error combinado: {bal['combined_uncertainty_g_s']:.5f} g/s.</li>
<li>Separación: {bal['compatibility_sigma']:.2f}σ; las pendientes no son compatibles.</li>
<li>Potencia residual: {bal['residual_power_w']:.3f} W.</li></ul>
<h2>Temperatura de Einstein</h2>
<table><tr><th>T [K]</th><th>θE [K]</th><th>Diferencia vs. θD</th></tr>
<tr><td>77</td><td>{ein['77']['theta_e_k']:.2f}</td><td>{ein['77']['difference_from_theta_d_pct']:.2f}%</td></tr>
<tr><td>300</td><td>{ein['300']['theta_e_k']:.2f}</td><td>{ein['300']['difference_from_theta_d_pct']:.2f}%</td></tr></table>
<h2>Checks</h2><p><strong>{passes} PASS, {failures} FAIL</strong></p>
<table><tr><th>Estado</th><th>Check</th><th>Detalle</th></tr>{check_rows}</table>
<h2>Alcance</h2><p>Los valores fuente fueron transcritos visualmente del PDF y están documentados en <code>config.json</code>. El pipeline verifica su identidad mediante SHA-256, renderiza todas las páginas y recalcula los resultados. No automatiza juicios conceptuales, lectura de gráficos ni conclusiones físicas.</p>
</body></html>"""


def main() -> int:
    configure_utf8_output()
    config = load_config()
    pdf_path = (HERE / config["pdf"]["path"]).resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"No se encontró el PDF: {pdf_path}")
    OUT.mkdir(parents=True, exist_ok=True)
    page_count = render_pdf(pdf_path, config["render_dpi"])
    results, provenance = calculate(config)
    checks = run_checks(config, pdf_path, page_count, results)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pymupdf": pymupdf.__version__,
        "input_pdf": str(pdf_path),
        "input_sha256": sha256(pdf_path),
    }
    provenance["run.metadata"] = {"type": "metadata", "value": metadata}
    (OUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    check_text = "\n".join(f"[{c['status']}] {c['name']}: {c['detail']}" for c in checks) + "\n"
    passes = sum(c["status"] == "PASS" for c in checks)
    failures = sum(c["status"] == "FAIL" for c in checks)
    check_text += f"\nchecks: {passes} PASS, {failures} FAIL\n"
    (OUT / "checks.txt").write_text(check_text, encoding="utf-8")
    (OUT / "report.html").write_text(build_report(pdf_path, results, checks), encoding="utf-8")
    print(check_text, end="")
    print(f"Reporte: {OUT / 'report.html'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
