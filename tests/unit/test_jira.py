import json
from pathlib import Path

import pytest

from orquestador.jira import JiraInvalida, enviar
from orquestador.vista import html_pagina


def test_la_pagina_permite_marcar_y_enviar():
    pagina = html_pagina()
    assert 'id="enviar-jira" hidden disabled' in pagina
    assert "Seleccionar los que se quedan" in pagina


def test_sin_configuracion_no_hay_llamada(tmp_path: Path, monkeypatch):
    for nombre in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT"):
        monkeypatch.delenv(nombre, raising=False)
    llamadas = []
    with pytest.raises(JiraInvalida) as exc:
        enviar(tmp_path, [{"mes": "2026-07", "id": "hallazgo-1"}], crear=lambda *args: llamadas.append(args))
    assert "JIRA_API_TOKEN" in exc.value.motivo
    assert llamadas == []


def test_envia_uno_o_varios_y_no_repite(tmp_path: Path, monkeypatch):
    _configurar(monkeypatch)
    _caso(tmp_path, "2026-07", "hallazgo-uno", "[BUG]", "aceptado")
    _caso(tmp_path, "2026-07", "hallazgo-dos", "[UX/Usabilidad]", "aceptado")
    _caso(tmp_path, "2026-07", "hallazgo-fuera", "[BUG]", "rechazado")
    _caso(tmp_path, "2026-08", "hallazgo-abierto", "[BUG]", "")
    llamadas = []

    def crear(ajustes, resumen, descripcion):
        llamadas.append(resumen)
        clave = f"UX-{len(llamadas)}"
        return {"clave": clave, "url": f"https://magneto.example/browse/{clave}"}

    primero = enviar(tmp_path, [{"mes": "2026-07", "id": "hallazgo-uno"}], crear=crear)
    varios = enviar(
        tmp_path,
        [
            {"mes": "2026-07", "id": "hallazgo-uno"},
            {"mes": "2026-07", "id": "hallazgo-dos"},
            {"mes": "2026-07", "id": "hallazgo-fuera"},
            {"mes": "2026-08", "id": "hallazgo-abierto"},
            {"mes": "2026-07", "id": "hallazgo-sin-etiqueta"},
        ],
        crear=crear,
    )
    assert [item["clave"] for item in primero["creados"]] == ["UX-1"]
    assert [item["clave"] for item in varios["creados"]] == ["UX-1", "UX-2"]
    assert len(llamadas) == 2
    assert any("Solo se envían a Jira los que se quedan." in item["error"] for item in varios["errores"])
    assert any(item["id"] == "hallazgo-abierto" for item in varios["errores"])
    guardado = json.loads((tmp_path / "salidas" / "2026-07" / "jira.json").read_text(encoding="utf-8"))
    assert [item["clave"] for item in guardado] == ["UX-1", "UX-2"]
    assert not (tmp_path / "salidas" / "2026-08" / "jira.json").exists()


def _configurar(monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://magneto.example")
    monkeypatch.setenv("JIRA_EMAIL", "ux@magneto.example")
    monkeypatch.setenv("JIRA_API_TOKEN", "token-de-prueba")
    monkeypatch.setenv("JIRA_PROJECT", "UX")


def _caso(raiz: Path, mes: str, identificador: str, etiqueta: str | None, resultado: str) -> None:
    carpeta = raiz / "salidas" / mes
    carpeta.mkdir(parents=True, exist_ok=True)
    auditoria = carpeta / "auditoria.jsonl"
    previa = auditoria.read_text(encoding="utf-8") if auditoria.is_file() else ""
    linea = json.dumps(
        {
            "hallazgo_id": identificador,
            "mes": mes,
            "etiqueta": etiqueta,
            "modulo": "[Creación de vacantes]",
            "criticidad": "rojo",
            "sintesis": "El listado queda en blanco.",
            "conteo": 4,
        },
        ensure_ascii=False,
    )
    auditoria.write_text(previa + linea + "\n", encoding="utf-8")
    if not resultado:
        return
    ruta = carpeta / "decisiones.json"
    actuales = json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else []
    actuales.append({"hallazgo_id": identificador, "resultado": resultado, "motivo": "Se queda en el comité."})
    ruta.write_text(json.dumps(actuales), encoding="utf-8")
