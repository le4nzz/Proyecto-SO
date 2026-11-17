#Módulo 7: Menú, pantallas y bucle principal del simulador.

"""
Es la parte que une todo: pide el archivo, corre la simulación evento por
evento (usando los módulos 1 a 6) y muestra el estado en cada llegada o
finalización de proceso.
"""

import math
import os
import textwrap
from Modulo1 import admitir_nuevos, cargar_procesos
from Modulo2 import crear_memoria
from Modulo3 import ejecutar_tick_cpu, srtf_seleccionar_proceso
from Modulo4 import verificar_terminado
from Modulo5 import admision_suspendidos_y_nuevos_best_fit, contar_procesos_activos
from Modulo6 import mostrar_informe_final
from constantes import (
    CAMPOS_ARCHIVO,
    CARPETA_PROCESOS,
    ESTADO_EJECUCION,
    ESTADO_LISTO,
    ESTADO_PENDIENTE,
    EXTENSIONES_VALIDAS,
    MAX_LINEAS_ARCHIVO,
    MAX_PROCESOS,
    TAM_MEMORIA_USUARIO,
)


# ==========================================================================
# Menú principal y selección de archivo
# ==========================================================================


def limpiar_pantalla():
    """Borra la consola ("cls" en Windows, "clear" en otros sistemas)."""
    os.system("cls" if os.name == "nt" else "clear")


def esperar_enter(mensaje="\nEnter para continuar "):
    """Pausa el programa hasta que el usuario presiona Enter."""
    input(mensaje)


def hay_archivos_validos():
    """Dice si hay al menos un archivo de procesos utilizable en la carpeta."""
    return bool(buscar_archivos_validos())


def buscar_archivos_validos():
    """Busca los archivos de procesos que hay en la carpeta del programa.

    Toma los archivos que coinciden con EXTENSIONES_VALIDAS (*.txt y *.csv) dentro
    de CARPETA_PROCESOS, y descarta los que están vacíos."""

    archivos = []
    for patron in EXTENSIONES_VALIDAS:
        for archivo in CARPETA_PROCESOS.glob(patron):
            if archivo.is_file() and archivo.stat().st_size > 0:
                archivos.append(archivo.name)
    return sorted(archivos)


def mostrar_archivos_disponibles(archivos, archivo_elegido):
    """Muestra la lista de archivos disponibles en la carpeta del programa."""

    print("Archivos disponibles (carpeta del programa)\n")
    for i, nombre in enumerate(archivos, start=1):
        print(f"[{i}] {nombre} {'(seleccionado)' if archivo_elegido == nombre else ''}")
    print("\n[0] Volver al menu")


def elegir_archivo(archivo_elegido):
    """Permite al usuario elegir un archivo de procesos, tambien permite ver su contenido.
    Para confirmar la elección, el usuario debe presionar 's' o Enter. Devuelve el nombre del archivo elegido, o None si se cancela.
    """
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
    """Muestra el menú principal y permite al usuario elegir un archivo y ejecutar el simulador."""
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


# ==========================================================================
# Simulador (bucle principal)
# ==========================================================================


def crear_sistema(procesos):
    """Crea y devuelve la estructura del sistema con los procesos inicializados."""
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


def hay_procesos_validos(sistema):
    """Dice si hay al menos un proceso válido en el sistema."""
    return bool(sistema["procesos"])


def hay_procesos_por_atender(sistema):
    """Dice si hay procesos que aún no han terminado."""
    return len(sistema["terminados"]) != len(sistema["procesos"])


def proceso_llego(sistema):
    """Dice si hay procesos que han llegado al tiempo actual del reloj."""
    return bool(sistema["pendientes"]) and sistema["pendientes"][0]["TA"] <= sistema["reloj"]


def registrar_llegada(sistema):
    """Mueve los procesos que han llegado del estado pendiente al estado nuevo."""
    admitir_nuevos(sistema["pendientes"], sistema["nuevos"], sistema["reloj"])


def admitir_procesos(sistema):
    """Admite procesos al sistema. Intenta paras los procesos suspendido y nuevos a la memoria 
    con la politica Best-Fit"""
    return admision_suspendidos_y_nuevos_best_fit(
        sistema["suspendidos"],
        sistema["nuevos"],
        sistema["listos"],
        sistema["memoria"],
        sistema["en_cpu"],
    )


def planificar_cpu(sistema):
    """Selecciona el proceso a ejecutar en la CPU según la política SRTF."""
    nuevo, desplazado = srtf_seleccionar_proceso(sistema["en_cpu"], sistema["listos"])
    if nuevo is not None:
        nuevo["estado"] = ESTADO_EJECUCION
    if desplazado is not None:
        desplazado["estado"] = ESTADO_LISTO
    sistema["en_cpu"] = nuevo


def ejecutar_simulador(archivo_elegido):
    """Ejecuta el simulador con el archivo de procesos elegido."""
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
# Pantallas del simulador
# ==========================================================================


