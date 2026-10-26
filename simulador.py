#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Asignación de Memoria y Planificación de Procesos
UTN FRRe - Sistemas Operativos

  * Memoria: 100K Sistema Operativo + 450K usuario, particiones variables (MVT), Best-Fit.
  * CPU: un solo procesador, SRTF (Shortest Remaining Time First, preemptivo).
  * Estados: Nuevo, Listo, Listo y Suspendido, Ejecución, Terminado.
  * Límite: Ejecución + Listos + Listos/Suspendidos <= 5 procesos admitidos.
  * Avance manual: una unidad de tiempo por cada Enter (no hay corrida automática).

Uso:
    python3 simulador.py procesos_ejemplo.csv
    python3 simulador.py                      (pide la ruta del archivo)

Formato del archivo (CSV, una línea por proceso, máximo 10):
    id,tamano,tiempo_arribo,tiempo_irrupcion
    P1,120,0,8

  id                identificador único (texto sin espacios)
  tamano            tamaño en K (entero > 0, máximo 450)
  tiempo_arribo     instante de llegada (entero >= 0)
  tiempo_irrupcion  tiempo total de CPU (entero > 0)

Correspondencia con el diagrama de flujo (ver Simulador.paso):
  Inicialización ............ Simulador.__init__
  ¿TA <= clock? / admisión .. Simulador._admitir_nuevos
  Asignar CPU al menor TI ... Simulador._planificar
  TiempoRestante - 1 ........ Simulador.paso
  clock := clock + 1 ........ Simulador.paso
  TR = 0 -> terminar ........ Simulador._finalizar
  ¿Suspendidos y Nuevos? .... Simulador._reintentar_suspendidos + _admitir_nuevos
  Informe estadístico ....... Simulador.estadisticas / mostrar_informe
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Constantes del enunciado
# --------------------------------------------------------------------------
MEMORIA_SO = 100            # K reservados al Sistema Operativo
MEMORIA_USUARIO = 450       # K para trabajos de usuario
MAX_PROCESOS_ENTRADA = 10
LIMITE_ADMITIDOS = 5        # Ejecución + Listos + Listos/Suspendidos

NUEVO = "Nuevo"
LISTO = "Listo"
SUSPENDIDO = "Listo y Suspendido"
EJECUCION = "Ejecución"
TERMINADO = "Terminado"


# --------------------------------------------------------------------------
# Estructuras de datos
# --------------------------------------------------------------------------
@dataclass
class Proceso:
    """PCB del proceso."""
    id: str
    tamano: int
    tiempo_arribo: int
    tiempo_irrupcion: int
    orden: int = 0                        # orden original en el archivo (desempates)
    tiempo_restante: int = field(init=False)
    estado: str = NUEVO
    tiempo_finalizacion: Optional[int] = None
    tiempo_retorno: Optional[int] = None
    tiempo_espera: Optional[int] = None
    particion_asignada: Optional[int] = None   # dirección de inicio de su partición
    llegada_notificada: bool = False

    def __post_init__(self) -> None:
        self.tiempo_restante = self.tiempo_irrupcion


@dataclass
class Bloque:
    """Partición de memoria (ocupada, libre o reservada al S.O.)."""
    id: int
    inicio: int
    tamano: int
    proceso_id: Optional[str] = None
    solicitado: int = 0                   # tamaño pedido por el proceso (para fragmentación)
    es_so: bool = False

    @property
    def libre(self) -> bool:
        return self.proceso_id is None and not self.es_so

    @property
    def fragmentacion_interna(self) -> int:
        return 0 if self.libre or self.es_so else self.tamano - self.solicitado


