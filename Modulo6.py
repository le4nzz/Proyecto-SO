# Módulo 6: Informe de estadísticas finales.

"""
Muestra el informe estadístico final de la simulación. Lo llama el módulo 7
al terminar el último proceso.

Recibe 'cola_terminados' (lista de diccionarios, la que va llenando el módulo 4).
Cada proceso debe traer:
    "TA":          tiempo de arribo
    "TI":          tiempo de irrupción
    "tiempo_fin":  clock en el que terminó (lo guarda el módulo 4. El módulo 1
                   lo crea en None)

    tiempo_retorno = tiempo_fin - TA
    tiempo_espera  = tiempo_retorno - TI
    rendimiento    = procesos terminados / tiempo total de la simulación

El tiempo total de la simulación es el 'tiempo_fin' del último proceso en
terminar (se cuenta desde el clock 0).

Los tiempos están en segundos (s), igual que el reloj del resto de las pantallas.
"""

def calcular_estadisticas(cola_terminados):
    """
    Agrega 'tiempo_retorno' y 'tiempo_espera' a cada proceso terminado.
    Devuelve (promedio_retorno, promedio_espera, rendimiento, tiempo_total).
    El rendimiento es cantidad de procesos / tiempo_total.
    Requiere que la lista no esté vacía (lo controla mostrar_informe_final).
    """
    for p in cola_terminados:
        p["tiempo_retorno"] = p["tiempo_fin"] - p["TA"]
        p["tiempo_espera"] = p["tiempo_retorno"] - p["TI"]

    cantidad = len(cola_terminados)
    promedio_retorno = sum(p["tiempo_retorno"] for p in cola_terminados) / cantidad
    promedio_espera = sum(p["tiempo_espera"] for p in cola_terminados) / cantidad
    tiempo_total = max(p["tiempo_fin"] for p in cola_terminados)

    return promedio_retorno, promedio_espera, cantidad / tiempo_total, tiempo_total


def mostrar_informe_final(cola_terminados):
    """
    Imprime el informe: una tabla con el retorno y la espera de cada proceso
    (en el orden en que terminaron), los promedios, el rendimiento del sistema,
    la cantidad de procesos finalizados y el tiempo total de simulación.
    """
    if not cola_terminados:
        print("No hay procesos terminados para mostrar estadísticas.")
        return

    promedio_retorno, promedio_espera, rendimiento, tiempo_total = calcular_estadisticas(cola_terminados)

    # Anchos de columna de la tabla
    ancho_id = 4
    ancho_otro = 9
    barra_id = "─" * ancho_id
    barra_otro = "─" * ancho_otro

    # Tabla con bordes, mismo estilo que las pantallas del módulo 7
    print(f"\nInforme estadístico")

    print(f"┌─{barra_id}─┬─{barra_otro}─┬─{barra_otro}─┐")
    print(f"│ {"ID":<{ancho_id}} │ {"Retorno":<{ancho_otro}} │ {"Espera":<{ancho_otro}} │")
    print(f"├─{barra_id}─┼─{barra_otro}─┼─{barra_otro}─┤")

    for p in cola_terminados:
        print(f"│ {"P" + str(p["id"]):<{ancho_id}} │ {p["tiempo_retorno"]:>{ancho_otro}} │ {p["tiempo_espera"]:>{ancho_otro}} │")

    print(f"└─{barra_id}─┴─{barra_otro}─┴─{barra_otro}─┘")
    print()

    # Promedios, rendimiento y totales
    print(f"Tiempo promedio de retorno: {promedio_retorno:.2f} s")
    print(f"Tiempo promedio de espera: {promedio_espera:.2f} s")
    print(f"Rendimiento del sistema: {rendimiento:.2f}")
    print(f"Cantidad de procesos finalizados {len(cola_terminados)}")
    print(f"Tiempo total de simulación {tiempo_total} s")