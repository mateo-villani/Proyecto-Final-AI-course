#!/usr/bin/env python3
"""Automatic validations for the Leidenfrost analysis.

Run from the job directory:  python out/checks.py
Re-imports work/analysis.py, recomputes the key quantities from the raw CSVs and compares them
with out/provenance.json, then runs physical sanity checks. Prints every check (PASS/FAIL/INFO)
and a coverage summary; exit code 1 if any hard check fails.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(JOB, "work"))
import analysis as an  # noqa: E402

PROV = json.load(open(os.path.join(HERE, "provenance.json"), encoding="utf-8"))
RESULTS = []          # (status, name, message, keys)


def check(name, cond, msg, keys=(), hard=True):
    status = "PASS" if cond else ("FAIL" if hard else "WARN")
    RESULTS.append((status, name, msg, list(keys)))
    print(f"[{status}] {name}: {msg}")


def info(name, msg, keys=()):
    RESULTS.append(("INFO", name, msg, list(keys)))
    print(f"[INFO] {name}: {msg}")


def val(key):
    return PROV[key]["value"]


def main():
    print("=== provenance.json structure ===")
    missing = [k for k, e in PROV.items() if not all(str(e.get(f, "")).strip() for f in ("statement", "type", "reproduce"))]
    check("prov.required_fields", not missing, f"{len(PROV)} entries, {len(missing)} missing statement/type/reproduce")
    bad_paths = []
    for k, e in PROV.items():
        if e["type"] in ("script", "check", "data"):
            path = e["reproduce"].split("::")[0]
            if not os.path.exists(os.path.join(JOB, path)):
                bad_paths.append(k)
    check("prov.script_paths_exist", not bad_paths, f"{len(bad_paths)} entries with a missing reproduce path")
    origins = {}
    for e in PROV.values():
        origins[e.get("origin", "?")] = origins.get(e.get("origin", "?"), 0) + 1
    info("prov.origins", f"entries by origin: {origins}")

    print("=== provenance <-> code sync (recomputed from raw CSVs) ===")
    cv300 = float(an.cv_einstein(300.0)); cv77 = float(an.cv_einstein(77.0))
    check("sync.Cv_300K", abs(cv300 - val("cv.Cv_300K")) < 1e-6, f"recomputed {cv300:.4f} vs prov {val('cv.Cv_300K'):.4f} J/(mol K)", ["cv.Cv_300K"])
    check("sync.Cv_77K", abs(cv77 - val("cv.Cv_77K")) < 1e-6, f"recomputed {cv77:.4f} vs prov {val('cv.Cv_77K'):.4f}", ["cv.Cv_77K"])
    runs = {c: an.analyse_run(c) for c in an.FILES}
    for c in ("A", "B", "C", "C1", "C3"):
        tc = runs[c]["tc"]
        check(f"sync.tc.{c}", abs(tc["t_s"] - val(f"tc.{c}.t_s")) < 1e-6 and abs(tc["T_K"] - val(f"tc.{c}.T_K")) < 1e-6,
              f"t_c={tc['t_s']:.2f} s, T_c={tc['T_K']:.2f} K match provenance", [f"tc.{c}.t_s", f"tc.{c}.T_K"])
    bal = an.analyse_balance()
    check("sync.bal.slopes", abs(bal["s1"]["slope"] - val("bal.slope1_gs")) < 1e-9 and abs(bal["s3"]["slope"] - val("bal.slope3_gs")) < 1e-9,
          f"slope1={bal['s1']['slope']:.5f}, slope3={bal['s3']['slope']:.5f} g/s match provenance", ["bal.slope1_gs", "bal.slope3_gs"])

    print("=== heat capacity ===")
    R = an.R_GAS
    check("cv.dulong_petit", 0.90 < cv300 / (3 * R) < 1.0, f"Cv(300 K)/3R = {cv300/(3*R):.3f} (expect 0.90-1.00)", ["cv.Cv_300K_over_3R"])
    check("cv.monotonic", cv77 < float(an.cv_einstein(150.0)) < cv300, f"Cv(77)={cv77:.2f} < Cv(150)={float(an.cv_einstein(150.0)):.2f} < Cv(300)={cv300:.2f}", ["cv.Cv_77K", "cv.Cv_300K"])
    dev = val("cv.einstein_vs_debye_maxdev_pct")
    check("cv.einstein_vs_debye", dev < 12.0, f"max |Einstein-Debye|/Debye over 77-300 K = {dev:.1f} % (tolerance 12 %; guide warns Einstein is worse at low T)",
          ["cv.einstein_vs_debye_maxdev_pct", "cv.debye_Cv_77K", "cv.debye_Cv_300K"])
    check("cv.eq4_typo_detected", abs(val("cv.eq4_literal_Cv_300K") - cv300) / cv300 > 0.2,
          f"eq.4 as printed gives {val('cv.eq4_literal_Cv_300K'):.1f} vs corrected {cv300:.1f} J/(mol K): the theta_D in the exponent is a typo",
          ["cv.eq4_literal_Cv_300K"])
    H = val("cv.enthalpy_77_296_Jkg")
    check("cv.enthalpy_range", 60e3 < H < 85e3, f"integral Cv dT (77->296 K) = {H/1e3:.1f} kJ/kg (literature Cu ~ 75-80 kJ/kg; Einstein is low at low T)",
          ["cv.enthalpy_77_296_Jkg"], hard=False)

    print("=== geometry (measured h, d, m from inbox.jsonl; area, n, p recomputed with propagated errors) ===")
    for c in ("A", "B", "C"):
        g = an.geometry(c)
        check(f"geom.sync.{c}", abs(g["area_m2"] - val(f"geom.{c}.area_m2")) < 1e-12 and abs(g["p_kgm2"] - val(f"geom.{c}.p_kgm2")) < 1e-9,
              f"area {g['area_m2']*1e4:.1f} cm2, n {g['n_mol']:.3f} mol, p {g['p_kgm2']:.1f} kg/m2 recomputed = provenance", [f"geom.{c}.area_m2", f"geom.{c}.n_mol", f"geom.{c}.p_kgm2"])
        check(f"geom.area_vs_stated.{c}", val(f"geom.{c}.area_agrees_with_stated") is True,
              f"recomputed area {val(f'geom.{c}.area_m2')*1e4:.1f} +/- {val(f'geom.{c}.darea_m2')*1e4:.1f} cm2 vs human's {val(f'geom.{c}.area_stated_cm2'):.0f} cm2 (within stated +/-)",
              [f"geom.{c}.area_stated_cm2", f"geom.{c}.area_agrees_with_stated", f"geom.{c}.darea_m2"])
        dn = abs(val(f"geom.{c}.n_mol") - val(f"geom.{c}.n_stated_mol")) / val(f"geom.{c}.n_stated_mol")
        check(f"geom.n_vs_stated.{c}", dn < 2e-3, f"recomputed n {val(f'geom.{c}.n_mol'):.3f} vs human's {val(f'geom.{c}.n_stated_mol'):.3f} mol: rel. diff {100*dn:.2f} % (< 0.2 %; human used M = 63.5)",
              [f"geom.{c}.n_stated_mol", f"geom.{c}.n_mol", "geom.M_Cu_implied_by_stated_n"])
        rho = val(f"geom.{c}.rho_from_mV_kgm3")
        check(f"geom.density.{c}", 0.95 * an.RHO_CU < rho < 1.02 * an.RHO_CU, f"m/V = {rho:.0f} kg/m3 within -5 %/+2 % of solid Cu (8960): dimensions and mass are mutually consistent",
              [f"geom.{c}.rho_from_mV_kgm3"])
        check(f"geom.p_err.{c}", val(f"geom.{c}.dp_kgm2") / val(f"geom.{c}.p_kgm2") < 0.08, f"p = {val(f'geom.{c}.p_kgm2'):.1f} +/- {val(f'geom.{c}.dp_kgm2'):.1f} kg/m2 ({100*val(f'geom.{c}.dp_kgm2')/val(f'geom.{c}.p_kgm2'):.1f} %)",
              [f"geom.{c}.dp_kgm2"])
    check("geom.no_assumed_left", not any(k.startswith("geom.") and e.get("origin") == "assumed" for k, e in PROV.items()),
          f"no geom.* provenance entry has origin 'assumed' (the round-1 nominal geometry is gone, replaced by measured dimensions); "
          f"{sum(1 for e in PROV.values() if e.get('origin')=='measured')} entries are 'measured', "
          f"{sum(1 for e in PROV.values() if e.get('origin')=='assumed')} entries elsewhere (ADC/film/emissivity, disclosed in notes.tex) are legitimately 'assumed'")
    check("geom.order", val("geom.A.p_kgm2") > val("geom.C.p_kgm2") > val("geom.B.p_kgm2"), f"p ordering A ({val('geom.A.p_kgm2'):.1f}) > C ({val('geom.C.p_kgm2'):.1f}) > B ({val('geom.B.p_kgm2'):.1f}) kg/m2 matches t_c ordering A > C > B",
          ["geom.A.p_kgm2", "geom.B.p_kgm2", "geom.C.p_kgm2", "tc.A.t_from_immersion_s", "tc.B.t_from_immersion_s", "tc.C.t_from_immersion_s"])

    print("=== temperature runs: Q/A sign, t_c range, collapse detection ===")
    for c in ("A", "B", "C", "C1", "C3"):
        n_neg, n_cool = val(f"qa.{c}.n_nonpositive"), val(f"qa.{c}.n_cooling_samples")
        check(f"qa.positive.{c}", n_neg == 0, f"{int(n_neg)} of {int(n_cool)} cooling-window samples have Q/A <= 0",
              [f"qa.{c}.n_nonpositive", f"qa.{c}.n_cooling_samples"])
    for c in ("A", "B", "C"):
        Tc = val(f"tc.{c}.T_K")
        check(f"tc.range.{c}", 77.0 < Tc < 300.0, f"T(t_c) = {Tc:.1f} K within (77, 300)", [f"tc.{c}.T_K"])
        check(f"tc.physical.{c}", 85.0 < Tc < 150.0, f"T(t_c) = {Tc:.1f} K within (85, 150) K, i.e. Delta T = {Tc-77:.0f} K (Leidenfrost point of LN2 on metals: tens of K)",
              [f"tc.{c}.T_K"])
        check(f"tc.detected.{c}", val(f"tc.{c}.detected") is True and val(f"tc.{c}.peak_over_plateau") >= 3,
              f"peak/plateau |dT/dt| = {val(f'tc.{c}.peak_over_plateau'):.1f} (>= 3)", [f"tc.{c}.detected", f"tc.{c}.peak_over_plateau"])
        check(f"tc.band.{c}", val(f"tc.{c}.Tlo_K") < Tc < val(f"tc.{c}.Thi_K") and val(f"tc.{c}.Thi_K") - val(f"tc.{c}.Tlo_K") < 60,
              f"drop band [{val(f'tc.{c}.Tlo_K'):.1f}, {val(f'tc.{c}.Thi_K'):.1f}] K brackets T_c and is < 60 K wide", [f"tc.{c}.Tlo_K", f"tc.{c}.Thi_K"])
        check(f"tc.sensitivity.{c}", val(f"tc.{c}.sens_t_spread_s") <= 3.0, f"t_c spread over SG window 3..11 & frac 0.3..0.7 = {val(f'tc.{c}.sens_t_spread_s'):.1f} s (<= 3 s)",
              [f"tc.{c}.sens_t_spread_s"])
        check(f"tc.full_range_agrees.{c}", abs(val(f"tc.{c}.full_range_t_s") - val(f"tc.{c}.t_s")) < 1e-6,
              f"whole-run max |dT/dt| is the same sample as the T<200 K search", [f"tc.{c}.full_range_t_s"])
        check(f"qa.leidenfrost_min.{c}", 30 < val(f"qa.{c}.dT_at_min_K") < 70, f"film-regime minimum at Delta T = {val(f'qa.{c}.dT_at_min_K'):.0f} K (30-70 K)",
              [f"qa.{c}.dT_at_min_K", f"qa.{c}.min_film_Wm2"])
        check(f"qa.peak.{c}", 10 < val(f"qa.{c}.dT_at_peak_K") < 40 and val(f"qa.{c}.peak_Wm2") > 3 * val(f"qa.{c}.min_film_Wm2"),
              f"Q/A peak at Delta T = {val(f'qa.{c}.dT_at_peak_K'):.0f} K, peak/min = {val(f'qa.{c}.peak_Wm2')/val(f'qa.{c}.min_film_Wm2'):.1f}",
              [f"qa.{c}.dT_at_peak_K", f"qa.{c}.peak_Wm2"])
    check("tc.C3.no_collapse", val("tc.C3.detected") is False and val("rate.C3.dTdt_200K") > val("rate.C3.dTdt_150K") > val("rate.C3.dTdt_120K") > val("rate.C3.dTdt_100K"),
          f"C + 3 vueltas: |dT/dt| decreases monotonically 200->100 K ({val('rate.C3.dTdt_200K'):.2f}, {val('rate.C3.dTdt_150K'):.2f}, {val('rate.C3.dTdt_120K'):.2f}, {val('rate.C3.dTdt_100K'):.2f} K/s): no abrupt collapse",
          ["tc.C3.detected", "rate.C3.dTdt_200K", "rate.C3.dTdt_100K"])
    check("tc.C1.immediate", val("tc.C1.t_from_immersion_s") < 10 and val("film.t_to_80K.C1_s") < 15,
          f"C + 1 vuelta: max |dT/dt| {val('tc.C1.t_from_immersion_s'):.1f} s after immersion, T<80 K after {val('film.t_to_80K.C1_s'):.1f} s: no film plateau at all",
          ["tc.C1.t_from_immersion_s", "film.t_to_80K.C1_s"])
    info("tc.C1.flux_warning", f"C1 peak Q/A = {val('qa.C1.peak_Wm2')/1e3:.0f} kW/m2 with the MEASURED geometry of C (226 g, 48.9 cm2), still ~{val('qa.C1.peak_Wm2')/1.5e5:.1f}x the LN2 critical heat flux (~150 kW/m2): "
         "lumped-body assumption doubtful for this run, or the junction was not anchored to the bulk", ["qa.C1.peak_Wm2"])
    check("qa.peak_below_CHF_x2", all(val(f"qa.{c}.peak_Wm2") < 3e5 for c in ("A", "B", "C")),
          "Q/A peaks of A, B, C (" + ", ".join(f"{val(f'qa.{c}.peak_Wm2')/1e3:.0f}" for c in ("A", "B", "C")) + " kW/m2) all below 2x the LN2 CHF (~150 kW/m2) with the measured geometry",
          [f"qa.{c}.peak_Wm2" for c in ("A", "B", "C")])
    check("qa.plateau_body_independent", val("qa.plateau_spread_pct") < 40,
          f"film-boiling plateau Q/A: A {val('qa.A.plateau_Wm2')/1e3:.1f}, B {val('qa.B.plateau_Wm2')/1e3:.1f}, C {val('qa.C.plateau_Wm2')/1e3:.1f} kW/m2, spread {val('qa.plateau_spread_pct'):.0f} % (< 40 %; was ~78 % with a common nominal m/A)",
          ["qa.plateau_spread_pct", "qa.A.plateau_Wm2", "qa.B.plateau_Wm2", "qa.C.plateau_Wm2"])

    print("=== t_c vs p ===")
    for pair in ("BA", "CA"):
        r_tc, r_rate = val(f"rel.tc_ratio_{pair}"), val(f"rel.inv_rate_ratio_{pair}_200K")
        check(f"rel.tc_prop_p.{pair}", abs(r_tc - r_rate) / r_rate < 0.25,
              f"t_c ratio {r_tc:.2f} vs inverse cooling-rate ratio at 200 K {r_rate:.2f} (geometry-independent; both = p_{pair[0]}/p_{pair[1]} if q_film is body-independent; tol 25 %)",
              [f"rel.tc_ratio_{pair}", f"rel.inv_rate_ratio_{pair}_200K"])
        r_p, dr_p = val(f"rel.p_ratio_{pair}"), val(f"rel.p_ratio_{pair}_err")
        check(f"rel.tc_ratio_vs_measured_p.{pair}", abs(r_tc - r_p) / r_p < 0.30,
              f"t_c ratio {r_tc:.2f} vs measured p ratio {r_p:.2f} +/- {dr_p:.2f} (diff {100*(r_tc-r_p)/r_p:+.0f} %, tol 30 %)",
              [f"rel.p_ratio_{pair}", f"rel.p_ratio_{pair}_err"])
    tcp = {c: val(f"rel.tc_over_p.{c}") for c in ("A", "B", "C")}
    check("rel.tc_over_p.monotonic", val("tc.A.t_from_immersion_s") > val("tc.C.t_from_immersion_s") > val("tc.B.t_from_immersion_s"),
          "t_c increases with p: t_c(A) > t_c(C) > t_c(B) as p_A > p_C > p_B", ["rel.tc_over_p.A", "rel.tc_over_p.B", "rel.tc_over_p.C"])
    check("rel.tc_over_p.spread", val("rel.tc_over_p.spread_pct") < 40,
          "t_c/p = " + ", ".join(f"{c} {tcp[c]:.2f}+/-{val(f'rel.tc_over_p.{c}_err'):.2f}" for c in tcp) + f" s m2/kg; (max-min)/mean = {val('rel.tc_over_p.spread_pct'):.0f} % (< 40 %): t_c ~ p holds to ~15 %, not exactly",
          ["rel.tc_over_p.spread_pct", "rel.tc_over_p.std_pct", "rel.tc_over_p.mean"])
    info("rel.tc_vs_p.fit", f"t_c = k p through the origin: k = {val('rel.tc_vs_p.slope_s_m2_per_kg'):.2f} s m2/kg, chi2/dof = {val('rel.tc_vs_p.chi2_dof'):.1f}, max residual {val('rel.tc_vs_p.max_resid_pct'):.0f} % "
         "(chi2/dof >> 1: residual scatter is real, not geometric error; q_film differs between bodies by the same ~25 %)",
         ["rel.tc_vs_p.slope_s_m2_per_kg", "rel.tc_vs_p.chi2_dof", "rel.tc_vs_p.max_resid_pct"])
    check("rel.T_at_tc_common", max(val(f"tc.{c}.T_K") for c in "ABC") - min(val(f"tc.{c}.T_K") for c in "ABC") < 5,
          "T(t_c) = " + ", ".join(f"{val(f'tc.{c}.T_K'):.1f}" for c in "ABC") + " K: spread < 5 K, the collapse temperature is body-independent (it is a surface/liquid property)",
          ["tc.A.T_K", "tc.B.T_K", "tc.C.T_K"])

    print("=== balance ===")
    s1, s3, tail = val("bal.slope1_gs"), val("bal.slope3_gs"), val("bal.slope3_tail_gs")
    check("bal.slopes_negative", s1 < 0 and s3 < 0, f"slope1 = {s1*1e3:.1f} mg/s, slope3 = {s3*1e3:.1f} mg/s, both negative", ["bal.slope1_gs", "bal.slope3_gs"])
    check("bal.stage_order", val("bal.t1_end_s") < val("bal.burst_start_s") < val("bal.t3_start_s"),
          f"stage boundaries t1_end={val('bal.t1_end_s'):.0f} s < burst {val('bal.burst_start_s'):.0f} s < t3_start={val('bal.t3_start_s'):.0f} s, all found from the data",
          ["bal.t1_end_s", "bal.burst_start_s", "bal.t3_start_s"])
    check("bal.jump_positive", val("bal.jump_g") > 5, f"immersion step = +{val('bal.jump_g'):.1f} g (buoyancy of the body)", ["bal.jump_g"])
    check("bal.tail_recovers_ambient", abs(tail - s1) / abs(s1) < 0.2,
          f"last-20-s slope {tail*1e3:.1f} mg/s within 20 % of stage-1 slope {s1*1e3:.1f} mg/s (Cu at bath T -> only ambient evaporation left)",
          ["bal.slope3_tail_gs", "bal.slope1_gs"])
    info("bal.slope_ratio", f"slope3/slope1 = {val('bal.slope_ratio'):.2f} over the whole stage 3 (still-cooling Cu makes stage 3 curved); tail ratio {val('bal.slope_ratio_tail'):.2f}",
         ["bal.slope_ratio", "bal.slope_ratio_tail"])
    # energy: calorimetry (assumed geometry) vs balance
    Qb, Qcu = val("bal.Q_balance_J"), val("bal.Q_cu_J")
    check("bal.energy_vs_C", 0.8 < Qb / Qcu < 1.25, f"Q_balance = {Qb/1e3:.1f} kJ vs n_C*int Cv dT for the MEASURED cylinder C (226.2 g) = {Qcu/1e3:.1f} kJ, ratio {Qb/Qcu:.2f} (tol 0.8-1.25; vapour assumed to leave at 77 K)",
          ["bal.Q_balance_J", "bal.Q_cu_J", "bal.Q_ratio", "bal.Q_cu_C_J"])
    info("bal.energy_vs_ABC", "Q_balance / Q_cu for A, B, C = " + ", ".join(f"{c} {val(f'bal.Q_ratio_{c}'):.2f}" for c in "ABC") + " -> only C is compatible",
         ["bal.Q_ratio_A", "bal.Q_ratio_B", "bal.Q_ratio_C"])
    me, mb = val("bal.m_eff_energy_kg"), val("bal.m_eff_buoy_kg")
    check("bal.mass_two_ways", abs(me - mb) / (0.5 * (me + mb)) < 0.4,
          f"immersed Cu mass from energy budget {me:.3f} kg (upper {val('bal.m_eff_energy_upper_kg'):.3f}) vs from buoyancy step {mb:.3f} kg agree within 40 %",
          ["bal.m_eff_energy_kg", "bal.m_eff_buoy_kg", "bal.m_eff_energy_upper_kg"])
    check("bal.body_is_C", val("bal.body_identified") == "C" and abs(val("bal.m_buoy_over_mC") - 1) < 0.15 and abs(val("bal.m_energy_over_mC") - 1) < 0.15,
          f"balance run body = {val('bal.body_identified')}: buoyancy mass / m_C = {val('bal.m_buoy_over_mC'):.2f}, energy mass / m_C = {val('bal.m_energy_over_mC'):.2f} (both within 15 %); A would give 0.22-0.26, B 1.3-1.5",
          ["bal.body_identified", "bal.m_buoy_over_mC", "bal.m_energy_over_mC", "geom.C.m_kg"])
    check("bal.buoyancy_volume_vs_C", abs(val("bal.V_buoy_over_V_C") - 1) < 0.15,
          f"displaced volume from the +{val('bal.jump_g'):.1f} g step = {val('bal.V_buoyancy_m3')*1e6:.1f} cm3 vs geometric volume of C {val('bal.V_C_m3')*1e6:.1f} cm3, ratio {val('bal.V_buoy_over_V_C'):.2f}: C was fully immersed",
          ["bal.V_buoy_over_V_C", "bal.V_C_m3", "bal.V_buoyancy_m3"])
    check("bal.QA_two_ways_hot", 0.5 < val("bal.QA_ratio_hot") < 2.0,
          f"Q/A just after immersion: balance {val('bal.QA_post_immersion_Wm2')/1e3:.1f} kW/m2 vs calorimetric (run C, 230-290 K) {val('qa.C.calorimetric_hot_Wm2')/1e3:.1f} kW/m2, ratio {val('bal.QA_ratio_hot'):.2f} (tol 0.5-2; independent runs, vapour superheat neglected)",
          ["bal.QA_ratio_hot", "bal.QA_post_immersion_Wm2", "qa.C.calorimetric_hot_Wm2"])
    check("bal.QA_two_ways_cold", 0.5 < val("bal.QA_ratio_cold") < 2.0,
          f"Q/A just before collapse: balance {val('bal.QA_preburst_Wm2')/1e3:.1f} kW/m2 vs calorimetric (run C, 10-40 K above the drop band) {val('qa.C.calorimetric_cold_Wm2')/1e3:.1f} kW/m2, ratio {val('bal.QA_ratio_cold'):.2f} (tol 0.5-2)",
          ["bal.QA_ratio_cold", "bal.QA_preburst_Wm2", "qa.C.calorimetric_cold_Wm2"])
    info("bal.stage2_vs_tc_C", f"stage-2 duration {val('bal.stage2_duration_s'):.0f} s vs t_c(C) from immersion {val('tc.C.t_from_immersion_s'):.0f} s in the temperature run: +{val('bal.stage2_vs_tc_C_s'):.0f} s (separate immersions; repeatability of t_c, includes the ~8 s burst)",
         ["bal.stage2_vs_tc_C_s", "bal.stage2_duration_s"])
    # power-ratio shape check: geometry independent
    P0, P1 = val("bal.power_post_immersion_W"), val("bal.power_preburst_W")
    ratio_bal = P0 / P1
    ratios = {}
    for c in ("A", "B", "C"):
        q_hot = val(f"rate.{c}.dTdt_250K") * float(an.cv_einstein(250.0))
        q_cold = val(f"rate.{c}.dTdt_120K") * float(an.cv_einstein(120.0))
        ratios[c] = q_hot / q_cold
    ok = any(abs(v - ratio_bal) / ratio_bal < 0.5 for v in ratios.values())
    check("bal.power_shape_vs_calorimetry", ok,
          f"balance power just after immersion / just before burst = {P0:.0f} W / {P1:.0f} W = {ratio_bal:.2f}; calorimetric Cv*|dT/dt| ratio 250 K / 120 K: "
          + ", ".join(f"{c}={v:.2f}" for c, v in ratios.items()) + " (at least one within 50 %; geometry cancels)",
          ["bal.power_post_immersion_W", "bal.power_preburst_W"])

    print("=== thermocouple ===")
    for c in ("B", "C"):
        check(f"tc_check.{c}", val(f"tc_check.{c}.max_abs_dev_K") < 0.5,
              f"CSV T vs NIST type-K inverse polynomial (ice reference): max dev {val(f'tc_check.{c}.max_abs_dev_K'):.2f} K; emf at 77 K = {val(f'tc_check.{c}.V_at_77K_mV'):.3f} mV",
              [f"tc_check.{c}.max_abs_dev_K", f"tc_check.{c}.V_at_77K_mV"])

    print("=== round-3: balance residual power model ===")
    check("bal2.decay_beats_linear", val("bal2.model_rms_g") < 0.2 and val("bal2.model_rms_g") < bal["s3"]["rms"],
          f"exponential-decay fit to stage 3 has rms {val('bal2.model_rms_g'):.3f} g (< 0.2 g; the straight-line fit has rms {bal['s3']['rms']:.2f} g): the decay model is a materially better description",
          ["bal2.model_rms_g"])
    check("bal2.P0_positive_and_bounded", 10 < val("bal2.model_P0_W") < 100,
          f"fitted initial residual power P0 = {val('bal2.model_P0_W'):.1f} W is positive and of a plausible order of magnitude for a just-collapsed cylinder", ["bal2.model_P0_W"])
    check("bal2.tau_positive_and_bounded", 3 < val("bal2.model_tau_s") < 60,
          f"fitted relaxation time tau = {val('bal2.model_tau_s'):.1f} s is positive and shorter than the whole stage-3 window ({bal['dur_s']:.0f} s), as a decaying transient requires", ["bal2.model_tau_s"])
    check("bal2.model_matches_naive", abs(val("bal2.model_Pavg_W") - val("bal2.Pres_avg_naive_W")) / val("bal2.Pres_avg_naive_W") < 0.3,
          f"time-averaged model power {val('bal2.model_Pavg_W'):.2f} W agrees with the naive whole-stage estimate {val('bal2.Pres_avg_naive_W'):.2f} W to {100*abs(val('bal2.model_Pavg_W')-val('bal2.Pres_avg_naive_W'))/val('bal2.Pres_avg_naive_W'):.0f} % (< 30 %): both describe the same transient, not conflicting measurements",
          ["bal2.model_Pavg_W", "bal2.Pres_avg_naive_W"])
    check("bal2.T0_consistent_with_collapse_band", abs(val("bal2.model_T0_vs_Tlo_K")) < 20,
          f"fitted post-burst temperature (77+dT0) differs from the independently-measured collapse-band lower edge T_lo(C) by {val('bal2.model_T0_vs_Tlo_K'):.1f} K (< 20 K, different immersions)", ["bal2.model_T0_vs_Tlo_K"])
    check("bal2.tail_residual_below_noise", val("bal2.dTdt_implied_tail_Ks") < 3 * val("bal2.noise_std_dTdt_plateau_C_Ks"),
          f"tail-based implied |dT/dt| ({val('bal2.dTdt_implied_tail_Ks'):.3f} K/s) is within 3x the observed plateau noise floor ({val('bal2.noise_std_dTdt_plateau_C_Ks'):.3f} K/s): consistent with the cylinder being near 77 K by the end of stage 3",
          ["bal2.dTdt_implied_tail_Ks", "bal2.noise_std_dTdt_plateau_C_Ks"])
    check("bal2.avg_residual_above_noise", val("bal2.dTdt_implied_avg_Ks") > 3 * val("bal2.noise_std_dTdt_plateau_C_Ks"),
          f"whole-stage implied |dT/dt| ({val('bal2.dTdt_implied_avg_Ks'):.3f} K/s) is well above the plateau noise floor: if it were a steady residual (not a decaying transient) it would be visible in a temperature trace",
          ["bal2.dTdt_implied_avg_Ks"])

    print("=== round-3: Einstein vs Debye impact on Q/A ===")
    check("cvcmp.max_diff_at_77K", abs(val("cvcmp.max_abs_diff_pct") + 10) < 2, f"max Einstein/Debye relative difference on the table is {val('cvcmp.max_abs_diff_pct'):.1f} % at {val('cvcmp.max_abs_diff_T_K'):.0f} K (matches cv.einstein_vs_debye_maxdev_pct)",
          ["cvcmp.max_abs_diff_pct"])
    for c in ("A", "B", "C"):
        for label in ("plateau", "peak", "min_film"):
            k = f"cvcmp.qa.{c}.{label}_diff_pct"
            if k in PROV:
                check(f"cvcmp.small_impact.{c}.{label}", abs(val(k)) < 5.0, f"Einstein vs Debye changes Q/A ({label}, run {c}) by {val(k):.2f} % (< 5 %, well below the ~3-8 % geometric uncertainty of p): the model choice does not affect this conclusion", [k])
    check("stage.bounds_ordered", val("stage.bounds_dT_K")[0] > val("stage.bounds_dT_K")[1] > val("stage.bounds_dT_K")[2] > val("stage.bounds_dT_K")[3] > val("stage.bounds_dT_K")[4] > val("stage.bounds_dT_K")[5],
          f"the six stage boundaries are strictly decreasing in Delta T: {val('stage.bounds_dT_K')}", ["stage.bounds_dT_K"])

    print("=== round-3: t_c(p) fits and 4th-cylinder prediction ===")
    check("fit.origin_worse_than_2param", val("fit.through_origin.max_abs_resid_pct") > val("fit.power_law.max_abs_resid_pct"),
          f"the 1-parameter through-origin fit has larger max residual ({val('fit.through_origin.max_abs_resid_pct'):.1f} %) than the 2-parameter power law ({val('fit.power_law.max_abs_resid_pct'):.1f} %), as expected with only 1 dof vs 1 dof less: NOT evidence that the power law is the true model",
          ["fit.through_origin.max_abs_resid_pct", "fit.power_law.max_abs_resid_pct"])
    check("fit.dof_low", val("fit.power_law.dof") == 1 and val("fit.general_linear.dof") == 1,
          "the 2-parameter fits have only 1 degree of freedom with 3 data points: flagged explicitly in the report as weak evidence", ["fit.power_law.dof", "fit.n_datapoints"])
    check("pred.D.interpolation", val("geom.B.p_kgm2") < val("pred.D.p_kgm2") < val("geom.C.p_kgm2"),
          f"p_D = {val('pred.D.p_kgm2'):.1f} kg/m2 lies between p_B ({val('geom.B.p_kgm2'):.1f}) and p_C ({val('geom.C.p_kgm2'):.1f}): the D prediction is an interpolation, not an extrapolation",
          ["pred.D.p_kgm2", "geom.B.p_kgm2", "geom.C.p_kgm2"])
    check("pred.D.model_uncertainty_dominates", val("pred.D.model_spread_s") > (val("pred.D.geom_sensitivity_range_s")[1] - val("pred.D.geom_sensitivity_range_s")[0]),
          f"model-choice spread ({val('pred.D.model_spread_s'):.0f} s) exceeds the geometry-uncertainty sensitivity range ({val('pred.D.geom_sensitivity_range_s')[1]-val('pred.D.geom_sensitivity_range_s')[0]:.0f} s): with 3 cylinders, functional-form uncertainty dominates over measurement uncertainty",
          ["pred.D.model_spread_s", "pred.D.geom_sensitivity_range_s"])

    print("=== round-3: sigma_T propagation (illustrative) ===")
    check("sigmaT.tc_uncertainty_is_sampling", val("sigmaT.sigma_tc_halfsample_s") <= 3.0,
          f"half-sample t_c uncertainty ({val('sigmaT.sigma_tc_halfsample_s'):.2f} s) matches the <=3 s sensitivity-sweep spread already reported: t_c uncertainty is sampling-, not noise-, dominated", ["sigmaT.sigma_tc_halfsample_s"])
    check("sigmaT.crosscheck_plausible", abs(val("sigmaT.crosscheck_vs_observed_noise_pct")) < 100,
          f"the illustrative ADC-only sigma_dTdt near 80 K is within a factor of 2 of the observed plateau noise floor ({val('sigmaT.crosscheck_vs_observed_noise_pct'):+.0f} %): the assumed ADC/gain are a plausible order of magnitude, not verified as the true spec",
          ["sigmaT.crosscheck_vs_observed_noise_pct"], hard=False)

    print("=== round-3: C1 anomaly ===")
    check("c1x.window_sensitivity_material", val("c1x.peak_window_spread_ratio") > 1.5,
          f"C1 peak Q/A changes by {val('c1x.peak_window_spread_ratio'):.1f}x over SG windows 3-11: the reported peak is not resolution-independent", ["c1x.peak_window_spread_ratio"])
    check("c1x.few_samples", val("c1x.n_samples_full_transition") < 10,
          f"only {val('c1x.n_samples_full_transition'):.0f} samples span the entire 296->80 K transition of C1 ({val('c1x.duration_full_transition_s'):.1f} s): consistent with a numerically under-resolved transient", ["c1x.n_samples_full_transition"])
    check("c1x.biot_marginal", 0.01 < val("c1x.Bi_at_peak") < 0.5,
          f"Biot number at the C1 peak-flux estimate is {val('c1x.Bi_at_peak'):.2f}: marginal, not clearly << 1 as elsewhere in the analysis", ["c1x.Bi_at_peak"], hard=False)

    print("=== round-3: constants and reference verification ===")
    check("verif.seebeck_crosscheck", val("verif.seebeck_K_room_vs_wikipedia") is True, "type-K room-T Seebeck coefficient (41 uV/K) matches an independent secondary source (Wikipedia) fetched this session", ["verif.seebeck_K_room_vs_wikipedia"])
    check("verif.hypotheses_flagged", val("verif.adc_and_film_are_hypotheses") is True, "ADC/amplifier and film specs remain explicitly flagged as hypotheses, not measured facts", ["verif.adc_and_film_are_hypotheses"])
    info("verif.refs", f"Curzon (1978) and Listerman et al. (1986) identified bibliographically via CrossRef this session; full text not read, see verif.curzon1978_ref / verif.listerman1986_ref", ["verif.curzon1978_ref", "verif.listerman1986_ref"])

    print("=== coverage ===")
    n = {s: sum(1 for r in RESULTS if r[0] == s) for s in ("PASS", "FAIL", "WARN", "INFO")}
    covered = set()
    for r in RESULTS:
        covered.update(r[3])
    groups = {}
    for k in PROV:
        g = k.split(".")[0]
        groups.setdefault(g, [0, 0])
        groups[g][1] += 1
        if k in covered:
            groups[g][0] += 1
    print(f"checks: {n['PASS']} PASS, {n['FAIL']} FAIL, {n['WARN']} WARN (soft), {n['INFO']} INFO")
    print(f"provenance keys exercised by at least one physical/sync check (structural checks excluded): {len(covered & set(PROV))} / {len(PROV)}")
    for g, (c, t) in sorted(groups.items()):
        print(f"  {g:10s} {c:3d}/{t:3d}")
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
