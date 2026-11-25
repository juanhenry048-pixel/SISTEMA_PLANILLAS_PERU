
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from xml.sax.saxutils import escape
from datetime import datetime


# ============================================================
# CONFIGURACIÓN DE LA EMPRESA
# MODIFICA ESTOS DATOS CUANDO SEA NECESARIO
# ============================================================

EMPRESA = "CORPORACION EMPRESARIAL HOLDING S.A.C."
RUC = "20611137355"
DOMICILIO_EMPRESA = "TRUJILLO - LA LIBERTAD"
TELEFONO_EMPRESA = ""
CORREO_EMPRESA = ""

# Colores corporativos
AZUL_OSCURO = HexColor("#17365D")
AZUL_MEDIO = HexColor("#24476B")
AZUL_CLARO = HexColor("#EAF1F8")
GRIS_FONDO = HexColor("#F3F5F7")
GRIS_TEXTO = HexColor("#525B65")
GRIS_LINEA = HexColor("#D5DCE3")
VERDE = HexColor("#217346")
BLANCO = colors.white
NEGRO = colors.black


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def obtener(datos, *claves, defecto=""):
    """Obtiene un dato utilizando varias posibles claves."""
    for clave in claves:
        valor = datos.get(clave)
        if valor is not None and valor != "":
            return valor
    return defecto


def numero(valor):
    try:
        return float(valor or 0)
    except (ValueError, TypeError):
        return 0.0


def moneda(valor):
    return f"S/ {numero(valor):,.2f}"


def texto(valor):
    if valor is None or valor == "":
        return "No registrado"
    return escape(str(valor))


def nombre_mes(mes):
    meses = [
        "Enero", "Febrero", "Marzo", "Abril",
        "Mayo", "Junio", "Julio", "Agosto",
        "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    try:
        return meses[int(mes) - 1]
    except (ValueError, TypeError, IndexError):
        return str(mes)


def crear_estilos():
    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloBoleta",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER,
        spaceAfter=4
    ))

    estilos.add(ParagraphStyle(
        name="Empresa",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=AZUL_OSCURO,
        alignment=TA_CENTER
    ))

    estilos.add(ParagraphStyle(
        name="Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=GRIS_TEXTO,
        alignment=TA_CENTER
    ))

    estilos.add(ParagraphStyle(
        name="Seccion",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=BLANCO
    ))

    estilos.add(ParagraphStyle(
        name="Texto",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=GRIS_TEXTO
    ))

    estilos.add(ParagraphStyle(
        name="TextoNegrita",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=AZUL_OSCURO
    ))

    estilos.add(ParagraphStyle(
        name="TextoPequeno",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=GRIS_TEXTO
    ))

    estilos.add(ParagraphStyle(
        name="Total",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=AZUL_OSCURO
    ))

    estilos.add(ParagraphStyle(
        name="Neto",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=BLANCO,
        alignment=TA_CENTER
    ))

    estilos.add(ParagraphStyle(
        name="NetoEtiqueta",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=BLANCO,
        alignment=TA_CENTER
    ))

    return estilos


