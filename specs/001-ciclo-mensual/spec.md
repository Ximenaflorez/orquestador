# Feature Specification: Ciclo mensual de métricas UX

**Feature Branch**: `001-ciclo-mensual`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "Quitar la pestaña Vacantes Stages de los documentos de entrada y especificar el ciclo mensual del orquestador de métricas UX de Magneto. Cada mes entra un libro de feedback con Creación de Vacantes, Catálogo y Gestión de Vacantes. La corrida calcula CSAT y CES, tipifica las quejas, entrega el reporte, deja la revisión humana, corre el día 1 a las 06:00 y avisa si algo falla. Crear tickets queda bloqueado hasta una aprobación posterior del comité."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recibir el reporte del mes (Priority: P1)

La Líder UX entrega el libro de feedback de un mes y recibe un reporte listo para leer: las métricas del periodo y las quejas agrupadas por módulo, con etiqueta y criticidad semaforizada. El libro fuente no se modifica.

**Why this priority**: Este es el resultado que hoy se arma a mano. Sin el reporte, el resto del ciclo no tiene nada que revisar ni que llevar al comité.

**Independent Test**: Se puede probar con `feedback_response_2026-07.xlsx`. El resultado es un reporte de julio que la Líder UX puede leer sin abrir las tres pestañas ni calcular promedios.

**Acceptance Scenarios**:

1. **Given** un libro mensual con las tres pestañas y respuestas del mes indicado en el nombre, **When** la Líder UX inicia la corrida de ese mes, **Then** recibe una tabla con Métrica, Valor Calculado y Tamaño de Muestra (n) para el CSAT y el CES de cada pestaña, el CSAT 2 de Catálogo, y una lista de quejas agrupadas por módulo oficial.
2. **Given** un comentario con contenido cualitativo, **When** la corrida lo clasifica con confianza igual o superior al 70 %, **Then** el hallazgo muestra una sola etiqueta oficial, un solo módulo oficial, el color de criticidad, una síntesis de máximo dos líneas y la cantidad de respuestas que describen la misma fricción. El mismo comentario normalizado del mes es un solo hallazgo. El color lo calcula el ciclo: hasta el 20 % del total de preguntas abiertas que entran a tipificación es verde, más del 20 % y hasta el 50 % es amarillo, y más del 50 % es rojo. Ni el modelo ni la Líder UX escriben ese color.
3. **Given** el mismo libro mensual, **When** la corrida termina, **Then** el archivo de entrada conserva sus filas, columnas y pestañas.

---

### User Story 2 - Detener una corrida que no se puede confiar (Priority: P2)

Si el libro del mes está incompleto o el reporte sale con una estructura o una taxonomía inválida, la Líder UX recibe un aviso por correo y ese reporte no se presenta como listo para el comité.

**Why this priority**: Un reporte con cifras inventadas o etiquetas fuera de la lista oficial trasladaría el error al comité y a futuras decisiones de ingeniería.

**Independent Test**: Se puede probar con un libro al que le falta una pestaña, con una fecha fuera del mes, o con una salida forzada a una etiqueta inexistente. En todos los casos hay aviso y no hay reporte oficial.

**Acceptance Scenarios**:

1. **Given** que el día 1 a las 06:00 no está el libro del mes que acaba de cerrar, o el libro no trae alguna de las tres pestañas, **When** llega la hora de la corrida, **Then** la corrida se detiene, no hay reporte oficial y la Líder UX recibe un correo en ese momento.
2. **Given** un libro válido cuya salida no cumple la tabla, la taxonomía o el registro de auditoría, **When** falla la primera entrega, **Then** hay un solo reintento. Si el segundo resultado también falla, el traspaso queda bloqueado y la Líder UX recibe un correo.
3. **Given** una respuesta sin CSAT o sin CES, o con un puntaje fuera de 1 a 5, **When** se calculan los promedios, **Then** ese puntaje no entra al promedio y aparece en Alertas de Calidad de Datos, agrupado por tipo de anomalía y por cantidad de veces que se repite.

---

### User Story 3 - Revisar y decidir sin crear tickets (Priority: P3)

