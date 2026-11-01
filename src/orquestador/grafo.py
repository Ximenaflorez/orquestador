"""Recorrido ordenado: ingesta, métricas, voz del cliente y reporte."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from orquestador.clasificacion import clasificar
from orquestador.config import Ajustes
from orquestador.ingesta import EntradaInvalida, leer_libro
from orquestador.metricas import calcular
from orquestador.modelos import Corrida, Hallazgo, Respuesta
from orquestador.muestra import seleccionar
from orquestador.reporte import escribir, escribir_estado


class Estado(TypedDict, total=False):
    ruta: str
    mes: str
    respuestas: list[Respuesta]
    ignoradas: int
    metricas: list
    alertas: list
    hallazgos: list[Hallazgo]
    costo: float
    corte_costo: bool
    error: str


def _ingesta(estado: Estado) -> dict:
    try:
        respuestas, ignoradas = leer_libro(Path(estado["ruta"]), estado["mes"])
    except EntradaInvalida as exc:
        return {"error": exc.motivo}
    return {"respuestas": respuestas, "ignoradas": ignoradas}


def _metricas(estado: Estado) -> dict:
    if estado.get("error"):
        return {}
    metricas, alertas = calcular(estado["respuestas"], estado.get("ignoradas", 0))
    for metrica in metricas:
        if not metrica.mes:
            metrica.mes = estado["mes"]
    return {"metricas": metricas, "alertas": alertas}


def _clasificar(estado: Estado, ajustes: Ajustes) -> dict:
    if estado.get("error"):
        return {}
    hallazgos, costo, corte = clasificar(estado["respuestas"], ajustes, estado["mes"])
    return {"hallazgos": hallazgos, "costo": costo, "corte_costo": corte}


def _reporte(estado: Estado) -> dict:
    return {}


def compilar(ajustes: Ajustes):
    grafo = StateGraph(Estado)
    grafo.add_node("ingesta", _ingesta)
    grafo.add_node("metricas", _metricas)
    grafo.add_node("voz", lambda estado: _clasificar(estado, ajustes))
    grafo.add_node("reporte", _reporte)
    grafo.add_edge(START, "ingesta")
    grafo.add_edge("ingesta", "metricas")
    grafo.add_edge("metricas", "voz")
    grafo.add_edge("voz", "reporte")
    grafo.add_edge("reporte", END)
    return grafo.compile()


def ejecutar(ruta: Path, mes: str, raiz: Path, ajustes: Ajustes) -> tuple[Corrida, int]:
    inicio = datetime.now()
    apagado = (raiz / "datos" / "control" / "apagado.flag").is_file()
    resultado = compilar(ajustes).invoke({"ruta": str(ruta), "mes": mes})
    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()
    error = resultado.get("error")
    respuestas = resultado.get("respuestas") or []
    hallazgos = resultado.get("hallazgos") or []
    costo = float(resultado.get("costo") or 0)
    tasa = _tasa(respuestas, hallazgos)
    cola_vacia = not any(item.estado == "requiere_revision" for item in hallazgos)
    oficial = (
        not error
        and not apagado
        and not resultado.get("corte_costo")
        and duracion < 180
        and costo <= 3
        and _auditoria_completa(hallazgos)
    )
    corrida = Corrida(
        mes=mes,
        inicio=inicio,
        fin=fin,
        duracion_segundos=round(duracion, 3),
        costo_usd=round(costo, 6),
        tasa_finalizacion=tasa,
        apagado=apagado,
        oficial=oficial,
        listo_para_comite=oficial and (tasa >= 0.85 or cola_vacia),
    )
    if error:
        escribir_estado(raiz, corrida)
        return corrida, 2
    escribir(
        raiz,
        corrida,
        resultado.get("metricas") or [],
        resultado.get("alertas") or [],
        hallazgos,
        seleccionar(respuestas),
    )
    if oficial:
        return corrida, 0
    return corrida, 3


def _tasa(respuestas: list[Respuesta], hallazgos: list[Hallazgo]) -> float:
    utiles = [
        respuesta.id
        for respuesta in respuestas
        if not respuesta.es_ruido and not respuesta.es_b2c and not respuesta.fuera_de_mes and respuesta.pregunta_abierta.strip()
    ]
    if not utiles:
        return 1.0
    logradas = {
        identificador
        for hallazgo in hallazgos
        if hallazgo.estado == "clasificado" and not hallazgo.correccion_lider
        for identificador in hallazgo.respuestas
    }
    return round(sum(1 for identificador in utiles if identificador in logradas) / len(utiles), 4)


def _auditoria_completa(hallazgos: list[Hallazgo]) -> bool:
    return all(hallazgo.motivo.strip() for hallazgo in hallazgos)
