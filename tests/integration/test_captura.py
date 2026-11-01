import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from orquestador.captura import CapturaInvalida, guardar, plantilla, recibir_libro

ROOT = Path(__file__).resolve().parents[2]
JULIO = ROOT / "datos" / "meses" / "feedback_response_2026-07.xlsx"


def test_guardar_junio_no_cambia_julio(tmp_path: Path):
    destino = tmp_path / "datos" / "meses"
    destino.mkdir(parents=True)
    copia = destino / JULIO.name
    shutil.copy(JULIO, copia)
    antes = _valores(copia)
    original = _valores(JULIO)
    guardar(
        tmp_path,
        "2026-06",
        [
            {
                "pestana": "catalogo",
                "fecha": "2026-06-03",
                "csat": 4,
                "csat_2": 5,
                "ces": 3,
                "pregunta": "El filtro no conserva la selección.",
            }
        ],
    )
    assert _valores(copia) == antes
    assert _valores(JULIO) == original
    libro = load_workbook(destino / "feedback_response_2026-06.xlsx", read_only=True, data_only=True)
    try:
        assert libro.sheetnames == ["Creacion de Vacantes", "Catalogo", "Gestion de Vacantes"]
        filas = list(libro["Catalogo"].iter_rows(values_only=True))
    finally:
        libro.close()
    assert filas[0] == ("DATE", "CSAT", "CSAT 2", "CES", "PREGUNTA ABIERTA")
    assert filas[1][1:5] == (4, 5, 3, "El filtro no conserva la selección.")
    try:
        guardar(tmp_path, "2026-06", [{"pestana": "creacion", "fecha": "2026-06-01", "csat": 9, "ces": 3, "pregunta": "x"}])
    except CapturaInvalida:
        return
    raise AssertionError("un puntaje fuera de 1 a 5 debe rechazarse")


def test_el_excel_de_ejemplo_se_guarda_sin_tocar_otro_mes(tmp_path: Path):
    destino = tmp_path / "datos" / "meses"
    destino.mkdir(parents=True)
    copia = destino / JULIO.name
    shutil.copy(JULIO, copia)
    antes = _valores(copia)
    contenido = plantilla()
    mes = recibir_libro(tmp_path, "feedback_response_2026-01.xlsx", contenido)
    assert mes == "2026-01"
    assert (destino / "feedback_response_2026-01.xlsx").read_bytes() == contenido
    assert _valores(copia) == antes
    libro = load_workbook(BytesIO(contenido), read_only=True, data_only=True)
    try:
        assert libro.sheetnames == ["Creacion de Vacantes", "Catalogo", "Gestion de Vacantes"]
        encabezados = next(libro["Catalogo"].iter_rows(max_row=1, values_only=True))
    finally:
        libro.close()
    assert encabezados == ("DATE", "CSAT", "CSAT 2", "CES", "PREGUNTA ABIERTA")
    try:
        recibir_libro(tmp_path, "libro.xlsx", contenido)
    except CapturaInvalida:
        return
    raise AssertionError("un nombre sin el mes debe rechazarse")


def _valores(ruta: Path) -> list:
    libro = load_workbook(ruta, data_only=True, read_only=True)
    try:
        return [(hoja, fila) for hoja in libro.sheetnames for fila in libro[hoja].iter_rows(values_only=True)]
    finally:
        libro.close()
