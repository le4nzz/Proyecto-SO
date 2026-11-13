import sys
import os
import pathlib
import textwrap
import math

CARPETA_PROCESOS = pathlib.Path(sys.executable).parent if getattr(sys, "frozen", False) else patpathlib.Path(__file__).parent
EXTENSIONES_VALIDAS = ("*.txt", "*.csv")
MAX_LINEAS_ARCHIVO = 100
CAMPOS_ARCHIVO = 4

TAM_MEMORIA_SO = 100
TAM_MEMORIA_USUARIO = 450

MAX_PROCESOS = 10
MAX_PROCESOS_ACTIVOS = 5

ESTADO_PENDIENTE = "Pendiente"
ESTADO_NUEVO = "Nuevo"
ESTADO_LISTO = "Listo"
ESTADO_SUSPENDIDO = "Suspendido"
ESTADO_EJECUCION = "Ejecución"
ESTADO_TERMINADO = "Terminado"


# ==========================================================================
# Menú y utilidades de pantalla
# ==========================================================================

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def esperar_enter(mensaje="\nEnter para continuar "):
    input(mensaje)


def hay_archivos_validos():
    return bool(buscar_archivos_validos())


def buscar_archivos_validos():
    archivos = []
    for patron in EXTENSIONES_VALIDAS:
        for archivo in CARPETA_PROCESOS.glob(patron):
            if archivo.is_file() and archivo.stat().st_size > 0:
                archivos.append(archivo.name)
    return sorted(archivos)


def mostrar_archivos_disponibles(archivos, archivo_elegido):
    print("Archivos disponibles (carpeta del programa)\n")
    for i, nombre in enumerate(archivos, start=1):
        print(f"[{i}] {nombre} {'(seleccionado)' if archivo_elegido == nombre else ''}")
    print("\n[0] Volver al menu")


def elegir_archivo(archivo_elegido):
    archivos = buscar_archivos_validos()
    while True:
        limpiar_pantalla()
        mostrar_archivos_disponibles(archivos, archivo_elegido)

        print("\nSeleccione un archivo y presione Enter > ", end="")
        seleccion = input().strip()

        if seleccion == "0":
            break

        if not seleccion.isdecimal() or not (1 <= int(seleccion) <= len(archivos)):
            esperar_enter("\nRespuesta inválida, Enter e inténtelo de nuevo ")
            continue

        candidato = archivos[int(seleccion) - 1]

        print(f"\nArchivo: {candidato}\n")
        try:
            with open(CARPETA_PROCESOS / candidato, encoding="utf-8-sig") as archivo:
                for i, linea in enumerate(archivo, start=1):
                    if i > MAX_LINEAS_ARCHIVO:
                        break
                    print(linea, end="")
        except (OSError, UnicodeDecodeError):
            esperar_enter("\nNo se pudo leer el archivo, Enter para volver a la lista ")
            continue

        confirmacion = input("\n\nConfirmar [s/n]? > ").strip().lower()

        if confirmacion == "s" or confirmacion == "":
            return candidato


def ejecutar_menu():
    archivo_elegido = None

    while True:
        limpiar_pantalla()
        print(textwrap.dedent(f'''\
        SIMULADOR v2

        Archivo seleccionado: {archivo_elegido or '(vacío)'}

        [1] Iniciar simulador
        [2] Elegir archivo
        [3] Formato del archivo

        [4] Salir

        Seleccione una opción y presione Enter > '''), end='')

        seleccion = input().strip()

        match seleccion:
            case "1" if archivo_elegido is None:
                esperar_enter("\nPrimero elija un archivo (opción 2), Enter para regresar ")
            case "1":
                ejecutar_simulador(archivo_elegido)
            case "2":
                if hay_archivos_validos():
                    nuevo = elegir_archivo(archivo_elegido)
                    if nuevo is not None:
                        archivo_elegido = nuevo
                else:
                    print("\nNo hay archivos .txt o .csv en la carpeta del programa")
                    esperar_enter()
            case "3":
                mostrar_formato_archivo()
            case "4":
                return
            case _:
                esperar_enter("\nRespuesta inválida, Enter para regresar ")


