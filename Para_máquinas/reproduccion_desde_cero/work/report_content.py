# -*- coding: utf-8 -*-
"""Shared text of out/report.html and out/report.py (marimo).

Every number in the prose is a placeholder  [[key|fmt]]  resolved against out/provenance.json
by render(); the rendered number carries a small [key] tag exactly like \\src{} in notes.tex.
    [[key|.1f]]        value formatted, tag shown
    [[key|.1f|notag]]  value only
    [[key|.1f|x1e-3]]  value scaled before formatting (kW from W, cm2 from m2 ...)
Sections are returned by sections(P): list of dicts {id, title, html, figs}.
"""
import re

FIG_CAPTIONS = {
    "Cv_models.png": "Fig. 1 — C_v(T) del Cu: Einstein con Θ_E(T) de la ec. (5) (usado), Debye Θ_D = 315 K (control) y la ec. (4) leída literalmente (errata).",
    "T_vs_t_ABC.png": "Fig. 2 — T(t) de los tres cilindros desnudos; punteado: t_c (máximo de |dT/dt|).",
    "dTdt_vs_T.png": "Fig. 3 — Velocidad de enfriamiento −dT/dt vs T (Savitzky–Golay 5 muestras). El pico es el colapso; a su izquierda el plateau de película.",
    "tc_vs_p.png": "Fig. 4 — t_c (desde la inmersión) vs p = m/A con la geometría medida; barras: ±½ muestra en t y δp propagado; recta: ajuste pesado por el origen.",
    "balance.png": "Fig. 5 — Masa de N₂ (relativa a la tara) vs tiempo; rectas ajustadas a las etapas 1 y 3; líneas punteadas: inmersión y fin del burst, detectados en los datos.",
    "T_vs_t_C_film.png": "Fig. 6 — Cilindro C desnudo, con 1 vuelta y con 3 vueltas de film.",
    "QA_vs_dT_C_lin.png": "Fig. 7 — Q/A vs ΔT, cilindro C, escala lineal.",
    "QA_vs_dT_C_log.png": "Fig. 8 — Q/A vs ΔT, cilindro C, log–log (forma de Nukiyama recorrida de derecha a izquierda).",
    "QA_vs_dT_A_log.png": "Fig. 9 — Q/A vs ΔT, cilindro A, log–log.",
    "QA_vs_dT_B_log.png": "Fig. 10 — Q/A vs ΔT, cilindro B, log–log.",
    "Cv_diff.png": "Fig. 11 — Izq.: C_v(T) de Einstein y Debye superpuestos. Der.: diferencia relativa (Einstein−Debye)/Debye; máxima a la temperatura más baja de la grilla.",
    "QA_models_compare.png": "Fig. 12 — Cilindro C: Q/A(ΔT) recalculado con C_v de Einstein y con C_v de Debye sobre la misma T(t) y geometría (round-3, sec. 2.4).",
    "tc_vs_p_models.png": "Fig. 13 — t_c vs p: ajuste físico por el origen, ley de potencia y recta general (2 parámetros, 3 puntos); derecha: residuos por cilindro y modelo.",
    "pred_D.png": "Fig. 14 — Predicción de t_c para un cuarto cilindro D hipotético (p intermedio entre B y C) según los tres modelos de la Fig. 13.",
    "balance_residual_model.png": "Fig. 15 — Balanza, etapa 3: modelo de relajación exponencial P(t) = P₀ e^(−t/τ) (izq.) y comparación de residuos contra la recta simple (der.).",
    "QA_dT_stages_C.png": "Fig. 16 — Cilindro C: Q/A vs ΔT con las seis etapas de la guía superpuestas sobre los datos reales y el sentido temporal del enfriamiento.",
    "C1_sensitivity.png": "Fig. 17 — Cilindro C + 1 vuelta: el Q/A pico recalculado con distintas ventanas de Savitzky–Golay, mostrando su fuerte dependencia numérica.",
}

_PH = re.compile(r"\[\[([^\]\[|]+)\|([^\]|]*)(?:\|([^\]]*))?\]\]")


def render(template, P):
    def sub(m):
        key, fmt, opt = m.group(1), m.group(2), m.group(3) or ""
        if key not in P:
            return f'<span class="missing">[{key}?]</span>'
        v = P[key]["value"]
        for o in opt.split(","):
            o = o.strip()
            if o.startswith("x") and isinstance(v, (int, float)):
                v = v * float(o[1:])
        try:
            txt = format(v, fmt) if fmt else str(v)
        except (TypeError, ValueError):
            txt = str(v)
        txt = txt.replace(".", ",") if fmt and isinstance(v, (int, float)) and not isinstance(v, bool) else txt
        if "notag" in opt:
            return txt
        return f'{txt}<sup class="src" title="{P[key]["statement"]}">[{key}]</sup>'
    return _PH.sub(sub, template)


