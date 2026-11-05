# Orquestador

Ciclo mensual de métricas UX para Magneto. Toma las encuestas de CSAT y CES, calcula el total y el histórico, agrupa los comentarios que se repiten y deja decidir cuáles hallazgos se quedan y cuáles se van. Los que se quedan se pueden enviar a Jira.

La consulta se abre en el navegador. En el celular, Total e histórico y los listados de hallazgos se ven como tarjetas. En escritorio siguen siendo tablas.

## Caso de estudio

La copia pública es de solo lectura:

https://ximenaflorez.github.io/orquestador/

Ahí se puede recorrer la interfaz y los datos de ejemplo. Subir el Excel, guardar Se queda o Se va y enviar a Jira no responden en esa página. Esas acciones necesitan el programa de Python, las credenciales de Jira y los archivos del mes. Dejarlas en una URL pública expondría esas claves y permitiría que cualquiera modificara los datos o creara tickets.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Arranque local

Desde la raíz del repositorio:

```powershell
uv python install 3.12
uv sync
uv run orquestador consultar
```

La consulta queda en http://127.0.0.1:8765/. Con `--sin-navegador` no abre el navegador solo. Con `--puerto` se cambia el puerto.

En la página se puede subir el Excel del mes, revisar Total e histórico, decidir Se queda o Se va y enviar a Jira los hallazgos que se quedan. Después de subir el archivo hay que correr el ciclo para que ese mes entre al total y al histórico.

## Correr un mes

El libro tiene que llamarse `feedback_response_AAAA-MM.xlsx` y estar en `datos/meses/`.

```powershell
uv run orquestador correr --mes 2026-07
```

También se puede indicar otro archivo, siempre que el mes del nombre coincida:

```powershell
uv run orquestador correr --mes 2026-07 --archivo datos\meses\feedback_response_2026-07.xlsx
```

El ciclo lee el libro, calcula las métricas, agrupa la voz del cliente y escribe el resultado en `salidas/AAAA-MM/`. Si no hay `MODEL_API_KEY`, no llama al modelo: las métricas se calculan igual y los comentarios quedan para revisión, con costo 0. El gasto de modelo se corta al llegar a 3 USD.

El libro trae tres hojas: `Creacion de Vacantes`, `Catalogo` y `Gestion de Vacantes`. Cada una tiene `DATE`, `CSAT`, `CES` y `PREGUNTA ABIERTA`. Catálogo además tiene `CSAT 2`.

## Configuración

Las claves van en un archivo `.env` en la raíz. Ese archivo no se sube al repositorio.

| Variable | Uso |
| --- | --- |
| `MODEL_BASE_URL` | Extremo del modelo |
| `MODEL_NAME` | Nombre del modelo |
| `MODEL_API_KEY` | Clave del modelo |
| `MODEL_USD_PER_MILLION` | Precio por millón de tokens |
| `MODEL_EMBEDDING_NAME` | Modelo de embeddings |
| `MODEL_EMBEDDING_UMBRAL` | Umbral de similitud |
| `JIRA_BASE_URL` | Sitio de Jira, con `https://` |
| `JIRA_EMAIL` | Correo de la cuenta |
| `JIRA_API_TOKEN` | Token de Jira |
| `JIRA_PROJECT` | Clave del proyecto |
| `JIRA_ISSUE_TYPE` | Tipo de issue. Si falta, usa `Task` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_TO` | Correo de aviso |

## Pruebas

```powershell
uv run pytest
```

## Qué no se publica

`.env` guarda las claves. `salidas/` guarda los resultados de cada mes, incluidas las decisiones. Ninguno de los dos entra en git.
