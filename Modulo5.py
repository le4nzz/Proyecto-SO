# Módulo 5: Admisión y Reubicación por Best-Fit (Suspendidos y Nuevos)

# CAMBIOS sobre el módulo original:
#  - Se agrega el límite de MAX_PROCESOS_ACTIVOS (Ejecución + Listos +
#    Suspendidos). Solo frena a los Nuevos: un Suspendido ya cuenta como activo.
#  - Ya no imprime (limpiar_pantalla lo borraría). En su lugar devuelve una
#    lista de (proceso, destino) con lo que pasó con cada proceso.
#  - Recibe 'en_cpu' (en lugar de 'clock') para poder contar los activos.
#  - Usa las constantes de estado (antes "listo" / "suspendido" en minúscula).
#  - Se agrega contar_procesos_activos.

from constantes import ESTADO_LISTO, ESTADO_SUSPENDIDO, MAX_PROCESOS_ACTIVOS
from Modulo2 import asignar_best_fit


def contar_procesos_activos(cola_listos, cola_suspendidos, en_cpu):
  """Cuenta los procesos activos: Ejecución + Listos + Suspendidos."""
  return len(cola_listos) + len(cola_suspendidos) + (0 if en_cpu is None else 1)


def admision_suspendidos_y_nuevos_best_fit(
    cola_suspendidos, cola_nuevos, cola_listos, memoria, en_cpu
):
  """Intenta asignar memoria mediante Best-Fit a los procesos en espera:

  1. Evalúa primero la 'cola_suspendidos' (proceso a proceso). Si hay hueco, lo
  ubica, lo pasa a 'cola_listos' y lo remueve de suspendidos.
  2. Evalúa luego la 'cola_nuevos'. Si hay hueco, lo ubica y lo pasa a
  'cola_listos'.
     Si NO entra en memoria, se lo transfiere a 'cola_suspendidos'.
     Si ya hay MAX_PROCESOS_ACTIVOS procesos activos, los nuevos esperan.

  Devuelve una lista de (proceso, destino) con lo que pasó con cada proceso
  en este clock.
  """
  resultados = []

  # -------------------------------------------------------------
  # 1. Intentar des-suspender procesos que ya estaban esperando
  # -------------------------------------------------------------
  for p in list(cola_suspendidos):  # Iteramos sobre una copia para no romper los índices
    if asignar_best_fit(memoria, p):
      p["estado"] = ESTADO_LISTO
      cola_listos.append(p)
      cola_suspendidos.remove(p)
      resultados.append((p, ESTADO_LISTO))

  # -------------------------------------------------------------
  # 2. Intentar admitir los procesos nuevos ingresados en este clock
  # -------------------------------------------------------------
  for p in list(cola_nuevos):
    if contar_procesos_activos(cola_listos, cola_suspendidos, en_cpu) >= MAX_PROCESOS_ACTIVOS:
      break  # No se admiten más: el resto sigue en Nuevos

    if asignar_best_fit(memoria, p):
      p["estado"] = ESTADO_LISTO
      cola_listos.append(p)
      cola_nuevos.remove(p)
      resultados.append((p, ESTADO_LISTO))
    else:
      # No hubo partición disponible para este proceso nuevo: Pasa a Suspendidos
      p["estado"] = ESTADO_SUSPENDIDO
      cola_suspendidos.append(p)
      cola_nuevos.remove(p)
      resultados.append((p, ESTADO_SUSPENDIDO))

  return resultados
