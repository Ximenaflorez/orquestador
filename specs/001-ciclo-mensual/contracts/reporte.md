# Contrato: reporte mensual

Cada corrida con entrada legible escribe `salidas/YYYY-MM/`. El libro de `datos/meses/` permanece igual, byte a byte no es la promesa; la promesa es que sus hojas, filas y valores no cambian.

## reporte.md

Documento en español con estas secciones, en este orden:

1. `Resumen de KPIs mensuales`
2. `Alertas de calidad de datos`
3. `Quejas tipificadas`
4. `Revisión humana`
5. `Muestra para auditoría numérica`

La primera sección es una tabla con las columnas `Métrica`, `Valor calculado` y `Tamaño de muestra (n)`. Hay una fila por CSAT y CES de cada pestaña, y una fila de CSAT 2 solo para Catálogo. El valor vacío se escribe como `sin dato` cuando n es 0.

Las alertas agrupan el tipo de anomalía y la cantidad. Los tipos posibles son `puntaje vacío`, `puntaje fuera de escala`, `fecha fuera de mes`, `fila B2C` y `pestaña ignorada`.

Cada hallazgo de `Quejas tipificadas` empieza por el módulo, luego la etiqueta, el color (`verde`, `amarillo` o `rojo`), la síntesis de máximo dos líneas, el conteo y el porcentaje. Un caso en `requiere_revision` no aparece aquí. Su color y su porcentaje sí quedan en la auditoría.

`Revisión humana` lista los casos `[REQUIERE_REVISION_HUMANA]` con el identificador, el texto anonimizado y el motivo.

La muestra enumera los puntajes del 10 % definido en [data-model.md](../data-model.md).

## metricas.json

Lista de métricas con los campos de `Métrica mensual` en el modelo de datos. Los promedios se redondean a dos decimales.

## estado.json

Un objeto con los campos de `Corrida`. `oficial` y `listo_para_comite` siguen las reglas del modelo. Este archivo existe también cuando la entrada es inválida: en ese caso ambos quedan en falso y el resto de los archivos de resultado pueden no existir, salvo `aviso.md`.

## revision.json

Lista de hallazgos en estado `requiere_revision`, con `id`, `pregunta_anonimizada`, `motivo` y `pestaña`.

## decisiones.json

Lista de decisiones del comité. Empieza vacía al terminar `correr`. `decidir` agrega elementos sin borrar los anteriores.