La Líder UX resuelve los comentarios ambiguos. Después, junto con el Product Owner y el Líder de Célula, acepta o rechaza cada hallazgo. Ninguna decisión de esta corrida crea ni modifica un ticket de desarrollo.

**Why this priority**: La priorización del backlog es la decisión que el negocio se reservó. El reporte ya entrega valor antes de que exista esa compuerta, por eso esta historia va después de la P1.

**Independent Test**: Se puede probar marcando un comentario con confianza menor al 70 % y registrando una aprobación y un rechazo del comité. El resultado visible es la cola de revisión y el estado de cada hallazgo, con cero tickets creados.

**Acceptance Scenarios**:

1. **Given** un comentario ambiguo o con confianza menor al 70 %, **When** la corrida lo evalúa, **Then** no le asigna una etiqueta forzada: lo marca `[REQUIERE_REVISION_HUMANA]` y lo deja en la cola de la Líder UX junto con el texto anonimizado y el motivo de la duda.
2. **Given** un reporte listo y la revisión tripartita, **When** el comité acepta o rechaza un hallazgo, **Then** la decisión queda registrada con deseabilidad, factibilidad y viabilidad. Un rechazo se conserva como `[DESCARTADO-ESTRATÉGICO]`.
3. **Given** cualquier resultado de la corrida, **When** termina el ciclo, **Then** no existe un ticket nuevo ni un cambio de estado en el tablero de desarrollo atribuible a esta corrida.

---

### User Story 4 - Correr el cierre y poder apagarlo (Priority: P4)

El ciclo arranca solo el día 1 a las 06:00 con el libro del mes cerrado. La Líder UX puede detenerlo y volver al análisis manual sobre el mismo archivo.

**Why this priority**: La programación y el apagado protegen la operación mensual. El reporte de la historia P1 ya puede producirse de forma manual mientras esta historia no exista.

**Independent Test**: Se puede comprobar que una corrida del día 1 usa solo el mes cerrado y que, al activar el apagado, el comité no recibe un reporte listo y el libro fuente sigue igual.

**Acceptance Scenarios**:

1. **Given** el libro del mes que acaba de cerrar ya está en la bandeja de entrada el día 1 a las 06:00, **When** llega esa hora, **Then** la corrida usa únicamente las respuestas de ese mes.
2. **Given** una corrida en curso o un reporte aún no llevado al comité, **When** la Líder UX apaga el ciclo, **Then** el reporte deja de estar listo para el comité, la autorización de tickets permanece cerrada y el libro fuente queda intacto para el proceso manual.
3. **Given** un hallazgo ya agrupado, **When** la Líder UX apaga el ciclo o corrige la etiqueta o el módulo, **Then** el color de criticidad sigue siendo el que salió del conteo. Nadie lo edita a mano.

---

### User Story 5 - Ver el mes, el total y el histórico (Priority: P5)

La Líder UX guarda las respuestas de cada mes en su propio libro y consulta tres cosas juntas: el resultado de un mes, el total de los meses ya corridos y el histórico de lo tipificado. Guardar julio no borra junio.

**Why this priority**: El reporte de un mes ya existe. Esta historia lo vuelve consultable junto con los meses anteriores. No sustituye los avisos, el comité ni el apagado.

**Independent Test**: Con los libros de julio y agosto ya corridos, se elige julio y se ve el total ponderado. Guardar el mes abre primero. Tipificados lista lo que se queda y aún no tiene clave de Jira. Excluidos lista lo que se va. Backlog lista lo que ya tiene clave. En las cuatro vistas, el ojo muestra los comentarios que originaron la síntesis.

**Acceptance Scenarios**:

