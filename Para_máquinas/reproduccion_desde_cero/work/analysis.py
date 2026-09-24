#!/usr/bin/env python3
"""Leidenfrost / Cu-in-LN2 numerical pipeline.

Run from the job directory:  python work/analysis.py
Produces  out/provenance.json,  work/results.json,  work/fig/*.png.

Every number that lands in provenance.json is computed here; the function that produced it is
named in the entry's `reproduce` field (path::function).  Constants copied from the guide are
flagged origin="guide"; the per-cylinder geometry supplied by the human is origin="measured"; literature constants are
origin="literature"; everything else is origin="derived".
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.signal import medfilt, savgol_filter

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.dirname(HERE)
DATOS = os.path.join(JOB, "datos")
FIG = os.path.join(HERE, "fig")
OUT = os.path.join(JOB, "out")

# ----------------------------------------------------------------------------- constants
# origin="guide": copied verbatim from guia/Leidenfrost-guia.pdf (see work/equations.md)
THETA_D = 315.0      # K
A_E, B_E, C_E = 0.77, 0.26, 9.17
T_SAT = 77.0         # K
# origin="literature" (CODATA 2018 / CRC): not in the guide
R_GAS = 8.314462618  # J/(mol K)
M_CU = 63.546e-3     # kg/mol
RHO_CU = 8960.0      # kg/m3 (293 K)
L_V_N2 = 199.0e3     # J/kg, latent heat of vaporisation of N2 at 1 atm, 77 K
RHO_LN2 = 807.0      # kg/m3, liquid N2 density at 77 K
CP_N2_VAP = 1040.0   # J/(kg K), vapour cp (only used for a sensitivity bound)

# origin="measured": per-cylinder h, d, m supplied by the human (inbox.jsonl, 2026-09-18 21:12 and
# 21:35) with their stated uncertainties. These replace the round-1 nominal 10 cm / 4 cm / 1 kg.
# The human also stated area and n; those are recomputed here from (h, d, m) and compared
# (geom.<cyl>.area_stated_cm2 / n_stated_mol) -- the recomputed values are the ones used.
GEOM = {
    "A": {"h_m": 0.094, "d_m": 0.038, "m_kg": 0.9410, "dh_m": 0.001, "dd_m": 0.001, "dm_kg": 1e-4,
          "area_stated_cm2": 135.0, "darea_stated_cm2": 4.0, "n_stated_mol": 14.820, "dn_stated_mol": 0.002},
    "B": {"h_m": 0.049, "d_m": 0.022, "m_kg": 0.1658, "dh_m": 0.001, "dd_m": 0.001, "dm_kg": 1e-4,
          "area_stated_cm2": 42.0, "darea_stated_cm2": 2.0, "n_stated_mol": 2.611, "dn_stated_mol": 0.002},
    "C": {"h_m": 0.027, "d_m": 0.035, "m_kg": 0.2262, "dh_m": 0.001, "dd_m": 0.001, "dm_kg": 1e-4,
          "area_stated_cm2": 49.0, "darea_stated_cm2": 2.0, "n_stated_mol": 3.562, "dn_stated_mol": 0.002},
}
# guide nominal (page 3, "aprox. 10 cm, 4 cm, 1 kg"): kept ONLY for the density consistency remark,
# no longer used in any computation.
GEOM_NOMINAL_GUIDE = {"h_m": 0.10, "d_m": 0.04, "m_kg": 1.0}

FILES = {
    "A": "CilindroA_sumergido.csv",
    "B": "CilindroB_sumergido.csv",
    "C": "CilindroC_sumergido.csv",
    "C1": "cilindroC(aislado con 1 vuelta).csv",
    "C3": "cilindroC(aislado con 3 vueltas).csv",
}
BODY = {"A": "A", "B": "B", "C": "C", "C1": "C", "C3": "C"}   # which body each run uses

# analysis parameters (each is a choice; justified in the report)
SG_WINDOW = 5          # samples (7.2 s) for Savitzky-Golay derivative; drop lasts ~7-10 s
SG_ORDER = 2
MEDFILT_WINDOW = 7     # samples; three consecutive glitches in B need >5
OUTLIER_K = 8.0        # K; plateau noise ~0.1 K, cooling step <=2.5 K/sample outside collapse
T_SEARCH_MAX = 200.0   # K; collapse searched only below this (film regime certainly above)
FRAC = 0.5             # D3: abrupt-drop band = |dT/dt| >= FRAC * max
DETECT_RATIO = 3.0     # collapse "detected" if peak rate >= DETECT_RATIO x plateau median rate

PROV = {}


def prov(key, value, statement, reproduce, origin, unit="", inputs=None, detail="",
         ptype="script"):
    PROV[key] = {
        "statement": statement,
        "type": ptype,
        "reproduce": reproduce,
        "detail": detail,
        "value": (None if value is None else (float(value) if isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool) else value)),
        "unit": unit,
        "origin": origin,
        "inputs": inputs or [],
    }


# ----------------------------------------------------------------------------- heat capacity
def theta_E(T):
    """Eq. (5) of the guide: theta_E = theta_D [a + b exp(-c T/theta_D)]."""
    T = np.asarray(T, dtype=float)
    return THETA_D * (A_E + B_E * np.exp(-C_E * T / THETA_D))


def cv_einstein(T):
    """Einstein Cv with x = theta_E(T)/T in all three places [J/(mol K)] (corrected eq. 4)."""
    T = np.asarray(T, dtype=float)
    x = theta_E(T) / T
    return 3 * R_GAS * x**2 * np.exp(x) / (np.exp(x) - 1) ** 2


def cv_einstein_literal(T):
    """Eq. (4) exactly as printed: prefactor theta_E/T, exponentials theta_D/T (typo check)."""
    T = np.asarray(T, dtype=float)
    xe = theta_E(T) / T
    xd = THETA_D / T
    return 3 * R_GAS * xe**2 * np.exp(xd) / (np.exp(xd) - 1) ** 2


def debye_D(lam):
    val, _ = quad(lambda t: t**3 / np.expm1(t), 0, lam)
    return 3.0 / lam**3 * val


def cv_debye(T):
    """Debye Cv [J/(mol K)], guide p.2-3 expression, 3Nk -> 3R per mole."""
    T = np.atleast_1d(np.asarray(T, dtype=float))
    out = np.empty_like(T)
    for i, Ti in enumerate(T):
        lam = THETA_D / Ti
        out[i] = 3 * R_GAS * (4 * debye_D(lam) - 3 * lam / np.expm1(lam))
    return out if out.size > 1 else out[0]


def enthalpy_change(T1, T2, cv=cv_einstein):
    """integral of Cv dT from T1 to T2 [J/mol]."""
    val, _ = quad(lambda T: float(cv(T)), T1, T2)
    return val


# ----------------------------------------------------------------------------- geometry
def geometry(cyl, h_m=None, d_m=None, m_kg=None):
    """Area, moles, p = m/A of a closed cylinder, with first-order uncertainty propagation.
    A = pi d^2/2 + pi d h  ->  dA = sqrt[(pi (d + h) dd)^2 + (pi d dh)^2]  (independent errors)
    n = m/M               ->  dn = dm/M
    p = m/A               ->  dp/p = sqrt[(dm/m)^2 + (dA/A)^2]
    Explicit h_m/d_m/m_kg override the measured values (used by the marimo notebook)."""
    g = GEOM[cyl]
    h = g["h_m"] if h_m is None else h_m
    d = g["d_m"] if d_m is None else d_m
    m = g["m_kg"] if m_kg is None else m_kg
    dh, dd, dm = g["dh_m"], g["dd_m"], g["dm_kg"]
    r = d / 2
    area = 2 * np.pi * r**2 + 2 * np.pi * r * h
    darea = np.sqrt((np.pi * (d + h) * dd) ** 2 + (np.pi * d * dh) ** 2)
    n = m / M_CU
    dn = dm / M_CU
    p = m / area
    dp = p * np.sqrt((dm / m) ** 2 + (darea / area) ** 2)
    vol = np.pi * r**2 * h
    return {"h_m": h, "d_m": d, "m_kg": m, "dh_m": dh, "dd_m": dd, "dm_kg": dm,
            "area_m2": area, "darea_m2": darea, "n_mol": n, "dn_mol": dn,
            "p_kgm2": p, "dp_kgm2": dp, "n_over_A": n / area, "vol_m3": vol,
            "rho_from_m_V": m / vol, "Lc_m": vol / area}


# ----------------------------------------------------------------------------- temperature runs
def load_run(cyl):
    df = pd.read_csv(os.path.join(DATOS, FILES[cyl]))
    t = df["Tiempo (s)"].to_numpy(float)
    T = df["Temperatura (K)"].to_numpy(float)
    V = df["Voltaje (V)"].to_numpy(float)
    return t, T, V


def clean(T, k=MEDFILT_WINDOW, thr=OUTLIER_K):
    """Replace spikes (|T - running median| > thr) by linear interpolation. Returns (Tc, mask)."""
    med = medfilt(T, kernel_size=k)
    bad = np.abs(T - med) > thr
    Tc = T.copy()
    idx = np.arange(len(T))
    if bad.any():
        Tc[bad] = np.interp(idx[bad], idx[~bad], T[~bad])
    return Tc, bad


def derivative(t, Tc, window=SG_WINDOW, order=SG_ORDER):
    dt = np.median(np.diff(t))
    Ts = savgol_filter(Tc, window, order, deriv=0, delta=dt)
    dTdt = savgol_filter(Tc, window, order, deriv=1, delta=dt)
    return Ts, dTdt


def find_tc(t, Ts, dTdt, frac=FRAC, T_search_max=T_SEARCH_MAX, detect_ratio=DETECT_RATIO):
    """D3 criterion. t_c = time of max |dT/dt| among samples with Ts < T_search_max.
    Band [T_lo, T_hi]: contiguous samples around the peak with |dT/dt| >= frac*max.
    detected: peak rate / median rate on the film plateau (T_search_max .. T_peak+20 K) >= ratio."""
    rate = -dTdt
    sel = np.where(Ts < T_search_max)[0]
    if len(sel) == 0:
        return None
    ipk = sel[np.argmax(rate[sel])]
    peak = rate[ipk]
    lo = ipk
    while lo - 1 >= 0 and rate[lo - 1] >= frac * peak:
        lo -= 1
    hi = ipk
    while hi + 1 < len(rate) and rate[hi + 1] >= frac * peak:
        hi += 1
    plateau = np.where((Ts >= Ts[ipk] + 20) & (Ts < T_search_max))[0]
    plateau_rate = float(np.median(rate[plateau])) if len(plateau) >= 3 else np.nan
    ratio = peak / plateau_rate if plateau_rate and plateau_rate > 0 else np.nan
    return {"i": int(ipk), "t_s": float(t[ipk]), "T_K": float(Ts[ipk]), "rate_max_Ks": float(peak),
            "Thi_K": float(Ts[lo]), "Tlo_K": float(Ts[hi]), "t_lo_s": float(t[lo]), "t_hi_s": float(t[hi]),
            "plateau_rate_Ks": plateau_rate, "peak_over_plateau": float(ratio),
            "detected": bool(np.isfinite(ratio) and ratio >= detect_ratio)}


def cooling_start(t, Ts, drop_K=1.0):
    """First time the smoothed T has fallen drop_K below its initial value (immersion instant)."""
    i = np.argmax(Ts < Ts[0] - drop_K)
    return float(t[i]) if Ts[i] < Ts[0] - drop_K else float(t[0])


def heat_flux(cyl, Ts, dTdt, geom=None):
    """D4: Q/A = -(n/A) Cp(T) dT/dt, W/m2, Cp ~ Cv (Einstein). geom: optional geometry() dict override."""
    g = geometry(BODY[cyl]) if geom is None else geom
    return -g["n_over_A"] * cv_einstein(Ts) * dTdt


def analyse_run(cyl, window=SG_WINDOW, frac=FRAC, T_search_max=T_SEARCH_MAX, geom=None):
    t, T, V = load_run(cyl)
    Tc, bad = clean(T)
    Ts, dTdt = derivative(t, Tc, window=window)
    tc = find_tc(t, Ts, dTdt, frac=frac, T_search_max=T_search_max)
    qa = heat_flux(cyl, Ts, dTdt, geom=geom)
    return {"t": t, "T_raw": T, "V": V, "T_clean": Tc, "bad": bad, "T_s": Ts, "dTdt": dTdt,
            "qa": qa, "tc": tc, "t0": cooling_start(t, Ts)}


def rate_at(Ts, dTdt, T_target):
    """-dT/dt interpolated at the first crossing of T_target on the way down."""
    i = np.argmax(Ts <= T_target)
    if i == 0 or Ts[i] > T_target:
        return np.nan
    return float(np.interp(T_target, [Ts[i], Ts[i - 1]], [-dTdt[i], -dTdt[i - 1]]))


def sensitivity(cyl):
    """t_c and band vs SG window and band fraction."""
    rows = []
    for w in (3, 5, 7, 9, 11):
        for fr in (0.3, 0.5, 0.7):
            r = analyse_run(cyl, window=w, frac=fr)["tc"]
            rows.append({"window": w, "frac": fr, "t_s": r["t_s"], "T_K": r["T_K"],
                         "Tlo_K": r["Tlo_K"], "Thi_K": r["Thi_K"], "rate_max_Ks": r["rate_max_Ks"]})
    return rows


# ----------------------------------------------------------------------------- balance
def load_balance():
    df = pd.read_csv(os.path.join(DATOS, "medicion_balanza.csv"))
    ts = pd.to_datetime(df["timestamp"])
    t = (ts - ts.iloc[0]).dt.total_seconds().to_numpy(float)
    m = df["peso_g"].to_numpy(float)
    return t, m


BAL_SG_WINDOW = 11   # s; smooths the 0.1-g quantisation noise, still resolves the ~15 s burst


def balance_rate(m, window=BAL_SG_WINDOW):
    """Smoothed dm/dt (g/s), Savitzky-Golay linear, 1-s sampling."""
    return savgol_filter(m, window, 1, deriv=1, delta=1.0)


def balance_stages(t, m):
    """Change-points from the data, not fixed times.
    stage1 -> stage2: the largest single upward 1-s step (buoyancy when the Cu enters the bath).
    stage2 -> stage3: end of the violent-boiling burst = the contiguous window around the minimum of the
    smoothed rate (searched > 30 s after the jump) where the rate is below half that minimum."""
    dm = np.diff(m)
    i_jump = int(np.argmax(dm))                # m[i_jump] -> m[i_jump+1] is the jump
    jump_g = float(dm[i_jump])
    r = balance_rate(m)
    lo_search = i_jump + 30
    i_min = lo_search + int(np.argmin(r[lo_search:]))
    thr = 0.5 * r[i_min]                       # r < 0: "below half the minimum" = |r| > 0.5 |r_min|
    a = i_min
    while a - 1 > i_jump and r[a - 1] < thr:
        a -= 1
    b = i_min
    while b + 1 < len(r) and r[b + 1] < thr:
        b += 1
    return {"i_jump": i_jump, "jump_g": jump_g, "i_burst_start": int(a), "i_burst_end": int(b),
            "i_burst_peak": int(i_min), "burst_peak_rate_gs": float(r[i_min]),
            "rate_prejump_gs": float(np.median(r[max(0, i_jump - 20):i_jump - 5])),
            "rate_post_immersion_gs": float(np.median(r[i_jump + 8:i_jump + 30])),
            "rate_preburst_gs": float(np.median(r[max(i_jump + 30, a - 25):a - 5]))}


def linfit(t, m):
    A = np.vstack([t, np.ones_like(t)]).T
    coef, res, *_ = np.linalg.lstsq(A, m, rcond=None)
    resid = m - A @ coef
    n = len(t)
    s2 = (resid**2).sum() / (n - 2)
    cov = s2 * np.linalg.inv(A.T @ A)
    return {"slope": float(coef[0]), "intercept": float(coef[1]), "slope_err": float(np.sqrt(cov[0, 0])),
            "rms": float(np.sqrt((resid**2).mean())), "n": int(n)}


def robust_linfit(t, m, spike_K=2.0):
    """Least squares after dropping points > spike_K g from a first fit (balance glitches)."""
    f = linfit(t, m)
    resid = m - (f["slope"] * t + f["intercept"])
    keep = np.abs(resid) < spike_K
    f2 = linfit(t[keep], m[keep])
    f2["n_dropped"] = int((~keep).sum())
    return f2


def analyse_balance(stage1_skip_end_s=0.0, stage3_skip_start_s=0.0, tail_s=20):
    """stage1 fit: t=0 .. jump (minus stage1_skip_end_s); stage3 fit: burst end (+stage3_skip_start_s) .. end."""
    t, m = load_balance()
    st = balance_stages(t, m)
    ij, ie = st["i_jump"], st["i_burst_end"]
    k1 = np.where(t[: ij + 1] <= t[ij] - stage1_skip_end_s)[0]
    k3 = np.where(t >= t[ie] + stage3_skip_start_s)[0]
    s1 = robust_linfit(t[k1], m[k1])
    s3 = robust_linfit(t[k3], m[k3])
    tail = linfit(t[-tail_s:], m[-tail_s:])
    # stage 2 evaporation attributable to the Cu: from right after the jump to the burst end,
    # minus the ambient-evaporation baseline (stage-1 slope) over the same interval
    m_start = m[ij + 1]
    m_end = m[ie]
    dur = t[ie] - t[ij + 1]
    dm_raw = m_start - m_end
    dm_net = dm_raw + s1["slope"] * dur       # s1 slope < 0: ambient loss over dur is -slope*dur
    burst_dm = m[st["i_burst_start"]] - m[ie]
    return {"t": t, "m": m, "st": st, "s1": s1, "s3": s3, "tail": tail, "dm_raw_g": float(dm_raw),
            "dm_net_g": float(dm_net), "dur_s": float(dur), "burst_dm_g": float(burst_dm),
            "t_jump_s": float(t[ij + 1]), "t_burst_start_s": float(t[st["i_burst_start"]]),
            "t_burst_end_s": float(t[ie])}


# ----------------------------------------------------------------------------- thermocouple check
# NIST ITS-90 type K inverse polynomial coefficients (E in mV -> t90 in degC). Typed from memory
# of the NIST table; NOT verified against the source. Used only as a consistency check on the
# CSV's own V->T conversion, never as a primary result.
_K_NEG = [0.0, 2.5173462e1, -1.1662878, -1.0833638, -8.9773540e-1, -3.7342377e-1,
          -8.6632643e-2, -1.0450598e-2, -5.1920577e-4]
_K_POS = [0.0, 2.508355e1, 7.860106e-2, -2.503131e-1, 8.315270e-2, -1.228034e-2,
          9.804036e-4, -4.413030e-5, 1.057734e-6, -1.052755e-8]


def typeK_T_from_V(V):
    E = np.asarray(V) * 1e3
    out = np.empty_like(E)
    for i, e in enumerate(E):
        c = _K_NEG if e < 0 else _K_POS
        out[i] = sum(ck * e**k for k, ck in enumerate(c))
    return out + 273.15


# ----------------------------------------------------------------------------- figures
PAL = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a", "C1": "#eb6834", "C3": "#2a78d6"}


def make_figures(runs, bal):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": 0.25, "lines.linewidth": 1.6})

    # 1. T(t) A/B/C
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for k, cyl in enumerate(("A", "B", "C")):
        r = runs[cyl]
        nb = int(r["bad"].sum())
        ax.plot(r["t"], r["T_clean"], color=PAL[cyl], label=f"Cilindro {cyl}" + (f" ({nb} espurios interpolados)" if nb else ""))
        tc = r["tc"]
        ax.axvline(tc["t_s"], color=PAL[cyl], ls=":", lw=1)
        ax.text(tc["t_s"] - 3, 305 - 22 * k, f"t_c({cyl}) = {tc['t_s']:.0f} s", color=PAL[cyl], fontsize=9, ha="right", va="top")
    ax.axhline(T_SAT, color="gray", lw=0.8, ls="--")
    ax.text(5, T_SAT + 3, "T_sat = 77 K", color="gray", fontsize=8)
    ax.set_ylim(60, 310); ax.set_xlabel("t (s)"); ax.set_ylabel("T (K)")
    ax.set_title("Enfriamiento de los tres cilindros de Cu en N2 líquido")
    ax.legend(frameon=False, loc="center right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T_vs_t_ABC.png"), dpi=150); plt.close(fig)

    # 2. T(t) C / C1 / C3
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    lab = {"C": "C sin film", "C1": "C + 1 vuelta film", "C3": "C + 3 vueltas film"}
    for cyl in ("C", "C1", "C3"):
        r = runs[cyl]
        ax.plot(r["t"], r["T_clean"], color=PAL[cyl], label=lab[cyl])
        tc = r["tc"]
        if tc["detected"]:
            ax.axvline(tc["t_s"], color=PAL[cyl], ls=":", lw=1)
    ax.set_xlim(-5, 260); ax.set_ylim(60, 310)
    ax.axhline(T_SAT, color="gray", lw=0.8, ls="--")
    ax.set_xlabel("t (s)"); ax.set_ylabel("T (K)")
    ax.set_title("Cilindro C: efecto del recubrimiento con film (punteado: t_c detectado)")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T_vs_t_C_film.png"), dpi=150); plt.close(fig)

    # 3. balance
    t, m = bal["t"], bal["m"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(t, m, color="#52514e", lw=1.2, label="balanza (masa relativa)")
    s1, s3 = bal["s1"], bal["s3"]
    tt1 = np.array([0, bal["t_jump_s"]]); ax.plot(tt1, s1["slope"] * tt1 + s1["intercept"], color="#2a78d6", lw=2,
                                              label=f"etapa 1: {s1['slope']*1e3:.0f} mg/s")
    tt3 = np.array([bal["t_burst_end_s"], t[-1]]); ax.plot(tt3, s3["slope"] * tt3 + s3["intercept"], color="#eb6834", lw=2,
                                                        label=f"etapa 3: {s3['slope']*1e3:.0f} mg/s")
    for x, txt in ((bal["t_jump_s"], "inmersión"), (bal["t_burst_end_s"], "colapso")):
        ax.axvline(x, color="gray", ls=":", lw=1); ax.text(x + 2, -60, txt, rotation=90, color="gray", fontsize=8)
    ax.set_xlabel("t (s)"); ax.set_ylabel("Δm (g)")
    ax.set_title("Masa de N2 líquido (relativa a la tara) vs tiempo")
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "balance.png"), dpi=150); plt.close(fig)

    # 4/5. Q/A vs dT for C (lin, log)
    for cyl in ("C", "A", "B"):
        r = runs[cyl]
        dT = r["T_s"] - T_SAT
        ok = (r["t"] >= r["t0"]) & (r["qa"] > 0)
        for scale in ("lin", "log"):
            fig, ax = plt.subplots(figsize=(7.0, 4.2))
            ax.plot(dT[ok], r["qa"][ok], "-o", color=PAL[cyl], ms=3, lw=1)
            if scale == "log":
                ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(1, 300); ax.set_ylim(1e2, 1e6)
            else:
                ax.set_xlim(0, 230)
            ax.axvline(r["tc"]["T_K"] - T_SAT, color="gray", ls=":", lw=1)
            ax.text(r["tc"]["T_K"] - T_SAT, ax.get_ylim()[1] * (0.5 if scale == "log" else 0.95), " t_c", color="gray", fontsize=8, va="top")
            ax.set_xlabel("ΔT = T − T_sat (K)"); ax.set_ylabel("Q/A (W/m²)")
            ax.set_title(f"Cilindro {cyl}: Q/A vs ΔT ({scale}); m/A = {geometry(cyl)['p_kgm2']:.1f} kg/m² (medido)")
            fig.tight_layout(); fig.savefig(os.path.join(FIG, f"QA_vs_dT_{cyl}_{scale}.png"), dpi=150); plt.close(fig)

    # 5b. t_c vs p (measured geometry, error bars)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ps, ts, dps, dts = [], [], [], []
    for cyl in ("A", "B", "C"):
        g = geometry(cyl); r = runs[cyl]
        tci = r["tc"]["t_s"] - r["t0"]; dt = np.sqrt(2) * 0.5 * np.median(np.diff(r["t"]))
        ps.append(g["p_kgm2"]); ts.append(tci); dps.append(g["dp_kgm2"]); dts.append(dt)
        ax.errorbar(g["p_kgm2"], tci, xerr=g["dp_kgm2"], yerr=dt, fmt="o", color=PAL[cyl], capsize=3, label=f"{cyl}: t_c/p = {tci/g['p_kgm2']:.2f} s m²/kg")
    ps, ts, dps, dts = map(np.array, (ps, ts, dps, dts))
    sig = np.sqrt(dts**2 + (ts * dps / ps) ** 2)          # same weights as rel.tc_vs_p.slope_s_m2_per_kg
    w = 1 / sig**2
    k = (w * ps * ts).sum() / (w * ps * ps).sum()
    xx = np.linspace(0, 80, 10)
    ax.plot(xx, k * xx, color="gray", lw=1, ls="--", label=f"t_c = k·p, k = {k:.2f} s m²/kg (mín. cuadrados pesados)")
    ax.set_xlim(0, 80); ax.set_ylim(0, 330); ax.set_xlabel("p = m/A (kg/m²)"); ax.set_ylabel("t_c desde la inmersión (s)")
    ax.set_title("t_c vs p (geometría medida)"); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "tc_vs_p.png"), dpi=150); plt.close(fig)

    # 6. Cv models
    TT = np.linspace(60, 320, 200)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(TT, cv_einstein(TT), color="#2a78d6", label="Einstein, θ_E(T) ec. 5 (usado)")
    ax.plot(TT, cv_debye(TT), color="#eb6834", ls="--", label="Debye θ_D=315 K")
    ax.plot(TT, cv_einstein_literal(TT), color="#1baf7a", ls=":", label="ec. 4 literal (θ_D en exp)")
    ax.axhline(3 * R_GAS, color="gray", lw=0.8); ax.text(65, 3 * R_GAS + 0.3, "3R", color="gray", fontsize=8)
    ax.set_xlabel("T (K)"); ax.set_ylabel("Cv (J mol⁻¹ K⁻¹)"); ax.legend(frameon=False)
    ax.set_title("Calor específico molar del Cu")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "Cv_models.png"), dpi=150); plt.close(fig)

    # 7. dT/dt for all runs vs T
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for cyl in ("A", "B", "C"):
        r = runs[cyl]
        ok = r["t"] >= r["t0"]
        ax.plot(r["T_s"][ok], -r["dTdt"][ok], color=PAL[cyl], label=cyl, lw=1.2)
    ax.set_xlabel("T (K)"); ax.set_ylabel("−dT/dt (K/s)"); ax.set_yscale("log"); ax.invert_xaxis()
    ax.legend(frameon=False); ax.set_title("Velocidad de enfriamiento (Savitzky–Golay, 5 muestras)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "dTdt_vs_T.png"), dpi=150); plt.close(fig)


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    S = "work/analysis.py"
    results = {}

    # --- physical constants
    prov("phys.T_sat_K", T_SAT, "Saturation temperature of liquid N2 at 1 atm", "guia/Leidenfrost-guia.pdf p.2",
         "guide", "K", ptype="source")
    prov("phys.R", R_GAS, "Gas constant", "CODATA 2018", "literature", "J/(mol K)", ptype="source")
    prov("phys.M_Cu", M_CU, "Molar mass of Cu", "IUPAC standard atomic weight 63.546", "literature", "kg/mol", ptype="source")
    prov("phys.rho_Cu", RHO_CU, "Density of Cu at 293 K", "CRC Handbook", "literature", "kg/m3", ptype="source")
    prov("phys.L_v_N2", L_V_N2, "Latent heat of vaporisation of N2 at 77 K, 1 atm", "CRC Handbook / NIST webbook (199 kJ/kg)",
         "literature", "J/kg", ptype="source")
    prov("phys.rho_LN2", RHO_LN2, "Density of liquid N2 at 77 K", "CRC Handbook (0.807 g/cm3)", "literature", "kg/m3", ptype="source")

    # --- Cv
    for k, v, st in (("cv.thetaD_K", THETA_D, "Debye temperature of Cu"), ("cv.a", A_E, "eq.5 coefficient a"),
                     ("cv.b", B_E, "eq.5 coefficient b"), ("cv.c", C_E, "eq.5 coefficient c")):
        prov(k, v, st, "guia/Leidenfrost-guia.pdf p.3, eq.(5)", "guide", "K" if k.endswith("_K") else "", ptype="source")
    cv300, cv77 = float(cv_einstein(300.0)), float(cv_einstein(77.0))
    prov("cv.thetaE_300K", float(theta_E(300.0)), "Einstein temperature from eq.5 at 300 K", f"{S}::theta_E", "derived", "K",
         ["cv.thetaD_K", "cv.a", "cv.b", "cv.c"])
    prov("cv.thetaE_77K", float(theta_E(77.0)), "Einstein temperature from eq.5 at 77 K", f"{S}::theta_E", "derived", "K",
         ["cv.thetaD_K", "cv.a", "cv.b", "cv.c"])
    prov("cv.Cv_300K", cv300, "Einstein Cv of Cu at 300 K (eq.4 with theta_E everywhere)", f"{S}::cv_einstein", "derived",
         "J/(mol K)", ["cv.thetaE_300K", "phys.R"])
    prov("cv.Cv_77K", cv77, "Einstein Cv of Cu at 77 K", f"{S}::cv_einstein", "derived", "J/(mol K)", ["cv.thetaE_77K", "phys.R"])
    prov("cv.Cv_300K_over_3R", cv300 / (3 * R_GAS), "Cv(300K)/3R, Dulong-Petit ratio", f"{S}::cv_einstein", "derived", "")
    d300, d77 = float(cv_debye(300.0)), float(cv_debye(77.0))
    prov("cv.debye_Cv_300K", d300, "Debye Cv of Cu at 300 K, theta_D=315 K (cross-check)", f"{S}::cv_debye", "derived", "J/(mol K)")
    prov("cv.debye_Cv_77K", d77, "Debye Cv of Cu at 77 K (cross-check)", f"{S}::cv_debye", "derived", "J/(mol K)")
    TT = np.linspace(77, 300, 224)
    dev = 100 * (cv_einstein(TT) - cv_debye(TT)) / cv_debye(TT)
    prov("cv.einstein_vs_debye_maxdev_pct", float(np.max(np.abs(dev))),
         "Max |Einstein(eq.4-5) - Debye| / Debye over 77-300 K", f"{S}::main", "derived", "%",
         detail=f"max deviation at T={TT[np.argmax(np.abs(dev))]:.0f} K; Einstein is low at 77 K by {-dev[0]:.1f} %")
    prov("cv.eq4_literal_Cv_300K", float(cv_einstein_literal(300.0)),
         "Eq.4 evaluated exactly as printed (theta_D in the exponentials): unphysical, shows the typo",
         f"{S}::cv_einstein_literal", "derived", "J/(mol K)")
    H = enthalpy_change(77.0, 296.0)
    prov("cv.enthalpy_77_296_Jmol", H, "Integral of Einstein Cv dT from 77 K to 296 K", f"{S}::enthalpy_change", "derived", "J/mol")
    prov("cv.enthalpy_77_296_Jkg", H / M_CU, "Same per kg of Cu", f"{S}::enthalpy_change", "derived", "J/kg", ["cv.enthalpy_77_296_Jmol", "phys.M_Cu"])
    prov("cv.enthalpy_77_296_debye_Jmol", enthalpy_change(77.0, 296.0, cv_debye), "Same integral with Debye Cv (cross-check)",
         f"{S}::enthalpy_change", "derived", "J/mol")
    results["cv"] = {"T": TT.tolist(), "einstein": cv_einstein(TT).tolist(), "debye": cv_debye(TT).tolist()}

    # --- geometry (measured, human direction in inbox.jsonl)
    m_rho = RHO_CU * np.pi * (GEOM_NOMINAL_GUIDE["d_m"] / 2) ** 2 * GEOM_NOMINAL_GUIDE["h_m"]
    prov("geom.density_check_m_kg", m_rho, "Mass implied by rho_Cu x pi r^2 h for the guide's nominal 10 cm x 4 cm (consistency remark only; nominal geometry is NOT used)",
         f"{S}::main", "derived", "kg", ["phys.rho_Cu"])
    geoms = {}
    for cyl in ("A", "B", "C"):
        g = geometry(cyl)
        geoms[cyl] = g
        raw = GEOM[cyl]
        for k, unit in (("h_m", "m"), ("d_m", "m"), ("m_kg", "kg")):
            prov(f"geom.{cyl}.{k}", g[k], f"Cylinder {cyl} {k.split('_')[0]} = {g[k]} +/- {raw['d'+k]} {unit}, measured by the human (caliper/balance), supplied in inbox.jsonl 2026-09-18",
                 "inbox.jsonl (human direction, 2026-09-18 21:12 and 21:35)", "measured", unit, ptype="source",
                 detail=f"uncertainty +/- {raw['d'+k]} {unit} as stated by the human")
            prov(f"geom.{cyl}.d{k}", raw["d" + k], f"Stated uncertainty of {k} for cylinder {cyl}", "inbox.jsonl (human direction)", "measured", unit, ptype="source")
        prov(f"geom.{cyl}.area_m2", g["area_m2"], f"Total surface pi d^2/2 + pi d h of cylinder {cyl} from measured h, d", f"{S}::geometry", "derived", "m2",
             [f"geom.{cyl}.h_m", f"geom.{cyl}.d_m"], detail=f"= {g['area_m2']*1e4:.1f} +/- {g['darea_m2']*1e4:.1f} cm2; human stated {raw['area_stated_cm2']} +/- {raw['darea_stated_cm2']} cm2")
        prov(f"geom.{cyl}.darea_m2", g["darea_m2"], f"Uncertainty of the area of cylinder {cyl}: sqrt[(pi(d+h) dd)^2 + (pi d dh)^2]", f"{S}::geometry", "derived", "m2",
             [f"geom.{cyl}.dh_m", f"geom.{cyl}.dd_m"])
        prov(f"geom.{cyl}.area_stated_cm2", raw["area_stated_cm2"], f"Area of cylinder {cyl} as stated by the human (+/- {raw['darea_stated_cm2']} cm2)", "inbox.jsonl (human direction)", "measured", "cm2", ptype="source")
        prov(f"geom.{cyl}.area_agrees_with_stated", bool(abs(g["area_m2"] * 1e4 - raw["area_stated_cm2"]) <= raw["darea_stated_cm2"]),
             f"Recomputed area of {cyl} within the human's stated +/-", f"{S}::geometry", "derived", "bool",
             detail=f"|{g['area_m2']*1e4:.1f} - {raw['area_stated_cm2']}| = {abs(g['area_m2']*1e4-raw['area_stated_cm2']):.1f} cm2 vs +/- {raw['darea_stated_cm2']}")
        prov(f"geom.{cyl}.n_mol", g["n_mol"], f"Moles of Cu in cylinder {cyl} = m/M", f"{S}::geometry", "derived", "mol",
             [f"geom.{cyl}.m_kg", "phys.M_Cu"], detail=f"= {g['n_mol']:.3f} +/- {g['dn_mol']:.4f} mol; human stated {raw['n_stated_mol']} +/- {raw['dn_stated_mol']}")
        prov(f"geom.{cyl}.dn_mol", g["dn_mol"], f"Uncertainty of n for cylinder {cyl} = dm/M", f"{S}::geometry", "derived", "mol", [f"geom.{cyl}.dm_kg"])
        prov(f"geom.{cyl}.n_stated_mol", raw["n_stated_mol"], f"n of cylinder {cyl} as stated by the human (+/- {raw['dn_stated_mol']} mol)", "inbox.jsonl (human direction)", "measured", "mol", ptype="source")
        prov(f"geom.{cyl}.n_agrees_with_stated", bool(abs(g["n_mol"] - raw["n_stated_mol"]) <= raw["dn_stated_mol"] + g["dn_mol"]),
             f"Recomputed n of {cyl} within the stated +/- (both uncertainties added)", f"{S}::geometry", "derived", "bool",
             detail=f"|{g['n_mol']:.4f} - {raw['n_stated_mol']}| = {abs(g['n_mol']-raw['n_stated_mol']):.4f} mol")
        prov(f"geom.{cyl}.p_kgm2", g["p_kgm2"], f"p = m/A for cylinder {cyl}", f"{S}::geometry", "derived", "kg/m2",
             [f"geom.{cyl}.m_kg", f"geom.{cyl}.area_m2"], detail=f"= {g['p_kgm2']:.1f} +/- {g['dp_kgm2']:.1f} kg/m2")
        prov(f"geom.{cyl}.dp_kgm2", g["dp_kgm2"], f"Uncertainty of p for cylinder {cyl}: p sqrt[(dm/m)^2 + (dA/A)^2]", f"{S}::geometry", "derived", "kg/m2",
             [f"geom.{cyl}.darea_m2", f"geom.{cyl}.dm_kg"])
        prov(f"geom.{cyl}.n_over_A_molm2", g["n_over_A"], f"n/A for cylinder {cyl} (the prefactor of eq. 1)", f"{S}::geometry", "derived", "mol/m2",
             [f"geom.{cyl}.n_mol", f"geom.{cyl}.area_m2"])
        prov(f"geom.{cyl}.rho_from_mV_kgm3", g["rho_from_m_V"], f"m/V of cylinder {cyl} (should be ~8960 kg/m3 if solid Cu; less if it has a thermocouple hole)", f"{S}::geometry", "derived", "kg/m3",
             [f"geom.{cyl}.m_kg", f"geom.{cyl}.h_m", f"geom.{cyl}.d_m"])
        prov(f"geom.{cyl}.Lc_m", g["Lc_m"], f"Characteristic length V/A of cylinder {cyl}", f"{S}::geometry", "derived", "m")
    # the human's stated n values are m/63.5 (not m/63.546): record the implied molar mass; 0.07 % effect
    M_impl = np.mean([GEOM[c]["m_kg"] / GEOM[c]["n_stated_mol"] for c in ("A", "B", "C")])
    prov("geom.M_Cu_implied_by_stated_n", M_impl, "Molar mass implied by the human's stated n = m/M (mean over A, B, C); 63.5 g/mol was evidently used, we use 63.546",
         f"{S}::main", "derived", "kg/mol", detail=f"relative difference to 63.546: {100*(M_CU/M_impl-1):+.2f} %, negligible for Q/A")
    results["geom"] = geoms

    # --- temperature runs
    runs = {cyl: analyse_run(cyl) for cyl in FILES}
    prov("run.dt_s", float(np.median(np.diff(runs["A"]["t"]))), "Median sampling interval of the temperature CSVs",
         f"{S}::load_run", "derived", "s", ptype="script", detail="A,B,C: 1.439 s; C1,C3: 1.416 s")
    prov("run.sg_window", SG_WINDOW, "Savitzky-Golay window (samples) for dT/dt", f"{S}::derivative", "derived", "samples",
         detail=f"{SG_WINDOW} samples = {SG_WINDOW*1.439:.1f} s; shorter than the ~7-10 s collapse so it is not smeared")
    prov("run.T_search_max_K", T_SEARCH_MAX, "Collapse searched only below this T", f"{S}::find_tc", "derived", "K")
    prov("run.frac", FRAC, "Band fraction of max |dT/dt| defining the abrupt-drop interval (D3)", f"{S}::find_tc", "derived", "")
    for cyl, r in runs.items():
        tc = r["tc"]
        body = BODY[cyl]
        prov(f"clean.{cyl}.n_outliers", int(r["bad"].sum()), f"Samples replaced as spikes in run {cyl} (|T - median7| > {OUTLIER_K} K)",
             f"{S}::clean", "derived", "samples", [FILES[cyl]])
        prov(f"tc.{cyl}.t_s", tc["t_s"], f"t_c run {cyl}: time of max |dT/dt| (T<{T_SEARCH_MAX:.0f} K), from file t=0", f"{S}::find_tc",
             "derived", "s", [FILES[cyl]])
        prov(f"tc.{cyl}.t0_s", r["t0"], f"Immersion instant run {cyl}: first sample 1 K below the initial T", f"{S}::cooling_start",
             "derived", "s", [FILES[cyl]])
        prov(f"tc.{cyl}.t_from_immersion_s", tc["t_s"] - r["t0"], f"t_c run {cyl} measured from immersion", f"{S}::find_tc", "derived", "s",
             [f"tc.{cyl}.t_s", f"tc.{cyl}.t0_s"])
        prov(f"tc.{cyl}.T_K", tc["T_K"], f"Body temperature at t_c, run {cyl}", f"{S}::find_tc", "derived", "K", [FILES[cyl]])
        prov(f"tc.{cyl}.Thi_K", tc["Thi_K"], f"Upper T of the abrupt-drop band (|dT/dt| >= {FRAC} max), run {cyl}", f"{S}::find_tc", "derived", "K")
        prov(f"tc.{cyl}.Tlo_K", tc["Tlo_K"], f"Lower T of the abrupt-drop band, run {cyl}", f"{S}::find_tc", "derived", "K")
        prov(f"tc.{cyl}.dTdt_max_Ks", tc["rate_max_Ks"], f"Max cooling rate |dT/dt| at t_c, run {cyl}", f"{S}::find_tc", "derived", "K/s")
        prov(f"tc.{cyl}.plateau_rate_Ks", tc["plateau_rate_Ks"], f"Median |dT/dt| on the film plateau ({T_SEARCH_MAX:.0f} K .. T_c+20 K), run {cyl}",
             f"{S}::find_tc", "derived", "K/s")
        prov(f"tc.{cyl}.peak_over_plateau", tc["peak_over_plateau"], f"Peak/plateau rate ratio, run {cyl}; collapse 'detected' if >= {DETECT_RATIO}",
             f"{S}::find_tc", "derived", "")
        prov(f"tc.{cyl}.detected", tc["detected"], f"Whether an abrupt collapse is detected in run {cyl}", f"{S}::find_tc", "derived", "bool")
        # Q/A
        ok = (r["t"] >= r["t0"]) & np.isfinite(r["qa"])
        qa = r["qa"]; Ts = r["T_s"]
        i_pk = np.argmax(np.where(ok, qa, -np.inf))
        film = ok & (Ts > tc["Thi_K"] + 10) & (Ts < 250)
        i_min = np.where(film)[0][np.argmin(qa[film])] if film.any() else None
        prov(f"qa.{cyl}.peak_Wm2", float(qa[i_pk]), f"Max Q/A (nucleate-boiling peak), run {cyl}, measured n/A of body {body}", f"{S}::heat_flux", "derived", "W/m2",
             [f"geom.{body}.n_mol", f"geom.{body}.area_m2", "cv.Cv_300K"])
        prov(f"qa.{cyl}.dT_at_peak_K", float(Ts[i_pk] - T_SAT), f"Delta T at the Q/A peak, run {cyl}", f"{S}::heat_flux", "derived", "K")
        prov(f"qa.{cyl}.QA_at_tc_Wm2", float(qa[tc["i"]]), f"Q/A at t_c, run {cyl}", f"{S}::heat_flux", "derived", "W/m2")
        if i_min is not None:
            prov(f"qa.{cyl}.min_film_Wm2", float(qa[i_min]), f"Min Q/A in the film regime before collapse (Leidenfrost point), run {cyl}",
                 f"{S}::heat_flux", "derived", "W/m2")
            prov(f"qa.{cyl}.dT_at_min_K", float(Ts[i_min] - T_SAT), f"Delta T at the film-regime minimum, run {cyl}", f"{S}::heat_flux", "derived", "K")
        plateau = ok & (Ts > 150) & (Ts < 250)
        if plateau.any():
            prov(f"qa.{cyl}.plateau_Wm2", float(np.median(qa[plateau])), f"Median Q/A for 150<T<250 K (film boiling), run {cyl}",
                 f"{S}::heat_flux", "derived", "W/m2")
        ok_full = np.where(r["t"] >= r["t0"])[0]
        i_full = ok_full[np.argmax(-r["dTdt"][ok_full])]
        prov(f"tc.{cyl}.full_range_t_s", float(r["t"][i_full]), f"Time of max |dT/dt| over the whole run (no T<{T_SEARCH_MAX:.0f} K restriction), run {cyl}",
             f"{S}::main", "derived", "s")
        prov(f"tc.{cyl}.full_range_T_K", float(Ts[i_full]), f"T at the whole-run max |dT/dt|, run {cyl}", f"{S}::main", "derived", "K")
        prov(f"tc.{cyl}.plateau_T_K", float(np.median(Ts[r["t"] > r["t"][-1] - 30])), f"Median T over the last 30 s of run {cyl} (bath plateau; A never reaches it)",
             f"{S}::main", "derived", "K")
        for Tt in (250, 200, 150, 120, 100):
            prov(f"rate.{cyl}.dTdt_{Tt}K", rate_at(Ts, r["dTdt"], Tt), f"|dT/dt| at T={Tt} K, run {cyl}", f"{S}::rate_at", "derived", "K/s")
        cooling = ok & (r["t"] > r["t0"] + 15) & (r["t"] < tc["t_hi_s"] + 15) & (Ts > 79)
        neg = cooling & (qa <= 0)
        prov(f"qa.{cyl}.n_cooling_samples", int(cooling.sum()), f"Samples in the cooling window (t0+15 s .. end of drop band +15 s, T>79 K), run {cyl}",
             f"{S}::heat_flux", "derived", "samples")
        prov(f"qa.{cyl}.n_nonpositive", int(neg.sum()), f"Samples with Q/A<=0 inside the cooling window (15 s after immersion skips the immersion glitch in B), run {cyl}",
             f"{S}::heat_flux", "derived", "samples")
        results[cyl] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items()}

    # sensitivity
    for cyl in FILES:
        rows = sensitivity(cyl)
        ts = [x["t_s"] for x in rows]; Tl = [x["Tlo_K"] for x in rows]; Th = [x["Thi_K"] for x in rows]
        prov(f"tc.{cyl}.sens_t_spread_s", max(ts) - min(ts), f"Spread of t_c over SG window 3..11 and frac 0.3..0.7, run {cyl}",
             f"{S}::sensitivity", "derived", "s", detail=f"t_c in [{min(ts):.1f}, {max(ts):.1f}] s")
        prov(f"tc.{cyl}.sens_Tlo_range_K", f"{min(Tl):.1f}..{max(Tl):.1f}", f"Range of T_lo over the sensitivity grid, run {cyl}", f"{S}::sensitivity", "derived", "K")
        prov(f"tc.{cyl}.sens_Thi_range_K", f"{min(Th):.1f}..{max(Th):.1f}", f"Range of T_hi over the sensitivity grid, run {cyl}", f"{S}::sensitivity", "derived", "K")
        results.setdefault("sens", {})[cyl] = rows

    # film effect
    for k in ("C1", "C3"):
        d = runs[k]["tc"]["t_s"] - runs[k]["t0"] - (runs["C"]["tc"]["t_s"] - runs["C"]["t0"])
        prov(f"film.dtc_{k[1]}_s", d, f"t_c(C+{k[1]} vuelta(s)) - t_c(C sin film), both from immersion", f"{S}::main", "derived", "s",
             [f"tc.{k}.t_from_immersion_s", "tc.C.t_from_immersion_s"])
    prov("film.t_to_80K.C_s", float(runs["C"]["t"][np.argmax(runs["C"]["T_s"] < 80)] - runs["C"]["t0"]), "Time from immersion to T<80 K, C sin film", f"{S}::main", "derived", "s")
    prov("film.t_to_80K.C1_s", float(runs["C1"]["t"][np.argmax(runs["C1"]["T_s"] < 80)] - runs["C1"]["t0"]), "Time from immersion to T<80 K, C + 1 vuelta", f"{S}::main", "derived", "s")
    prov("film.t_to_80K.C3_s", float(runs["C3"]["t"][np.argmax(runs["C3"]["T_s"] < 80)] - runs["C3"]["t0"]), "Time from immersion to T<80 K, C + 3 vueltas", f"{S}::main", "derived", "s")

    # p vs t_c relation. Lumped body: dT/dt = -(Q/A)/(p c) -> if q_film(T) is the same for all bodies,
    # t_c ∝ p and |dT/dt| ∝ 1/p. Two tests: (i) geometry-independent: t_c ratios vs inverse rate ratios;
    # (ii) with the measured p: t_c/p per cylinder and a fit t_c = k p through the origin.
    for a, b in (("B", "A"), ("C", "A"), ("C", "B")):
        ta = runs[a]["tc"]["t_s"] - runs[a]["t0"]; tb = runs[b]["tc"]["t_s"] - runs[b]["t0"]
        ra = rate_at(runs[a]["T_s"], runs[a]["dTdt"], 200.0); rb = rate_at(runs[b]["T_s"], runs[b]["dTdt"], 200.0)
        prov(f"rel.tc_ratio_{a}{b}", ta / tb, f"t_c({a})/t_c({b}) from immersion", f"{S}::main", "derived", "")
        prov(f"rel.inv_rate_ratio_{a}{b}_200K", rb / ra, f"|dT/dt|_{b}/|dT/dt|_{a} at 200 K = implied p_{a}/p_{b} if q_film is body-independent",
             f"{S}::rate_at", "derived", "")
        pa, pb = geoms[a], geoms[b]
        pr = pa["p_kgm2"] / pb["p_kgm2"]
        dpr = pr * np.sqrt((pa["dp_kgm2"] / pa["p_kgm2"]) ** 2 + (pb["dp_kgm2"] / pb["p_kgm2"]) ** 2)
        prov(f"rel.p_ratio_{a}{b}", pr, f"p_{a}/p_{b} from the measured geometry", f"{S}::geometry", "derived", "",
             [f"geom.{a}.p_kgm2", f"geom.{b}.p_kgm2"], detail=f"+/- {dpr:.3f}")
        prov(f"rel.p_ratio_{a}{b}_err", dpr, f"Uncertainty of p_{a}/p_{b}", f"{S}::geometry", "derived", "")
    for cyl in ("B", "C"):
        rA = rate_at(runs["A"]["T_s"], runs["A"]["dTdt"], 200.0); rc = rate_at(runs[cyl]["T_s"], runs[cyl]["dTdt"], 200.0)
        prov(f"rel.p_{cyl}_over_pA_implied", rA / rc, f"p_{cyl}/p_A implied by cooling rates at 200 K (same q_film assumption); compare rel.p_ratio_{cyl}A (measured)",
             f"{S}::rate_at", "derived", "")
    tcp = {}
    for cyl in ("A", "B", "C"):
        g = geoms[cyl]
        tci = runs[cyl]["tc"]["t_s"] - runs[cyl]["t0"]
        dt_tc = 0.5 * float(np.median(np.diff(runs[cyl]["t"])))   # +/- half a sample on t_c and on t0
        v = tci / g["p_kgm2"]
        dv = v * np.sqrt((np.sqrt(2) * dt_tc / tci) ** 2 + (g["dp_kgm2"] / g["p_kgm2"]) ** 2)
        tcp[cyl] = (v, dv, tci, g["p_kgm2"], g["dp_kgm2"])
        prov(f"rel.tc_over_p.{cyl}", v, f"t_c/p for cylinder {cyl} (t_c from immersion, measured p)", f"{S}::main", "derived", "s m2/kg",
             [f"tc.{cyl}.t_from_immersion_s", f"geom.{cyl}.p_kgm2"], detail=f"+/- {dv:.2f} (half-sample on t_c and t0, dp from geometry)")
        prov(f"rel.tc_over_p.{cyl}_err", dv, f"Uncertainty of t_c/p for {cyl}", f"{S}::main", "derived", "s m2/kg")
    vals = np.array([tcp[c][0] for c in ("A", "B", "C")]); errs = np.array([tcp[c][1] for c in ("A", "B", "C")])
    prov("rel.tc_over_p.mean", float(vals.mean()), "Mean of t_c/p over A, B, C", f"{S}::main", "derived", "s m2/kg")
    prov("rel.tc_over_p.spread_pct", float(100 * (vals.max() - vals.min()) / vals.mean()), "(max-min)/mean of t_c/p over A, B, C", f"{S}::main", "derived", "%")
    prov("rel.tc_over_p.std_pct", float(100 * vals.std(ddof=1) / vals.mean()), "Sample std / mean of t_c/p over A, B, C", f"{S}::main", "derived", "%")
    # weighted fit t_c = k p through the origin, and chi2
    ps = np.array([tcp[c][3] for c in ("A", "B", "C")]); ts_ = np.array([tcp[c][2] for c in ("A", "B", "C")])
    w = 1 / (errs * ps) ** 2      # sigma of t_c ~ dv * p
    k = float((w * ps * ts_).sum() / (w * ps * ps).sum())
    chi2 = float((w * (ts_ - k * ps) ** 2).sum())
    prov("rel.tc_vs_p.slope_s_m2_per_kg", k, "Weighted least-squares slope of t_c = k p through the origin (A, B, C)", f"{S}::main", "derived", "s m2/kg")
    prov("rel.tc_vs_p.chi2_dof", chi2 / 2, "chi2 per dof (2 dof) of t_c = k p with the propagated errors", f"{S}::main", "derived", "",
         detail="chi2/dof >> 1 means the scatter of t_c/p exceeds the geometric uncertainty: q_film is not exactly body-independent (surface state, end effects)")
    resid = 100 * (ts_ - k * ps) / (k * ps)
    prov("rel.tc_vs_p.max_resid_pct", float(np.max(np.abs(resid))), "Max |t_c - k p| / (k p) over A, B, C", f"{S}::main", "derived", "%",
         detail="residuals A, B, C: " + ", ".join(f"{r:+.1f} %" for r in resid))
    # is the film-boiling flux body-independent? compare plateau Q/A across A, B, C (now with measured n/A)
    plateaus = {c: PROV[f"qa.{c}.plateau_Wm2"]["value"] for c in ("A", "B", "C")}
    pv = np.array(list(plateaus.values()))
    prov("qa.plateau_spread_pct", float(100 * (pv.max() - pv.min()) / pv.mean()), "(max-min)/mean of the film-boiling plateau Q/A across A, B, C with measured geometry",
         f"{S}::main", "derived", "%", [f"qa.{c}.plateau_Wm2" for c in ("A", "B", "C")],
         detail="with the round-1 nominal geometry (same m/A for all) this spread was ~78 %")
    results["tcp"] = {c: list(tcp[c]) for c in tcp}

    # --- balance
    bal = analyse_balance()
    prov("bal.dt_s", float(np.median(np.diff(bal["t"]))), "Balance sampling interval", f"{S}::load_balance", "derived", "s")
    prov("bal.t1_end_s", bal["t_jump_s"], "End of stage 1 = instant of the largest upward step (Cu enters the bath)", f"{S}::balance_stages", "derived", "s",
         ["medicion_balanza.csv"])
    prov("bal.jump_g", bal["st"]["jump_g"], "Upward step in balance reading when the Cu enters (buoyancy of the immersed body)", f"{S}::balance_stages", "derived", "g")
    prov("bal.t3_start_s", bal["t_burst_end_s"], "Start of stage 3 = end of the burst (last 1-s step steeper than -1 g/s)", f"{S}::balance_stages", "derived", "s")
    prov("bal.burst_start_s", bal["t_burst_start_s"], "Start of the violent-boiling burst (collapse of the vapour film)", f"{S}::balance_stages", "derived", "s")
    prov("bal.burst_peak_rate_gs", bal["st"]["burst_peak_rate_gs"], "Most negative smoothed dm/dt during the burst", f"{S}::balance_stages", "derived", "g/s")
    prov("bal.rate_post_immersion_gs", bal["st"]["rate_post_immersion_gs"], "Median smoothed dm/dt 8-30 s after immersion (film boiling, hot Cu)", f"{S}::balance_stages", "derived", "g/s")
    prov("bal.rate_preburst_gs", bal["st"]["rate_preburst_gs"], "Median smoothed dm/dt in the 25 s before the burst (film boiling, cold Cu)", f"{S}::balance_stages", "derived", "g/s")
    prov("bal.power_post_immersion_W", -(bal["st"]["rate_post_immersion_gs"] - bal["s1"]["slope"]) * 1e-3 * L_V_N2, "Cu->bath power just after immersion = (rate - ambient rate) x L_v", f"{S}::main", "derived", "W")
    prov("bal.power_preburst_W", -(bal["st"]["rate_preburst_gs"] - bal["s1"]["slope"]) * 1e-3 * L_V_N2, "Cu->bath power just before the burst", f"{S}::main", "derived", "W")
    prov("bal.burst_dm_g", bal["burst_dm_g"], "Mass evaporated during the burst", f"{S}::analyse_balance", "derived", "g")
    prov("bal.stage2_duration_s", bal["dur_s"], "Duration of stage 2 (immersion to end of burst)", f"{S}::analyse_balance", "derived", "s")
    prov("bal.slope1_gs", bal["s1"]["slope"], f"Stage-1 slope, least squares after dropping {bal['s1']['n_dropped']} glitch points", f"{S}::robust_linfit", "derived", "g/s",
         detail=f"+/- {bal['s1']['slope_err']:.2e} g/s, rms {bal['s1']['rms']:.2f} g, n={bal['s1']['n']}")
    prov("bal.slope1_err_gs", bal["s1"]["slope_err"], "Std error of stage-1 slope", f"{S}::linfit", "derived", "g/s")
    prov("bal.slope3_gs", bal["s3"]["slope"], f"Stage-3 slope, least squares from end of burst to end of file (n={bal['s3']['n']})", f"{S}::robust_linfit", "derived", "g/s",
         detail=f"+/- {bal['s3']['slope_err']:.2e} g/s, rms {bal['s3']['rms']:.2f} g (curved: still-cooling Cu)")
    prov("bal.slope3_err_gs", bal["s3"]["slope_err"], "Std error of stage-3 slope", f"{S}::linfit", "derived", "g/s")
    prov("bal.slope3_tail_gs", bal["tail"]["slope"], "Slope of the last 20 s (asymptotic stage 3)", f"{S}::linfit", "derived", "g/s")
    prov("bal.slope_ratio", bal["s3"]["slope"] / bal["s1"]["slope"], "slope3/slope1", f"{S}::main", "derived", "", ["bal.slope1_gs", "bal.slope3_gs"])
    prov("bal.slope_ratio_tail", bal["tail"]["slope"] / bal["s1"]["slope"], "slope3(last 20 s)/slope1", f"{S}::main", "derived", "")
    prov("bal.dm_stage2_g", bal["dm_raw_g"], "Raw mass drop over stage 2 (post-jump reading minus post-burst reading)", f"{S}::analyse_balance", "derived", "g")
    prov("bal.dm_stage2_net_g", bal["dm_net_g"], "Stage-2 mass drop minus the ambient baseline (slope1 x duration): evaporation attributable to the Cu",
         f"{S}::analyse_balance", "derived", "g", ["bal.dm_stage2_g", "bal.slope1_gs", "bal.stage2_duration_s"])
    Qbal = bal["dm_net_g"] * 1e-3 * L_V_N2
    prov("bal.Q_balance_J", Qbal, "Heat removed = net evaporated mass x L_v (vapour leaving at 77 K)", f"{S}::main", "derived", "J", ["bal.dm_stage2_net_g", "phys.L_v_N2"])
    for cyl in ("A", "B", "C"):
        QCu_c = geoms[cyl]["n_mol"] * H
        prov(f"bal.Q_cu_{cyl}_J", QCu_c, f"Heat released by cylinder {cyl} ({geoms[cyl]['m_kg']*1e3:.1f} g) from 296 K to 77 K = n * integral Cv dT", f"{S}::main", "derived", "J",
             [f"geom.{cyl}.n_mol", "cv.enthalpy_77_296_Jmol"])
        prov(f"bal.Q_ratio_{cyl}", Qbal / QCu_c, f"Q_balance / Q_cu({cyl})", f"{S}::main", "derived", "")
    QCu = geoms["C"]["n_mol"] * H
    prov("bal.Q_cu_J", QCu, "Heat released by cylinder C (the body identified on the balance run) from 296 K to 77 K = n_C * integral Cv dT",
         f"{S}::main", "derived", "J", ["geom.C.n_mol", "cv.enthalpy_77_296_Jmol"])
    prov("bal.Q_ratio", Qbal / QCu, "Q_balance / Q_cu(C)", f"{S}::main", "derived", "")
    m_eff = Qbal / (H / M_CU)
    prov("bal.m_eff_energy_kg", m_eff, "Cu mass that would balance the energy budget (all heat into latent heat)", f"{S}::main", "derived", "kg",
         ["bal.Q_balance_J", "cv.enthalpy_77_296_Jkg"])
    Tv = 0.5 * (296 + 77)
    m_eff_hi = bal["dm_net_g"] * 1e-3 * (L_V_N2 + CP_N2_VAP * (Tv - 77)) / (H / M_CU)
    prov("bal.m_eff_energy_upper_kg", m_eff_hi, "Same, upper bound if vapour leaves superheated to (296+77)/2 K", f"{S}::main", "derived", "kg")
    V_b = bal["st"]["jump_g"] * 1e-3 / RHO_LN2
    prov("bal.V_buoyancy_m3", V_b, "Displaced LN2 volume implied by the buoyancy jump", f"{S}::main", "derived", "m3", ["bal.jump_g", "phys.rho_LN2"])
    prov("bal.m_eff_buoy_kg", V_b * RHO_CU, "Cu mass implied by the buoyancy jump if fully immersed", f"{S}::main", "derived", "kg", ["bal.V_buoyancy_m3", "phys.rho_Cu"])
    # which cylinder was on the balance? nearest measured mass to the two independent estimates
    m_meas = {c: geoms[c]["m_kg"] for c in ("A", "B", "C")}
    m_bal = 0.5 * (m_eff + V_b * RHO_CU)
    best = min(m_meas, key=lambda c: abs(m_meas[c] - m_bal))
    prov("bal.body_identified", best, "Cylinder on the balance run = the one whose measured mass is closest to the mean of the energy and buoyancy estimates",
         f"{S}::main", "derived", "", ["bal.m_eff_energy_kg", "bal.m_eff_buoy_kg", "geom.A.m_kg", "geom.B.m_kg", "geom.C.m_kg"],
         detail=f"mean estimate {m_bal:.3f} kg; measured A {m_meas['A']:.3f}, B {m_meas['B']:.3f}, C {m_meas['C']:.3f} kg")
    prov("bal.m_bal_mean_kg", m_bal, "Mean of the energy-budget and buoyancy mass estimates", f"{S}::main", "derived", "kg")
    prov("bal.m_buoy_over_mC", V_b * RHO_CU / m_meas["C"], "Buoyancy mass estimate / measured m_C", f"{S}::main", "derived", "")
    prov("bal.m_energy_over_mC", m_eff / m_meas["C"], "Energy-budget mass estimate / measured m_C", f"{S}::main", "derived", "")
    prov("bal.V_C_m3", geoms["C"]["vol_m3"], "Geometric volume of cylinder C (pi r^2 h)", f"{S}::geometry", "derived", "m3", ["geom.C.h_m", "geom.C.d_m"])
    prov("bal.V_buoy_over_V_C", V_b / geoms["C"]["vol_m3"], "Displaced volume from the buoyancy step / geometric volume of C", f"{S}::main", "derived", "")
    # Q/A two ways, absolute (needs the body = C and its measured area): balance power / A_C vs calorimetric Q/A of run C
    A_C = geoms["C"]["area_m2"]
    P0 = PROV["bal.power_post_immersion_W"]["value"]; P1 = PROV["bal.power_preburst_W"]["value"]
    qa_C = runs["C"]["qa"]; Ts_C = runs["C"]["T_s"]; ok_C = runs["C"]["t"] >= runs["C"]["t0"] + 8
    qa_hot = float(np.median(qa_C[ok_C & (Ts_C > 230) & (Ts_C < 290)]))
    qa_cold = float(np.median(qa_C[ok_C & (Ts_C > runs["C"]["tc"]["Thi_K"] + 10) & (Ts_C < runs["C"]["tc"]["Thi_K"] + 40)]))
    prov("bal.QA_post_immersion_Wm2", P0 / A_C, "Balance-derived Q/A 8-30 s after immersion = (evaporation rate - ambient rate) L_v / A_C", f"{S}::main", "derived", "W/m2",
         ["bal.power_post_immersion_W", "geom.C.area_m2"])
    prov("bal.QA_preburst_Wm2", P1 / A_C, "Balance-derived Q/A in the 25 s before the burst, / A_C", f"{S}::main", "derived", "W/m2", ["bal.power_preburst_W", "geom.C.area_m2"])
    prov("qa.C.calorimetric_hot_Wm2", qa_hot, "Calorimetric Q/A of run C (eq. 1), median for 230<T<290 K (just after immersion)", f"{S}::heat_flux", "derived", "W/m2")
    prov("qa.C.calorimetric_cold_Wm2", qa_cold, "Calorimetric Q/A of run C, median in the 10-40 K above the drop band (just before collapse)", f"{S}::heat_flux", "derived", "W/m2")
    prov("bal.QA_ratio_hot", (P0 / A_C) / qa_hot, "Balance Q/A / calorimetric Q/A just after immersion (two independent ways of getting Q/A)", f"{S}::main", "derived", "",
         ["bal.QA_post_immersion_Wm2", "qa.C.calorimetric_hot_Wm2"])
    prov("bal.QA_ratio_cold", (P1 / A_C) / qa_cold, "Balance Q/A / calorimetric Q/A just before the collapse", f"{S}::main", "derived", "",
         ["bal.QA_preburst_Wm2", "qa.C.calorimetric_cold_Wm2"])
    prov("bal.stage2_vs_tc_C_s", bal["dur_s"] - (runs["C"]["tc"]["t_s"] - runs["C"]["t0"]),
         "Stage-2 duration (immersion to burst end) minus t_c of the C temperature run from immersion", f"{S}::main", "derived", "s",
         ["bal.stage2_duration_s", "tc.C.t_from_immersion_s"], detail="the balance run and the temperature run of C are different immersions; a difference of tens of s is a repeatability figure, not a contradiction")
    results["bal"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in bal.items()}

    # --- thermocouple consistency (auxiliary)
    for cyl in ("B", "C"):
        r = runs[cyl]
        Tk = typeK_T_from_V(r["V"])
        good = ~r["bad"]
        prov(f"tc_check.{cyl}.max_abs_dev_K", float(np.max(np.abs(Tk[good] - r["T_raw"][good]))),
             f"Max |T(NIST type-K inverse poly, coefficients from memory) - T(csv)| over non-spike samples, run {cyl}",
             f"{S}::typeK_T_from_V", "derived", "K", detail="auxiliary only; NIST coefficients not verified against the table")
        prov(f"tc_check.{cyl}.V_at_77K_mV", float(1e3 * np.median(r["V"][r["T_raw"] < 78])), f"Median thermocouple emf at the 77 K plateau, run {cyl}",
             f"{S}::main", "derived", "mV")

    # --- write
    # load-and-update: other roles (worker 2: phys.*, guide.*, assume.*, qual.*) also write entries
    # into provenance.json; keep theirs, overwrite only the keys produced here.
    ppath = os.path.join(OUT, "provenance.json")
    merged = {}
    if os.path.exists(ppath):
        try:
            with open(ppath, encoding="utf-8") as fh:
                merged = json.load(fh)
        except json.JSONDecodeError:
            merged = {}
    merged.update(PROV)
    with open(ppath, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh)
    make_figures(runs, bal)

    # console summary
    print(f"Cv_E(300)={cv300:.3f}  Cv_E(77)={cv77:.3f}  Debye(300)={d300:.3f}  Debye(77)={d77:.3f}  literal(300)={cv_einstein_literal(300.0):.2f}")
    print(f"H(77->296)={H:.1f} J/mol = {H/M_CU:.0f} J/kg")
    for cyl, r in runs.items():
        tc = r["tc"]
        print(f"{cyl:3s} outliers={int(r['bad'].sum()):2d} t0={r['t0']:6.1f}  t_c={tc['t_s']:6.1f} s (from imm. {tc['t_s']-r['t0']:6.1f})  T_c={tc['T_K']:6.1f} K "
              f"band [{tc['Tlo_K']:.1f},{tc['Thi_K']:.1f}] K  rate_max={tc['rate_max_Ks']:.2f} K/s plateau={tc['plateau_rate_Ks']:.2f} ratio={tc['peak_over_plateau']:.1f} detected={tc['detected']}")
    print("balance:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in bal.items() if k not in ("t", "m", "s1", "s3", "tail", "st")})
    print("s1", bal["s1"], "\ns3", bal["s3"], "\ntail", bal["tail"])
    print(f"Q_bal={Qbal:.0f} J  Q_cu(C)={QCu:.0f} J  m_eff={m_eff:.3f} kg (upper {m_eff_hi:.3f})  m_buoy={V_b*RHO_CU:.3f} kg")
    print(f"provenance entries written by analysis.py: {len(PROV)}; total in file: {len(merged)}")


if __name__ == "__main__":
    main()
