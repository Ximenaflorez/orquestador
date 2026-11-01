"""Guarda las respuestas de un solo mes."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook, load_workbook

from orquestador.ingesta import EntradaInvalida, mes_del_nombre
from orquestador.modelos import NOMBRES_PESTANA

HOJAS = {
    "creacion": ["DATE", "CSAT", "CES", "PREGUNTA ABIERTA"],
    "catalogo": ["DATE", "CSAT", "CSAT 2", "CES", "PREGUNTA ABIERTA"],
    "gestion": ["DATE", "CSAT", "CES", "PREGUNTA ABIERTA"],
}


class CapturaInvalida(Exception):
    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def ruta_mes(raiz: Path, mes: str) -> Path:
    _validar_mes(mes)
    return raiz / "datos" / "meses" / f"feedback_response_{mes}.xlsx"


def recibir_libro(raiz: Path, nombre: str, contenido: bytes) -> str:
    try:
        mes = mes_del_nombre(Path(nombre))
    except EntradaInvalida as exc:
        raise CapturaInvalida(exc.motivo) from exc
    if not contenido:
        raise CapturaInvalida("El archivo está vacío.")
    try:
        libro = load_workbook(BytesIO(contenido), read_only=True, data_only=True)
    except Exception as exc:
        raise CapturaInvalida("El archivo no es un Excel válido.") from exc
    try:
        nombres = set(libro.sheetnames)
        faltan = [titulo for titulo in NOMBRES_PESTANA.values() if titulo not in nombres]
        if faltan:
            raise CapturaInvalida("Falta una pestaña obligatoria: " + ", ".join(faltan))
        for clave, titulo in NOMBRES_PESTANA.items():
            filas = libro[titulo].iter_rows(max_row=1, values_only=True)
            encabezados = {str(celda).strip().lower() for celda in next(filas, ()) if celda not in (None, "")}
            ausentes = [columna for columna in HOJAS[clave] if columna.lower() not in encabezados]
            if ausentes:
                raise CapturaInvalida(f"La pestaña {titulo} no trae: " + ", ".join(ausentes))
    finally:
        libro.close()
    destino = ruta_mes(raiz, mes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return mes


def plantilla() -> bytes:
    libro = Workbook()
    primera = True
    ejemplos = {
        "creacion": (datetime(2026, 1, 15), 4, 3, "El formulario no conserva el borrador."),
        "catalogo": (datetime(2026, 1, 15), 5, 4, 3, "El filtro no conserva la selección."),
        "gestion": (datetime(2026, 1, 15), 3, 2, "No distingo cuáles vacantes siguen abiertas."),
    }
    for clave, titulo in NOMBRES_PESTANA.items():
        hoja = libro.active if primera else libro.create_sheet(titulo)
        hoja.title = titulo
        primera = False
        hoja.append(HOJAS[clave])
        hoja.append(ejemplos[clave])
    buffer = BytesIO()
    libro.save(buffer)
    libro.close()
    return buffer.getvalue()


def guardar(raiz: Path, mes: str, filas: list[dict]) -> Path:
    destino = ruta_mes(raiz, mes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    libro = Workbook()
    primera = True
    for clave, titulo in NOMBRES_PESTANA.items():
        hoja = libro.active if primera else libro.create_sheet(titulo)
        hoja.title = titulo
        primera = False
        encabezados = HOJAS[clave]
        hoja.append(encabezados)
        for fila in filas:
            if fila.get("pestana") != clave:
                continue
            hoja.append(_valores(mes, fila, "CSAT 2" in encabezados))
    libro.save(destino)
    libro.close()
    return destino


def _validar_mes(mes: str) -> None:
    try:
        datetime.strptime(mes, "%Y-%m")
    except ValueError as exc:
        raise CapturaInvalida("El mes debe tener la forma YYYY-MM.") from exc


def _valores(mes: str, fila: dict, incluye_csat_2: bool) -> tuple:
    fecha = _fecha(mes, str(fila.get("fecha") or ""))
    csat = _puntaje(fila.get("csat"), "CSAT")
    ces = _puntaje(fila.get("ces"), "CES")
    pregunta = str(fila.get("pregunta") or "").strip()
    if incluye_csat_2:
        return fecha, csat, _puntaje(fila.get("csat_2"), "CSAT 2"), ces, pregunta
    return fecha, csat, ces, pregunta


def _fecha(mes: str, texto: str) -> datetime:
    crudo = texto.strip()
    if not crudo:
        raise CapturaInvalida("Cada fila necesita una fecha.")
    try:
        momento = datetime.fromisoformat(crudo)
    except ValueError as exc:
        raise CapturaInvalida("La fecha no es válida.") from exc
    if momento.strftime("%Y-%m") != mes:
        raise CapturaInvalida("La fecha tiene que caer dentro del mes que se guarda.")
    return momento


def _puntaje(valor, nombre: str) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise CapturaInvalida(f"{nombre} debe ser un entero del 1 al 5.") from exc
    if not 1 <= numero <= 5:
        raise CapturaInvalida(f"{nombre} debe ser un entero del 1 al 5.")
    return numero