1. **Given** un mes sin archivo, **When** la Líder UX agrega respuestas de Creación de Vacantes, Catálogo y Gestión de Vacantes y guarda, **Then** queda `feedback_response_YYYY-MM.xlsx` con esas filas y los demás meses no cambian.
2. **Given** julio y agosto ya tienen reporte, **When** se consulta el total, **Then** los periodos van en columnas y las tres áreas en filas. El CSAT se muestra como porcentaje de 5 y el CES se queda en la escala de 1 a 5. CSAT 2 no entra en esa tabla. El filtro permite mes, trimestre o semestre, y el encabezado nombra los meses del periodo. El total es el promedio ponderado por el tamaño de muestra, no el promedio de los promedios. Un CSAT de 4,00 se muestra como 80 % y uno de 2,00 como 40 %. Con n 10 y n 30, el total de 2,50 se muestra como 50 %. El CES de esos mismos valores se muestra 4,00, 2,00 y 2,50.
3. **Given** varios meses corridos, **When** se abre la consulta, **Then** Guardar el mes es la primera pestaña y muestra los incidentes del mes elegido que aún no tienen decisión. Tipificados muestra los que se quedan y no tienen clave en `jira.json`, aunque no tengan etiqueta oficial. Excluidos muestra solo los que se van. Backlog muestra los que se quedan y ya tienen clave. Un caso sin decidir no entra en esas tres listas. Un mes guardado que todavía no se corrió no entra al total ni a las listas.
4. **Given** un hallazgo cuyas frases de origen no son idénticas, **When** la Líder UX abre el ojo en Guardar el mes, **Then** se abre una fila de la tabla, titulada Hallazgos, con cada comentario anonimizado. Un clic más la cierra. Esa vista no tiene columna Decisión. Abrir el ojo no llama al modelo: lee los comentarios ya guardados. En Tipificados, Backlog y Excluidos el ojo muestra esa misma lista junto con la decisión.

---

### Edge Cases