def mostrar_formato_archivo():
    """Muestra en pantalla el formato esperado del archivo de procesos y las reglas de validación."""
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
    - Un proceso por línea, {CAMPOS_ARCHIVO} campos separados por comas, en el orden ID, TA, TI, TAM. El ID puede llevar la P (P1) o no (1). Se ignoran 
    las líneas vacías y las que empiezan con #.
    - Valores válidos: enteros no negativos. TI y TAM deben ser mayores a 0. TAM máximo: {TAM_MEMORIA_USUARIO}K.
    - Sin IDs repetidos, máximo {MAX_PROCESOS} procesos.
    - Se leen como máximo {MAX_LINEAS_ARCHIVO} líneas."""))

    esperar_enter()


def mostrar_lineas_archivo(lineas_analizadas):
    """Muestra en pantalla el análisis de las líneas del archivo de procesos."""
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


def mostrar_procesos_validos(sistema):
    """Muestra en pantalla la tabla de procesos válidos que se van a simular."""
    ancho_id = 4
    ancho_tiempo = 7
    ancho_tamanio = 7

    barra_id = "─" * ancho_id
    barra_tiempo = "─" * ancho_tiempo
    barra_tamanio = "─" * ancho_tamanio

    print(f"┌─{barra_id}─┬─{barra_tiempo}─┬─{barra_tiempo}─┬─{barra_tamanio}─┐")
    print(f"│ {"ID":^{ancho_id}} │ {"TA":^{ancho_tiempo}} │ {"TI":^{ancho_tiempo}} │ {"TAM(KB)":^{ancho_tamanio}} │")
    print(f"├─{barra_id}─┼─{barra_tiempo}─┼─{barra_tiempo}─┼─{barra_tamanio}─┤")

    for p in sistema["procesos"]:
        print(f"│ {nombre_proceso(p):<{ancho_id}} ", end="")
        print(f"│ {p["TA"]:>{ancho_tiempo}} ", end="")
        print(f"│ {p["TI"]:>{ancho_tiempo}} ", end="")
        print(f"│ {p["TAM"]:>{ancho_tamanio}} │")

    print(f"└─{barra_id}─┴─{barra_tiempo}─┴─{barra_tiempo}─┴─{barra_tamanio}─┘")


def nombre_proceso(p):
    """Devuelve el nombre del proceso para mostrar en pantalla."""
    return f"P{p['id']}"


def nombre_particion(particion):
    """Devuelve el nombre de la partición para mostrar en pantalla."""
    if particion["libre"]:
        return ""
    if particion["id_proc"] == "SO":
        return "SO"
    return f"P{particion['id_proc']}"


def particion_proceso(sistema, p):
    """Devuelve el número de la partición en la que se encuentra el proceso."""
    for i, particion in enumerate(sistema["memoria"], start=1):
        if not particion["libre"] and particion["id_proc"] == p["id"]:
            return i


def estado_proceso(sistema, p):
    """Devuelve el estado del proceso para mostrar en pantalla."""
    # Los pendientes se muestran con el estado en blanco, como en la versión original.
    return "" if p["estado"] == ESTADO_PENDIENTE else p["estado"]


def mostrar_colas_resumen(cola):
    """Muestra en pantalla un resumen de los procesos en la cola, con su tiempo restante."""
    if not bool(cola):
        print("")
    else:
        for p in cola:
            print(f"{nombre_proceso(p)}({p["tiempo_rest"]}) ", end="")
        print()


def mostrar_estado_cpu(sistema, evento):
    """Muestra en pantalla el estado de la CPU y las colas de procesos, según el evento que ocurrió."""
    print("===========================================================================================================")
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
    """Devuelve True si la partición anterior a la i-ésima está libre, False en caso contrario."""
    return i != 0 and memoria[i - 1]["libre"]


def dibujar_barra_particiones(sistema):
    """Dibuja en pantalla la barra de particiones de memoria, con el nombre del proceso y el tamaño de cada partición."""
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
    """Muestra en pantalla la tabla de particiones de memoria, con el nombre del proceso y el tamaño de cada partición."""
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
    """Cuenta cuántos procesos pendientes hay en el sistema."""
    return sum(estado_proceso(sistema, p) == "" for p in sistema["procesos"])


def mostrar_colas(sistema):
    """Muestra en pantalla la tabla de procesos con su estado, tiempo de arribo, tiempo de irrupción, tamaño, tiempo restante y tiempo de finalización."""
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
    """Muestra en pantalla el estado del sistema tras un evento (llegada o finalización de proceso) y espera a que el usuario presione Enter."""
    #limpiar_pantalla()

    mostrar_estado_cpu(sistema, evento)
    dibujar_barra_particiones(sistema)
    mostrar_tabla_particiones(sistema)
    mostrar_colas(sistema)

    se_mostro.add(sistema["reloj"])

    esperar_enter()
