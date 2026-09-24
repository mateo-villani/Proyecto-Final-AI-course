# -*- coding: utf-8 -*-
"""Efecto Leidenfrost — cilindros de Cu en N2 líquido. Notebook marimo.

Mismo contenido que out/report.html (texto compartido en work/report_content.py, números tomados de
out/provenance.json) más una sección interactiva que recomputa T(t), dT/dt, t_c, Q/A y las etapas de la
balanza con parámetros libres: cilindro, ventana Savitzky-Golay, fracción de banda, T máxima de búsqueda,
geometría (h, d, m; por defecto la medida) y ventanas de ajuste de la balanza.

Correr desde el directorio del job:   marimo edit out/report.py     (o  marimo run out/report.py)
Exportar sin interfaz:                marimo export html out/report.py -o work/report_check.html
"""
import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", app_title="Leidenfrost — Cu en N2 líquido")


@app.cell
def _():
    import json
    import os
    import sys

    import marimo as mo
    import numpy as np

    # the notebook lives in <job>/out; the pipeline in <job>/work
    _here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.join(os.getcwd(), "out")
    JOB = os.path.dirname(_here) if os.path.basename(_here) == "out" else os.getcwd()
    WORK = os.path.join(JOB, "work")
    sys.path.insert(0, WORK)
    import analysis as an
    import report_content as rc

    P = json.load(open(os.path.join(JOB, "out", "provenance.json"), encoding="utf-8"))
    FIG = os.path.join(WORK, "fig")
    return FIG, JOB, P, WORK, an, mo, np, os, rc


@app.cell
def _(P, mo):
    mo.Html(
        "<h1>Efecto Leidenfrost en cilindros de cobre sumergidos en nitrógeno líquido</h1>"
        "<p><em>Reproducción desde cero a partir de <code>datos/</code>, <code>guia/</code> y las dimensiones medidas por el humano. "
        "Job 2026-09-18_205159, ronda 2. Los números del texto salen de <code>out/provenance.json</code> "
        f"({len(P)} entradas; cada uno lleva su clave en gris). La sección interactiva del final recomputa todo con parámetros libres.</em></p>"
        "<p><strong>Fence:</strong> nadie del equipo leyó, listó ni buscó nada bajo <code>informe-original/</code>.</p>"
    )
    return


@app.cell
def _(FIG, P, mo, os, rc):
    def section_view(sec):
        parts = [mo.Html(f'<h2>{sec["title"]}</h2>' + rc.render(sec["html"], P))]
        for f in sec["figs"]:
            parts.append(mo.image(src=os.path.join(FIG, f), caption=rc.FIG_CAPTIONS.get(f, f), width=760))
        return mo.vstack(parts)

    SECS = {s["id"]: s for s in rc.sections(P)}
    section_view(SECS["alcance"])
    return SECS, section_view


