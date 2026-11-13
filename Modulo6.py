"""
INFORME DE ESTADISTICAS FINALES.

Recibe 'cola_terminados' (una lista de diccionarios). Cada proceso debe traer
la clave 'tiempo_fin' (clock en el que terminó, la guarda el módulo 4).

    tiempo_retorno = tiempo_fin - TA
    tiempo_espera  = tiempo_retorno - TI
    rendimiento    = procesos terminados / tiempo total de la simulación
"""

def calcular_estadisticas(cola_terminados):
    """
    Agrega 'tiempo_retorno' y 'tiempo_espera' a cada proceso terminado.
    Devuelve (promedio_retorno, promedio_espera, rendimiento).
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
    """Muestra la tabla por proceso, los promedios y el rendimiento del sistema."""
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
