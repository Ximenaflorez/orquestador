# Contrato: línea de comandos

El programa se invoca como `orquestador`. Las rutas son relativas a la raíz del repositorio. El detalle de los archivos está en [reporte.md](./reporte.md), [auditoria.md](./auditoria.md) y [avisos.md](./avisos.md).

## correr

Calcula un mes y escribe su carpeta de salida.

```text
orquestador correr [--mes YYYY-MM] [--archivo RUTA]
```

- Sin argumentos: mes calendario anterior y `datos/meses/feedback_response_YYYY-MM.xlsx`.
- `--mes` elige el mes y busca ese nombre en `datos/meses/`.
- `--archivo` usa esa ruta y toma el mes del nombre. Si ambos se indican, el mes del nombre y `--mes` deben coincidir.

Salidas:

| Código | Cuándo |
|--------|--------|
| 0 | Existe `salidas/YYYY-MM/reporte.md` y `estado.json` dice `oficial: true` |
| 2 | Entrada inválida. Hay aviso y no hay reporte oficial |
| 3 | La salida falló dos veces, se superó el tiempo o el costo, o el ciclo está apagado |
| 1 | Error inesperado de ejecución |

## revisar

La Líder UX cierra un caso de la cola humana.

```text
orquestador revisar --mes YYYY-MM --id HALLAZGO --etiqueta ETIQUETA --modulo MODULO
```

`ETIQUETA` es `BUG`, `UX/Usabilidad`, `PERFORMANCE` o `FEATURE`. `MODULO` es uno de los siete nombres oficiales, sin corchetes. El comando no recibe criticidad: el color ya quedó calculado.

El comando actualiza el hallazgo a `clasificado`, marca `correccion_lider` y reescribe el reporte. No acepta el hallazgo ante el comité. Código 0 si el identificador existe. Código 2 si el identificador o la taxonomía no sirven.

## decidir

Registra la decisión tripartita.

```text
orquestador decidir --mes YYYY-MM --id HALLAZGO --resultado aceptado|rechazado --deseabilidad TEXTO --factibilidad TEXTO --viabilidad TEXTO
```

Escribe en `decisiones.json` y, si el resultado es `rechazado`, en `memoria/hallazgos.json`. No crea tickets. Código 0 cuando el hallazgo está `clasificado` o `reincidente`. Código 2 en cualquier otro estado.

## apagar y reanudar

```text
orquestador apagar
orquestador reanudar
```

`apagar` crea `datos/control/apagado.flag`. `reanudar` la elimina. Una corrida que encuentra la bandera escribe el aviso de tipo `apagado`, deja `oficial` en falso y termina con código 3. El libro de entrada no cambia.

## Variables de entorno

| Variable | Uso |
|----------|-----|
| MODEL_BASE_URL | Extremo de chat. Vacío o ausente junto con la clave: no hay llamadas |
| MODEL_NAME | Nombre del modelo |
| MODEL_API_KEY | Secreto. No se escribe en salidas ni en el repositorio |
| MODEL_USD_PER_MILLION | Precio usado para el techo de 3 USD |
| SMTP_HOST, SMTP_PORT, SMTP_FROM, SMTP_TO | Si están las cuatro, el aviso también sale por correo |
