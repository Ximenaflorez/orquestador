"""Genera una plantilla mensual y tres meses ficticios. No lee datos reales."""

from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

ROOT = Path(__file__).resolve().parent
MESES = ROOT / "meses"

SHEETS = {
    "Creacion de Vacantes": ["DATE", "CSAT", "CES", "PREGUNTA ABIERTA"],
    "Catalogo": ["DATE", "CSAT", "CSAT 2", "CES", "PREGUNTA ABIERTA"],
    "Gestion de Vacantes": ["DATE", "CSAT", "CES", "PREGUNTA ABIERTA"],
}

NOISE = [".", "N", "Nada", "OK", "na", ".."]

COMMENTS = {
    "Creacion de Vacantes": [
        "No veo un botón claro para guardar el borrador de la vacante.",
        "El formulario vuelve a pedir el salario después de la vista previa.",
        "Al cambiar la ciudad, el listado de cargos queda en blanco.",
        "La vista previa de la publicación tarda varios segundos en abrir.",
        "Me serviría duplicar una vacante anterior sin reescribirla.",
        "El campo de modalidad aparece después de publicar, no antes.",
        "Perdí el texto de la descripción al regresar un paso.",
        "La ayuda del formulario usa términos distintos a los de mi equipo.",
    ],
    "Catalogo": [
        "El filtro por habilidad no conserva lo que ya había marcado.",
        "Dos perfiles parecidos aparecen como si fueran la misma persona.",
        "La ficha no muestra la última actualización del perfil.",
        "Ordenar por experiencia mueve la página hasta el inicio.",
        "Necesito ocultar perfiles que ya revisé en esta vacante.",
        "El buscador ignora los acentos y devuelve otro resultado.",
        "La comparación de dos perfiles no cabe en la pantalla.",
        "Al exportar la selección, el archivo sale sin los encabezados.",
    ],
    "Gestion de Vacantes": [
        "No distingo cuáles vacantes siguen abiertas y cuáles ya cerré.",
        "El cambio de responsable no queda registrado en la vacante.",
        "Quiero pausar una vacante sin borrarla del listado.",
        "La fecha de cierre se muestra en un formato distinto al resto.",
        "El indicador de postulaciones no coincide con el listado.",
        "Falta un aviso cuando una vacante lleva días sin actividad.",
    ],
}

# Volúmenes ilustrativos, distintos a cualquier corte real.
VOLUMES = {
    "2026-07": {
        "Creacion de Vacantes": 28,
        "Catalogo": 34,
        "Gestion de Vacantes": 10,
    },
    "2026-08": {
        "Creacion de Vacantes": 24,
        "Catalogo": 30,
        "Gestion de Vacantes": 8,
    },
    "2026-09": {
        "Creacion de Vacantes": 32,
        "Catalogo": 38,
        "Gestion de Vacantes": 12,
    },
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True, name="Calibri", size=11)
THIN = Border(
    left=Side(style="thin", color="D9E2F3"),
    right=Side(style="thin", color="D9E2F3"),
    top=Side(style="thin", color="D9E2F3"),
    bottom=Side(style="thin", color="D9E2F3"),
)
ZEBRA = PatternFill("solid", fgColor="F7F9FC")


def style_header(ws, headers):
    for col, name in enumerate(headers, start=1):
        cell = ws.cell(1, col, name)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 22
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    ws.freeze_panes = "A2"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.tabColor = "1F4E79"
    widths = {"DATE": 20, "CSAT": 12, "CSAT 2": 12, "CES": 12, "PREGUNTA ABIERTA": 78}
    for col, name in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col)].width = widths[name]


def add_validations(ws, headers):
    last = 500
    score = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True)
    score.error = "Usa un entero del 1 al 5."
    score.errorTitle = "Escala"
    score.prompt = "Entero del 1 al 5."
    score.promptTitle = "Puntaje"
    ws.add_data_validation(score)
    for name in ("CSAT", "CSAT 2", "CES"):
        if name in headers:
            col = get_column_letter(headers.index(name) + 1)
            score.add(f"{col}2:{col}{last}")
    date_col = "A"
    dates = DataValidation(type="date", operator="between", formula1="DATE(2024,1,1)", formula2="DATE(2035,12,31)", allow_blank=True)
    dates.error = "Ingresa una fecha válida."
    dates.errorTitle = "Fecha"
    ws.add_data_validation(dates)
    dates.add(f"{date_col}2:{date_col}{last}")


def write_rows(ws, headers, rows):
    text_col = headers.index("PREGUNTA ABIERTA") + 1
    date_col = headers.index("DATE") + 1
    for r, row in enumerate(rows, start=2):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(r, c, value)
            cell.border = THIN
            cell.font = Font(name="Calibri", size=11)
            cell.alignment = Alignment(vertical="center", wrap_text=(c == text_col))
            if r % 2 == 0:
                cell.fill = ZEBRA
        ws.cell(r, date_col).number_format = "YYYY-MM-DD HH:MM"
        ws.row_dimensions[r].height = 18


