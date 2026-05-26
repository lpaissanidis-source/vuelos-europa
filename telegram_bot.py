# ============================================================
# TELEGRAM_BOT.PY
# Maneja el envio de mensajes por Telegram.
# Lee el TOKEN y CHAT_ID desde credenciales.txt
# y usa la API de Telegram para mandar alertas.
# ============================================================

import requests
import os


# ============================================================
# LECTURA DE CREDENCIALES
# ============================================================

def leer_credenciales():
    """
    Lee credenciales.txt y devuelve un diccionario con
    las claves TOKEN y CHAT_ID.
    El archivo debe tener el formato:
        TELEGRAM_BOT_TOKEN=xxxxx
        TELEGRAM_CHAT_ID=xxxxx
    """

    credenciales = {}

    with open("credenciales.txt", "r") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" in linea:
                clave, valor = linea.split("=", 1)
                credenciales[clave.strip()] = valor.strip()

    return credenciales


_credenciales = leer_credenciales()

TOKEN   = _credenciales.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = _credenciales.get("TELEGRAM_CHAT_ID", "")

URL_API = f"https://api.telegram.org/bot{TOKEN}"


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def enviar_mensaje(texto):
    """
    Envia un mensaje de texto simple por Telegram.
    Devuelve True si se envio correctamente, False si hubo error.
    """

    url = f"{URL_API}/sendMessage"

    datos = {
        "chat_id":    CHAT_ID,
        "text":       texto,
        "parse_mode": "HTML"
    }

    try:
        respuesta = requests.post(url, data=datos, timeout=10)
        resultado = respuesta.json()

        if resultado.get("ok"):
            return True
        else:
            print(f"  Error de Telegram: {resultado.get('description', 'Error desconocido')}")
            return False

    except requests.exceptions.Timeout:
        print("  Error: Timeout al conectar con Telegram")
        return False

    except requests.exceptions.ConnectionError:
        print("  Error: Sin conexion a internet")
        return False

    except Exception as e:
        print(f"  Error inesperado: {e}")
        return False


def enviar_alerta_precio(ruta, fecha_ida, fecha_vuelta, precio_total,
                         aerolinea, duracion, escalas, pasajeros,
                         salida="", llegada="", salida_vuelta="", llegada_vuelta="",
                         buscador="", es_minimo_historico=False):
    """
    Envia una alerta formateada cuando se encuentra un precio bajo el umbral.
    """

    if es_minimo_historico:
        encabezado = "NUEVO MINIMO HISTORICO"
    else:
        encabezado = "PRECIO BAJO UMBRAL"

    linea_horario_ida    = f"<b>🕐 Horario ida:</b> {salida} → {llegada}\n" if (salida or llegada) else ""
    linea_horario_vuelta = f"<b>🕐 Horario vuelta:</b> {salida_vuelta} → {llegada_vuelta}\n" if (salida_vuelta or llegada_vuelta) else ""

    mensaje = (
        f"<b>📁 {buscador}</b>\n"
        f"<b>✈️ {encabezado}</b>\n"
        f"\n"
        f"<b>Ruta:</b> {ruta}\n"
        f"<b>Ida:</b> {fecha_ida}\n"
        f"<b>Vuelta:</b> {fecha_vuelta}\n"
        f"<b>Pasajeros:</b> {pasajeros}\n"
        f"\n"
        f"<b>💰 Precio total:</b> {precio_total:.2f} EUR\n"
        f"<b>Precio por persona:</b> {precio_total / pasajeros:.2f} EUR\n"
        f"\n"
        f"<b>Aerolínea:</b> {aerolinea}\n"
        f"<b>Duración:</b> {duracion}\n"
        f"<b>Escalas:</b> {escalas}\n"
        f"{linea_horario_ida}"
        f"{linea_horario_vuelta}"
    )

    return enviar_mensaje(mensaje)


def enviar_mensaje_prueba():
    """Manda un mensaje simple para verificar que el bot funciona."""

    mensaje = (
        "<b>✅ Test de conexion exitoso</b>\n"
        "\n"
        "El buscador de vuelos 2 esta configurado correctamente.\n"
        "Vas a recibir alertas aqui cuando encuentre precios bajos."
    )

    return enviar_mensaje(mensaje)


# ============================================================
# BLOQUE DE PRUEBA
# ============================================================
if __name__ == "__main__":

    print("Leyendo credenciales...")
    print(f"  TOKEN encontrado: {'Si' if TOKEN else 'NO - revisar credenciales.txt'}")
    print(f"  CHAT_ID encontrado: {'Si' if CHAT_ID else 'NO - revisar credenciales.txt'}")

    print("\nEnviando mensaje de prueba a Telegram...")
    exito = enviar_mensaje_prueba()

    if exito:
        print("✓ Mensaje enviado correctamente. Revisa tu Telegram.")
    else:
        print("✗ No se pudo enviar. Revisa el TOKEN y CHAT_ID en credenciales.txt")