def mostrar_formato_archivo():
    limpiar_pantalla()

    print(textwrap.dedent(
    f"""
    Guarde su archivo .txt o .csv en la misma carpeta que main.py
    Formato esperado del archivo:

        #ID, TA, TI, TAM(KB)
        P1, 0, 6, 150
        P2, 5, 5, 50
        P3, 10, 4, 80
        ...

    - TA = tiempo de arribo | TI = tiempo de irrupción | TAM = tamaño
    - Un proceso por línea, {CAMPOS_ARCHIVO} campos separados por comas, en el orden ID, TA, TI, TAM. El ID puede llevar la P (P1) o no (1). Se ignoran las líneas vacías y las que empiezan con #.
    - Valores válidos: enteros no negativos. TI y TAM deben ser mayores a 0. TAM máximo: {TAM_MEMORIA_USUARIO}K.
    - Sin IDs repetidos, máximo {MAX_PROCESOS} procesos.
    - Se leen como máximo {MAX_LINEAS_ARCHIVO} líneas."""))

    esperar_enter()


# ==========================================================================
# Módulo 1: Ivan (carga y validación del archivo)
# ==========================================================================
# CAMBIOS sobre el módulo original:
#  - El orden de columnas pasa a ser id, TA, TI, TAM (como los lotes de prueba de la cátedra).
#  - El id se acepta con o sin prefijo P (P1 o 1).
#  - Se usa TAM_MEMORIA_USUARIO (se elimina TAM_MAX_USUARIO, era el mismo valor).
#  - validar_linea ahora también controla el máximo de 3 dígitos por campo.
#  - Los mensajes de error se acortaron para que entren en la tabla de análisis.
#  - leer_archivo abre con utf-8-sig (tildes y BOM de Windows), respeta
#    MAX_LINEAS_ARCHIVO y devuelve una fila por línea para la tabla de análisis,
#    en lugar de una lista de textos de error.
#  - Cada proceso se crea ya con tiempo_rest, estado y tiempo_fin.
#  - admitir_nuevos ya no copia el proceso: mueve el mismo diccionario, así la
#    tabla de procesos (lista maestra) ve los cambios de estado.
#  - Se quitó el bloque de prueba que estaba en __main__.

def validar_extension(ruta):
    extensiones = tuple(e[1:] for e in EXTENSIONES_VALIDAS)
    if not str(ruta).lower().endswith(extensiones):
        return False, "El archivo debe tener extensión .txt o .csv"
    if not os.path.isfile(ruta):
        return False, f"El archivo '{ruta}' no existe"
    return True, ""


def es_entero(campo):
    digitos = campo[1:] if campo.startswith("-") else campo
    return digitos.isdecimal()


def validar_linea(campos, ids_vistos):
    if len(campos) != CAMPOS_ARCHIVO:
        return False, "Cantidad de campos incorrecta"
    if any(campo == "" for campo in campos):
        return False, "Hay campos vacíos"
    if not all(es_entero(c) for c in campos):
        return False, "Campo no numérico"
    if any(len(c) > 3 for c in campos):
        return False, "Número superior a 3 dígitos"

    id_proc, ta, ti, tam = (int(c) for c in campos)

    if id_proc < 0:
        return False, "El id no puede ser negativo"
    if id_proc in ids_vistos:
        return False, "ID de proceso duplicado"
    if ta < 0:
        return False, "TA no puede ser negativo"
    if ti <= 0:
        return False, "Tiempo de irrupción inválido"
    if tam <= 0 or tam > TAM_MEMORIA_USUARIO:
        return False, "Tamaño fuera de rango"

    return True, ""