def build_month(month_key):
    year, month = (int(part) for part in month_key.split("-"))
    start = datetime(year, month, 1, 9, 0, 0)
    volumes = VOLUMES[month_key]
    wb = Workbook()
    first = True
    for sheet_name, headers in SHEETS.items():
        ws = wb.active if first else wb.create_sheet(sheet_name)
        if first:
            ws.title = sheet_name
            first = False
        style_header(ws, headers)
        add_validations(ws, headers)
        count = volumes[sheet_name]
        rows = []
        for i in range(count):
            moment = start + timedelta(days=i % 27, hours=(i * 3) % 9, minutes=(i * 11) % 50)
            csat = (1, 2, 3, 4, 4, 5, 5, 5)[i % 8]
            ces = (1, 2, 3, 3, 4, 4, 5, 5)[i % 8]
            if i % 5 == 0:
                answer = NOISE[i % len(NOISE)]
            else:
                pool = COMMENTS[sheet_name]
                answer = pool[i % len(pool)]
            if "CSAT 2" in headers:
                csat2 = (1, 2, 3, 4, 4, 5, 5)[i % 7]
                rows.append((moment, csat, csat2, ces, answer))
            else:
                rows.append((moment, csat, ces, answer))
        write_rows(ws, headers, rows)
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(count + 1, 2)}"
        ws.oddHeader.left.text = "Muestra ficticia"
        ws.oddFooter.left.text = month_key
        ws.sheet_view.showGridLines = False
    wb.properties.title = f"Muestra ficticia {month_key}"
    wb.properties.creator = "Orquestador de métricas UX"
    wb.properties.subject = "Datos de ejemplo, sin información de clientes"
    path = MESES / f"feedback_response_{month_key}.xlsx"
    wb.save(path)
    return path


def build_template():
    wb = Workbook()
    guide = wb.active
    guide.title = "Como usarla"
    guide.sheet_properties.tabColor = "C65911"
    guide.sheet_view.showGridLines = False
    guide.page_setup.orientation = "landscape"
    guide.page_setup.fitToPage = True
    guide.page_setup.fitToWidth = 1
    guide.page_setup.fitToHeight = 1
    guide.column_dimensions["A"].width = 28
    guide.column_dimensions["B"].width = 88
    guide.row_dimensions[1].height = 32
    title = guide["A1"]
    title.value = "Plantilla mensual de feedback"
    title.font = Font(name="Calibri", size=20, bold=True, color="1F4E79")
    guide.merge_cells("A1:B1")
    intro = guide["A2"]
    intro.value = (
        "Un archivo representa un mes. Duplica esta plantilla, "
        "renómbrala feedback_response_AAAA-MM.xlsx y completa solo ese periodo."
    )
    intro.alignment = Alignment(wrap_text=True, vertical="center")
    guide.merge_cells("A2:B2")
    guide.row_dimensions[2].height = 36
    rows = [
        ("Qué va en el archivo", "Solo las respuestas de un mes. La fecha de cada fila debe caer dentro de ese mes."),
        ("Nombre sugerido", "feedback_response_2026-10.xlsx, cambiando el año y el mes."),
        ("Pestañas", "Creacion de Vacantes, Catalogo y Gestion de Vacantes."),
        ("DATE", "Fecha y hora de la respuesta."),
        ("CSAT y CSAT 2", "Entero del 1 al 5. CSAT 2 existe solo en Catalogo."),
        ("CES", "Entero del 1 al 5, igual que la exportación de origen."),
        ("PREGUNTA ABIERTA", "Texto de la persona usuaria. Puede ser ruido: .  N  Nada  OK  na."),
        ("Qué no pegar aquí", "Nombres, correos, teléfonos, empresas ni el archivo confidencial de trabajo."),
        ("Muestras", "datos/meses trae julio, agosto y septiembre ficticios para probar el orquestador."),
    ]
    header_fill = PatternFill("solid", fgColor="1F4E79")
    for col, text in enumerate(("Campo", "Cómo completarlo"), start=1):
        cell = guide.cell(4, col, text)
        cell.fill = header_fill
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
    for offset, (label, detail) in enumerate(rows):
        excel_row = 5 + offset
        left = guide.cell(excel_row, 1, label)
        right = guide.cell(excel_row, 2, detail)
        left.font = Font(name="Calibri", size=11, bold=True, color="1F4E79")
        right.font = Font(name="Calibri", size=11)
        right.alignment = Alignment(wrap_text=True, vertical="center")
        guide.row_dimensions[excel_row].height = 28
        fill = PatternFill("solid", fgColor="FFF8F1" if offset % 2 else "F7F9FC")
        left.fill = fill
        right.fill = fill
        left.border = THIN
        right.border = THIN
    guide.oddHeader.center.text = "Plantilla de entrada mensual"
    guide.oddFooter.left.text = "Datos de clientes no van en esta plantilla"
    guide.print_title_rows = "1:4"
    guide.page_setup.paperSize = guide.PAPERSIZE_TABLOID

    for sheet_name, headers in SHEETS.items():
        ws = wb.create_sheet(sheet_name)
        style_header(ws, headers)
        add_validations(ws, headers)
        note = Comment(
            "Deja esta fila para la primera respuesta del mes. No escribas datos de clientes reales en el repositorio de muestra.",
            "Plantilla",
        )
        note.width = 280
        note.height = 70
        ws.cell(2, len(headers)).comment = note
    wb.properties.title = "Plantilla mensual de feedback"
    wb.properties.creator = "Orquestador de métricas UX"
    wb.properties.subject = "Formato de entrada, un archivo por mes"
    path = ROOT / "plantilla-mensual.xlsx"
    wb.save(path)
    return path


if __name__ == "__main__":
    MESES.mkdir(parents=True, exist_ok=True)
    print(build_template())
    for month in VOLUMES:
        print(build_month(month))
