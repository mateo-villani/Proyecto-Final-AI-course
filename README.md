# Proyecto Final — Reproducibilidad con agentes de IA aplicada al efecto Leidenfrost



**Autores:** Nikita Kacuk y Mateo Villani

**Asistentes de IA utilizados:** Claude y Codex



## Descripción



Este repositorio contiene el trabajo realizado para el proyecto final, cuyo objetivo fue estudiar el uso de agentes de inteligencia artificial para **verificar y reproducir un análisis experimental de física**.



Como caso de estudio se utilizó un experimento previamente realizado sobre el **efecto Leidenfrost en cilindros de cobre sumergidos en nitrógeno líquido**.



La pregunta central del proyecto fue:



> ¿Qué cambia cuando un agente de IA trabaja con un informe experimental ya terminado frente a cuando debe reconstruir el análisis directamente desde los datos y las fuentes primarias, sin conocer previamente el resultado?



Para estudiarlo se siguieron dos enfoques diferentes.



## 1. Verificación con acceso al informe



En el primer enfoque, el agente recibió el **informe experimental terminado**.



Su tarea fue auditar el trabajo existente: reconstruir los cálculos que podían verificarse a partir de la información publicada, revisar la coherencia entre ecuaciones, valores, figuras y conclusiones, e identificar posibles inconsistencias.



Este procedimiento permitió, entre otras cosas:



* revisar cantidades geométricas y la relación entre masa y área de los cilindros;

* analizar los tiempos críticos reportados;

* verificar el tratamiento del calor específico;

* detectar una inconsistencia en el uso de las temperaturas características de Einstein y Debye;

* revisar el análisis de las pendientes obtenidas en la medición con la balanza.



Este método responde principalmente a la pregunta:



**¿Puede un agente auditar y verificar un resultado que ya conoce?**



## 2. Reproducción independiente desde los datos



En el segundo enfoque, el agente **no recibió el informe experimental original como entrada**.



En cambio, trabajó a partir de:



* los archivos CSV con las mediciones experimentales;

* las guías de la experiencia;

* los parámetros y dimensiones necesarios para el análisis;

* una descripción de los objetivos que debía alcanzar.



A partir de estas fuentes reconstruyó el análisis del experimento, incluyendo:



* conversión de las mediciones a temperatura;

* curvas de temperatura en función del tiempo;

* determinación de los tiempos críticos;

* cálculo del flujo de calor por unidad de área;

* análisis de la medición con balanza;

* comparación entre cilindros;

* estudio del efecto de modificar la superficie;

* generación de figuras;

* análisis adicionales de los resultados.



Además, se incorporaron mecanismos de **trazabilidad y verificación automática**, mediante archivos de provenance y checks.



Este método responde a una pregunta diferente:



**¿Puede un agente recuperar los resultados sin conocer previamente la respuesta?**



## Comparación de los métodos



Los dos procedimientos no realizan exactamente la misma tarea y son complementarios.



El método con acceso al informe funciona principalmente como una **auditoría**: parte de un resultado conocido y estudia si está correctamente respaldado.



La reproducción independiente funciona como una prueba más exigente de **reproducibilidad**: el agente debe volver desde los datos experimentales hasta los resultados sin utilizar el informe como referencia durante el análisis.



Al comparar posteriormente ambas ramas se encontró que la reproducción independiente recuperó los principales comportamientos físicos y obtuvo tiempos críticos próximos a los del informe original.



También aparecieron diferencias útiles para estudiar las limitaciones del procedimiento automático, por ejemplo en la determinación de la temperatura asociada a una transición rápida.



El proyecto muestra además que obtener un número similar al original no es suficiente para hablar de reproducibilidad: es importante conservar información sobre **qué datos, supuestos y procedimientos produjeron cada resultado**.



## Estructura del repositorio



```text

Proyecto-Final-AI-course/

│

├── Para_humanos/

│   ├── ProyectoFinal_Leidenfrost_agentesdeIA.pdf

│   ├── Grupo_3___Informe_Leidenfrost_Reentrega.pdf

│   ├── verificacion-informe-leidenfrost.html

│   ├── reproduccion-leidenfrost-desde-cero.html

│   └── ...

│

└── Para_máquinas/

&#x20;   ├── codigo_verificacion_informe.sh

&#x20;   │

&#x20;   └── reproduccion_desde_cero/

&#x20;       ├── README.md

&#x20;       ├── objective.txt

&#x20;       ├── requirements.txt

&#x20;       ├── datos/

&#x20;       ├── guia/

&#x20;       ├── work/

&#x20;       └── out/

```



### `Para_humanos/`



Contiene los materiales destinados principalmente a lectura y evaluación humana.



El documento principal de síntesis del proyecto es:



**`Para_humanos/ProyectoFinal_Leidenfrost_agentesdeIA.pdf`**



Este PDF resume la pregunta del proyecto, los dos métodos utilizados, las comparaciones principales y las conclusiones.



También se encuentran aquí:



* el informe experimental original;

* el resultado de la verificación con acceso al informe;

* el informe generado mediante la reproducción independiente desde los datos.



### `Para_máquinas/`



Contiene los archivos destinados a reproducir, verificar o inspeccionar computacionalmente el trabajo.



En particular:



**`Para_máquinas/reproduccion_desde_cero/`**



contiene el paquete utilizado para la reproducción independiente.



Dentro de este directorio:



* `datos/`: mediciones experimentales crudas;

* `guia/`: documentación utilizada como fuente;

* `work/`: código del análisis;

* `out/provenance.json`: trazabilidad de los resultados;

* `out/checks.py`: verificaciones automáticas;

* `out/report.py`: versión reproducible/interactiva del informe;

* `objective.txt`: objetivo entregado al agente;

* `requirements.txt`: dependencias de Python;

* `README.md`: instrucciones específicas para reproducir este análisis.



## Reproducción

La verificación automatizada del informe terminado se ejecuta con:

```powershell
python "Para_máquinas/verificacion_informe/run_all.py"
```

Sus instrucciones, alcance y dependencias se encuentran en:

`Para_máquinas/verificacion_informe/README.md`

Este pipeline comprueba la identidad del PDF, renderiza sus páginas y reproduce los cálculos numéricos auditables. La interpretación física del informe permanece documentada por separado como revisión humana.



Las instrucciones detalladas para ejecutar nuevamente la reproducción independiente se encuentran en:



`Para_máquinas/reproduccion_desde_cero/README.md`



El paquete fue organizado para que pueda ser inspeccionado por una persona o por un nuevo agente sin necesidad de acceder a las conversaciones utilizadas durante el desarrollo del proyecto.



## Resultado principal



La comparación muestra una diferencia importante entre **verificar un resultado conocido** y **reconstruirlo desde evidencia primaria**.



El acceso al informe permite al agente detectar inconsistencias y auditar las conclusiones existentes. Trabajar desde los datos permite evaluar de manera más directa la reproducibilidad del análisis y obliga a hacer explícitas decisiones, supuestos y procedimientos que pueden quedar ocultos cuando solo se observa el resultado final.



Por este motivo, el proyecto no evalúa únicamente si una IA puede producir una respuesta similar a la original, sino también **qué evidencia permite determinar cómo obtuvo esa respuesta y hasta qué punto el proceso puede repetirse y verificarse**.



