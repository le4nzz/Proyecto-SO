# Módulo 3: Planificador SRTF para la asignación de CPU.

def srtf_seleccionar_proceso(proceso_en_ejecucion, cola_listos):
    """
    Evalúa si entra un nuevo proceso al CPU o si hay expropiación.
    Devuelve proceso_seleccionado y proceso_expropiado
    """
    # Si la cola de listos está vacía, sigue el que está (o None si no hay ninguno)
    if not cola_listos:
        return proceso_en_ejecucion, None

    # Buscamos el candidato con menor tiempo restante en la cola de listos
    # Utilizamos lambda para hallar todos los tiempo_rest de la cola_listos
    # Luego hallamos el menor tiempo_rest con la función min
    candidato = min(cola_listos, key=lambda x: x['tiempo_rest'])

    # Caso 1: El CPU está libre
    if proceso_en_ejecucion is None:
        cola_listos.remove(candidato)
        return candidato, None

    # Caso 2: El CPU está ocupado, evaluamos expropiación
    if candidato['tiempo_rest'] < proceso_en_ejecucion['tiempo_rest']:
        # Sacamos al candidato de listos y metemos al actual
        cola_listos.remove(candidato)
        cola_listos.append(proceso_en_ejecucion) # El actual vuelve a listos
        return candidato, proceso_en_ejecucion

    # Caso 3: No hay expropiación, el actual se queda
    return proceso_en_ejecucion, None

def ejecutar_tick_cpu(proceso_en_ejecucion):
    """
    Decrementa en 1 el tiempo restante del proceso en ejecución.
    Devuelve True si el proceso terminó (tiempo_rest == 0), False si continúa.
    """
    if proceso_en_ejecucion is not None:
        proceso_en_ejecucion['tiempo_rest'] -= 1
        if proceso_en_ejecucion['tiempo_rest'] == 0:
            return True
    return False
