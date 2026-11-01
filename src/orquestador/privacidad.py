"""Sustituye contactos y documentos por un marcador neutro."""

from __future__ import annotations

import re

MARCADOR = "[dato oculto]"
_CORREO = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
_TELEFONO = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(\d{2,4}\)[\s-]?|\d{2,4}[\s-])\d{3,4}[\s-]?\d{4}")
_DOCUMENTO = re.compile(r"\b\d{6,12}\b")


def anonimizar(texto: str) -> str:
    sin_correo = _CORREO.sub(MARCADOR, texto)
    sin_telefono = _TELEFONO.sub(MARCADOR, sin_correo)
    return _DOCUMENTO.sub(MARCADOR, sin_telefono)
