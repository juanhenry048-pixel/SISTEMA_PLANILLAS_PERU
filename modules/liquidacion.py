import sqlite3
from datetime import date, datetime, timedelta
from database.conexion import conectar


def _fecha(valor, nombre):
    try:
        return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"{nombre}: usa el formato AAAA-MM-DD.")


def _dias_30_360(inicio, fin):
    """Días comerciales 30/360 usados para la prorrata mensual laboral."""
    return max(0, (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30
               + (fin.day - inicio.day) + 1)


def _meses_dias_30_360(inicio, fin):
    dias = _dias_30_360(inicio, fin)
    return divmod(dias, 30)


def _numero(valor, nombre, minimo=0):
    try:
        n = float(valor or 0)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre}: ingresa un importe numérico válido.")
    if n < minimo:
        raise ValueError(f"{nombre}: no puede ser menor que {minimo}.")
    return n


def crear_tabla_liquidaciones():
    con = conectar()
    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS liquidaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajador_id INTEGER NOT NULL,
                fecha_cese TEXT NOT NULL,
                regimen_laboral TEXT NOT NULL,
                datos_json TEXT NOT NULL,
                total_bruto REAL NOT NULL,
                descuentos REAL NOT NULL DEFAULT 0,
                neto REAL NOT NULL,
                creado_en TEXT NOT NULL,
                FOREIGN KEY(trabajador_id) REFERENCES trabajadores(id)
            )
        """)
        con.commit()
        return True
    finally:
        con.close()


def listar_trabajadores_liquidacion():
    con = conectar()
    try:
        filas = con.execute("""
            SELECT id, dni, nombres, apellidos, cargo, sueldo_basico,
                   fecha_ingreso_laboral, fecha_ingreso, estado, regimen_salud
            FROM trabajadores ORDER BY apellidos, nombres
        """).fetchall()
        return [dict(zip(("id", "dni", "nombres", "apellidos", "cargo", "sueldo_basico",
                          "fecha_ingreso_laboral", "fecha_ingreso", "estado", "regimen_salud"), f))
                for f in filas]
    finally:
        con.close()


def calcular_liquidacion(datos):
    """Estimación para régimen privado general, micro o pequeña empresa REMYPE.

    Los saldos pendientes y pagos previos se ingresan manualmente para evitar
    duplicar depósitos o descansos ya gozados. No calcula indemnización por despido.
    """
    ingreso = _fecha(datos.get("fecha_ingreso"), "Fecha de ingreso")
    cese = _fecha(datos.get("fecha_cese"), "Fecha de cese")
    if cese < ingreso:
        raise ValueError("La fecha de cese no puede ser anterior al ingreso.")

    regimen = str(datos.get("regimen_laboral", "GENERAL")).upper()
    if regimen not in ("GENERAL", "PEQUEÑA EMPRESA", "MICROEMPRESA"):
        raise ValueError("Selecciona un régimen laboral válido.")

    sueldo = _numero(datos.get("sueldo"), "Sueldo básico")
    asignacion = _numero(datos.get("asignacion_familiar"), "Asignación familiar")
    otros_computables = _numero(datos.get("otros_computables"), "Otros conceptos computables")
    ultima_grati = _numero(datos.get("ultima_gratificacion"), "Última gratificación")
    vacaciones_pendientes = _numero(datos.get("vacaciones_pendientes"), "Vacaciones pendientes (días)")
    vacaciones_tomadas = _numero(datos.get("vacaciones_tomadas"), "Vacaciones gozadas en el periodo")
    sueldo_pendiente = _numero(datos.get("sueldo_pendiente"), "Remuneración pendiente")
    otros_pendientes = _numero(datos.get("otros_pendientes"), "Otros pagos pendientes")
    descuentos = _numero(datos.get("descuentos"), "Descuentos autorizados")
    dias_indemnizables = _numero(datos.get("dias_vacaciones_indemnizables"), "Días sujetos a indemnización vacacional")

    remuneracion = sueldo + asignacion + otros_computables
    if remuneracion <= 0:
        raise ValueError("La remuneración computable debe ser mayor que cero.")

    # CTS: desde el último periodo de depósito (1 de mayo o 1 de noviembre).
    inicio_cts = _fecha(datos.get("inicio_periodo_cts"), "Inicio del periodo CTS")
    if inicio_cts > cese:
        raise ValueError("El inicio del periodo CTS no puede ser posterior al cese.")
    dias_cts = _dias_30_360(inicio_cts, cese)
    meses_cts, rem_cts = divmod(dias_cts, 30)
    rc_cts = remuneracion + (ultima_grati / 6.0)
    factor_cts = 1.0 if regimen == "GENERAL" else (0.5 if regimen == "PEQUEÑA EMPRESA" else 0.0)
    cts = (rc_cts * (meses_cts / 12 + rem_cts / 360)) * factor_cts
    if (cese - ingreso).days < 30:
        cts = 0.0

    # Gratificación trunca: solo meses calendario completos del semestre.
    inicio_semestre = date(cese.year, 1 if cese.month <= 6 else 7, 1)
    if ingreso > inicio_semestre:
        inicio_semestre = ingreso
    meses_grati = 0
    cursor = date(inicio_semestre.year, inicio_semestre.month, 1)
    while True:
        siguiente = date(cursor.year + (cursor.month // 12), cursor.month % 12 + 1, 1)
        fin_mes = siguiente - timedelta(days=1)
        if fin_mes <= cese and cursor >= date(cese.year, 1 if cese.month <= 6 else 7, 1) and cursor >= ingreso:
            meses_grati += 1
        if siguiente > cese or siguiente.month == 1 and siguiente.year > cese.year:
            break
        cursor = siguiente
    factor_grati = 1.0 if regimen == "GENERAL" else (0.5 if regimen == "PEQUEÑA EMPRESA" else 0.0)
    gratificacion = remuneracion * meses_grati / 6 * factor_grati
    bonificacion_pct = 0.0675 if str(datos.get("regimen_salud", "ESSALUD")).upper() == "EPS" else 0.09
    bonificacion = gratificacion * bonificacion_pct

    # Vacaciones: el usuario indica el inicio del récord y días ya gozados.
    inicio_vac = _fecha(datos.get("inicio_periodo_vacaciones"), "Inicio del periodo vacacional")
    if inicio_vac > cese:
        raise ValueError("El inicio del periodo vacacional no puede ser posterior al cese.")
    dias_periodo = _dias_30_360(inicio_vac, cese)
    dias_anuales = 30 if regimen == "GENERAL" else 15
    dias_generados = dias_periodo * dias_anuales / 360
    dias_truncos = max(0.0, dias_generados - vacaciones_tomadas)
    dias_vacaciones_total = vacaciones_pendientes + dias_truncos
    vacaciones = remuneracion / 30 * dias_vacaciones_total
    indemnizacion_vacacional = remuneracion / 30 * dias_indemnizables

    conceptos = {
        "CTS trunca": round(cts, 2),
        "Gratificación trunca": round(gratificacion, 2),
        "Bonificación extraordinaria": round(bonificacion, 2),
        "Vacaciones pendientes y truncas": round(vacaciones, 2),
        "Indemnización vacacional (ingreso manual)": round(indemnizacion_vacacional, 2),
        "Remuneración pendiente": round(sueldo_pendiente, 2),
        "Otros pagos pendientes": round(otros_pendientes, 2),
    }
    bruto = round(sum(conceptos.values()), 2)
    neto = round(bruto - descuentos, 2)
    if neto < 0:
        raise ValueError("Los descuentos superan el total bruto de la liquidación.")

    return {
        "trabajador_id": int(datos["trabajador_id"]),
        "dni": str(datos.get("dni", "")),
        "trabajador": str(datos.get("trabajador", "")),
        "cargo": str(datos.get("cargo", "")),
        "fecha_ingreso": ingreso.isoformat(),
        "fecha_cese": cese.isoformat(),
        "regimen_laboral": regimen,
        "regimen_salud": str(datos.get("regimen_salud", "ESSALUD")),
        "sueldo": round(sueldo, 2),
        "asignacion_familiar": round(asignacion, 2),
        "remuneracion_computable": round(remuneracion, 2),
        "inicio_periodo_cts": inicio_cts.isoformat(),
        "dias_cts": dias_cts,
        "ultima_gratificacion": round(ultima_grati, 2),
        "meses_gratificacion": meses_grati,
        "inicio_periodo_vacaciones": inicio_vac.isoformat(),
        "dias_vacaciones_generados": round(dias_generados, 2),
        "dias_vacaciones_tomados": round(vacaciones_tomadas, 2),
        "dias_vacaciones_pendientes": round(vacaciones_pendientes, 2),
        "dias_vacaciones_truncos": round(dias_truncos, 2),
        "descuentos": round(descuentos, 2),
        "conceptos": conceptos,
        "total_bruto": bruto,
        "total_descuentos": round(descuentos, 2),
        "neto": neto,
        "observaciones": str(datos.get("observaciones", "")),
        "nota_calculo": "Estimación sujeta a validación del régimen aplicable, récord vacacional, remuneraciones computables y pagos/depositos previos. No incluye indemnización por despido arbitrario ni utilidades.",
    }


def guardar_liquidacion(resultado):
    import json
    crear_tabla_liquidaciones()
    con = conectar()
    try:
        cur = con.execute("""
            INSERT INTO liquidaciones
            (trabajador_id, fecha_cese, regimen_laboral, datos_json, total_bruto, descuentos, neto, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (resultado["trabajador_id"], resultado["fecha_cese"], resultado["regimen_laboral"],
              json.dumps(resultado, ensure_ascii=False), resultado["total_bruto"],
              resultado["total_descuentos"], resultado["neto"], datetime.now().isoformat(timespec="seconds")))
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def listar_liquidaciones():
    import json
    crear_tabla_liquidaciones()
    con = conectar()
    try:
        filas = con.execute("""
            SELECT l.id, t.dni, t.nombres, t.apellidos, l.fecha_cese,
                   l.total_bruto, l.descuentos, l.neto
            FROM liquidaciones l JOIN trabajadores t ON t.id=l.trabajador_id
            ORDER BY l.id DESC
        """).fetchall()
        return filas
    finally:
        con.close()
