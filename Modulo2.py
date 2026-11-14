# Módulo 2: Asignación de memoria, best-fit.

# CAMBIOS sobre el módulo original (integración al simulador):
#  - TAM_MEMORIA_USUARIO pasó a constantes.py.
#  - crear_memoria agrega primero la partición del SO (100K, ocupada), así las
#    direcciones de usuario empiezan en 100 como en la salida.
#  - buscar_mejor_particion y asignar_best_fit quedan sin cambios.

from constantes import TAM_MEMORIA_SO, TAM_MEMORIA_USUARIO

#creamos las particiones iniciales: el SO (ocupada) y la memoria total disponible para los procesos de usuario
def crear_memoria():
    return [
        {"inicio": 0, "tamanio": TAM_MEMORIA_SO, "libre": False, "id_proc": "SO"},
        {"inicio": TAM_MEMORIA_SO, "tamanio": TAM_MEMORIA_USUARIO, "libre": True, "id_proc": None},
    ]

#la funcion que busca la mejor particion libre para un proceso de tamaño 'tam'
def buscar_mejor_particion(memoria, tam):
    mejor_indice = None

    for i in range(len(memoria)):
        particion = memoria[i]
        if particion["libre"] and particion["tamanio"] >= tam:
            if mejor_indice is None or particion["tamanio"] < memoria[mejor_indice]["tamanio"]:
                mejor_indice = i

    return mejor_indice

# la funcion que asigna un proceso a la memoria, si no hay espacio devuelve False
def asignar_best_fit(memoria, proceso):
    indice = buscar_mejor_particion(memoria, proceso["TAM"])

    if indice is None:
        return False

    particion = memoria[indice]
    sobra = particion["tamanio"] - proceso["TAM"]

    # La partición queda ocupada con el tamaño justo del proceso
    particion["tamanio"] = proceso["TAM"]
    particion["libre"] = False
    particion["id_proc"] = proceso["id"]

    # Si sobró espacio, se crea una partición libre justo después
    if sobra > 0:
        resto = {
            "inicio": particion["inicio"] + proceso["TAM"],
            "tamanio": sobra,
            "libre": True,
            "id_proc": None,
        }
        memoria.insert(indice + 1, resto)

    return True
