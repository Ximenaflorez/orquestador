from datetime import datetime

import pytest
from pydantic import ValidationError

from orquestador.clasificacion import clasificar
from orquestador.config import Ajustes
from orquestador.modelos import Hallazgo, Respuesta


def test_el_porcentaje_del_total_fija_el_color():
    assert _color(20, 80) == "verde"
    assert _color(21, 79) == "amarillo"
    assert _color(50, 50) == "amarillo"
    assert _color(51, 49) == "rojo"


def test_el_mismo_comentario_es_un_hallazgo():
    filas = [
        _fila(1, "  El filtro se reinicia. "),
        _fila(2, "el   filtro se reinicia."),
    ]
    hallazgos, _, _ = clasificar(filas, _sin_modelo(), "2026-07")
    assert len(hallazgos) == 1
    assert hallazgos[0].conteo == 2
    assert hallazgos[0].porcentaje == 100.0
    assert hallazgos[0].criticidad == "rojo"


def test_el_modelo_no_elige_el_color(monkeypatch):
    def falso(_ajustes, _texto):
        return (
            {
                "modulo": "[Creación de vacantes]",
                "etiqueta": "[BUG]",
                "criticidad": "Crítico",
                "sintesis": "La pantalla se queda en blanco.",
                "sentimiento": "negativo",
                "intensidad": 80,
                "confianza": 90,
                "justificacion": "Falla al guardar.",
            },
            10,
        )

    monkeypatch.setattr("orquestador.clasificacion._consultar", falso)
    ajustes = Ajustes("http://modelo", "nombre", "clave", 1.0, "", "", "", "")
    hallazgos, _, _ = clasificar([_fila(1, "La pantalla se queda en blanco.")], ajustes, "2026-07")
    assert hallazgos[0].estado == "clasificado"
    assert hallazgos[0].etiqueta == "[BUG]"
    assert hallazgos[0].criticidad == "rojo"
    assert hallazgos[0].porcentaje == 100.0


def test_rechaza_la_criticidad_manual():
    with pytest.raises(ValidationError):
        Hallazgo(
            id="hallazgo-1",
            mes="2026-07",
            conteo=1,
            estado="requiere_revision",
            respuestas=["1"],
            pestanas=["creacion"],
            criticidad="Crítico",
        )


def _color(repetidos: int, unicos: int) -> str:
    filas = [_fila(numero, "El mismo comentario.") for numero in range(repetidos)]
    filas.extend(_fila(repetidos + numero, f"Comentario distinto {numero}.") for numero in range(unicos))
    hallazgos, _, _ = clasificar(filas, _sin_modelo(), "2026-07")
    elegido = next(item for item in hallazgos if item.conteo == repetidos)
    assert elegido.porcentaje == round(repetidos * 100 / (repetidos + unicos), 2)
    return elegido.criticidad


def _fila(numero: int, texto: str) -> Respuesta:
    return Respuesta(
        id=f"creacion-{numero}",
        mes="2026-07",
        pestana="creacion",
        fecha=datetime(2026, 7, 2, 9, 0),
        csat=4,
        ces=3,
        pregunta_abierta=texto,
        pregunta_anonimizada=texto,
    )


def _sin_modelo() -> Ajustes:
    return Ajustes("", "", "", 1.0, "", "", "", "")
