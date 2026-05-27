# ============================================================
# BUSCADOR.PY
# ============================================================

import re
from fast_flights import FlightData, Passengers, get_flights


def parsear_precio(texto_precio):
    if not texto_precio:
        return None
    texto = str(texto_precio)
    texto = texto.replace("€", "").replace("$", "").replace("£", "").strip()
    if "," in texto and "." in texto:
        if texto.index(".") < texto.index(","):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        partes = texto.split(",")
        if len(partes) == 2 and len(partes[1]) == 3:
            texto = texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes) == 2 and len(partes[1]) == 3:
            texto = texto.replace(".", "")
    solo_numeros = re.sub(r"[^\d.]", "", texto)
    try:
        return float(solo_numeros)
    except ValueError:
        return None


def _buscar_horario_vuelta(destino, origen, fecha_vuelta, pasajeros):
    """
    Hace una busqueda de solo-ida para el tramo de vuelta y devuelve
    (salida_vuelta, llegada_vuelta). Necesario porque fast-flights no
    expone los horarios del tramo de vuelta en la busqueda redonda.
    """
    try:
        res = get_flights(
            flight_data=[
                FlightData(date=fecha_vuelta, from_airport=destino, to_airport=origen),
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=pasajeros),
            fetch_mode="local",
        )
        if not res or not res.flights:
            return "", ""

        # Toma el vuelo marcado como "mejor" o, si no hay, el primero
        vuelo = next((f for f in res.flights if getattr(f, "is_best", False)), res.flights[0])
        salida  = getattr(vuelo, "departure", "")
        llegada = getattr(vuelo, "arrival", "")
        dia_sig = getattr(vuelo, "arrival_time_ahead", "")
        if dia_sig:
            llegada = f"{llegada} ({dia_sig})"
        return salida, llegada
    except Exception:
        return "", ""


def buscar_vuelo_mas_barato(origen, destino, fecha_ida, fecha_vuelta,
                             pasajeros, solo_carry_on=True):

    print(f"    Buscando {origen}→{destino} | Ida: {fecha_ida} | Vuelta: {fecha_vuelta} ...", end=" ")

    try:
        resultado = get_flights(
            flight_data=[
                FlightData(date=fecha_ida,    from_airport=origen,  to_airport=destino),
                FlightData(date=fecha_vuelta, from_airport=destino, to_airport=origen),
            ],
            trip="round-trip",
            seat="economy",
            passengers=Passengers(adults=pasajeros),
            fetch_mode="local",
        )

        if not resultado or not resultado.flights:
            print("Sin resultados.")
            return None

        vuelo_mas_barato = None
        precio_minimo    = float("inf")

        for vuelo in resultado.flights:
            precio = parsear_precio(getattr(vuelo, "price", None))
            if precio is not None and precio < precio_minimo:
                precio_minimo    = precio
                vuelo_mas_barato = vuelo

        if vuelo_mas_barato is None:
            print("No se pudo leer el precio.")
            return None

        aerolinea = getattr(vuelo_mas_barato, "name", "Desconocida")
        duracion  = getattr(vuelo_mas_barato, "duration", "Desconocida")

        stops = getattr(vuelo_mas_barato, "stops", None)
        if stops == 0:
            escalas = "Sin escalas"
        elif stops == 1:
            escalas = "1 escala"
        elif stops and stops > 1:
            escalas = f"{stops} escalas"
        else:
            escalas = str(stops) if stops else "Desconocido"

        salida  = getattr(vuelo_mas_barato, "departure", "")
        llegada = getattr(vuelo_mas_barato, "arrival", "")
        dia_sig = getattr(vuelo_mas_barato, "arrival_time_ahead", "")
        if dia_sig:
            llegada = f"{llegada} ({dia_sig})"

        # La libreria fast-flights no expone horarios del tramo de vuelta
        # en la busqueda redonda, asi que hacemos una segunda busqueda.
        salida_vuelta, llegada_vuelta = _buscar_horario_vuelta(
            destino, origen, fecha_vuelta, pasajeros
        )

        print(f"Precio encontrado: {precio_minimo:.2f} EUR")

        return {
            "origen":         origen,
            "destino":        destino,
            "fecha_ida":      fecha_ida,
            "fecha_vuelta":   fecha_vuelta,
            "pasajeros":      pasajeros,
            "precio_total":   precio_minimo,
            "aerolinea":      aerolinea,
            "duracion":       duracion,
            "escalas":        escalas,
            "salida":         salida,
            "llegada":        llegada,
            "salida_vuelta":  salida_vuelta,
            "llegada_vuelta": llegada_vuelta,
        }

    except Exception as e:
        print(f"Error: {e}")
        return None


def buscar_todas_las_combinaciones(config_ruta):
    origen        = config_ruta["origen"]
    destino       = config_ruta["destino"]
    pasajeros     = config_ruta["pasajeros"]
    fechas_ida    = config_ruta["fechas_ida"]
    fechas_vuelta = config_ruta["fechas_vuelta"]
    solo_carry_on = config_ruta.get("solo_carry_on", True)

    resultados = []
    total = len(fechas_ida) * len(fechas_vuelta)
    print(f"  Combinaciones a buscar: {total} ({len(fechas_ida)} fechas ida x {len(fechas_vuelta)} fechas vuelta)")

    for fecha_ida in fechas_ida:
        for fecha_vuelta in fechas_vuelta:
            vuelo = buscar_vuelo_mas_barato(
                origen=origen,
                destino=destino,
                fecha_ida=str(fecha_ida),
                fecha_vuelta=str(fecha_vuelta),
                pasajeros=pasajeros,
                solo_carry_on=solo_carry_on,
            )
            if vuelo:
                resultados.append(vuelo)

    return resultados


if __name__ == "__main__":
    print("=" * 55)
    print("TEST DE BUSQUEDA - UNA COMBINACION")
    print("=" * 55)
    resultado = buscar_vuelo_mas_barato(
        origen="EZE",
        destino="MAD",
        fecha_ida="2026-10-01",
        fecha_vuelta="2026-10-20",
        pasajeros=2,
        solo_carry_on=True,
    )
    if resultado:
        print(f"\nPrecio: {resultado['precio_total']:.2f} EUR | {resultado['aerolinea']}")
        print(f"Ida:    {resultado['salida']} → {resultado['llegada']}")
        print(f"Vuelta: {resultado['salida_vuelta']} → {resultado['llegada_vuelta']}")
    else:
        print("\nNo se encontraron resultados.")