# --------------------------------------------------------------------------
# Gestor de memoria: MVT + Best-Fit
# --------------------------------------------------------------------------
class GestorMemoria:
    def __init__(self) -> None:
        self.bloques: List[Bloque] = [
            Bloque(0, 0, MEMORIA_SO, es_so=True),
            Bloque(1, MEMORIA_SO, MEMORIA_USUARIO),
        ]

    def _renumerar(self) -> None:
        for i, b in enumerate(self.bloques):
            b.id = i

    def asignar_best_fit(self, proceso: Proceso) -> Optional[Bloque]:
        """Reserva memoria en el bloque libre más pequeño que alcance
        (desempate: dirección más baja). Devuelve None si no hay lugar."""
        candidatos = [b for b in self.bloques if b.libre and b.tamano >= proceso.tamano]
        if not candidatos:
            return None
        elegido = min(candidatos, key=lambda b: (b.tamano, b.inicio))
        resto = elegido.tamano - proceso.tamano
        if resto > 0:   # el sobrante queda como bloque libre independiente
            idx = self.bloques.index(elegido)
            self.bloques.insert(idx + 1, Bloque(0, elegido.inicio + proceso.tamano, resto))
            elegido.tamano = proceso.tamano
        elegido.proceso_id = proceso.id
        elegido.solicitado = proceso.tamano
        proceso.particion_asignada = elegido.inicio
        self._renumerar()
        return elegido

    def liberar(self, proceso: Proceso) -> Tuple[int, int, int, bool]:
        """Libera la partición del proceso y fusiona libres contiguos.
        Devuelve (inicio, tamaño liberado, tamaño del libre resultante, hubo fusión)."""
        bloque = next(b for b in self.bloques if b.proceso_id == proceso.id)
        inicio, liberado = bloque.inicio, bloque.tamano
        bloque.proceso_id = None
        bloque.solicitado = 0
        proceso.particion_asignada = None
        fusion = False
        i = 0
        while i < len(self.bloques) - 1:
            a, b = self.bloques[i], self.bloques[i + 1]
            if a.libre and b.libre:
                a.tamano += b.tamano
                self.bloques.pop(i + 1)
                fusion = True
            else:
                i += 1
        self._renumerar()
        resultante = next(b for b in self.bloques if b.libre and b.inicio <= inicio < b.inicio + b.tamano)
        return inicio, liberado, resultante.tamano, fusion

    def total_libre(self) -> int:
        return sum(b.tamano for b in self.bloques if b.libre)

    def mayor_libre(self) -> int:
        return max((b.tamano for b in self.bloques if b.libre), default=0)

    def verificar(self) -> List[str]:
        """Chequeo de coherencia (continuidad, sin solapamientos, tamaño total)."""
        problemas = []
        esperado = 0
        for b in self.bloques:
            if b.inicio != esperado:
                problemas.append(f"Bloque {b.id}: inicio {b.inicio}, se esperaba {esperado}")
            if b.tamano <= 0:
                problemas.append(f"Bloque {b.id}: tamaño inválido {b.tamano}")
            esperado = b.inicio + b.tamano
        if esperado != MEMORIA_SO + MEMORIA_USUARIO:
            problemas.append(f"La memoria suma {esperado}K y debería sumar {MEMORIA_SO + MEMORIA_USUARIO}K")
        for a, b in zip(self.bloques, self.bloques[1:]):
            if a.libre and b.libre:
                problemas.append(f"Bloques libres contiguos sin fusionar: {a.id} y {b.id}")
        return problemas


