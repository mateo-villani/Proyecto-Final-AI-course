# Reproducción desde cero — Experimento de Leidenfrost

Este directorio contiene un paquete reproducible del análisis del experimento de Leidenfrost con nitrógeno líquido.

## Objetivo

Reproducir el análisis únicamente a partir de:

- los datos experimentales crudos de `datos/`;
- las guías de la experiencia de `guia/`;
- las dimensiones y masas experimentales incorporadas explícitamente en el pipeline;
- el código contenido en `work/`.

El informe humano original NO forma parte de los inputs de esta reproducción.

El objetivo completo utilizado para construir el análisis se encuentra en `objective.txt`.

## Estructura

- `datos/`: CSV experimentales originales.
- `guia/`: guías de la experiencia.
- `work/`: código de análisis y generación del informe.
- `out/`: provenance, checks y productos reproducidos.
- `objective.txt`: objetivo entregado al agente.
- `requirements.txt`: dependencias de Python.

Los archivos de `work/fig/`, `work/results.json`, `work/checks_output.txt` y varios archivos de `out/` son productos generados por el pipeline.

## Dependencias

Se requiere Python 3 y los paquetes indicados en:

    requirements.txt

Para instalarlos:

    python -m pip install -r requirements.txt

## Reproducción

Todos los comandos siguientes deben ejecutarse desde este directorio:

    Para_máquinas/reproduccion_desde_cero/

### 1. Reconstruir cálculos, provenance y figuras

    python work/build_all.py

Este comando ejecuta el pipeline numérico y reconstruye `out/provenance.json` a partir de los datos.

### 2. Ejecutar las verificaciones

    python out/checks.py

En la versión validada del proyecto, el resultado esperado es:

    114 PASS
    0 FAIL
    0 WARN
    7 INFO

Los INFO son observaciones documentales o físicas y no representan fallos.

### 3. Reconstruir el informe HTML

    python work/build_report.py

El resultado se escribe en:

    out/report.html

El HTML es autocontenido: las figuras están embebidas y no requiere recursos externos.

## Provenance

`out/provenance.json` registra el origen y la reproducción de los resultados numéricos.

Las entradas distinguen entre valores:

- medidos;
- derivados;
- tomados de la guía;
- tomados de literatura;
- asumidos.

Los checks verifican, entre otras cosas, la estructura del provenance, la existencia de las rutas de reproducción y la sincronización de resultados con los CSV crudos.

## Criterio de éxito

Una reproducción se considera exitosa si:

1. `python work/build_all.py` termina sin error;
2. `python out/checks.py` termina con 0 FAIL y 0 WARN;
3. `python work/build_report.py` termina con checks exit 0 y sin placeholders faltantes;
4. se genera `out/report.html`.

## Alcance

Los checks validan consistencia numérica, física y de provenance, pero no convierten las hipótesis explícitas en mediciones.

En particular, algunas especificaciones instrumentales y del recubrimiento permanecen etiquetadas como hipótesis cuando no estaban disponibles en los datos o guías.

El caso del cilindro C con una vuelta presenta una transición submuestreada y una estimación de flujo sensible al suavizado; el pipeline lo conserva como limitación en lugar de forzar una conclusión cuantitativa.

## Prueba con agente nuevo

Para evaluar la reproducibilidad de manera independiente, entregar este repositorio a un agente sin contexto previo y pedirle que:

1. identifique los inputs y el procedimiento de reproducción;
2. ejecute o describa los comandos necesarios;
3. reproduzca resultados directamente desde los CSV;
4. ejecute los checks;
5. informe cualquier dependencia, archivo faltante o supuesto no documentado.

El agente no debería necesitar acceso a conversaciones anteriores ni al directorio de trabajo original.
