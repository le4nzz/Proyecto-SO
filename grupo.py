import os

EXTENSIONES_VALIDAS = (".txt", ".csv")
MAX_PROCESOS = 10
TAM_MAX_USUARIO = 450 
TAM_MEMORIA_USUARIO = 450


# Módulo 1: Ivan
def validar_extension(ruta):
    
    if not ruta.lower().endswith(EXTENSIONES_VALIDAS):
        return False, "El archivo debe tener extensión .txt o .csv"
    if not os.path.isfile(ruta):
        return False, f"El archivo '{ruta}' no existe"
    return True, ""

def validar_linea(campos, ids_vistos):

    if len(campos) != 4:
        return False, f"se esperaban 4 campos {{#id, TA, TI, TAM}} y hay {len(campos)}"
    else:
        if any(campo == "" for campo in campos):
            return False, "hay campos vacíos"

        try:
            id_proc, ta, ti, tam = (int(c) for c in campos)
        except ValueError:
            return False, "todos los campos deben ser números enteros"

        if id_proc in ids_vistos:
            return False, f"el id {id_proc} está repetido"
        if ta < 0:
            return False, "TA no puede ser negativo"
        if ti <= 0:
            return False, "TI debe ser mayor que 0"
        if tam <= 0:
            return False, "TAM debe ser mayor que 0"
        if tam > TAM_MAX_USUARIO:
            return False, f"TAM ({tam}K) supera los {TAM_MAX_USUARIO}K de memoria de usuario"

        return True, ""

def leer_archivo(ruta):
    
    procesos = []
    errores = []
    ids_vistos = set()

    with open(ruta, "r") as archivo:
         for numero, linea in enumerate(archivo, start=1):
            linea = linea.strip()
            if linea == "" or linea.startswith("#"):
                continue

            campos = [c.strip() for c in linea.split(",")]
            es_valida, mensaje = validar_linea(campos, ids_vistos)

            if not es_valida:
                errores.append(f"Línea {numero}: {mensaje} -> '{linea}'")
                continue

            id_proc, ta, ti, tam = (int(c) for c in campos)
            ids_vistos.add(id_proc)
            procesos.append({"id": id_proc, "TA": ta, "TI": ti, "TAM": tam})

            if len(procesos) == MAX_PROCESOS:
                break 

    return procesos, errores

def obtener_ta(proc):
    return proc["TA"]

def ordenar_procesos(procesos):
    return sorted(procesos, key=obtener_ta)

def cargar_procesos(ruta):

    es_valida, mensaje = validar_extension(ruta)
    if not es_valida:
        return [], [mensaje]

    procesos, errores = leer_archivo(ruta)
    procesos = ordenar_procesos(procesos)

    if not procesos:
        errores.append("No se cargó ningún proceso válido")

    return procesos, errores

def admitir_nuevos(procesos, cola_nuevos, clock):

    admitidos = []
    while procesos and procesos[0]["TA"] <= clock:
        proc= procesos.pop(0)
        nuevo = {"id": proc["id"], "TA": proc["TA"], "TI": proc["TI"], "TAM": proc["TAM"], "tiempo_rest": proc["TI"],}
        cola_nuevos.append(nuevo)
        admitidos.append(nuevo)
    return admitidos



# Módulo 2: Tomas
def crear_memoria():
    return [{"inicio": 0, "tamanio": TAM_MEMORIA_USUARIO, "libre": True, "id_proc": None}]

def buscar_mejor_particion(memoria, tam):
    mejor_indice = None

    for i in range(len(memoria)):
        particion = memoria[i]
        if particion["libre"] and particion["tamanio"] >= tam:
            if mejor_indice is None or particion["tamanio"] < memoria[mejor_indice]["tamanio"]:
                mejor_indice = i

    return mejor_indice

def asignar_best_fit(memoria, proceso):
    indice = buscar_mejor_particion(memoria, proceso["TAM"])

    if indice is None:
        return False

    particion = memoria[indice]
    sobra = particion["tamanio"] - proceso["TAM"]


    particion["tamanio"] = proceso["TAM"]
    particion["libre"] = False
    particion["id_proc"] = proceso["id"]


    if sobra > 0:
        resto = {
            "inicio": particion["inicio"] + proceso["TAM"],
            "tamanio": sobra,
            "libre": True,
            "id_proc": None,
        }
        memoria.insert(indice + 1, resto)

    return True



# Módulo 3: Gonza
def srtf_seleccionar_proceso(proceso_en_ejecucion, cola_listos):

    if not cola_listos:
        return proceso_en_ejecucion, None


    candidato = min(cola_listos, key=lambda x: x['tiempo_rest'])

    if proceso_en_ejecucion is None:
        cola_listos.remove(candidato)
        return candidato, None


    if candidato['tiempo_rest'] < proceso_en_ejecucion['tiempo_rest']:

        cola_listos.remove(candidato)
        cola_listos.append(proceso_en_ejecucion)
        return candidato, proceso_en_ejecucion

    return proceso_en_ejecucion, None