- Una pestaña obligatoria existe pero no tiene respuestas. El reporte indica muestra n = 0 para esa pestaña y sigue con las demás. No es un fallo de entrada.
- Una pestaña distinta de las tres obligatorias, incluida Vacantes Stages, no entra al cálculo ni a la tipificación.
- Todas las preguntas abiertas de una pestaña son ruido (`.`, `N`, `nada`, `OK`, `na`, `..`, en cualquier combinación de mayúsculas). Esas filas pueden aportar CSAT y CES, y no generan hallazgos.
- Todas las quejas quedan bajo el 70 % de confianza. El reporte cuantitativo sí se entrega y la lista cualitativa queda completa en la cola humana. La tasa de finalización de ese mes no cuenta esas filas como clasificadas solas.
- El nombre del archivo dice un mes y una o más fechas caen en otro. Esas filas salen del cálculo, aparecen en Alertas de Calidad de Datos y no se tipifican. Si ninguna fecha pertenece al mes del archivo, la entrada se considera inválida.
- Catálogo trae CSAT y CSAT 2. Se reportan por separado. Un vacío en uno no anula el otro.
- El mismo dolor aparece en más de una pestaña. Se conserva un hallazgo por módulo y fricción, con el conteo sumado y la procedencia de cada pestaña visible.
- Un hallazgo rechazado vuelve a aparecer en los dos ciclos mensuales siguientes. En el segundo de esos ciclos se presenta otra vez al comité con la marca `[REINCIDENTE]`.
- El comentario incluye un correo, un teléfono o un documento de identidad. El reporte y el registro que ve el comité muestran el resto del texto, con ese dato reemplazado por un marcador neutro.
- Falta el registro de auditoría de un hallazgo. Ese hallazgo no puede recibir autorización de ticket.
- La Líder UX corrige la etiqueta o el módulo. Esa corrección queda marcada con `correccion_lider` y no entra en el numerador de la tasa de finalización. El color de criticidad no se corrige: vuelve a calcularse con el conteo.
- De 100 preguntas abiertas que entran a tipificación, un comentario con 20 apariciones queda verde, uno con 21 o con 50 queda amarillo, y uno con 51 queda rojo.
- Hay un libro de un mes y todavía no existe su carpeta en `salidas/`. Ese mes no entra al total ni al histórico.
- Un mes corrido no tiene hallazgos que se queden. Tipificados y Backlog quedan vacíos para ese mes y sus métricas sí entran al total.
- Dos frases dicen el mismo dolor con otras palabras y hay modelo de embeddings. Forman un hallazgo y el ojo lista las dos frases, cada una como está escrita. «Al cambiar la ciudad, el listado de cargos queda en blanco» no entra en el grupo de «la pantalla se queda en blanco».
- No hay modelo de embeddings, o la llamada falla. Cada texto distinto sigue siendo su propio hallazgo. El ojo igual muestra el comentario guardado.
- Un hallazgo se queda y no tiene etiqueta oficial. Aparece en Tipificados y Enviar a Jira lo rechaza.
- Catálogo no tiene respuestas en un mes. El total de CSAT 2 usa solo los meses donde esa métrica tiene muestra mayor a cero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El ciclo MUST aceptar un libro de feedback por mes, nombrado con el año y el mes, y MUST limitar la corrida a las pestañas Creacion de Vacantes, Catalogo y Gestion de Vacantes.
- **FR-002**: El ciclo MUST ignorar cualquier otra pestaña, incluida Vacantes Stages.
- **FR-003**: El ciclo MUST tratar cada fila como una respuesta con fecha, CSAT, CES y pregunta abierta. En Catalogo también MUST leer CSAT 2.
- **FR-004**: El ciclo MUST excluir del promedio todo puntaje vacío o fuera de la escala de 1 a 5, y MUST informarlo en Alertas de Calidad de Datos por tipo de anomalía y por cantidad.
- **FR-005**: El ciclo MUST calcular por separado el CSAT y el CES de cada pestaña, con su tamaño de muestra. En Catalogo MUST calcular CSAT 2 como métrica propia, sin mezclarla con CSAT.
- **FR-006**: El ciclo MUST descartar como ruido plano, sin crear un hallazgo, las preguntas abiertas vacías o equivalentes a `.`, `N`, `nada`, `OK`, `na` y `..`.
- **FR-007**: El ciclo MUST clasificar cada pregunta abierta restante con una sola etiqueta (`[BUG]`, `[UX/Usabilidad]`, `[PERFORMANCE]` o `[FEATURE]`) y un solo módulo oficial. El mismo texto normalizado MUST producir un solo hallazgo en el mes. Si `MODEL_EMBEDDING_NAME` está configurado, los textos con similitud igual o mayor al umbral MUST unirse en ese hallazgo. Si la llamada falla, el costo llega al tope o no hay modelo de embeddings, el ciclo MUST dejar el agrupado por texto idéntico. El conteo MUST ser la cantidad de comentarios del grupo. La síntesis MUST ser el título, de máximo dos líneas, y cada comentario original anonimizado MUST conservarse. La criticidad MUST ser `verde`, `amarillo` o `rojo`, calculada por el ciclo y no elegida por el modelo ni por la Líder UX.
- **FR-008**: Los módulos oficiales permitidos son `[Gestión de Vacantes]`, `[Catálogo de Candidatos]`, `[Solicitud de vacantes]`, `[Creación de vacantes]`, `[Carga Masiva de Perfiles]`, `[Analítica / Superset]` y `[Bot omnicanal]`.
- **FR-009**: Si la confianza de una clasificación es menor al 70 %, o el comentario es ambiguo o contradictorio, el ciclo MUST marcarlo `[REQUIERE_REVISION_HUMANA]` y MUST NOT asignarle una etiqueta definitiva.
- **FR-010**: El reporte MUST agrupar los hallazgos por módulo y MUST mostrar, en cada uno, la etiqueta, una síntesis de máximo dos líneas y el número de respuestas que reportan la misma fricción.
- **FR-011**: Cada hallazgo clasificado MUST conservar un registro de auditoría con el comentario ya anonimizado, el sentimiento calculado y la justificación del agrupamiento.
- **FR-012**: El reporte entregado al comité y el registro de auditoría MUST sustituir correos, teléfonos y documentos de identidad por un marcador neutro, y MUST conservar el resto del texto de la persona usuaria.
- **FR-013**: El ciclo MUST NOT inventar respuestas, puntajes, quejas ni módulos que no estén en el libro de ese mes.
- **FR-014**: El ciclo MUST dejar el libro de entrada sin cambios.
- **FR-015**: Una entrada inválida MUST detener la corrida sin reintento de negocio, MUST impedir un reporte oficial y MUST avisar por correo a la Líder UX. La entrada es inválida cuando falta el libro, falta una pestaña obligatoria o ninguna fecha pertenece al mes del archivo.
- **FR-016**: Una salida inválida MUST disparar un solo reintento. Un segundo fallo MUST bloquear el traspaso, MUST impedir un reporte oficial y MUST avisar por correo a la Líder UX. La salida es inválida cuando falta la tabla exigida, aparece una etiqueta o un módulo fuera de la lista, o falta el registro de auditoría.
- **FR-017**: La Líder UX MUST poder registrar la etiqueta y el módulo definitivos de un caso `[REQUIERE_REVISION_HUMANA]`. MUST NOT registrar la criticidad: el color ya quedó fijado por el conteo.
- **FR-018**: En Guardar el mes cada fila sin decisión MUST mostrar las acciones Se queda y Se va, y MUST NOT mostrar una columna Decisión. Cada acción MUST abrir un modal que pide deseabilidad, factibilidad y viabilidad. Esas tres respuestas son el motivo. Se va MUST NOT guardarse si falta alguna. Se queda MUST registrar las tres y pasar el hallazgo a Tipificados. Se va MUST conservar el hallazgo como `[DESCARTADO-ESTRATÉGICO]`, sin borrarlo, y MUST pasarlo a Excluidos. El comando `decidir` MUST registrar la misma decisión y los mismos tres campos. En Tipificados, Backlog y Excluidos el ojo MUST mostrar el resultado y los tres campos junto a los comentarios, sin cambiar el ancho de las demás columnas.
- **FR-019**: Un hallazgo rechazado que vuelva a aparecer en los dos ciclos mensuales siguientes MUST presentarse en el segundo de esos ciclos con la marca `[REINCIDENTE]`.
- **FR-020**: La corrida mensual MUST NOT crear ni modificar tickets. La página de consulta MAY crear issues en Jira, de uno o de varios, solo para hallazgos que se quedan y tienen etiqueta oficial. MUST NOT enviar un caso sin decidir, rechazado o sin esa etiqueta. El token de Jira MUST vivir en el entorno y MUST NOT guardarse en el repositorio.
- **FR-021**: El porcentaje de un hallazgo MUST ser su conteo dividido por el total de preguntas abiertas del mes que entran a tipificación, multiplicado por 100. Ese total MUST excluir ruido, filas B2C y fechas fuera del mes. Hasta el 20 % inclusive el color MUST ser verde. Más del 20 % y hasta el 50 % inclusive MUST ser amarillo. Más del 50 % MUST ser rojo. El ciclo MUST NOT aceptar un valor manual de criticidad.
- **FR-022**: El día 1 de cada mes, a las 06:00, el ciclo MUST iniciar con el libro del mes que acaba de cerrar, si ese libro ya está disponible y es válido.
- **FR-023**: La Líder UX MUST poder iniciar a mano la corrida de un libro mensual y MUST poder apagar el ciclo. El apagado MUST retirar el reporte de la bandeja del comité y MUST mantener cerrada la autorización de tickets.
- **FR-024**: Cada corrida MUST incluir una muestra reproducible del 10 % de los puntajes usados en CSAT y CES, para que UX o Datos los recalculen. El mismo libro MUST producir la misma muestra.
- **FR-025**: La tasa de finalización MUST ser el número de respuestas con etiqueta y módulo oficiales y con `correccion_lider` en falso, dividido por las preguntas abiertas del mes que entran a tipificación. Ese denominador MUST excluir ruido, filas B2C y fechas fuera del mes. Mientras esa tasa no supere el 85 %, `listo_para_comite` MUST permanecer en falso y la Líder UX MUST revisar el reporte completo antes de llevarlo al comité. Cerrar la cola humana MUST NOT encender `listo_para_comite`.
- **FR-026**: La Líder UX MUST poder guardar las respuestas de un mes en `feedback_response_YYYY-MM.xlsx` sin modificar los libros de los otros meses. La corrida de ese mes MUST seguir dejando ese libro sin cambios.
- **FR-027**: La consulta MUST mostrar, arriba de las pestañas, el valor y la n de cada métrica en cada periodo ya corrido, y el total de esos periodos. El filtro MUST permitir mes, trimestre o semestre, y el encabezado MUST nombrar los meses que cubre. Las columnas son los periodos y las filas son las tres áreas. El CSAT de esa tabla MUST mostrarse como porcentaje de 5. El CES MUST quedarse en la escala de 1 a 5. CSAT 2 MUST NOT aparecer en esa tabla. El total de cada métrica MUST ser la suma de sus valores multiplicados por su n, dividida por la suma de esas n. Una métrica con n = 0 no entra en esa división y se muestra como sin dato en su mes.
- **FR-028**: La consulta MUST separar cuatro vistas. Guardar el mes es la primera pestaña, abre sola y lista los incidentes del mes elegido que no tienen decisión; el título MUST nombrar ese mes. Tipificados lista los que se quedan y no tienen clave en `jira.json`, con o sin etiqueta oficial. Excluidos lista solo los que se van. Backlog lista los que se quedan y ya tienen clave. Un caso sin decidir MUST NOT aparecer en Tipificados, Excluidos ni Backlog. El orden de las listas MUST ser rojo, amarillo, verde y, dentro del mismo color, el mes más reciente.
- **FR-029**: La consulta MUST NOT clasificar quejas y MUST NOT enviar avisos. Enviar a Jira MUST verse solo en Tipificados, a la derecha, y MUST permanecer deshabilitado hasta que haya al menos un caso marcado. MAY crear en Jira los hallazgos que se quedan y tienen etiqueta oficial, uno o varios, según FR-020. Si el envío sale bien, la página MUST abrir Backlog.
- **FR-030**: En Guardar el mes, Tipificados, Backlog y Excluidos, la fila MUST mostrar la síntesis y MUST permitir ver la lista de comentarios anonimizados que la originaron, uno por fila del grupo, aunque el texto no sea idéntico. En Guardar el mes esa lista MUST abrirse como una fila de la misma tabla, titulada Hallazgos, y MUST cerrarse con otro clic. La lista MUST crecer con la cantidad de comentarios. Abrirla MUST NOT llamar al modelo. MUST NOT dejar esa lista solo en el reporte.

