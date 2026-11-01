# Data Model: Ciclo mensual de métricas UX

Las reglas de validación salen de [spec.md](./spec.md). Los estados de un hallazgo avanzan solo en la dirección descrita abajo.

## Lote mensual

Un libro y un mes.

| Campo | Regla |
|-------|-------|
| mes | `YYYY-MM`, tomado del nombre `feedback_response_YYYY-MM.xlsx` |
| ruta | Archivo dentro de `datos/meses/` |
| pestañas | Deben existir `Creacion de Vacantes`, `Catalogo` y `Gestion de Vacantes` |
| valido | Falso si falta el archivo, falta una pestaña o ninguna fecha cae en el mes |
| motivo | Texto breve cuando `valido` es falso |

Relación: un lote tiene muchas respuestas y una sola corrida.

## Respuesta

Una fila de una pestaña.

| Campo | Regla |
|-------|-------|
| id | Estable dentro del mes: pestaña más número de fila |
| mes | El del lote |
| pestaña | `creacion`, `catalogo` o `gestion` |
| fecha | Fecha y hora de la columna DATE |
| csat | Entero 1 a 5, o vacío |
| csat_2 | Solo en catálogo. Entero 1 a 5, o vacío |
| ces | Entero 1 a 5, o vacío |
| pregunta_abierta | Texto de la celda, puede estar vacío |
| pregunta_anonimizada | El mismo texto con contactos sustituidos por `[dato oculto]` |
| es_b2c | Verdadero solo si una columna de tipo de usuario dice B2C |
| es_ruido | Verdadero si el texto útil, ya sin espacios y en minúsculas, está vacío o es `.`, `..`, `n`, `na`, `nada` u `ok` |
| fuera_de_mes | Verdadero si la fecha no pertenece al mes del archivo |
| exclusion_puntaje | Lista de motivos: vacío o fuera de escala, por cada puntaje afectado |

Una respuesta B2C o fuera de mes no entra a métricas ni a hallazgos. Una pestaña sin filas es válida y produce muestra 0.

## Métrica mensual

| Campo | Regla |
|-------|-------|
| mes | El del lote |
| pestaña | Una de las tres |
| nombre | `CSAT`, `CES` o, solo en catálogo, `CSAT 2` |
| valor | Promedio de los puntajes válidos. Vacío si n es 0 |
| n | Cantidad de puntajes válidos |
| alertas | Tipo de anomalía y cuántas veces ocurrió |

CSAT y CSAT 2 no se promedian entre sí.

## Hallazgo

Una fricción agrupada. El mismo texto normalizado del mes es un solo hallazgo. Si hay modelo de embeddings, los textos con similitud igual o mayor al umbral se unen a ese hallazgo. Si la llamada falla o no hay modelo, cada texto distinto sigue separado.

| Campo | Regla |
|-------|-------|
| id | Identificador dentro del mes |
| mes | El del lote |
| modulo | Uno de los siete módulos oficiales, o vacío mientras exige revisión |
| etiqueta | `[BUG]`, `[UX/Usabilidad]`, `[PERFORMANCE]`, `[FEATURE]`, o vacía en revisión |
| criticidad | `verde`, `amarillo` o `rojo`. La calcula el conteo. Vacía solo si todavía no hay conteo |
| sintesis | Título de máximo dos líneas. No reemplaza la lista de comentarios |
| conteo | Cantidad de comentarios del grupo |
| comentarios | Textos anonimizados de origen, uno por fila, aunque la redacción cambie. En Guardar el mes el ojo los abre como fila de la tabla |
| porcentaje | Conteo dividido por las preguntas abiertas del mes que entran a tipificación, multiplicado por 100 |
| confianza | Entero 0 a 100. Si falta, se trata como menor de 70 |
| sentimiento | `positivo`, `neutral` o `negativo` |
| intensidad | Entero 0 a 100 |
| estado | Ver transiciones |
| respuestas | Identificadores de las filas de origen |
| pestañas | Pestañas que aportaron filas |
| correccion_lider | Verdadero si la Líder UX cambió etiqueta o módulo. El color no se corrige |

### Estados

