"""Configuración leída del entorno. La clave del modelo no se imprime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def proyecto_raiz() -> Path:
    indicado = os.environ.get("ORQUESTADOR_RAIZ")
    if indicado:
        return Path(indicado)
    return Path.cwd()


def cargar_entorno(raiz: Path | None = None) -> None:
    ruta = (raiz or proyecto_raiz()) / ".env"
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        texto = linea.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        nombre, _, valor = texto.partition("=")
        nombre = nombre.strip()
        valor = valor.strip().strip('"').strip("'")
        if nombre and valor and nombre not in os.environ:
            os.environ[nombre] = valor


@dataclass(frozen=True)
class Ajustes:
    model_base_url: str
    model_name: str
    model_api_key: str
    usd_por_millon: float
    smtp_host: str
    smtp_port: str
    smtp_from: str
    smtp_to: str
    embedding_name: str = ""
    embedding_umbral: float = 0.85

    @property
    def tiene_modelo(self) -> bool:
        return bool(self.model_api_key.strip() and self.model_base_url.strip() and self.model_name.strip())

    @property
    def tiene_embeddings(self) -> bool:
        return bool(self.model_api_key.strip() and self.model_base_url.strip() and self.embedding_name.strip())

    @property
    def tiene_correo(self) -> bool:
        return all(parte.strip() for parte in (self.smtp_host, self.smtp_port, self.smtp_from, self.smtp_to))


def cargar_ajustes() -> Ajustes:
    def leer(nombre: str) -> str:
        return os.environ.get(nombre, "").strip()

    precio = leer("MODEL_USD_PER_MILLION") or "1"
    try:
        usd = float(precio)
    except ValueError:
        usd = 1.0
    umbral_texto = leer("MODEL_EMBEDDING_UMBRAL") or "0.85"
    try:
        umbral = float(umbral_texto)
    except ValueError:
        umbral = 0.85
    if not 0 <= umbral <= 1:
        umbral = 0.85
    return Ajustes(
        model_base_url=leer("MODEL_BASE_URL").rstrip("/"),
        model_name=leer("MODEL_NAME"),
        model_api_key=leer("MODEL_API_KEY"),
        usd_por_millon=usd,
        smtp_host=leer("SMTP_HOST"),
        smtp_port=leer("SMTP_PORT"),
        smtp_from=leer("SMTP_FROM"),
        smtp_to=leer("SMTP_TO"),
        embedding_name=leer("MODEL_EMBEDDING_NAME"),
        embedding_umbral=umbral,
    )
