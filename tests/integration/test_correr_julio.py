import json
import shutil
from pathlib import Path

from openpyxl import load_workbook

from orquestador.cli import main

ROOT = Path(__file__).resolve().parents[2]
ORIGEN = ROOT / "datos" / "meses" / "feedback_response_2026-07.xlsx"


def test_julio_entrega_reporte_sin_cambiar_el_libro(tmp_path, monkeypatch):
    antes = _valores(ORIGEN)
    monkeypatch.setenv("ORQUESTADOR_RAIZ", str(tmp_path))
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    carpeta = tmp_path / "datos" / "meses"
    carpeta.mkdir(parents=True)
    copia = carpeta / ORIGEN.name
    shutil.copy(ORIGEN, copia)
    assert main(["correr", "--mes", "2026-07"]) == 0
    assert main(["correr", "--mes", "2026-07"]) == 0
    reporte = (tmp_path / "salidas" / "2026-07" / "reporte.md").read_text(encoding="utf-8")
    for nombre in ("Creacion de Vacantes", "Catalogo", "Gestion de Vacantes"):
        assert nombre in reporte
    assert "Vacantes Stages" not in reporte
    assert "CSAT 2" in reporte
    primera = (tmp_path / "salidas" / "2026-07" / "muestra-auditoria.json").read_text(encoding="utf-8")
    assert main(["correr", "--mes", "2026-07"]) == 0
    segunda = (tmp_path / "salidas" / "2026-07" / "muestra-auditoria.json").read_text(encoding="utf-8")
    assert json.loads(primera) == json.loads(segunda)
    assert _valores(copia) == antes
    assert _valores(ORIGEN) == antes


def _valores(ruta: Path) -> list:
    libro = load_workbook(ruta, data_only=True, read_only=True)
    try:
        return [
            (hoja, fila)
            for hoja in libro.sheetnames
            for fila in libro[hoja].iter_rows(values_only=True)
        ]
    finally:
        libro.close()