def leer_archivo(ruta):
    procesos = []
    lineas = []
    ids_vistos = set()
    se_excedio = False

    with open(ruta, "r", encoding="utf-8-sig") as archivo:
        for numero, linea in enumerate(archivo, start=1):
            if numero > MAX_LINEAS_ARCHIVO:
                se_excedio = True
                break

            texto = linea.strip()

            if texto.startswith("#"):
                lineas.append({"linea": numero, "contenido": linea, "motivo": "Comentario ignorado"})
                continue

            if texto == "":
                lineas.append({"linea": numero, "contenido": linea, "motivo": "Línea vacía ignorada"})
                continue

            campos = [c.strip() for c in texto.split(",")]
            if campos[0][:1] in ("P", "p"):
                campos[0] = campos[0][1:]
            es_valida, mensaje = validar_linea(campos, ids_vistos)

            if es_valida and len(procesos) >= MAX_PROCESOS:
                es_valida = False
                mensaje = f"Límite alcanzado de procesos, máx. {MAX_PROCESOS}"

            if not es_valida:
                lineas.append({"linea": numero, "contenido": linea, "motivo": mensaje})
                continue

            id_proc, ta, ti, tam = (int(c) for c in campos)
            ids_vistos.add(id_proc)
            procesos.append(
                {
                    "id": id_proc,
                    "TAM": tam,
                    "TA": ta,
                    "TI": ti,
                    "tiempo_rest": ti,
                    "tiempo_fin": None,
                    "estado": ESTADO_PENDIENTE,
                }
            )
            lineas.append({"linea": numero, "contenido": linea, "motivo": "Correcto"})

    return procesos, lineas, se_excedio


def obtener_ta(proc):
    return proc["TA"]


def ordenar_procesos(procesos):
    return sorted(procesos, key=obtener_ta)


def cargar_procesos(ruta):
    es_valida, mensaje = validar_extension(ruta)
    if not es_valida:
        return [], [], False, mensaje

    try:
        procesos, lineas, se_excedio = leer_archivo(ruta)
    except (OSError, UnicodeDecodeError):
        return [], [], False, "No se pudo leer el archivo (permisos o codificación)"

    return ordenar_procesos(procesos), lineas, se_excedio, ""


def admitir_nuevos(procesos, cola_nuevos, clock):
    admitidos = []
    while procesos and procesos[0]["TA"] <= clock:
        proc = procesos.pop(0)
        proc["estado"] = ESTADO_NUEVO
        cola_nuevos.append(proc)
        admitidos.append(proc)
    return admitidos


def mostrar_lineas_archivo(lineas_analizadas):
    ancho_linea = 5
    ancho_contenido = 50
    ancho_motivo = 40

    barra_linea = "─" * ancho_linea
    barra_contenido = "─" * ancho_contenido
    barra_motivo = "─" * ancho_motivo

    print(f"Análisis del archivo")

    print(f"┌─{barra_linea}─┬─{barra_contenido}───{barra_motivo}─┐")
    print(f"│ {"Línea":<{ancho_linea}} │ {"Contenido":<{ancho_contenido}}   {"Motivo":<{ancho_motivo}} │")
    print(f"├─{barra_linea}─┼─{barra_contenido}───{barra_motivo}─┤")

    for r in lineas_analizadas:
        print(f"│ {r["linea"]:>{ancho_linea}} ", end="")
        print(f"│ {r["contenido"].rstrip("\r\n")[:ancho_contenido]:<{ancho_contenido}} ", end="")
        print(f"  {r["motivo"][:ancho_motivo]:<{ancho_motivo}} │")

    print(f"└─{barra_linea}─┴─{barra_contenido}───{barra_motivo}─┘")


def hay_procesos_validos(sistema):
    return bool(sistema["procesos"])


# ==========================================================================
# Módulo 2: Tomas (memoria, Best-Fit)
# ==========================================================================
# CAMBIO: crear_memoria incluye primero la partición del SO (100K, ocupada),
# así las direcciones de usuario arrancan en 100 como en la salida.
# buscar_mejor_particion y asignar_best_fit quedan sin cambios.

def crear_memoria():
    return [
        {"inicio": 0, "tamanio": TAM_MEMORIA_SO, "libre": False, "id_proc": "SO"},
        {"inicio": TAM_MEMORIA_SO, "tamanio": TAM_MEMORIA_USUARIO, "libre": True, "id_proc": None},
    ]


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


# ==========================================================================
# Módulo 3: Gonza (SRTF)
# ==========================================================================
# Sin cambios de lógica. (El estado de los procesos lo actualiza planificar_cpu.)

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


