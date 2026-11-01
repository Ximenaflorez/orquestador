"""Escribe el reporte mensual y sus archivos de apoyo."""

from __future__ import annotations

import json
from pathlib import Path

from orquestador.modelos import NOMBRES_PESTANA, Alerta, Corrida, Hallazgo, MetricaMensual

SECCIONES = (
    "Resumen de KPIs mensuales",
    "Alertas de calidad de datos",
    "Quejas tipificadas",
    "Revisión humana",
    "Muestra para auditoría numérica",
)


def escribir(
    raiz: Path,
    corrida: Corrida,
    metricas: list[MetricaMensual],
    alertas: list[Alerta],
    hallazgos: list[Hallazgo],
    muestra: list[dict],
) -> None:
    carpeta = raiz / "salidas" / corrida.mes
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "reporte.md").write_text(_markdown(corrida.mes, metricas, alertas, hallazgos, muestra), encoding="utf-8")
    (carpeta / "metricas.json").write_text(_json([item.model_dump() for item in metricas]), encoding="utf-8")
    (carpeta / "estado.json").write_text(_json(corrida.model_dump(mode="json")), encoding="utf-8")
    (carpeta / "muestra-auditoria.json").write_text(
        _json({"mes": corrida.mes, "items": muestra}),
        encoding="utf-8",
    )
    (carpeta / "revision.json").write_text(_json(_revision(hallazgos)), encoding="utf-8")
    (carpeta / "decisiones.json").write_text("[]\n", encoding="utf-8")
    lineas = [_json_linea(_auditoria(hallazgo)) for hallazgo in hallazgos]
    (carpeta / "auditoria.jsonl").write_text("\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")


def escribir_estado(raiz: Path, corrida: Corrida) -> None:
    carpeta = raiz / "salidas" / corrida.mes
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "estado.json").write_text(_json(corrida.model_dump(mode="json")), encoding="utf-8")


def _markdown(mes, metricas, alertas, hallazgos, muestra) -> str:
    clasificados = [item for item in hallazgos if item.estado == "clasificado"]
    revision = [item for item in hallazgos if item.estado == "requiere_revision"]
    filas = ["| Métrica | Valor calculado | Tamaño de muestra (n) |", "| --- | --- | --- |"]
    for metrica in metricas:
        valor = "sin dato" if metrica.valor is None else f"{metrica.valor:.2f}"
        filas.append(f"| {NOMBRES_PESTANA[metrica.pestana]} · {metrica.nombre} | {valor} | {metrica.n} |")
    alertas_md = "\n".join(f"- {alerta.tipo}: {alerta.cantidad}" for alerta in alertas)
    if clasificados:
        quejas = "\n".join(
            f"- {item.modulo} {item.etiqueta} {item.criticidad}. {item.sintesis} Conteo: {item.conteo}. Porcentaje: {_porcentaje(item)}."
            for item in clasificados
        )
    else:
        quejas = "Ningún hallazgo quedó clasificado."
    if revision:
        humanos = "\n".join(
            f"- [REQUIERE_REVISION_HUMANA] {item.id}: {item.comentario} Motivo: {item.motivo} Color: {item.criticidad}. Conteo: {item.conteo}. Porcentaje: {_porcentaje(item)}."
            for item in revision
        )
    else:
        humanos = "No hay casos en revisión."
    if muestra:
        muestra_md = "\n".join(
            f"- {item['respuesta_id']} · {item['puntaje']} · {item['valor']}" for item in muestra
        )
    else:
        muestra_md = "No hay puntajes en la muestra."
    return (
        f"# Reporte {mes}\n\n"
        f"## {SECCIONES[0]}\n\n" + "\n".join(filas) + "\n\n"
        f"## {SECCIONES[1]}\n\n{alertas_md}\n\n"
        f"## {SECCIONES[2]}\n\n{quejas}\n\n"
        f"## {SECCIONES[3]}\n\n{humanos}\n\n"
        f"## {SECCIONES[4]}\n\n{muestra_md}\n"
    )


def _auditoria(hallazgo: Hallazgo) -> dict:
    return {
        "hallazgo_id": hallazgo.id,
        "mes": hallazgo.mes,
        "comentario_anonimizado": hallazgo.comentario,
        "sentimiento": hallazgo.sentimiento,
        "intensidad": hallazgo.intensidad,
        "justificacion": hallazgo.motivo,
        "modulo": hallazgo.modulo,
        "etiqueta": hallazgo.etiqueta,
        "confianza": hallazgo.confianza,
        "criticidad": hallazgo.criticidad,
        "sintesis": hallazgo.sintesis,
        "conteo": hallazgo.conteo,
        "porcentaje": hallazgo.porcentaje,
        "comentarios": hallazgo.comentarios,
    }


def _porcentaje(hallazgo: Hallazgo) -> str:
    if hallazgo.porcentaje is None:
        return "sin dato"
    return f"{hallazgo.porcentaje:.2f}"


def _revision(hallazgos: list[Hallazgo]) -> list[dict]:
    return [
        {
            "id": item.id,
            "pregunta_anonimizada": item.comentario,
            "motivo": item.motivo,
            "pestaña": ",".join(item.pestanas),
        }
        for item in hallazgos
        if item.estado == "requiere_revision"
    ]


def _json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False, indent=2) + "\n"


def _json_linea(valor) -> str:
    return json.dumps(valor, ensure_ascii=False)
