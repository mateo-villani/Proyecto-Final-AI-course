#!/usr/bin/env python3
"""Round-3 review extensions (human request, 2026-09-23): quantify the balance-slope discrepancy,
extend Einstein vs Debye, add power-law/general-linear fits to t_c(p) with residuals, derive the
sigma_T error chain, build the annotated six-stage figure, predict a fourth cylinder, extend the
C1 anomaly investigation, and cross-check constants against reachable literature.

Reads work/analysis.py (imported, not re-run standalone) and the already-merged out/provenance.json
(analysis.py + physics_numbers.py keys). Writes ONLY new keys (prefixed bal2./cvcmp./fit./sigmaT./
pred./c1x./verif., plus a handful of stage.* keys) -- nothing written by analysis.py or
physics_numbers.py is overwritten. New figures go to work/fig/.

Run from the job directory, AFTER work/build_all.py:   python work/w3/extensions.py
"""
import itertools
import json
import os
import sys

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_coeffs

HERE = os.path.dirname(os.path.abspath(__file__))          # .../work/w3
WORK = os.path.dirname(HERE)                                # .../work
JOB = os.path.dirname(WORK)
sys.path.insert(0, WORK)
import analysis as an  # noqa: E402

FIG = os.path.join(WORK, "fig")
OUT = os.path.join(JOB, "out")
PPATH = os.path.join(OUT, "provenance.json")
S = "work/w3/extensions.py"

PROV = {}


