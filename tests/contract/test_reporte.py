import json
from pathlib import Path

from orquestador.cli import main

ROOT = Path(__file__).resolve().parents[2]
SECCIONES = [
    "Resumen de KPIs mensuales",
    "Alertas de calidad de datos",
    "Quejas tipificadas",
    "Revisión humana",
    "Muestra para auditoría numérica",
]


def test_reporte_cumple_el_contrato(tmp_path, monkeypatch):
    monkeypatch.setenv("ORQUESTADOR_RAIZ", str(tmp_path))
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    _copiar_julio(tmp_path)
    assert main(["correr", "--mes", "2026-07"]) == 0
    reporte = (tmp_path / "salidas" / "2026-07" / "reporte.md").read_text(encoding="utf-8")
    posiciones = [reporte.index(seccion) for seccion in SECCIONES]
    assert posiciones == sorted(posiciones)
    assert "Valor calculado" in reporte
    assert "Tamaño de muestra (n)" in reporte
    metricas = json.loads((tmp_path / "salidas" / "2026-07" / "metricas.json").read_text(encoding="utf-8"))
    pares = {(item["pestana"], item["nombre"]) for item in metricas}
    assert ("catalogo", "CSAT 2") in pares
    assert all(item["nombre"] != "CSAT 2" or item["pestana"] == "catalogo" for item in metricas)
    for item in metricas:
        if item["valor"] is not None:
            assert item["valor"] == round(item["valor"], 2)
            assert f"{item['valor']:.2f}" in reporte


def _copiar_julio(destino: Path) -> None:
    import shutil

    origen = ROOT / "datos" / "meses" / "feedback_response_2026-07.xlsx"
    carpeta = destino / "datos" / "meses"
    carpeta.mkdir(parents=True)
    shutil.copy(origen, carpeta / origen.name)
