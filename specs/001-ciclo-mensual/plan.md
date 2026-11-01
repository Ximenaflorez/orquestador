# Implementation Plan: Ciclo mensual de métricas UX

**Branch**: `001-ciclo-mensual` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ciclo-mensual/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

La Líder UX deja un libro mensual en `datos/meses/` y el ciclo devuelve métricas, quejas tipificadas, una cola de revisión y la decisión del comité. El cálculo numérico es determinista. Solo la etiqueta y el módulo consultan un modelo, y únicamente con el texto de ese libro. El mismo comentario normalizado es un hallazgo. Su criticidad es verde hasta el 20 % inclusive del total de preguntas abiertas que entran a tipificación, amarillo por encima de ese corte y hasta el 50 % inclusive, y rojo por encima del 50 %. Ese color no lo escribe el modelo ni la Líder UX. Aceptar o rechazar el hallazgo sigue siendo manual. La corrida es un grafo ordenado de cinco pasos: ingesta, métricas, voz del cliente, reporte y compuerta. En este corte la compuerta registra la decisión y no abre tickets. Una página local deja el Excel arriba y, debajo, el total ponderado por mes, trimestre o semestre. Luego van cuatro pestañas: Guardar el mes, Tipificados, Backlog y Excluidos. Enviar a Jira solo se ve en Tipificados. Si hay modelo de embeddings, las frases parecidas se unen y la síntesis es el título. En Guardar el mes el ojo abre Hallazgos como una fila de la tabla, con cada frase original aunque no sea idéntica. En las otras tres listas el ojo muestra esa lista junto con la decisión. Abrir el ojo no llama al modelo.

## Technical Context

**Language/Version**: Python 3.12, gestionado con uv

**Primary Dependencies**: LangGraph para el recorrido ordenado, openpyxl para leer y guardar el libro, Pydantic para los contratos de salida. La página local usa el servidor de la biblioteca estándar.

**Storage**: Archivos. Entrada en `datos/meses/`, resultados en `salidas/YYYY-MM/`, memoria de rechazos en `memoria/hallazgos.json`, apagado en `datos/control/apagado.flag`

**Testing**: pytest

**Target Platform**: Windows 10 o superior, ejecución local el día 1 a las 06:00 mediante el Programador de tareas

**Project Type**: CLI de un solo proyecto, más una página local de captura y consulta

**Performance Goals**: Una corrida de hasta 5.000 filas termina en menos de 3 minutos y queda dentro de 3 USD

**Constraints**: Tres pestañas obligatorias y ninguna otra. Escala 1 a 5. Taxonomía cerrada. Confianza menor a 70 % va a revisión humana. La criticidad es `verde`, `amarillo` o `rojo` según el porcentaje del conteo, y no admite un valor manual. La corrida no navega la web, no llama APIs de tickets y no modifica el libro de entrada. La página puede guardar el libro de un mes antes de correrlo y, aparte de la corrida, crear en Jira los hallazgos que se quedan y tienen etiqueta oficial. El agrupado por parecido solo ocurre en la corrida, con `MODEL_EMBEDDING_NAME`, y si falla vuelve al texto idéntico. Costo y duración se miden; si se superan, el reporte no queda oficial. El total no incluye un mes sin carpeta en `salidas/`

**Scale/Scope**: Un lote por mes, una operadora, tres pestañas. Las muestras de julio, agosto y septiembre tienen entre 62 y 82 filas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Exigencia | Resultado |
|-----------|-----------|-----------|
| I. La priorización permanece en el comité | La corrida no crea tickets. La página solo crea en Jira un hallazgo que se queda y tiene etiqueta oficial, y ese botón solo se ve en Tipificados. El color no sustituye aceptar o rechazar | Pasa. Enviar a Jira es una acción manual posterior a se queda |
| II. El lote del mes es la única fuente | Una corrida lee un solo libro y no imputa puntajes | Pasa. Las métricas son cálculo directo |
| III. B2B y taxonomía cerrada | Filtrar B2C y ruido. Una etiqueta y un módulo oficiales. El mismo comentario, una sola vez. Criticidad por porcentaje: ≤20 verde, >20 y ≤50 amarillo, >50 rojo | Pasa. El esquema rechaza módulos y etiquetas ajenos. El color se calcula del conteo |
| IV. Auditoría y apagado | Cada hallazgo tiene registro, y la Líder UX puede detener el ciclo | Pasa. Sin auditoría no hay reporte oficial. La bandera de apagado cierra la compuerta |
| V. Umbrales antes de ampliar autonomía | Menos de 3 minutos, 85 % de finalización, 3 USD y 30 minutos humanos | Pasa. Duración, costo y validación deciden si el reporte es oficial. `listo_para_comite` solo se enciende si `oficial` es verdadero y la tasa de finalización es de al menos 85 %. Cerrar la cola no lo enciende. El numerador excluye `correccion_lider` |

No hay violaciones. La sección Complexity Tracking no aplica.

Revisión posterior al diseño: los contratos de `contracts/` no agregan un canal de tickets ni una fuente distinta del libro mensual. El dictamen se mantiene.

## Project Structure

### Documentation (this feature)

```text
specs/001-ciclo-mensual/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── reporte.md
│   ├── auditoria.md
│   └── avisos.md
└── tasks.md              # lo produce /speckit-tasks, no este paso
```

### Source Code (repository root)

```text
src/orquestador/
├── cli.py                 # correr, revisar, decidir, apagar, reanudar, consultar
├── grafo.py               # ingesta → métricas → voz del cliente → reporte → compuerta
├── ingesta.py
├── captura.py             # guarda filas en el Excel de un mes
├── consulta.py            # total ponderado y las cuatro listas
├── vista.py               # página local
├── metricas.py
├── clasificacion.py
├── privacidad.py
├── reporte.py
├── memoria.py
├── avisos.py
└── modelos.py

conocimiento/
└── taxonomia.md

datos/
├── plantilla-mensual.xlsx
├── meses/
│   └── feedback_response_YYYY-MM.xlsx
└── control/
    └── apagado.flag

salidas/
└── YYYY-MM/
    ├── estado.json
    ├── metricas.json
    ├── reporte.md
    ├── auditoria.jsonl
    ├── revision.json
    ├── decisiones.json
    ├── jira.json
    ├── muestra-auditoria.json
    └── aviso.md

memoria/
└── hallazgos.json

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: El grafo sigue dentro del comando y el estado de cada mes queda en archivos. La página local no tiene base de datos: al guardar escribe solo `datos/meses/feedback_response_YYYY-MM.xlsx` y, al consultar, lee `salidas/YYYY-MM/metricas.json`, `salidas/YYYY-MM/auditoria.jsonl`, `decisiones.json` y `jira.json`. La corrida no reescribe el libro ni borra las claves de `jira.json`. El único canal de tickets es el envío manual desde Tipificados hacia Jira. El agrupado por embeddings ocurre en la voz del cliente, antes de clasificar, y la auditoría guarda cada comentario del grupo.

## Complexity Tracking

No aplica. El diseño no incumple la constitución.
