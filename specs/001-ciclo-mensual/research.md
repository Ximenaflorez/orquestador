# Research: Ciclo mensual de métricas UX

## Runtime y lenguaje

- **Decision**: Python 3.12 con uv.
- **Rationale**: El recorrido debe ejecutarse solo, el día 1, sobre Windows. Python 3.12 tiene soporte estable en LangGraph, Pydantic y openpyxl. En esta máquina uv ya puede instalar esa versión. La 3.14 disponible en el perfil no se usa como runtime del proyecto.
- **Alternatives considered**: Quedarse en la 3.14 del perfil. Se rechaza porque el ecosistema del grafo todavía fija sus pruebas en 3.11 y 3.12.

## Motor del ciclo

- **Decision**: LangGraph con cinco nodos fijos: ingesta, métricas, voz del cliente, reporte y compuerta.
- **Rationale**: El negocio ya comparó opciones y pidió un camino ordenado, con una arista cuando la confianza baja de 70 %. Los números no pasan por el modelo. El modelo solo ve las preguntas abiertas que sobrevivieron al filtro.
- **Alternatives considered**: CrewAI, porque conversar entre roles alarga la corrida y afloja la taxonomía. Un asistente de terminal, porque el cierre de las 06:00 tiene que ocurrir sin una persona delante. n8n como motor, porque agrega otro sistema para un lote que cabe en un comando.

## Lectura del libro

- **Decision**: openpyxl lee `datos/meses/feedback_response_YYYY-MM.xlsx`. Las únicas pestañas de datos son `Creacion de Vacantes`, `Catalogo` y `Gestion de Vacantes`. `Como usarla` y `Vacantes Stages` se ignoran.
- **Rationale**: Es el contrato que quedó en la plantilla y en la especificación. El mes sale del nombre del archivo. Una fecha fuera de ese mes se alerta y se excluye.
- **Alternatives considered**: Aceptar un libro histórico y filtrar por una fecha escrita a mano. La Líder UX ya eligió un archivo por mes para no mezclar periodos ni subir el archivo confidencial.

## Métricas y clasificación

- **Decision**: CSAT, CES y CSAT 2 se calculan en Python como promedio de enteros del 1 al 5. El vacío y lo que esté fuera de escala no entran al promedio. La voz del cliente usa un modelo con salida estructurada: módulo, etiqueta, síntesis, sentimiento y confianza de 0 a 100. Por debajo de 70, o si el modelo no entrega confianza, el caso queda en revisión humana. La criticidad no sale del modelo: es verde hasta el 20 % inclusive del total de preguntas abiertas que entran a tipificación, amarillo por encima de ese corte y hasta el 50 % inclusive, y rojo por encima del 50 %. El mismo texto normalizado es un hallazgo. Con `MODEL_EMBEDDING_NAME`, las frases cuya similitud de coseno llega al umbral `MODEL_EMBEDDING_UMBRAL` (0,85 por defecto) se unen antes de clasificar. El conteo lo cuenta Python. La síntesis es el título y `comentarios` guarda cada texto original anonimizado. Si la llamada falla o no hay ese modelo, el agrupado vuelve al texto idéntico. NotebookLM no se conecta al ciclo.
- **Rationale**: Separa el cálculo auditable del juicio semántico. Cumple la prohibición de imputar cifras y la de inventar etiquetas.
- **Alternatives considered**: Pedirle al modelo también los promedios. Se rechaza porque la muestra del 10 % no podría recalcularse de forma independiente.

## Proveedor del modelo

