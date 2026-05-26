# ============================================================
# MAIN.PY
# Archivo principal. Lo unico que tenes que ejecutar:
#   python main.py
#
# Coordina todo el sistema:
#   1. Lee las rutas desde config.yaml
#   2. Busca vuelos con Playwright (Google Flights)
#   3. Guarda cada precio encontrado en la base de datos
#   4. Manda alerta por Telegram si el precio baja del umbral
#      o si es un nuevo minimo historico
# ============================================================

import yaml
import datetime

from database     import crear_tabla, guardar_precio, obtener_minimo_historico
from buscador     import buscar_todas_las_combinaciones
from telegram_bot import enviar_alerta_precio, enviar_mensaje

NOMBRE_BUSCADOR = "Vuelos Europa"


# ============================================================
# FUNCION: leer configuracion
# ============================================================

def leer_config():
    """Lee el archivo config.yaml y devuelve la lista de rutas."""

    with open("config.yaml", "r", encoding="utf-8") as archivo:
        config = yaml.safe_load(archivo)

    return config.get("rutas", [])


# ============================================================
# FUNCION: procesar una ruta completa
# ============================================================

def procesar_ruta(config_ruta):
    """
    Recibe la configuracion de una ruta, busca todos los vuelos,
    guarda los precios y manda alerta si corresponde.

    Regla anti-spam: manda como maximo 1 alerta por ruta
    (la combinacion de fechas con el precio mas bajo encontrado).
    """

    nombre    = config_ruta["nombre"]
    origen    = config_ruta["origen"]
    destino   = config_ruta["destino"]
    umbral    = config_ruta["umbral_precio"]
    pasajeros = config_ruta["pasajeros"]

    codigo_ruta = f"{origen}-{destino}"

    print(f"\n{'='*55}")
    print(f"  Ruta: {nombre}")
    print(f"  Umbral: {umbral} EUR para {pasajeros} pasajeros")
    print(f"{'='*55}")

    # --------------------------------------------------------
    # PASO 1: Buscar todas las combinaciones de fechas
    # --------------------------------------------------------
    resultados = buscar_todas_las_combinaciones(config_ruta)

    if not resultados:
        print(f"  Sin resultados para esta ruta.")
        return

    print(f"\n  Resultados obtenidos: {len(resultados)} combinaciones con precio")

    # --------------------------------------------------------
    # PASO 2: Guardar resultados y detectar el mejor precio
    # --------------------------------------------------------
    mejor_vuelo          = None
    mejor_precio         = float("inf")
    mejor_es_nuevo_min   = False

    for vuelo in resultados:

        fecha_ida    = vuelo["fecha_ida"]
        fecha_vuelta = vuelo["fecha_vuelta"]
        precio_total = vuelo["precio_total"]

        guardar_precio(
            ruta         = codigo_ruta,
            fecha_ida    = fecha_ida,
            fecha_vuelta = fecha_vuelta,
            pasajeros    = pasajeros,
            precio_total = precio_total,
            aerolinea    = vuelo["aerolinea"],
            duracion     = vuelo["duracion"],
            escalas      = vuelo["escalas"],
        )

        bajo_umbral = "✓ BAJO UMBRAL" if precio_total < umbral else ""
        print(f"    {fecha_ida} → {fecha_vuelta} | {precio_total:.0f} EUR | "
              f"{vuelo['aerolinea']} | {vuelo['escalas']} {bajo_umbral}")

        if precio_total < mejor_precio:
            mejor_precio = precio_total
            mejor_vuelo  = vuelo

            minimo_historico = obtener_minimo_historico(
                ruta         = codigo_ruta,
                fecha_ida    = fecha_ida,
                fecha_vuelta = fecha_vuelta,
            )

            if minimo_historico is None or precio_total < minimo_historico:
                mejor_es_nuevo_min = True
            else:
                mejor_es_nuevo_min = False

    # --------------------------------------------------------
    # PASO 3: Decidir si mandar alerta (maximo 1 por ruta)
    # --------------------------------------------------------
    if mejor_vuelo is None:
        return

    debe_alertar = (mejor_precio < umbral) or mejor_es_nuevo_min

    if debe_alertar:
        print(f"\n  *** ALERTA: Precio {mejor_precio:.0f} EUR")
        if mejor_es_nuevo_min:
            print(f"  *** Es nuevo minimo historico para esta ruta/fechas")
        print(f"  Enviando Telegram...")

        exito = enviar_alerta_precio(
            ruta               = nombre,
            fecha_ida          = mejor_vuelo["fecha_ida"],
            fecha_vuelta       = mejor_vuelo["fecha_vuelta"],
            precio_total       = mejor_precio,
            aerolinea          = mejor_vuelo["aerolinea"],
            duracion           = mejor_vuelo["duracion"],
            escalas            = mejor_vuelo["escalas"],
            salida             = mejor_vuelo.get("salida", ""),
            llegada            = mejor_vuelo.get("llegada", ""),
            salida_vuelta      = mejor_vuelo.get("salida_vuelta", ""),
            llegada_vuelta     = mejor_vuelo.get("llegada_vuelta", ""),
            buscador           = NOMBRE_BUSCADOR,
            pasajeros          = pasajeros,
            es_minimo_historico = mejor_es_nuevo_min,
        )

        if exito:
            print(f"  ✓ Telegram enviado correctamente")
        else:
            print(f"  ✗ Error al enviar Telegram")
    else:
        print(f"\n  Mejor precio encontrado: {mejor_precio:.0f} EUR")
        print(f"  Umbral: {umbral} EUR — No se manda alerta (precio sobre el umbral)")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

if __name__ == "__main__":

    hora_inicio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nBuscador de vuelos 2 iniciado: {hora_inicio}")

    crear_tabla()

    try:
        rutas = leer_config()
    except FileNotFoundError:
        print("ERROR: No se encontro config.yaml en la carpeta actual.")
        print("Asegurate de ejecutar el script desde la carpeta del proyecto.")
        exit(1)

    if not rutas:
        print("ERROR: No hay rutas configuradas en config.yaml")
        exit(1)

    print(f"Rutas a buscar: {len(rutas)}")

    for ruta in rutas:
        try:
            procesar_ruta(ruta)
        except Exception as e:
            print(f"\n  ERROR procesando {ruta.get('nombre', '?')}: {e}")
            print(f"  Continuando con la siguiente ruta...")

    hora_fin = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"Busqueda completada: {hora_fin}")
    print(f"{'='*55}\n")
