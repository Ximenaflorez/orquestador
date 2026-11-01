"""Muestra reproducible del 10 % de los puntajes usados en los promedios."""

from __future__ import annotations

import math

from orquestador.modelos import Respuesta


def seleccionar(respuestas: list[Respuesta]) -> list[dict]:
    usados: list[dict] = []
    for respuesta in respuestas:
        if respuesta.fuera_de_mes or respuesta.es_b2c:
            continue
        pares = [("CSAT", respuesta.csat), ("CES", respuesta.ces)]
        if respuesta.pestana == "catalogo":
            pares.append(("CSAT 2", respuesta.csat_2))
        for nombre, valor in pares:
            if valor is None:
                continue
            usados.append(
                {
                    "respuesta_id": respuesta.id,
                    "pestaña": respuesta.pestana,
                    "puntaje": nombre,
                    "valor": valor,
                }
            )
    usados.sort(key=lambda item: (item["respuesta_id"], item["puntaje"]))
    if not usados:
        return []
    cantidad = max(1, math.ceil(len(usados) * 0.1))
    return usados[:cantidad]
