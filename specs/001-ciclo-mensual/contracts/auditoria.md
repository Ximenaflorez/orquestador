# Contrato: auditoría y memoria

## auditoria.jsonl

Una línea JSON por hallazgo, incluidos los que esperan revisión. Campos obligatorios:

| Campo | Tipo |
|-------|------|
| hallazgo_id | texto |
| mes | `YYYY-MM` |
| comentario_anonimizado | texto |
| sentimiento | `positivo`, `neutral` o `negativo` |
| intensidad | entero 0 a 100 |
| justificacion | texto |
| modulo | texto o null |
| etiqueta | texto o null |
| confianza | entero 0 a 100 |
| criticidad | `verde`, `amarillo` o `rojo` |
| porcentaje | número. Conteo sobre las preguntas abiertas que entran a tipificación, por 100 |
| comentarios | lista de textos. Cada comentario anonimizado que entró al hallazgo, con la redacción de esa fila |
| sintesis | texto de máximo dos líneas. Título del hallazgo |

El comentario no contiene un correo, un teléfono ni una secuencia de 6 a 12 dígitos que haya estado en el original. Esos tramos aparecen como `[dato oculto]`.

Si a un hallazgo le falta su línea, la salida es inválida y la corrida aplica el reintento descrito en el comando `correr`.

## memoria/hallazgos.json

Objeto cuya clave es la firma `modulo::friccion-normalizada`. Cada valor tiene:

| Campo | Tipo |
|-------|------|
| mes_descarte | `YYYY-MM` |
| reapariciones | lista de `YYYY-MM` |

Solo `decidir --resultado rechazado` agrega o actualiza una firma. `correr` la consulta y, cuando las dos reapariciones siguientes al descarte ya están completas, marca ese hallazgo como `reincidente` en `reporte.md` y en `auditoria.jsonl` mediante el campo adicional `marca: "REINCIDENTE"`.

## muestra-auditoria.json

| Campo | Tipo |
|-------|------|
| mes | `YYYY-MM` |
| items | lista de `respuesta_id`, `pestaña`, `puntaje` y `valor` |

Dos corridas del mismo archivo, sin cambiar el libro, producen la misma lista.