### Key Entities *(include if feature involves data)*

- **Lote mensual**: El libro de un solo mes. Se identifica por año y mes. Contiene tres pestañas de respuestas. La captura puede guardar filas en ese libro. La corrida no lo modifica.
- **Total acumulado**: CSAT, CES y CSAT 2 reunidos de los meses que ya tienen reporte, ponderados por su tamaño de muestra.
- **Cuatro listas de la consulta**: Guardar el mes conserva lo que no tiene decisión. Tipificados conserva lo que se queda y aún no tiene clave de Jira. Excluidos conserva lo que se va. Backlog conserva lo que se queda y ya tiene clave. Cada fila guarda la síntesis y los comentarios que la originaron.
- **Respuesta**: Una fila con fecha, puntajes y pregunta abierta. Puede aportar métricas, un hallazgo, ambos o ninguno, según tenga puntajes válidos y texto útil.
- **Métrica mensual**: CSAT, CES o CSAT 2 de una pestaña, con valor calculado, tamaño de muestra y alertas de calidad.
- **Hallazgo**: Una fricción agrupada una sola vez en el mes, con módulo, etiqueta, color de criticidad (`verde`, `amarillo` o `rojo`), síntesis, conteo, porcentaje, confianza y estado de revisión. Aceptarlo o rechazarlo sigue siendo una decisión manual del comité.
- **Registro de auditoría**: La evidencia de un hallazgo: texto anonimizado, sentimiento y justificación. Sin este registro el hallazgo no puede avanzar hacia una autorización de ticket.
- **Decisión del comité**: Aceptación o rechazo de un hallazgo, con el criterio de deseabilidad, factibilidad y viabilidad. El rechazo permanece en la memoria del ciclo.
- **Aviso operativo**: El correo a la Líder UX cuando la entrada o la salida impiden un reporte oficial.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Con el libro del mes ya disponible, la Líder UX tiene la tabla de métricas y la lista tipificada en menos de 3 minutos desde el inicio de la corrida.
- **SC-002**: Al menos el 85 % de los comentarios cualitativos del mes quedan con la etiqueta y el módulo correctos sin que la Líder UX los cambie.
- **SC-003**: Cada corrida mensual se mantiene dentro de 3 USD de costo de modelo y de 30 minutos de supervisión humana antes del comité.
- **SC-004**: El 100 % de los hallazgos clasificados que llegan al comité tienen comentario anonimizado, sentimiento y justificación.
- **SC-005**: El 100 % de las corridas mensuales terminan con cero tickets creados o modificados. Un issue de Jira solo aparece cuando la Líder UX lo envía desde la página, y solo si el hallazgo se queda y tiene etiqueta oficial.
- **SC-006**: El 100 % de las entradas inválidas y de las salidas que fallan dos veces generan un aviso a la Líder UX y ningún reporte marcado como oficial.
- **SC-007**: En una revisión del reporte entregado, ningún correo, teléfono o documento de identidad del texto original permanece visible.
- **SC-008**: La muestra del 10 % de puntajes permite a una persona recalcular CSAT y CES y obtener los mismos promedios que el reporte para esa muestra.
- **SC-009**: Después de guardar un mes, la Líder UX vuelve a abrirlo y encuentra las mismas filas, y los archivos de los otros meses siguen iguales.
- **SC-010**: Con dos meses ya corridos, el total mostrado coincide con el promedio ponderado recalculado a mano a partir de los dos reportes. Tipificados incluye los que se quedan y aún no tienen clave de Jira. Backlog incluye los que ya tienen clave. Excluidos incluye los que se van. Un caso sin decidir no entra en esas tres listas. En Guardar el mes esa lista se abre como fila de la tabla, titulada Hallazgos, con cada frase aunque no sea idéntica. En las otras tres vistas el ojo muestra la lista junto con la decisión.

