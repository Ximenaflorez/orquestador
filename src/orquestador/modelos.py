"""Entidades del ciclo mensual."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MODULOS = (
    "[Gestión de Vacantes]",
    "[Catálogo de Candidatos]",
    "[Solicitud de vacantes]",
    "[Creación de vacantes]",
    "[Carga Masiva de Perfiles]",
    "[Analítica / Superset]",
    "[Bot omnicanal]",
)
ETIQUETAS = ("[BUG]", "[UX/Usabilidad]", "[PERFORMANCE]", "[FEATURE]")
SENTIMIENTOS = ("positivo", "neutral", "negativo")
CRITICIDADES = ("verde", "amarillo", "rojo")
PESTANAS = ("creacion", "catalogo", "gestion")
NOMBRES_PESTANA = {
    "creacion": "Creacion de Vacantes",
    "catalogo": "Catalogo",
    "gestion": "Gestion de Vacantes",
}
RUIDO = {".", "..", "n", "na", "nada", "ok"}


def es_ruido(texto: str) -> bool:
    return texto.strip().lower() in RUIDO


def puntaje_valido(valor: int | None) -> bool:
    return valor is not None and 1 <= valor <= 5


class Respuesta(BaseModel):
    id: str
    mes: str
    pestana: Literal["creacion", "catalogo", "gestion"]
    fecha: datetime | None
    csat: int | None = None
    csat_2: int | None = None
    ces: int | None = None
    pregunta_abierta: str = ""
    pregunta_anonimizada: str = ""
    es_b2c: bool = False
    es_ruido: bool = False
    fuera_de_mes: bool = False
    exclusion_puntaje: list[str] = Field(default_factory=list)

    @field_validator("csat", "csat_2", "ces")
    @classmethod
    def _escala(cls, valor: int | None) -> int | None:
        if valor is None:
            return None
        if not 1 <= valor <= 5:
            raise ValueError("Entero 1 a 5, o vacío")
        return valor


class Alerta(BaseModel):
    tipo: str
    cantidad: int


class MetricaMensual(BaseModel):
    mes: str
    pestana: Literal["creacion", "catalogo", "gestion"]
    nombre: Literal["CSAT", "CES", "CSAT 2"]
    valor: float | None
    n: int
    alertas: list[Alerta] = Field(default_factory=list)

    @field_validator("valor")
    @classmethod
    def _dos_decimales(cls, valor: float | None) -> float | None:
        if valor is None:
            return None
        return round(valor, 2)


class Hallazgo(BaseModel):
    id: str
    mes: str
    modulo: str | None = None
    etiqueta: str | None = None
    criticidad: str | None = None
    sintesis: str = ""
    conteo: int
    porcentaje: float | None = None
    confianza: int = 0
    sentimiento: Literal["positivo", "neutral", "negativo"] = "neutral"
    intensidad: int = 0
    estado: Literal["requiere_revision", "clasificado", "aceptado", "descartado", "reincidente"]
    respuestas: list[str]
    pestanas: list[str]
    correccion_lider: bool = False
    motivo: str = ""
    comentario: str = ""
    comentarios: list[str] = Field(default_factory=list)
    marca: str | None = None

    @field_validator("sintesis")
    @classmethod
    def _dos_lineas(cls, valor: str) -> str:
        lineas = [linea for linea in valor.splitlines() if linea.strip()]
        if len(lineas) > 2:
            raise ValueError("Máximo dos líneas")
        return "\n".join(lineas)

    @field_validator("confianza", "intensidad")
    @classmethod
    def _porcentaje(cls, valor: int) -> int:
        if not 0 <= valor <= 100:
            raise ValueError("Entero 0 a 100")
        return valor

    @field_validator("modulo")
    @classmethod
    def _modulo(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in MODULOS:
            raise ValueError("Módulo fuera de la lista oficial")
        return valor

    @field_validator("etiqueta")
    @classmethod
    def _etiqueta(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in ETIQUETAS:
            raise ValueError("Etiqueta fuera de la lista oficial")
        return valor

    @field_validator("criticidad")
    @classmethod
    def _criticidad(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in CRITICIDADES:
            raise ValueError("La criticidad es verde, amarillo o rojo")
        return valor

    @field_validator("porcentaje")
    @classmethod
    def _critico_porcentaje(cls, valor: float | None) -> float | None:
        if valor is None:
            return None
        return round(valor, 2)


class Corrida(BaseModel):
    mes: str
    inicio: datetime
    fin: datetime
    duracion_segundos: float
    costo_usd: float
    tasa_finalizacion: float
    tasa_override: float = 0.0
    intento_salida: int = 1
    apagado: bool = False
    oficial: bool
    listo_para_comite: bool
