"""Crea en Jira los hallazgos que se quedan. El token no se guarda."""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from orquestador.modelos import ETIQUETAS

_MES = re.compile(r"\d{4}-\d{2}")


class JiraInvalida(Exception):
    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


@dataclass(frozen=True)
class AjustesJira:
    base: str
    correo: str
    token: str
    proyecto: str
    tipo: str


def leer_ajustes() -> AjustesJira:
    def leer(nombre: str) -> str:
        return os.environ.get(nombre, "").strip()

    base = leer("JIRA_BASE_URL").rstrip("/")
    correo = leer("JIRA_EMAIL")
    token = leer("JIRA_API_TOKEN")
    proyecto = leer("JIRA_PROJECT")
    tipo = leer("JIRA_ISSUE_TYPE") or "Task"
    faltan = [
        nombre
        for nombre, valor in (
            ("JIRA_BASE_URL", base),
            ("JIRA_EMAIL", correo),
            ("JIRA_API_TOKEN", token),
            ("JIRA_PROJECT", proyecto),
        )
        if not valor
    ]
    if faltan:
        raise JiraInvalida("Falta configurar Jira: " + ", ".join(faltan) + ".")
    if not base.startswith("https://"):
        raise JiraInvalida("JIRA_BASE_URL tiene que empezar por https://.")
    return AjustesJira(base, correo, token, proyecto, tipo)


def enviar(raiz: Path, items: list[dict], crear=None) -> dict:
    if not isinstance(items, list) or not items:
        raise JiraInvalida("Selecciona al menos un caso que se queda.")
    ajustes = leer_ajustes()
    crear = crear or _crear_http
    vistos: set[tuple[str, str]] = set()
    creados: list[dict] = []
    errores: list[dict] = []
    for crudo in items:
        mes = str((crudo or {}).get("mes") or "")
        identificador = str((crudo or {}).get("id") or "")
        if (mes, identificador) in vistos:
            continue
        vistos.add((mes, identificador))
        try:
            creados.append(_uno(raiz, mes, identificador, ajustes, crear))
        except JiraInvalida as exc:
            errores.append({"mes": mes, "id": identificador, "error": exc.motivo})
    return {"ok": not errores, "creados": creados, "errores": errores}


def _uno(raiz: Path, mes: str, identificador: str, ajustes: AjustesJira, crear) -> dict:
    if not _MES.fullmatch(mes) or not identificador:
        raise JiraInvalida("El caso no es válido.")
    carpeta = raiz / "salidas" / mes
    hallazgo = _hallazgo(carpeta / "auditoria.jsonl", identificador)
    if hallazgo is None:
        raise JiraInvalida("Ese caso no está en el mes.")
    if hallazgo.get("etiqueta") not in ETIQUETAS:
        raise JiraInvalida("Solo se envía un caso con etiqueta oficial que se queda.")
    decision = _decision(carpeta / "decisiones.json", identificador)
    if decision.get("resultado") != "aceptado":
        raise JiraInvalida("Solo se envían a Jira los que se quedan.")
    previa = _clave_guardada(carpeta / "jira.json", identificador)
    if previa:
        return {"mes": mes, "id": identificador, "clave": previa["clave"], "url": previa.get("url") or ""}
    creado = crear(ajustes, _resumen(hallazgo), _descripcion(hallazgo, decision))
    clave = str(creado.get("clave") or "")
    url = str(creado.get("url") or "")
    if not clave:
        raise JiraInvalida("Jira no devolvió la clave del ticket.")
    _guardar(carpeta / "jira.json", identificador, clave, url)
    return {"mes": mes, "id": identificador, "clave": clave, "url": url}


def _hallazgo(ruta: Path, identificador: str) -> dict | None:
    if not ruta.is_file():
        return None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        hallazgo = json.loads(linea)
        if hallazgo.get("hallazgo_id") == identificador:
            return hallazgo
    return None


def _decision(ruta: Path, identificador: str) -> dict:
    for item in _leer(ruta):
        if item.get("hallazgo_id") == identificador:
            return item
    return {}


def _clave_guardada(ruta: Path, identificador: str) -> dict | None:
    for item in _leer(ruta):
        if item.get("hallazgo_id") == identificador and item.get("clave"):
            return item
    return None


def _guardar(ruta: Path, identificador: str, clave: str, url: str) -> None:
    actuales = [item for item in _leer(ruta) if item.get("hallazgo_id") != identificador]
    actuales.append(
        {
            "hallazgo_id": identificador,
            "clave": clave,
            "url": url,
            "fecha": datetime.now().isoformat(timespec="seconds"),
        }
    )
    ruta.write_text(json.dumps(actuales, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _leer(ruta: Path) -> list[dict]:
    if not ruta.is_file():
        return []
    valor = json.loads(ruta.read_text(encoding="utf-8"))
    return valor if isinstance(valor, list) else []


def _resumen(hallazgo: dict) -> str:
    sintesis = (hallazgo.get("sintesis") or hallazgo.get("comentario_anonimizado") or "Hallazgo UX").replace("\n", " ").strip()
    texto = f"{hallazgo.get('etiqueta') or ''} {hallazgo.get('modulo') or ''}: {sintesis}".strip()
    if len(texto) <= 255:
        return texto
    return texto[:252] + "..."


def _descripcion(hallazgo: dict, decision: dict) -> str:
    lineas = [
        f"Mes: {hallazgo.get('mes') or ''}",
        f"Módulo: {hallazgo.get('modulo') or ''}",
        f"Etiqueta: {hallazgo.get('etiqueta') or ''}",
        f"Criticidad: {hallazgo.get('criticidad') or ''}",
        f"Conteo: {hallazgo.get('conteo') if hallazgo.get('conteo') is not None else ''}",
        f"Síntesis: {hallazgo.get('sintesis') or hallazgo.get('comentario_anonimizado') or ''}",
        "Decisión: Se queda",
    ]
    motivo = str(decision.get("motivo") or "").strip()
    if motivo:
        lineas.append(f"Por qué: {motivo}")
    return "\n".join(lineas)


def _adf(texto: str) -> dict:
    contenido = [
        {"type": "paragraph", "content": [{"type": "text", "text": linea}]}
        for linea in texto.split("\n")
        if linea
    ]
    return {"type": "doc", "version": 1, "content": contenido or [{"type": "paragraph", "content": []}]}


def _crear_http(ajustes: AjustesJira, resumen: str, descripcion: str) -> dict:
    url = ajustes.base + "/rest/api/3/issue"
    cuerpo = json.dumps(
        {
            "fields": {
                "project": {"key": ajustes.proyecto},
                "summary": resumen,
                "issuetype": {"name": ajustes.tipo},
                "description": _adf(descripcion),
            }
        }
    ).encode("utf-8")
    credencial = base64.b64encode(f"{ajustes.correo}:{ajustes.token}".encode()).decode()
    solicitud = urllib.request.Request(
        url,
        data=cuerpo,
        method="POST",
        headers={
            "Authorization": f"Basic {credencial}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    abridor = urllib.request.build_opener(_SinRedireccion)
    try:
        with abridor.open(solicitud, timeout=30) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", "replace")[:300]
        raise JiraInvalida(f"Jira respondió {exc.code}. {detalle}") from None
    except urllib.error.URLError as exc:
        raise JiraInvalida("No se pudo conectar con Jira.") from exc
    clave = str(datos.get("key") or "")
    if not clave:
        raise JiraInvalida("Jira no devolvió la clave del ticket.")
    return {"clave": clave, "url": f"{ajustes.base}/browse/{clave}"}


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise JiraInvalida("Jira pidió una redirección y no se reenvió el token.")
