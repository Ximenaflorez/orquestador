"""Lee un libro mensual sin modificarlo."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from orquestador.modelos import NOMBRES_PESTANA, Respuesta, es_ruido
from orquestador.privacidad import anonimizar

HOJAS = {nombre: clave for clave, nombre in NOMBRES_PESTANA.items()}
_MES = re.compile(r"feedback_response_(\d{4}-\d{2})\.xlsx$", re.IGNORECASE)
_COLUMNAS_TIPO = {"user_type", "tipo_usuario", "tipo"}


class EntradaInvalida(Exception):
    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def mes_del_nombre(ruta: Path) -> str:
    coincidencia = _MES.search(ruta.name)
    if not coincidencia:
        raise EntradaInvalida("El nombre del archivo no trae el mes YYYY-MM.")
    return coincidencia.group(1)


def leer_libro(ruta: Path, mes: str) -> tuple[list[Respuesta], int]:
    if not ruta.is_file():
        raise EntradaInvalida(f"No está el libro {ruta.name}.")
    libro = load_workbook(ruta, data_only=True, read_only=True)
    try:
        nombres = set(libro.sheetnames)
        faltan = [nombre for nombre in HOJAS if nombre not in nombres]
        if faltan:
            raise EntradaInvalida("Falta una pestaña obligatoria: " + ", ".join(faltan))
        respuestas: list[Respuesta] = []
        ignoradas = 0
        for nombre in libro.sheetnames:
            hoja = libro[nombre]
            filas = hoja.iter_rows(values_only=True)
            try:
                encabezados = next(filas)
            except StopIteration:
                encabezados = ()
            if nombre not in HOJAS:
                ignoradas += sum(1 for fila in filas if any(celda not in (None, "") for celda in fila))
                continue
            columnas = _indice(encabezados)
            for numero, fila in enumerate(filas, start=2):
                if all(celda in (None, "") for celda in fila):
                    continue
                respuestas.append(_respuesta(HOJAS[nombre], numero, fila, columnas, mes))
        if respuestas and all(item.fuera_de_mes for item in respuestas):
            raise EntradaInvalida("Ninguna fecha pertenece al mes del archivo.")
        return respuestas, ignoradas
    finally:
        libro.close()


def _indice(encabezados: tuple) -> dict[str, int]:
    indice: dict[str, int] = {}
    for posicion, encabezado in enumerate(encabezados):
        if encabezado is None:
            continue
        indice[str(encabezado).strip().lower()] = posicion
    return indice


def _respuesta(pestana: str, numero: int, fila: tuple, columnas: dict[str, int], mes: str) -> Respuesta:
    fecha = _fecha(_celda(fila, columnas, "date"))
    anio, mes_numero = (int(parte) for parte in mes.split("-"))
    fuera = fecha is None or fecha.year != anio or fecha.month != mes_numero
    exclusiones: list[str] = []
    csat, motivo = _puntaje(_celda(fila, columnas, "csat"))
    if motivo:
        exclusiones.append(f"CSAT: {motivo}")
    ces, motivo = _puntaje(_celda(fila, columnas, "ces"))
    if motivo:
        exclusiones.append(f"CES: {motivo}")
    csat_2 = None
    if pestana == "catalogo":
        csat_2, motivo = _puntaje(_celda(fila, columnas, "csat 2"))
        if motivo:
            exclusiones.append(f"CSAT 2: {motivo}")
    pregunta = str(_celda(fila, columnas, "pregunta abierta") or "").strip()
    tipo = str(_celda_tipo(fila, columnas) or "").strip().lower()
    return Respuesta(
        id=f"{pestana}-{numero}",
        mes=mes,
        pestana=pestana,
        fecha=fecha,
        csat=csat,
        csat_2=csat_2,
        ces=ces,
        pregunta_abierta=pregunta,
        pregunta_anonimizada=anonimizar(pregunta),
        es_b2c=tipo == "b2c",
        es_ruido=es_ruido(pregunta),
        fuera_de_mes=fuera,
        exclusion_puntaje=exclusiones,
    )


def _celda(fila: tuple, columnas: dict[str, int], nombre: str):
    posicion = columnas.get(nombre)
    if posicion is None or posicion >= len(fila):
        return None
    return fila[posicion]


def _celda_tipo(fila: tuple, columnas: dict[str, int]):
    for nombre in _COLUMNAS_TIPO:
        if nombre in columnas:
            return _celda(fila, columnas, nombre)
    return None


def _fecha(valor) -> datetime | None:
    if isinstance(valor, datetime):
        return valor
    return None


def _puntaje(valor) -> tuple[int | None, str | None]:
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None, "puntaje vacío"
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None, "puntaje fuera de escala"
    if not numero.is_integer() or not 1 <= int(numero) <= 5:
        return None, "puntaje fuera de escala"
    return int(numero), None
