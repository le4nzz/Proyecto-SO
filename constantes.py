"""Constantes y estados del simulador (compartidos por todos los módulos)."""

import pathlib
import sys


CARPETA_PROCESOS = pathlib.Path(sys.executable).parent if getattr(sys, "frozen", False) else pathlib.Path(__file__).parent
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