# ==========================================================================
# Módulo 4: Lean (terminar proceso y liberar memoria)
# ==========================================================================
# CAMBIOS (el módulo original no podía ejecutarse):
#  - verificar_terminado compara tiempo_rest (antes TI, que nunca baja) y
#    recibe memoria, terminados y reloj por parámetro (antes usaba globales).
#  - Se quitó el print: la pantalla la maneja mostrar_evento_y_esperar.
#  - liberar_memoria marca libre=True e id_proc=None (antes "id_proceso") y
#    guarda tiempo_fin, que necesitan las estadísticas.
#  - fusionar_particiones usa las claves "libre" y "tamanio" de Tomas.

def verificar_terminado(proceso, memoria, cola_terminados, clock):
    if proceso["tiempo_rest"] == 0:
        liberar_memoria(memoria, proceso, cola_terminados, clock)
        fusionar_particiones(memoria)
        return True
    return False


def liberar_memoria(memoria, proceso, cola_terminados, clock):
    for bloque in memoria:
        if bloque["id_proc"] == proceso["id"]:
            bloque["libre"] = True
            bloque["id_proc"] = None
            break

    proceso["estado"] = ESTADO_TERMINADO
    proceso["tiempo_fin"] = clock
    cola_terminados.append(proceso)


def fusionar_particiones(memoria):
    i = 0
    while i < len(memoria) - 1:
        if memoria[i]["libre"] and memoria[i + 1]["libre"]:
            memoria[i]["tamanio"] += memoria[i + 1]["tamanio"]
            memoria.pop(i + 1)
        else:
            i += 1


# ==========================================================================
# Módulo 5: Edgar (admisión de suspendidos y nuevos)
# ==========================================================================
# CAMBIOS:
#  - Se agrega el límite de MAX_PROCESOS_ACTIVOS (Ejecución + Listos +
#    Suspendidos). Solo frena a los Nuevos: un Suspendido ya cuenta como activo.
#  - Ya no imprime (limpiar_pantalla lo borraría). Devuelve una lista de
#    (proceso, destino) con lo que pasó con cada uno.
#  - Recibe en_cpu para poder contar los activos.
#  - Usa constantes de estado (antes "listo"/"suspendido" en minúscula).

def contar_procesos_activos(cola_listos, cola_suspendidos, en_cpu):
    return len(cola_listos) + len(cola_suspendidos) + (0 if en_cpu is None else 1)


def admision_suspendidos_y_nuevos_best_fit(cola_suspendidos, cola_nuevos, cola_listos, memoria, en_cpu):
    resultados = []

    for p in list(cola_suspendidos):
        if asignar_best_fit(memoria, p):
            p["estado"] = ESTADO_LISTO
            cola_listos.append(p)
            cola_suspendidos.remove(p)
            resultados.append((p, ESTADO_LISTO))

    for p in list(cola_nuevos):
        if contar_procesos_activos(cola_listos, cola_suspendidos, en_cpu) >= MAX_PROCESOS_ACTIVOS:
            break

        if asignar_best_fit(memoria, p):
            p["estado"] = ESTADO_LISTO
            cola_listos.append(p)
            cola_nuevos.remove(p)
            resultados.append((p, ESTADO_LISTO))
        else:
            p["estado"] = ESTADO_SUSPENDIDO
            cola_suspendidos.append(p)
            cola_nuevos.remove(p)
            resultados.append((p, ESTADO_SUSPENDIDO))

    return resultados


# ==========================================================================
# Módulo 6: Benja (estadísticas)
# ==========================================================================
# CAMBIOS:
#  - tiempo_fin ahora existe (lo guarda Lean).
#  - calcular_estadisticas devuelve también el tiempo total.
#  - mostrar_informe_final usa las tablas con bordes del resto de las pantallas
#    y lista los procesos en orden de finalización (antes ordenaba el id como
#    texto, y P10 quedaba antes que P2).
#  - Se quitó print_procesos (era código de prueba con variables inexistentes).

def calcular_estadisticas(cola_terminados):
    for p in cola_terminados:
        p["tiempo_retorno"] = p["tiempo_fin"] - p["TA"]
        p["tiempo_espera"] = p["tiempo_retorno"] - p["TI"]

    cantidad = len(cola_terminados)
    promedio_retorno = sum(p["tiempo_retorno"] for p in cola_terminados) / cantidad
    promedio_espera = sum(p["tiempo_espera"] for p in cola_terminados) / cantidad
    tiempo_total = max(p["tiempo_fin"] for p in cola_terminados)

    return promedio_retorno, promedio_espera, cantidad / tiempo_total, tiempo_total