# --------------------------------------------------------------------------
# Simulador
# --------------------------------------------------------------------------
class Simulador:
    def __init__(self, procesos: List[Proceso]) -> None:
        self.reloj = 0                                              # clock := 0
        self.memoria = GestorMemoria()                              # cargar el SO en memoria
        self.procesos = list(procesos)                              # cargar archivo con procesos
        for i, p in enumerate(self.procesos):
            p.orden = i
        # Ordenar y generar cola de Nuevos (arribo, y orden del archivo como desempate)
        self.cola_nuevos: List[Proceso] = sorted(self.procesos, key=lambda p: (p.tiempo_arribo, p.orden))
        self.cola_listos: List[Proceso] = []
        self.cola_suspendidos: List[Proceso] = []
        self.actual: Optional[Proceso] = None
        self.terminados: List[Proceso] = []
        self.cambios_cpu = 0
        self.eventos: List[str] = []
        self.ultima_unidad: Optional[Tuple[int, int, Optional[str]]] = None

    # ----- utilidades -----------------------------------------------------
    def _log(self, mensaje: str) -> None:
        self.eventos.append(f"[t={self.reloj}] {mensaje}")

    def cantidad_admitidos(self) -> int:
        """Ejecución + Listos + Listo y Suspendido (los Nuevos no cuentan)."""
        return len(self.cola_listos) + len(self.cola_suspendidos) + (1 if self.actual else 0)

    def terminado(self) -> bool:
        """¿Quedan procesos en el sistema por atender?  (NO -> informe)"""
        return len(self.terminados) == len(self.procesos)

    # ----- admisión (¿TA <= clock? / ¿cola < 5? / ¿hay espacio?) -----------
    def _notificar_llegadas(self) -> None:
        for p in self.cola_nuevos:
            if p.tiempo_arribo > self.reloj:
                break
            if not p.llegada_notificada:
                p.llegada_notificada = True
                self._log(f"LLEGADA de {p.id} (tamaño {p.tamano}K, irrupción {p.tiempo_irrupcion})")

    def _intentar_admitir(self, p: Proceso) -> None:
        """Admisión de un proceso Nuevo: Best-Fit -> Listo, o sin espacio -> Listo y Suspendido."""
        bloque = self.memoria.asignar_best_fit(p)
        if bloque is not None:
            p.estado = LISTO
            self.cola_listos.append(p)
            self._log(f"{p.id} ADMITIDO: Best-Fit en partición #{bloque.id} "
                      f"(inicio {bloque.inicio}K, {bloque.tamano}K) -> Listo")
        else:
            p.estado = SUSPENDIDO
            self.cola_suspendidos.append(p)
            self._log(f"{p.id} ADMITIDO sin memoria suficiente (necesita {p.tamano}K, "
                      f"mayor bloque libre {self.memoria.mayor_libre()}K) -> Listo y Suspendido")

    def _admitir_nuevos(self) -> None:
        self._notificar_llegadas()
        while self.cola_nuevos and self.cola_nuevos[0].tiempo_arribo <= self.reloj:
            if self.cantidad_admitidos() >= LIMITE_ADMITIDOS:
                # Capacidad llena: el proceso espera en Nuevos; el reloj NO se detiene.
                return
            p = self.cola_nuevos.pop(0)
            self._intentar_admitir(p)

    def _reintentar_suspendidos(self) -> None:
        """Tras liberar memoria: Listo y Suspendido -> Listo si ahora entran."""
        for p in list(self.cola_suspendidos):
            bloque = self.memoria.asignar_best_fit(p)
            if bloque is not None:
                self.cola_suspendidos.remove(p)
                p.estado = LISTO
                self.cola_listos.append(p)
                self._log(f"{p.id} REINCORPORADO: Best-Fit en partición #{bloque.id} "
                          f"(inicio {bloque.inicio}K, {bloque.tamano}K) -> Listo")

    # ----- planificación SRTF ----------------------------------------------
    def _planificar(self) -> None:
        """Asignar a la CPU el proceso con menor tiempo restante y comparar con el anterior."""
        candidatos = list(self.cola_listos) + ([self.actual] if self.actual else [])
        if not candidatos:
            return                                   # CPU sin proceso ejecutable
        elegido = min(candidatos, key=lambda p: (p.tiempo_restante,
                                                 0 if p is self.actual else 1,   # empate: conserva el actual
                                                 p.tiempo_arribo, p.orden))
        if elegido is self.actual:
            return                                   # ¿mismo que el anterior? SI: sin cambio de contexto
        # NO: actualizar PCB del proceso actual, asignar la CPU al nuevo
        if self.actual is not None:
            anterior = self.actual
            anterior.estado = LISTO
            self.cola_listos.append(anterior)
            self._log(f"PREEMPCIÓN: {anterior.id} (restante {anterior.tiempo_restante}) vuelve a Listos")
        self.cola_listos.remove(elegido)
        elegido.estado = EJECUCION
        self.actual = elegido
        self.cambios_cpu += 1
        self._log(f"CPU asignada a {elegido.id} (restante {elegido.tiempo_restante})")

    def _preparar_instante(self) -> None:
        """Admisión de llegadas + decisión del planificador para el instante actual."""
        self._admitir_nuevos()
        if not self.cola_listos and self.actual is None and self.cola_suspendidos:
            self._reintentar_suspendidos()           # resguardo: evita quedar colgado
        self._planificar()

    # ----- finalización -----------------------------------------------------
    def _finalizar(self, p: Proceso) -> None:
        p.tiempo_finalizacion = self.reloj
        p.tiempo_retorno = p.tiempo_finalizacion - p.tiempo_arribo
        p.tiempo_espera = p.tiempo_retorno - p.tiempo_irrupcion
        p.estado = TERMINADO
        self.actual = None                           # desencolar y retirar de la CPU
        self.terminados.append(p)
        self._log(f"FINALIZACIÓN de {p.id} -> Terminado (retorno {p.tiempo_retorno}, espera {p.tiempo_espera})")
        inicio, liberado, resultante, fusion = self.memoria.liberar(p)
        msg = f"MEMORIA liberada: {liberado}K desde {inicio}K"
        if fusion:
            msg += f" (bloques libres contiguos fusionados -> libre de {resultante}K)"
        self._log(msg)
        # ¿Hay procesos en Suspendidos y Nuevos?
        self._reintentar_suspendidos()
        self._admitir_nuevos()

    # ----- un paso = como máximo una unidad de tiempo ------------------------
    def paso(self) -> List[str]:
        if self.terminado():
            return []
        self.eventos = []
        self._preparar_instante()
        t0 = self.reloj
        p = self.actual
        if p is None:
            # ¿hay procesos en la cola de Listos? NO -> clock := clock + 1 (CPU inactiva)
            self.ultima_unidad = (t0, t0 + 1, None)
            self.reloj += 1
            self._log("CPU INACTIVA durante la unidad anterior: no hay procesos ejecutables")
        else:
            p.tiempo_restante -= 1                   # TiempoRestante := TiempoRestante - 1
            self.reloj += 1                          # clock := clock + 1
            self.ultima_unidad = (t0, self.reloj, p.id)
            if p.tiempo_restante == 0:               # ¿hay procesos que atender y TR = 0?
                self._finalizar(p)
        self._preparar_instante()                    # llegadas y decisión del instante nuevo
        return self.eventos

    # ----- estadísticas ------------------------------------------------------
    def estadisticas(self) -> Dict[str, float]:
        n = len(self.terminados)
        total = self.reloj
        return {
            "n": n,
            "tiempo_total": total,
            "retorno_prom": sum(p.tiempo_retorno for p in self.terminados) / n if n else 0.0,
            "espera_prom": sum(p.tiempo_espera for p in self.terminados) / n if n else 0.0,
            "rendimiento": n / total if total > 0 else 0.0,
        }

    def invariantes(self) -> List[str]:
        """Chequeo de coherencia entre colas, estados, memoria y límite de 5."""
        problemas = self.memoria.verificar()
        vistos: Dict[str, str] = {}
        grupos = [("Nuevos", self.cola_nuevos), ("Listos", self.cola_listos),
                  ("Suspendidos", self.cola_suspendidos), ("Terminados", self.terminados),
                  ("CPU", [self.actual] if self.actual else [])]
        for nombre, cola in grupos:
            for p in cola:
                if p.id in vistos:
                    problemas.append(f"{p.id} duplicado en {vistos[p.id]} y {nombre}")
                vistos[p.id] = nombre
        esperado = {"Nuevos": NUEVO, "Listos": LISTO, "Suspendidos": SUSPENDIDO,
                    "Terminados": TERMINADO, "CPU": EJECUCION}
        for nombre, cola in grupos:
            for p in cola:
                if p.estado != esperado[nombre]:
                    problemas.append(f"{p.id} está en {nombre} con estado {p.estado}")
        if len(vistos) != len(self.procesos):
            problemas.append("Hay procesos que no están en ninguna cola")
        if self.cantidad_admitidos() > LIMITE_ADMITIDOS:
            problemas.append(f"Más de {LIMITE_ADMITIDOS} procesos admitidos")
        con_memoria = {b.proceso_id for b in self.memoria.bloques if b.proceso_id}
        activos = {p.id for p in self.cola_listos} | ({self.actual.id} if self.actual else set())
        if con_memoria != activos:
            problemas.append(f"Procesos con memoria {sorted(con_memoria)} != Listos/Ejecución {sorted(activos)}")
        return problemas