def ejecutar_tick_cpu(proceso_en_ejecucion):

    if proceso_en_ejecucion is not None:
        proceso_en_ejecucion['tiempo_rest'] -= 1
        if proceso_en_ejecucion['tiempo_rest'] == 0:
            return True
    return False



#Módulo 4: Lean
def verificar_terminado(proceso):
    if proceso["TI"] == 0:
        print(f"El proceso {proceso['id']} ha terminado.")
        liberar_memoria(memoria, proceso, cola_ejecucion, cola_terminados)
        fusionar_particiones(memoria)
        return True
    return False

def liberar_memoria(memoria, proceso, cola_ejecucion, cola_terminados):


    for bloque in memoria:
        if bloque["id_proceso"] == proceso["id"]:
            bloque["id_proceso"] = None  # Liberar la particion
            break

    proceso["estado"] = "terminado" 

    for i, p in enumerate(cola_ejecucion):
        if p["id"] == proceso["id"]:
            cola_terminados.append(cola_ejecucion.pop(i))
            break

def fusionar_particiones(memoria):
    i = 0
    while i < len(memoria) - 1:
        if memoria[i]["id_proceso"] is None and memoria[i + 1]["id_proceso"] is None:
            memoria[i]["tam"] += memoria[i + 1]["tam"]
            memoria.pop(i + 1)  
            
           
        else:
            i += 1



#Módulo 5: Edgar
def admision_suspendidos_y_nuevos_best_fit(cola_suspendidos, cola_nuevos, cola_listos, memoria, clock):

  admitidos_en_este_tick = []

  for p in list(cola_suspendidos):  
    if asignar_best_fit(memoria, p):
      p["estado"] = "listo"
      cola_listos.append(p)
      cola_suspendidos.remove(p)
      admitidos_en_este_tick.append(p)
      print(
          f"[Clock {clock}] Proceso {p['id']} (TAM: {p['TAM']}K) des-suspendido"
          " -> Asignado a memoria -> Cola de Listos."
      )


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

      p["estado"] = "suspendido"
      cola_suspendidos.append(p)
      cola_nuevos.remove(p)
      print(
          f"[Clock {clock}] Proceso {p['id']} (TAM: {p['TAM']}K) nuevo sin"
          " espacio en memoria -> Movido a Cola de Suspendidos."
      )

  return admitidos_en_este_tick



#Módulo 6: Benja
def calcular_estadisticas(cola_terminados):

    for p in cola_terminados:
        p["tiempo_retorno"] = p["tiempo_fin"] - p["TA"]
        p["tiempo_espera"] = p["tiempo_retorno"] - p["TI"]

    cantidad = len(cola_terminados)
    promedio_retorno = sum(p["tiempo_retorno"] for p in cola_terminados) / cantidad
    promedio_espera = sum(p["tiempo_espera"] for p in cola_terminados) / cantidad
    tiempo_total = max(p["tiempo_fin"] for p in cola_terminados)

    return promedio_retorno, promedio_espera, cantidad / tiempo_total

def mostrar_informe_final(cola_terminados):
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

def print_procesos():

    print(f"Admitidos en clock {clock}:")
    for p in cola_nuevos:
        print(p)

    if errores:
        print(f"\n Se generaron los siguientes errores al cargar el archivo:")
        for error in errores:
            print(f"\n {error}")

    cola_Listos = []
    memo = crear_memoria()

    print_procesos()
    if(cola_nuevos):
        for p in cola_nuevos:
            if asignar_best_fit(memo, p):
                print(f"Proceso {p['id']} asignado a memoria.")
                cola_Listos.append(p)
                cola_nuevos.remove(p)
                print_procesos()

            else:
                print(f"No hay espacio para el proceso {p['id']}.")



#Módulo 7: Eze
def mostrar_estado_cpu():

def mostrar_tabla_particiones():

def mostrar_colas():

def mostrar_evento():



if __name__ == "__main__":

    import sys

    ruta_archivo = sys.argv[1] if len(sys.argv) > 1 else "procesos_ejemplo.csv"
    lista_procesos, lista_errores = cargar_procesos(ruta_archivo)

    for error in lista_errores:
        print("[AVISO]", error)

    print("\nProcesos cargados:")
    for p in lista_procesos:
        print(p)

    cola_nuevos = []
    clock = 0
    while lista_procesos:
        for p in admitir_nuevos(lista_procesos, cola_nuevos, clock):
            print(f"clock={clock}: llegó el proceso {p['id']}")
        clock += 1

    
    carpeta = os.path.dirname(os.path.abspath(__file__)) 
    ruta = os.path.join(carpeta, "procesos_ejemplo.txt")

    procesos, errores = cargar_procesos(ruta)
    cola_nuevos = []

    clock = int(input("Ingrese el instante de clock: "))


    admitir_nuevos(procesos, cola_nuevos, clock)