def mostrar_informe_final(cola_terminados):
    if not cola_terminados:
        print("No hay procesos terminados para mostrar estadísticas.")
        return

    promedio_retorno, promedio_espera, rendimiento, tiempo_total = calcular_estadisticas(cola_terminados)

    ancho_id = 4
    ancho_otro = 9
    barra_id = "─" * ancho_id
    barra_otro = "─" * ancho_otro

    print(f"\nInforme estadístico")

    print(f"┌─{barra_id}─┬─{barra_otro}─┬─{barra_otro}─┐")
    print(f"│ {"ID":<{ancho_id}} │ {"Retorno":<{ancho_otro}} │ {"Espera":<{ancho_otro}} │")
    print(f"├─{barra_id}─┼─{barra_otro}─┼─{barra_otro}─┤")

    for p in cola_terminados:
        print(f"│ {nombre_proceso(p):<{ancho_id}} │ {p["tiempo_retorno"]:>{ancho_otro}} │ {p["tiempo_espera"]:>{ancho_otro}} │")

    print(f"└─{barra_id}─┴─{barra_otro}─┴─{barra_otro}─┘")
    print()

    print(f"Tiempo promedio de retorno: {promedio_retorno:.2f} s")
    print(f"Tiempo promedio de espera: {promedio_espera:.2f} s")
    print(f"Rendimiento del sistema: {rendimiento:.2f}")
    print(f"Cantidad de procesos finalizados {len(cola_terminados)}")
    print(f"Tiempo total de simulación {tiempo_total} s")


# ==========================================================================
# Simulador (bucle principal)
# ==========================================================================

def crear_sistema(procesos):
    return {
        "reloj": 0,
        "procesos": procesos,
        "pendientes": list(procesos),
        "nuevos": [],
        "listos": [],
        "en_cpu": None,
        "suspendidos": [],
        "terminados": [],
        "memoria": crear_memoria(),
    }


def hay_procesos_por_atender(sistema):
    return len(sistema["terminados"]) != len(sistema["procesos"])


def proceso_llego(sistema):
    return bool(sistema["pendientes"]) and sistema["pendientes"][0]["TA"] <= sistema["reloj"]


def registrar_llegada(sistema):
    admitir_nuevos(sistema["pendientes"], sistema["nuevos"], sistema["reloj"])


def admitir_procesos(sistema):
    return admision_suspendidos_y_nuevos_best_fit(
        sistema["suspendidos"],
        sistema["nuevos"],
        sistema["listos"],
        sistema["memoria"],
        sistema["en_cpu"],
    )


def planificar_cpu(sistema):
    nuevo, desplazado = srtf_seleccionar_proceso(sistema["en_cpu"], sistema["listos"])
    if nuevo is not None:
        nuevo["estado"] = ESTADO_EJECUCION
    if desplazado is not None:
        desplazado["estado"] = ESTADO_LISTO
    sistema["en_cpu"] = nuevo


def ejecutar_simulador(archivo_elegido):
    procesos, lineas_analizadas, se_excedio, error = cargar_procesos(CARPETA_PROCESOS / archivo_elegido)

    limpiar_pantalla()

    if error:
        print(error)
        esperar_enter()
        return

    mostrar_lineas_archivo(lineas_analizadas)

    if se_excedio:
        esperar_enter(f"Se ignoraron las líneas siguientes a la {MAX_LINEAS_ARCHIVO}.")
    else:
        esperar_enter()

    sistema = crear_sistema(procesos)
    se_mostro = set()

    if not hay_procesos_validos(sistema):
        print(f"No hay procesos válidos en el archivo {archivo_elegido} para el simulador.")
        esperar_enter()
        return

    while hay_procesos_por_atender(sistema):
        if proceso_llego(sistema):
            registrar_llegada(sistema)
            admitir_procesos(sistema)
            planificar_cpu(sistema)
            if sistema["reloj"] not in se_mostro:
                mostrar_evento_y_esperar(sistema, se_mostro, "Llega")

        termino = ejecutar_tick_cpu(sistema["en_cpu"])

        sistema["reloj"] += 1

        if termino and verificar_terminado(sistema["en_cpu"], sistema["memoria"], sistema["terminados"], sistema["reloj"]):
            sistema["en_cpu"] = None
            registrar_llegada(sistema)
            admitir_procesos(sistema)
            planificar_cpu(sistema)
            mostrar_evento_y_esperar(sistema, se_mostro, "Termina")

    mostrar_informe_final(sistema["terminados"])
    esperar_enter("\nFIN del simulador, Enter para volver al menu")


