#Modulo 4: Verificar si el proceso terminó y liberar memoria


"""
    Verifica si el proceso en CPU terminó su TI.
    Si terminó, lo libera de memoria y lo manda a terminados.
"""
def verificar_terminado(proceso):
    if proceso["TI"] == 0:
        print(f"El proceso {proceso['id']} ha terminado.")
        liberar_memoria(memoria, proceso, cola_ejecucion, cola_terminados)
        fusionar_particiones(memoria)
        return True
    return False


"""En este caso se libera la particion que estaba ocupada por el proceso,
lo cambia de ejecucion a terminados"""
def liberar_memoria(memoria, proceso, cola_ejecucion, cola_terminados):

    #En este caso se libera la particion que estaba ocupada en memoria
    for bloque in memoria:
        if bloque["id_proceso"] == proceso["id"]:
            bloque["id_proceso"] = None  # Liberar la particion
            break

    proceso["estado"] = "terminado" 

    for i, p in enumerate(cola_ejecucion):
        if p["id"] == proceso["id"]:
            cola_terminados.append(cola_ejecucion.pop(i))  # Se mueve el proceso a la cola de terminados
            break



""" Esta funcion se encargara de fusionar las particiones libres en memoria.
Cada que encuentra dos particiones continuas libres"""
def fusionar_particiones(memoria):
    i = 0
    while i < len(memoria) - 1:
        if memoria[i]["id_proceso"] is None and memoria[i + 1]["id_proceso"] is None:
            memoria[i]["tam"] += memoria[i + 1]["tam"]  # se suma el tamaño de las particiones libres
            memoria.pop(i + 1)  
            
            # Aclaracion: no incrementamos i para verificar la nueva particion fusionada
        else:
            i += 1