## Assumptions

- El denominador de cada tasa es el libro del mes en curso. Las cifras históricas de 350 registros y de 3,907 filas no se usan para aprobar ni rechazar una corrida.
- Los libros de julio, agosto y septiembre en `datos/meses/` son ficticios y sirven para probar el ciclo. El libro confidencial de trabajo queda fuera del repositorio.
- CSAT, CSAT 2 y CES usan la escala de 1 a 5 de la plantilla acordada.
- Si el libro no trae una columna de tipo de usuario, todas sus filas se tratan como B2B. Si una fila indica B2C, se excluye antes de calcular y de tipificar.
- La pestaña de origen no decide sola el módulo del hallazgo. La clasificación usa la lista oficial de módulos, que es más específica que las tres pestañas.
- El correo de aviso llega a la Líder UX. La dirección concreta se configura al preparar la operación y no forma parte de esta especificación.
- "El mes que acaba de cerrar" el día 1 es el mes calendario anterior.
- Aceptar un hallazgo registra la decisión del comité y lo pasa a Tipificados. Rechazarlo lo pasa a Excluidos. Crear el issue lo pasa a Backlog. Desde el 2026-10-27 la página puede abrir el issue de Jira de los que se quedan y tienen etiqueta oficial. La corrida mensual no lo abre sola. Enviar a Jira solo se ve en Tipificados.
- El agrupado por parecido usa embeddings y el umbral `MODEL_EMBEDDING_UMBRAL`, 0,85 si no se indica otro. Sin `MODEL_EMBEDDING_NAME` no hay esa llamada. NotebookLM no forma parte del ciclo. El plan Plus de Gemini y la suscripción de Cursor no entregan esa clave. La corrida de esta máquina usa la API de Gemini en el nivel gratuito de AI Studio: `MODEL_BASE_URL` es `https://generativelanguage.googleapis.com/v1beta/openai` y `MODEL_EMBEDDING_NAME` es `gemini-embedding-001`. La clave vive en `.env` y no entra al repositorio.
- Los libros ficticios de julio, agosto y septiembre traen, para cada dolor repetido, frases parecidas y no idénticas. El ojo muestra esas frases tal como quedaron en el Excel. Un comentario que aparece una sola vez sigue en una sola línea.
- La Líder UX revisa el reporte completo antes del comité hasta que la tasa de finalización se sostenga por encima del 85 %.
- El total y el histórico leen las salidas ya generadas. No vuelven a calcular un mes que no se ha corrido.
- La pantalla de consulta es local y de una sola persona. No reemplaza el comando que arma el reporte.
