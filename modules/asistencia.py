import sqlite3
from datetime import datetime
from database.conexion import conectar

# Estados permitidos para el control de asistencia.
ESTADOS_ASISTENCIA = ["PRESENTE", "FALTA", "DESCANSO", "PERMISO"]


def crear_tabla_asistencia():
    """Crea la tabla de asistencia sin eliminar datos existentes."""
    conexion = conectar()
    try:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajador_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                hora_entrada TEXT,
                hora_salida TEXT,
                estado TEXT NOT NULL DEFAULT 'PRESENTE',
                observaciones TEXT,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id),
                UNIQUE (trabajador_id, fecha)
            )
        """)
        conexion.commit()
        return True
    except sqlite3.Error as error:
        conexion.rollback()
        raise RuntimeError(f"Error al crear la tabla de asistencia: {error}")
    finally:
        conexion.close()


def validar_fecha(fecha):
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("La fecha debe tener formato AAAA-MM-DD.")


def validar_hora(hora):
    if hora in (None, ""):
        return
    try:
        datetime.strptime(hora, "%H:%M")
    except (ValueError, TypeError):
        raise ValueError("La hora debe tener formato HH:MM.")


def calcular_horas_trabajadas(hora_entrada, hora_salida):
    if not hora_entrada or not hora_salida:
        return 0.0
    entrada = datetime.strptime(hora_entrada, "%H:%M")
    salida = datetime.strptime(hora_salida, "%H:%M")
    diferencia = (salida - entrada).total_seconds() / 3600
    if diferencia < 0:
        diferencia += 24
    return round(diferencia, 2)


def registrar_asistencia(
    trabajador_id, fecha, hora_entrada=None, hora_salida=None,
    estado="PRESENTE", observaciones=""
):
    validar_fecha(fecha)
    validar_hora(hora_entrada)
    validar_hora(hora_salida)
    estado = str(estado).strip().upper()

    if estado not in ESTADOS_ASISTENCIA:
        raise ValueError("Selecciona un estado de asistencia válido.")
    if estado == "PRESENTE" and not hora_entrada:
        raise ValueError("Debes registrar la hora de entrada del trabajador.")
    if hora_salida and not hora_entrada:
        raise ValueError("No puedes registrar una salida sin una entrada.")

    conexion = conectar()
    try:
        trabajador = conexion.execute(
            "SELECT id FROM trabajadores WHERE id = ?", (trabajador_id,)
        ).fetchone()
        if not trabajador:
            raise ValueError("El trabajador no existe.")

        conexion.execute("""
            INSERT INTO asistencias (
                trabajador_id, fecha, hora_entrada, hora_salida,
                estado, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trabajador_id, fecha, hora_entrada, hora_salida,
            estado, observaciones
        ))
        conexion.commit()
        return True, "Asistencia registrada correctamente."
    except sqlite3.IntegrityError:
        return False, (
            "Ya existe un registro de asistencia para este trabajador "
            "en esa fecha."
        )
    except sqlite3.Error as error:
        conexion.rollback()
        return False, f"Error al registrar asistencia: {error}"
    finally:
        conexion.close()


def actualizar_asistencia(
    asistencia_id, fecha, hora_entrada=None, hora_salida=None,
    estado="PRESENTE", observaciones=""
):
    validar_fecha(fecha)
    validar_hora(hora_entrada)
    validar_hora(hora_salida)
    estado = str(estado).strip().upper()

    if estado not in ESTADOS_ASISTENCIA:
        raise ValueError("Estado de asistencia inválido.")
    if estado == "PRESENTE" and not hora_entrada:
        raise ValueError("La entrada es obligatoria para un presente.")
    if hora_salida and not hora_entrada:
        raise ValueError("No puedes registrar salida sin entrada.")

    conexion = conectar()
    try:
        cursor = conexion.execute("""
            UPDATE asistencias
            SET fecha = ?, hora_entrada = ?, hora_salida = ?,
                estado = ?, observaciones = ?
            WHERE id = ?
        """, (
            fecha, hora_entrada, hora_salida, estado,
            observaciones, asistencia_id
        ))
        conexion.commit()
        if cursor.rowcount == 0:
            return False, "No se encontró el registro de asistencia."
        return True, "Asistencia actualizada correctamente."
    except sqlite3.IntegrityError:
        return False, "Ya existe una asistencia para esa fecha."
    except sqlite3.Error as error:
        conexion.rollback()
        return False, f"Error al actualizar: {error}"
    finally:
        conexion.close()


def listar_asistencias(fecha_inicio=None, fecha_fin=None, trabajador_id=None):
    conexion = conectar()
    try:
        consulta = """
            SELECT a.id, a.trabajador_id, t.dni, t.nombres, t.apellidos,
                   a.fecha, a.hora_entrada, a.hora_salida, a.estado,
                   a.observaciones
            FROM asistencias a
            INNER JOIN trabajadores t ON a.trabajador_id = t.id
            WHERE 1=1
        """
        parametros = []
        if fecha_inicio:
            validar_fecha(fecha_inicio)
            consulta += " AND a.fecha >= ?"
            parametros.append(fecha_inicio)
        if fecha_fin:
            validar_fecha(fecha_fin)
            consulta += " AND a.fecha <= ?"
            parametros.append(fecha_fin)
        if trabajador_id is not None:
            consulta += " AND a.trabajador_id = ?"
            parametros.append(trabajador_id)
        consulta += " ORDER BY a.fecha DESC, t.apellidos ASC"
        return conexion.execute(consulta, parametros).fetchall()
    finally:
        conexion.close()


def obtener_asistencia_por_id(asistencia_id):
    conexion = conectar()
    try:
        return conexion.execute("""
            SELECT a.id, a.trabajador_id, t.dni, t.nombres, t.apellidos,
                   a.fecha, a.hora_entrada, a.hora_salida, a.estado,
                   a.observaciones
            FROM asistencias a
            INNER JOIN trabajadores t ON a.trabajador_id = t.id
            WHERE a.id = ?
        """, (asistencia_id,)).fetchone()
    finally:
        conexion.close()


def resumen_mensual_asistencia(anio, mes, trabajador_id=None):
    anio = int(anio)
    mes = int(mes)
    if not 1 <= mes <= 12:
        raise ValueError("El mes debe estar entre 1 y 12.")

    conexion = conectar()
    try:
        consulta = """
            SELECT t.id, t.dni, t.nombres, t.apellidos,
                   COUNT(a.id) AS dias_registrados,
                   SUM(CASE WHEN a.estado = 'PRESENTE' THEN 1 ELSE 0 END) AS presentes,
                   SUM(CASE WHEN a.estado = 'FALTA' THEN 1 ELSE 0 END) AS faltas,
                   SUM(CASE WHEN a.estado = 'PERMISO' THEN 1 ELSE 0 END) AS permisos,
                   SUM(CASE WHEN a.estado = 'DESCANSO' THEN 1 ELSE 0 END) AS descansos
            FROM trabajadores t
            LEFT JOIN asistencias a
              ON t.id = a.trabajador_id
             AND strftime('%Y', a.fecha) = ?
             AND strftime('%m', a.fecha) = ?
            WHERE 1=1
        """
        parametros = [str(anio), f"{mes:02d}"]
        if trabajador_id is not None:
            consulta += " AND t.id = ?"
            parametros.append(trabajador_id)
        consulta += " GROUP BY t.id ORDER BY t.apellidos, t.nombres"
        return conexion.execute(consulta, parametros).fetchall()
    finally:
        conexion.close()


if __name__ == "__main__":
    crear_tabla_asistencia()
    print("Tabla de asistencia creada correctamente.")
