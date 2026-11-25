from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from xml.sax.saxutils import escape


def _documento(ruta, titulo, subtitulo, filas, texto_final=None):
    doc = SimpleDocTemplate(ruta, pagesize=A4, rightMargin=2.2*cm, leftMargin=2.2*cm,
                            topMargin=2.0*cm, bottomMargin=2.0*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TituloCentro', parent=styles['Title'], alignment=TA_CENTER,
                              textColor=colors.HexColor('#172554'), fontSize=16, leading=20, spaceAfter=8))
    styles.add(ParagraphStyle(name='SubCentro', parent=styles['Normal'], alignment=TA_CENTER,
                              fontSize=10, textColor=colors.HexColor('#475569'), spaceAfter=22))
    styles.add(ParagraphStyle(name='CuerpoJustificado', parent=styles['BodyText'], alignment=TA_JUSTIFY,
                              fontSize=10.5, leading=17, spaceAfter=12))
    story = [Paragraph(escape(titulo), styles['TituloCentro']), Paragraph(escape(subtitulo), styles['SubCentro'])]
    data = [[Paragraph(f'<b>{escape(str(k))}</b>', styles['BodyText']),
             Paragraph(escape(str(v if v not in (None, '') else 'No consignado')), styles['BodyText'])]
            for k, v in filas]
    tabla = Table(data, colWidths=[5.0*cm, 10.0*cm], hAlign='CENTER')
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EFF6FF')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 9), ('RIGHTPADDING', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story += [tabla, Spacer(1, 22)]
    if texto_final:
        story.append(Paragraph(escape(texto_final), styles['CuerpoJustificado']))
    story += [Spacer(1, 42), Paragraph('________________________________________', styles['Normal']),
              Paragraph('Firma y sello del empleador', styles['Normal'])]
    doc.build(story)


def generar_certificado_trabajo(datos, empresa, ruc, representante, cargo_representante, fecha_emision, ruta):
    nombre = f"{datos.get('nombres','')} {datos.get('apellidos','')}".strip()
    fecha_ingreso = datos.get('fecha_ingreso_laboral') or datos.get('fecha_ingreso') or 'No consignada'
    cargo = datos.get('cargo') or 'No consignado'
    texto = (f"Por medio del presente, {empresa} deja constancia de que {nombre}, identificado(a) "
             f"con DNI N.° {datos.get('dni','')}, prestó servicios en la organización desempeñando el cargo de "
             f"{cargo}, desde el {fecha_ingreso} hasta el {datos.get('fecha_cese') or 'la fecha de emisión, si continúa laborando'}. "
             f"Se expide el presente documento a solicitud del interesado para los fines que estime convenientes.")
    filas = [('Empresa', empresa), ('RUC', ruc), ('Trabajador', nombre), ('DNI', datos.get('dni')),
             ('Cargo', cargo), ('Área', datos.get('area')), ('Fecha de ingreso', fecha_ingreso),
             ('Fecha de cese', datos.get('fecha_cese') or 'Vínculo laboral vigente'),
             ('Fecha de emisión', fecha_emision), ('Representante', representante),
             ('Cargo del representante', cargo_representante)]
    _documento(ruta, 'CERTIFICADO DE TRABAJO', 'CONSTANCIA DE SERVICIOS LABORALES', filas, texto)


def generar_constancia_quinta(datos, empresa, ruc, anio, renta_bruta, retencion, fecha_emision, ruta):
    nombre = f"{datos.get('nombres','')} {datos.get('apellidos','')}".strip()
    filas = [('Empresa', empresa), ('RUC', ruc), ('Trabajador', nombre), ('DNI', datos.get('dni')),
             ('Ejercicio', anio), ('Rentas brutas de quinta categoría (S/)', f'{renta_bruta:,.2f}'),
             ('Retenciones de quinta categoría (S/)', f'{retencion:,.2f}'),
             ('Fecha de emisión', fecha_emision)]
    texto = ('La información de rentas y retenciones consignada en este documento fue ingresada por el usuario '
             'a partir de los registros de la empresa. Verifique su concordancia con las planillas, boletas, '
             'declaraciones y constancias tributarias antes de emitir o utilizar este documento. '
             'Este reporte no sustituye la declaración ni la constancia oficial que corresponda.')
    _documento(ruta, 'CONSTANCIA DE RENTAS Y RETENCIONES', 'QUINTA CATEGORÍA - EJERCICIO ANUAL', filas, texto)