# --------------------------------------------------------------------------
# Carga y validación del archivo
# --------------------------------------------------------------------------
_ENTERO = re.compile(r"[+-]?\d+")


def cargar_procesos(ruta: str) -> Tuple[List[Proceso], List[str]]:
    """Lee el archivo. Devuelve (procesos, errores). Si hay errores no se debe simular."""
    errores: List[str] = []
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            lineas = f.read().splitlines()
    except FileNotFoundError:
        return [], [f"No se encontró el archivo '{ruta}'."]
    except UnicodeDecodeError:
        return [], [f"El archivo '{ruta}' no es texto UTF-8 válido."]
    except OSError as e:
        return [], [f"No se pudo leer '{ruta}': {e.strerror or e}"]

    procesos: List[Proceso] = []
    ids = set()
    primera = True
    for nro, linea in enumerate(lineas, start=1):
        texto = linea.strip()
        if not texto or texto.startswith("#"):
            continue
        campos = [c for c in re.split(r"[,;\s]+", texto) if c != ""]
        if primera:
            primera = False
            if campos and campos[0].lower() in ("id", "proceso", "pid") and \
                    not all(_ENTERO.fullmatch(c) for c in campos[1:4]):
                continue                              # encabezado
        if len(campos) != 4:
            errores.append(f"Línea {nro}: se esperaban 4 campos (id,tamano,tiempo_arribo,tiempo_irrupcion) "
                           f"y hay {len(campos)}: '{texto}'")
            continue
        pid, s_tam, s_arr, s_irr = campos
        valores = {}
        for nombre, valor in (("tamano", s_tam), ("tiempo_arribo", s_arr), ("tiempo_irrupcion", s_irr)):
            if not _ENTERO.fullmatch(valor):
                errores.append(f"Línea {nro}: '{nombre}' debe ser un entero y se recibió '{valor}'.")
            else:
                valores[nombre] = int(valor)
        if len(valores) < 3:
            continue
        if pid in ids:
            errores.append(f"Línea {nro}: el identificador '{pid}' está repetido.")
        ids.add(pid)
        if valores["tamano"] <= 0:
            errores.append(f"Línea {nro} ({pid}): el tamaño debe ser mayor que 0.")
        elif valores["tamano"] > MEMORIA_USUARIO:
            errores.append(f"Línea {nro} ({pid}): tamaño {valores['tamano']}K supera los "
                           f"{MEMORIA_USUARIO}K de memoria de usuario; no podría alojarse nunca.")
        if valores["tiempo_arribo"] < 0:
            errores.append(f"Línea {nro} ({pid}): el tiempo de arribo no puede ser negativo.")
        if valores["tiempo_irrupcion"] <= 0:
            errores.append(f"Línea {nro} ({pid}): el tiempo de irrupción debe ser mayor que 0.")
        procesos.append(Proceso(pid, valores["tamano"], valores["tiempo_arribo"],
                                valores["tiempo_irrupcion"], orden=len(procesos)))
    if not procesos and not errores:
        errores.append("El archivo no contiene procesos.")
    if len(procesos) > MAX_PROCESOS_ENTRADA:
        errores.append(f"El archivo tiene {len(procesos)} procesos y el máximo permitido es {MAX_PROCESOS_ENTRADA}.")
    return procesos, errores


