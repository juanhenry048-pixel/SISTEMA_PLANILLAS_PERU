
import sqlite3
from database.conexion import conectar


# ============================================================
# REGISTRAR TRABAJADOR
# ============================================================

def registrar_trabajador(
    dni,
    nombres,
    apellidos,
    fecha_ingreso,
    cargo,
    sueldo_basico,
    fecha_nacimiento=None,
    fecha_ingreso_laboral=None,
    fecha_contrato=None,
    genero=None,
    nacionalidad=None,
    domicilio=None,
    condicion="Domiciliado",
    area=None,
    sub_area=None,
    tipo_contrato=None,
    centro_costo=None,
    tipo_trabajador="Empleado",
    regimen_salud="EsSalud",
    cuspp=None
):

    conexion = conectar()

    try:
        conexion.execute("""
            INSERT INTO trabajadores (
                dni,
                nombres,
                apellidos,
                fecha_ingreso,
                cargo,
                sueldo_basico,
                estado,
                fecha_nacimiento,
                fecha_ingreso_laboral,
                fecha_contrato,
                genero,
                nacionalidad,
                domicilio,
                condicion,
                area,
                sub_area,
                tipo_contrato,
                centro_costo,
                tipo_trabajador,
                regimen_salud,
                cuspp
            )
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dni,
            nombres,
            apellidos,
            fecha_ingreso,
            cargo,
            sueldo_basico,
            fecha_nacimiento or fecha_ingreso,
            fecha_ingreso_laboral,
            fecha_contrato,
            genero,
            nacionalidad,
            domicilio,
            condicion,
            area,
            sub_area,
            tipo_contrato,
            centro_costo,
            tipo_trabajador,
            regimen_salud,
            cuspp
        ))

        conexion.commit()
        return True, "Trabajador registrado correctamente."

    except sqlite3.IntegrityError:
        return False, "El DNI ya se encuentra registrado."

    except sqlite3.Error as error:
        return False, f"Error al registrar: {error}"

    finally:
        conexion.close()


# ============================================================
# LISTAR TRABAJADORES
# ============================================================

def listar_trabajadores():

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT *
            FROM trabajadores
            ORDER BY id DESC
        """)

        return cursor.fetchall()

    finally:
        conexion.close()


# ============================================================
# BUSCAR TRABAJADOR POR DNI
# ============================================================

def buscar_trabajador(dni):

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT *
            FROM trabajadores
            WHERE dni = ?
        """, (dni,))

        return cursor.fetchone()

    finally:
        conexion.close()


# ============================================================
# OBTENER TRABAJADOR POR ID
# ============================================================

def obtener_trabajador_por_id(id_trabajador):

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT *
            FROM trabajadores
            WHERE id = ?
        """, (id_trabajador,))

        return cursor.fetchone()

    finally:
        conexion.close()


# ============================================================
# ACTUALIZAR DATOS DEL TRABAJADOR
# ============================================================

def actualizar_trabajador(id_trabajador, datos):

    conexion = conectar()

    try:
        campos_permitidos = {
            "dni",
            "nombres",
            "apellidos",
            "fecha_ingreso",
            "cargo",
            "sueldo_basico",
            "estado",
            "fecha_nacimiento",
            "fecha_ingreso_laboral",
            "fecha_contrato",
            "genero",
            "nacionalidad",
            "domicilio",
            "condicion",
            "area",
            "sub_area",
            "tipo_contrato",
            "centro_costo",
            "tipo_trabajador",
            "regimen_salud",
            "cuspp"
        }

        campos = {
            clave: valor
            for clave, valor in datos.items()
            if clave in campos_permitidos
        }

        if not campos:
            return False, "No hay datos para actualizar."

        asignaciones = ", ".join(
            f"{campo} = ?" for campo in campos
        )

        valores = list(campos.values())
        valores.append(id_trabajador)

        conexion.execute(
            f"""
            UPDATE trabajadores
            SET {asignaciones}
            WHERE id = ?
            """,
            valores
        )

        conexion.commit()
        return True, "Trabajador actualizado correctamente."

    except sqlite3.IntegrityError:
        return False, "El DNI ya se encuentra registrado."

    except sqlite3.Error as error:
        return False, f"Error al actualizar: {error}"

    finally:
        conexion.close()


# ============================================================
# CAMBIAR ESTADO DEL TRABAJADOR
# ============================================================

def cambiar_estado(id_trabajador, nuevo_estado):

    conexion = conectar()

    try:
        conexion.execute("""
            UPDATE trabajadores
            SET estado = ?
            WHERE id = ?
        """, (nuevo_estado, id_trabajador))

        conexion.commit()
        return True

    except sqlite3.Error:
        return False

    finally:
        conexion.close()
