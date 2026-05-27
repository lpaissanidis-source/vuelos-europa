# ============================================================
# BUSCADOR.PY
# ============================================================

import re
from fast_flights import FlightData, Passengers, get_flights

_debug_impreso = False  # Imprime los atributos del vuelo solo la primera vez


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


def buscar_vuelo_mas_barato(origen, destino, fecha_ida, fecha_vuelta,
                             pasajeros, solo_carry_on=True):
    global _debug_impreso

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

        # --------------------------------------------------------
        # DEBUG: imprime todos los atributos del resultado y del
        # primer vuelo, solo en la primera busqueda exitosa.
        # Aparece en los logs de GitHub Actions.
        # --------------------------------------------------------
        if not _debug_impreso:
            _debug_impreso = True
            try:
                _res_attrs = [a for a in dir(resultado) if not a.startswith('_')]
                print(f"\n    [DEBUG] resultado attrs: {_res_attrs}")
                _v = resultado.flights[0]
                _v_attrs = [a for a in dir(_v) if not a.startswith('_')]
                print(f"    [DEBUG] flight attrs: {_v_attrs}")
                print(f"    [DEBUG] flight str: {_v}")
            except Exception as _e:
                print(f"    [DEBUG] error inspeccionando: {_e}")

        vuelo_mas_barato = None
        precio_minimo    = float("inf")
        idx_mejor        = 0

        for i, vuelo in enumerate(resultado.flights):
            precio_texto = getattr(vuelo, "price", None)
            precio = parsear_precio(precio_texto)
            if precio is None:
                continue
            if precio < precio_minimo:
                precio_minimo    = precio
                vuelo_mas_barato = vuelo
                idx_mejor        = i

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

        # --------------------------------------------------------
        # Intenta obtener el horario de vuelta de varias fuentes:
        # 1. Atributos directos del objeto vuelo
        # 2. Lista returning_flights del resultado (indice correspondiente)
        # 3. Lista return_flights del resultado
        # --------------------------------------------------------
        salida_vuelta  = (getattr(vuelo_mas_barato, "return_departure", "") or
                          getattr(vuelo_mas_barato, "return_depart", ""))
        llegada_vuelta = (getattr(vuelo_mas_barato, "return_arrival", "") or
                          getattr(vuelo_mas_barato, "return_arrive", ""))

        if not salida_vuelta:
            _ret_list = (getattr(resultado, "returning_flights", None) or
                         getattr(resultado, "return_flights", None))
            if _ret_list:
                _ret = _ret_list[idx_mejor] if idx_mejor < len(_ret_list) else _ret_list[0]
                salida_vuelta  = getattr(_ret, "departure", "")
                llegada_vuelta = getattr(_ret, "arrival", "")
                _dia_sig_v     = getattr(_ret, "arrival_time_ahead", "")
                if _dia_sig_v:
                    llegada_vuelta = f"{llegada_vuelta} ({_dia_sig_v})"

        dia_sig_vuelta = getattr(vuelo_mas_barato, "return_arrival_time_ahead", "")
        if dia_sig_vuelta and llegada_vuelta and "(" not in llegada_vuelta:
            llegada_vuelta = f"{llegada_vuelta} ({dia_sig_vuelta})"

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
