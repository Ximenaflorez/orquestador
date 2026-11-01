"""Total ponderado e histórico de los meses ya corridos."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from orquestador.modelos import ETIQUETAS, MODULOS

_MES = re.compile(r"\d{4}-\d{2}")


def resumir(raiz: Path) -> dict:
    totales: dict[tuple[str, str], list[tuple[float, int]]] = {}
    historico: list[dict] = []
    excluidos: list[dict] = []
    backlog: list[dict] = []
    por_mes: list[dict] = []
    meses: list[str] = []
    carpeta = raiz / "salidas"
    if not carpeta.is_dir():
        return {"meses": [], "por_mes": [], "totales": [], "historico": [], "excluidos": [], "backlog": []}
    for mes_dir in sorted(ruta for ruta in carpeta.iterdir() if ruta.is_dir() and _MES.fullmatch(ruta.name)):
        metricas = mes_dir / "metricas.json"
        if not metricas.is_file():
            continue
        meses.append(mes_dir.name)
        for item in json.loads(metricas.read_text(encoding="utf-8")):
            n = int(item.get("n") or 0)
            valor = item.get("valor")
            por_mes.append(
                {
                    "mes": mes_dir.name,
                    "pestana": item["pestana"],
                    "nombre": item["nombre"],
                    "valor": None if n <= 0 or valor is None else round(float(valor), 2),
                    "n": n,
                }
            )
            if n <= 0 or valor is None:
                continue
            clave = (item["pestana"], item["nombre"])
            totales.setdefault(clave, []).append((float(valor), n))
        auditoria = mes_dir / "auditoria.jsonl"
        if not auditoria.is_file():
            continue
        decisiones = _leer_decisiones(mes_dir / "decisiones.json")
        decisiones_por_id = {item.get("hallazgo_id"): item for item in decisiones}
        for linea in auditoria.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            hallazgo = json.loads(linea)
            identificador = hallazgo.get("hallazgo_id")
            decision = decisiones_por_id.get(identificador) or {}
            fila = {
                "mes": hallazgo.get("mes") or mes_dir.name,
                "modulo": hallazgo.get("modulo"),
                "etiqueta": hallazgo.get("etiqueta"),
                "criticidad": hallazgo.get("criticidad"),
                "sintesis": hallazgo.get("sintesis") or hallazgo.get("comentario_anonimizado") or "",
                "conteo": hallazgo.get("conteo"),
                "comentarios": _comentarios(hallazgo),
                "resultado": decision.get("resultado"),
                "motivo": decision.get("motivo") or "",
            }
            if fila["resultado"] == "rechazado":
                excluidos.append(fila)
                continue
            if fila["resultado"] != "aceptado":
                continue
            fila["id"] = identificador
            fila["jira"] = _jira_de(mes_dir, identificador)
            if fila["jira"]:
                backlog.append(fila)
            else:
                historico.append(fila)
    return {
        "meses": meses,
        "por_mes": por_mes,
        "totales": [_total(clave, partes) for clave, partes in totales.items()],
        "historico": historico,
        "excluidos": excluidos,
        "backlog": backlog,
    }


class DecisionInvalida(Exception):
    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def incidentes(raiz: Path, mes: str) -> list[dict]:
    carpeta = raiz / "salidas" / mes
    auditoria = carpeta / "auditoria.jsonl"
    if not auditoria.is_file():
        return []
    tomadas = {item.get("hallazgo_id"): item for item in _leer_decisiones(carpeta / "decisiones.json")}
    salida: list[dict] = []
    for linea in auditoria.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        hallazgo = json.loads(linea)
        decision = tomadas.get(hallazgo.get("hallazgo_id")) or {}
        salida.append(
            {
                "id": hallazgo.get("hallazgo_id"),
                "mes": hallazgo.get("mes") or mes,
                "comentario": hallazgo.get("comentario_anonimizado") or "",
                "sintesis": hallazgo.get("sintesis") or "",
                "comentarios": _comentarios(hallazgo),
                "criticidad": hallazgo.get("criticidad"),
                "porcentaje": hallazgo.get("porcentaje"),
                "conteo": hallazgo.get("conteo") or 0,
                "etiqueta": hallazgo.get("etiqueta"),
                "modulo": hallazgo.get("modulo"),
                "resultado": decision.get("resultado"),
                "motivo": decision.get("motivo") or "",
            }
        )
    salida.sort(key=lambda item: (-int(item["conteo"]), item["comentario"]))
    return salida


def decidir(
    raiz: Path,
    mes: str,
    hallazgo_id: str,
    resultado: str,
    motivo: str,
    *,
    sintesis: str | None = None,
    modulo: str | None = None,
    etiqueta: str | None = None,
) -> None:
    if not _MES.fullmatch(mes or ""):
        raise DecisionInvalida("El mes no es válido.")
    if resultado not in ("aceptado", "rechazado"):
        raise DecisionInvalida("La decisión es se queda o se va.")
    texto = (motivo or "").strip()
    if resultado == "rechazado" and not texto:
        raise DecisionInvalida("Si se va, escribe por qué.")
    carpeta = raiz / "salidas" / mes
    auditoria = carpeta / "auditoria.jsonl"
    if not auditoria.is_file():
        raise DecisionInvalida("Ese mes no tiene incidentes.")
    crudas = [linea for linea in auditoria.read_text(encoding="utf-8").splitlines() if linea.strip()]
    registros = [json.loads(linea) for linea in crudas]
    if hallazgo_id not in {item.get("hallazgo_id") for item in registros}:
        raise DecisionInvalida("Ese incidente no está en el mes.")
    if sintesis is not None or modulo is not None or etiqueta is not None:
        corregidas = [
            _corregir_hallazgo(item, sintesis, modulo, etiqueta) if item.get("hallazgo_id") == hallazgo_id else linea
            for item, linea in zip(registros, crudas, strict=True)
        ]
        auditoria.write_text("\n".join(corregidas) + "\n", encoding="utf-8")
    ruta = carpeta / "decisiones.json"
    actuales = [item for item in _leer_decisiones(ruta) if item.get("hallazgo_id") != hallazgo_id]
    actuales.append(
        {
            "hallazgo_id": hallazgo_id,
            "resultado": resultado,
            "motivo": texto,
            "deseabilidad": texto,
            "factibilidad": texto,
            "viabilidad": texto,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "actores": "Líder UX, Product Owner y Líder de Célula",
        }
    )
    ruta.write_text(json.dumps(actuales, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _corregir_hallazgo(hallazgo: dict, sintesis: str | None, modulo: str | None, etiqueta: str | None) -> str:
    cambio = False
    if sintesis is not None:
        lineas = [linea.strip() for linea in sintesis.splitlines() if linea.strip()]
        if not lineas:
            raise DecisionInvalida("Escribe la síntesis.")
        if len(lineas) > 2:
            raise DecisionInvalida("La síntesis tiene como máximo dos líneas.")
        hallazgo["sintesis"] = "\n".join(lineas)
    if modulo is not None:
        valor = modulo.strip() or None
        if valor is not None and valor not in MODULOS:
            raise DecisionInvalida("El módulo no está en la lista oficial.")
        cambio = cambio or hallazgo.get("modulo") != valor
        hallazgo["modulo"] = valor
    if etiqueta is not None:
        valor = etiqueta.strip() or None
        if valor is not None and valor not in ETIQUETAS:
            raise DecisionInvalida("La etiqueta no está en la lista oficial.")
        cambio = cambio or hallazgo.get("etiqueta") != valor
        hallazgo["etiqueta"] = valor
    if cambio:
        hallazgo["correccion_lider"] = True
    return json.dumps(hallazgo, ensure_ascii=False)


def _comentarios(hallazgo: dict) -> list[str]:
    crudos = hallazgo.get("comentarios")
    if isinstance(crudos, list):
        textos = [str(item).strip() for item in crudos if str(item).strip()]
        if textos:
            return textos
    uno = (hallazgo.get("comentario_anonimizado") or hallazgo.get("sintesis") or "").strip()
    return [uno] if uno else []


def _jira_de(mes_dir: Path, hallazgo_id: str | None) -> dict | None:
    if not hallazgo_id:
        return None
    for item in _leer_decisiones(mes_dir / "jira.json"):
        if item.get("hallazgo_id") == hallazgo_id and item.get("clave"):
            return {"clave": item.get("clave"), "url": item.get("url") or ""}
    return None


def _leer_decisiones(ruta: Path) -> list[dict]:
    if not ruta.is_file():
        return []
    valor = json.loads(ruta.read_text(encoding="utf-8"))
    return valor if isinstance(valor, list) else []


def _total(clave: tuple[str, str], partes: list[tuple[float, int]]) -> dict:
    peso = sum(n for _, n in partes)
    valor = round(sum(numero * n for numero, n in partes) / peso, 2)
    return {"pestana": clave[0], "nombre": clave[1], "valor": valor, "n": peso}