# --------------------------------------------------------------------------
# Presentación por consola
# --------------------------------------------------------------------------
ANCHO = 84


def _linea(c: str = "=") -> None:
    print(c * ANCHO)


def _fmt_listo(p: Proceso) -> str:
    return f"{p.id}(rest={p.tiempo_restante}, {p.tamano}K)"


def _fmt_nuevo(p: Proceso) -> str:
    return f"{p.id}(arribo={p.tiempo_arribo}, irr={p.tiempo_irrupcion}, {p.tamano}K)"


def _fmt_cola(items: List[str]) -> str:
    return ", ".join(items) if items else "(vacía)"


def mostrar_cpu(sim: Simulador) -> None:
    print("PROCESADOR")
    if sim.ultima_unidad:
        t0, t1, pid = sim.ultima_unidad
        print(f"  Última unidad [{t0},{t1}): " + (f"ejecutó {pid}" if pid else "CPU inactiva"))
    if sim.actual:
        p = sim.actual
        print(f"  Ahora en Ejecución: {p.id}  (restante {p.tiempo_restante} de {p.tiempo_irrupcion}, {p.tamano}K)")
    else:
        print("  Ahora en Ejecución: CPU INACTIVA")


def mostrar_memoria(sim: Simulador) -> None:
    print("TABLA DE PARTICIONES DE MEMORIA")
    print(f"  {'ID':>3} {'Inicio':>7} {'Tamaño':>8}  {'Proceso':<10} {'Frag. interna':>13}  Estado")
    for b in sim.memoria.bloques:
        if b.es_so:
            proc, frag, est = "S.O.", "-", "Reservada"
        elif b.libre:
            proc, frag, est = "(libre)", "-", "Libre"
        else:
            proc, frag, est = b.proceso_id, f"{b.fragmentacion_interna}K", "Ocupada"
        print(f"  {b.id:>3} {str(b.inicio) + 'K':>7} {str(b.tamano) + 'K':>8}  {proc:<10} {frag:>13}  {est}")
    print(f"  Libre total: {sim.memoria.total_libre()}K | mayor bloque libre: {sim.memoria.mayor_libre()}K")


