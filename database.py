# ============================================================
# DATABASE.PY
# Crea y maneja la base de datos SQLite donde se guarda
# el historico de precios de cada busqueda.
# SQLite guarda todo en un solo archivo: precios.db
# ============================================================

import sqlite3
import datetime


ARCHIVO_DB = "precios.db"


def crear_tabla():
    """Crea la tabla de precios si no existe todavia."""

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ruta            TEXT,
            fecha_ida       TEXT,
            fecha_vuelta    TEXT,
            pasajeros       INTEGER,
            precio_total    REAL,
            aerolinea       TEXT,
            duracion        TEXT,
            escalas         TEXT,
            fecha_consulta  TEXT
        )
    """)

    conexion.commit()
    conexion.close()


def guardar_precio(ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
                   aerolinea, duracion, escalas):
    """Guarda un precio encontrado en la base de datos."""

    fecha_consulta = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO precios
            (ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
             aerolinea, duracion, escalas, fecha_consulta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
          aerolinea, duracion, escalas, fecha_consulta))

    conexion.commit()
    conexion.close()


def obtener_minimo_historico(ruta, fecha_ida, fecha_vuelta):
    """
    Busca el precio mas bajo que se haya registrado para
    una combinacion especifica de ruta + fechas.
    Devuelve el precio minimo, o None si no hay registros previos.
    """

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT MIN(precio_total)
        FROM precios
        WHERE ruta = ?
          AND fecha_ida = ?
          AND fecha_vuelta = ?
    """, (ruta, fecha_ida, fecha_vuelta))

    resultado = cursor.fetchone()
    conexion.close()

    return resultado[0]


def obtener_ultimos_precios(ruta, limite=10):
    """Devuelve los ultimos N precios registrados para una ruta."""

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha_ida, fecha_vuelta, precio_total, aerolinea, fecha_consulta
        FROM precios
        WHERE ruta = ?
        ORDER BY fecha_consulta DESC
        LIMIT ?
    """, (ruta, limite))

    resultados = cursor.fetchall()
    conexion.close()

    return resultados


# ============================================================
# BLOQUE DE PRUEBA
# ============================================================
if __name__ == "__main__":

    print("Creando base de datos...")
    crear_tabla()
    print("✓ Tabla creada correctamente en precios.db")

    print("Insertando precio de prueba...")
    guardar_precio(
        ruta="EZE-MAD",
        fecha_ida="2026-10-01",
        fecha_vuelta="2026-10-20",
        pasajeros=2,
        precio_total=1850.00,
        aerolinea="Iberia",
        duracion="14h 20m",
        escalas="Sin escalas"
    )
    print("✓ Precio de prueba guardado")

    minimo = obtener_minimo_historico("EZE-MAD", "2026-10-01", "2026-10-20")
    print(f"✓ Minimo historico para EZE-MAD (1oct/20oct): {minimo} EUR")
