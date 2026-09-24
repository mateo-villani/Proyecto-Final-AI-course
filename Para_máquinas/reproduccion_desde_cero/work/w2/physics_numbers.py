"""Worker-2 (physics) numbers for out/notes.tex.

Every number here is either a tabulated constant (type 'source', citation given), a value
copied from the guide (type 'source', page given), an explicit assumption (type 'derivation',
flagged ASSUMED), or a one-line derivation from those (type 'script', reproduce = this file).
Writes work/w2/provenance_physics.json; merge_provenance.py folds it into out/provenance.json
without overwriting keys that worker 1 already wrote.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.abspath(os.path.join(HERE, "..", ".."))
DATOS = os.path.join(JOB, "datos")
ME = "work/w2/physics_numbers.py"

P = {}


def src(key, value, statement, cite, unit=""):
    P[key] = {"statement": f"{statement} = {value} {unit}".strip(), "type": "source",
              "reproduce": cite, "value": value, "unit": unit, "origin": "literature"}


def der(key, value, statement, func, inputs, unit=""):
    P[key] = {"statement": f"{statement} = {value} {unit}".strip(), "type": "script",
              "reproduce": f"{ME}::{func}", "detail": f"inputs: {inputs}",
              "value": value, "unit": unit, "origin": "derived"}


def guide(key, value, statement, where, unit=""):
    P[key] = {"statement": f"{statement} = {value} {unit}".strip(), "type": "source",
              "reproduce": f"guia/Leidenfrost-guia.pdf, {where}", "value": value, "unit": unit,
              "detail": "taken from the guide as-is, not re-derived", "origin": "guide"}


def assume(key, value, statement, where, unit=""):
    P[key] = {"statement": f"ASSUMED {statement} = {value} {unit}".strip(), "type": "derivation",
              "reproduce": f"assumption, stated in {where}", "value": value, "unit": unit, "origin": "assumed"}


# ---------------- constants (tabulated) ----------------
src("phys.R", 8.314, "gas constant R", "CODATA 2018", "J/(mol K)")
src("phys.M_Cu", 63.546e-3, "molar mass of Cu", "IUPAC atomic weight 63.546 g/mol", "kg/mol")
src("phys.rho_Cu", 8960.0, "density of Cu at 293 K", "CRC Handbook of Chemistry and Physics", "kg/m^3")
src("phys.k_Cu", 400.0, "thermal conductivity of Cu at 300 K (rises to ~500 W/mK near 77 K)",
    "CRC Handbook; Touloukian TPRC vol. 1", "W/(m K)")
src("phys.c_Cu", 385.0, "specific heat of Cu at 300 K", "CRC Handbook (0.385 J/gK)", "J/(kg K)")
src("phys.T_sat_K", 77.0, "saturation temperature of N2 at 1 atm (guide uses 77 K; NIST: 77.36 K)",
    "guia/Leidenfrost-guia.pdf p.2; NIST WebBook", "K")
src("phys.L_v_N2", 199.0e3, "latent heat of vaporisation of N2 at 1 atm",
    "NIST WebBook (198.8 kJ/kg at 77.35 K)", "J/kg")
src("phys.rho_LN2", 807.0, "density of liquid N2 at 77 K", "NIST WebBook", "kg/m^3")
src("phys.k_N2vap", 7.5e-3, "thermal conductivity of N2 vapour at ~100 K, 1 atm",
    "NIST WebBook / Touloukian", "W/(m K)")
src("phys.k_N2liq", 0.14, "thermal conductivity of liquid N2 at 77 K", "NIST WebBook", "W/(m K)")
src("phys.h_film_Wm2K", 150.0,
    "typical film-boiling heat-transfer coefficient of LN2 on cm-scale bodies (order of magnitude; range ~100-300)",
    "Listerman et al. Am.J.Phys. 54, 554 (1986); Frederking & Clark (1963) film-boiling correlation, order of magnitude only",
    "W/(m^2 K)")
src("phys.h_nucleate_Wm2K", 1.0e4,
    "order-of-magnitude nucleate-boiling coefficient of LN2 near the critical heat flux",
    "Brentari & Smith (1965) LN2 pool-boiling correlations, order of magnitude only", "W/(m^2 K)")
src("phys.qmax_LN2_Wm2", 1.5e5, "critical (peak nucleate) heat flux of LN2 at 1 atm, order of magnitude (literature 1-2e5)",
    "Brentari & Smith (1965); Kutateladze correlation", "W/m^2")
src("phys.seebeck_K_uVK", 41.0, "type K (chromel-alumel) Seebeck coefficient near room temperature",
    "NIST ITS-90 thermocouple tables (type K, ~41 uV/K at 20 C)", "uV/K")
src("phys.emf_K_77K_mV", -5.8, "type K EMF at -196 C with 0 C reference (NIST: -5.73 mV at -190 C, -5.89 mV at -200 C)",
    "NIST ITS-90 type K table, interpolated", "mV")
src("phys.seebeck_K_77K_uVK", 16.0, "type K Seebeck coefficient near 77 K (table slope between -200 and -190 C)",
    "NIST ITS-90 type K table", "uV/K")
src("phys.dTdt_tc_typ_s", 0.5, "typical time constant of an exposed, welded ~0.5 mm type-K junction in a liquid",
    "Omega thermocouple response-time tables (order of magnitude)", "s")
src("phys.pt100_alpha", 3.85e-3, "Pt100 temperature coefficient (IEC 60751)", "IEC 60751", "1/K")
src("phys.pt100_R77", 20.0, "Pt100 resistance at 77 K (Callendar-Van Dusen, ~20 ohm)",
    "IEC 60751, Callendar-Van Dusen A,B,C coefficients", "ohm")

# ---------------- guide values ----------------
guide("guide.thetaD_K", 315.0, "Debye temperature of Cu used by the guide", "p.3, after eq. (5)", "K")
guide("guide.a", 0.77, "eq. (5) coefficient a", "p.3", "")
guide("guide.b", 0.26, "eq. (5) coefficient b", "p.3", "")
guide("guide.c", 9.17, "eq. (5) coefficient c", "p.3", "")
guide("guide.h_m", 0.10, "nominal cylinder length", "p.3, 'aproximadamente 10 cm de longitud'", "m")
guide("guide.d_m", 0.04, "nominal cylinder diameter", "p.3, 'y 4 cm de diametro'", "m")
guide("guide.m_kg", 1.0, "nominal cylinder mass", "p.3, 'aproximadamente 1 Kg'", "kg")
guide("guide.CpCv_max_pct", 3.0, "max (Cp-Cv)/Cv in 77-300 K, at 300 K", "p.2 after eq. (2)", "%")
guide("guide.gamma_max_pct", 2.5, "max electronic contribution gamma*T/Cv in 70-300 K, at 70 K", "p.2 after eq. (3)", "%")
guide("guide.gamma_cal", 1.7e-4, "electronic gamma of Cu, midpoint of the (1.60-1.80)e-4 range quoted", "p.2 after eq. (3)", "cal/(mol K^2)")

# ---------------- assumptions ----------------
assume("assume.adc_fs_V", 10.0, "ADC input range +-10 V (MPLI datasheet not in the sources)", "notes.tex sec. 1", "V")
assume("assume.adc_bits", 12, "ADC resolution 12 bit (MPLI datasheet not in the sources)", "notes.tex sec. 1", "bit")
assume("assume.film_thickness_m", 12e-6, "thickness of one turn of cling film (typical household PE/PVC; not measured)", "notes.tex sec. 5", "m")
assume("assume.film_k", 0.2, "thermal conductivity of the film (LDPE/PVC)", "notes.tex sec. 5", "W/(m K)")
assume("assume.eps_Cu", 0.05, "emissivity of the Cu surface (polished 0.03, lightly oxidised ~0.1)", "notes.tex sec. 6", "")


# ---------------- measured geometry (human direction, inbox.jsonl 2026-09-18) ----------------
# Same numbers as work/analysis.py::GEOM (single source of truth is the inbox; both scripts copy it).
MEAS = {"A": (0.094, 0.038, 0.9410), "B": (0.049, 0.022, 0.1658), "C": (0.027, 0.035, 0.2262)}
for cyl, (h, d, m) in MEAS.items():
    P[f"qual.meas_{cyl}_h_m"] = {"statement": f"measured height of cylinder {cyl} = {h} m (+/- 0.001)", "type": "source",
                                 "reproduce": "inbox.jsonl (human direction, 2026-09-18)", "value": h, "unit": "m", "origin": "measured"}
    P[f"qual.meas_{cyl}_d_m"] = {"statement": f"measured diameter of cylinder {cyl} = {d} m (+/- 0.001)", "type": "source",
                                 "reproduce": "inbox.jsonl (human direction, 2026-09-18)", "value": d, "unit": "m", "origin": "measured"}
    P[f"qual.meas_{cyl}_m_kg"] = {"statement": f"measured mass of cylinder {cyl} = {m} kg (+/- 0.0001)", "type": "source",
                                  "reproduce": "inbox.jsonl (human direction, 2026-09-18)", "value": m, "unit": "kg", "origin": "measured"}


# ---------------- derived: geometry & thermal ----------------
def geometry(h, d, m):
    r = d / 2
    V = math.pi * r ** 2 * h
    A = 2 * math.pi * r ** 2 + 2 * math.pi * r * h
    return dict(V=V, A=A, m_from_rho=P["phys.rho_Cu"]["value"] * V,
                n=m / P["phys.M_Cu"]["value"], p=m / A, Lc=V / A, r=r, m=m, h=h, d=d)


# guide nominal: kept as a remark only ("~10 cm, 4 cm, 1 kg"); NOT used in any argument below
g_nom = geometry(P["guide.h_m"]["value"], P["guide.d_m"]["value"], P["guide.m_kg"]["value"])
der("qual.V_nom_m3", round(g_nom["V"], 6), "volume of the guide's nominal 10 cm x 4 cm cylinder (remark only; measured geometry is used everywhere else)", "geometry", "guide.h_m, guide.d_m", "m^3")
der("qual.A_nom_m2", round(g_nom["A"], 5), "total surface area of the guide's nominal cylinder (remark only)", "geometry", "guide.h_m, guide.d_m", "m^2")
der("qual.m_from_rho_kg", round(g_nom["m_from_rho"], 3), "mass implied by rho_Cu x nominal volume (consistency remark on the guide's '~1 kg'; not used)", "geometry", "phys.rho_Cu, qual.V_nom_m3", "kg")
der("qual.p_nom_kgm2", round(g_nom["p"], 1), "p = m/A for the guide's nominal cylinder (remark only)", "geometry", "guide.m_kg, qual.A_nom_m2", "kg/m^2")

G = {cyl: geometry(*MEAS[cyl]) for cyl in MEAS}
for cyl, gg in G.items():
    der(f"qual.A_{cyl}_m2", round(gg["A"], 5), f"total surface area (2 caps + lateral) of cylinder {cyl}, measured h, d", "geometry", f"qual.meas_{cyl}_h_m, qual.meas_{cyl}_d_m", "m^2")
    der(f"qual.V_{cyl}_m3", float(f"{gg['V']:.4g}"), f"volume of cylinder {cyl}", "geometry", f"qual.meas_{cyl}_h_m, qual.meas_{cyl}_d_m", "m^3")
    der(f"qual.n_{cyl}_mol", round(gg["n"], 3), f"moles of Cu in cylinder {cyl}", "geometry", f"qual.meas_{cyl}_m_kg, phys.M_Cu", "mol")
    der(f"qual.p_{cyl}_kgm2", round(gg["p"], 1), f"p = m/A for cylinder {cyl}", "geometry", f"qual.meas_{cyl}_m_kg, qual.A_{cyl}_m2", "kg/m^2")
    der(f"qual.Lc_{cyl}_m", round(gg["Lc"], 5), f"characteristic length V/A of cylinder {cyl}", "geometry", f"qual.V_{cyl}_m3, qual.A_{cyl}_m2", "m")
    der(f"qual.rho_mV_{cyl}_kgm3", round(gg["m"] / gg["V"]), f"m/V of cylinder {cyl} (solid Cu 8960; lower = thermocouple hole / caliper rounding)", "geometry", f"qual.meas_{cyl}_m_kg, qual.V_{cyl}_m3", "kg/m^3")
g = G["A"]   # A: largest radius -> worst case for Biot and internal gradients; longest run


def thermal(gg):
    k, rho, c = P["phys.k_Cu"]["value"], P["phys.rho_Cu"]["value"], P["phys.c_Cu"]["value"]
    alpha = k / (rho * c)
    q_film = P["phys.h_film_Wm2K"]["value"] * (296 - 77)
    return dict(alpha=alpha, tau_diff=gg["r"] ** 2 / alpha,
                Bi_film=P["phys.h_film_Wm2K"]["value"] * gg["Lc"] / k,
                Bi_nuc=P["phys.h_nucleate_Wm2K"]["value"] * gg["Lc"] / k,
                tau_cool_film=gg["p"] * c / P["phys.h_film_Wm2K"]["value"],
                q_film=q_film,
                dT_internal=q_film * gg["r"] / (2 * k),   # cylinder, uniform surface flux, centre-to-surface
                dT_internal_peak=P["phys.qmax_LN2_Wm2"]["value"] * gg["r"] / (2 * k))


t = thermal(g)
der("qual.alpha_Cu_m2s", float(f"{t['alpha']:.3g}"), "thermal diffusivity of Cu, k/(rho c)", "thermal", "phys.k_Cu, phys.rho_Cu, phys.c_Cu", "m^2/s")
der("qual.tau_diff_s", round(t["tau_diff"], 1), "radial diffusion time r^2/alpha of cylinder A (r = 1.9 cm, the largest)", "thermal", "qual.alpha_Cu_m2s, qual.meas_A_d_m", "s")
der("qual.Bi_film", float(f"{t['Bi_film']:.2g}"), "Biot number h Lc/k in film boiling (h=150 W/m2K), cylinder A (largest Lc)", "thermal", "phys.h_film_Wm2K, qual.Lc_A_m, phys.k_Cu", "")
der("qual.Bi_nucleate", float(f"{t['Bi_nuc']:.2g}"), "Biot number in nucleate boiling (h=1e4 W/m2K), i.e. during the collapse, cylinder A", "thermal", "phys.h_nucleate_Wm2K, qual.Lc_A_m, phys.k_Cu", "")
der("qual.q_film_Wm2", round(t["q_film"]), "film-boiling flux h (296-77) K with h=150 W/m2K", "thermal", "phys.h_film_Wm2K", "W/m^2")
der("qual.dT_internal_film_K", round(t["dT_internal"], 3), "centre-to-surface temperature difference q r/(2k) at the film-boiling flux, cylinder A", "thermal", "qual.q_film_Wm2, qual.meas_A_d_m, phys.k_Cu", "K")
der("qual.dT_internal_peak_K", round(t["dT_internal_peak"], 2), "centre-to-surface difference at the LN2 critical heat flux (worst case, during collapse), cylinder A", "thermal", "phys.qmax_LN2_Wm2, qual.meas_A_d_m, phys.k_Cu", "K")
for cyl, gg in G.items():
    der(f"qual.tau_cool_film_{cyl}_s", round(thermal(gg)["tau_cool_film"]), f"lumped cooling time scale p c/h in film boiling, cylinder {cyl}", "thermal", f"qual.p_{cyl}_kgm2, phys.c_Cu, phys.h_film_Wm2K", "s")
der("qual.tau_cool_film_s", round(t["tau_cool_film"]), "lumped cooling time scale p c/h in film boiling, cylinder A", "thermal", "qual.p_A_kgm2, phys.c_Cu, phys.h_film_Wm2K", "s")

# ---------------- derived: Einstein Cv, and the eq.(4) typo check ----------------
def einstein(T, thE):
    x = thE / T
    return 3 * P["phys.R"]["value"] * x ** 2 * math.exp(x) / (math.exp(x) - 1) ** 2


def thetaE(T):
    a, b, c, tD = (P[k]["value"] for k in ("guide.a", "guide.b", "guide.c", "guide.thetaD_K"))
    return tD * (a + b * math.exp(-c * T / tD))


def eq4_literal(T):
    """eq. (4) exactly as printed: (thetaE/T)^2 prefactor but exp(thetaD/T) in the exponentials."""
    tD = P["guide.thetaD_K"]["value"]
    x = tD / T
    return 3 * P["phys.R"]["value"] * (thetaE(T) / T) ** 2 * math.exp(x) / (math.exp(x) - 1) ** 2


def debye(T):
    tD = P["guide.thetaD_K"]["value"]
    lam = tD / T
    ts = np.linspace(1e-9, lam, 20001)
    D = 3 / lam ** 3 * np.trapezoid(ts ** 3 / np.expm1(ts), ts)
    return 3 * P["phys.R"]["value"] * (4 * D - 3 * lam / math.expm1(lam))


def energy_296_77(n, cv):
    Ts = np.linspace(77, 296, 2000)
    return n * np.trapezoid([cv(T) for T in Ts], Ts)


der("qual.thetaE_300K", round(thetaE(300), 1), "Einstein temperature from eq. (5) at 300 K", "thetaE", "guide.a,b,c,thetaD_K", "K")
der("qual.thetaE_77K", round(thetaE(77), 1), "Einstein temperature from eq. (5) at 77 K", "thetaE", "guide.a,b,c,thetaD_K", "K")
der("qual.Cv_einstein_300K", round(einstein(300, thetaE(300)), 2), "Einstein Cv at 300 K with theta_E everywhere in eq. (4)", "einstein", "qual.thetaE_300K, phys.R", "J/(mol K)")
der("qual.Cv_einstein_77K", round(einstein(77, thetaE(77)), 2), "Einstein Cv at 77 K with theta_E everywhere in eq. (4)", "einstein", "qual.thetaE_77K, phys.R", "J/(mol K)")
der("qual.Cv_debye_300K", round(debye(300), 2), "Debye Cv at 300 K (thetaD = 315 K), cross-check", "debye", "guide.thetaD_K, phys.R", "J/(mol K)")
der("qual.Cv_debye_77K", round(debye(77), 2), "Debye Cv at 77 K (thetaD = 315 K), cross-check", "debye", "guide.thetaD_K, phys.R", "J/(mol K)")
der("qual.eq4_literal_300K", round(eq4_literal(300), 2),
    "eq. (4) read literally (exp(thetaD/T) with (thetaE/T)^2 prefactor) at 300 K -- violates Dulong-Petit, so the printed thetaD is a typo for thetaE",
    "eq4_literal", "guide.thetaD_K, qual.thetaE_300K", "J/(mol K)")
der("qual.dulong_petit", round(3 * P["phys.R"]["value"], 2), "Dulong-Petit limit 3R", "-", "phys.R", "J/(mol K)")
der("qual.einstein_vs_debye_77K_pct", round(100 * (einstein(77, thetaE(77)) / debye(77) - 1), 1), "relative deviation of Einstein(eq.4-5) from Debye at 77 K", "einstein,debye", "", "%")
der("qual.einstein_vs_debye_300K_pct", round(100 * (einstein(300, thetaE(300)) / debye(300) - 1), 2), "relative deviation of Einstein(eq.4-5) from Debye at 300 K", "einstein,debye", "", "%")
E_mol = energy_296_77(1.0, lambda T: einstein(T, thetaE(T)))
der("qual.H_296_77_Jmol", round(E_mol, 1), "integral of Einstein Cv dT from 77 K to 296 K, per mole", "energy_296_77", "qual.Cv_einstein_*", "J/mol")
E_cyl = {}
for cyl, gg in G.items():
    E_cyl[cyl] = energy_296_77(gg["n"], lambda T: einstein(T, thetaE(T)))
    der(f"qual.Q_cu_296_77_kJ_{cyl}", round(E_cyl[cyl] / 1e3, 2), f"heat released by cylinder {cyl} cooling 296 -> 77 K, n * integral Cv_Einstein dT", "energy_296_77", f"qual.n_{cyl}_mol, qual.Cv_einstein_*", "kJ")
    der(f"qual.m_N2_boiled_g_{cyl}", round(E_cyl[cyl] / P["phys.L_v_N2"]["value"] * 1e3), f"LN2 mass that the heat of cylinder {cyl} evaporates, Q / L_v", "energy_296_77", f"qual.Q_cu_296_77_kJ_{cyl}, phys.L_v_N2", "g")
E_ein = E_cyl["A"]
der("qual.Q_cu_296_77_kJ", round(E_ein / 1e3, 1), "heat released by cylinder A (941 g) cooling 296 -> 77 K", "energy_296_77", "qual.n_A_mol, qual.Cv_einstein_*", "kJ")
der("qual.m_N2_boiled_g", round(E_ein / P["phys.L_v_N2"]["value"] * 1e3), "LN2 mass that the heat of cylinder A evaporates, Q / L_v", "energy_296_77", "qual.Q_cu_296_77_kJ, phys.L_v_N2", "g")
der("qual.gamma_T_over_Cv_77K_pct", round(100 * P["guide.gamma_cal"]["value"] * 4.184 * 77 / einstein(77, thetaE(77)), 2), "electronic gamma*T / Cv at 77 K, own check of the guide's 2.5 %", "-", "guide.gamma_cal, qual.Cv_einstein_77K", "%")
der("qual.Cv_ratio_77_300", round(einstein(77, thetaE(77)) / einstein(300, thetaE(300)), 3), "Cv(77 K)/Cv(300 K), Einstein", "einstein", "", "")


# ---------------- derived from the raw data: thermocouple calibration, signal levels, data quality ----------------
RUNS = [("A", "CilindroA_sumergido.csv"), ("B", "CilindroB_sumergido.csv"), ("C", "CilindroC_sumergido.csv"),
        ("C1", "cilindroC(aislado con 1 vuelta).csv"), ("C3", "cilindroC(aislado con 3 vueltas).csv")]


def tc_calibration():
    """Local slope dT/dV of the acquisition's own calibration near room T and near 80 K, spike count,
    signal extremes.  Rows outside 70-310 K are physically impossible and counted as spikes."""
    out = {}
    for lab, f in RUNS:
        d = np.genfromtxt(os.path.join(DATOS, f), delimiter=",", skip_header=1)
        t, V, TC, TK = d.T
        bad = (TK < 70) | (TK > 310)
        res = dict(n_rows=len(t), n_spikes=int(bad.sum()), t_spikes=[round(float(x), 1) for x in t[bad]],
                   V_max_mV=float(V[~bad].max() * 1e3), V_min_mV=float(V[~bad].min() * 1e3),
                   T_min_K=float(TK[~bad].min()), T_max_K=float(TK[~bad].max()),
                   dt_s=float(np.median(np.diff(t))), duration_s=float(t[-1] - t[0]),
                   V_step_uV=float(np.min(np.diff(np.unique(V))) * 1e6))
        for name, mm in [("hi", (TK > 290) & ~bad), ("lo", (TK > 78) & (TK < 90) & ~bad)]:
            if mm.sum() > 3:
                res["slope_" + name] = float(np.polyfit(V[mm], TC[mm], 1)[0])   # K/V
        out[lab] = res
    return out


cal = tc_calibration()
c = cal["A"]
der("qual.tc_sens_hi_uVK", round(1e6 / c["slope_hi"], 1), "thermocouple sensitivity implied by the acquisition calibration near 295 K (run A): 1/(dT/dV)", "tc_calibration", "datos/CilindroA_sumergido.csv", "uV/K")
der("qual.tc_sens_lo_uVK", round(1e6 / c["slope_lo"], 1), "thermocouple sensitivity implied by the acquisition calibration at 78-90 K (run A)", "tc_calibration", "datos/CilindroA_sumergido.csv", "uV/K")
der("qual.V_max_mV_A", round(c["V_max_mV"], 3), "largest thermocouple EMF recorded in run A (room temperature, 0 C reference)", "tc_calibration", "datos/CilindroA_sumergido.csv", "mV")
der("qual.V_min_mV_A", round(c["V_min_mV"], 3), "smallest (most negative) valid thermocouple EMF recorded in run A", "tc_calibration", "datos/CilindroA_sumergido.csv", "mV")
der("qual.T_min_K_A", round(c["T_min_K"], 1), "lowest temperature recorded in run A", "tc_calibration", "datos/CilindroA_sumergido.csv", "K")
der("qual.duration_s_A", round(c["duration_s"]), "duration of run A", "tc_calibration", "datos/CilindroA_sumergido.csv", "s")
der("qual.dt_sample_s", round(c["dt_s"], 3), "median sampling interval of the temperature files", "tc_calibration", "datos/CilindroA_sumergido.csv", "s")
der("qual.V_step_uV_A", round(c["V_step_uV"], 3), "smallest voltage step between distinct recorded values in run A (effective resolution referred to the thermocouple)", "tc_calibration", "datos/CilindroA_sumergido.csv", "uV")
der("qual.T_step_K_A", round(c["V_step_uV"] * 1e-6 * c["slope_hi"], 4), "temperature resolution implied by that voltage step near 295 K", "tc_calibration", "datos/CilindroA_sumergido.csv", "K")
for lab, f in RUNS:
    der(f"qual.n_spikes_{lab}", cal[lab]["n_spikes"], f"rows with T outside 70-310 K (impossible values = acquisition spikes) in run {lab}; at t = {cal[lab]['t_spikes']} s", "tc_calibration", f"datos/{f}", "rows")
    der(f"qual.n_rows_{lab}", cal[lab]["n_rows"], f"rows in run {lab}", "tc_calibration", f"datos/{f}", "rows")
    der(f"qual.duration_s_{lab}", round(cal[lab]["duration_s"]), f"duration of run {lab}", "tc_calibration", f"datos/{f}", "s")
    der(f"qual.T_min_K_{lab}", round(cal[lab]["T_min_K"], 1), f"lowest valid temperature in run {lab}", "tc_calibration", f"datos/{f}", "K")


def effusivity():
    """Contact temperature of two semi-infinite bodies: T_i = (e1 T1 + e2 T2)/(e1 + e2), e = sqrt(k rho c)."""
    e_cu = math.sqrt(P["phys.k_Cu"]["value"] * P["phys.rho_Cu"]["value"] * P["phys.c_Cu"]["value"])
    e_pe = math.sqrt(P["assume.film_k"]["value"] * 950 * 1900)          # LDPE: rho 950, c 1900
    e_ln2 = math.sqrt(P["phys.k_N2liq"]["value"] * P["phys.rho_LN2"]["value"] * 2040)   # c_p LN2 2040 J/kgK
    Ti_cu = (e_cu * 296 + e_ln2 * 77) / (e_cu + e_ln2)
    Ti_pe = (e_pe * 296 + e_ln2 * 77) / (e_pe + e_ln2)
    return dict(e_cu=e_cu, e_pe=e_pe, e_ln2=e_ln2, Ti_cu=Ti_cu, Ti_pe=Ti_pe)


e = effusivity()
der("qual.effusivity_Cu", round(e["e_cu"]), "thermal effusivity sqrt(k rho c) of Cu", "effusivity", "phys.k_Cu, phys.rho_Cu, phys.c_Cu", "J/(m^2 K s^0.5)")
der("qual.effusivity_film", round(e["e_pe"]), "thermal effusivity of the polymer film (k=0.2, rho=950, c=1900 assumed)", "effusivity", "assume.film_k", "J/(m^2 K s^0.5)")
der("qual.effusivity_LN2", round(e["e_ln2"]), "thermal effusivity of liquid N2 (k=0.14, rho=807, c=2040)", "effusivity", "phys.k_N2liq, phys.rho_LN2", "J/(m^2 K s^0.5)")
der("qual.T_contact_Cu_LN2_K", round(e["Ti_cu"], 1), "instantaneous contact temperature Cu(296 K)/LN2(77 K) on liquid touch-down", "effusivity", "qual.effusivity_Cu, qual.effusivity_LN2", "K")
der("qual.T_contact_film_LN2_K", round(e["Ti_pe"], 1), "instantaneous contact temperature polymer film(296 K)/LN2(77 K)", "effusivity", "qual.effusivity_film, qual.effusivity_LN2", "K")


def flux_estimates():
    """Mean heat flux implied by the run durations, measured geometry of the body of each run."""
    body = {"A": "A", "B": "B", "C": "C", "C1": "C", "C3": "C"}
    return {lab: E_cyl[body[lab]] / (G[body[lab]]["A"] * cal[lab]["duration_s"]) for lab, _ in RUNS}


fl = flux_estimates()
der("qual.mean_flux_A_Wm2", round(fl["A"]), "mean flux Q/(A t_run) for run A with measured geometry (whole run, incl. plateau)", "flux_estimates", "qual.Q_cu_296_77_kJ_A, qual.A_A_m2, qual.duration_s_A", "W/m^2")
der("qual.flux_C1_10s_Wm2", round(E_cyl["C"] / (G["C"]["A"] * 10)), "mean flux needed to cool cylinder C (measured 226 g, 48.9 cm2) 296->77 K in 10 s (what the 1-turn run shows); compare the LN2 critical heat flux", "flux_estimates", "qual.Q_cu_296_77_kJ_C, qual.A_C_m2", "W/m^2")
der("qual.flux_C1_over_CHF", round(E_cyl["C"] / (G["C"]["A"] * 10) / P["phys.qmax_LN2_Wm2"]["value"], 1), "ratio of that flux to the LN2 critical heat flux", "flux_estimates", "qual.flux_C1_10s_Wm2, phys.qmax_LN2_Wm2", "")


def adc_numbers():
    fs_V, bits = P["assume.adc_fs_V"]["value"], P["assume.adc_bits"]["value"]
    lsb_mV = 2 * fs_V / 2 ** bits * 1e3
    span_mV = P["phys.seebeck_K_uVK"]["value"] * 1e-3 * (296 - 273) - P["phys.emf_K_77K_mV"]["value"]
    return dict(lsb_mV=lsb_mV, span_mV=span_mV, counts_unamp=span_mV / lsb_mV,
                gain_for_1000_counts=1000 * lsb_mV / span_mV)


a = adc_numbers()
der("qual.adc_lsb_mV", round(a["lsb_mV"], 2), "LSB of the assumed 12-bit, +-10 V ADC", "adc_numbers", "assume.adc_fs_V, assume.adc_bits", "mV")
der("qual.tc_span_mV", round(a["span_mV"], 2), "full thermocouple EMF span between 296 K and 77 K (0 C reference)", "adc_numbers", "phys.seebeck_K_uVK, phys.emf_K_77K_mV", "mV")
der("qual.adc_counts_unamplified", round(a["counts_unamp"], 1), "number of ADC counts the whole 296->77 K span would occupy without amplification", "adc_numbers", "qual.tc_span_mV, qual.adc_lsb_mV", "counts")
der("qual.gain_for_1000_counts", round(a["gain_for_1000_counts"]), "amplifier gain needed to spread the span over ~1000 counts (~0.2 K resolution)", "adc_numbers", "qual.tc_span_mV, qual.adc_lsb_mV", "x")
der("qual.pt100_signal_mV_per_K_1mA", round(100 * P["phys.pt100_alpha"]["value"], 3), "Pt100 signal with 1 mA excitation: dV/dT = I R0 alpha", "-", "phys.pt100_alpha", "mV/K")
der("qual.pt100_self_heat_mW_1mA", round(1e-3 ** 2 * 100 * 1e3, 3), "Pt100 self-heating I^2 R at 1 mA, 100 ohm", "-", "-", "mW")


def film_stage_numbers():
    """thermal resistance of 1 and 3 turns of cling film vs. that of the vapour film."""
    t_film, k_film = P["assume.film_thickness_m"]["value"], P["assume.film_k"]["value"]
    R1 = t_film / k_film
    Rv = 1 / P["phys.h_film_Wm2K"]["value"]
    return dict(R_film1=R1, R_vap=Rv, ratio1=R1 / Rv, ratio3=3 * R1 / Rv)


fs = film_stage_numbers()
der("qual.R_film1_m2KW", float(f"{fs['R_film1']:.2g}"), "conductive resistance of 1 turn of film, t/k", "film_stage_numbers", "assume.film_thickness_m, assume.film_k", "m^2 K/W")
der("qual.R_vapour_m2KW", float(f"{fs['R_vap']:.2g}"), "thermal resistance of the vapour film, 1/h_film", "film_stage_numbers", "phys.h_film_Wm2K", "m^2 K/W")
der("qual.film1_over_vapour_pct", round(100 * fs["ratio1"], 2), "1 turn of film as a percentage of the vapour-film resistance", "film_stage_numbers", "qual.R_film1_m2KW, qual.R_vapour_m2KW", "%")
der("qual.film3_over_vapour_pct", round(100 * fs["ratio3"], 2), "3 turns of film as a percentage of the vapour-film resistance", "film_stage_numbers", "qual.R_film1_m2KW, qual.R_vapour_m2KW", "%")


def radiation():
    sigma, eps = 5.670e-8, P["assume.eps_Cu"]["value"]
    q_rad = eps * sigma * (296 ** 4 - 77 ** 4)
    return dict(q_rad=q_rad, frac=q_rad / t["q_film"])


r = radiation()
der("qual.q_rad_296_Wm2", round(r["q_rad"], 1), "radiative flux eps sigma (296^4 - 77^4) across the vapour film at the start", "radiation", "assume.eps_Cu", "W/m^2")
der("qual.q_rad_over_film_pct", round(100 * r["frac"], 1), "radiation as a percentage of the film-boiling flux at 296 K", "radiation", "qual.q_rad_296_Wm2, qual.q_film_Wm2", "%")

if __name__ == "__main__":
    out = os.path.join(HERE, "provenance_physics.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(P, fh, indent=1, ensure_ascii=False)
    for k, v in P.items():
        print(f"{k:38s} {v.get('value', '')!s:>12} {v.get('unit', '')}")
    print(len(P), "entries ->", out)
    print("calibration per run:")
    for k, v in cal.items():
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
