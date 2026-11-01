import json
from pathlib import Path

import pytest

from orquestador.consulta import DecisionInvalida, decidir, incidentes
from orquestador.vista import html_pagina


def test_la_tipificacion_trae_color_conteo_y_la_decision(tmp_path: Path):
    _auditoria(
        tmp_path,
        "2026-07",
        [
            {"hallazgo_id": "hallazgo-1", "comentario_anonimizado": "El filtro se reinicia.", "criticidad": "amarillo", "porcentaje": 21, "conteo": 21},
            {"hallazgo_id": "hallazgo-2", "comentario_anonimizado": "La pantalla se queda en blanco.", "criticidad": "verde", "porcentaje": 4, "conteo": 4},
        ],
    )
    (tmp_path / "salidas" / "2026-08" / "decisiones.json").parent.mkdir(parents=True)
    (tmp_path / "salidas" / "2026-08" / "decisiones.json").write_text("[]\n", encoding="utf-8")

    with pytest.raises(DecisionInvalida):
        decidir(tmp_path, "2026-07", "hallazgo-1", "rechazado", "")
    decidir(tmp_path, "2026-07", "hallazgo-1", "rechazado", "No mueve la retención.")
    decidir(tmp_path, "2026-07", "hallazgo-2", "aceptado", "")

    lista = incidentes(tmp_path, "2026-07")
    assert [item["conteo"] for item in lista] == [21, 4]
    assert lista[0]["criticidad"] == "amarillo"
    assert lista[0]["resultado"] == "rechazado"
    assert lista[0]["motivo"] == "No mueve la retención."
    assert lista[1]["resultado"] == "aceptado"
    assert lista[1]["comentarios"] == ["La pantalla se queda en blanco."]
    assert json.loads((tmp_path / "salidas" / "2026-08" / "decisiones.json").read_text(encoding="utf-8")) == []
    pagina = html_pagina()
    assert "Se queda" in pagina
    assert "Se va" in pagina
    assert pagina.index("Subir Excel") < pagina.index("Total e histórico")
    assert "Descargar plantilla" in pagina


def test_la_decision_puede_corregir_sintesis_modulo_y_etiqueta(tmp_path: Path):
    _auditoria(
        tmp_path,
        "2026-07",
        [
            {
                "hallazgo_id": "hallazgo-1",
                "sintesis": "El filtro se reinicia.",
                "modulo": "[Catálogo de Candidatos]",
                "etiqueta": "[BUG]",
                "criticidad": "verde",
                "conteo": 2,
            }
        ],
    )
    decidir(
        tmp_path,
        "2026-07",
        "hallazgo-1",
        "aceptado",
        "",
        sintesis="El filtro pierde la selección.",
        modulo="[Gestión de Vacantes]",
        etiqueta="[UX/Usabilidad]",
    )
    guardado = json.loads((tmp_path / "salidas" / "2026-07" / "auditoria.jsonl").read_text(encoding="utf-8"))
    assert guardado["sintesis"] == "El filtro pierde la selección."
    assert guardado["modulo"] == "[Gestión de Vacantes]"
    assert guardado["etiqueta"] == "[UX/Usabilidad]"
    assert guardado["correccion_lider"] is True
    with pytest.raises(DecisionInvalida):
        decidir(tmp_path, "2026-07", "hallazgo-1", "aceptado", "", modulo="Inventado")


def _auditoria(raiz: Path, mes: str, filas: list[dict]) -> None:
    carpeta = raiz / "salidas" / mes
    carpeta.mkdir(parents=True)
    carpeta.joinpath("auditoria.jsonl").write_text(
        "\n".join(json.dumps(fila, ensure_ascii=False) for fila in filas) + "\n",
        encoding="utf-8",
    )
    carpeta.joinpath("decisiones.json").write_text("[]\n", encoding="utf-8")