@app.cell
def _(SECS, section_view):
    section_view(SECS["preguntas"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["cv"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["geom"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["balanza"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["film"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["etapas"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["conclusiones"])
    return


@app.cell
def _(SECS, section_view):
    section_view(SECS["noverif"])
    return


@app.cell
def _(mo):
    mo.Html("<h2>9. Exploración interactiva</h2>"
            "<p>Los controles de abajo recomputan el pipeline (<code>work/analysis.py</code>) sobre los CSV crudos. "
            "Los valores por defecto son los del informe. El texto de las secciones anteriores <em>no</em> cambia "
            "(está atado a <code>provenance.json</code>); las figuras y tablas de esta sección sí.</p>")
    return


@app.cell
def _(an, mo):
    ui_cyl = mo.ui.dropdown(options=["A", "B", "C", "C1", "C3"], value="C", label="corrida")
    ui_sg = mo.ui.slider(start=3, stop=15, step=2, value=an.SG_WINDOW, label="ventana Savitzky–Golay (muestras, impar)")
    ui_frac = mo.ui.slider(start=0.2, stop=0.8, step=0.05, value=an.FRAC, label="fracción del máximo que define la banda de colapso")
    ui_tmax = mo.ui.slider(start=120, stop=290, step=5, value=an.T_SEARCH_MAX, label="T máxima de búsqueda de t_c (K)")
    ui_bal_skip1 = mo.ui.slider(start=0, stop=60, step=5, value=0, label="balanza: segundos excluidos al final de la etapa 1")
    ui_bal_skip3 = mo.ui.slider(start=0, stop=40, step=2, value=0, label="balanza: segundos excluidos al inicio de la etapa 3")
    ui_bal_tail = mo.ui.slider(start=10, stop=60, step=5, value=20, label="balanza: largo de la cola final (s)")
    mo.vstack([ui_cyl, ui_sg, ui_frac, ui_tmax, ui_bal_skip1, ui_bal_skip3, ui_bal_tail])
    return ui_bal_skip1, ui_bal_skip3, ui_bal_tail, ui_cyl, ui_frac, ui_sg, ui_tmax


@app.cell
def _(an, mo, ui_cyl):
    _body = an.BODY[ui_cyl.value]
    _g = an.GEOM[_body]
    ui_h = mo.ui.number(start=0.5, stop=30, step=0.1, value=round(_g["h_m"] * 100, 1), label=f"h del cilindro {_body} (cm)")
    ui_d = mo.ui.number(start=0.5, stop=20, step=0.1, value=round(_g["d_m"] * 100, 1), label=f"d del cilindro {_body} (cm)")
    ui_m = mo.ui.number(start=1, stop=5000, step=0.1, value=round(_g["m_kg"] * 1000, 1), label=f"m del cilindro {_body} (g)")
    mo.hstack([ui_h, ui_d, ui_m])
    return ui_d, ui_h, ui_m


@app.cell
def _(an, mo, np, ui_cyl, ui_d, ui_frac, ui_h, ui_m, ui_sg, ui_tmax):
    cyl = ui_cyl.value
    body = an.BODY[cyl]
    geom = an.geometry(body, h_m=ui_h.value / 100, d_m=ui_d.value / 100, m_kg=ui_m.value / 1000)
    run = an.analyse_run(cyl, window=int(ui_sg.value), frac=float(ui_frac.value), T_search_max=float(ui_tmax.value), geom=geom)
    tc = run["tc"]
    _ok = (run["t"] >= run["t0"]) & np.isfinite(run["qa"])
    _plateau = _ok & (run["T_s"] > 150) & (run["T_s"] < 250)
    _film = _ok & (run["T_s"] > tc["Thi_K"] + 10) & (run["T_s"] < 250)
    tbl = {
        "corrida": cyl, "cuerpo": body,
        "A (cm²)": round(geom["area_m2"] * 1e4, 1), "n (mol)": round(geom["n_mol"], 3), "p = m/A (kg/m²)": round(geom["p_kgm2"], 1),
        "t0 inmersión (s)": round(run["t0"], 1), "t_c archivo (s)": round(tc["t_s"], 1), "t_c desde t0 (s)": round(tc["t_s"] - run["t0"], 1),
        "T(t_c) (K)": round(tc["T_K"], 1), "T_lo (K)": round(tc["Tlo_K"], 1), "T_hi (K)": round(tc["Thi_K"], 1),
        "|dT/dt|max (K/s)": round(tc["rate_max_Ks"], 2), "pico/plateau": round(tc["peak_over_plateau"], 1) if np.isfinite(tc["peak_over_plateau"]) else None,
        "colapso detectado": tc["detected"], "espurios interpolados": int(run["bad"].sum()),
        "Q/A plateau 150-250 K (kW/m²)": round(float(np.median(run["qa"][_plateau])) / 1e3, 1) if _plateau.any() else None,
        "Q/A mín película (kW/m²)": round(float(run["qa"][_film].min()) / 1e3, 1) if _film.any() else None,
        "Q/A pico (kW/m²)": round(float(run["qa"][_ok].max()) / 1e3, 1),
        "t_c/p (s m²/kg)": round((tc["t_s"] - run["t0"]) / geom["p_kgm2"], 2),
    }
    mo.ui.table([tbl], selection=None)
    return body, cyl, geom, run, tc


@app.cell
def _(an, cyl, np, run, tc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _fig, _ax = plt.subplots(1, 3, figsize=(13, 3.8))
    _ax[0].plot(run["t"], run["T_raw"], ".", ms=2, color="#bbb", label="crudo")
    _ax[0].plot(run["t"], run["T_s"], color="#2a78d6", label="suavizado")
    _ax[0].axvline(tc["t_s"], color="gray", ls=":"); _ax[0].axhspan(tc["Tlo_K"], tc["Thi_K"], color="#eb6834", alpha=0.15, label="banda de colapso")
    _ax[0].set_xlabel("t (s)"); _ax[0].set_ylabel("T (K)"); _ax[0].set_ylim(60, 310); _ax[0].legend(frameon=False, fontsize=8); _ax[0].set_title(f"{cyl}: T(t)")
    _ok = run["t"] >= run["t0"]
    _ax[1].plot(run["T_s"][_ok], -run["dTdt"][_ok], color="#1baf7a"); _ax[1].set_yscale("log"); _ax[1].invert_xaxis()
    _ax[1].axvline(tc["T_K"], color="gray", ls=":"); _ax[1].set_xlabel("T (K)"); _ax[1].set_ylabel("−dT/dt (K/s)"); _ax[1].set_title("velocidad de enfriamiento")
    _okq = _ok & (run["qa"] > 0)
    _dT = run["T_s"] - an.T_SAT
    _ax[2].plot(_dT[_okq], run["qa"][_okq], "-o", ms=2.5, lw=0.9, color="#eb6834"); _ax[2].set_xscale("log"); _ax[2].set_yscale("log")
    _ax[2].set_xlim(1, 300); _ax[2].set_ylim(1e2, 1e6); _ax[2].axvline(tc["T_K"] - an.T_SAT, color="gray", ls=":")
    _ax[2].set_xlabel("ΔT = T − T_sat (K)"); _ax[2].set_ylabel("Q/A (W/m²)"); _ax[2].set_title("Q/A vs ΔT (log–log)")
    for _a in _ax:
        _a.grid(alpha=0.25)
    _fig.tight_layout()
    _fig
    return matplotlib, plt


@app.cell
def _(an, mo, np, plt, ui_bal_skip1, ui_bal_skip3, ui_bal_tail):
    bal = an.analyse_balance(stage1_skip_end_s=float(ui_bal_skip1.value), stage3_skip_start_s=float(ui_bal_skip3.value), tail_s=int(ui_bal_tail.value))
    _s1, _s3, _tail = bal["s1"], bal["s3"], bal["tail"]
    _Qbal = bal["dm_net_g"] * 1e-3 * an.L_V_N2
    _H = an.enthalpy_change(77.0, 296.0)
    _rows = [{
        "t1 fin (s)": round(bal["t_jump_s"], 1), "salto (g)": round(bal["st"]["jump_g"], 2), "burst (s)": f"{bal['t_burst_start_s']:.1f}–{bal['t_burst_end_s']:.1f}",
        "pendiente 1 (mg/s)": f"{_s1['slope']*1e3:.1f} ± {_s1['slope_err']*1e3:.1f} (n={_s1['n']})",
        "pendiente 3 (mg/s)": f"{_s3['slope']*1e3:.1f} ± {_s3['slope_err']*1e3:.1f} (n={_s3['n']})",
        "cola (mg/s)": f"{_tail['slope']*1e3:.1f} ± {_tail['slope_err']*1e3:.1f}",
        "s3/s1": round(_s3["slope"] / _s1["slope"], 2), "cola/s1": round(_tail["slope"] / _s1["slope"], 2),
        "Δm etapa 2 neto (g)": round(bal["dm_net_g"], 1), "Q balanza (kJ)": round(_Qbal / 1e3, 1),
        "Q_Cu(A/B/C) (kJ)": ", ".join(f"{an.geometry(c)['n_mol']*_H/1e3:.1f}" for c in "ABC"),
        "m por energía (kg)": round(_Qbal / (_H / an.M_CU), 3), "m por empuje (kg)": round(bal["st"]["jump_g"] * 1e-3 / an.RHO_LN2 * an.RHO_CU, 3),
    }]
    _fig, _ax = plt.subplots(figsize=(8, 3.8))
    _t, _m = bal["t"], bal["m"]
    _ax.plot(_t, _m, color="#52514e", lw=1.2, label="balanza")
    _tt1 = np.array([0, bal["t_jump_s"]]); _ax.plot(_tt1, _s1["slope"] * _tt1 + _s1["intercept"], color="#2a78d6", lw=2, label=f"etapa 1: {_s1['slope']*1e3:.1f} mg/s")
    _tt3 = np.array([bal["t_burst_end_s"], _t[-1]]); _ax.plot(_tt3, _s3["slope"] * _tt3 + _s3["intercept"], color="#eb6834", lw=2, label=f"etapa 3: {_s3['slope']*1e3:.1f} mg/s")
    for _x in (bal["t_jump_s"], bal["t_burst_start_s"], bal["t_burst_end_s"]):
        _ax.axvline(_x, color="gray", ls=":", lw=1)
    _ax.set_xlabel("t (s)"); _ax.set_ylabel("Δm (g)"); _ax.legend(frameon=False); _ax.grid(alpha=0.25); _ax.set_title("Balanza: etapas y ajustes con las ventanas elegidas")
    _fig.tight_layout()
    mo.vstack([mo.ui.table(_rows, selection=None), _fig])
    return


@app.cell
def _(an, mo, np, plt, ui_frac, ui_sg, ui_tmax):
    # t_c vs p for A, B, C with the chosen smoothing parameters and the measured geometry
    _ps, _ts, _dps, _lab = [], [], [], []
    for _c in ("A", "B", "C"):
        _g = an.geometry(_c)
        _r = an.analyse_run(_c, window=int(ui_sg.value), frac=float(ui_frac.value), T_search_max=float(ui_tmax.value))
        _ps.append(_g["p_kgm2"]); _ts.append(_r["tc"]["t_s"] - _r["t0"]); _dps.append(_g["dp_kgm2"]); _lab.append(_c)
    _ps, _ts, _dps = map(np.array, (_ps, _ts, _dps))
    _k = (_ps * _ts).sum() / (_ps * _ps).sum()
    _fig, _ax = plt.subplots(figsize=(5.5, 3.8))
    for _p, _t, _dp, _l in zip(_ps, _ts, _dps, _lab):
        _ax.errorbar(_p, _t, xerr=_dp, yerr=1.0, fmt="o", capsize=3, label=f"{_l}: t_c/p = {_t/_p:.2f} s m²/kg")
    _xx = np.linspace(0, 80, 5); _ax.plot(_xx, _k * _xx, ls="--", color="gray", label=f"t_c = k p, k = {_k:.2f}")
    _ax.set_xlim(0, 80); _ax.set_ylim(0, 330); _ax.set_xlabel("p = m/A (kg/m²)"); _ax.set_ylabel("t_c desde la inmersión (s)"); _ax.legend(frameon=False, fontsize=8); _ax.grid(alpha=0.25)
    _fig.tight_layout()
    mo.vstack([mo.Html("<h3>t_c vs p (A, B, C) con los parámetros de suavizado elegidos</h3>"), _fig])
    return


@app.cell
def _(WORK, mo, os):
    _p = os.path.join(WORK, "checks_output.txt")
    _txt = open(_p, encoding="utf-8").read() if os.path.exists(_p) else "(correr python out/checks.py)"
    mo.vstack([mo.Html("<h2>10. Salida de <code>out/checks.py</code></h2>"), mo.Html(f"<pre style='font-size:.8em'>{_txt.replace('<', '&lt;')}</pre>")])
    return


if __name__ == "__main__":
    app.run()