def prov(key, value, statement, reproduce, origin, unit="", inputs=None, detail="", ptype="script"):
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, (np.integer,)):
        value = int(value)
    if isinstance(value, np.bool_):
        value = bool(value)
    PROV[key] = {"statement": statement, "type": ptype, "reproduce": reproduce, "detail": detail,
                 "value": value, "unit": unit, "origin": origin, "inputs": inputs or []}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": 0.25, "lines.linewidth": 1.6})

    P0json = json.load(open(PPATH, encoding="utf-8"))

    def val(k):
        return P0json[k]["value"]

    geoms = {c: an.geometry(c) for c in ("A", "B", "C")}
    runs = {c: an.analyse_run(c) for c in an.FILES}

    # =========================================================================== 2. balance residual power
    t, m = an.load_balance()
    bal = an.analyse_balance()
    st = bal["st"]
    ie = st["i_burst_end"]
    t0b, m0b = t[ie], m[ie]
    tail = bal["tail"]
    a_ambient = tail["slope"]                 # g/s, best estimate of the true ambient background (matches slope1 to 4 %)
    ks = np.where(t >= t0b)[0]
    tt, mm = t[ks] - t0b, m[ks]

    def decay_model(tt, P0_W, tau_s):
        return m0b + a_ambient * tt - (P0_W / an.L_V_N2 * 1e3) * tau_s * (1 - np.exp(-tt / tau_s))

    popt, pcov = curve_fit(decay_model, tt, mm, p0=[7.0, 60.0], maxfev=20000)
    perr = np.sqrt(np.diag(pcov))
    P0_res, tau_res = float(popt[0]), float(popt[1])
    dP0_res, dtau_res = float(perr[0]), float(perr[1])
    resid_decay = mm - decay_model(tt, *popt)
    rms_decay = float(np.sqrt(np.mean(resid_decay**2)))
    rms_linear3 = bal["s3"]["rms"]

    # naive (previous) estimate: whole-stage-3 slope vs stage-1 slope, and vs the tail
    dslope_avg = bal["s3"]["slope"] - bal["s1"]["slope"]
    Pres_avg_naive = abs(dslope_avg) * 1e-3 * an.L_V_N2
    dslope_tail = tail["slope"] - bal["s1"]["slope"]
    Pres_tail_naive = abs(dslope_tail) * 1e-3 * an.L_V_N2
    T_dur = tt[-1]
    Pres_avg_from_model = P0_res * tau_res / T_dur * (1 - np.exp(-T_dur / tau_res))

    g_C = geoms["C"]
    cv80 = float(an.cv_einstein(80.0))
    cv77 = float(an.cv_einstein(77.0))
    dT0_res = P0_res * tau_res / (g_C["n_mol"] * cv80)
    h_implied = g_C["n_mol"] * cv80 / (g_C["area_m2"] * tau_res)
    dT0_err = dT0_res * np.sqrt((dP0_res / P0_res) ** 2 + (dtau_res / tau_res) ** 2)

    r_C = runs["C"]
    tc_C = r_C["tc"]
    plateau_mask = (r_C["T_s"] < 85) & (r_C["t"] > tc_C["t_hi_s"] + 5)
    noise_std_dTdt = float(np.std(r_C["dTdt"][plateau_mask]))
    noise_mean_dTdt = float(np.mean(r_C["dTdt"][plateau_mask]))
    dTdt_implied_avg = Pres_avg_naive / (g_C["n_mol"] * cv77)
    dTdt_implied_tail = Pres_tail_naive / (g_C["n_mol"] * cv77)

    prov("bal2.slope1_mgs", bal["s1"]["slope"] * 1e3, "Stage-1 (ambient) slope, for reference in this section", f"{S}::main", "derived", "mg/s", ["bal.slope1_gs"])
    prov("bal2.slope3_whole_mgs", bal["s3"]["slope"] * 1e3, "Stage-3 slope fit over the WHOLE stage (curved: still includes the post-collapse transient)", f"{S}::main", "derived", "mg/s", ["bal.slope3_gs"])
    prov("bal2.slope3_tail_mgs", tail["slope"] * 1e3, "Stage-3 slope over the last 20 s only (best proxy for the true asymptotic ambient rate)", f"{S}::main", "derived", "mg/s", ["bal.slope3_tail_gs"])
    prov("bal2.slope_gap_naive_pct", 100 * (abs(bal["s3"]["slope"]) / abs(bal["s1"]["slope"]) - 1),
         "Naive (whole-stage) discrepancy (|slope3|/|slope1| - 1): the ~37 %% the human flagged", f"{S}::main", "derived", "%")
    prov("bal2.Pres_avg_naive_W", Pres_avg_naive, "Naive residual power: (|slope3_whole| - |slope1|) x L_v, averaged over the WHOLE stage-3 window", f"{S}::main", "derived", "W",
         ["bal2.slope3_whole_mgs", "bal2.slope1_mgs", "phys.L_v_N2"],
         detail="matches the previously quoted ~7.1 W to ~7 %; but mixes a real decaying transient with the asymptotic background (see bal2.model_*)")
    prov("bal2.Pres_tail_naive_W", Pres_tail_naive, "Naive residual power using the last-20-s slope instead: (|slope3_tail| - |slope1|) x L_v", f"{S}::main", "derived", "W",
         ["bal2.slope3_tail_mgs", "bal2.slope1_mgs"],
         detail="an order of magnitude smaller: by the end of the run the excess has mostly decayed")
    prov("bal2.model_P0_W", P0_res, "Fitted model m(t)=m0+a*t-(P0/Lv)*tau*(1-exp(-t/tau)) for stage 3 (a fixed = tail slope): initial residual power right after the burst",
         f"{S}::decay_model (scipy.optimize.curve_fit)", "derived", "W", detail=f"+/- {dP0_res:.2f} W (fit stderr only; does not include the ~10 %% Cv and L_v systematic uncertainties)")
    prov("bal2.model_tau_s", tau_res, "Fitted relaxation time constant of the residual power", f"{S}::decay_model", "derived", "s", detail=f"+/- {dtau_res:.2f} s (fit stderr only)")
    prov("bal2.model_rms_g", rms_decay, "RMS residual of the exponential-decay fit to stage 3", f"{S}::main", "derived", "g",
         detail=f"vs {rms_linear3:.2f} g RMS for the straight-line fit (bal.slope3_gs): the decay model removes the curvature the straight line could not")
    prov("bal2.model_Pavg_W", Pres_avg_from_model, "Time-average of the fitted P(t)=P0 exp(-t/tau) over the actual stage-3 duration", f"{S}::main", "derived", "W",
         ["bal2.model_P0_W", "bal2.model_tau_s"], detail="consistency check against bal2.Pres_avg_naive_W and the previous ~7.1 W estimate")
    prov("bal2.model_dT0_K", dT0_res, "Initial temperature excess above 77 K implied by the fitted P0 and tau via P0 = n Cv(T) dT0/tau", f"{S}::main", "derived", "K",
         ["bal2.model_P0_W", "bal2.model_tau_s", "geom.C.n_mol"], detail=f"+/- {dT0_err:.1f} K (fit stderr propagated; does not include Cv systematic)")
    prov("bal2.model_T0_K", 77.0 + dT0_res, "Fitted post-burst absolute temperature T0 = 77 K + dT0", f"{S}::main", "derived", "K",
         ["bal2.model_dT0_K"], detail=f"+/- {dT0_err:.1f} K (same stderr as bal2.model_dT0_K, added to the fixed 77 K reference)")
    prov("bal2.model_h_implied_Wm2K", h_implied, "Effective heat-transfer coefficient implied by tau = n Cv/(h A_C) (order of magnitude, NOT a calibrated result)",
         f"{S}::main", "derived", "W/(m2 K)", detail="between the film-boiling (~150) and nucleate-boiling (~1e4) order-of-magnitude estimates of phys.*: plausible for a transition-boiling relaxation")
    prov("bal2.Tlo_C_temperature_run_K", tc_C["Tlo_K"], "Lower edge of the collapse band measured in the SEPARATE temperature-only run of cylinder C (for comparison, not the same immersion)", f"{S}::main", "derived", "K", ["tc.C.Tlo_K"])
    prov("bal2.model_T0_vs_Tlo_K", 77 + dT0_res - tc_C["Tlo_K"], "Fitted post-burst temperature (77+dT0) minus the collapse-band lower edge of the temperature run (cross-check, different immersion)", f"{S}::main", "derived", "K")
    prov("bal2.noise_std_dTdt_plateau_C_Ks", noise_std_dTdt, "Std of dT/dt on the T<85 K plateau of the temperature-only run of C (noise floor for comparison)", f"{S}::main", "derived", "K/s")
    prov("bal2.noise_mean_dTdt_plateau_C_Ks", noise_mean_dTdt, "Mean of dT/dt on the same plateau (consistent with 0 within the noise)", f"{S}::main", "derived", "K/s")
    prov("bal2.dTdt_implied_avg_Ks", dTdt_implied_avg, "|dT/dt| that the naive whole-stage residual power would require at 77 K via Q/A eq. (1): Pres/(n Cv(77))", f"{S}::main", "derived", "K/s",
         detail="well above the plateau noise floor: if sustained, it would be visible in a temperature trace -- consistent with a real (not yet decayed) transient, not a steady residual")
    prov("bal2.dTdt_implied_tail_Ks", dTdt_implied_tail, "Same, from the tail-based residual power", f"{S}::main", "derived", "K/s",
         detail="comparable to or below the plateau noise floor: consistent with the cylinder being close to 77 K within the resolution of the temperature measurement by the end of the run")

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    axs[0].plot(t, m, color="#52514e", lw=1, label="balanza")
    tt1 = np.array([0, bal["t_jump_s"]])
    axs[0].plot(tt1, bal["s1"]["slope"] * tt1 + bal["s1"]["intercept"], color="#2a78d6", lw=1.6, label=f"etapa 1: {bal['s1']['slope']*1e3:.1f} mg/s")
    tt3 = t0b + tt
    axs[0].plot(tt3, decay_model(tt, *popt), color="#eb6834", lw=2, label=f"modelo exp.: P0={P0_res:.1f} W, τ={tau_res:.1f} s")
    axs[0].plot(tt3, bal["s3"]["slope"] * tt3 + bal["s3"]["intercept"], color="#c9a227", lw=1, ls="--", label=f"recta etapa 3: {bal['s3']['slope']*1e3:.1f} mg/s")
    axs[0].axvline(bal["t_jump_s"], color="gray", ls=":", lw=1)
    axs[0].axvline(t0b, color="gray", ls=":", lw=1)
    axs[0].set_xlabel("t (s)"); axs[0].set_ylabel("Δm (g)"); axs[0].legend(frameon=False, fontsize=8)
    axs[0].set_title("Balanza: modelo de relajación exponencial de la etapa 3")
    axs[1].plot(tt, resid_decay, "o", ms=3, color="#eb6834", label=f"modelo exp. (rms {rms_decay:.2f} g)")
    axs[1].plot(tt, mm - (bal["s3"]["slope"] * (tt + t0b) + bal["s3"]["intercept"]), "o", ms=3, color="#c9a227", label=f"recta (rms {rms_linear3:.2f} g)")
    axs[1].axhline(0, color="gray", lw=0.8)
    axs[1].set_xlabel("t desde fin del burst (s)"); axs[1].set_ylabel("residuo (g)"); axs[1].legend(frameon=False, fontsize=8)
    axs[1].set_title("Residuos: exponencial vs recta")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "balance_residual_model.png"), dpi=150); plt.close(fig)

    # =========================================================================== 3. Einstein vs Debye, extended
    Ttab = np.array([77, 90, 100, 120, 150, 180, 200, 220, 250, 280, 300], dtype=float)
    cve = an.cv_einstein(Ttab)
    cvd = an.cv_debye(Ttab)
    diff_abs = cve - cvd
    diff_pct = 100 * diff_abs / cvd
    prov("cvcmp.table_T_K", Ttab.tolist(), "Temperature grid for the Einstein/Debye Cv comparison table", f"{S}::main", "derived", "K", ptype="data")
    prov("cvcmp.table_Cv_Einstein", [round(float(x), 4) for x in cve], "Einstein Cv(T) on the grid", f"{S}::main", "derived", "J/(mol K)", ptype="data")
    prov("cvcmp.table_Cv_Debye", [round(float(x), 4) for x in cvd], "Debye Cv(T) on the grid", f"{S}::main", "derived", "J/(mol K)", ptype="data")
    prov("cvcmp.table_diff_abs", [round(float(x), 4) for x in diff_abs], "Cv_Einstein - Cv_Debye on the grid", f"{S}::main", "derived", "J/(mol K)", ptype="data")
    prov("cvcmp.table_diff_pct", [round(float(x), 3) for x in diff_pct], "100 (Cv_Einstein-Cv_Debye)/Cv_Debye on the grid", f"{S}::main", "derived", "%", ptype="data")
    i_max = int(np.argmax(np.abs(diff_pct)))
    prov("cvcmp.max_abs_diff_pct", float(diff_pct[i_max]), "Signed relative difference at the point of largest |difference| (always 77 K in 77-300 K)", f"{S}::main", "derived", "%", ["cvcmp.table_diff_pct"])
    prov("cvcmp.max_abs_diff_T_K", float(Ttab[i_max]), "T where the difference is largest", f"{S}::main", "derived", "K")

    # recompute Q/A with Debye instead of Einstein, same experimental T(t)/dT/dt, same geometry
    qa_cmp = {}
    for cyl in ("A", "B", "C"):
        r = runs[cyl]
        g = geoms[cyl]
        qa_e = r["qa"]                                  # Einstein, already computed by analyse_run
        qa_d = -g["n_over_A"] * an.cv_debye(r["T_s"]) * r["dTdt"]
        ok = (r["t"] >= r["t0"]) & np.isfinite(qa_e) & (qa_e > 0)
        plateau = ok & (r["T_s"] > 150) & (r["T_s"] < 250)
        tc = r["tc"]
        i_pk = np.argmax(np.where(ok, qa_e, -np.inf))
        film = ok & (r["T_s"] > tc["Thi_K"] + 10) & (r["T_s"] < 250)
        i_min = np.where(film)[0][np.argmin(qa_e[film])] if film.any() else None
        qa_cmp[cyl] = dict(qa_e=qa_e, qa_d=qa_d, ok=ok)
        for label, idx_or_mask, kind in (("plateau", plateau, "mask"), ("peak", i_pk, "idx"), ("min_film", i_min, "idx")):
            if kind == "mask":
                if not idx_or_mask.any():
                    continue
                ve, vd = float(np.median(qa_e[idx_or_mask])), float(np.median(qa_d[idx_or_mask]))
            else:
                if idx_or_mask is None:
                    continue
                ve, vd = float(qa_e[idx_or_mask]), float(qa_d[idx_or_mask])
            pct = 100 * (ve - vd) / vd
            prov(f"cvcmp.qa.{cyl}.{label}_Einstein_Wm2", ve, f"Q/A ({label}) of run {cyl}, Einstein Cv (= qa.{cyl}.*, repeated here for the side-by-side comparison)", f"{S}::main", "derived", "W/m2")
            prov(f"cvcmp.qa.{cyl}.{label}_Debye_Wm2", vd, f"Same Q/A ({label}) of run {cyl}, recomputed with Debye Cv on the identical T(t)/dT/dt/geometry", f"{S}::main", "derived", "W/m2")
            prov(f"cvcmp.qa.{cyl}.{label}_diff_pct", pct, f"(Einstein-Debye)/Debye for Q/A ({label}) of run {cyl}", f"{S}::main", "derived", "%")

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    TT = np.linspace(70, 305, 240)
    axs[0].plot(TT, an.cv_einstein(TT), color="#2a78d6", label="Einstein (usado, ec. 5)")
    axs[0].plot(TT, an.cv_debye(TT), color="#eb6834", ls="--", label="Debye Θ_D=315 K")
    axs[0].set_xlabel("T (K)"); axs[0].set_ylabel("Cv (J/mol K)"); axs[0].legend(frameon=False); axs[0].set_title("Cv(T): Einstein vs Debye")
    ax2 = axs[1]
    diffTT = 100 * (an.cv_einstein(TT) - an.cv_debye(TT)) / an.cv_debye(TT)
    ax2.plot(TT, diffTT, color="#1baf7a")
    ax2.axhline(0, color="gray", lw=0.8)
    ax2.set_xlabel("T (K)"); ax2.set_ylabel("(Einstein−Debye)/Debye (%)")
    ax2.set_title(f"Diferencia relativa (máx {float(np.max(np.abs(diffTT))):.1f} % a {TT[np.argmax(np.abs(diffTT))]:.0f} K)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Cv_diff.png"), dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    r = runs["C"]; g = geoms["C"]
    ok = qa_cmp["C"]["ok"]
    dT = r["T_s"][ok] - an.T_SAT
    ax.plot(dT, qa_cmp["C"]["qa_e"][ok], color="#2a78d6", lw=1.4, label="Q/A, Einstein")
    ax.plot(dT, qa_cmp["C"]["qa_d"][ok], color="#eb6834", lw=1.4, ls="--", label="Q/A, Debye")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(1, 300); ax.set_ylim(1e2, 1e6)
    ax.set_xlabel("ΔT = T − T_sat (K)"); ax.set_ylabel("Q/A (W/m²)"); ax.legend(frameon=False)
    ax.set_title("Cilindro C: Q/A con Cv de Einstein vs Debye (misma T(t) y geometría)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "QA_models_compare.png"), dpi=150); plt.close(fig)

    # =========================================================================== 4. p vs t_c: power-law & general-linear fits
    order = ("A", "B", "C")
    ps = np.array([geoms[c]["p_kgm2"] for c in order])
    dps = np.array([geoms[c]["dp_kgm2"] for c in order])
    tcs = np.array([runs[c]["tc"]["t_s"] - runs[c]["t0"] for c in order])
    w_origin = 1 / ((tcs * dps / ps) ** 2 + (0.5 * np.median(np.diff(runs["A"]["t"]))) ** 2)
    k_origin = float((w_origin * ps * tcs).sum() / (w_origin * ps * ps).sum())
    pred_origin = k_origin * ps

    lp, lt = np.log(ps), np.log(tcs)
    n_pow, lnA_pow = np.polyfit(lp, lt, 1)
    A_pow = float(np.exp(lnA_pow))
    pred_pow = A_pow * ps ** n_pow

    k_lin, b_lin = np.polyfit(ps, tcs, 1)
    pred_lin = k_lin * ps + b_lin

    for name, pred, params in (("through_origin", pred_origin, {"k_s_m2_per_kg": k_origin}),
                                ("power_law", pred_pow, {"A": A_pow, "n": float(n_pow)}),
                                ("general_linear", pred_lin, {"k_s_m2_per_kg": float(k_lin), "b_s": float(b_lin)})):
        resid_pct = 100 * (tcs - pred) / tcs
        prov(f"fit.{name}.params", params, f"Parameters of the {name.replace('_',' ')} fit t_c(p) over A, B, C", f"{S}::main", "derived", "", ptype="data")
        prov(f"fit.{name}.resid_pct", [round(float(x), 2) for x in resid_pct], f"Residuals (t_c - pred)/t_c x100 for A, B, C, {name.replace('_',' ')} fit", f"{S}::main", "derived", "%", ptype="data")
        prov(f"fit.{name}.max_abs_resid_pct", float(np.max(np.abs(resid_pct))), f"Max |residual| of the {name.replace('_',' ')} fit", f"{S}::main", "derived", "%")
        prov(f"fit.{name}.dof", 1 if name != "through_origin" else 2, f"Degrees of freedom of the {name.replace('_',' ')} fit with 3 data points", f"{S}::main", "derived", "")
    prov("fit.n_datapoints", 3, "Number of independent (p, t_c) pairs available (A, B, C): any 2-parameter model has only 1 residual degree of freedom",
         f"{S}::main", "derived", "", detail="a 2-parameter fit to 3 points is only weakly constrained: it will look good (small residuals) almost regardless of the true functional form, because 2 of the 3 points fix the 2 parameters and only the third point carries information")

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    pp = np.linspace(0.1, 80, 200)
    axs[0].errorbar(ps, tcs, xerr=dps, yerr=1.0, fmt="o", color="#1c1c1c", capsize=3, zorder=5, label="A, B, C (medido)")
    axs[0].plot(pp, k_origin * pp, color="#2a78d6", label=f"t_c=k·p (motivado por balance): k={k_origin:.2f}")
    axs[0].plot(pp, A_pow * pp ** n_pow, color="#eb6834", ls="--", label=f"ley de potencia: t_c=A·p^n, n={n_pow:.2f}")
    axs[0].plot(pp, k_lin * pp + b_lin, color="#1baf7a", ls=":", label=f"recta general: t_c=k·p+b, b={b_lin:.0f} s")
    axs[0].set_xlim(0, 80); axs[0].set_ylim(0, 330); axs[0].set_xlabel("p = m/A (kg/m²)"); axs[0].set_ylabel("t_c desde inmersión (s)")
    axs[0].legend(frameon=False, fontsize=7.5); axs[0].set_title("t_c vs p: tres modelos, 3 puntos")
    width = 0.25
    xi = np.arange(3)
    for off, (name, pred) in zip((-width, 0, width), (("origen", pred_origin), ("potencia", pred_pow), ("recta", pred_lin))):
        resid_pct = 100 * (tcs - pred) / tcs
        axs[1].bar(xi + off, resid_pct, width=width, label=name)
    axs[1].axhline(0, color="gray", lw=0.8)
    axs[1].set_xticks(xi); axs[1].set_xticklabels(order); axs[1].set_ylabel("residuo (%)"); axs[1].legend(frameon=False, fontsize=8)
    axs[1].set_title("Residuos por cilindro y modelo")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "tc_vs_p_models.png"), dpi=150); plt.close(fig)

    # =========================================================================== 7. fourth hypothetical cylinder D
    pD = 0.5 * (geoms["B"]["p_kgm2"] + geoms["C"]["p_kgm2"])
    dpD = 0.5 * np.sqrt(geoms["B"]["dp_kgm2"] ** 2 + geoms["C"]["dp_kgm2"] ** 2)
    predD = {"through_origin": k_origin * pD, "power_law": A_pow * pD ** n_pow, "general_linear": k_lin * pD + b_lin}
    prov("pred.D.p_kgm2", float(pD), "Chosen p for the hypothetical cylinder D: midpoint of p_B and p_C", f"{S}::main", "derived", "kg/m2",
         ["geom.B.p_kgm2", "geom.C.p_kgm2"], detail=f"+/- {dpD:.1f} kg/m2 (quadrature of B, C uncertainties)")
    prov("pred.D.dp_kgm2", float(dpD), "Uncertainty of p_D", f"{S}::main", "derived", "kg/m2")
    for name, v in predD.items():
        prov(f"pred.D.t_c_{name}_s", float(v), f"Predicted t_c of cylinder D from the {name.replace('_',' ')} model", f"{S}::main", "derived", "s", [f"fit.{name}.params", "pred.D.p_kgm2"])
    spread = max(predD.values()) - min(predD.values())
    prov("pred.D.model_spread_s", float(spread), "Spread of the 3 model predictions for t_c(D): the dominant source of uncertainty", f"{S}::main", "derived", "s")

    # geometry-uncertainty sensitivity of the through-origin prediction (only the physically-motivated model)
    vals = []
    for da, db, dc in itertools.product((-1, 0, 1), repeat=3):
        pps = ps + np.array([da, db, dc]) * dps
        kk = (w_origin * pps * tcs).sum() / (w_origin * pps * pps).sum()
        vals.append(kk * pD)
    vals = np.array(vals)
    prov("pred.D.geom_sensitivity_range_s", [float(vals.min()), float(vals.max())],
         "Range of the through-origin t_c(D) prediction when A/B/C geometry is perturbed by +/-1 sigma in every combination (2^3 corners)",
         f"{S}::main", "derived", "s", ptype="data",
         detail="much narrower than the spread between models (pred.D.model_spread_s): with only 3 cylinders, choosing the functional form matters far more than the geometric measurement uncertainty")
    for f in (-1, 0, 1):
        prov(f"pred.D.pD_{'lo' if f<0 else 'hi' if f>0 else 'mid'}_t_c_s", float(k_origin * (pD + f * dpD)),
             f"Through-origin t_c(D) if p_D is shifted by {f:+d} sigma", f"{S}::main", "derived", "s")

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.errorbar(ps, tcs, xerr=dps, yerr=1.0, fmt="o", color="#1c1c1c", capsize=3, label="A, B, C (medido)")
    pp = np.linspace(0.1, 80, 200)
    ax.plot(pp, k_origin * pp, color="#2a78d6", lw=1, label="t_c = k·p")
    ax.plot(pp, A_pow * pp ** n_pow, color="#eb6834", lw=1, ls="--", label="ley de potencia")
    ax.plot(pp, k_lin * pp + b_lin, color="#1baf7a", lw=1, ls=":", label="recta general")
    for name, col in zip(("through_origin", "power_law", "general_linear"), ("#2a78d6", "#eb6834", "#1baf7a")):
        ax.plot([pD], [predD[name]], "s", ms=8, color=col, mec="k")
    ax.errorbar([pD], [np.mean(list(predD.values()))], xerr=[dpD],
                yerr=[[np.mean(list(predD.values())) - min(predD.values())], [max(predD.values()) - np.mean(list(predD.values()))]],
                fmt="none", color="gray", capsize=4, lw=1.2)
    ax.axvline(pD, color="gray", ls=":", lw=1)
    ax.set_xlim(0, 80); ax.set_ylim(0, 330); ax.set_xlabel("p = m/A (kg/m²)"); ax.set_ylabel("t_c desde inmersión (s)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"Cilindro D hipotético (p={pD:.1f} kg/m²): t_c = {min(predD.values()):.0f}–{max(predD.values()):.0f} s según el modelo", fontsize=10.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "pred_D.png"), dpi=150); plt.close(fig)

    # =========================================================================== 5. temperature uncertainty propagation
    window, sg_order, dt_s = an.SG_WINDOW, an.SG_ORDER, float(np.median(np.diff(runs["A"]["t"])))
    coeffs = savgol_coeffs(window, sg_order, deriv=1, delta=dt_s)
    sg_gain = float(np.sqrt(np.sum(coeffs ** 2)))       # sigma_{dT/dt} = sg_gain * sigma_T, iid noise on T
    prov("sigmaT.sg_gain_per_s", sg_gain, f"Noise-gain factor of the {window}-point order-{sg_order} Savitzky-Golay derivative: sigma_dTdt = this x sigma_T (iid noise on T)",
         f"{S}::main (scipy.signal.savgol_coeffs)", "derived", "1/s", ["run.sg_window"])

    fs_V, bits = val("assume.adc_fs_V"), val("assume.adc_bits")
    lsb_adc_mV = 2 * fs_V / 2 ** bits * 1e3
    span_mV = val("qual.tc_span_mV")
    gain_amp = 1000 * lsb_adc_mV / span_mV               # the gain chosen elsewhere in the report for ~1000 counts
    lsb_referred_uV = lsb_adc_mV / gain_amp * 1e3
    sigma_ADC_uV = lsb_referred_uV / np.sqrt(12)          # uniform quantisation, +/- half LSB
    sens_hi_uVK = val("qual.tc_sens_hi_uVK")
    sens_lo_uVK = val("qual.tc_sens_lo_uVK")
    sigma_T_ADC_hi = sigma_ADC_uV / sens_hi_uVK
    sigma_T_ADC_lo = sigma_ADC_uV / sens_lo_uVK
    sigma_dTdt_hi = sg_gain * sigma_T_ADC_hi
    sigma_dTdt_lo = sg_gain * sigma_T_ADC_lo

    prov("sigmaT.formula", "sigma_T = sqrt[ (dT/dV)^2 (sigma_ADC/G)^2 + sigma_calib^2 + sigma_Tref^2 ]",
         "Symbolic error chain: quadrature sum of (i) ADC quantisation referred to the thermocouple through the local calibration slope dT/dV and the amplifier gain G, (ii) the thermocouple calibration/polynomial uncertainty, (iii) the ice-point reference-junction uncertainty",
         "derivation, not a fit", "guide", "", ptype="derivation",
         detail="each sigma is itself possibly T-dependent (dT/dV is, sigma_ADC is not); no cross-terms because the three sources are physically independent")
    prov("sigmaT.sigma_ADC_uV", float(sigma_ADC_uV), "ILLUSTRATIVE ONLY: half-LSB quantisation noise referred to the thermocouple, using the ASSUMED ADC (assume.adc_fs_V, assume.adc_bits) and the gain that spreads the run's span over ~1000 counts (qual.gain_for_1000_counts)",
         f"{S}::main", "derived", "uV", ["assume.adc_fs_V", "assume.adc_bits", "qual.tc_span_mV"],
         detail="NOT a measured instrument spec: the true ADC/amplifier noise floor is not in the sources; if it is worse than assumed here, sigma_T scales linearly with it")
    prov("sigmaT.sigma_T_ADC_hi_K", float(sigma_T_ADC_hi), "ILLUSTRATIVE: sigma_T from ADC quantisation alone near 295 K (high sensitivity, dT/dV small)", f"{S}::main", "derived", "K", ["sigmaT.sigma_ADC_uV", "qual.tc_sens_hi_uVK"])
    prov("sigmaT.sigma_T_ADC_lo_K", float(sigma_T_ADC_lo), "ILLUSTRATIVE: sigma_T from ADC quantisation alone near 80 K (low sensitivity, dT/dV large -> worse)", f"{S}::main", "derived", "K", ["sigmaT.sigma_ADC_uV", "qual.tc_sens_lo_uVK"])
    prov("sigmaT.sigma_dTdt_hi_Ks", float(sigma_dTdt_hi), "ILLUSTRATIVE: propagated sigma_dTdt near 295 K = sg_gain x sigma_T_ADC_hi", f"{S}::main", "derived", "K/s", ["sigmaT.sg_gain_per_s", "sigmaT.sigma_T_ADC_hi_K"])
    prov("sigmaT.sigma_dTdt_lo_Ks", float(sigma_dTdt_lo), "ILLUSTRATIVE: propagated sigma_dTdt near 80 K = sg_gain x sigma_T_ADC_lo", f"{S}::main", "derived", "K/s", ["sigmaT.sg_gain_per_s", "sigmaT.sigma_T_ADC_lo_K"])
    prov("sigmaT.crosscheck_vs_observed_noise_pct", 100 * (sigma_dTdt_lo / noise_std_dTdt - 1),
         "How far the ILLUSTRATIVE ADC-only sigma_dTdt near 80 K falls from the actually observed dT/dt noise floor on the plateau of run C (bal2.noise_std_dTdt_plateau_C_Ks)",
         f"{S}::main", "derived", "%", ["sigmaT.sigma_dTdt_lo_Ks", "bal2.noise_std_dTdt_plateau_C_Ks"],
         detail="agreement to within a few tens of percent is a nontrivial cross-check that the assumed ADC/gain are in the right ballpark, NOT proof of the true spec")
    dt_half = 0.5 * dt_s
    prov("sigmaT.sigma_tc_halfsample_s", float(dt_half), "sigma_t_c from finite sampling alone: since the collapse is sharp (peak/plateau ratio 5-11, run.frac), the identified peak sample changes only if the noise perturbation rivals the peak-to-neighbour drop; the residual uncertainty is +/- half a sample",
         f"{S}::main", "derived", "s", ["run.dt_s"], detail="matches the <=3 s sensitivity-sweep spread already reported (tc.*.sens_t_spread_s): dominated by sampling, not by sigma_T")
    for cyl in ("A", "B", "C"):
        r = runs[cyl]
        rate_plateau = float(np.median(np.abs(r["dTdt"][(r["T_s"] > 150) & (r["T_s"] < 250) & (r["t"] >= r["t0"])])))
        rate_peak = r["tc"]["rate_max_Ks"]
        rel_lo = sigma_dTdt_lo / rate_plateau if rate_plateau else np.nan
        rel_hi = sigma_dTdt_hi / rate_peak if rate_peak else np.nan
        prov(f"sigmaT.relQA_plateau_{cyl}_pct", 100 * rel_lo, f"ILLUSTRATIVE relative Q/A uncertainty from sigma_dTdt alone on the film plateau of run {cyl} (dominant term there)", f"{S}::main", "derived", "%")
        prov(f"sigmaT.relQA_peak_{cyl}_pct", 100 * rel_hi, f"ILLUSTRATIVE relative Q/A uncertainty from sigma_dTdt alone at the Q/A peak of run {cyl} (small: the signal is huge there)", f"{S}::main", "derived", "%")

    # =========================================================================== 6. six-stage annotated figure (cylinder C)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    r = runs["C"]
    ok = qa_cmp["C"]["ok"]
    dT = r["T_s"][ok] - an.T_SAT
    qa = qa_cmp["C"]["qa_e"][ok]
    order_idx = np.argsort(-dT)                     # right (large dT, early t) -> left (small dT, late t)
    ax.plot(dT[order_idx], qa[order_idx], "-", color="#1c1c1c", lw=1.5, zorder=5)
    tc_C_ = r["tc"]
    bounds = [300, 150, tc_C_["Thi_K"] - an.T_SAT, tc_C_["Tlo_K"] - an.T_SAT, 5, 1]
    names = ["VI: película + radiación", "V: película estable", "IV: transición", "III–II: nucleada", "I: convección"]
    status = ["indicios (rad. <1% del flujo, sec. 5x)", "observada", "observada", "observada (pocas muestras)", "no resuelta (Q/A~ruido)"]
    colors = ["#dfe7f2", "#c8dff0", "#f6d8b8", "#f2b8a8", "#e3e3e3"]
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(1, 300); ax.set_ylim(2e3, 3e5)
    ylo, yhi = ax.get_ylim()
    for i in range(len(bounds) - 1):
        ax.axvspan(bounds[i + 1], bounds[i], color=colors[i], alpha=0.6, zorder=0)
    for x in bounds[1:-1]:
        ax.axvline(x, color="gray", ls=":", lw=0.8, zorder=1)
    row_y = [yhi * 0.72, yhi * 0.42]                 # alternate two rows so adjacent bands never collide
    for i, (name, x0, x1) in enumerate(zip(names, bounds[:-1], bounds[1:])):
        xm = np.sqrt(max(x1, 1.05) * x0)
        y = row_y[i % 2]
        ax.text(xm, y, name, fontsize=8.5, ha="center", va="center", fontweight="bold")
    ax.set_xlabel("ΔT = T − T_sat (K)  (escala log)"); ax.set_ylabel("Q/A (W/m²)")
    ax.set_title("Cilindro C: Q/A vs ΔT con las seis etapas de la guía superpuestas")
    ax.annotate("", xy=(6, 3.0e3), xytext=(200, 3.0e3), arrowprops=dict(arrowstyle="-|>", color="#2a78d6", lw=2))
    ax.text(45, 3.4e3, "sentido temporal (el cilindro se enfría: derecha → izquierda)", color="#2a78d6", fontsize=8, ha="center")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "QA_dT_stages_C.png"), dpi=150); plt.close(fig)
    prov("stage.status", dict(zip(names, status)), "Evidentiary status of each stage given this experiment (observed / indications only / not resolved), used verbatim in sec. 6", f"{S}::main", "derived", "", ptype="data")
    prov("stage.bounds_dT_K", [round(float(x), 1) for x in bounds], "ΔT boundaries used to shade stages VI/V/IV/III-II/I on cylinder C (right to left: 300(edge), 150(VI/V, arbitrary, matches the plateau window already used elsewhere), T_hi-77(V/IV, measured), T_lo-77(IV/III-II, measured), 5(III-II/I, arbitrary: below this Q/A is noise-dominated), 1(edge))",
         f"{S}::main", "derived", "K", ["tc.C.Thi_K", "tc.C.Tlo_K"], ptype="data",
         detail="only the IV/III-II and III-II-side boundaries (T_hi, T_lo) come from a measured feature; the VI/V and I edges are drawn where the report's own qualitative description already puts them and are not separately justified by a data feature")

    # =========================================================================== 8. C1 anomaly: smoothing sensitivity + Biot at the transient
    windows = (3, 5, 7, 9, 11)
    peak_by_window = []
    for wnd in windows:
        rr = an.analyse_run("C1", window=wnd)
        okc = rr["t"] >= rr["t0"]
        peak_by_window.append(float(np.nanmax(rr["qa"][okc])))
    peak_by_window = np.array(peak_by_window)
    prov("c1x.peak_Wm2_vs_window", {str(w): round(float(v), 0) for w, v in zip(windows, peak_by_window)},
         "Peak Q/A of run C1 recomputed with different Savitzky-Golay windows (samples), everything else fixed", f"{S}::main", "derived", "W/m2", ptype="data")
    prov("c1x.peak_window_spread_ratio", float(peak_by_window.max() / peak_by_window.min()),
         "Ratio of the largest to the smallest peak Q/A over window in {3,5,7,9,11}: the reported C1 peak is not resolution-independent",
         f"{S}::main", "derived", "", detail="the whole 296->77 K drop spans only ~6 samples (run.dt_s ~1.42 s over ~8.5 s), so the numerical derivative -- and hence the peak Q/A -- is itself window-dependent by a factor >2")
    t1, T1, V1 = an.load_run("C1")
    r1 = an.analyse_run("C1")
    i0 = int(np.argmax(t1 > r1["t0"] - 1))
    below80 = np.where(T1[i0:] < 80)[0]
    i80 = i0 + int(below80[0]) if len(below80) else len(T1) - 1
    n_transient_samples = i80 - i0 + 1
    duration_transient_s = float(t1[i80] - t1[i0])
    prov("c1x.n_samples_full_transition", int(n_transient_samples), "Number of samples spanning the ENTIRE 296 K -> <80 K transition of run C1", f"{S}::main", "derived", "samples")
    prov("c1x.duration_full_transition_s", duration_transient_s, "Duration of that transition", f"{S}::main", "derived", "s")
    Q_peak_5 = float(peak_by_window[list(windows).index(5)])
    dT_peak_est = 100.0
    h_eq_peak = Q_peak_5 / dT_peak_est
    Bi_peak = h_eq_peak * geoms["C"]["Lc_m"] / 400.0
    prov("c1x.h_equiv_at_peak_Wm2K", h_eq_peak, "Equivalent heat-transfer coefficient at the SG-window-5 peak Q/A of C1, using an order-of-magnitude Delta T ~ 100 K", f"{S}::main", "derived", "W/(m2 K)")
    prov("c1x.Bi_at_peak", Bi_peak, "Biot number h Lc/k_Cu implied by that equivalent h, cylinder C (Lc = geom.C.Lc_m, k_Cu = 400 W/mK)", f"{S}::main", "derived", "",
         detail="Bi ~ 0.05-0.1: not overwhelmingly >1, but no longer negligible either -- the lumped-body assumption is marginal, not clearly satisfied, during this specific transient")
    plateau_T_C1 = val("tc.C1.plateau_T_K")
    plateau_T_C = val("tc.C.plateau_T_K")
    prov("c1x.plateau_T_diff_K", plateau_T_C1 - plateau_T_C, "Plateau temperature of C1 minus that of C (bare): if the junction were reading a locally colder/wetted spot, a persistent offset would be expected here",
         f"{S}::main", "derived", "K", ["tc.C1.plateau_T_K", "tc.C.plateau_T_K"],
         detail="the observed difference is comparable to the plateau's own noise level: the data neither support nor rule out the wetted-junction hypothesis")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(windows, peak_by_window / 1e3, "o-", color="#eb6834")
    ax.axhline(val("phys.qmax_LN2_Wm2") / 1e3, color="gray", ls="--", lw=1, label="q_max LN2 (orden de magnitud, literatura)")
    ax.set_xlabel("ventana Savitzky-Golay (muestras)"); ax.set_ylabel("Q/A pico, C1 (kW/m²)")
    ax.set_title("C1: el 'pico' de Q/A depende fuertemente de la ventana de suavizado")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "C1_sensitivity.png"), dpi=150); plt.close(fig)

    # =========================================================================== 1. constants cross-check (best-effort, offline+WebFetch)
    prov("verif.seebeck_K_room_vs_wikipedia", True,
         "phys.seebeck_K_uVK (41 uV/K) cross-checked against an independent secondary source (Wikipedia, 'Thermocouple' article, accessed this session): 'a sensitivity of approximately 41 uV/degC' for type K -- exact match",
         "WebFetch: https://en.wikipedia.org/wiki/Thermocouple (this session)", "literature", "bool", ["phys.seebeck_K_uVK"], ptype="source")
    prov("verif.nist_type_k_table_attempt", "not retrieved",
         "Attempted to fetch the primary NIST ITS-90 type-K inverse-polynomial coefficient table directly (srdata.nist.gov/its90 redirected to a navigation-only page; a secondary mirror returned HTTP 403). The digit-level polynomial used in work/analysis.py::typeK_T_from_V therefore remains UNVERIFIED against the primary source in this session",
         "WebFetch attempts, this session (see session log)", "literature", "", ptype="source",
         detail="mitigating evidence: (i) recomputing T from the CSV's own V with this polynomial reproduces the CSV's T column to <=0.2 K over two independent runs (tc_check.B/C.max_abs_dev_K), which is strong internal/empirical evidence the polynomial is correct even though its digits were not re-derived from the primary table here; (ii) the 41 uV/K room-T slope implied by the same polynomial matches the independently-sourced Wikipedia figure exactly (verif.seebeck_K_room_vs_wikipedia)")
    prov("verif.constants_status", "the tabulated constants (phys.*) are standard, widely reproduced textbook/handbook values (CRC Handbook, NIST WebBook, CODATA); this session did not have live access to CRC/NIST WebBook itself (paywalled/DB-only) so they were not re-fetched digit-by-digit, but they agree with each other and with the internal data (e.g. m/V of A/B/C matches rho_Cu to 1-3%, sec. 3) to well within their quoted tolerances",
         "constants cross-check", "guide, this file", "literature", "", ptype="source")
    prov("verif.listerman1986_ref", "Listerman, T.W., Boshinski, T.A., Knese, L.F. (1986), 'Cooling by immersion in liquid nitrogen', American Journal of Physics 54(6), 554-558",
         "Bibliographic identification (title/authors/journal/volume/pages) obtained via a CrossRef metadata query this session; the full text was NOT retrieved or read. Directly on-topic: a body cooling by LN2 immersion, the same class of experiment as this lab (already cited as the source of phys.h_film_Wm2K's order-of-magnitude film coefficient)",
         "WebFetch: api.crossref.org bibliographic search (this session)", "literature", "", ptype="source")
    prov("verif.curzon1978_ref", "Curzon, F.L. (1978), 'The Leidenfrost phenomenon', American Journal of Physics 46(8), 825-828",
         "Bibliographic identification obtained via the same CrossRef query; an automatically-fetched summary (not independently verified against the primary text) describes it as presenting four lecture-hall demonstrations of the Leidenfrost effect (drops floating on a vapour cushion, delayed quenching of heated brass) -- qualitative/demonstration in nature, not a quantitative lumped-body calorimetry study like this one. No numeric result from this paper is used or compared here because the primary text was not read",
         "WebFetch: api.crossref.org bibliographic search (this session)", "literature", "", ptype="source")
    prov("verif.adc_and_film_are_hypotheses", True,
         "assume.adc_fs_V, assume.adc_bits, assume.film_thickness_m and assume.film_k remain explicit, labelled HYPOTHESES: no ADC/amplifier datasheet or film specification was found in guia/ or datos/. Conclusions that depend on them (the illustrative sigma_T numbers of sec. 5x, and the film-vs-vapour resistance comparison of sec. 5) are flagged as such and are not used to support any quantitative conclusion in sec. 7-10",
         f"{S}::main", "derived", "bool", ["assume.adc_fs_V", "assume.adc_bits", "assume.film_thickness_m", "assume.film_k"], ptype="check")

    # =========================================================================== write
    ppath = PPATH
    merged = json.load(open(ppath, encoding="utf-8")) if os.path.exists(ppath) else {}
    clobber = sorted(k for k in PROV if k in merged)
    merged.update(PROV)
    with open(ppath, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=1, ensure_ascii=False)
    print(f"extensions.py wrote {len(PROV)} new provenance keys (total now {len(merged)}); {len(clobber)} keys overwritten (should be 0 on a first run): {clobber}")
    print(f"Pres_avg_naive={Pres_avg_naive:.2f} W, model P0={P0_res:.2f}+/-{dP0_res:.2f} W tau={tau_res:.2f}+/-{dtau_res:.2f} s, dT0={dT0_res:.1f}+/-{dT0_err:.1f} K")
    print(f"fits: through_origin k={k_origin:.3f}, power_law n={n_pow:.3f} A={A_pow:.3f}, general_linear k={k_lin:.3f} b={b_lin:.1f}")
    print(f"pred D: p={pD:.2f}+/-{dpD:.2f} kg/m2 -> t_c = {predD}")
    print(f"C1 peak Q/A vs window: {dict(zip(windows, peak_by_window.round(0)))}")


if __name__ == "__main__":
    main()