def encabezado_seccion(titulo, ancho):
    tabla = Table(
        [[Paragraph(titulo.upper(), crear_estilos()["Seccion"])]],
        colWidths=[ancho]
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_OSCURO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return tabla


def tabla_datos(filas, anchos, encabezado=False):
    tabla = Table(
        filas,
        colWidths=anchos,
        repeatRows=1 if encabezado else 0
    )

    reglas = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, GRIS_LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if encabezado:
        reglas.extend([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_CLARO),
            ("TEXTCOLOR", (0, 0), (-1, 0), AZUL_OSCURO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    else:
        for fila in range(len(filas)):
            if fila % 2 == 1:
                reglas.append(
                    ("BACKGROUND", (0, fila), (-1, fila), GRIS_FONDO)
                )

    tabla.setStyle(TableStyle(reglas))
    return tabla


# ============================================================
# GENERADOR PRINCIPAL DE BOLETA
# ============================================================

def generar_boleta_pdf(datos, ruta):

    estilos = crear_estilos()

    ancho_pagina, alto_pagina = A4
    ancho_util = ancho_pagina - 30 * mm

    documento = SimpleDocTemplate(
        ruta,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title="Boleta de Pago",
        author=EMPRESA
    )

    elementos = []

    # --------------------------------------------------------
    # DATOS GENERALES
    # --------------------------------------------------------

    nombres = obtener(datos, "nombres", defecto="")
    apellidos = obtener(datos, "apellidos", defecto="")
    trabajador = f"{apellidos}, {nombres}".strip(", ")

    dni = obtener(datos, "dni")
    cargo = obtener(datos, "cargo")
    # Mantener separadas la fecha de nacimiento y la fecha de ingreso laboral.
    fecha_nacimiento = obtener(datos, "fecha_nacimiento")
    fecha_ingreso_laboral = obtener(
        datos, "fecha_ingreso_laboral", "fecha_ingreso"
    )
    genero = str(obtener(datos, "genero")).strip().upper()
    if genero not in ("FEMENINO", "MASCULINO"):
        genero = "No registrado"

    tipo_contrato = obtener(datos, "tipo_contrato")

    anio = obtener(datos, "anio", defecto=datetime.now().year)
    mes = obtener(datos, "mes", defecto=datetime.now().month)
    periodo = f"{nombre_mes(mes)} {anio}"

    sueldo = numero(obtener(datos, "sueldo_basico"))
    asignacion = numero(obtener(datos, "asignacion_familiar"))
    horas_extras = numero(obtener(datos, "horas_extras"))
    otros_ingresos = numero(obtener(datos, "otros_ingresos"))

    total_ingresos = numero(obtener(datos, "total_ingresos"))

    if total_ingresos == 0:
        total_ingresos = (
            sueldo + asignacion + horas_extras + otros_ingresos
        )

    pension = numero(obtener(datos, "descuento_pension"))
    essalud = numero(obtener(datos, "essalud"))
    neto = numero(obtener(datos, "neto_pagar"))

    if neto == 0 and total_ingresos > 0:
        neto = total_ingresos - pension

    tipo_pension = obtener(datos, "tipo_pension", defecto="No registrado")
    porcentaje = numero(obtener(datos, "porcentaje_pension"))

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------

    elementos.append(Paragraph("BOLETA DE PAGO", estilos["TituloBoleta"]))
    elementos.append(Paragraph(escape(EMPRESA), estilos["Empresa"]))
    elementos.append(Paragraph(
        f"RUC: {escape(RUC)}",
        estilos["Subtitulo"]
    ))
    elementos.append(Paragraph(
        f"Domicilio: {escape(DOMICILIO_EMPRESA)}",
        estilos["Subtitulo"]
    ))

    elementos.append(Spacer(1, 5))

    cabecera = Table(
        [[
            Paragraph(
                f"<b>PERIODO:</b> {escape(periodo)}",
                estilos["TextoNegrita"]
            ),
            Paragraph(
                f"<b>ÁREA:</b> {texto(obtener(datos, 'area', 'sub_area'))}",
                estilos["TextoNegrita"]
            ),
            Paragraph(
                "<b>MONEDA:</b> SOLES (S/)",
                estilos["TextoNegrita"]
            )
        ]],
        colWidths=[ancho_util * 0.34, ancho_util * 0.40, ancho_util * 0.26]
    )

    cabecera.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.7, AZUL_MEDIO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(cabecera)
    elementos.append(Spacer(1, 9))

    # --------------------------------------------------------
    # INFORMACIÓN DEL TRABAJADOR
    # --------------------------------------------------------

    elementos.append(encabezado_seccion(
        "Datos del trabajador", ancho_util
    ))

    elementos.append(Spacer(1, 3))

    datos_personales = [
        [
            Paragraph("<b>Apellidos y nombres</b>", estilos["Texto"]),
            Paragraph(texto(trabajador), estilos["Texto"]),
            Paragraph("<b>DNI</b>", estilos["Texto"]),
            Paragraph(texto(dni), estilos["Texto"])
        ],
        [
            Paragraph("<b>Fecha de nacimiento</b>", estilos["Texto"]),
            Paragraph(texto(fecha_nacimiento), estilos["Texto"]),
            Paragraph("<b>Género</b>", estilos["Texto"]),
            Paragraph(texto(genero), estilos["Texto"])
        ],
        [
            Paragraph("<b>Cargo</b>", estilos["Texto"]),
            Paragraph(texto(cargo), estilos["Texto"]),
            Paragraph("<b>Tipo de contrato</b>", estilos["Texto"]),
            Paragraph(texto(tipo_contrato), estilos["Texto"])
        ],
        [
            Paragraph("<b>Régimen pensionario</b>", estilos["Texto"]),
            Paragraph(texto(tipo_pension), estilos["Texto"]),
            Paragraph("<b>Porcentaje</b>", estilos["Texto"]),
            Paragraph(f"{porcentaje:.2f} %", estilos["Texto"])
        ],
        [
            Paragraph("<b>Domicilio</b>", estilos["Texto"]),
            Paragraph(
                texto(obtener(datos, "domicilio")),
                estilos["Texto"]
            ),
            Paragraph("<b>Condición</b>", estilos["Texto"]),
            Paragraph(
                texto(obtener(datos, "condicion", defecto="Domiciliado")),
                estilos["Texto"]
            )
        ],
        [
            Paragraph("<b>Fecha de ingreso laboral</b>", estilos["Texto"]),
            Paragraph(texto(fecha_ingreso_laboral), estilos["Texto"]),
            Paragraph("<b>Fecha de contrato</b>", estilos["Texto"]),
            Paragraph(texto(obtener(datos, "fecha_contrato")), estilos["Texto"])
        ],
        [
            Paragraph("<b>Días trabajados</b>", estilos["Texto"]),
            Paragraph(
                texto(obtener(datos, "dias_trabajados", defecto="30")),
                estilos["Texto"]
            ),
            Paragraph("<b>Nacionalidad</b>", estilos["Texto"]),
            Paragraph(texto(obtener(datos, "nacionalidad")), estilos["Texto"])
        ]
    ]

    anchos_personales = [
        ancho_util * 0.19,
        ancho_util * 0.36,
        ancho_util * 0.17,
        ancho_util * 0.28
    ]

    elementos.append(tabla_datos(
        datos_personales,
        anchos_personales
    ))

    elementos.append(Spacer(1, 10))

    # --------------------------------------------------------
    # DETALLE DE INGRESOS Y DESCUENTOS
    # --------------------------------------------------------

    elementos.append(encabezado_seccion(
        "Detalle de remuneraciones", ancho_util
    ))

    elementos.append(Spacer(1, 4))

    ingresos = [
        [
            Paragraph("<b>INGRESOS</b>", estilos["TextoNegrita"]),
            Paragraph("<b>IMPORTE</b>", estilos["TextoNegrita"])
        ],
        ["Sueldo básico", moneda(sueldo)],
        ["Asignación familiar", moneda(asignacion)],
        ["Horas extras", moneda(horas_extras)],
        ["Otros ingresos", moneda(otros_ingresos)],
    ]

    descuentos = [
        [
            Paragraph("<b>DESCUENTOS</b>", estilos["TextoNegrita"]),
            Paragraph("<b>IMPORTE</b>", estilos["TextoNegrita"])
        ],
        ["Descuento pensionario", moneda(pension)],
        ["Otros descuentos", moneda(
            obtener(datos, "otros_descuentos")
        )],
        ["Adelantos", moneda(obtener(datos, "adelantos"))],
        ["Otros conceptos", moneda(
            obtener(datos, "otros_descuentos_adicionales")
        )],
    ]

    mitad = ancho_util / 2

    tabla_ingresos = tabla_datos(
        ingresos,
        [mitad * 0.70, mitad * 0.30],
        encabezado=True
    )

    tabla_descuentos = tabla_datos(
        descuentos,
        [mitad * 0.70, mitad * 0.30],
        encabezado=True
    )

    comparativo = Table(
        [[tabla_ingresos, tabla_descuentos]],
        colWidths=[mitad, mitad]
    )

    comparativo.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    elementos.append(comparativo)
    elementos.append(Spacer(1, 8))

    # --------------------------------------------------------
    # TOTALES
    # --------------------------------------------------------

    otros_descuentos = (
        numero(obtener(datos, "otros_descuentos"))
        + numero(obtener(datos, "adelantos"))
        + numero(obtener(datos, "otros_descuentos_adicionales"))
    )

    total_descuentos = pension + otros_descuentos

    resumen = Table(
        [
            [
                Paragraph("TOTAL HABERES", estilos["TextoNegrita"]),
                Paragraph("TOTAL DESCUENTOS", estilos["TextoNegrita"])
            ],
            [
                Paragraph(f"<b>{moneda(total_ingresos)}</b>", estilos["Total"]),
                Paragraph(f"<b>{moneda(total_descuentos)}</b>", estilos["Total"])
            ]
        ],
        colWidths=[mitad, mitad]
    )

    resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_CLARO),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS_FONDO),
        ("BOX", (0, 0), (-1, -1), 0.7, GRIS_LINEA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos.append(resumen)
    elementos.append(Spacer(1, 7))

    neto_tabla = Table(
        [[
            Paragraph("NETO A PAGAR", estilos["NetoEtiqueta"])],
         [Paragraph(moneda(neto), estilos["Neto"])
        ]],
        colWidths=[ancho_util]
    )

    neto_tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_OSCURO),
        ("BOX", (0, 0), (-1, -1), 1, AZUL_OSCURO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos.append(neto_tabla)
    elementos.append(Spacer(1, 9))

    # --------------------------------------------------------
    # APORTES DEL EMPLEADOR
    # --------------------------------------------------------

    elementos.append(encabezado_seccion(
        "Aportes del empleador", ancho_util
    ))

    elementos.append(Spacer(1, 3))

    aportes = [
        [
            Paragraph("<b>CONCEPTO</b>", estilos["TextoNegrita"]),
            Paragraph("<b>IMPORTE</b>", estilos["TextoNegrita"]),
            Paragraph("<b>OBSERVACIÓN</b>", estilos["TextoNegrita"])
        ],
        [
            "EsSalud",
            moneda(essalud),
            "Aporte a cargo del empleador"
        ],
        [
            "Vida Ley",
            moneda(obtener(datos, "vida_ley")),
            "Según información registrada"
        ],
    ]

    elementos.append(tabla_datos(
        aportes,
        [ancho_util * 0.35, ancho_util * 0.22, ancho_util * 0.43],
        encabezado=True
    ))

    elementos.append(Spacer(1, 9))

    # --------------------------------------------------------
    # CONSTANCIA Y FIRMAS
    # --------------------------------------------------------

    constancia = (
        f"Certifico que he recibido de <b>{escape(EMPRESA)}</b> "
        f"el importe neto indicado en la presente boleta de pago, "
        f"correspondiente al periodo de {escape(periodo)}."
    )

    elementos.append(Paragraph(
        constancia,
        estilos["TextoPequeno"]
    ))

    elementos.append(Spacer(1, 28))

    firmas = Table(
        [
            ["", ""],
            [
                Paragraph(
                    f"<b>{escape(EMPRESA)}</b><br/>"
                    "FIRMA DEL EMPLEADOR",
                    estilos["Subtitulo"]
                ),
                Paragraph(
                    f"<b>{texto(trabajador)}</b><br/>"
                    "FIRMA CONFORME DEL TRABAJADOR",
                    estilos["Subtitulo"]
                )
            ]
        ],
        colWidths=[mitad, mitad],
        rowHeights=[1, 35]
    )

    firmas.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 0.8, AZUL_MEDIO),
        ("LINEABOVE", (1, 1), (1, 1), 0.8, AZUL_MEDIO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))

    elementos.append(firmas)

    # --------------------------------------------------------
    # SEGUNDA PÁGINA: ANEXO
    # --------------------------------------------------------

    elementos.append(PageBreak())

    elementos.append(Paragraph(
        "ANEXO DE BOLETA DE PAGO",
        estilos["TituloBoleta"]
    ))

    elementos.append(Paragraph(
        escape(EMPRESA),
        estilos["Empresa"]
    ))

    elementos.append(Paragraph(
        f"RUC: {escape(RUC)}",
        estilos["Subtitulo"]
    ))

    elementos.append(Spacer(1, 15))

    elementos.append(encabezado_seccion(
        "Identificación del trabajador", ancho_util
    ))

    elementos.append(Spacer(1, 4))

    anexo_trabajador = [
        [
            Paragraph("<b>Trabajador</b>", estilos["Texto"]),
            Paragraph(texto(trabajador), estilos["Texto"])
        ],
        [
            Paragraph("<b>DNI</b>", estilos["Texto"]),
            Paragraph(texto(dni), estilos["Texto"])
        ],
        [
            Paragraph("<b>Periodo</b>", estilos["Texto"]),
            Paragraph(escape(periodo), estilos["Texto"])
        ],
        [
            Paragraph("<b>Cargo</b>", estilos["Texto"]),
            Paragraph(texto(cargo), estilos["Texto"])
        ],
        [
            Paragraph("<b>Género</b>", estilos["Texto"]),
            Paragraph(texto(genero), estilos["Texto"])
        ],
        [
            Paragraph("<b>Tipo de contrato</b>", estilos["Texto"]),
            Paragraph(texto(tipo_contrato), estilos["Texto"])
        ],
        [
            Paragraph("<b>Fecha de ingreso laboral</b>", estilos["Texto"]),
            Paragraph(texto(fecha_ingreso_laboral), estilos["Texto"])
        ]
    ]

    elementos.append(tabla_datos(
        anexo_trabajador,
        [ancho_util * 0.25, ancho_util * 0.75]
    ))

    elementos.append(Spacer(1, 15))

    elementos.append(encabezado_seccion(
        "Indicadores", ancho_util
    ))

    elementos.append(Spacer(1, 4))

    indicadores = [
        [
            Paragraph("<b>INDICADOR</b>", estilos["TextoNegrita"]),
            Paragraph("<b>VALOR</b>", estilos["TextoNegrita"]),
            Paragraph("<b>UNIDAD</b>", estilos["TextoNegrita"])
        ],
        ["Tipo de cambio", "3.15", "Soles"],
        ["Moneda de pago", "PEN", "Sol peruano"],
        ["Periodo de cálculo", escape(periodo), "Mensual"],
    ]

    elementos.append(tabla_datos(
        indicadores,
        [
            ancho_util * 0.40,
            ancho_util * 0.35,
            ancho_util * 0.25
        ],
        encabezado=True
    ))

    elementos.append(Spacer(1, 18))

    nota = (
        "El presente documento contiene el detalle de los conceptos "
        "remunerativos, descuentos y aportes registrados en el sistema "
        "de planillas para el periodo indicado."
    )

    elementos.append(Paragraph(nota, estilos["TextoPequeno"]))

    # --------------------------------------------------------
    # PIE DE PÁGINA
    # --------------------------------------------------------

    def pie_pagina(canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(GRIS_LINEA)
        canvas.setLineWidth(0.5)
        canvas.line(
            15 * mm,
            10 * mm,
            ancho_pagina - 15 * mm,
            10 * mm
        )

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS_TEXTO)

        canvas.drawString(
            15 * mm,
            6 * mm,
            f"{EMPRESA} | RUC: {RUC}"
        )

        canvas.drawRightString(
            ancho_pagina - 15 * mm,
            6 * mm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    documento.build(
        elementos,
        onFirstPage=pie_pagina,
        onLaterPages=pie_pagina
    )

    return ruta
