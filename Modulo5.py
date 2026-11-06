"""
Módulo 5: Admisión y Reubicación por Best-Fit (Suspendidos y Nuevos)
"""

from Modulo2 import asignar_best_fit


def admision_suspendidos_y_nuevos_best_fit(
    cola_suspendidos, cola_nuevos, cola_listos, memoria, clock
):
  """Intenta asignar memoria mediante Best-Fit a los procesos en espera:

  1. Evalúa primero la 'cola_suspendidos' (proceso a proceso). Si hay hueco, lo
  ubica, lo pasa a 'cola_listos' y lo remueve de suspendidos.
  2. Evalúa luego la 'cola_nuevos'. Si hay hueco, lo ubica y lo pasa a
  'cola_listos'.
     Si NO entra en memoria, se lo transfiere a 'cola_suspendidos'.

  Devuelve una lista con todos los procesos que lograron ingresar a memoria en
  este clock.
  """
  admitidos_en_este_tick = []

  # -------------------------------------------------------------
  # 1. Intentar des-suspender procesos que ya estaban esperando
  # -------------------------------------------------------------
  for p in list(cola_suspendidos):  # Iteramos sobre una copia para no romper los índices
    if asignar_best_fit(memoria, p):
      p["estado"] = "listo"
      cola_listos.append(p)
      cola_suspendidos.remove(p)
      admitidos_en_este_tick.append(p)
      print(
          f"[Clock {clock}] Proceso {p['id']} (TAM: {p['TAM']}K) des-suspendido"
          " -> Asignado a memoria -> Cola de Listos."
      )

  # -------------------------------------------------------------
  # 2. Intentar admitir los procesos nuevos ingresados en este clock
  # -------------------------------------------------------------
  for p in list(cola_nuevos):
    if asignar_best_fit(memoria, p):
      p["estado"] = "listo"
      cola_listos.append(p)
      cola_nuevos.remove(p)
      admitidos_en_este_tick.append(p)
      print(
          f"[Clock {clock}] Proceso {p['id']} (TAM: {p['TAM']}K) nuevo ->"
          " Asignado a memoria -> Cola de Listos."
      )
    else:
      # No hubo partición disponible para este proceso nuevo: Pasa a Suspendidos
      p["estado"] = "suspendido"
      cola_suspendidos.append(p)
      cola_nuevos.remove(p)
      print(
          f"[Clock {clock}] Proceso {p['id']} (TAM: {p['TAM']}K) nuevo sin"
          " espacio en memoria -> Movido a Cola de Suspendidos."
      )

  return admitidos_en_este_tick