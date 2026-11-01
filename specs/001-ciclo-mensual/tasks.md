# Tasks: Ciclo mensual de métricas UX

**Input**: Design documents from `/specs/001-ciclo-mensual/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Incluidas. plan.md fija pytest, research.md define la pirámide y quickstart.md exige `uv run pytest`. Dentro de cada historia, las pruebas se escriben primero y deben fallar antes de la implementación.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/orquestador/`, `tests/` at repository root
- Paths shown below follow `specs/001-ciclo-mensual/plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Proyecto Python 3.12 y carpetas del ciclo, sin lógica de negocio

- [x] T001 Create `src/orquestador/__init__.py` and the directories from plan.md: `src/orquestador/`, `conocimiento/`, `datos/control/`, `salidas/`, `memoria/`, `tests/unit/`, `tests/contract/`, and `tests/integration/`
- [x] T002 [P] Create `pyproject.toml` with `requires-python >=3.12,<3.13`, dependencies `langgraph`, `openpyxl`, and `pydantic`, dev dependency `pytest`, package layout `src`, and console script `orquestador = orquestador.cli:main`
- [x] T003 [P] Create `.gitignore` ignoring `.env`, `.venv/`, `salidas/`, `__pycache__/`, and `*.pyc`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modelos, configuración, taxonomía, anonimización y lectura del libro. Ninguna historia empieza antes de cerrar esta fase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create `src/orquestador/modelos.py` with the entities from `specs/001-ciclo-mensual/data-model.md`. Enforce these constraints verbatim: CSAT, CSAT 2 y CES son "Entero 1 a 5, o vacío"; CSAT 2 es "Solo en catálogo"; el ruido es texto vacío o `.`, `..`, `n`, `na`, `nada`, `ok` tras recortar y pasar a minúsculas; la confianza es "Entero 0 a 100. Si falta, se trata como menor de 70"; la síntesis tiene "Máximo dos líneas"; el sentimiento es `positivo`, `neutral` o `negativo`; la criticidad es `verde`, `amarillo`, `rojo` o vacía solo si todavía no hay conteo. Rechaza `Crítico` y `Medio`. El color lo fija el conteo, no el modelo. T045 dejó esa regla en el código; la etiqueta es `[BUG]`, `[UX/Usabilidad]`, `[PERFORMANCE]`, `[FEATURE]` o vacía en revisión
- [x] T005 [P] Implement `src/orquestador/config.py` reading `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY`, `MODEL_USD_PER_MILLION`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, and `SMTP_TO`. A missing model key means no model calls and cost 0
- [x] T006 [P] Write `conocimiento/taxonomia.md` with the only allowed modules `[Gestión de Vacantes]`, `[Catálogo de Candidatos]`, `[Solicitud de vacantes]`, `[Creación de vacantes]`, `[Carga Masiva de Perfiles]`, `[Analítica / Superset]`, and `[Bot omnicanal]`, and the only labels `[BUG]`, `[UX/Usabilidad]`, `[PERFORMANCE]`, and `[FEATURE]`. Criticidad is `verde` up to 20% inclusive, `amarillo` above 20% and up to 50% inclusive, and `rojo` above 50%. The leader does not choose it. Below 70 confidence there is no final label. T048 wrote this rule
- [x] T007 [P] Implement `src/orquestador/privacidad.py` so emails, phone numbers, and identity sequences of 6 to 12 digits are replaced by the exact marker `[dato oculto]`, keeping the rest of the user text
- [x] T008 Implement `src/orquestador/ingesta.py` for `feedback_response_YYYY-MM.xlsx`. Required sheets are exactly `Creacion de Vacantes`, `Catalogo`, and `Gestion de Vacantes`. Ignore every other sheet, including `Vacantes Stages` and `Como usarla`. Take the month from the filename. A date outside that month sets `fuera_de_mes`. A user-type value `B2C` sets `es_b2c`. If that column is absent, every row is B2B. Do not write back to the workbook

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Recibir el reporte del mes (Priority: P1) 🎯 MVP

**Goal**: Con un libro mensual válido, la Líder UX obtiene la tabla de CSAT, CES y CSAT 2, las quejas tipificadas y la muestra del 10 %. El libro de entrada no cambia.

**Independent Test**: `orquestador correr --mes 2026-07` sobre `datos/meses/feedback_response_2026-07.xlsx` produce un reporte de julio legible sin abrir las tres pestañas ni calcular promedios.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Add a contract test in `tests/contract/test_reporte.py` for `specs/001-ciclo-mensual/contracts/reporte.md`: sections in order, columns `Métrica`, `Valor calculado`, and `Tamaño de muestra (n)`, CSAT and CES for each sheet, CSAT 2 only for Catálogo, and averages rounded to two decimals
- [x] T010 [P] [US1] Add an integration test in `tests/integration/test_correr_julio.py` that runs `datos/meses/feedback_response_2026-07.xlsx`, asserts the three sheet names appear, asserts Vacantes Stages is not used, asserts the source sheets and values stay unchanged, and asserts two runs write the same `salidas/2026-07/muestra-auditoria.json`
- [x] T011 [P] [US1] Add a unit test in `tests/unit/test_metricas.py` where empty or out-of-scale scores are excluded, CSAT and CSAT 2 are not averaged together, noise texts `.`, `N`, `nada`, `OK`, `na`, and `..` create no hallazgo, and an empty sheet yields n = 0

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement `src/orquestador/metricas.py`. Exclude empty or non 1-5 scores. Group alerts as `puntaje vacío`, `puntaje fuera de escala`, `fecha fuera de mes`, `fila B2C`, and `pestaña ignorada`, each with a count. Round averages to two decimals. Leave the value empty when n is 0
- [x] T013 [P] [US1] Implement `src/orquestador/clasificacion.py`. Call the model only for anonymized, in-month, non-B2C, non-noise text. Require one official label, one official module, a síntesis of at most two lines, sentimiento, and confianza 0-100. Do not ask the model for criticidad, and ignore it if one is returned. If confianza is missing or below 70, or the comment is ambiguous, set state `requiere_revision` and leave etiqueta and modulo empty. Still keep the color and the percentage calculated from the count, as T046 specifies. With no `MODEL_API_KEY`, every qualitative row goes to `requiere_revision` at cost 0. Stop further calls when accumulated cost reaches 3 USD
- [x] T014 [US1] Implement `src/orquestador/muestra.py`. Select 10% of the scores that entered an average, rounding up to at least one cell when there is data. The selection depends only on the month and respuesta ids, so the same book produces the same list. Write `muestra-auditoria.json` with `mes` and items of `respuesta_id`, `pestaña`, `puntaje`, and `valor`
- [x] T015 [US1] Implement `src/orquestador/reporte.py` writing `salidas/YYYY-MM/reporte.md`, `metricas.json`, and `auditoria.jsonl` per `specs/001-ciclo-mensual/contracts/reporte.md` and `specs/001-ciclo-mensual/contracts/auditoria.md`. Group hallazgos by module. A classified item shows label, criticidad, síntesis of at most two lines, and conteo. Items in `requiere_revision` appear only under Revisión humana as `[REQUIERE_REVISION_HUMANA]`, with id, anonymized text, and reason. Render an empty metric value as `sin dato`
- [x] T016 [US1] Implement the happy path in `src/orquestador/grafo.py`: ingesta, métricas, voz del cliente, reporte. Record `inicio`, `fin`, `duracion_segundos`, and `costo_usd` in `estado.json`. Set `oficial` true only when input and output are valid, duration is under 180 seconds, cost is at most 3 USD, and the kill flag is absent. Set `listo_para_comite` true only when `oficial` is true and the completion rate is at least 85%. Closing the human queue does not set it. The numerator is classified rows with `correccion_lider` false. The denominator is the open questions that enter classification
- [x] T017 [US1] Implement `orquestador correr --mes YYYY-MM` and `--archivo` in `src/orquestador/cli.py`. If both are present, the filename month and `--mes` must match. Exit 0 when `estado.json` has `oficial` true

**Checkpoint**: User Story 1 is functional and testable on the July sample without the later stories

---

## Phase 4: User Story 2 - Detener una corrida que no se puede confiar (Priority: P2)

**Goal**: Una entrada inválida o una salida que falla dos veces no produce reporte oficial y deja un aviso para la Líder UX.

**Independent Test**: Un libro temporal sin la pestaña `Gestion de Vacantes` termina con código 2, `aviso.md` de tipo `entrada_invalida` y `oficial` en falso.

### Tests for User Story 2 ⚠️

- [ ] T018 [P] [US2] Add a contract test in `tests/contract/test_avisos.py` for the subject, the recipient `Líder UX`, and the types `entrada_invalida` and `salida_invalida` defined in `specs/001-ciclo-mensual/contracts/avisos.md`
- [ ] T019 [P] [US2] Add an integration test in `tests/integration/test_entrada_invalida.py` using a temporary copy, not the sample files. A missing `Gestion de Vacantes` sheet exits 2, writes `entrada_invalida`, and sets `oficial` false. A July file whose dates all fall outside 2026-07 does the same
- [ ] T020 [P] [US2] Add a unit test in `tests/unit/test_reintento.py` where the first invalid output is retried once and the second failure sets `oficial` false and writes `salida_invalida`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `src/orquestador/avisos.py` writing `salidas/YYYY-MM/aviso.md`. When `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, and `SMTP_TO` are all set, send the same subject and body. Append `Correo: no enviado` after a failed send and `Correo: enviado` after a successful one. Do not delete `aviso.md` if mail fails
- [ ] T022 [US2] Extend `src/orquestador/grafo.py` so invalid input stops with no business retry. Invalid output is a missing required table, a label or module outside the official lists, or a hallazgo without its auditoría line. Retry that output once. The second failure blocks the handoff and prevents an official report
- [ ] T023 [US2] Map exit codes in `src/orquestador/cli.py`: 2 for invalid input, 3 when output fails twice or duration reaches 180 seconds or cost reaches 3 USD before every complaint is classified, and 1 for an unexpected error

