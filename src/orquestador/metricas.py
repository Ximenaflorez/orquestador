"""Promedios deterministas. No imputa puntajes."""

from __future__ import annotations

from orquestador.modelos import NOMBRES_PESTANA, Alerta, MetricaMensual, Respuesta

TIPOS_ALERTA = (
    "puntaje vacío",
    "puntaje fuera de escala",
    "fecha fuera de mes",
    "fila B2C",
    "pestaña ignorada",
)


def calcular(respuestas: list[Respuesta], filas_ignoradas: int) -> tuple[list[MetricaMensual], list[Alerta]]:
    conteo = {tipo: 0 for tipo in TIPOS_ALERTA}
    conteo["pestaña ignorada"] = filas_ignoradas
    for respuesta in respuestas:
        if respuesta.fuera_de_mes:
            conteo["fecha fuera de mes"] += 1
        if respuesta.es_b2c:
            conteo["fila B2C"] += 1
        for exclusion in respuesta.exclusion_puntaje:
            if "puntaje vacío" in exclusion:
                conteo["puntaje vacío"] += 1
            if "puntaje fuera de escala" in exclusion:
                conteo["puntaje fuera de escala"] += 1
    alertas = [Alerta(tipo=tipo, cantidad=conteo[tipo]) for tipo in TIPOS_ALERTA]
    mes = respuestas[0].mes if respuestas else ""
    metricas: list[MetricaMensual] = []
    for pestana in NOMBRES_PESTANA:
        nombres = ["CSAT", "CES", "CSAT 2"] if pestana == "catalogo" else ["CSAT", "CES"]
        for nombre in nombres:
            valores = [
                valor
                for respuesta in respuestas
                if (valor := _valor_util(respuesta, pestana, nombre)) is not None
            ]
            promedio = round(sum(valores) / len(valores), 2) if valores else None
            metricas.append(
                MetricaMensual(
                    mes=mes,
                    pestana=pestana,
                    nombre=nombre,
                    valor=promedio,
                    n=len(valores),
                    alertas=alertas,
                )
            )
    return metricas, alertas


def _valor_util(respuesta: Respuesta, pestana: str, nombre: str) -> int | None:
    if respuesta.pestana != pestana or respuesta.fuera_de_mes or respuesta.es_b2c:
        return None
    return _valor(respuesta, nombre)


def _valor(respuesta: Respuesta, nombre: str) -> int | None:
    if nombre == "CSAT":
        return respuesta.csat
    if nombre == "CES":
        return respuesta.ces
    return respuesta.csat_2
