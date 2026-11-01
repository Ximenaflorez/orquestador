# Quickstart: comprobar el ciclo mensual

Guía de validación. Los comandos describen el comportamiento esperado cuando el programa exista. El detalle de cada archivo está en [data-model.md](./data-model.md) y en [contracts/](./contracts/).

## Prerrequisitos

- Windows con el Programador de tareas.
- uv instalado.
- Python 3.12 disponible para el proyecto mediante uv.
- Los libros ficticios en `datos/meses/`:
  - `feedback_response_2026-07.xlsx`
  - `feedback_response_2026-08.xlsx`
  - `feedback_response_2026-09.xlsx`
- Esas tres pestañas y ninguna dependencia de Vacantes Stages.
- Para una corrida sin gasto, no definas `MODEL_API_KEY`. Todas las quejas deben ir a revisión humana y el costo debe quedar en 0.

## Preparar

Desde la raíz del repositorio:

```powershell
uv python install 3.12
uv sync
```

## Escenario 1. Julio entrega reporte

```powershell
orquestador correr --mes 2026-07
```

Resultado esperado, sin `MODEL_API_KEY`:

- Código 0 y `estado.json` con `oficial` en verdadero, `listo_para_comite` en falso y `costo_usd` en 0.
- La tasa de finalización queda en 0 % y todas las quejas aparecen en Revisión humana. El reporte se puede leer, y la Líder UX clasifica esos casos con `revisar` antes del comité.
- Existen `salidas/2026-07/reporte.md`, `metricas.json`, `auditoria.jsonl` y `muestra-auditoria.json`.
- El reporte nombra Creacion de Vacantes, Catalogo y Gestion de Vacantes, y no usa Vacantes Stages.
- CSAT 2 aparece solo en Catálogo.
- El libro de julio no cambia de hojas ni de valores.

Con clave de modelo y una clasificación que cumple la taxonomía, el código sigue en 0 y la tasa de finalización refleja solo las quejas que no necesitó corregir la Líder UX.

## Escenario 2. Libro inválido

Quita temporalmente una copia de prueba a la que le falte la pestaña `Gestion de Vacantes`. No modifiques los meses de ejemplo del repositorio.

```powershell
orquestador correr --mes 2026-07 --archivo RUTA\libro-incompleto.xlsx
```

Resultado esperado: código 2, `salidas/2026-07/aviso.md` con tipo `entrada_invalida`, y `estado.json` con `oficial` en falso.

## Escenario 3. Fecha de otro mes

Agrega en una copia una fila de agosto dentro del libro de julio.

Resultado esperado: esa fila aparece como `fecha fuera de mes` en las alertas y no cambia el promedio.

## Escenario 4. Apagado

```powershell
orquestador apagar
orquestador correr --mes 2026-08
orquestador reanudar
```

Resultado esperado: código 3, aviso de tipo `apagado`, libro de agosto intacto y, después de reanudar, la bandera ya no está.

## Escenario 5. Decisión sin ticket

Con un hallazgo ya clasificado:

```powershell
orquestador decidir --mes 2026-09 --id ID --resultado rechazado --deseabilidad "fuera del flujo principal" --factibilidad "no cabe en el sprint" --viabilidad "no mueve la retención"
```

Resultado esperado: el hallazgo queda `descartado` en `decisiones.json` y en `memoria/hallazgos.json`. No aparece un ticket nuevo en ningún archivo de salida.

## Escenario 6. Pruebas automáticas

```powershell
uv run pytest
```

Deben pasar las pruebas de promedios, de ruido, de pestaña ignorada, del contrato de `auditoria.jsonl` y de los escenarios 1, 2 y 4 sobre copias temporales.

## Cierre programado

Crear en el Programador de tareas una acción mensual, día 1 a las 06:00, con inicio en la raíz del repositorio:

```powershell
uv run orquestador correr
```

Antes de esa hora, el libro del mes que acaba de cerrar tiene que estar en `datos/meses/` con el nombre `feedback_response_YYYY-MM.xlsx`. Si no está, el resultado válido es el aviso de entrada inválida.
