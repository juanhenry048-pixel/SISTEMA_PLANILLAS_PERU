import sqlite3
import calendar
from database.conexion import conectar


# =========================================================
# PARÁMETROS LABORALES Y PREVISIONALES
# Actualizar estos valores cuando cambie la normativa/SBS.
# =========================================================

RMV_HISTORICA = {
    2025: 1130.00,
    2026: 1130.00,  # Enero a septiembre
}

RMV_DESDE_OCTUBRE_2026 = 1230.00

PORCENTAJE_ONP = 13.00
PORCENTAJE_APORTE_AFP = 10.00
PORCENTAJE_SEGURO_AFP = 1.37
TOPE_SEGURO_AFP_NOV_2026 = 12732.70

# Comisión sobre flujo publicada por SBS para devengue noviembre 2026.
# La comisión sobre saldo NO se descuenta como porcentaje del sueldo mensual.
COMISION_AFP_FLUJO = {
    "HABITAT": 1.47,
    "INTEGRA": 1.55,
    "PRIMA": 1.60,
    "PROFUTURO": 1.69,
}


def obtener_rmv(anio, mes):
    """Devuelve la RMV aplicable al periodo de la planilla."""
    anio = int(anio)
    mes = int(mes)

    if anio > 2026 or (anio == 2026 and mes >= 10):
        return RMV_DESDE_OCTUBRE_2026

    if anio >= 2025:
        return RMV_HISTORICA[2025]

    if anio >= 2022:
        return 1025.00

    raise ValueError(
        "El sistema tiene parametrizada la RMV desde 2022. "
        "Revisa el periodo solicitado."
    )


def _agregar_columna_si_falta(conexion, tabla, columna, definicion):
    columnas = {
        fila[1]
        for fila in conexion.execute(f"PRAGMA table_info({tabla})").fetchall()
    }
    if columna not in columnas:
        conexion.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


# =========================================================
# CREACIÓN Y MIGRACIÓN SEGURA DE TABLA
# No elimina ni reinicia planillas históricas.
# =========================================================