# ==========================================================================
# Pantallas del simulador (Eze)
# ==========================================================================

def nombre_proceso(p):
    return f"P{p['id']}"


def nombre_particion(particion):
    if particion["libre"]:
        return ""
    if particion["id_proc"] == "SO":
        return "SO"
    return f"P{particion['id_proc']}"


def particion_proceso(sistema, p):
    for i, particion in enumerate(sistema["memoria"], start=1):
        if not particion["libre"] and particion["id_proc"] == p["id"]:
            return i


def estado_proceso(sistema, p):
    return "" if p["estado"] == ESTADO_PENDIENTE else p["estado"]


def mostrar_colas_resumen(cola):
    if not bool(cola):
        print("")
    else:
        for p in cola:
            print(f"{nombre_proceso(p)}({p["tiempo_rest"]}) ", end="")
        print()


def mostrar_estado_cpu(sistema, evento):
    print(f"Reloj = {sistema["reloj"]} s")

    print(f"\nEvento")
    if evento == "Llega":
        for p in sistema["procesos"]:
            estado = estado_proceso(sistema, p)
            if p["TA"] == sistema["reloj"]:
                if p == sistema["en_cpu"]:
                    print(f"    {nombre_proceso(p)} → Listo (partición {particion_proceso(sistema, p)}) → {estado}")
                elif p in sistema["listos"]:
                    print(f"    {nombre_proceso(p)} → {estado} (partición {particion_proceso(sistema, p)})")
                else:
                    print(f"    {nombre_proceso(p)} → {estado}")

    if evento == "Termina":
        for p in sistema["procesos"]:
            if p["tiempo_fin"] == sistema["reloj"]:
                print(f"    {nombre_proceso(p)} → Terminado")
                break
        if sistema["en_cpu"] is not None:
            print(f"    {nombre_proceso(sistema["en_cpu"])} → Ejecución")

    print(f"\nSistema")
    en_cpu = sistema["en_cpu"]
    print(f"    CPU         = {"" if en_cpu is None else f"{nombre_proceso(en_cpu)}({en_cpu["tiempo_rest"]})"}")
    print(f"    Listos      = ", end="")
    mostrar_colas_resumen(sistema["listos"])

    print(f"    Suspendidos = ", end="")
    mostrar_colas_resumen(sistema["suspendidos"])

    print(f"    Nuevos      = ", end="")
    mostrar_colas_resumen(sistema["nuevos"])


def libre_anterior(memoria, i):
    return i != 0 and memoria[i - 1]["libre"]


def dibujar_barra_particiones(sistema):
    memoria = sistema["memoria"]
    kb = 5
    print("\nParticiones")
    print("┌", end="")
    for p in memoria:
        ancho = math.ceil(p["tamanio"] / kb)
        proceso = nombre_particion(p)

        print(f"{proceso}{"─" * (ancho - len(proceso))}", end="")
    print("┐")

    print("│", end="")
    for i, p in enumerate(memoria):
        ancho = math.ceil(p["tamanio"] / kb)

        if not p["libre"]:
            if libre_anterior(memoria, i):
                print(f"▐{"█" * (ancho - 2)}▌", end="")
            else:
                print(f"{"█" * (ancho - 1)}▌", end="")
        else:
            print(f"{"░" * ancho}", end="")

    print("│")

    print(f"└", end="")
    for p in memoria:
        ancho = math.ceil(p["tamanio"] / kb)
        tamanio = p["inicio"] + p["tamanio"]

        if ancho > 2:
            print(f"{"─" * (ancho - len(str(tamanio)))}{tamanio}", end="")
        else:
            print(f"{"─" * ancho}", end="")

    print(f"┘")


