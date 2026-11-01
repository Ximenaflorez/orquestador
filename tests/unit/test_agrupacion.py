from datetime import datetime

from orquestador.clasificacion import clasificar
from orquestador.config import Ajustes
from orquestador.modelos import Respuesta


def test_sin_embeddings_no_une_frases_distintas(monkeypatch):
    def no_debe_llamarse(*_args):
        raise AssertionError("no hay modelo de embeddings")

    monkeypatch.setattr("orquestador.clasificacion._embeddings", no_debe_llamarse)
    filas = [
        _fila(1, "La pantalla se queda en blanco"),
        _fila(2, "Se queda en blanco la pantalla"),
    ]
    hallazgos, costo, _ = clasificar(filas, _sin_modelo(), "2026-07")
    assert len(hallazgos) == 2
    assert costo == 0
    assert all(len(item.comentarios) == 1 for item in hallazgos)


def test_frases_parecidas_se_unen_y_conservan_los_originales(monkeypatch):
    monkeypatch.setattr("orquestador.clasificacion._consultar", lambda *_args: (None, 0))
    monkeypatch.setattr("orquestador.clasificacion._embeddings", _vectores)
    filas = [
        _fila(1, "La pantalla se queda en blanco"),
        _fila(2, "Se queda en blanco la pantalla"),
        _fila(3, "Al cambiar la ciudad, el listado de cargos queda en blanco."),
    ]
    hallazgos, costo, _ = clasificar(filas, _con_embeddings(), "2026-07")
    assert costo > 0
    assert len(hallazgos) == 2
    unidos = next(item for item in hallazgos if item.conteo == 2)
    assert unidos.comentarios == [
        "La pantalla se queda en blanco",
        "Se queda en blanco la pantalla",
    ]
    assert unidos.comentario == "La pantalla se queda en blanco"
    aparte = next(item for item in hallazgos if item.conteo == 1)
    assert aparte.comentarios == ["Al cambiar la ciudad, el listado de cargos queda en blanco."]


def test_embeddings_invalidos_dejan_el_texto_identico(monkeypatch):
    monkeypatch.setattr("orquestador.clasificacion._consultar", lambda *_args: (None, 0))
    monkeypatch.setattr("orquestador.clasificacion._embeddings", lambda *_args: (None, 0))
    filas = [
        _fila(1, "La pantalla se queda en blanco"),
        _fila(2, "Se queda en blanco la pantalla"),
    ]
    hallazgos, costo, _ = clasificar(filas, _con_embeddings(), "2026-07")
    assert len(hallazgos) == 2
    assert costo == 0


def _vectores(_ajustes, textos):
    tabla = {
        "La pantalla se queda en blanco": [1.0, 0.0],
        "Se queda en blanco la pantalla": [0.9, 0.1],
        "Al cambiar la ciudad, el listado de cargos queda en blanco.": [0.0, 1.0],
    }
    return [tabla[texto] for texto in textos], 12


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


def _con_embeddings() -> Ajustes:
    return Ajustes(
        "http://modelo",
        "nombre",
        "clave",
        1.0,
        "",
        "",
        "",
        "",
        embedding_name="embed",
        embedding_umbral=0.85,
    )