def crear_tabla_planillas():
    conexion = conectar()

    try:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS planillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajador_id INTEGER NOT NULL,
                anio INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                sueldo_basico REAL NOT NULL,
                asignacion_familiar REAL DEFAULT 0,
                horas_extras REAL DEFAULT 0,
                otros_ingresos REAL DEFAULT 0,
                total_ingresos REAL NOT NULL,
                tipo_pension TEXT NOT NULL,
                porcentaje_pension REAL NOT NULL,
                descuento_pension REAL NOT NULL,
                essalud REAL NOT NULL,
                neto_pagar REAL NOT NULL,
                FOREIGN KEY (trabajador_id)
                    REFERENCES trabajadores(id),
                UNIQUE(trabajador_id, anio, mes)
            )
        """)

        # Columnas nuevas: se agregan sin tocar los registros anteriores.
        nuevas_columnas = [
            ("afp_nombre", "TEXT"),
            ("afp_tipo_comision", "TEXT"),
            ("horas_extras_diurnas", "REAL DEFAULT 0"),
            ("horas_extras_nocturnas", "REAL DEFAULT 0"),
            ("dias_extras_diurnas", "INTEGER DEFAULT 0"),
            ("dias_extras_nocturnas", "INTEGER DEFAULT 0"),
            ("valor_hora_diurna", "REAL DEFAULT 0"),
            ("valor_hora_nocturna", "REAL DEFAULT 0"),
            ("pago_horas_diurnas", "REAL DEFAULT 0"),
            ("pago_horas_nocturnas", "REAL DEFAULT 0"),
            ("detalle_pension", "TEXT"),
            ("rmv_aplicada", "REAL DEFAULT 0"),
            ("asistencia_dias_registrados", "INTEGER DEFAULT 0"),
            ("asistencia_presentes", "INTEGER DEFAULT 0"),
            ("asistencia_faltas", "INTEGER DEFAULT 0"),
            ("asistencia_permisos", "INTEGER DEFAULT 0"),
            ("asistencia_descansos", "INTEGER DEFAULT 0"),
        ]

        for columna, definicion in nuevas_columnas:
            _agregar_columna_si_falta(
                conexion, "planillas", columna, definicion
            )

        conexion.commit()
        return True

    finally:
        conexion.close()


# =========================================================
# CÁLCULO DE HORAS EXTRAS
# =========================================================

def calcular_horas_extras(
    sueldo_basico,
    anio,
    mes,
    horas_diurnas=0,
    horas_nocturnas=0,
    dias_diurnos=1,
    dias_nocturnos=1
):
    """
    Calcula horas extras diurnas y nocturnas.
    Las dos primeras horas extras de cada tipo/día se liquidan al 25%;
    las siguientes al 35%.

    Para horas nocturnas se usa como base la remuneración mensual,
    respetando el piso mínimo nocturno de RMV + 35%.
    El sistema considera jornada ordinaria de 8 horas diarias y 30 días.
    """
    sueldo = float(sueldo_basico)
    horas_diurnas = float(horas_diurnas or 0)
    horas_nocturnas = float(horas_nocturnas or 0)
    dias_diurnos = int(dias_diurnos or 0)
    dias_nocturnos = int(dias_nocturnos or 0)

    if sueldo <= 0:
        raise ValueError("El sueldo básico debe ser mayor que cero.")

    if horas_diurnas < 0 or horas_nocturnas < 0:
        raise ValueError("Las horas extras no pueden ser negativas.")

    if horas_diurnas > 0 and dias_diurnos < 1:
        raise ValueError("Indica en cuántos días se realizaron las horas extras diurnas.")
    if horas_nocturnas > 0 and dias_nocturnos < 1:
        raise ValueError("Indica en cuántos días se realizaron las horas extras nocturnas.")

    rmv = obtener_rmv(anio, mes)
    valor_hora_diurna = sueldo / 30 / 8

    # La remuneración nocturna no puede ser inferior a RMV + 35%.
    remuneracion_nocturna_referencial = max(sueldo, rmv * 1.35)
    valor_hora_nocturna = remuneracion_nocturna_referencial / 30 / 8

    def importe_horas(cantidad_total, dias, valor_hora):
        if cantidad_total <= 0:
            return 0.0
        # La regla de 25%/35% se aplica por día, no sobre el total mensual.
        horas_promedio_dia = cantidad_total / dias
        primeras_dos_por_dia = min(horas_promedio_dia, 2)
        siguientes_por_dia = max(horas_promedio_dia - 2, 0)
        importe_diario = (
            primeras_dos_por_dia * valor_hora * 1.25
            + siguientes_por_dia * valor_hora * 1.35
        )
        return importe_diario * dias

    pago_diurno = round(
        importe_horas(horas_diurnas, dias_diurnos, valor_hora_diurna), 2
    )
    pago_nocturno = round(
        importe_horas(horas_nocturnas, dias_nocturnos, valor_hora_nocturna), 2
    )

    return {
        "horas_extras_diurnas": horas_diurnas,
        "horas_extras_nocturnas": horas_nocturnas,
        "dias_extras_diurnas": dias_diurnos,
        "dias_extras_nocturnas": dias_nocturnos,
        "valor_hora_diurna": round(valor_hora_diurna, 4),
        "valor_hora_nocturna": round(valor_hora_nocturna, 4),
        "pago_horas_diurnas": pago_diurno,
        "pago_horas_nocturnas": pago_nocturno,
        "horas_extras": round(pago_diurno + pago_nocturno, 2),
        "rmv_aplicada": rmv,
    }


# =========================================================
# CÁLCULO DE PENSIÓN
# =========================================================

def calcular_descuento_pension(
    base_pensionable,
    tipo_pension,
    anio,
    mes,
    porcentaje_afp=None,
    afp_nombre=None,
    afp_tipo_comision="FLUJO"
):
    tipo = str(tipo_pension).strip().upper()
    base = float(base_pensionable)

    if base < 0:
        raise ValueError("La base pensionable no puede ser negativa.")

    if tipo == "ONP":
        porcentaje = PORCENTAJE_ONP
        descuento = round(base * porcentaje / 100, 2)
        return {
            "porcentaje_pension": porcentaje,
            "descuento_pension": descuento,
            "detalle_pension": "ONP 13%",
            "afp_nombre": None,
            "afp_tipo_comision": None,
        }

    if tipo != "AFP":
        raise ValueError("Selecciona ONP o AFP.")

    # Compatibilidad temporal con la interfaz anterior.
    # Si llega porcentaje_afp, se respeta el porcentaje que el usuario indicó.
    if porcentaje_afp is not None:
        porcentaje = float(porcentaje_afp)
        if not 0 < porcentaje <= 100:
            raise ValueError("El porcentaje AFP debe ser mayor que 0 y no superar 100.")

        return {
            "porcentaje_pension": porcentaje,
            "descuento_pension": round(base * porcentaje / 100, 2),
            "detalle_pension": f"AFP porcentaje ingresado: {porcentaje:.2f}%",
            "afp_nombre": afp_nombre,
            "afp_tipo_comision": afp_tipo_comision,
        }

    nombre = str(afp_nombre or "").strip().upper()
    tipo_comision = str(afp_tipo_comision or "FLUJO").strip().upper()

    if nombre not in COMISION_AFP_FLUJO:
        raise ValueError(
            "Para calcular AFP automáticamente debes seleccionar "
            "Habitat, Integra, Prima o Profuturo."
        )

    aporte_fondo = base * PORCENTAJE_APORTE_AFP / 100
    base_seguro = min(base, TOPE_SEGURO_AFP_NOV_2026)
    prima_seguro = base_seguro * PORCENTAJE_SEGURO_AFP / 100

    if tipo_comision == "FLUJO":
        comision = base * COMISION_AFP_FLUJO[nombre] / 100
    elif tipo_comision == "SALDO":
        # La comisión sobre saldo se cobra sobre el fondo acumulado,
        # no como porcentaje mensual de la remuneración.
        comision = 0.0
    else:
        raise ValueError("Tipo de comisión AFP no válido: FLUJO o SALDO.")

    descuento = round(aporte_fondo + prima_seguro + comision, 2)
    porcentaje_equivalente = (
        (descuento / base) * 100 if base else 0.0
    )

    detalle = (
        f"AFP {nombre}: fondo 10% + seguro "
        f"{PORCENTAJE_SEGURO_AFP:.2f}%"
    )
    if tipo_comision == "FLUJO":
        detalle += f" + comisión flujo {COMISION_AFP_FLUJO[nombre]:.2f}%"
    else:
        detalle += " + comisión sobre saldo (no descontada del sueldo)"

    return {
        "porcentaje_pension": round(porcentaje_equivalente, 4),
        "descuento_pension": descuento,
        "detalle_pension": detalle,
        "afp_nombre": nombre,
        "afp_tipo_comision": tipo_comision,
    }


# =========================================================
# RESUMEN DE ASISTENCIA PARA HISTORIAL DE PLANILLA
# Se guarda una fotografía del periodo; no genera descuentos.
# =========================================================

def obtener_resumen_asistencia(conexion, trabajador_id, anio, mes):
    """Cuenta la asistencia del trabajador en el mes indicado."""
    ultimo_dia = calendar.monthrange(int(anio), int(mes))[1]
    fecha_inicio = f"{int(anio):04d}-{int(mes):02d}-01"
    fecha_fin = f"{int(anio):04d}-{int(mes):02d}-{ultimo_dia:02d}"

    # Si todavía no existe la tabla de asistencia, devuelve ceros
    # para mantener la compatibilidad con instalaciones anteriores.
    existe = conexion.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'asistencias'
    """).fetchone()

    if not existe:
        return {
            "asistencia_dias_registrados": 0,
            "asistencia_presentes": 0,
            "asistencia_faltas": 0,
            "asistencia_permisos": 0,
            "asistencia_descansos": 0,
        }

    fila = conexion.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(CASE WHEN UPPER(TRIM(estado)) = 'PRESENTE' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN UPPER(TRIM(estado)) IN ('FALTA', 'AUSENTE') THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN UPPER(TRIM(estado)) = 'PERMISO' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN UPPER(TRIM(estado)) = 'DESCANSO' THEN 1 ELSE 0 END), 0)
        FROM asistencias
        WHERE trabajador_id = ?
          AND fecha >= ?
          AND fecha <= ?
    """, (trabajador_id, fecha_inicio, fecha_fin)).fetchone()

    return {
        "asistencia_dias_registrados": int(fila[0] or 0),
        "asistencia_presentes": int(fila[1] or 0),
        "asistencia_faltas": int(fila[2] or 0),
        "asistencia_permisos": int(fila[3] or 0),
        "asistencia_descansos": int(fila[4] or 0),
    }


# =========================================================
# CÁLCULO GENERAL DE PLANILLA
# =========================================================

def calcular_planilla(
    trabajador_id,
    anio,
    mes,
    tipo_pension,
    asignacion_familiar=0,
    horas_extras=0,
    otros_ingresos=0,
    porcentaje_afp=None,
    *,
    tiene_asignacion_familiar=None,
    horas_extras_diurnas=0,
    horas_extras_nocturnas=0,
    dias_extras_diurnas=1,
    dias_extras_nocturnas=1,
    afp_nombre=None,
    afp_tipo_comision="FLUJO"
):
    conexion = conectar()

    try:
        anio = int(anio)
        mes = int(mes)

        if not 1 <= mes <= 12:
            raise ValueError("El mes debe estar entre 1 y 12.")

        if not 2000 <= anio <= 2100:
            raise ValueError("Ingresa un año válido.")

        trabajador = conexion.execute("""
            SELECT
                id,
                dni,
                nombres,
                apellidos,
                sueldo_basico
            FROM trabajadores
            WHERE id = ? AND estado = 'ACTIVO'
        """, (trabajador_id,)).fetchone()

        if not trabajador:
            raise ValueError("Trabajador no encontrado o inactivo.")

        sueldo = float(trabajador[4])

        if sueldo <= 0:
            raise ValueError("El sueldo básico del trabajador no es válido.")

        rmv = obtener_rmv(anio, mes)

        # Asignación familiar: 10% de RMV si el trabajador tiene derecho.
        if tiene_asignacion_familiar is not None:
            if isinstance(tiene_asignacion_familiar, str):
                tiene_asignacion_familiar = (
                    tiene_asignacion_familiar.strip().upper()
                    in ("SI", "SÍ", "1", "TRUE", "YES")
                )
            asignacion = round(rmv * 0.10, 2) if tiene_asignacion_familiar else 0.0
        else:
            # Compatibilidad con la interfaz anterior, que enviaba un importe.
            asignacion = float(asignacion_familiar or 0)

        if asignacion < 0:
            raise ValueError("La asignación familiar no puede ser negativa.")

        # Si se proporcionan horas detalladas, el sistema las calcula.
        # Si no, conserva el importe de horas_extras de la interfaz antigua.
        if float(horas_extras_diurnas or 0) > 0 or float(horas_extras_nocturnas or 0) > 0:
            detalle_horas = calcular_horas_extras(
                sueldo,
                anio,
                mes,
                horas_extras_diurnas,
                horas_extras_nocturnas,
                dias_extras_diurnas,
                dias_extras_nocturnas
            )
            importe_horas = detalle_horas["horas_extras"]
        else:
            detalle_horas = calcular_horas_extras(sueldo, anio, mes, 0, 0)
            importe_horas = float(horas_extras or 0)

        otros = float(otros_ingresos or 0)

        if importe_horas < 0 or otros < 0:
            raise ValueError("Los ingresos adicionales no pueden ser negativos.")

        ingresos = round(sueldo + asignacion + importe_horas + otros, 2)

        # Para ONP/AFP, la base pensionable considera remuneraciones
        # computables incluidas en esta planilla.
        pension = calcular_descuento_pension(
            ingresos,
            tipo_pension,
            anio,
            mes,
            porcentaje_afp=porcentaje_afp,
            afp_nombre=afp_nombre,
            afp_tipo_comision=afp_tipo_comision
        )

        descuento = pension["descuento_pension"]
        essalud = round(ingresos * 0.09, 2)
        neto = round(ingresos - descuento, 2)

        resultado = {
            "trabajador_id": trabajador[0],
            "dni": trabajador[1],
            "nombres": trabajador[2],
            "apellidos": trabajador[3],
            "anio": anio,
            "mes": mes,
            "sueldo_basico": round(sueldo, 2),
            "asignacion_familiar": round(asignacion, 2),
            "horas_extras": round(importe_horas, 2),
            "otros_ingresos": round(otros, 2),
            "total_ingresos": ingresos,
            "tipo_pension": str(tipo_pension).strip().upper(),
            "porcentaje_pension": pension["porcentaje_pension"],
            "descuento_pension": descuento,
            "essalud": essalud,
            "neto_pagar": neto,
            "afp_nombre": pension["afp_nombre"],
            "afp_tipo_comision": pension["afp_tipo_comision"],
            "detalle_pension": pension["detalle_pension"],
            "horas_extras_diurnas": detalle_horas["horas_extras_diurnas"],
            "horas_extras_nocturnas": detalle_horas["horas_extras_nocturnas"],
            "valor_hora_diurna": detalle_horas["valor_hora_diurna"],
            "valor_hora_nocturna": detalle_horas["valor_hora_nocturna"],
            "pago_horas_diurnas": detalle_horas["pago_horas_diurnas"],
            "pago_horas_nocturnas": detalle_horas["pago_horas_nocturnas"],
            "rmv_aplicada": rmv,
        }

        # Se conserva el resumen como fotografía de la asistencia del periodo.
        # Importante: no modifica ingresos, descuentos ni neto a pagar.
        resultado.update(
            obtener_resumen_asistencia(
                conexion, trabajador[0], anio, mes
            )
        )

        return resultado

    finally:
        conexion.close()


# =========================================================
# GUARDAR PLANILLA
# =========================================================

def guardar_planilla(datos):
    conexion = conectar()

    try:
        # Garantiza que existan las columnas nuevas antes del INSERT.
        crear_tabla_planillas_en_conexion(conexion)

        conexion.execute("""
            INSERT INTO planillas (
                trabajador_id,
                anio,
                mes,
                sueldo_basico,
                asignacion_familiar,
                horas_extras,
                otros_ingresos,
                total_ingresos,
                tipo_pension,
                porcentaje_pension,
                descuento_pension,
                essalud,
                neto_pagar,
                afp_nombre,
                afp_tipo_comision,
                horas_extras_diurnas,
                horas_extras_nocturnas,
                dias_extras_diurnas,
                dias_extras_nocturnas,
                valor_hora_diurna,
                valor_hora_nocturna,
                pago_horas_diurnas,
                pago_horas_nocturnas,
                detalle_pension,
                rmv_aplicada,
                asistencia_dias_registrados,
                asistencia_presentes,
                asistencia_faltas,
                asistencia_permisos,
                asistencia_descansos
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos["trabajador_id"],
            datos["anio"],
            datos["mes"],
            datos["sueldo_basico"],
            datos["asignacion_familiar"],
            datos["horas_extras"],
            datos["otros_ingresos"],
            datos["total_ingresos"],
            datos["tipo_pension"],
            datos["porcentaje_pension"],
            datos["descuento_pension"],
            datos["essalud"],
            datos["neto_pagar"],
            datos.get("afp_nombre"),
            datos.get("afp_tipo_comision"),
            datos.get("horas_extras_diurnas", 0),
            datos.get("horas_extras_nocturnas", 0),
            datos.get("dias_extras_diurnas", 0),
            datos.get("dias_extras_nocturnas", 0),
            datos.get("valor_hora_diurna", 0),
            datos.get("valor_hora_nocturna", 0),
            datos.get("pago_horas_diurnas", 0),
            datos.get("pago_horas_nocturnas", 0),
            datos.get("detalle_pension"),
            datos.get("rmv_aplicada", 0),
            datos.get("asistencia_dias_registrados", 0),
            datos.get("asistencia_presentes", 0),
            datos.get("asistencia_faltas", 0),
            datos.get("asistencia_permisos", 0),
            datos.get("asistencia_descansos", 0),
        ))

        conexion.commit()
        return True, "Planilla guardada correctamente."

    except sqlite3.IntegrityError:
        return False, "Ya existe una planilla para este trabajador y periodo."

    except (sqlite3.Error, ValueError) as error:
        return False, f"Error al guardar: {error}"

    finally:
        conexion.close()