- **Decision**: Un extremo compatible con la API de chat de OpenAI, configurado con `MODEL_BASE_URL`, `MODEL_NAME` y `MODEL_API_KEY`. El precio por millón de tokens se configura con `MODEL_USD_PER_MILLION`. Si no hay clave, las métricas se calculan igual y todas las quejas quedan en revisión humana, con costo 0. Si el costo acumulado llega a 3 USD, se cortan las llamadas restantes y el reporte no queda oficial. Los embeddings de esta instalación usan el extremo compatible de Gemini: `MODEL_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai` y `MODEL_EMBEDDING_NAME=gemini-embedding-001`, con la clave gratuita de AI Studio. El plan Plus de Gemini y Cursor no sirven como esa clave. Abrir el ojo no llama al modelo.
- **Rationale**: El techo de 3 USD y el cierre desatendido importan más que fijar una marca. La misma configuración sirve para un proveedor hospedado o un extremo local. Las muestras se pueden comprobar sin gastar tokens. Gemini expone embeddings en el formato que la corrida ya llama.
- **Alternatives considered**: Atar el ciclo a un único proveedor. Se rechaza porque la Líder UX todavía no eligió la cuenta de modelo. Dejar la clasificación solo con reglas fijas. Se rechaza porque la taxonomía exige leer matices de usabilidad, falla y rendimiento. Usar NotebookLM o el plan Plus como motor. Se rechaza porque no hay una API que la corrida pueda llamar.

## Privacidad y red

- **Decision**: Antes de persistir o de llamar al modelo, correos, teléfonos y secuencias de documento se sustituyen por `[dato oculto]`. El proceso no tiene búsqueda web ni cliente de Azure DevOps. La corrida no llama a Jira. La página puede crear issues en Jira cuando la Líder UX envía hallazgos que se quedan. Las salidas de red de la corrida siguen siendo el extremo del modelo y el correo SMTP.
- **Rationale**: El texto original debe seguir siendo reconocible para auditar el agrupamiento, y los datos de contacto no deben viajar al comité ni al modelo.
- **Alternatives considered**: Guardar el comentario crudo en el registro y anonimizar solo el Markdown. Se rechaza porque el registro también lo ve el comité.

## Avisos

- **Decision**: Todo aviso se escribe en `salidas/YYYY-MM/aviso.md`. Si existen `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` y `SMTP_TO`, además se envía por correo a la Líder UX. Sin SMTP, el archivo es la evidencia comprobable.
- **Rationale**: La especificación pide el aviso en el momento del fallo. Las pruebas del repositorio no pueden depender de un buzón real.
- **Alternatives considered**: Exigir un servidor de correo para dar por válida la corrida local. Se rechaza porque bloquea la prueba con los meses ficticios.

## Memoria y apagado

- **Decision**: `memoria/hallazgos.json` guarda la clave módulo más fricción, el mes del rechazo y las reapariciones. Al segundo mes seguido con la misma fricción, el hallazgo sale con `[REINCIDENTE]`. `orquestador apagar` crea `datos/control/apagado.flag`. Mientras exista, la corrida no marca el reporte como oficial ni abre la compuerta.
- **Rationale**: El rechazo tiene que sobrevivir de un mes a otro, y el apagado tiene que funcionar aunque el Programador de tareas vuelva a lanzar el comando.
- **Alternatives considered**: Una base de datos para la memoria. Se rechaza porque son pocos hallazgos y el proceso manual debe poder leerlos. Una interfaz gráfica para el apagado. Se rechaza en este corte porque el comando y la bandera ya cubren el protocolo.

## Programación

- **Decision**: El Programador de tareas de Windows ejecuta, el día 1 a las 06:00, `orquestador correr` sin argumentos. Ese modo selecciona el mes calendario anterior y su archivo en `datos/meses/`.
- **Rationale**: Coincide con el cierre posterior al ETL y no deja un servicio residente.
- **Alternatives considered**: Un demonio propio esperando la hora. Se rechaza porque Windows ya tiene el programador y el apagado se controla con la bandera.

## Pruebas

- **Decision**: pytest, con pruebas de unidad para filtros y promedios, de contrato para los archivos de salida y de integración para julio completo, libro inválido y ciclo apagado.
- **Rationale**: El denominador y los promedios tienen que poder recalcularse sin mirar la implementación por dentro.
- **Alternatives considered**: Comprobar solo a mano el Markdown. Se rechaza porque la tasa de finalización y la muestra del 10 % necesitan repetirse igual.