def mostrar_colas(sim: Simulador) -> None:
    print("COLAS")
    print(f"  Listos             : {_fmt_cola([_fmt_listo(p) for p in sim.cola_listos])}")
    print(f"  Listos/Suspendidos : {_fmt_cola([_fmt_listo(p) for p in sim.cola_suspendidos])}")
    print(f"  Nuevos             : {_fmt_cola([_fmt_nuevo(p) for p in sim.cola_nuevos])}")
    print(f"  Terminados         : {_fmt_cola([f'{p.id}(fin={p.tiempo_finalizacion})' for p in sim.terminados])}")
    print(f"  Admitidos (Ejec+Listos+Susp): {sim.cantidad_admitidos()}/{LIMITE_ADMITIDOS}")


def mostrar_estado(sim: Simulador, titulo: str, eventos: Optional[List[str]] = None) -> None:
    _linea()
    print(f"{titulo}   |   RELOJ = {sim.reloj}")
    _linea()
    if eventos is not None:
        print("EVENTOS")
        for e in eventos or ["(sin eventos)"]:
            print(f"  {e}")
    mostrar_cpu(sim)
    mostrar_memoria(sim)
    mostrar_colas(sim)
    _linea("-")


def mostrar_informe(sim: Simulador) -> None:
    est = sim.estadisticas()
    print()
    _linea()
    print("INFORME ESTADÍSTICO FINAL")
    _linea()
    print(f"  {'Proceso':<9}{'Arribo':>7}{'Irrup.':>8}{'Fin':>6}{'Retorno':>9}{'Espera':>8}")
    for p in sorted(sim.procesos, key=lambda p: p.orden):
        print(f"  {p.id:<9}{p.tiempo_arribo:>7}{p.tiempo_irrupcion:>8}{p.tiempo_finalizacion:>6}"
              f"{p.tiempo_retorno:>9}{p.tiempo_espera:>8}")
    print()
    print(f"  Tiempo promedio de retorno : {est['retorno_prom']:.2f}")
    print(f"  Tiempo promedio de espera  : {est['espera_prom']:.2f}")
    print(f"  Tiempo total de simulación : {est['tiempo_total']}")
    print(f"  Rendimiento                : {est['rendimiento']:.4f} trabajos/unidad de tiempo "
          f"({est['n']} terminados / {est['tiempo_total']})")
    print(f"  Cambios de proceso en CPU  : {sim.cambios_cpu}")
    print("  Retorno = finalización - arribo | Espera = retorno - irrupción")
    _linea()


# --------------------------------------------------------------------------
# Programa principal
# --------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Simulador de memoria (MVT/Best-Fit) y planificación SRTF")
    parser.add_argument("archivo", nargs="?", help="archivo CSV con los procesos")
    args = parser.parse_args(argv)

    ruta = args.archivo
    if not ruta:
        try:
            ruta = input("Ruta del archivo de procesos [procesos_ejemplo.csv]: ").strip() or "procesos_ejemplo.csv"
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

    procesos, errores = cargar_procesos(ruta)
    if errores:
        print(f"\nNo se puede iniciar la simulación. Errores en '{ruta}':")
        for e in errores:
            print(f"  - {e}")
        return 1

    sim = Simulador(procesos)
    print(f"\nSimulador cargado con {len(procesos)} procesos desde '{ruta}'.")
    mostrar_estado(sim, "ESTADO INICIAL")

    while not sim.terminado():
        try:
            resp = input("Enter = avanzar 1 unidad de tiempo | q = salir > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSimulación interrumpida.")
            return 0
        if resp in ("q", "salir"):
            print("Simulación interrumpida por el usuario.")
            return 0
        eventos = sim.paso()
        mostrar_estado(sim, "PASO DE SIMULACIÓN", eventos)

    mostrar_informe(sim)
    return 0


if __name__ == "__main__":
    sys.exit(main())
