# Módulo 4: Verificar si el proceso terminó y liberar memoria.

# CAMBIOS sobre el módulo original (el original no podía ejecutarse):
#  - verificar_terminado compara "tiempo_rest" (antes "TI", que nunca baja) y
#    recibe memoria, cola_terminados y clock por parámetro (antes usaba
#    variables globales que no existían). Se quitó el print: la pantalla la
#    maneja el simulador.
#  - liberar_memoria usa las claves de Modulo2: marca "libre" = True e
#    "id_proc" = None (antes "id_proceso"). Guarda "tiempo_fin" (lo necesita
#    Modulo6) y manda el proceso a terminados. Ya no recibe cola_ejecucion:
#    el simulador tiene un solo proceso en CPU.
#  - fusionar_particiones usa las claves "libre" y "tamanio" (antes "tam").

from constantes import ESTADO_TERMINADO

"""
    Verifica si el proceso en CPU terminó su TI.
    Si terminó, lo libera de memoria y lo manda a terminados.
"""
def verificar_terminado(proceso, memoria, cola_terminados, clock):
    if proceso["tiempo_rest"] == 0:
        liberar_memoria(memoria, proceso, cola_terminados, clock)
        fusionar_particiones(memoria)
        return True
    return False


"""En este caso se libera la particion que estaba ocupada por el proceso,
lo cambia de ejecucion a terminados"""
def liberar_memoria(memoria, proceso, cola_terminados, clock):

    #En este caso se libera la particion que estaba ocupada en memoria
    for bloque in memoria:
        if bloque["id_proc"] == proceso["id"]:
            bloque["libre"] = True
            bloque["id_proc"] = None  # Liberar la particion
            break

    proceso["estado"] = ESTADO_TERMINADO
    proceso["tiempo_fin"] = clock

    cola_terminados.append(proceso)  # Se mueve el proceso a la cola de terminados



""" Esta funcion se encargara de fusionar las particiones libres en memoria.
Cada que encuentra dos particiones continuas libres"""
def fusionar_particiones(memoria):
    i = 0
    while i < len(memoria) - 1:
        if memoria[i]["libre"] and memoria[i + 1]["libre"]:
            memoria[i]["tamanio"] += memoria[i + 1]["tamanio"]  # se suma el tamaño de las particiones libres
            memoria.pop(i + 1)  
            
            # Aclaracion: no incrementamos i para verificar la nueva particion fusionada
        else:
            i += 1
