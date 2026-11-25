
import sqlite3
from pathlib import Path

# ============================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "planillas.db"


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ============================================================
# CREACIÓN Y ACTUALIZACIÓN DE LA TABLA DE TRABAJADORES
# ============================================================

def inicializar_base_datos():

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        # Crear tabla si todavía no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabajadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni TEXT UNIQUE NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                fecha_ingreso TEXT,
                cargo TEXT,
                sueldo_basico REAL DEFAULT 0,
                estado TEXT DEFAULT 'ACTIVO'
            )
        """)

        # Columnas adicionales para la ficha laboral
        nuevas_columnas = {
            "fecha_nacimiento": "TEXT",
            "fecha_ingreso_laboral": "TEXT",
            "fecha_contrato": "TEXT",
            "genero": "TEXT",
            "nacionalidad": "TEXT",
            "domicilio": "TEXT",
            "condicion": "TEXT DEFAULT 'Domiciliado'",
            "area": "TEXT",
            "sub_area": "TEXT",
            "tipo_contrato": "TEXT",
            "centro_costo": "TEXT",
            "tipo_trabajador": "TEXT",
            "regimen_salud": "TEXT",
            "cuspp": "TEXT"
        }

        # Consultar las columnas que ya existen
        cursor.execute("PRAGMA table_info(trabajadores)")
        columnas_existentes = {
            columna[1] for columna in cursor.fetchall()
        }

        # Agregar solamente las columnas que faltan
        for nombre, tipo in nuevas_columnas.items():

            if nombre not in columnas_existentes:

                cursor.execute(
                    f"ALTER TABLE trabajadores "
                    f"ADD COLUMN {nombre} {tipo}"
                )

        # Migración de datos antiguos:
        # El campo fecha_ingreso se utilizaba como fecha de nacimiento.
        cursor.execute("""
            UPDATE trabajadores
            SET fecha_nacimiento = fecha_ingreso
            WHERE (fecha_nacimiento IS NULL OR fecha_nacimiento = '')
              AND fecha_ingreso IS NOT NULL
              AND fecha_ingreso != ''
        """)

        conexion.commit()

        print("Base de datos inicializada correctamente.")
        print("Estructura de trabajadores actualizada.")
        return True

    except sqlite3.Error as error:

        conexion.rollback()
        print(f"Error al actualizar la base de datos: {error}")
        return False

    finally:
        conexion.close()


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    inicializar_base_datos()
