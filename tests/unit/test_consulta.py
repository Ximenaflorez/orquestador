import json
from pathlib import Path

from orquestador.consulta import resumir
from orquestador.vista import html_pagina


def test_total_ponderado_omite_n_cero_revision_y_meses_sin_salida(tmp_path: Path):
    _mes(
        tmp_path,
        "2026-07",
        [
            {"pestana": "creacion", "nombre": "CSAT", "valor": 4.0, "n": 10},
            {"pestana": "catalogo", "nombre": "CSAT 2", "valor": None, "n": 0},
        ],
        [
            {"hallazgo_id": "hallazgo-abierto", "mes": "2026-07", "etiqueta": None, "modulo": None, "criticidad": None, "sintesis": "", "conteo": 1},
            {
                "hallazgo_id": "hallazgo-aceptado",
                "mes": "2026-07",
                "etiqueta": None,
                "modulo": "[Gestión de Vacantes]",
                "criticidad": "amarillo",
                "sintesis": "",
                "comentario_anonimizado": "Quiero pausar una vacante.",
                "conteo": 2,
            },
            {
                "mes": "2026-07",
                "etiqueta": "[BUG]",
                "modulo": "[Creación de vacantes]",
                "criticidad": "verde",
                "sintesis": "La pantalla se queda en blanco.",
                "conteo": 2,
            },
            {
                "hallazgo_id": "hallazgo-excluido",
                "mes": "2026-07",
                "etiqueta": "[BUG]",
                "modulo": "[Catálogo de Candidatos]",
                "criticidad": "rojo",
                "sintesis": "El buscador ignora los acentos.",
                "conteo": 5,
            },
        ],
    )
    _mes(
        tmp_path,
        "2026-08",
        [{"pestana": "creacion", "nombre": "CSAT", "valor": 2.0, "n": 30}],
        [],
    )
    (tmp_path / "salidas" / "2026-07" / "decisiones.json").write_text(
        json.dumps(
            [
                {"hallazgo_id": "hallazgo-aceptado", "resultado": "aceptado", "motivo": ""},
                {"hallazgo_id": "hallazgo-excluido", "resultado": "rechazado", "motivo": "No mueve la retención."},
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "datos" / "meses").mkdir(parents=True)
    (tmp_path / "datos" / "meses" / "feedback_response_2026-09.xlsx").write_bytes(b"sin correr")

    resumen = resumir(tmp_path)
    assert resumen["meses"] == ["2026-07", "2026-08"]
    csat = next(item for item in resumen["totales"] if item["nombre"] == "CSAT" and item["pestana"] == "creacion")
    assert csat["valor"] == 2.5
    assert csat["n"] == 40
    assert all(item["nombre"] != "CSAT 2" for item in resumen["totales"])
    assert resumen["historico"] == [
        {
            "mes": "2026-07",
            "modulo": "[Gestión de Vacantes]",
            "etiqueta": None,
            "criticidad": "amarillo",
            "sintesis": "Quiero pausar una vacante.",
            "conteo": 2,
            "resultado": "aceptado",
            "motivo": "",
            "id": "hallazgo-aceptado",
            "jira": None,
            "comentarios": ["Quiero pausar una vacante."],
        },
    ]
    assert resumen["backlog"] == []
    assert resumen["excluidos"] == [
        {
            "mes": "2026-07",
            "modulo": "[Catálogo de Candidatos]",
            "etiqueta": "[BUG]",
            "criticidad": "rojo",
            "sintesis": "El buscador ignora los acentos.",
            "conteo": 5,
            "resultado": "rechazado",
            "motivo": "No mueve la retención.",
            "comentarios": ["El buscador ignora los acentos."],
        }
    ]
    pagina = html_pagina()
    assert "Excluidos" in pagina
    assert "Tipificados" in pagina
    assert "Backlog" in pagina
    assert "Guardar el mes" in pagina
    assert "Ver comentarios" in pagina
    assert "Ver hallazgos" in pagina
    assert "<th>Decisión</th>" not in pagina
    assert "${botonOjo(item)}" in pagina
    assert "${botonHallazgos()}" in pagina
    assert 'class="acordeon"' in pagina
    assert "Total e histórico" in pagina
    assert "Cuántas personas evaluaron" in pagina
    assert "Por mes" in pagina
    assert "Trimestre" in pagina
    assert "Semestre" in pagina
    assert "Resultado del mes" not in pagina
    assert pagina.index("Total e histórico") < pagina.index("Guardar el mes")
    assert pagina.index("Guardar el mes") < pagina.index("Tipificados")
    julio = next(item for item in resumen["por_mes"] if item["mes"] == "2026-07" and item["nombre"] == "CSAT")
    agosto = next(item for item in resumen["por_mes"] if item["mes"] == "2026-08" and item["nombre"] == "CSAT")
    assert julio["valor"] == 4.0 and julio["n"] == 10
    assert agosto["valor"] == 2.0 and agosto["n"] == 30
    vacio = next(item for item in resumen["por_mes"] if item["nombre"] == "CSAT 2")
    assert vacio["valor"] is None and vacio["n"] == 0
    (tmp_path / "salidas" / "2026-07" / "jira.json").write_text(
        json.dumps([{"hallazgo_id": "hallazgo-aceptado", "clave": "KAN-1", "url": "https://ximena-alvarez.atlassian.net/browse/KAN-1"}]),
        encoding="utf-8",
    )
    con_ticket = resumir(tmp_path)
    assert con_ticket["historico"] == []
    assert con_ticket["backlog"][0]["id"] == "hallazgo-aceptado"
    assert con_ticket["backlog"][0]["jira"]["clave"] == "KAN-1"


def _mes(raiz: Path, mes: str, metricas: list[dict], auditoria: list[dict]) -> None:
    carpeta = raiz / "salidas" / mes
    carpeta.mkdir(parents=True)
    (carpeta / "metricas.json").write_text(json.dumps(metricas), encoding="utf-8")
    lineas = [json.dumps(item, ensure_ascii=False) for item in auditoria]
    (carpeta / "auditoria.jsonl").write_text("\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")
