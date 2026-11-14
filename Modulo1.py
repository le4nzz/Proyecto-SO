# Módulo 1: Validación, carga y orden de procesos.

"""
Formato esperado del archivo (.txt o .csv), separado por comas:
    #id, TA, TI, TAM
    1, 0, 5, 150
    2, 0, 6, 15

- Las líneas vacías y las que empiezan con '#' se ignoran.
- Cada proceso válido se guarda como diccionario:
    {"id": int, "TA": int, "TI": int, "TAM": int}
"""

# CAMBIOS sobre el módulo original (integración al simulador):
#  - Las constantes (EXTENSIONES_VALIDAS, MAX_PROCESOS, TAM_MAX_USUARIO) pasaron
#    a constantes.py para compartirlas con el resto. TAM_MAX_USUARIO ahora es
#    TAM_MEMORIA_USUARIO (mismo valor, 450K).
#  - validar_linea: mensajes más cortos (entran en la tabla de análisis), se
#    agrega el máximo de 3 dígitos por campo y el control de id negativo.
#  - leer_archivo: abre con utf-8-sig (tildes y BOM de Windows), respeta
#    MAX_LINEAS_ARCHIVO y devuelve una fila por línea para la tabla de análisis,
#    además de los procesos. El id puede escribirse con o sin P (P1 o 1).
#  - Cada proceso se crea ya con tiempo_rest, tiempo_fin y estado.
#  - admitir_nuevos mueve el mismo diccionario (no crea una copia) para que la
#    tabla de procesos vea los cambios de estado.
#  - Se quitó el bloque de prueba aislada del final.

import os

from constantes import (
    CAMPOS_ARCHIVO,
    ESTADO_NUEVO,
    ESTADO_PENDIENTE,
    EXTENSIONES_VALIDAS,
    MAX_LINEAS_ARCHIVO,
    MAX_PROCESOS,
    TAM_MEMORIA_USUARIO,
)

"""Chequea extensión y existencia."
   Devuelve (bool, mensaje). """
def validar_extension(ruta):
    extensiones = tuple(e[1:] for e in EXTENSIONES_VALIDAS)
    if not str(ruta).lower().endswith(extensiones):
        return False, "El archivo debe tener extensión .txt o .csv"
    if not os.path.isfile(ruta):
        return False, f"El archivo '{ruta}' no existe"
    return True, ""


"""Dice si un campo es un número entero (permite el signo menos)."""
def es_entero(campo):
    digitos = campo[1:] if campo.startswith("-") else campo
    return digitos.isdecimal()


"""Valida los campos de una línea ya separada.
    
    Devuelve (bool, mensaje_error). """
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

"""
    Lee el archivo y devuelve (procesos_validos, lineas, se_excedio).
    (lineas) es una lista con una fila por línea leída: número de línea,
    contenido y motivo ("Correcto" o la causa del rechazo).
    (se_excedio) es True si el archivo tenía más de MAX_LINEAS_ARCHIVO líneas.
    """
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
                    "TA": ta,
                    "TI": ti,
                    "TAM": tam,
                    "tiempo_rest": ti,
                    "tiempo_fin": None,
                    "estado": ESTADO_PENDIENTE,
                }
            )
            lineas.append({"linea": numero, "contenido": linea, "motivo": "Correcto"})

    return procesos, lineas, se_excedio

"""Ordena por TA (menor a mayor)."""
def obtener_ta(proc):
    return proc["TA"]

def ordenar_procesos(procesos):
    return sorted(procesos, key=obtener_ta)


def cargar_procesos(ruta):
    """
    Función principal del módulo.
    Devuelve (procesos, lineas, se_excedio, error):
      - (procesos) es una lista ordenada por TA, con máximo MAX_PROCESOS elementos
      - (lineas) es el análisis línea por línea del archivo
      - (se_excedio) indica si había más líneas que MAX_LINEAS_ARCHIVO
      - (error) es un mensaje si el archivo no es válido o no se pudo leer, o "" si todo bien
    Si el archivo no es válido, devuelve ([], [], False, mensaje).
    """
    es_valida, mensaje = validar_extension(ruta)
    if not es_valida:
        return [], [], False, mensaje

    try:
        procesos, lineas, se_excedio = leer_archivo(ruta)
    except (OSError, UnicodeDecodeError):
        return [], [], False, "No se pudo leer el archivo (permisos o codificación)"

    procesos = ordenar_procesos(procesos)

    return procesos, lineas, se_excedio, ""


def admitir_nuevos(procesos, cola_nuevos, clock):
    """
    Pasa de la lista 'procesos' a 'cola_nuevos' todo proceso con TA <= clock.
    Cambia su estado a Nuevo. El proceso ya trae 'tiempo_rest' (= TI), para no modificar TI original.
    Devuelve la lista de procesos admitidos en ese clock.
    """
    admitidos = []
    while procesos and procesos[0]["TA"] <= clock:
        proc = procesos.pop(0)
        proc["estado"] = ESTADO_NUEVO
        cola_nuevos.append(proc)
        admitidos.append(proc)
    return admitidos