```text
nuevo
  ├─ confianza >= 70 y taxonomía válida → clasificado
  └─ confianza < 70, ambiguo o taxonomía inválida → requiere_revision

requiere_revision
  └─ la Líder UX fija etiqueta y módulo → clasificado
     (correccion_lider queda verdadero; el color sigue el del conteo)

clasificado
  ├─ el comité acepta → aceptado
  └─ el comité rechaza → descartado

descartado
  └─ la misma firma reaparece en los dos meses siguientes → el hallazgo
     de ese segundo mes nace como reincidente y vuelve al comité
```

`aceptado` en este corte no crea un ticket. `descartado` no se borra.

La tasa de finalización usa como denominador las respuestas con texto que no es ruido, no es B2C y no está fuera de mes. El numerador son las que quedan clasificadas sin `correccion_lider`. Ese mismo denominador es el total del semáforo: hasta el 20 % inclusive es verde, más del 20 % y hasta el 50 % inclusive es amarillo, y más del 50 % es rojo. La criticidad no tiene tasa de override.

## Registro de auditoría

Uno por hallazgo. Si falta, la salida es inválida.

| Campo | Regla |
|-------|-------|
| hallazgo_id | Hallazgo correspondiente |
| comentario_anonimizado | Texto representativo del grupo, el que más se repite |
| comentarios | Lista de los textos anonimizados que originaron la síntesis. Uno por fila del grupo, con la redacción de esa fila |
| sintesis | Título de máximo dos líneas |
| sentimiento | El del hallazgo |
| intensidad | El del hallazgo |
| justificacion | Por qué se agrupó así |

## Decisión del comité

| Campo | Regla |
|-------|-------|
| hallazgo_id | Un hallazgo en estado clasificado o reincidente |
| resultado | `aceptado` o `rechazado` |
| deseabilidad | Texto de la evaluación |
| factibilidad | Texto de la evaluación |
| viabilidad | Texto de la evaluación |
| fecha | Momento del registro |
| actores | Líder UX, Product Owner y Líder de Célula |

## Muestra de auditoría numérica

El 10 % de los puntajes que sí entraron a un promedio, con un redondeo hacia arriba de al menos una celda cuando hay datos. La selección depende solo del mes y de los identificadores de respuesta, así el mismo libro produce la misma muestra.

| Campo | Regla |
|-------|-------|
| mes | El del lote |
| items | id de respuesta, pestaña, nombre del puntaje y valor |

## Aviso operativo

| Campo | Regla |
|-------|-------|
| mes | El del intento |
| tipo | `entrada_invalida`, `salida_invalida`, `apagado`, `tope_costo` o `tope_tiempo` |
| destinatario | Rol Líder UX |
| asunto | Una línea |
| cuerpo | Qué falló y qué archivo revisar |
| emitido_en | Fecha y hora |

## Corrida

| Campo | Regla |
|-------|-------|
| mes | El del lote |
| inicio y fin | Marcas de tiempo |
| duracion_segundos | Fin menos inicio |
| costo_usd | Suma estimada de las llamadas al modelo |
| tasa_finalizacion | Según la regla del hallazgo |
| tasa_override | Queda en 0. La criticidad no se corrige a mano |
| intento_salida | 1 o 2 |
| apagado | Verdadero si existe la bandera |
| oficial | Verdadero solo si la entrada y la salida son válidas, la duración es menor a 180 segundos, el costo es menor o igual a 3 USD, la bandera de apagado no existe y el intento de salida no agotó los dos fallos |
| listo_para_comite | Verdadero solo si `oficial` es verdadero y la tasa de finalización es de al menos 85 %. Cerrar la cola de revisión no lo enciende. Por debajo de ese umbral el reporte se entrega y el comité espera |

## Memoria de hallazgos

Persiste entre meses.

| Campo | Regla |
|-------|-------|
| firma | Módulo más fricción normalizada |
| mes_descarte | Mes en que el comité rechazó |
| reapariciones | Meses posteriores en los que volvió el mismo texto de fricción |

La memoria se actualiza al rechazar y se consulta al armar los hallazgos del mes nuevo.