def sections(P):
    S = []

    S.append(dict(id="alcance", title="Alcance, fuentes y trazabilidad", figs=[], html="""
<p>Este informe reproduce el análisis del laboratorio «Efecto Leidenfrost» usando únicamente los seis CSV de
<code>datos/</code>, las dos guías de <code>guia/</code> y las dimensiones de los tres cilindros que el humano
midió y comunicó (<code>inbox.jsonl</code>). <strong>Nadie del equipo abrió <code>informe-original/</code></strong>
(ni lectura, ni búsqueda, ni listado). Cada número lleva una etiqueta gris <sup class="src">[clave]</sup> que
resuelve en <code>out/provenance.json</code>: allí consta qué script y función lo generó, con qué entradas, y si es
<em>derivado</em>, <em>tomado de la guía</em>, de <em>tablas</em> (<code>phys.*</code>), <em>medido por el humano</em>
(<code>geom.*</code>) o <em>supuesto</em> (<code>assume.*</code>). Todo se regenera con
<code>python work/build_all.py</code>; las validaciones automáticas corren con <code>python out/checks.py</code>
y su salida completa está al final de este documento.</p>
<p><strong>Tomado de la guía tal cual:</strong> las ecuaciones (1), (4) y (5) y sus constantes
a = [[guide.a|]], b = [[guide.b|]], c = [[guide.c|]], Θ<sub>D</sub> = [[guide.thetaD_K|.0f]] K; las aproximaciones
C<sub>p</sub> ≃ C<sub>v</sub> (error ≤ [[guide.CpCv_max_pct|.0f]] %) y γT ≪ C<sub>l</sub> (≤ [[guide.gamma_max_pct|.1f]] %);
T<sub>sat</sub> = [[phys.T_sat_K|.0f]] K; la descripción cualitativa de las seis etapas de su Fig. 1. La geometría nominal
de la guía (~10 cm × 4 cm, ~1 kg) <em>no</em> se usa: el humano entregó las dimensiones medidas (§3).</p>
<p><strong>Derivado aquí:</strong> todo lo demás — la corrección de la errata de la ec. (4), C<sub>v</sub>(T), Q/A(t), el
criterio de t<sub>c</sub> y sus valores, la propagación de incertezas de área, n y p, la relación p–t<sub>c</sub>,
las etapas de la balanza y sus ajustes, la identificación del cuerpo de la corrida de balanza, y dos comparaciones
independientes de Q/A.</p>
<p><strong>Una errata en la guía.</strong> La ec. (4) impresa tiene prefactor (Θ<sub>E</sub>/T)² pero exp(Θ<sub>D</sub>/T)
en las exponenciales. Leída literalmente da, a 300 K, C<sub>l</sub> = [[qual.eq4_literal_300K|.2f]] J/(mol K), muy por debajo
del límite de Dulong–Petit 3R = [[qual.dulong_petit|.2f]] J/(mol K) que todo modelo de fonones debe alcanzar a T ≫ Θ.
Con Θ<sub>E</sub> en todas partes (la forma estándar de Einstein) se obtiene [[qual.Cv_einstein_300K|.2f]] J/(mol K),
que coincide con Debye ([[qual.Cv_debye_300K|.2f]] J/(mol K)) a [[qual.einstein_vs_debye_300K_pct|.2f]] %. Usamos por lo tanto</p>
<div class="eq">C<sub>l</sub>(T) = 3R (Θ<sub>E</sub>/T)² e<sup>Θ<sub>E</sub>/T</sup> / (e<sup>Θ<sub>E</sub>/T</sup> − 1)²,
&nbsp;&nbsp; Θ<sub>E</sub>(T) = Θ<sub>D</sub> [a + b e<sup>−cT/Θ<sub>D</sub></sup>],
&nbsp;&nbsp; Q/A = −(n/A) C<sub>v</sub>(T) dT/dt &nbsp;(signo: Q/A &gt; 0 mientras el cuerpo se enfría).</div>
<p><strong>Ronda 3 (revisión, verificación y extensión, 2026-09-23).</strong> Este pase revisó las constantes y
supuestos (§1), modeló cuantitativamente la brecha de pendientes de la balanza (§4.4), extendió la comparación
Einstein/Debye a Q/A (§2.4), agregó ajustes alternativos y una predicción para un cuarto cilindro a la relación
p–t<sub>c</sub> (§3.3–3.4), derivó la cadena de propagación de σ<sub>T</sub> (§2.5), investigó cuantitativamente la
anomalía de C1 (§5.1), construyó la figura de las seis etapas sobre los datos reales (§6) y añadió una validación
dimensional (§6.1). Se preservó todo lo que ya estaba correctamente calculado; el resumen final (§7) separa
explícitamente qué se verificó, qué se corrigió, qué es nuevo y qué sigue sin poder resolverse. Para la verificación
de constantes se intentó además una consulta en línea (Wikipedia, «Thermocouple»; los intentos sobre las tablas
NIST primarias fueron redirigidos o bloqueados, ver <code>verif.*</code> en <code>provenance.json</code>); en ningún
momento se accedió a <code>informe-original/</code>.</p>
"""))

    S.append(dict(id="preguntas", title="1. Respuestas a las preguntas de la guía", figs=[], html="""
<h3>1.1 Preguntas previas (<code>Leidenfrost-preguntas.pdf</code>)</h3>
<p><strong>1) Curva cualitativa de Q/A vs ΔT = T − T<sub>sat</sub> y región Leidenfrost.</strong> En escala log–log la curva
(Fig. 1 de la guía, curva de Nukiyama) sube con pendiente suave en convección natural (I), más empinada al aparecer
burbujas (II–III, ebullición nucleada), alcanza un <em>máximo</em> (flujo crítico; para N₂ del orden de
[[phys.qmax_LN2_Wm2|.0f|x1e-3]] kW/m²), cae en la ebullición de transición (IV) hasta un <em>mínimo</em> (punto de Leidenfrost) y
vuelve a subir lentamente en ebullición en película (V) y con radiación (VI). La región Leidenfrost es la rama de
película estable a la derecha del mínimo: el vapor, de conductividad ~[[phys.k_N2vap|.4f]] W/(m K) frente a
[[phys.k_N2liq|.2f]] W/(m K) del líquido, aísla el sólido y la transferencia es baja y casi independiente de ΔT. Un
cuerpo que se enfría desde ~300 K la recorre de derecha a izquierda (§6). Medido aquí: mínimo ~7–14 kW/m² a
ΔT ≃ 50 K y máximo ~70–90 kW/m² a ΔT ≃ 26 K (§2).</p>
<p><strong>2) Esquema del dispositivo.</strong> Cilindro macizo de Cu con una termocupla chromel–alumel soldada en un
orificio; junta de referencia en agua con hielo (0 °C); la fem pasa por un amplificador y entra a la placa MPLI
conectada a la PC; el cilindro se sumerge en un dewar con N₂ líquido (NL). En la medición de balanza el dewar está
sobre una balanza tarada que registra la masa evaporada en función del tiempo.</p>
<p><strong>3) Cómo obtener Q/A vs ΔT de T(t).</strong> Con la ec. (1), Q/A = −(n/A) C<sub>p</sub>(T) dT/dt. Se mide
T(t), se suaviza (el muestreo es de [[qual.dt_sample_s|.3f]] s), se deriva numéricamente, se evalúa C<sub>p</sub> ≃ C<sub>v</sub>
con la ec. de Einstein en cada T y se grafica contra ΔT = T − 77 K. Cada instante t da un par (ΔT, Q/A); la curva se
recorre en el sentido en que baja T. El método exige que el cuerpo no tenga gradientes internos (Bi ≪ 1, §1.2).</p>
<p><strong>4) Termocupla vs resistencia de platino.</strong> <em>Termocupla:</em> junta de medida soldada en el orificio del
Cu, junta de referencia en hielo, fem (unos [[phys.seebeck_K_uVK|.0f]] µV/K a temperatura ambiente,
~[[phys.seebeck_K_77K_uVK|.0f]] µV/K cerca de 77 K) amplificada y digitalizada; la conversión fem→T usa la tabla del
tipo K, no lineal. <em>Pt100:</em> se inserta el sensor en el mismo orificio, se lo excita con corriente constante
(p. ej. 1 mA) a 4 hilos para eliminar la resistencia de los cables y se mide la caída de tensión:
[[qual.pt100_signal_mV_per_K_1mA|.3f]] mV/K, unas diez veces la señal de la termocupla, con autocalentamiento
[[qual.pt100_self_heat_mW_1mA|.1f]] mW (despreciable frente a los ~100 W que intercambia el cilindro). A 77 K la Pt100 vale
~[[phys.pt100_R77|.0f]] Ω y sigue siendo lineal a mejor del 1 %. La termocupla tiene la ventaja de la masa térmica mínima
(respuesta ~[[phys.dTdt_tc_typ_s|.1f]] s) y de poder <em>soldarse</em> al cobre, lo que garantiza contacto térmico; la Pt100
tiene más señal y linealidad pero necesita fuente de corriente y buen contacto mecánico.</p>
<p><strong>5) ¿Cambia la curva con el estado de la superficie?</strong> Sí, fuertemente, por dos vías. (i) La <em>rugosidad</em>
fija la densidad de sitios de nucleación: una superficie rugosa u oxidada nuclea burbujas a menor ΔT, sube el flujo
crítico y, sobre todo, <em>desestabiliza la película de vapor</em> (el mínimo de Leidenfrost se corre a mayor ΔT y el
colapso ocurre antes). (ii) Un <em>recubrimiento de baja efusividad</em> (e = √(kρc)) cambia la temperatura de contacto
instantánea entre superficie y líquido, T<sub>i</sub> = (e<sub>s</sub>T<sub>s</sub> + e<sub>ℓ</sub>T<sub>ℓ</sub>)/(e<sub>s</sub> + e<sub>ℓ</sub>):
para Cu/NL es T<sub>i</sub> = [[qual.T_contact_Cu_LN2_K|.1f]] K (la superficie del cobre casi no baja al tocar el líquido:
e<sub>Cu</sub> = [[qual.effusivity_Cu|.0f]] frente a e<sub>NL</sub> = [[qual.effusivity_LN2|.0f]] J m⁻² K⁻¹ s⁻½), mientras
que para un film plástico/NL es T<sub>i</sub> = [[qual.T_contact_film_LN2_K|.1f]] K. Una superficie que se enfría localmente
al tocar el líquido no puede sostener la película de vapor: el recubrimiento adelanta el colapso. Los datos del
cilindro C con film (§5) muestran exactamente esto.</p>

<h3>1.2 Preguntas embebidas en <code>Leidenfrost-guia.pdf</code></h3>
<p><strong>¿Por qué un metal como el Cu?</strong> La ec. (1) supone <em>ausencia de gradientes térmicos</em> en el cuerpo
(capacidad concentrada). Eso vale si el número de Biot Bi = hL<sub>c</sub>/k ≪ 1, con L<sub>c</sub> = V/A =
[[qual.Lc_A_m|.4f]] m para el cilindro A (el mayor). Con k<sub>Cu</sub> = [[phys.k_Cu|.0f]] W/(m K) y
h ~ [[phys.h_film_Wm2K|.0f]] W/(m² K) en ebullición en película, Bi = [[qual.Bi_film|.3f]]: el cuerpo es isotérmico y una
sola termocupla representa a todo el cilindro. Equivalentemente, la caída centro–superficie necesaria para conducir el
flujo de película q = h(296 − 77) = [[qual.q_film_Wm2|.0f]] W/m² es ΔT<sub>int</sub> = qr/2k = [[qual.dT_internal_film_K|.2f]] K.
Recién durante el colapso (h ~ [[phys.h_nucleate_Wm2K|.0e]] W/(m² K)) el Biot sube a [[qual.Bi_nucleate|.1f]] y ΔT<sub>int</sub>
llega a ~[[qual.dT_internal_peak_K|.1f]] K en el flujo crítico: la hipótesis se degrada justamente en la caída abrupta, que por
eso conviene tratar como <em>evento</em> (t<sub>c</sub>) y no como curva Q/A(ΔT) precisa. Además el Cu tiene un C<sub>v</sub>(T)
muy bien conocido (Θ<sub>D</sub> = 315 K, sólido monoatómico f.c.c. sin transiciones entre 77 y 300 K), no se oxida
apreciablemente en NL y se mecaniza fácil. Un aislante (vidrio) tendría Bi ≫ 1 y su T medida en un punto no diría nada
del flujo en la superficie.</p>
<p><strong>¿Por qué tan masivo?</strong> (a) <em>Escala de tiempo:</em> con capacidad concentrada dT/dt = −hA(T − T<sub>sat</sub>)/(mc),
es decir τ = pc/h con p = m/A; para A (p = [[qual.p_A_kgm2|.1f]] kg/m²) τ ≃ [[qual.tau_cool_film_A_s|.0f]] s en película, para B
[[qual.tau_cool_film_B_s|.0f]] s, para C [[qual.tau_cool_film_C_s|.0f]] s. Eso da centenares de segundos de curva (la corrida A dura
[[qual.duration_s_A|.0f]] s) frente a un muestreo de [[qual.dt_sample_s|.2f]] s: cientos de puntos por régimen. Un alambre de Pt como el
de la Fig. 1 de la guía (medido en estado estacionario, calentado por Joule) se enfriaría en milisegundos.
(b) <em>La termocupla no perturba:</em> su tiempo de respuesta (~[[phys.dTdt_tc_typ_s|.1f]] s) y su capacidad calorífica son
despreciables frente a las del cuerpo. (c) <em>Señal en la balanza:</em> el calor que entrega el cilindro A (941 g) de 296 a
77 K es Q = n∫C<sub>v</sub>dT = [[qual.Q_cu_296_77_kJ_A|.1f]] kJ, que evapora Q/L<sub>v</sub> = [[qual.m_N2_boiled_g_A|.0f]] g de N₂
(L<sub>v</sub> = [[phys.L_v_N2|.0f]] J/kg); el C (226 g) da [[qual.Q_cu_296_77_kJ_C|.1f]] kJ y [[qual.m_N2_boiled_g_C|.0f]] g: señales
cómodas para una balanza de 0,01 g y un cross-check independiente de Q/A (§4). La masa no es tan grande como para violar
Bi ≪ 1 (que depende de r, no de m): el radio de 1,9 cm de A da un tiempo de difusión r²/α = [[qual.tau_diff_s|.1f]] s con
α = [[qual.alpha_Cu_m2s|.2e]] m²/s, mucho menor que τ.</p>
<p><strong>¿Por qué una termocupla?</strong> Porque es el único sensor que se puede <em>soldar</em> dentro del cobre, con una
junta de masa despreciable, que cubre 77–300 K sin cambiar de régimen, no necesita excitación (sin autocalentamiento ni
corrientes en el baño) y da directamente una tensión que se digitaliza. El par chromel–alumel (tipo K) sigue siendo
sensible a 77 K (~[[phys.seebeck_K_77K_uVK|.0f]] µV/K; el tipo T o J también sirven, pero el K es el más robusto y el que estaba
disponible). La junta de referencia en agua con hielo fija T<sub>ref</sub> = 0 °C a centésimas de grado sin electrónica de
compensación. <em>Verificación con los datos:</em> la columna <code>Voltaje</code> va de [[qual.V_max_mV_A|.3f]] mV a 296 K hasta
[[qual.V_min_mV_A|.3f]] mV cerca de 77 K (corrida A); la tabla NIST del tipo K con referencia a 0 °C da +0,94 mV a 23 °C y
[[phys.emf_K_77K_mV|.1f]] mV a −196 °C. La pendiente local dT/dV de la calibración de la adquisición equivale a
[[qual.tc_sens_hi_uVK|.1f]] µV/K cerca de 295 K y [[qual.tc_sens_lo_uVK|.1f]] µV/K entre 78 y 90 K: es la curva del tipo K, no una
recta. Recalculando T desde <code>Voltaje</code> con el polinomio inverso NIST del tipo K la desviación máxima respecto de la
columna T es [[tc_check.B.max_abs_dev_K|.2f]] K (B) y [[tc_check.C.max_abs_dev_K|.2f]] K (C).</p>
<p><strong>¿Por qué amplificar antes de la MPLI?</strong> La señal completa de la corrida es de [[qual.tc_span_mV|.2f]] mV (de +0,94 a
−5,8 mV). Una placa genérica (supuesto: ±[[assume.adc_fs_V|.0f]] V, [[assume.adc_bits|]] bit) tiene un LSB de [[qual.adc_lsb_mV|.2f]] mV:
sin amplificar, <em>toda</em> la curva ocuparía [[qual.adc_counts_unamplified|.1f]] cuentas, es decir un solo escalón. Para
repartirla sobre ~1000 cuentas (~0,2 K) hace falta una ganancia ~[[qual.gain_for_1000_counts|.0f]]. Además el amplificador de
instrumentación (alta impedancia de entrada) aísla la termocupla del ruido de modo común de la PC. Los datos confirman que
se amplificó: el paso mínimo entre valores distintos de <code>Voltaje</code> en la corrida A es [[qual.V_step_uV_A|.3f]] µV
([[qual.T_step_K_A|.4f]] K), muy por debajo del LSB sin ganancia.</p>
<p><strong>¿Cómo modificar la superficie en forma reversible?</strong> Cualquier cambio que se pueda quitar sin mecanizar:
envolver el cilindro con film plástico (una o más vueltas, lo que se hizo: §5), con cinta o tela; aplicar grasa, aceite,
barniz o pintura removible; adherir arena o papel de lija; mojarlo con agua para que forme hielo al sumergirlo. Lo
<em>no</em> reversible es lijar, pulir o arenar el cobre. Un cambio reversible permite comparar dos estados de la
<em>misma</em> masa y geometría, que es lo que aísla el efecto de la superficie del de p = m/A.</p>
"""))

    S.append(dict(id="cv", title="2. Calor específico, T(t), t_c y Q/A(t)", figs=["Cv_models.png", "T_vs_t_ABC.png", "dTdt_vs_T.png", "Cv_diff.png", "QA_models_compare.png"], html="""
<p><strong>C<sub>v</sub>(T) de Einstein.</strong> Θ<sub>E</sub> vale [[cv.thetaE_300K|.1f]] K a 300 K y [[cv.thetaE_77K|.1f]] K a 77 K.
Resulta C<sub>v</sub>(300 K) = [[cv.Cv_300K|.2f]] y C<sub>v</sub>(77 K) = [[cv.Cv_77K|.2f]] J/(mol K)
(C<sub>v</sub>(300)/3R = [[cv.Cv_300K_over_3R|.3f]]). Contra Debye con el mismo Θ<sub>D</sub> ([[cv.debye_Cv_300K|.2f]] y
[[cv.debye_Cv_77K|.2f]] J/(mol K)) Einstein es exacto a 300 K y queda [[cv.einstein_vs_debye_maxdev_pct|.1f]] % por debajo a 77 K:
la imprecisión «sobre todo a bajas temperaturas» que anticipa la guía, y la mayor fuente de error sistemático de Q/A
cerca del final de cada corrida. El término electrónico da γT/C<sub>v</sub> = [[qual.gamma_T_over_Cv_77K_pct|.2f]] % a 77 K.
La entalpía 77→296 K es ∫C<sub>v</sub>dT = [[cv.enthalpy_77_296_Jmol|.0f]] J/mol = [[cv.enthalpy_77_296_Jkg|.0f]] J/kg
(Debye: [[cv.enthalpy_77_296_debye_Jmol|.0f]] J/mol).</p>
<p><strong>T(t) de los tres cilindros</strong> (Fig. 2). Las tres curvas tienen la misma forma: un descenso suave y cóncavo
desde ~296 K (régimen de película), una <em>caída abrupta</em> de decenas de kelvin en pocos segundos (colapso de la película)
y un plateau en T<sub>sat</sub>. La corrida A llega a [[qual.T_min_K_A|.1f]] K; B y C a [[qual.T_min_K_B|.1f]] y [[qual.T_min_K_C|.1f]] K.
El instante de inmersión t₀ (primera muestra 1 K por debajo de la inicial) es [[tc.A.t0_s|.1f]], [[tc.B.t0_s|.1f]] y [[tc.C.t0_s|.1f]] s.</p>
<p><strong>Limpieza y derivada.</strong> B y C contienen lecturas puntuales físicamente imposibles ([[qual.n_spikes_B|]] filas de B y
[[qual.n_spikes_C|]] de C con T &lt; 70 o &gt; 310 K; ninguna en A, C1, C3). El criterio del pipeline es más amplio,
|T − mediana₇| &gt; 8 K (8 K supera el mayor paso genuino fuera del colapso, ~2,5 K/muestra, y es menor que el menor
pico, 15 K): reemplaza [[clean.A.n_outliers|.0f]]/[[clean.B.n_outliers|.0f]]/[[clean.C.n_outliers|.0f]] muestras en A/B/C por
interpolación lineal. La derivada es Savitzky–Golay de [[run.sg_window|]] muestras (7,2 s), orden 2: la caída dura 5–7
muestras; ventanas ≥ 9 la ensanchan 20–30 K y la ventana 3 amplifica el ruido de cuantización (0,1 K) del plateau.</p>
<p><strong>Criterio de t<sub>c</sub> (decisión propia).</strong> t<sub>c</sub> es el instante de máximo |dT/dt| sobre T(t) suavizada,
buscado por debajo de [[run.T_search_max_K|.0f]] K (excluye el transitorio de inmersión, corrupto en B durante 15 s); el «rango
de temperatura del colapso» [T<sub>lo</sub>, T<sub>hi</sub>] es el intervalo contiguo donde |dT/dt| supera el [[run.frac|]] de su
máximo. Justificación: en película |dT/dt| ≲ 1 K/s, en el colapso el flujo sube más de un orden de magnitud; el máximo
de la derivada es unívoco y separado del ruido (pico/plateau = [[tc.A.peak_over_plateau|.1f]], [[tc.B.peak_over_plateau|.1f]],
[[tc.C.peak_over_plateau|.1f]] para A, B, C; umbral de detección 3), y el 50 % acota el evento sin depender del ruido de la
cola. Sensibilidad: barriendo la ventana SG en 3..11 y el umbral en 0,3..0,7 el instante t<sub>c</sub> no cambia (dispersión
[[tc.A.sens_t_spread_s|.1f]] s: siempre la misma muestra); los bordes de banda se mueven en T<sub>hi</sub> ∈ [[tc.A.sens_Thi_range_K|]] K (A),
[[tc.B.sens_Thi_range_K|]] (B), [[tc.C.sens_Thi_range_K|]] (C) y T<sub>lo</sub> ∈ [[tc.A.sens_Tlo_range_K|]] (A), [[tc.B.sens_Tlo_range_K|]] (B),
[[tc.C.sens_Tlo_range_K|]] (C). El intervalo de «caída abrupta» es por lo tanto ~112–115 K → 82–88 K, unos 30 K de ancho,
7–10 s de duración.</p>
<table><thead><tr><th>cil.</th><th>t<sub>c</sub> archivo [s]</th><th>t<sub>c</sub> desde t₀ [s]</th><th>T(t<sub>c</sub>) [K]</th>
<th>[T<sub>lo</sub>, T<sub>hi</sub>] [K]</th><th>|dT/dt|<sub>max</sub> [K/s]</th><th>espurios</th></tr></thead><tbody>
<tr><td>A</td><td>[[tc.A.t_s|.1f]]</td><td>[[tc.A.t_from_immersion_s|.1f]]</td><td>[[tc.A.T_K|.1f]]</td><td>[[[tc.A.Tlo_K|.1f]], [[tc.A.Thi_K|.1f]]]</td><td>[[tc.A.dTdt_max_Ks|.2f]]</td><td>[[clean.A.n_outliers|.0f]]</td></tr>
<tr><td>B</td><td>[[tc.B.t_s|.1f]]</td><td>[[tc.B.t_from_immersion_s|.1f]]</td><td>[[tc.B.T_K|.1f]]</td><td>[[[tc.B.Tlo_K|.1f]], [[tc.B.Thi_K|.1f]]]</td><td>[[tc.B.dTdt_max_Ks|.2f]]</td><td>[[clean.B.n_outliers|.0f]]</td></tr>
<tr><td>C</td><td>[[tc.C.t_s|.1f]]</td><td>[[tc.C.t_from_immersion_s|.1f]]</td><td>[[tc.C.T_K|.1f]]</td><td>[[[tc.C.Tlo_K|.1f]], [[tc.C.Thi_K|.1f]]]</td><td>[[tc.C.dTdt_max_Ks|.2f]]</td><td>[[clean.C.n_outliers|.0f]]</td></tr>
</tbody></table>
<p>T(t<sub>c</sub>) ≃ 102–105 K (ΔT ≃ 25–28 K) es la misma para los tres cuerpos dentro de 2 K: la temperatura de colapso es una
propiedad de la superficie y del líquido, no de la masa. La búsqueda sin la restricción T &lt; 200 K da la misma muestra
en los tres casos.</p>
<p><strong>Q/A(t) con la geometría medida</strong> (n/A de §3, ec. 1):</p>
<table><thead><tr><th>cil.</th><th>plateau película 150–250 K [kW/m²]</th><th>mínimo (Leidenfrost) [kW/m²]</th><th>ΔT<sub>min</sub> [K]</th>
<th>pico (flujo crítico) [kW/m²]</th><th>ΔT<sub>pico</sub> [K]</th></tr></thead><tbody>
<tr><td>A</td><td>[[qa.A.plateau_Wm2|.1f|x1e-3]]</td><td>[[qa.A.min_film_Wm2|.1f|x1e-3]]</td><td>[[qa.A.dT_at_min_K|.0f]]</td><td>[[qa.A.peak_Wm2|.0f|x1e-3]]</td><td>[[qa.A.dT_at_peak_K|.0f]]</td></tr>
<tr><td>B</td><td>[[qa.B.plateau_Wm2|.1f|x1e-3]]</td><td>[[qa.B.min_film_Wm2|.1f|x1e-3]]</td><td>[[qa.B.dT_at_min_K|.0f]]</td><td>[[qa.B.peak_Wm2|.0f|x1e-3]]</td><td>[[qa.B.dT_at_peak_K|.0f]]</td></tr>
<tr><td>C</td><td>[[qa.C.plateau_Wm2|.1f|x1e-3]]</td><td>[[qa.C.min_film_Wm2|.1f|x1e-3]]</td><td>[[qa.C.dT_at_min_K|.0f]]</td><td>[[qa.C.peak_Wm2|.0f|x1e-3]]</td><td>[[qa.C.dT_at_peak_K|.0f]]</td></tr>
</tbody></table>
<p>Q/A &gt; 0 en todas las muestras de la ventana de enfriamiento ([[qa.A.n_cooling_samples|]]/[[qa.B.n_cooling_samples|]]/[[qa.C.n_cooling_samples|]]
muestras, [[qa.A.n_nonpositive|]] no positivas). Los picos están por debajo del flujo crítico del NL (~1,5×10⁵ W/m²), como debe
ser; los plateaus de película de los tres cuerpos coinciden a [[qa.plateau_spread_pct|.0f]] % (máx−mín sobre media). Con una m/A
común para los tres (ronda 1, geometría nominal) la dispersión era ~78 %: <strong>la geometría medida hace que el flujo de
película salga independiente del cuerpo</strong>, que es lo que la física exige. El residuo (B, el más delgado, d = 2,2 cm, tiene
el flujo mayor) va en el sentido de las correlaciones de película para cilindros (h ∝ d<sup>−1/4</sup>), pero no se cuantificó.</p>

<h3>2.4 Einstein vs Debye, extendido a Q/A</h3>
<p>Tabulando ambos modelos entre 77 y 300 K (77, 90, 100, 120, 150, 180, 200, 220, 250, 280, 300 K): la diferencia
relativa (Einstein−Debye)/Debye vale [[cvcmp.max_abs_diff_pct|.1f]] % a [[cvcmp.max_abs_diff_T_K|.0f]] K (el extremo frío de la
grilla) y decrece monótonamente hasta ≈0 % a 300 K (Fig. 11); en valor absoluto la brecha máxima es
[[cv.Cv_77K|.2f]] − [[cv.debye_Cv_77K|.2f]] J/(mol K). Para saber si esto importa para las conclusiones (no sólo para C<sub>v</sub> en
sí) se recalculó Q/A(t) de los tres cilindros con C<sub>v,Debye</sub> en la misma T(t), dT/dt y geometría medida (Fig. 12,
cilindro C). El resultado: en el plateau de película (150–250 K) la diferencia es
[[cvcmp.qa.A.plateau_diff_pct|.2f]] % (A), [[cvcmp.qa.B.plateau_diff_pct|.2f]] % (B), [[cvcmp.qa.C.plateau_diff_pct|.2f]] % (C); en
el pico de flujo crítico [[cvcmp.qa.A.peak_diff_pct|.2f]] %, [[cvcmp.qa.B.peak_diff_pct|.2f]] %, [[cvcmp.qa.C.peak_diff_pct|.2f]] %;
en el mínimo de Leidenfrost [[cvcmp.qa.A.min_film_diff_pct|.2f]] %, [[cvcmp.qa.B.min_film_diff_pct|.2f]] %,
[[cvcmp.qa.C.min_film_diff_pct|.2f]] %. Es decir: elegir Einstein en vez de Debye cambia el plateau y el mínimo de Leidenfrost en
apenas una décima de por ciento, y el pico en ~3 %; en los tres casos el efecto queda por debajo (o del mismo orden que el más
chico) de la incerteza experimental de p (§3, 3-8 %) y muy por debajo de la
dispersión entre cuerpos (§2, [[qa.plateau_spread_pct|.0f|notag]] %). El 10 % de diferencia en C<sub>v</sub> sólo se manifiesta en la
práctica donde ΔT → 0 (T → 77 K), justo la región donde Q/A ya es indistinguible del ruido de cuantización (§2.5):
<strong>ninguna conclusión cuantitativa de este informe depende de si se usa Einstein o Debye</strong>; se mantiene Einstein porque la
guía la pide (ecs. 4–5) y porque su forma cerrada facilita la integral de entalpía.</p>

<h3>2.5 Propagación de incertidumbre de T a dT/dt, t<sub>c</sub> y Q/A</h3>
<p><strong>Cadena de error.</strong> La medición es una fem V del par termoeléctrico, digitalizada tras amplificarla con
ganancia G; la calibración fem→T (polinomio inverso tipo K) da T(V). Propagando en cuadratura:</p>
<div class="eq">σ<sub>T</sub><sup>2</sup> = (dT/dV)² (σ<sub>ADC</sub>/G)² + σ<sub>calib</sub>² + σ<sub>T,ref</sub>²</div>
<p>tres términos físicamente independientes: (i) cuantización del ADC referida a la termocupla a través de la pendiente
local de calibración dT/dV y la ganancia G; (ii) la incerteza propia del polinomio/calibración de la termocupla; (iii) la
incerteza de la junta de referencia (hielo, nominalmente 0 °C). <strong>Ninguna hoja de datos del ADC/amplificador de la MPLI ni
del baño de referencia está en las fuentes</strong>: (i) y (iii) quedan simbólicos. Sólo a modo de <em>ejemplo ilustrativo</em>, usando
la ganancia ya estimada en §1.2 para llenar ~1000 cuentas (supuesto ±[[assume.adc_fs_V|.0f]] V, [[assume.adc_bits|]] bit,
<code>assume.*</code>) se obtiene una cuantización referida a la termocupla de σ<sub>ADC</sub> ≃ [[sigmaT.sigma_ADC_uV|.2f]] µV, que da
σ<sub>T</sub> ≃ [[sigmaT.sigma_T_ADC_hi_K|.3f]] K cerca de 295 K y σ<sub>T</sub> ≃ [[sigmaT.sigma_T_ADC_lo_K|.3f]] K cerca de 80 K
(peor: la pendiente fem–T se aplana a baja T). <strong>Esto es un ejemplo bajo un supuesto explícito, no una especificación medida.</strong></p>
<p><strong>Propagación a dT/dt.</strong> La derivada Savitzky–Golay (ventana [[run.sg_window|.0f]], orden 2) es un filtro lineal cuyo
factor de ganancia de ruido es σ<sub>dT/dt</sub> = [[sigmaT.sg_gain_per_s|.3f]] s⁻¹ × σ<sub>T</sub> (calculado de los coeficientes del filtro, no
supuesto). Con el ejemplo anterior, σ<sub>dT/dt</sub> ≃ [[sigmaT.sigma_dTdt_hi_Ks|.3f]] K/s cerca de 295 K y
[[sigmaT.sigma_dTdt_lo_Ks|.3f]] K/s cerca de 80 K. <strong>Cruce con el dato real:</strong> el ruido efectivamente medido de dT/dt en el
plateau (T&lt;85 K) de la corrida C es [[bal2.noise_std_dTdt_plateau_C_Ks|.3f]] K/s (§4.4) — a
[[sigmaT.crosscheck_vs_observed_noise_pct|.0f]] % del valor ilustrativo: el supuesto de ADC/ganancia no es arbitrario, reproduce el
piso de ruido observado dentro de un factor razonable, aunque sigue sin ser una verificación del instrumento real.</p>
<p><strong>Propagación a t<sub>c</sub>.</strong> El colapso es agudo (pico/plateau = [[tc.A.peak_over_plateau|.0f]]–[[tc.B.peak_over_plateau|.0f]]):
una perturbación de σ<sub>dT/dt</sub> ~10⁻²–10⁻¹ K/s es &lt;1 % del pico y no cambia qué muestra se identifica como t<sub>c</sub>; el
piso real de incerteza es el muestreo mismo, σ<sub>tc</sub> ≈ Δt/2 = [[sigmaT.sigma_tc_halfsample_s|.2f]] s, consistente con la
dispersión ≤3 s ya reportada en el barrido de sensibilidad (§2). σ<sub>T</sub> importa mucho más para <em>dónde</em> se ubican los bordes
T<sub>lo</sub>, T<sub>hi</sub> de la banda de colapso que para t<sub>c</sub> mismo.</p>
<p><strong>Propagación a Q/A.</strong> Q/A = −(n/A) C<sub>v</sub>(T) dT/dt: en cuadratura, δ(Q/A)/(Q/A) = √[(δp/p)² + (δC<sub>v</sub>/C<sub>v</sub>)² +
(σ<sub>dT/dt</sub>/|dT/dt|)²]. El primer término es 3–8 % (§3), el segundo ≤10 % sólo cerca de 77 K (§2.4) y despreciable en el resto,
el tercero depende del régimen: en el plateau (|dT/dt| ~0,5 K/s) el ejemplo da
[[sigmaT.relQA_plateau_C_pct|.0f]] % (C), [[sigmaT.relQA_plateau_A_pct|.0f]] % (A); en el pico (|dT/dt| ~5–7 K/s) cae a
[[sigmaT.relQA_peak_C_pct|.1f]] % (C), [[sigmaT.relQA_peak_A_pct|.1f]] % (A): la señal es tan grande ahí que el ruido de temperatura
es irrelevante. El régimen más sensible es, de nuevo, el más cercano a 77 K, donde dT/dt → 0 y el término relativo diverge —
la misma región donde Einstein/Debye tampoco importaban.</p>
"""))

    S.append(dict(id="geom", title="3. Geometría, moles y p = m/A; relación p–t_c", figs=["tc_vs_p.png", "tc_vs_p_models.png", "pred_D.png"], html="""
<p>Dimensiones medidas por el humano (calibre y balanza; <code>inbox.jsonl</code>), ±0,1 cm en h y d, ±0,1 g en m. Área
A = πd²/2 + πdh con δA = √{[π(d+h)δd]² + [πd δh]²}; n = m/M<sub>Cu</sub> con M<sub>Cu</sub> = 63,546 g/mol; p = m/A con
δp/p = √{(δm/m)² + (δA/A)²} (propagación lineal, errores independientes).</p>
<table><thead><tr><th>cil.</th><th>h [cm]</th><th>d [cm]</th><th>m [g]</th><th>A [cm²]</th><th>A humano [cm²]</th><th>n [mol]</th><th>p [kg/m²]</th><th>m/V [kg/m³]</th></tr></thead><tbody>
<tr><td>A</td><td>[[geom.A.h_m|.1f|x100]]</td><td>[[geom.A.d_m|.1f|x100]]</td><td>[[geom.A.m_kg|.1f|x1000]]</td><td>[[geom.A.area_m2|.1f|x1e4]] ± [[geom.A.darea_m2|.1f|x1e4]]</td><td>[[geom.A.area_stated_cm2|.0f]] ± 4</td><td>[[geom.A.n_mol|.3f]] ± [[geom.A.dn_mol|.3f]]</td><td>[[geom.A.p_kgm2|.1f]] ± [[geom.A.dp_kgm2|.1f]]</td><td>[[geom.A.rho_from_mV_kgm3|.0f]]</td></tr>
<tr><td>B</td><td>[[geom.B.h_m|.1f|x100]]</td><td>[[geom.B.d_m|.1f|x100]]</td><td>[[geom.B.m_kg|.1f|x1000]]</td><td>[[geom.B.area_m2|.1f|x1e4]] ± [[geom.B.darea_m2|.1f|x1e4]]</td><td>[[geom.B.area_stated_cm2|.0f]] ± 2</td><td>[[geom.B.n_mol|.3f]] ± [[geom.B.dn_mol|.3f]]</td><td>[[geom.B.p_kgm2|.1f]] ± [[geom.B.dp_kgm2|.1f]]</td><td>[[geom.B.rho_from_mV_kgm3|.0f]]</td></tr>
<tr><td>C</td><td>[[geom.C.h_m|.1f|x100]]</td><td>[[geom.C.d_m|.1f|x100]]</td><td>[[geom.C.m_kg|.1f|x1000]]</td><td>[[geom.C.area_m2|.1f|x1e4]] ± [[geom.C.darea_m2|.1f|x1e4]]</td><td>[[geom.C.area_stated_cm2|.0f]] ± 2</td><td>[[geom.C.n_mol|.3f]] ± [[geom.C.dn_mol|.3f]]</td><td>[[geom.C.p_kgm2|.1f]] ± [[geom.C.dp_kgm2|.1f]]</td><td>[[geom.C.rho_from_mV_kgm3|.0f]]</td></tr>
</tbody></table>
<p>Las áreas recalculadas coinciden con las del humano dentro de su ±. Los n del humano ([[geom.A.n_stated_mol|.3f]],
[[geom.B.n_stated_mol|.3f]], [[geom.C.n_stated_mol|.3f]] mol) corresponden a M = [[geom.M_Cu_implied_by_stated_n|.2f|x1000]] g/mol; la
diferencia (0,07 %) es irrelevante. m/V queda 1–3 % por debajo de ρ<sub>Cu</sub> = [[phys.rho_Cu|.0f]] kg/m³: consistente con
cobre macizo con el orificio de la termocupla y el redondeo del calibre.</p>
<p><strong>Relación p–t<sub>c</sub> (derivada).</strong> En capacidad concentrada dT/dt = −(Q/A)/(p c): a igual Q/A(T) (misma
superficie, mismo baño) el tiempo para llegar de T₀ a la temperatura de colapso T<sub>c</sub> es
t<sub>c</sub> = p ∫<sub>T<sub>c</sub></sub><sup>T₀</sup> c(T) dT / (Q/A)(T), <em>proporcional a p</em>, y T(t<sub>c</sub>) debe ser la misma.
Lo segundo se cumple (§2: 102–105 K). Lo primero, aproximadamente (Fig. 4):</p>
<table><thead><tr><th></th><th>A</th><th>B</th><th>C</th></tr></thead><tbody>
<tr><td>t<sub>c</sub> desde t₀ [s]</td><td>[[tc.A.t_from_immersion_s|.1f]]</td><td>[[tc.B.t_from_immersion_s|.1f]]</td><td>[[tc.C.t_from_immersion_s|.1f]]</td></tr>
<tr><td>p [kg/m²]</td><td>[[geom.A.p_kgm2|.1f|notag]] ± [[geom.A.dp_kgm2|.1f|notag]]</td><td>[[geom.B.p_kgm2|.1f|notag]] ± [[geom.B.dp_kgm2|.1f|notag]]</td><td>[[geom.C.p_kgm2|.1f|notag]] ± [[geom.C.dp_kgm2|.1f|notag]]</td></tr>
<tr><td>t<sub>c</sub>/p [s m²/kg]</td><td>[[rel.tc_over_p.A|.2f]] ± [[rel.tc_over_p.A_err|.2f]]</td><td>[[rel.tc_over_p.B|.2f]] ± [[rel.tc_over_p.B_err|.2f]]</td><td>[[rel.tc_over_p.C|.2f]] ± [[rel.tc_over_p.C_err|.2f]]</td></tr>
</tbody></table>
<p>t<sub>c</sub> crece monótonamente con p (A &gt; C &gt; B en ambos), pero t<sub>c</sub>/p no es constante: media
[[rel.tc_over_p.mean|.2f]] s m²/kg, dispersión máx−mín [[rel.tc_over_p.spread_pct|.0f]] % (desviación estándar
[[rel.tc_over_p.std_pct|.0f]] %). El ajuste pesado t<sub>c</sub> = k·p por el origen da k = [[rel.tc_vs_p.slope_s_m2_per_kg|.2f]] s m²/kg con
χ²/ν = [[rel.tc_vs_p.chi2_dof|.1f]] y residuo máximo [[rel.tc_vs_p.max_resid_pct|.0f]] %: la dispersión es real, no error geométrico.
Por pares: t<sub>c</sub>(B)/t<sub>c</sub>(A) = [[rel.tc_ratio_BA|.2f]] frente a p<sub>B</sub>/p<sub>A</sub> = [[rel.p_ratio_BA|.2f]] ± [[rel.p_ratio_BA_err|.2f]];
t<sub>c</sub>(C)/t<sub>c</sub>(A) = [[rel.tc_ratio_CA|.2f]] frente a p<sub>C</sub>/p<sub>A</sub> = [[rel.p_ratio_CA|.2f]] ± [[rel.p_ratio_CA_err|.2f]].
La misma desviación aparece en un test que no usa la geometría: si Q/A fuera idéntico, el cociente inverso de velocidades
de enfriamiento a 200 K debería igualar el de t<sub>c</sub>, y da [[rel.inv_rate_ratio_BA_200K|.2f]] (B/A) y [[rel.inv_rate_ratio_CA_200K|.2f]] (C/A):
a 5–10 % de los cocientes de t<sub>c</sub> pero 10–25 % por debajo de los de p.</p>
<p><strong>Interpretación:</strong> t<sub>c</sub> ∝ p vale a ~15 %; el residuo es el flujo de película, que <em>no</em> es exactamente el
mismo para los tres cuerpos (§2: B tiene el plateau mayor y por eso se enfría más rápido de lo que su p predice). Un cuerpo
más delgado tiene una película de vapor más fina y un h algo mayor; además la posición en el dewar, el subenfriamiento del
baño y el estado de la superficie varían entre corridas. Es decir: <em>p fija la escala de tiempo</em> (el cuerpo con más
masa por unidad de área tarda proporcionalmente más en llegar a la temperatura de colapso), y la temperatura a la que
colapsa no depende de p.</p>

<h3>3.3 t_c(p) como problema de modelado: ley de potencia y recta general</h3>
<p>El balance térmico simplificado de arriba predice t_c proporcional a p <em>por el origen</em> (1 parámetro): es la única forma
funcional derivada de la física, no ajustada. Con sólo A, B, C (3 puntos) se pueden además ajustar formas de 2 parámetros que no
están motivadas por ningún balance —una ley de potencia t_c = A·p^n y una recta general t_c = k·p + b— y
compararlas (Fig. 13). Resultado: ley de potencia (ver
<code>fit.power_law.params</code><sup class="src" title="Parameters of the power law fit t_c(p) over A, B, C">[fit.power_law.params]</sup> en <code>provenance.json</code>: n ≈ 1,52, A ≈ 0,48) con residuos máx.
[[fit.power_law.max_abs_resid_pct|.1f]] %; recta general (ver <code>fit.general_linear.params</code>: k ≈ 5,6 s m²/kg, b ≈ −98 s) con
residuos máx. [[fit.general_linear.max_abs_resid_pct|.1f]] %; el ajuste por el origen (motivado por el balance, 1 parámetro) tiene
residuos máx. [[fit.through_origin.max_abs_resid_pct|.1f]] %, bastante mayores.</p>
<p><strong>Esto no es evidencia de que la ley de potencia o la recta general sean correctas.</strong> Con
[[fit.n_datapoints|]] puntos y 2 parámetros libres quedan sólo [[fit.power_law.dof|]] grado(s) de libertad: dos de los tres puntos
fijan los parámetros y el tercero es la única información real que el ajuste usa. Cualquier forma de 2 parámetros
razonablemente suave logra residuos pequeños casi sin importar cuál sea la física real —eso es lo que muestran los residuos
comparables de la ley de potencia y la recta general (ajustan mejor que el modelo físico de 1 parámetro simplemente por tener un
grado de libertad más, no necesariamente porque capturen mejor la física). El ajuste por el origen, en cambio, conserva
[[fit.through_origin.dof|]] grados de libertad reales y sus residuos miden genuinamente cuánto se aparta cada cuerpo de la
proporcionalidad simple; ya se interpretaron arriba como el flujo de película no siendo exactamente igual entre cuerpos.
<strong>Conclusión defendible: t_c crece con p y la proporcionalidad simple da el orden de magnitud correcto a ~15–25 %; la forma
funcional exacta (¿lineal con corrección, potencia con n≈1,5, u otra?) no está determinada por este experimento</strong> —hace
falta un cuarto punto (o más) para distinguir entre modelos con 2 o más parámetros.</p>

<h3>3.4 Predicción para un cuarto cilindro D hipotético</h3>
<p>Se define D con p<sub>D</sub> = (p<sub>B</sub> + p<sub>C</sub>)/2 = [[pred.D.p_kgm2|.1f]] ± [[pred.D.dp_kgm2|.1f]] kg/m² (punto medio
entre B y C, elegido para que la predicción sea una interpolación y no una extrapolación). Los tres modelos de 3.3 predicen
t_c(D) = [[pred.D.t_c_through_origin_s|.0f]] s (por el origen), [[pred.D.t_c_power_law_s|.0f]] s (ley de potencia),
[[pred.D.t_c_general_linear_s|.0f]] s (recta general) (Fig. 14): un rango de [[pred.D.model_spread_s|.0f]] s, más del 15 % del
valor central, que viene enteramente de <em>qué forma funcional se elige</em>, no de la incerteza de los datos. En cambio,
perturbando la geometría medida de A, B y C dentro de su ±1σ en las 8 combinaciones posibles y recalculando el ajuste por el
origen, la predicción sólo se mueve dentro de un rango angosto (ver <code>pred.D.geom_sensitivity_range_s</code> en
<code>provenance.json</code>): la incerteza de medición (geometría) es pequeña frente a la incerteza de modelo. <strong>Con sólo tres
cilindros, la interpolación en p (D está entre B y C) es razonable; la elección de forma funcional no lo es</strong>: se reporta el
rango [[pred.D.t_c_power_law_s|.0f]]–[[pred.D.t_c_through_origin_s|.0f]] s como la predicción honesta, no un único número.</p>
"""))

    S.append(dict(id="balanza", title="4. Balanza: masa de N₂ vs tiempo", figs=["balance.png"], html="""
<p><code>medicion_balanza.csv</code> tiene lecturas a [[bal.dt_s|.3f]] s durante 480 s, taradas (arranca cerca de 0 g y decrece):
mide la <em>masa evaporada</em> −Δm(t). Tres etapas, con puntos de cambio detectados en los datos (Fig. 5):</p>
<ol>
<li><strong>Evaporación ambiente</strong> (antes de sumergir): pérdida lineal por el calor que entra por las paredes y la boca del
dewar; pendiente [[bal.slope1_gs|.1f|x1000]] ± [[bal.slope1_err_gs|.1f|x1000]] mg/s (mínimos cuadrados, 2 lecturas espurias descartadas,
rms 0,15 g) hasta t₁ = [[bal.t1_end_s|.1f]] s. El fin de la etapa es el mayor salto positivo de 1 s de todo el registro,
+[[bal.jump_g|.1f]] g: el empuje del cuerpo que entra al líquido.</li>
<li><strong>Inmersión</strong>: el N₂ se evapora al ritmo que fija Q/A del cobre. La etapa termina con el <em>burst</em> de ebullición
violenta del colapso (Listerman et al.): ventana donde la tasa suavizada (SG 11 s) supera la mitad de su mínimo,
[[bal.burst_start_s|.1f]]–[[bal.t3_start_s|.1f]] s, [[bal.burst_dm_g|.1f]] g evaporados en el burst. Masa evaporada en la etapa
[[bal.dm_stage2_g|.1f]] g en [[bal.stage2_duration_s|.0f]] s; neta de la evaporación ambiente (pendiente 1 × duración)
[[bal.dm_stage2_net_g|.1f]] g, equivalente a Q = Δm L<sub>v</sub> = [[bal.Q_balance_J|.1f|x1e-3]] kJ.</li>
<li><strong>Evaporación final</strong> (cilindro a 77 K, sólo convección): otra recta desde t₃ = [[bal.t3_start_s|.1f|notag]] s,
pendiente [[bal.slope3_gs|.1f|x1000]] ± [[bal.slope3_err_gs|.1f|x1000]] mg/s sobre toda la etapa (rms 0,38 g: no es recta, el cobre
sigue enfriándose de 80 a 77 K) y [[bal.slope3_tail_gs|.1f|x1000]] mg/s en los últimos 20 s.</li>
</ol>
<p><strong>Comparación de pendientes.</strong> Con el cilindro frío dentro, la etapa 3 debería tener pendiente igual o algo mayor
en módulo que la 1: el aporte ambiente es el mismo, más la conducción por el alambre de la termocupla y el hilo de
suspensión que ahora tocan el líquido, más el nivel más bajo. Cociente [[bal.slope_ratio|.2f]] sobre toda la etapa 3 y
[[bal.slope_ratio_tail|.2f]] en la cola: una vez que el cobre está a la temperatura del baño la tasa ambiente se recupera a 4 %.</p>
<p><strong>¿Qué cilindro estaba en la balanza?</strong> El archivo no lo dice. Dos estimaciones independientes de la masa sumergida:
(i) energía, m = Q<sub>balanza</sub>/∫c dT = [[bal.m_eff_energy_kg|.3f]] kg (cota superior [[bal.m_eff_energy_upper_kg|.3f]] kg si el vapor
sale sobrecalentado a 186 K); (ii) empuje, V = 21,7 g/ρ<sub>NL</sub> = [[bal.V_buoyancy_m3|.1f|x1e6]] cm³ y m = ρ<sub>Cu</sub>V =
[[bal.m_eff_buoy_kg|.3f]] kg. Ambas encierran a C (226,2 g): m<sub>empuje</sub>/m<sub>C</sub> = [[bal.m_buoy_over_mC|.2f]],
m<sub>energía</sub>/m<sub>C</sub> = [[bal.m_energy_over_mC|.2f]], mientras que A daría 0,22–0,26 y B 1,3–1,5
(Q<sub>balanza</sub>/Q<sub>Cu</sub> = [[bal.Q_ratio_A|.2f]], [[bal.Q_ratio_B|.2f]], [[bal.Q_ratio_C|.2f]] para A, B, C). El volumen desplazado
es [[bal.V_buoy_over_V_C|.2f]] veces el volumen geométrico de C ([[bal.V_C_m3|.1f|x1e6]] cm³): <strong>la corrida de balanza es el
cilindro C, totalmente sumergido</strong> ([[bal.body_identified|]]).</p>
<p><strong>Cross-check calorimétrico.</strong> Q<sub>balanza</sub>/Q<sub>Cu</sub>(C) = [[bal.Q_balance_J|.1f|x1e-3]]/[[bal.Q_cu_J|.1f|x1e-3]] kJ =
[[bal.Q_ratio|.2f]]. El 7 % faltante es del orden del sobrecalentamiento del vapor que sale del dewar (no medido) y de la
incerteza de L<sub>v</sub> y C<sub>v</sub> (Einstein queda 10 % bajo a 77 K). La duración de la etapa 2 ([[bal.stage2_duration_s|.0f|notag]] s)
supera en [[bal.stage2_vs_tc_C_s|.0f]] s al t<sub>c</sub> de la corrida de temperatura de C (168 s): son inmersiones distintas; es una
medida de la repetibilidad de t<sub>c</sub> (incluye los 8 s del burst).</p>
<p><strong>Q/A por dos caminos independientes.</strong> Identificado el cuerpo, la potencia de la balanza (tasa neta de evaporación
× L<sub>v</sub>) dividida por A<sub>C</sub> da Q/A sin usar ni C<sub>v</sub> ni la termocupla: [[bal.power_post_immersion_W|.0f]] W →
[[bal.QA_post_immersion_Wm2|.1f|x1e-3]] kW/m² recién sumergido y [[bal.power_preburst_W|.0f]] W → [[bal.QA_preburst_Wm2|.1f|x1e-3]] kW/m² justo
antes del burst. La calorimetría de la corrida C (ec. 1) da [[qa.C.calorimetric_hot_Wm2|.1f|x1e-3]] kW/m² (230–290 K) y
[[qa.C.calorimetric_cold_Wm2|.1f|x1e-3]] kW/m² (10–40 K por encima de la banda de colapso): cocientes [[bal.QA_ratio_hot|.2f]] y
[[bal.QA_ratio_cold|.2f]]. <strong>Dos métodos, dos corridas, acuerdo a 15 %.</strong></p>

<h3>4.4 Modelo cuantitativo de la brecha entre pendientes</h3>
<p>La comparación naive de toda la etapa 3 contra la etapa 1 da [[bal2.slope1_mgs|.1f]] mg/s vs [[bal2.slope3_whole_mgs|.1f]] mg/s
([[bal2.slope_gap_naive_pct|.0f]] % de diferencia, la brecha que motiva esta sección) y una potencia residual promedio
P<sub>res</sub> = (|pendiente<sub>3</sub>| − |pendiente<sub>1</sub>|) L<sub>v</sub> = [[bal2.Pres_avg_naive_W|.2f]] W, cercana a la
estimación previa de ~7,1 W. Pero la etapa 3 completa <em>no es una recta</em> (rms 0,38 g vs 0,05 g del modelo que sigue): el
cilindro sigue entregando calor sensible mientras termina de bajar de la banda de colapso a 77 K, así que ese promedio mezcla un
transitorio real con el fondo asintótico. Separando explícitamente ambas contribuciones con un ajuste no lineal de la etapa 3,</p>
<div class="eq">m(t) = m₀ + a·t − (P₀/L<sub>v</sub>)·τ·(1 − e<sup>−t/τ</sup>), &nbsp;&nbsp; a = pendiente de la cola (fondo ambiente)</div>
<p>(t medido desde el fin del burst) se obtiene P₀ = [[bal2.model_P0_W|.2f]] W (potencia residual justo después del burst) con
τ = [[bal2.model_tau_s|.2f]] s (tiempo de relajación), rms [[bal2.model_rms_g|.3f]] g —siete veces mejor que la recta simple
(Fig. 15)—. El promedio temporal de este modelo sobre la duración real de la etapa 3 da
[[bal2.model_Pavg_W|.2f]] W, consistente con el [[bal2.Pres_avg_naive_W|.1f|notag]] W naive y con la estimación previa de ~7,1 W:
<strong>ambos números coexisten porque describen promedios distintos de una potencia que decae</strong>, no dos mediciones en
conflicto.</p>
<p><strong>¿Qué temperatura efectiva es compatible con P₀?</strong> Invirtiendo la ec. (1), P₀ = n<sub>C</sub> C<sub>v</sub>(T) ΔT₀/τ da
ΔT₀ = [[bal2.model_dT0_K|.1f]] K, es decir T₀ ≈ 77 + [[bal2.model_dT0_K|.0f|notag]] = [[bal2.model_T0_K|.0f|notag]] K por encima
del baño justo tras el burst. Esa temperatura (~90–91 K) es compatible, dentro de lo esperable entre inmersiones distintas, con
el borde inferior de la banda de colapso medido en la corrida de temperatura de C, T<sub>lo</sub> =
[[bal2.Tlo_C_temperature_run_K|.1f]] K (diferencia [[bal2.model_T0_vs_Tlo_K|.1f]] K): el modelo dice que el cilindro sale del
colapso todavía a decenas de kelvin sobre 77 K y se relaja con τ ≈ 15 s, consistente con el rango de temperaturas del colapso
medido de forma independiente. El coeficiente h implícito en τ = n C<sub>v</sub>/(h A<sub>C</sub>) es
[[bal2.model_h_implied_Wm2K|.0f]] W/(m² K), entre los órdenes de magnitud de película (~150) y nucleada (~10⁴) ya usados en §1.2:
razonable para una relajación en régimen de transición, aunque no es un h calibrado.</p>
<p><strong>¿Y la hipótesis de 77 K exacto?</strong> Se sostiene sólo al final de la etapa 3: el residuo basado en la cola
([[bal2.Pres_tail_naive_W|.2f]] W) implica, vía la misma ec. (1), un |dT/dt| de [[bal2.dTdt_implied_tail_Ks|.3f]] K/s, comparable
al piso de ruido de dT/dt observado directamente en el plateau de la corrida de temperatura de C
([[bal2.noise_std_dTdt_plateau_C_Ks|.3f]] K/s, media [[bal2.noise_mean_dTdt_plateau_C_Ks|.4f]] K/s ≈ 0): al final del registro el
cilindro es indistinguible de 77 K dentro de la resolución de la termocupla. En cambio, el residuo naive de toda la etapa 3
implica [[bal2.dTdt_implied_avg_Ks|.3f]] K/s, muy por encima de ese piso: si esa tasa se sostuviera sería visible en una traza de
temperatura, lo que es consistente con que <em>no</em> se sostiene —es el transitorio inicial (P₀, τ) descrito arriba, no un
sesgo sistemático de la balanza. <strong>Conclusión: la brecha del ~[[bal2.slope_gap_naive_pct|.0f|notag]] % se explica
razonablemente como calor sensible residual del cilindro relajándose desde la banda de colapso hasta 77 K con τ ≈ 15 s, no como
un artefacto experimental</strong>; las incertezas dominantes son sistemáticas (L<sub>v</sub>, C<sub>v</sub> a baja T ~10 %, §2.4) más que
estadísticas (los errores de ajuste de P₀ y τ son ≤3 %).</p>
"""))

    S.append(dict(id="film", title="5. Efecto del recubrimiento (cilindro C con film)", figs=["T_vs_t_C_film.png", "C1_sensitivity.png"], html="""
<p>Tres corridas del mismo cuerpo (C, [[geom.C.p_kgm2|.1f|notag]] kg/m²): sin film (t<sub>c</sub> = [[tc.C.t_from_immersion_s|.1f|notag]] s desde t₀),
1 vuelta y 3 vueltas (Fig. 6). Hechos crudos, visibles sin procesamiento: la corrida con 1 vuelta pasa de 296 K a &lt; 80 K en
[[film.t_to_80K.C1_s|.1f]] s desde la inmersión (4 muestras, |dT/dt|<sub>max</sub> = [[tc.C1.dTdt_max_Ks|.1f]] K/s) y luego permanece en
el plateau durante los [[qual.duration_s_C1|.0f]] s restantes; la de 3 vueltas baja en forma <em>suave y monótona</em> de 295 a
[[qual.T_min_K_C3|.1f]] K en [[qual.duration_s_C3|.0f]] s (&lt; 80 K a los [[film.t_to_80K.C3_s|.1f]] s), sin caída abrupta: |dT/dt| decrece
monótonamente, [[rate.C3.dTdt_200K|.2f]], [[rate.C3.dTdt_150K|.2f]], [[rate.C3.dTdt_120K|.2f]], [[rate.C3.dTdt_100K|.2f]] K/s a 200/150/120/100 K,
frente a [[rate.C.dTdt_200K|.2f]] K/s a 200 K del C desnudo. El criterio de t<sub>c</sub> no detecta colapso en C1 ni en C3
(detected = [[tc.C1.detected|]] / [[tc.C3.detected|]]); los «t<sub>c</sub>» formales ([[tc.C1.t_from_immersion_s|.1f]] y [[tc.C3.t_from_immersion_s|.1f]] s;
Δt<sub>c</sub> = [[film.dtc_1_s|.0f]] y [[film.dtc_3_s|.0f]] s respecto del C desnudo) son el máximo de la derivada de una curva sin plateau,
no un evento. La comparación honesta es el tiempo hasta 80 K: [[film.t_to_80K.C_s|.0f]] s (desnudo), [[film.t_to_80K.C1_s|.1f|notag]] s (1 vuelta),
[[film.t_to_80K.C3_s|.0f|notag]] s (3 vueltas).</p>
<p><strong>Interpretación.</strong> El film no actúa como aislante: una vuelta de [[assume.film_thickness_m|.0f|x1e6]] µm con
k = [[assume.film_k|.1f]] W/(m K) tiene resistencia t/k = [[qual.R_film1_m2KW|.1e]] m² K/W, apenas el [[qual.film1_over_vapour_pct|.1f]] % de la
resistencia de la película de vapor 1/h = [[qual.R_vapour_m2KW|.1e]] m² K/W ([[qual.film3_over_vapour_pct|.1f]] % con tres vueltas). Lo que
cambia es la <em>efusividad</em> de la superficie que toca el líquido: T<sub>i</sub> baja de [[qual.T_contact_Cu_LN2_K|.0f]] K (cobre
desnudo) a [[qual.T_contact_film_LN2_K|.0f]] K (film): la superficie externa del film cae de inmediato por debajo del punto de
Leidenfrost, no se sostiene la capa de vapor y el cuerpo entra en ebullición nucleada desde el principio. Con una vuelta
ajustada el cobre queda expuesto a h ~ 10⁴ W/(m² K) y se enfría en segundos. Con tres vueltas el arrollado deja gas atrapado
entre capas; una lámina de N₂ gaseoso de 50 µm tiene R ≈ 50×10⁻⁶/[[phys.k_N2vap|.4f|notag]] ≈ 7×10⁻³ m² K/W, comparable a la de la
película de vapor: el flujo queda limitado por conducción a través del envoltorio —un <em>aislante real</em> esta vez— y la
curva es suave (Q/A «plateau» [[qa.C3.plateau_Wm2|.0f|x1e-3]] kW/m², el doble del C desnudo pero sin transición), porque la
transición de régimen ocurre en la cara externa del film desde t = 0 y ya no hay película de vapor que colapsar.
<strong>En síntesis:</strong> el recubrimiento <em>desestabiliza</em> la capa de vapor (la elimina), y su efecto sobre T(t) depende de
si además introduce una resistencia térmica propia (3 vueltas) o no (1 vuelta).</p>
<p><strong>Anomalía que sigue abierta.</strong> Enfriar C (226 g, 48,9 cm²) 296→77 K en 10 s exige un flujo medio
[[qual.flux_C1_10s_Wm2|.0f|x1e-3]] kW/m², [[qual.flux_C1_over_CHF|.1f]] veces el flujo crítico del NL; el pico calorimétrico de C1 es
[[qa.C1.peak_Wm2|.0f|x1e-3]] kW/m². Con la geometría medida la anomalía se reduce (era 3× con el nominal) pero no desaparece.</p>

<h3>5.1 Investigación cuantitativa de la anomalía de C1</h3>
<p>Cinco causas posibles, revisadas con los datos disponibles:</p>
<ul>
<li><strong>Calidad de los datos:</strong> sin espurios (<code>clean.C1.n_outliers</code> = 0); la caída de 296 a &lt;80 K ocurre en apenas
[[c1x.n_samples_full_transition|]] muestras ([[c1x.duration_full_transition_s|.1f]] s), a [[run.dt_s|.2f|notag]] s de muestreo: son
datos limpios pero extremadamente escasos para esta transición puntual.</li>
<li><strong>Derivada dT/dt y sensibilidad al suavizado:</strong> recalculando el Q/A pico de C1 con ventanas Savitzky–Golay de 3 a 11
muestras (Fig. 17) el resultado va de [[c1x.peak_Wm2_vs_window|]] W/m² extremo a extremo —factor
[[c1x.peak_window_spread_ratio|.1f]]×—. Con sólo [[c1x.n_samples_full_transition|]] muestras cubriendo toda la caída, el "pico" no
es una cantidad numéricamente estable: <strong>gran parte de la magnitud reportada es artefacto de la elección de ventana, no un
único flujo físico bien definido.</strong></li>
<li><strong>Instante de inmersión:</strong> no ambiguo (t₀ = [[tc.C1.t0_s|.1f]] s); el registro crudo muestra T todavía en 296 K una
muestra antes del primer descenso, consistente con una inmersión bien capturada, sólo que el proceso posterior es demasiado
rápido para el muestreo.</li>
<li><strong>Validez del modelo de cuerpo concentrado (Biot):</strong> el flujo pico con ventana 5 implica, para un ΔT de referencia
~100 K, un coeficiente equivalente h ≈ [[c1x.h_equiv_at_peak_Wm2K|.0f]] W/(m² K) y Bi = h L<sub>c</sub>/k<sub>Cu</sub> ≈
[[c1x.Bi_at_peak|.2f]]: ya no es &lt;&lt;1 con margen holgado como en el resto del análisis (§1.2, Bi<sub>película</sub> ~10⁻³), aunque
tampoco es &gt;&gt;1. La hipótesis de cuerpo isotermo es <em>marginal</em>, no claramente violada, durante este transitorio
específico.</li>
<li><strong>Posible artefacto de la termocupla (junta mojada):</strong> la temperatura de plateau de C1
([[tc.C1.plateau_T_K|.2f]] K) difiere de la de C desnudo ([[tc.C.plateau_T_K|.2f]] K) en sólo
[[c1x.plateau_T_diff_K|.2f]] K, del orden del propio ruido del plateau: <strong>los datos ni confirman ni descartan</strong> que la
unión haya quedado en contacto con líquido infiltrado en vez de con el bulk de cobre.</li>
</ul>
<p><strong>Balance de evidencia:</strong> lo que está <em>apoyado por los datos</em> es que la resolución temporal (2 muestras/s
frente a una transición de ~8 s) hace que el pico de Q/A reportado dependa fuertemente de una elección metodológica (ventana de
suavizado) y que el Biot deja de ser despreciable con margen; ambos bastan para explicar una gran fracción de la anomalía sin
apelar a nueva física. Lo que sigue siendo <em>sólo hipótesis, no descartable ni confirmable</em> con este dataset es si además el
flujo crítico real sobre una superficie plástica supera el de cobre desnudo, y si la termocupla estuvo leyendo una zona local en
vez del bulk. No se descartan los datos: se acota qué tan lejos se puede llevar su interpretación cuantitativa.</p>
"""))

    S.append(dict(id="etapas", title="6. Q/A vs ΔT y las seis etapas", figs=["QA_dT_stages_C.png", "QA_vs_dT_C_lin.png", "QA_vs_dT_C_log.png", "QA_vs_dT_A_log.png", "QA_vs_dT_B_log.png"], html="""
<p>La Fig. 16 superpone las seis etapas de la guía directamente sobre los datos reales de Q/A vs ΔT del cilindro C (escala
log–log), con el sentido temporal marcado explícitamente: el experimento es un enfriamiento, así que el cilindro recorre la
curva de <strong>derecha a izquierda</strong> (ΔT decreciente), al revés que el alambre calentado de la guía. Estado de cada etapa con
estos datos: <strong>VI</strong> (película + radiación) — sólo indicios: la radiación calculada es del
[[qual.q_rad_over_film_pct|.1f|notag]] % del flujo de película y no se resuelve como un tramo distinguible de V, sólo se estimó por separado (§1.2); <strong>V</strong>
(película estable) — observada, es el tramo largo y suave; <strong>IV</strong> (transición) — observada, es la banda
[T<sub>lo</sub>,T<sub>hi</sub>] medida (§2); <strong>III–II</strong> (nucleada) — observada pero con pocas muestras (5–7 a 1,44 s), el pico
de Q/A es el flujo crítico; <strong>I</strong> (convección) — no resuelta: cerca de 77 K, Q/A calculado es del orden del ruido de
cuantización de dT/dt (§2.5), no una medición confiable del régimen de convección natural. No se fuerza ninguna etapa que el
experimento no resuelva.</p>
<p>La curva de Nukiyama de la Fig. 1 de la guía se mide con un alambre <em>calentado</em> en estado estacionario y se recorre de
izquierda a derecha; nuestro cilindro la recorre <em>al revés</em>, de derecha a izquierda, y en forma transitoria (Figs. 7–10,
cilindro C como referencia):</p>
<ul>
<li><strong>VI (película + radiación)</strong>, ΔT ≃ 220 K al sumergir. La radiación a través del vapor es
εσ(T⁴ − T<sub>sat</sub>⁴) = [[qual.q_rad_296_Wm2|.1f]] W/m² con ε = [[assume.eps_Cu|.2f]], sólo el [[qual.q_rad_over_film_pct|.1f]] % del flujo de
película: para Cu a 300 K la etapa VI es indistinguible de la V (para el alambre de Pt a ΔT ~ 1000 K sí importa). En el
gráfico: extremo derecho, ΔT &gt; 150 K, Q/A ≃ 20–30 kW/m², levemente creciente con ΔT.</li>
<li><strong>V (película estable)</strong>, ΔT desde ~150 K hasta el mínimo en ΔT ≃ [[qa.C.dT_at_min_K|.0f|notag]] K: Q/A decrece lentamente de ~20 a
[[qa.C.min_film_Wm2|.1f|x1e-3,notag]] kW/m² (C); es el tramo largo y suave de T(t). En log–log, la rama derecha de pendiente pequeña y
positiva. Es la región Leidenfrost propiamente dicha; el mínimo es el punto de Leidenfrost.</li>
<li><strong>IV (transición)</strong> en ΔT ≃ 48 → 26 K: la película se rompe, Q/A sube de 8,7 a 70 kW/m² al bajar ΔT (pendiente
negativa en el gráfico, la rama «inestable» de Nukiyama, que aquí se atraviesa porque la T del cuerpo está impuesta por su
inercia térmica y no por un calefactor). Corresponde a la banda [T<sub>lo</sub>, T<sub>hi</sub>] de §2.</li>
<li><strong>III–II (nucleada)</strong>: máximo de Q/A (flujo crítico, [[qa.C.peak_Wm2|.0f|x1e-3,notag]] kW/m² a ΔT = [[qa.C.dT_at_peak_K|.0f|notag]] K en C), luego
descenso rápido con ΔT (~2 décadas entre ΔT = 25 y 1,5 K) mientras las burbujas dejan de llegar a la superficie. Son pocos
puntos (5–7 muestras a 1,44 s): la resolución temporal limita esta parte, y el Biot llega a ~0,2 (§1.2).</li>
<li><strong>I (convección)</strong>: ΔT → 0, Q/A → 0; en los datos es el plateau a 77 K, donde dT/dt es puro ruido y Q/A calculado
oscila alrededor de cero (en log–log estos puntos se dispersan en ~500 W/m²: es el ruido de cuantización, no física).</li>
</ul>
<p>En escala lineal se ve el plateau de película y el pico del colapso; en log–log se ve la forma de Nukiyama y la relación de
órdenes de magnitud entre mínimo y pico (8,1× en C, 13× en A, 5× en B; el pico depende de la ventana de suavizado).</p>

<h3>6.1 Validación dimensional y aplicabilidad de las correlaciones</h3>
<p><strong>Unidades.</strong> Q/A = (n/A)[mol/m²]·C<sub>v</sub>[J/(mol·K)]·dT/dt[K/s] = J/(s·m²) = W/m²: consistente; la conversión
W/m² ↔ kW/m² usada en todo el informe (factor ×10⁻³) se aplica siempre sobre el valor en W/m², nunca sobre un dato ya en kW/m²
(verificado por inspección de <code>report_content.py</code>/<code>build_report.py</code>: todos los <code>x1e-3</code> actúan sobre
claves <code>*_Wm2</code>). C<sub>v</sub> en J/(mol·K) con 3R = [[qual.dulong_petit|.2f]] J/(mol·K) como límite de alta T (verificado,
§2). El calor total ∫C<sub>v</sub>dT tiene unidades J/mol y, dividido por M<sub>Cu</sub>, J/kg (verificado: [[cv.enthalpy_77_296_Jmol|.0f]]
J/mol = [[cv.enthalpy_77_296_Jkg|.0f]] J/kg). m/A en kg/m² (p), tiempos en s, temperaturas críticas en K: sin ambigüedad de
unidades en ninguna ecuación usada.</p>
<p><strong>Comparación con el flujo crítico de N₂.</strong> El valor de literatura phys.qmax_LN2_Wm2 ([[phys.qmax_LN2_Wm2|.0f|x1e-3]] kW/m²)
corresponde a ebullición nucleada en pileta (<em>pool boiling</em>), saturada, 1 atm, sobre una superficie horizontal u
orden-de-magnitud independiente de geometría fina (Kutateladze/Zuber): nuestra situación —cilindro parcialmente inclinado o
vertical, transitorio, temperatura variando continuamente, no en estado estacionario— no cumple todas esas condiciones. La
comparación (picos de A/B/C muy por debajo de q<sub>max</sub>, C1 muy por encima) se usa sólo como <em>orden de magnitud</em>, nunca
como validación cuantitativa exacta; así se lo señaló ya en §5 y en <code>phys.qmax_LN2_Wm2</code>
(<code>detail="order of magnitude only"</code>).</p>
<p><strong>Correlaciones de ebullición en película (tipo Bromley).</strong> No se aplicó ninguna correlación de Bromley (o
análoga) para predecir Q/A cuantitativamente: los coeficientes de película usados (phys.h_film_Wm2K, phys.h_nucleate_Wm2K) son
órdenes de magnitud de la bibliografía citada, usados sólo para estimar números de Biot y escalas de tiempo (§1.2), nunca para
generar una curva Q/A(ΔT) que se compare con los datos. Bromley (1950) supone película laminar de vapor en un cilindro
horizontal en ebullición en película <em>estacionaria</em>, con propiedades del vapor evaluadas a la temperatura de película; nuestro
experimento es transitorio y la orientación exacta del cilindro en el dewar no está documentada, así que aplicar Bromley
cuantitativamente excedería lo que las fuentes permiten justificar. Se prefirió no extrapolar una correlación fuera de sus
hipótesis antes que presentar un número no respaldado.</p>
"""))

    S.append(dict(id="conclusiones", title="7. Conclusiones", figs=[], html="""
<p>Resumen final, separado explícitamente en lo que ya estaba bien y se conservó, lo que se corrigió, lo que es nuevo, y lo que
sigue abierto.</p>
<h3>A) Resultados de la ronda 2 que se verificaron y siguen siendo válidos</h3>
<ul>
<li>El C<sub>v</sub> de Einstein con Θ<sub>E</sub>(T) de la ec. (5) —corregida la errata de la ec. (4)— reproduce Debye a 0,03 % a 300 K y
queda 10 % bajo a 77 K; ∫C<sub>v</sub>dT (77→296 K) = [[cv.enthalpy_77_296_Jmol|.0f|notag]] J/mol. (Verificado y extendido en §2.4:
el 10 % nunca cambia el plateau, el mínimo o el pico en más de una fracción de por ciento.)</li>
<li>Los tres cilindros desnudos muestran película estable seguida de un colapso abrupto a T ≃ 102–105 K (ΔT ≃ 25–28 K), en
t<sub>c</sub> = [[tc.A.t_from_immersion_s|.0f|notag]] s (A), [[tc.B.t_from_immersion_s|.0f|notag]] s (B), [[tc.C.t_from_immersion_s|.0f|notag]] s (C) desde la
inmersión; la caída ocupa ~30 K en 7–10 s. t<sub>c</sub> es insensible a la ventana de suavizado y al umbral (confirmado también por
la propagación de σ<sub>T</sub>, §2.5: el piso real de incerteza de t<sub>c</sub> es de muestreo, no de ruido de temperatura).</li>
<li>Con la geometría medida, t<sub>c</sub> crece con p (p = [[geom.A.p_kgm2|.1f|notag]], [[geom.B.p_kgm2|.1f|notag]],
[[geom.C.p_kgm2|.1f|notag]] kg/m²) y la proporcionalidad simple vale a ~15 %; el flujo de película sale independiente del cuerpo a
[[qa.plateau_spread_pct|.0f|notag]] %, el mínimo de Leidenfrost a ΔT ≃ 50 K y el flujo crítico 70–90 kW/m² a ΔT ≃ 26 K.</li>
<li>La balanza distingue las tres etapas y su cuerpo se identifica como C (energía y empuje coinciden con 226 g a 7 %); el
balance de energía cierra a [[bal.Q_ratio|.2f|notag]] y Q/A medido por la balanza coincide con el calorimétrico a 15 %.</li>
<li>El film plástico elimina la película de vapor desde t = 0 (efusividad de contacto); una vuelta enfría el cobre muy rápido,
tres vueltas lo enfrían suave y monótonamente porque el arrollado agrega una resistencia térmica propia. No hay t<sub>c</sub> en
ninguna de las dos corridas recubiertas.</li>
</ul>
<h3>B) Resultados que se corrigieron o precisaron en esta revisión</h3>
<ul>
<li>La brecha de ~[[bal2.slope_gap_naive_pct|.0f]] % entre las pendientes 1 y 3 de la balanza ya no queda como observación
cualitativa: se separó el fondo ambiente (pendiente de la cola, ≈ pendiente 1 a 4 %) de un residuo térmico del cilindro que decae
exponencialmente con P₀ = [[bal2.model_P0_W|.1f]] W y τ = [[bal2.model_tau_s|.1f]] s (§4.4); la vieja estimación de ~7,1 W era el
promedio temporal de ese transitorio (modelo: [[bal2.model_Pavg_W|.1f]] W), no un número en conflicto con el nuevo resultado.</li>
<li>El ajuste t<sub>c</sub> = k·p por el origen ya no es el único ajuste presentado: se agregaron la ley de potencia y la recta
general (§3.3), y se dejó explícito que con 3 puntos y 2 parámetros esos ajustes no son evidencia fuerte de una forma funcional
particular, sólo el ajuste de 1 parámetro (motivado por el balance térmico) tiene contenido físico real.</li>
<li>Los valores de <code>assume.adc_fs_V</code>/<code>assume.adc_bits</code> y del film plástico se reafirman explícitamente como
hipótesis, nunca datos experimentales; ahora tienen además una consecuencia cuantificada acotada a §2.5 y no se usan para ninguna
conclusión de §7-9.</li>
</ul>
<h3>C) Análisis nuevos agregados en esta revisión</h3>
<ul>
<li>Comparación extendida Einstein/Debye con recálculo de Q/A por ambos modelos y cuantificación de cuánto cambian el plateau,
el mínimo y el pico (§2.4).</li>
<li>Cadena completa de propagación de σ<sub>T</sub> → σ<sub>dT/dt</sub> → σ<sub>tc</sub>, σ<sub>Q/A</sub>, con la fórmula simbólica y un
ejemplo ilustrativo bajo hipótesis explícitas de ADC/ganancia, cruzado contra el ruido realmente observado (§2.5).</li>
<li>Modelo cuantitativo (ajuste no lineal, no sólo comparación de pendientes) de la brecha de la balanza, con potencia inicial,
tiempo de relajación y temperatura efectiva post-colapso (§4.4).</li>
<li>Ley de potencia y recta general para t<sub>c</sub>(p), con residuos, grados de libertad y una discusión explícita de cuán poco
determina un ajuste de 3 puntos (§3.3), y una predicción para un cuarto cilindro D con análisis de sensibilidad de modelo vs.
geometría (§3.4).</li>
<li>Investigación cuantitativa de la anomalía de C1: sensibilidad del pico de Q/A a la ventana de suavizado (factor
[[c1x.peak_window_spread_ratio|.1f]]×), número de Biot durante el transitorio, y comparación de temperaturas de plateau para la
hipótesis de junta mojada (§5.1).</li>
<li>Figura de las seis etapas superpuesta directamente sobre los datos de Q/A vs ΔT reales, con el sentido temporal marcado y el
estado evidenciario (observada/indicios/no resuelta) de cada etapa (§6).</li>
<li>Validación dimensional explícita y discusión de la aplicabilidad (y no aplicación) de correlaciones tipo Bromley (§6.1).</li>
<li>Intento de verificación externa de constantes (Wikipedia para el coeficiente Seebeck del tipo K; intentos fallidos sobre la
tabla NIST primaria), documentado en <code>verif.*</code> (§1).</li>
</ul>
<h3>D) Lo que sigue sin poder resolverse con los datos disponibles</h3>
<ul>
<li>La forma funcional exacta de t<sub>c</sub>(p) (¿proporcional, con corrección, ley de potencia?): indistinguible con sólo 3
cilindros (§3.3); la predicción para un cuarto cilindro D varía [[pred.D.model_spread_s|.0f]] s sólo por esa elección (§3.4).</li>
<li>El espesor y las propiedades reales del film plástico, y el rango/resolución reales del ADC/amplificador de la MPLI: no
están en las fuentes: siguen siendo hipótesis explícitas, ahora con su impacto cuantificado y acotado en vez de simplemente
mencionado.</li>
<li>Si el flujo crítico de la corrida C1 refleja física real (CHF distinto sobre una superficie plástica) o es enteramente un
artefacto de resolución temporal/Biot marginal/posible junta mojada: la evidencia disponible acota el problema pero no lo
decide (§5.1).</li>
<li>Los coeficientes exactos del polinomio inverso tipo K no se verificaron dígito a dígito contra la tabla NIST primaria en
esta sesión (los intentos de acceso en línea fueron redirigidos o bloqueados); la validación sigue siendo indirecta
(consistencia interna a ≤0,2 K y coincidencia del coeficiente Seebeck con una fuente secundaria independiente).</li>
<li>El sobrecalentamiento del vapor que abandona el dewar, la dependencia exacta del flujo de película con el diámetro, y si el
colapso de C1 es enfriamiento real del bulk o un artefacto de la junta: sin datos adicionales (redundancia de sensores,
termocuplas de referencia, o una cuarta corrida real) no se pueden zanjar.</li>
</ul>
"""))

    S.append(dict(id="noverif", title="8. Lo que no se verificó", figs=[], html="""
<ul>
<li>Las dimensiones y masas de A, B, C se tomaron tal como las comunicó el humano (con sus incertezas); no se midieron aquí. Que C
sea el mismo cuerpo en C1 y C3 se asume por el nombre de los archivos.</li>
<li>El verificador de la ronda 1 no corrió (límite de sesión); sólo existe una recomputación independiente de t<sub>c</sub>
(<code>work/verifier/verify_r01.py</code>) que coincide en la muestra.</li>
<li>h<sub>film</sub>, h<sub>nucleado</sub> y q<sub>max</sub> del NL son órdenes de magnitud de literatura (<code>phys.*</code>); sólo sirven para los
argumentos de Biot, de escala de tiempo y para juzgar la anomalía de C1.</li>
<li>Los coeficientes exactos del polinomio inverso tipo K no se verificaron dígito a dígito contra la tabla NIST primaria: se
intentó en esta ronda (<code>verif.nist_type_k_table_attempt</code>) pero <code>srdata.nist.gov/its90</code> redirigió a una página de
navegación sin datos y un espejo devolvió HTTP 403; el respaldo sigue siendo indirecto (acuerdo a ≤0,2 K con la columna T de los
CSV, y el coeficiente Seebeck de 41 µV/K que ese mismo polinomio implica coincide exactamente con un valor independiente de
Wikipedia, <code>verif.seebeck_K_room_vs_wikipedia</code>). Lo mismo para L<sub>v</sub>, ρ<sub>NL</sub>, ρ<sub>Cu</sub>, k<sub>Cu</sub>: son valores
estándar de CRC/NIST WebBook/CODATA, no re-consultados dígito a dígito en esta sesión por no tener acceso a esas bases de datos.</li>
<li>Rango y bits del ADC de la MPLI y ganancia del amplificador no están en las fuentes (supuestos ±10 V, 12 bit); ahora su efecto
está acotado cuantitativamente en §2.5 y cruzado contra el ruido real de dT/dt, pero el supuesto en sí sigue sin verificarse.</li>
<li>Espesor y material del film (12 µm, k = 0,2 W/(m K), ρc de LDPE), el gas atrapado en las 3 vueltas y la emisividad del Cu
(0,05) son supuestos.</li>
<li>El sobrecalentamiento del vapor que abandona el dewar (Q<sub>balanza</sub> entre 14,9 y 23 kJ) no se midió; el acuerdo al 7 % con
Q<sub>Cu</sub>(C) sugiere que es pequeño.</li>
<li>Si el colapso de C1 es enfriamiento real del bulk o un artefacto de la junta mojada: acotado con Biot y sensibilidad al
suavizado (§5.1), pero no decidido.</li>
<li>La dependencia del flujo de película con el diámetro (residuo del 15-25 % en t<sub>c</sub>/p, §3.3) no se contrastó con una
correlación tipo Bromley (§6.1 explica por qué: excedería las hipótesis de esa correlación). Los artículos de Curzon (1978, «The
Leidenfrost phenomenon», Am. J. Phys. 46(8) 825-828) y Listerman, Boshinski & Knese (1986, «Cooling by immersion in liquid
nitrogen», Am. J. Phys. 54(6) 554-558) se identificaron bibliográficamente vía CrossRef en esta ronda
(<code>verif.curzon1978_ref</code>, <code>verif.listerman1986_ref</code>): el segundo es directamente pertinente (mismo tipo de
experimento, ya citado como fuente del orden de magnitud de h<sub>película</sub>); el primero parece ser, según un resumen obtenido
automáticamente y no verificado contra el texto primario, un trabajo de demostraciones de cátedra, no una calorimetría
cuantitativa comparable. No se compararon valores numéricos de ninguno de los dos porque el texto completo no se leyó.</li>
<li><code>out/notes.tex</code> no se compiló (no hay LaTeX en esta máquina); se verificó balance de llaves y entornos.</li>
</ul>
"""))
    return S