def crear_tabla_planillas_en_conexion(conexion):
    """Asegura columnas nuevas usando la conexión ya abierta."""
    columnas = [
        ("afp_nombre", "TEXT"),
        ("afp_tipo_comision", "TEXT"),
        ("horas_extras_diurnas", "REAL DEFAULT 0"),
        ("horas_extras_nocturnas", "REAL DEFAULT 0"),
        ("dias_extras_diurnas", "INTEGER DEFAULT 0"),
        ("dias_extras_nocturnas", "INTEGER DEFAULT 0"),
        ("valor_hora_diurna", "REAL DEFAULT 0"),
        ("valor_hora_nocturna", "REAL DEFAULT 0"),
        ("pago_horas_diurnas", "REAL DEFAULT 0"),
        ("pago_horas_nocturnas", "REAL DEFAULT 0"),
        ("detalle_pension", "TEXT"),
        ("rmv_aplicada", "REAL DEFAULT 0"),
        ("asistencia_dias_registrados", "INTEGER DEFAULT 0"),
        ("asistencia_presentes", "INTEGER DEFAULT 0"),
        ("asistencia_faltas", "INTEGER DEFAULT 0"),
        ("asistencia_permisos", "INTEGER DEFAULT 0"),
        ("asistencia_descansos", "INTEGER DEFAULT 0"),
    ]
    for columna, definicion in columnas:
        _agregar_columna_si_falta(
            conexion, "planillas", columna, definicion
        )


