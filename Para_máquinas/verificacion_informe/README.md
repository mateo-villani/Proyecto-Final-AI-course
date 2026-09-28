# Verificación automatizada del informe

Este directorio automatiza la parte numérica del método de verificación con acceso al informe terminado.

El input es `Para_humanos/Grupo_3___Informe_Leidenfrost_Reentrega.pdf`. El pipeline comprueba su SHA-256, renderiza sus 13 páginas, reproduce los cálculos auditables y genera checks, provenance y un reporte HTML.

La revisión conceptual completa sigue disponible en `Para_humanos/verificacion-informe-leidenfrost.html`. Este pipeline no presenta como automáticos los juicios físicos o la lectura visual de figuras.

## Requisitos

- Python 3.10 o posterior.
- PyMuPDF 1.28.2.

No se necesita Bash ni Poppler.

Instalación:

```powershell
python -m pip install -r requirements.txt
```

## Ejecución

El script puede ejecutarse desde cualquier directorio:

```powershell
python run_all.py
```

Desde la raíz del repositorio también puede ejecutarse así:

```powershell
python "Para_máquinas/verificacion_informe/run_all.py"
```

## Productos

Se escriben en `out/`:

- `pages/page-01.png` a `page-13.png`: renderizado visual del PDF a 150 dpi;
- `results.json`: resultados numéricos recalculados;
- `provenance.json`: origen de los valores extraídos y funciones que producen los derivados;
- `checks.txt`: salida legible de las validaciones;
- `report.html`: resumen reproducible de la verificación automatizada.

`out/` no se versiona porque se reconstruye por completo con `run_all.py`.

## Valores transcritos

`config.json` contiene los valores leídos visualmente del PDF. Cada bloque incluye su página, tabla o figura de origen. Modificar un valor fuente requiere revisar el PDF y actualizar también su referencia.

El hash esperado evita ejecutar silenciosamente la auditoría contra una versión diferente del informe.

## Criterio de éxito

La ejecución es exitosa cuando termina con código 0 y todos los checks quedan en `PASS`. Un cambio en el PDF, una página faltante o una inconsistencia numérica produce al menos un `FAIL` y código de salida 1.

## Alcance y límites

Se automatizan:

- identidad y cantidad de páginas del PDF;
- renderizado de todas las páginas;
- áreas de los cilindros;
- cantidad de moles y `p = masa/área`;
- orden entre `p` y el tiempo crítico;
- diferencia porcentual y compatibilidad estadística de pendientes;
- potencia residual de evaporación;
- evaluación de la temperatura de Einstein en 77 K y 300 K.

Continúan siendo revisión humana:

- transcripción inicial de valores desde tablas y figuras;
- interpretación de ecuaciones y gráficos;
- evaluación de la coherencia de las conclusiones;
- comparaciones que dependan de bibliografía externa.
