# Módulo 6: Informe de estadísticas finales.

"""
Muestra el informe estadístico final de la simulación. Lo llama el módulo 7
al terminar el último proceso.

Recibe 'cola_terminados' (lista de diccionarios, la que va llenando el módulo 4).
Cada proceso debe traer:
    "TA":          tiempo de arribo
    "TI":          tiempo de irrupción
    "tiempo_fin":  clock en el que terminó (lo guarda el Módulo 4. El Módulo 1
                   lo crea en None)

    tiempo_retorno = tiempo_fin - TA
    tiempo_espera  = tiempo_retorno - TI
    rendimiento    = procesos terminados / tiempo total de la simulación

El tiempo total de la simulación es el 'tiempo_fin' del último proceso en
terminar (se cuenta desde el clock 0).
"""

def calcular_estadisticas(cola_terminados):
    """
    Agrega 'tiempo_retorno' y 'tiempo_espera' a cada proceso terminado.
    Devuelve (promedio_retorno, promedio_espera, rendimiento).
    Requiere que la lista no esté vacía (lo controla mostrar_informe_final).
    """
    for p in cola_terminados:
        p["tiempo_retorno"] = p["tiempo_fin"] - p["TA"]
        p["tiempo_espera"] = p["tiempo_retorno"] - p["TI"]

    cantidad = len(cola_terminados)
    promedio_retorno = sum(p["tiempo_retorno"] for p in cola_terminados) / cantidad
    promedio_espera = sum(p["tiempo_espera"] for p in cola_terminados) / cantidad
    tiempo_total = max(p["tiempo_fin"] for p in cola_terminados)

    return promedio_retorno, promedio_espera, cantidad / tiempo_total


def mostrar_informe_final(cola_terminados):
    """
    Imprime la tabla por proceso (ordenada por id), los promedios de retorno y
    espera, y el rendimiento del sistema. No devuelve nada.
    """
    if not cola_terminados:
        print("No hay procesos terminados para mostrar estadísticas.")
        return

    promedio_retorno, promedio_espera, rendimiento = calcular_estadisticas(cola_terminados)

    print("\n" + "=" * 40)
    print("INFORME ESTADÍSTICO FINAL")
    print("=" * 40)
    print(f"{'Proceso':<10}{'Fin':<8}{'Retorno':<11}{'Espera':<11}")
    print("-" * 40)
  
    for p in sorted(cola_terminados, key=lambda x: x["id"]):
        print(f"{p['id']:<10}{p['tiempo_fin']:<8}{p['tiempo_retorno']:<11}{p['tiempo_espera']:<11}")

    print("-" * 40)
    print(f"Retorno promedio: {promedio_retorno:.2f}")
    print(f"Espera promedio:  {promedio_espera:.2f}")
    print(f"Rendimiento:      {rendimiento:.3f} procesos/unidad de tiempo")