# =========================================================
# LISTAR PLANILLAS
# =========================================================

def listar_planillas(anio=None, mes=None):
    conexion = conectar()

    try:
        consulta = """
            SELECT
                p.id,
                t.dni,
                t.nombres,
                t.apellidos,
                p.anio,
                p.mes,
                p.total_ingresos,
                p.descuento_pension,
                p.essalud,
                p.neto_pagar
            FROM planillas p
            INNER JOIN trabajadores t
                ON p.trabajador_id = t.id
            WHERE 1=1
        """

        parametros = []

        if anio is not None:
            consulta += " AND p.anio = ?"
            parametros.append(anio)

        if mes is not None:
            consulta += " AND p.mes = ?"
            parametros.append(mes)

        consulta += " ORDER BY p.anio DESC, p.mes DESC, p.id DESC"

        return conexion.execute(consulta, parametros).fetchall()

    finally:
        conexion.close()


# =========================================================
# OBTENER PLANILLA PARA BOLETA PDF
# =========================================================

def obtener_planilla_por_id(planilla_id):
    conexion = conectar()

    try:
        consulta = """
            SELECT
                p.id,
                t.id,
                t.dni,
                t.nombres,
                t.apellidos,
                t.cargo,
                t.fecha_nacimiento,
                t.fecha_ingreso_laboral,
                t.fecha_contrato,
                t.genero,
                t.nacionalidad,
                t.domicilio,
                t.condicion,
                t.area,
                t.sub_area,
                t.tipo_contrato,
                t.centro_costo,
                t.tipo_trabajador,
                t.regimen_salud,
                t.cuspp,
                p.anio,
                p.mes,
                p.sueldo_basico,
                p.asignacion_familiar,
                p.horas_extras,
                p.otros_ingresos,
                p.total_ingresos,
                p.tipo_pension,
                p.porcentaje_pension,
                p.descuento_pension,
                p.essalud,
                p.neto_pagar,
                p.afp_nombre,
                p.afp_tipo_comision,
                p.horas_extras_diurnas,
                p.horas_extras_nocturnas,
                p.dias_extras_diurnas,
                p.dias_extras_nocturnas,
                p.valor_hora_diurna,
                p.valor_hora_nocturna,
                p.pago_horas_diurnas,
                p.pago_horas_nocturnas,
                p.detalle_pension,
                p.rmv_aplicada,
                p.asistencia_dias_registrados,
                p.asistencia_presentes,
                p.asistencia_faltas,
                p.asistencia_permisos,
                p.asistencia_descansos
            FROM planillas p
            INNER JOIN trabajadores t
                ON p.trabajador_id = t.id
            WHERE p.id = ?
        """

        resultado = conexion.execute(
            consulta, (planilla_id,)
        ).fetchone()

        if resultado is None:
            return None

        return {
            "id": resultado[0],
            "trabajador_id": resultado[1],
            "dni": resultado[2],
            "nombres": resultado[3],
            "apellidos": resultado[4],
            "cargo": resultado[5],
            "fecha_nacimiento": resultado[6],
            "fecha_ingreso": resultado[7],
            "fecha_ingreso_laboral": resultado[7],
            "fecha_contrato": resultado[8],
            "genero": resultado[9],
            "nacionalidad": resultado[10],
            "domicilio": resultado[11],
            "condicion": resultado[12],
            "area": resultado[13],
            "sub_area": resultado[14],
            "tipo_contrato": resultado[15],
            "centro_costo": resultado[16],
            "tipo_trabajador": resultado[17],
            "regimen_salud": resultado[18],
            "cuspp": resultado[19],
            "anio": resultado[20],
            "mes": resultado[21],
            "sueldo_basico": resultado[22],
            "asignacion_familiar": resultado[23],
            "horas_extras": resultado[24],
            "otros_ingresos": resultado[25],
            "total_ingresos": resultado[26],
            "tipo_pension": resultado[27],
            "porcentaje_pension": resultado[28],
            "descuento_pension": resultado[29],
            "essalud": resultado[30],
            "neto_pagar": resultado[31],
            "afp_nombre": resultado[32],
            "afp_tipo_comision": resultado[33],
            "horas_extras_diurnas": resultado[34],
            "horas_extras_nocturnas": resultado[35],
            "dias_extras_diurnas": resultado[36],
            "dias_extras_nocturnas": resultado[37],
            "valor_hora_diurna": resultado[38],
            "valor_hora_nocturna": resultado[39],
            "pago_horas_diurnas": resultado[40],
            "pago_horas_nocturnas": resultado[41],
            "detalle_pension": resultado[42],
            "rmv_aplicada": resultado[43],
            "asistencia_dias_registrados": resultado[44],
            "asistencia_presentes": resultado[45],
            "asistencia_faltas": resultado[46],
            "asistencia_permisos": resultado[47],
            "asistencia_descansos": resultado[48],
            "otros_descuentos": 0,
            "adelantos": 0,
        }

    finally:
        conexion.close()
