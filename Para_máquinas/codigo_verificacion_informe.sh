#!/bin/bash
# ---------------------------------------------------------------------------
# codigo_verificacion_informe.sh
#
# Comandos y script usados para producir verificacion-informe-leidenfrost.html
# a partir de Grupo_3___Informe_Leidenfrost_Reentrega.pdf.
#
# Este archivo documenta la provenance del reporte de verificacion: cada
# imagen/pagina que se inspecciono visualmente para escribir el analisis fue
# generada con los comandos de abajo, no con una extraccion de texto.
#
# Requisitos:
#   - Poppler (pdftoppm, pdftohtml). Version usada en este proyecto: 26.07.0
#   - Python 3 con PyMuPDF:  pip install pymupdf
#
# Nota sobre lo que este script NO reproduce: los calculos numericos de la
# Seccion 3 del reporte (areas, moles, parametro p, test de compatibilidad
# de pendientes en ~12 sigma, potencia residual de 7,1 W) se hicieron a mano
# con calculadora, a partir de los valores que el PDF reporta en su Tabla 1
# y en los pies de Figura 6. No hay script para esa parte porque son cuentas
# de una sola linea cada una; estan explicitadas paso a paso dentro del
# propio HTML del reporte (Seccion 3).
# ---------------------------------------------------------------------------
set -e

PDF="Grupo_3___Informe_Leidenfrost_Reentrega.pdf"
PAGES_DIR="pages_render"
mkdir -p "$PAGES_DIR"

# ---------------------------------------------------------------------------
# Paso 0 (exploratorio, anterior a la verificacion): conversiones automaticas
# de PDF a HTML. Se hicieron ANTES de decidir el metodo de verificacion y NO
# se usaron como fuente de ningun dato citado en verificacion-informe-
# leidenfrost.html -- el texto extraido automaticamente rompe subindices y
# exponentes de las ecuaciones. Se dejan documentadas por transparencia,
# ya que sus salidas (infome_Leidenfrost.html, informe_Leidenfrost_poppler.html)
# quedaron versionadas en este mismo repositorio.
# ---------------------------------------------------------------------------

# 0a. Conversion con PyMuPDF: texto real posicionado + figuras embebidas en
#     base64 (una imagen solo por cada figura real del informe, no por pagina).
python3 - <<'PY'
import fitz  # PyMuPDF

src = "Grupo_3___Informe_Leidenfrost_Reentrega.pdf"
dst = "infome_Leidenfrost.html"

doc = fitz.open(src)
parts = [
    "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<title>Informe Leidenfrost</title>\n</head>\n<body>\n"
]
for i, page in enumerate(doc):
    parts.append(f"<!-- Page {i+1} -->\n")
    parts.append(page.get_text("html"))
parts.append("\n</body>\n</html>\n")

with open(dst, "w", encoding="utf-8") as f:
    f.write("".join(parts))

print(f"Pages: {doc.page_count} -> {dst}")
PY

# 0b. Conversion con pdftohtml de Poppler: cada pagina como imagen de fondo
#     (PNG) con el texto real superpuesto en una capa transparente para
#     busqueda/seleccion. Visualmente identica al PDF, pero el "contenido"
#     es una imagen, no texto reestructurado.
"${POPPLER_BIN:-}pdftohtml" -c -noframes "$PDF" informe_Leidenfrost_poppler.html

# ---------------------------------------------------------------------------
# Paso 1: renderizado pagina por pagina a 150 dpi.
# Este es el metodo REALMENTE usado como fuente para escribir
# verificacion-informe-leidenfrost.html: se leyeron las 13 imagenes
# resultantes una por una (texto, tablas, ecuaciones y figuras tal como
# aparecen en el PDF), en vez de depender de texto extraido automaticamente.
# ---------------------------------------------------------------------------
"${POPPLER_BIN:-}pdftoppm" -png -r 150 "$PDF" "$PAGES_DIR/page"
# Genera: pages_render/page-01.png ... pages_render/page-13.png

# ---------------------------------------------------------------------------
# Paso 2: recorte en alta resolucion (400 dpi) de la Ecuacion 3 en la
# pagina 3, partido en dos mitades (prefactor y termino exponencial), para
# confirmar sin ambiguedad los subindices theta_E vs theta_D antes de
# reportar la inconsistencia en la Seccion 4 del HTML de verificacion.
# ---------------------------------------------------------------------------
"${POPPLER_BIN:-}pdftoppm" -png -r 400 -f 3 -l 3 -x 250  -y 1350 -W 1400 -H 400 \
    "$PDF" "$PAGES_DIR/eq3_prefactor"
"${POPPLER_BIN:-}pdftoppm" -png -r 400 -f 3 -l 3 -x 1500 -y 1350 -W 1200 -H 400 \
    "$PDF" "$PAGES_DIR/eq3_exponencial"

echo "Listo. Paginas renderizadas en $PAGES_DIR/."
echo "Sobre esas imagenes se escribio, a mano, verificacion-informe-leidenfrost.html."
