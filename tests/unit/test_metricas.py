from datetime import datetime

from orquestador.clasificacion import clasificar
from orquestador.config import Ajustes
from orquestador.metricas import calcular
from orquestador.modelos import Respuesta


def _respuesta(**cambios) -> Respuesta:
    base = dict(
        id="creacion-2",
        mes="2026-07",
        pestana="creacion",
        fecha=datetime(2026, 7, 2, 9, 0),
        csat=4,
        ces=3,
        pregunta_abierta="El formulario pierde el borrador.",
        pregunta_anonimizada="El formulario pierde el borrador.",
        es_ruido=False,
        es_b2c=False,
        fuera_de_mes=False,
    )
    base.update(cambios)
    return Respuesta(**base)


def test_excluye_puntajes_vacios_y_fuera_de_escala():
    filas = [
        _respuesta(id="creacion-2", csat=None, exclusion_puntaje=["CSAT: puntaje vacío"]),
        _respuesta(id="creacion-3", csat=None, exclusion_puntaje=["CSAT: puntaje fuera de escala"]),
        _respuesta(id="creacion-4", csat=5, ces=5),
    ]
    metricas, alertas = calcular(filas, filas_ignoradas=0)
    csat = next(item for item in metricas if item.pestana == "creacion" and item.nombre == "CSAT")
    assert csat.n == 1
    assert csat.valor == 5.00
    tipos = {alerta.tipo: alerta.cantidad for alerta in alertas}
    assert tipos["puntaje vacío"] == 1
    assert tipos["puntaje fuera de escala"] == 1


def test_csat_y_csat_2_no_se_mezclan():
    fila = _respuesta(id="catalogo-2", pestana="catalogo", csat=2, csat_2=5, ces=4)
    metricas, _ = calcular([fila], filas_ignoradas=0)
    csat = next(item for item in metricas if item.nombre == "CSAT" and item.pestana == "catalogo")
    csat_2 = next(item for item in metricas if item.nombre == "CSAT 2")
    assert csat.valor == 2.00
    assert csat_2.valor == 5.00
    assert all(item.nombre != "CSAT 2" or item.pestana == "catalogo" for item in metricas)


def test_el_ruido_no_crea_hallazgo_y_la_pestaña_vacia_tiene_n_cero():
    ruido = [
        _respuesta(pregunta_abierta=texto, pregunta_anonimizada=texto, es_ruido=True)
        for texto in (".", "N", "nada", "OK", "na", "..")
    ]
    _, alertas = calcular(ruido, filas_ignoradas=2)
    hallazgos, costo, corte = clasificar(ruido, _sin_modelo(), "2026-07")
    assert hallazgos == []
    assert costo == 0
    assert corte is False
    gestion = next(item for item in calcular(ruido, 0)[0] if item.pestana == "gestion")
    assert gestion.n == 0
    assert gestion.valor is None
    assert {alerta.tipo for alerta in alertas} >= {
        "puntaje vacío",
        "puntaje fuera de escala",
        "fecha fuera de mes",
        "fila B2C",
        "pestaña ignorada",
    }


def _sin_modelo() -> Ajustes:
    return Ajustes("", "", "", 1.0, "", "", "", "")
