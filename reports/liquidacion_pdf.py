from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generar_liquidacion_pdf(datos, ruta):
    doc = SimpleDocTemplate(ruta, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=16*mm, bottomMargin=16*mm)
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name="CentroTitulo", parent=estilos["Title"], alignment=TA_CENTER,
                               textColor=colors.HexColor("#172554"), fontSize=16, leading=20))
    estilos.add(ParagraphStyle(name="Nota", parent=estilos["BodyText"], fontSize=8, leading=11,
                               textColor=colors.HexColor("#475569")))
    historia = [Paragraph("LIQUIDACIÓN DE BENEFICIOS SOCIALES", estilos["CentroTitulo"]),
                Spacer(1, 8*mm)]
    info = [
        ["Trabajador", datos.get("trabajador", ""), "DNI", datos.get("dni", "")],
        ["Cargo", datos.get("cargo", ""), "Régimen", datos.get("regimen_laboral", "")],
        ["Fecha de ingreso", datos.get("fecha_ingreso", ""), "Fecha de cese", datos.get("fecha_cese", "")],
        ["Remuneración computable", f"S/ {datos.get('remuneracion_computable', 0):,.2f}", "Salud", datos.get("regimen_salud", "")],
    ]
    t = Table(info, colWidths=[34*mm, 62*mm, 28*mm, 48*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    historia.extend([t, Spacer(1, 8*mm)])
    filas = [["CONCEPTO", "IMPORTE"]]
    for concepto, importe in datos.get("conceptos", {}).items():
        filas.append([concepto, f"S/ {importe:,.2f}"])
    filas.extend([
        ["TOTAL BRUTO", f"S/ {datos.get('total_bruto', 0):,.2f}"],
        ["DESCUENTOS AUTORIZADOS", f"S/ {datos.get('total_descuentos', 0):,.2f}"],
        ["NETO A PAGAR", f"S/ {datos.get('neto', 0):,.2f}"],
    ])
    tabla = Table(filas, colWidths=[120*mm, 52*mm], hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("PADDING", (0,0), (-1,-1), 7),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0,-3), (-1,-1), "Helvetica-Bold"),
    ]))
    historia.extend([tabla, Spacer(1, 7*mm)])
    historia.append(Paragraph("<b>Observaciones:</b> " + (datos.get("observaciones") or "—"), estilos["BodyText"]))
    historia.append(Spacer(1, 3*mm))
    historia.append(Paragraph(datos.get("nota_calculo", ""), estilos["Nota"]))
    historia.append(Spacer(1, 10*mm))
    historia.append(Paragraph("Documento de cálculo referencial. Verificar los datos laborales, pagos anteriores y régimen aplicable antes de efectuar el pago.", estilos["Nota"]))
    doc.build(historia)
