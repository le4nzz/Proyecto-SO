
"""
Gestiona la memoria principal del simulador con particiones variables y la
política de asignación Best-Fit (mejor ajuste).

La memoria se representa como una lista de particiones (diccionarios), ordenada
por dirección de inicio. Cada partición tiene:
    "inicio":  dirección donde empieza la partición (en K)
    "tamanio": tamaño de la partición (en K)
    "libre":   True si está disponible, False si está ocupada
    "id_proc": id del proceso que la ocupa, "SO" para el sistema operativo,
               o None si la partición está libre

Funciones del módulo:
    crear_memoria()          -> arma la memoria inicial (SO + zona de usuario)
    buscar_mejor_particion() -> elige la partición libre más ajustada (Best-Fit)
    asignar_best_fit()       -> ubica un proceso en memoria y parte la partición

Quien libera la memoria y fusiona particiones libres contiguas es el módulo 4.


"""

from constantes import TAM_MEMORIA_SO, TAM_MEMORIA_USUARIO


def crear_memoria():
    """
    Crea la memoria inicial del simulador.

    Devuelve una lista con dos particiones:
      1. El sistema operativo: desde 0, tamaño TAM_MEMORIA_SO, ocupada ("SO").
      2. La zona de usuario: empieza en TAM_MEMORIA_SO, tamaño
         TAM_MEMORIA_USUARIO, completamente libre.
    """
    return [
        {"inicio": 0, "tamanio": TAM_MEMORIA_SO, "libre": False, "id_proc": "SO"},
        {"inicio": TAM_MEMORIA_SO, "tamanio": TAM_MEMORIA_USUARIO, "libre": True, "id_proc": None},
    ]


def buscar_mejor_particion(memoria, tam):
    """
    Busca la partición libre más ajustada para un proceso de tamaño 'tam'
    (criterio Best-Fit).

    Recorre toda la memoria y, entre las particiones libres donde el proceso
    entra (tamanio >= tam), se queda con la de menor tamaño.

    Parámetros:
        memoria: lista de particiones (ver descripción del módulo).
        tam:     tamaño que necesita el proceso (en K).

    Devuelve el índice de la partición elegida dentro de 'memoria',
    o None si ninguna partición libre alcanza.
    """
    mejor_indice = None

    for i in range(len(memoria)):
        particion = memoria[i]
        # Solo se consideran particiones libres donde el proceso entra
        if particion["libre"] and particion["tamanio"] >= tam:
            # Si es la primera candidata, o es más chica que la mejor hasta ahora, la reemplaza
            if mejor_indice is None or particion["tamanio"] < memoria[mejor_indice]["tamanio"]:
                mejor_indice = i

    return mejor_indice


def asignar_best_fit(memoria, proceso):
    """
    Asigna un proceso a la memoria usando Best-Fit.

    Busca la mejor partición con buscar_mejor_particion. Si la encuentra, la
    marca como ocupada por el proceso y la recorta al tamaño justo (proceso["TAM"]).
    Si sobra espacio, el sobrante queda como una nueva partición libre ubicada
    después.

    Parámetros:
        memoria: lista de particiones; se modifica en el lugar.
        proceso: diccionario del proceso; usa las claves "TAM" e "id".

    Devuelve True si el proceso quedó asignado, False si no hay espacio
    (en ese caso la memoria no se modifica).
    """
    indice = buscar_mejor_particion(memoria, proceso["TAM"])

    # No hay ninguna partición libre lo bastante grande
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
