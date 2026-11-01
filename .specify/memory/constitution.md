<!--
Sync Impact Report
- Version change: 2.0.0 → 2.1.0
- Modified principles: I. La priorización permanece en el comité
  (la página puede crear en Jira los hallazgos que se quedan)
- Added sections: none
- Removed sections: none
- Motivo: la Líder UX abrió el corte de escritura a Jira el 2026-10-27.
  Solo entran los que se quedan, con etiqueta oficial, y el token vive
  fuera del repositorio. La corrida mensual sigue sin crear tickets.
-->

# Constitución del orquestador de métricas UX de Magneto

## Core Principles

### I. La priorización permanece en el comité

Crear o actualizar un ticket exige la revisión tripartita: Líder UX, Product
Owner y Líder de Célula. La célula propone hallazgos. El comité evalúa
deseabilidad, factibilidad y viabilidad antes de mover trabajo de ingeniería.
Aceptar o rechazar un hallazgo es manual. El color de criticidad no sustituye
esa decisión. Cuando el hallazgo se queda y tiene etiqueta oficial, la página
puede crear el issue en Jira, de uno en uno o varios a la vez. El token de la
API vive en el entorno y no entra al repositorio. Azure DevOps sigue cerrado.
La corrida mensual no crea tickets.

### II. El lote del mes es la única fuente

Cada corrida usa únicamente el `feedback_response.xlsx` del mes en curso.
Un valor numérico ausente se excluye del cálculo y aparece en Alertas de
Calidad de Datos. Cada queja citada existe de forma literal en el texto del
usuario. Datos de meses anteriores o tickets viejos entran solo si viajan
dentro de ese mismo lote.

### III. B2B y taxonomía cerrada

Antes de cualquier agente, el lote descarta filas B2C y ruido plano
(`.`, `N`, `nada`, `OK`). Una queja se clasifica solo con un módulo oficial
y una etiqueta oficial. El mismo comentario, ya normalizado, se clasifica
una sola vez en el mes: es un hallazgo y su conteo es el número de
apariciones. Si la confianza cae por debajo del 70 %, el registro queda
marcado `[REQUIERE_REVISION_HUMANA]` y espera a la Líder UX.

Módulos: `[Gestión de Vacantes]`, `[Catálogo de Candidatos]`,
`[Solicitud de vacantes]`, `[Creación de vacantes]`,
`[Carga Masiva de Perfiles]`, `[Analítica / Superset]`, `[Bot omnicanal]`.

Etiquetas: `[BUG]`, `[UX/Usabilidad]`, `[PERFORMANCE]`, `[FEATURE]`.

La criticidad es automática y nadie la escribe. El porcentaje de un hallazgo
es su conteo dividido por el total de preguntas abiertas del mes que entran
a tipificación, multiplicado por 100. Ese total excluye ruido, filas B2C y
fechas fuera del mes.

- Hasta el 20 % inclusive: verde.
- Más del 20 % y hasta el 50 % inclusive: amarillo.
- Más del 50 %: rojo.

### IV. Cada decisión queda auditada y se puede apagar

Cada etiqueta conserva el comentario original, el sentimiento calculado, la
justificación del agrupamiento, el conteo y el porcentaje que fijó el color.
Si ese registro no existe, el token de escritura hacia Jira o Azure permanece
bloqueado. Un hallazgo rechazado se conserva como `[DESCARTADO-ESTRATÉGICO]`.
Si el mismo dolor reaparece en los dos meses siguientes, vuelve al comité como
`[REINCIDENTE]`.

La Líder UX puede detener el grafo; el Excel fuente permanece intacto para
continuar el análisis en el proceso manual.

### V. La autonomía se amplía solo con umbrales cumplidos

Una corrida válida termina en menos de 3 minutos, clasifica al menos el 85 %
de los comentarios cualitativos sin corrección de etiqueta y se mantiene dentro
de 3 USD de costo de modelo más 30 minutos de supervisión humana previa al
comité. Una validación de entrada fallida detiene la corrida y avisa por
correo a la Líder UX. Una validación de salida fallida admite un solo
reintento; el segundo fallo bloquea el traspaso y también avisa por correo.

## Restricciones operativas

El producto es Magneto, el ATS B2B. El proceso es la consolidación mensual de
métricas UX y la tipificación del feedback cualitativo.

La entrada del primer corte es `feedback_response.xlsx`, con las pestañas de
Creación de vacantes, Catálogo y Gestión de vacantes. La corrida queda
programada el día 1 de cada mes a las 06:00, después del ETL de Superset.

El recorrido es un grafo ordenado: ingesta, cálculo cuantitativo, análisis de
voz del cliente, reporte y compuerta humana. El reporte cuantitativo trae las
columnas Métrica, Valor Calculado y Tamaño de Muestra (n), más las alertas de
calidad. El reporte cualitativo agrupa el mismo comentario en un hallazgo, con
módulo, etiqueta, síntesis de hasta dos líneas, conteo y color de criticidad.
La PII se anonimiza antes de entregar el reporte.

El primer corte incluye ingesta, métricas, tipificación, reporte, cola de
revisión, programación del día 1, alertas por correo y la compuerta previa a
los tickets. Desde el corte abierto el 2026-10-27, la página puede crear
issues en Jira para los hallazgos que se quedan y tienen etiqueta oficial.
La corrida mensual sigue sin crear ni modificar tickets.

Cada mes, una muestra aleatoria del 10 % de los cálculos de CSAT y CES se
audita para confirmar fórmulas y la exclusión de B2C.

TODO(VOLUMEN): la especificación debe fijar si el denominador operativo es
350 registros o 3,907 filas antes de medir tasa de finalización y ROI.

TODO(ARCHIVO): el Excel real todavía no está en el repositorio.

## Forma de construir

El trabajo sigue Spec Kit: constitución, especificación, plan, tareas y, solo
entonces, implementación. Cada corte de implementación espera un sí explícito
de la Líder UX antes de escribir código de producto.

La Líder UX audita el reporte completo antes de llevarlo al comité mientras la
tasa de finalización no se sostenga por encima del 85 %.

## Governance

Esta constitución prevalece sobre prompts, skills y borradores de reporte
cuando haya conflicto. Una enmienda requiere la aprobación escrita de la Líder
UX, el motivo del cambio y un incremento de versión.

- MAJOR: se vuelve automática una decisión que esta constitución reserva al
  comité, o se retira un control de auditoría o de apagado, o se redefine una
  regla de forma incompatible con la versión anterior.
- MINOR: se agrega un principio o una restricción operativa nueva.
- PATCH: aclaración de redacción sin cambio de regla.

Toda especificación y toda revisión de cambio comprueba cuatro controles:
compuerta humana, taxonomía cerrada, log de auditoría y apagado. El archivo de
guía de ejecución es `.specify/memory/constitution.md`.

**Version**: 2.1.0 | **Ratified**: 2026-10-22 | **Last Amended**: 2026-10-27