def mostrar_tabla_particiones(sistema):
    ancho_id = 4
    ancho_proceso = 7
    ancho_otro = 7
    barra_id = "─" * ancho_id
    barra_proceso = "─" * ancho_proceso
    barra_otro = "─" * ancho_otro

    print(f"┌─{barra_id}─┬─{barra_proceso}─┬─{barra_otro}─┬─{barra_otro}─┐")
    print(f"│ {"Part":<{ancho_id}} │ {"Proceso":^{ancho_proceso}} │ {"Inicio":^{ancho_otro}} │ {"TAM(KB)":^{ancho_otro}} │")
    print(f"├─{barra_id}─┼─{barra_proceso}─┼─{barra_otro}─┼─{barra_otro}─┤")

    for i, p in enumerate(sistema["memoria"], start=1):
        print(f"│ {i:<{ancho_id}} ", end="")
        print(f"│ {nombre_particion(p):<{ancho_proceso}} ", end="")
        print(f"│ {p["inicio"]:>{ancho_otro}} ", end="")
        print(f"│ {p["tamanio"]:>{ancho_otro}} │ {"← Libre" if p["libre"] else ""}")

    print(f"└─{barra_id}─┴─{barra_proceso}─┴─{barra_otro}─┴─{barra_otro}─┘")


def contar_pendientes(sistema):
    return sum(estado_proceso(sistema, p) == "" for p in sistema["procesos"])


def mostrar_colas(sistema):
    ancho_id = 4
    ancho_estado = 10
    ancho_restante = 8
    ancho_otro = 3

    barra_id = "─" * ancho_id
    barra_estado = "─" * ancho_estado
    barra_otro = "─" * ancho_otro
    barra_restante = "─" * ancho_restante

    print("\nProcesos")
    print(f"┌─{barra_id}─┬─{barra_estado}─┬─{barra_otro}─┬─{barra_otro}─┬─{barra_otro}─┬─{barra_restante}─┬─{barra_restante}─┐")

    print(f"│ {"ID":<{ancho_id}} ", end="")
    print(f"│ {"Estado":<{ancho_estado}} ", end="")
    print(f"│ {"TA":<{ancho_otro}} ", end="")
    print(f"│ {"TI":<{ancho_otro}} ", end="")
    print(f"│ {"TAM":<{ancho_otro}} ", end="")
    print(f"│ {"Restante":<{ancho_restante}} ", end="")
    print(f"│ {"Fin":<{ancho_restante}} │")

    print(f"├─{barra_id}─┼─{barra_estado}─┼─{barra_otro}─┼─{barra_otro}─┼─{barra_otro}─┼─{barra_restante}─┼─{barra_restante}─┤")

    for p in sistema["procesos"]:
        estado = estado_proceso(sistema, p)
        fin = "" if p["tiempo_fin"] is None else p["tiempo_fin"]
        print(f"│ {nombre_proceso(p):<{ancho_id}} ", end="")
        print(f"│ {estado:<{ancho_estado}} ", end="")
        print(f"│ {p["TA"]:>{ancho_otro}} ", end="")
        print(f"│ {p["TI"]:>{ancho_otro}} ", end="")
        print(f"│ {p["TAM"]:>{ancho_otro}} ", end="")
        print(f"│ {p["tiempo_rest"]:>{ancho_restante}} ", end="")
        print(f"│ {fin:>{ancho_restante}} │")

    print(f"└─{barra_id}─┴─{barra_estado}─┴─{barra_otro}─┴─{barra_otro}─┴─{barra_otro}─┴─{barra_restante}─┴─{barra_restante}─┘")

    activos = contar_procesos_activos(sistema["listos"], sistema["suspendidos"], sistema["en_cpu"])
    print(f"\nActivos = {activos} ", end="")
    print(f"| Terminados = {len(sistema["terminados"])} ", end="")
    print(f"| Pendientes = {contar_pendientes(sistema)}")


def mostrar_evento_y_esperar(sistema, se_mostro, evento):
    limpiar_pantalla()

    mostrar_estado_cpu(sistema, evento)
    dibujar_barra_particiones(sistema)
    mostrar_tabla_particiones(sistema)
    mostrar_colas(sistema)

    se_mostro.add(sistema["reloj"])

    esperar_enter()


if __name__ == "__main__":
    ejecutar_menu()