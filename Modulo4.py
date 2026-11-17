# Módulo 4: Verificar si el proceso terminó y liberar memoria.
from constantes import ESTADO_TERMINADO



def verificar_terminado(proceso, memoria, cola_terminados, clock):
    """Verifica si el proceso en CPU agotó su tiempo restante. Si terminó, libera y compacta memoria."""
    if proceso["tiempo_rest"] == 0:
        liberar_memoria(memoria, proceso, cola_terminados, clock)
        fusionar_particiones(memoria)
        return True
    return False



def liberar_memoria(memoria, proceso, cola_terminados, clock):
    """
    Desasigna el bloque en 'memoria' (claves de Módulo 2: 'libre', 'id_proc'),
    registra 'tiempo_fin' (requerido por Módulo 6) y envía el proceso a 'cola_terminados'.
    """
    for bloque in memoria:
        if bloque["id_proc"] == proceso["id"]:
            bloque["libre"] = True
            bloque["id_proc"] = None  
            break

    proceso["estado"] = ESTADO_TERMINADO
    proceso["tiempo_fin"] = clock

    cola_terminados.append(proceso)  


def fusionar_particiones(memoria):
    """
    Recorre 'memoria' y unifica particiones libres adyacentes sumando 'tamanio'
    para reducir la fragmentación externa.
    """
    i = 0
    while i < len(memoria) - 1:
        if memoria[i]["libre"] and memoria[i + 1]["libre"]:
            memoria[i]["tamanio"] += memoria[i + 1]["tamanio"] 
            memoria.pop(i + 1)  
            
          # No se incrementa i para verificar si la nueva partición puede fusionarse con la siguiente
        else:
            i += 1