**Checkpoint**: User Stories 1 and 2 both work. A bad book cannot be presented as the official report

---

## Phase 5: User Story 3 - Revisar y decidir sin crear tickets (Priority: P3)

**Goal**: La Líder UX cierra la cola ambigua y el comité acepta o rechaza. El rechazo se recuerda. Ninguna decisión crea un ticket.

**Independent Test**: Un caso con confianza menor a 70 queda en revisión. Un rechazo queda en `decisiones.json` y en `memoria/hallazgos.json`, y no aparece ningún ticket.

### Tests for User Story 3 ⚠️

- [ ] T024 [P] [US3] Add a contract test in `tests/contract/test_auditoria.py` requiring each `auditoria.jsonl` line to include `hallazgo_id`, `mes`, `comentario_anonimizado`, `sentimiento`, `intensidad`, `justificacion`, `modulo`, `etiqueta`, and `confianza`. Where the source had an email, a phone, or a 6-12 digit sequence, the stored comment contains `[dato oculto]` and not the raw value
- [ ] T025 [P] [US3] Add an integration test in `tests/integration/test_decidir.py`. `revisar` moves `requiere_revision` to `clasificado` and sets `correccion_lider` true. `decidir --resultado rechazado` appends `decisiones.json` and `memoria/hallazgos.json` without deleting the hallazgo. No output file describes a created ticket. The same rejected signature, present again in the next two monthly runs, is marked `REINCIDENTE` on the second of those runs

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/orquestador/memoria.py` for `memoria/hallazgos.json`. The key is `modulo::friccion-normalizada`. The value has `mes_descarte` and `reapariciones`. Only a rejection updates the file
- [ ] T027 [US3] Implement `orquestador revisar` in `src/orquestador/cli.py` with `--mes`, `--id`, `--etiqueta`, and `--modulo`. Etiqueta is `BUG`, `UX/Usabilidad`, `PERFORMANCE`, or `FEATURE`. Modulo is one of the seven official names without brackets. The command does not accept criticidad. Exit 0 when the id exists and 2 when the id or the taxonomy is invalid. Rewrite `reporte.md` and keep the color already calculated from the count. Do not accept the hallazgo for the committee
- [ ] T028 [US3] Implement `orquestador decidir` in `src/orquestador/cli.py` with `--resultado aceptado|rechazado` plus `--deseabilidad`, `--factibilidad`, and `--viabilidad`. Allow only states `clasificado` or `reincidente`. Exit 2 otherwise. `aceptado` records the decision and does not create a ticket. `rechazado` keeps the hallazgo as `[DESCARTADO-ESTRATÉGICO]`
- [ ] T029 [US3] Add the compuerta node in `src/orquestador/grafo.py`. `correr` writes `revision.json` for `requiere_revision` items and leaves `decisiones.json` as an empty list. This node must not import or call a Jira or Azure DevOps client
- [ ] T056 [US3] In `src/orquestador/vista.py`, Guardar el mes shows Se queda and Se va and no Decisión column. Both open a modal that requires deseabilidad, factibilidad, and viabilidad. Se va stays closed until the three fields have text. Se queda writes `aceptado` and moves the row to Tipificados. Se va writes `rechazado`, keeps `[DESCARTADO-ESTRATÉGICO]`, and moves the row to Excluidos. `orquestador decidir` writes those same three fields

**Checkpoint**: The committee decision is recorded and the ticket door stays closed

---

## Phase 6: User Story 4 - Correr el cierre y poder apagarlo (Priority: P4)

**Goal**: El día 1 a las 06:00 corre el mes que acaba de cerrar. La Líder UX puede apagar el ciclo y volver al Excel. El color de criticidad no se edita y no genera un aviso de override.

**Independent Test**: `orquestador apagar` y luego `orquestador correr --mes 2026-08` termina con código 3, aviso `apagado` y el libro de agosto intacto.

### Tests for User Story 4 ⚠️

- [ ] T030 [P] [US4] Add an integration test in `tests/integration/test_apagado.py`. `apagar` creates `datos/control/apagado.flag`. The following `correr` exits 3, writes aviso type `apagado`, sets `oficial` false, and leaves the source workbook unchanged. `reanudar` removes the flag

### Implementation for User Story 4

- [ ] T031 [US4] Implement `orquestador apagar` and `orquestador reanudar` in `src/orquestador/cli.py` using `datos/control/apagado.flag`
- [ ] T032 [US4] In `src/orquestador/cli.py`, `correr` with no arguments selects the previous calendar month and `datos/meses/feedback_response_YYYY-MM.xlsx`. A missing file is `entrada_invalida`
- [ ] T033 [US4] In `src/orquestador/grafo.py`, a change of etiqueta or modulo sets `correccion_lider` and does not count toward the completion rate. Do not emit aviso type `override` for criticidad. The color stays the one calculated from the count. Keep the ticket door closed for this cut
- [ ] T034 [US4] Create `scripts/programar-cierre.ps1` registering a Windows Task Scheduler job for day 1 at 06:00, working directory the repo root, action `uv run orquestador correr`

**Checkpoint**: All four stories work. The scheduled run and the kill switch can be demonstrated without creating tickets

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cerrar la privacidad y recorrer la guía de validación completa

- [ ] T035 [P] Add `tests/unit/test_privacidad.py` for an email, a phone, and a 6-12 digit document, asserting the marker `[dato oculto]` and that the surrounding words remain
- [ ] T036 Run the six scenarios in `specs/001-ciclo-mensual/quickstart.md` on temporary copies. Do not edit `datos/meses/feedback_response_2026-07.xlsx`, `datos/meses/feedback_response_2026-08.xlsx`, or `datos/meses/feedback_response_2026-09.xlsx` in place
- [ ] T037 [P] Update the scheduled-run section of `specs/001-ciclo-mensual/quickstart.md` so it points to `scripts/programar-cierre.ps1`

---

## Phase 8: User Story 5 - Ver el mes, el total y el histórico (Priority: P5)

**Goal**: La Líder UX guarda el Excel de un mes sin tocar los otros, y consulta el resultado de ese mes, el total ponderado de los meses ya corridos y el histórico de lo tipificado.

**Independent Test**: Tras correr julio y agosto, la consulta de julio muestra sus métricas y un total ponderado por n. Un caso sin decidir queda en Guardar el mes. Uno que se queda, con o sin etiqueta oficial y sin clave en `jira.json`, queda en Tipificados. Enviar a Jira rechaza el que no tiene etiqueta oficial. Guardar un mes nuevo no cambia los libros ya existentes.

### Tests for User Story 5 ⚠️

- [x] T038 [P] [US5] Add a unit test in `tests/unit/test_consulta.py` where July CSAT 4.00 with n 10 and August CSAT 2.00 with n 30 produce a total of 2.50. A metric with n 0 is excluded. A hallazgo that stays and has no official etiqueta remains in Tipificados and is rejected by Enviar a Jira. A month folder missing from `salidas/` is omitted from both
- [x] T039 [P] [US5] Add an integration test in `tests/integration/test_captura.py` that saves rows for `2026-06` and leaves `datos/meses/feedback_response_2026-07.xlsx` unchanged

### Implementation for User Story 5

- [x] T040 [P] [US5] Implement `src/orquestador/captura.py` so it writes `feedback_response_YYYY-MM.xlsx` with the sheets `Creacion de Vacantes`, `Catalogo`, and `Gestion de Vacantes`. Catalogo keeps `CSAT 2`. Scores outside 1 to 5 are rejected. Saving one month does not open the other month files
- [x] T041 [P] [US5] Implement `src/orquestador/consulta.py`. For each metric, the total is the sum of valor times n divided by the sum of n, using only months that have `salidas/YYYY-MM/metricas.json` and only rows with n greater than 0. The history reads `auditoria.jsonl`. Phase 11 replaces the rule that kept only official etiquetas
- [x] T042 [US5] Implement `src/orquestador/vista.py` as a local page. The page must not call the model or send mail. Ticket creation is the separate Jira action in T049. Phase 11 replaces the three-area layout
- [x] T043 [US5] Add `orquestador consultar` in `src/orquestador/cli.py` to open that page on localhost

**Checkpoint**: July and August can be stored and compared without changing the run that builds each report. Stories 2, 3, and 4 stay pending

---

## Phase 10: Enviar a Jira los que se quedan

**Goal**: En Tipificados se marca uno o varios hallazgos que se quedan y tienen etiqueta oficial, y la página crea el issue en Jira. La corrida mensual no crea tickets. El token no entra al repositorio.

**Independent Test**: Un caso aceptado con etiqueta oficial produce una clave de Jira y no se vuelve a crear. Un caso rechazado, sin decidir o sin etiqueta no sale. Sin `JIRA_API_TOKEN` no hay llamada de red.

- [x] T049 Add `src/orquestador/jira.py` and the Tipificados selection on `src/orquestador/vista.py`. `POST /api/jira` creates one or many issues from `mes` and `id` only. Eligible rows are `aceptado` with an official etiqueta. The key is stored in `salidas/YYYY-MM/jira.json`. Configuration is `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT`, and optional `JIRA_ISSUE_TYPE`. The button is visible only on the Tipificados tab

---

## Phase 11: Cuatro listas de la consulta

**Goal**: La página abre en Guardar el mes. Tipificados, Backlog y Excluidos separan se queda, ya enviado y se va. Enviar a Jira solo se ve en Tipificados.

**Independent Test**: Un caso sin decidir queda en Guardar el mes. Uno aceptado sin clave queda en Tipificados. Uno aceptado con clave queda en Backlog. Uno rechazado queda en Excluidos.

T041 y T042 describían un histórico único de etiquetas oficiales. Esta fase reemplaza esa vista.

- [x] T050 Split `src/orquestador/consulta.py` into Guardar el mes, Tipificados, Backlog, and Excluidos using `decisiones.json` and `jira.json`
- [x] T051 Put Guardar el mes first in `src/orquestador/vista.py`. Keep Total e histórico above the tabs. Show Enviar a Jira only on Tipificados, disabled until a row is selected

---

## Phase 12: Síntesis y comentarios de origen

**Goal**: Las frases parecidas pueden formar un hallazgo cuando hay modelo de embeddings. En Guardar el mes, Tipificados, Backlog y Excluidos el ojo muestra los comentarios que originaron la síntesis.

**Independent Test**: «La pantalla se queda en blanco» y «Se queda en blanco la pantalla» quedan en un hallazgo y los dos textos se conservan. «Al cambiar la ciudad, el listado de cargos queda en blanco» queda aparte. Sin `MODEL_EMBEDDING_NAME`, las dos primeras no se unen.

- [x] T052 Group similar anonymized comments in `src/orquestador/clasificacion.py` when `MODEL_EMBEDDING_NAME` is set. The threshold is `MODEL_EMBEDDING_UMBRAL`, default 0.85. A failed call keeps exact-text groups. `conteo` is the number of comments. Store every original in `comentarios`
- [x] T053 Show the síntesis on each of the four lists and open `comentarios` from the eye in `src/orquestador/vista.py`

---

## Phase 13: Hallazgos en acordeón y frases distintas

**Goal**: En Guardar el mes no hay columna Decisión. El ojo abre Hallazgos como una fila de la tabla, con una línea por comentario, aunque las frases no sean idénticas. Los Excel de ejemplo traen esas variantes.

**Independent Test**: El ojo de «El formulario vuelve a pedir el salario después de la vista previa» lista tres redacciones distintas. Otro clic cierra la fila. Un comentario que aparece una sola vez sigue en una línea.

- [x] T054 In Guardar el mes, remove the Decisión column and open Hallazgos as a table row from the eye in `src/orquestador/vista.py`. The page must not call the model for that list
- [x] T055 Write distinct paraphrases of each repeated comment into `datos/meses/feedback_response_2026-07.xlsx`, `feedback_response_2026-08.xlsx`, and `feedback_response_2026-09.xlsx`, and store those lines in `comentarios` of each month's `auditoria.jsonl`
- [ ] T057 [US5] In Tipificados, Backlog, and Excluidos, the eye in `src/orquestador/vista.py` shows `resultado`, deseabilidad, factibilidad, and viabilidad beside the stored comments. The other columns keep their width
- [ ] T058 [P] [US5] Extend `src/orquestador/consulta.py` with a filter of one month, a quarter, or a semester. The header names every month in that window. Rows are the three areas and columns are the periods. CSAT 2 is excluded from this table. A metric with n = 0 is `sin dato` and stays out of the weighted total. July CSAT 4.00 with n 10 and August CSAT 2.00 with n 30 still total 2.50 on the 1 to 5 scale
- [ ] T059 [US5] In `src/orquestador/vista.py`, show that CSAT total as a percentage of 5: 4.00 as 80 %, 2.00 as 40 %, and 2.50 as 50 %. Show CES as 4.00, 2.00, and 2.50. Place this table above the four tabs

---

## Phase 9: Criticidad por porcentaje

**Goal**: El mismo comentario del mes es un hallazgo. Su color es verde hasta el 20 % inclusive, amarillo por encima de 20 % y hasta el 50 % inclusive, y rojo por encima del 50 %. El porcentaje usa las preguntas abiertas que entran a tipificación. Ni el modelo ni la Líder UX escriben el color.

**Independent Test**: Con 100 preguntas abiertas válidas, conteos de 20, 21, 50 y 51 producen verde, amarillo, amarillo y rojo. Dos filas con el mismo texto producen un hallazgo de conteo 2.

T004, T006 y T013 describen ya la regla de color. T045–T048 la dejaron en el código.

- [x] T044 [P] Add a unit test in `tests/unit/test_criticidad.py`. One hundred qualitative rows and counts 20, 21, 50, and 51 yield `verde`, `amarillo`, `amarillo`, and `rojo`. Two identical comments become one hallazgo with conteo 2. A criticidad value returned by the model is ignored
- [x] T045 [US1] In `src/orquestador/modelos.py`, allow criticidad `verde`, `amarillo`, `rojo`, or empty. Reject `Crítico` and `Medio`
- [x] T046 [US1] In `src/orquestador/clasificacion.py`, group the same normalized comment once and set the color from conteo divided by the month's classifiable open questions. Do not ask the model for criticidad
- [x] T047 [US1] In `src/orquestador/reporte.py`, write `porcentaje` and the color beside conteo in `reporte.md` and `auditoria.jsonl`
- [x] T048 [P] Update `conocimiento/taxonomia.md` so criticidad is the three colors and the three percentage bands, and state that the leader does not choose it

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 7)**: Depends on the user stories that will be delivered
- **User Story 5 (Phase 8)**: Depends on User Story 1. It does not wait for Stories 2, 3, or 4

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on other stories
- **User Story 2 (P2)**: Starts after User Story 1 because it extends `grafo.py` and `cli.py`
- **User Story 3 (P3)**: Starts after User Story 1. It adds the queue and the committee records
- **User Story 4 (P4)**: The kill switch and the day-1 command start after User Story 1. T033 only records etiqueta and modulo corrections. It does not wait on a criticidad override
- **User Story 5 (P5)**: Starts after User Story 1. It reads `salidas/` and writes only the chosen month workbook
- **Phase 9**: Starts after User Story 1. T045–T048 apply the color already described in T004, T006, and T013. T027 and T033 assume this color already exists
- **Phase 11**: Starts after User Story 5 and Phase 10. It replaces the single official-etiqueta history from T041 and T042
- **Phase 12**: Starts after Phase 9 and Phase 11. Similar comments join only when an embedding model is configured, and the four lists keep the original comments
- **Phase 13**: Starts after Phase 12. Guardar el mes opens the stored comments as a table row, and the sample workbooks keep different wording for the same pain
- **T056**: Starts after T028 and T051. The modal writes the same decision as `decidir`
- **T057**: Starts after T054. The eye of Tipificados, Backlog, and Excluidos shows the stored decision
- **T058 and T059**: Start after T041 and T051. T059 waits for T058. The stored total stays on the 1 to 5 scale and the page shows CSAT as a percentage of 5

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models and pure calculations before the graph
- The graph before the command entry point
- The story checkpoint before the next priority

### Parallel Opportunities

- T002 and T003 can run together
- T004, T005, T006, and T007 can run together; T008 waits for T004
- T009, T010, and T011 can run together; then T012 and T013 can run together
- T018, T019, and T020 can run together
- T024 and T025 can run together; T026 can run beside the tests
- T030 can be written while T031 is still pending, and must fail first
- T035 and T037 can run together, apart from T036
- T038 and T039 can run together; then T040 and T041 can run together. T042 waits for both, and T043 waits for T042

---

## Parallel Example: User Story 1

```text
Task: "Contract test in tests/contract/test_reporte.py"
Task: "Integration test in tests/integration/test_correr_julio.py"
Task: "Unit test in tests/unit/test_metricas.py"

Task: "Implement src/orquestador/metricas.py"
Task: "Implement src/orquestador/clasificacion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run July and read `salidas/2026-07/reporte.md`
5. Demo the report before building notices, the committee gate, or the scheduler

### Incremental Delivery

1. Setup + Foundational
2. User Story 1: the monthly report
3. User Story 2: stop a run that cannot be trusted
4. User Story 3: human review and committee decision, still with no tickets
5. User Story 4: day-1 schedule and kill switch
6. User Story 5: save a month, then show its result, the weighted total, and the classified history
7. Polish: privacy unit test and the full quickstart
8. Phase 9: one hallazgo per repeated comment, with verde, amarillo, or rojo from its percentage

### Parallel Team Strategy

After Foundational:

- One person finishes User Story 1
- A second person can prepare the User Story 2 tests, and starts implementation only after `grafo.py` and `cli.py` exist
- User Story 3 and the kill-switch part of User Story 4 can proceed once the July report exists

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Do not implement a task until the Líder UX accepts that implementation slice
- Do not copy the confidential workbook into the repository
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
