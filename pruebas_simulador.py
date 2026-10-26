#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del simulador (python3 pruebas_simulador.py). Cada paso verifica además los invariantes."""
import os, tempfile, traceback
from simulador import (Simulador, Proceso, GestorMemoria, cargar_procesos,
                       LISTO, SUSPENDIDO, EJECUCION, TERMINADO, NUEVO)


def mk(lista):
    return Simulador([Proceso(i, t, a, r) for (i, t, a, r) in lista])


def paso(sim):
    sim.paso()
    prob = sim.invariantes()
    assert not prob, f"Invariantes rotos en t={sim.reloj}: {prob}"


def correr(sim, max_pasos=500):
    historia = []
    while not sim.terminado():
        assert len(historia) < max_pasos, "bucle infinito"
        paso(sim)
        historia.append((sim.reloj, sim.ultima_unidad[2]))
    return historia


def ids(cola):
    return [p.id for p in cola]


def t01():
    s = mk([("P1", 100, 0, 3), ("P2", 80, 0, 2), ("P3", 50, 0, 4)]); paso(s)
    assert ids(s.cola_nuevos) == [] and ids(s.cola_suspendidos) == []
    assert s.actual.id == "P2" and sorted(ids(s.cola_listos)) == ["P1", "P3"]
    return "P1,P2,P3 admitidos en t=0; P2 (menor TI) en CPU; Listos=[P1,P3]"

def t02():
    s = mk([("P1", 100, 3, 2), ("P2", 80, 5, 2)])
    paso(s); assert s.reloj == 1 and ids(s.cola_nuevos) == ["P1", "P2"]
    paso(s); paso(s)
    assert s.reloj == 3 and s.actual and s.actual.id == "P1" and ids(s.cola_nuevos) == ["P2"]
    return "Nuevos hasta t=3 (P1) y t=5 (P2); el reloj avanzó de a 1"

def t03():
    s = mk([("P1", 100, 0, 10), ("P2", 50, 3, 2)])
    for _ in range(3): paso(s)
    assert s.actual.id == "P2" and s.cola_listos[0].id == "P1" and s.cola_listos[0].tiempo_restante == 7
    assert s.cola_listos[0].estado == LISTO and s.actual.estado == EJECUCION
    return "En t=3 P2 desplaza a P1 (restante 7), que vuelve a Listos"

def t04():
    s = mk([("P1", 100, 0, 5), ("P2", 50, 1, 5), ("P3", 50, 2, 6)])
    h = correr(s)
    assert [x[1] for x in h[:5]] == ["P1"] * 5 and s.cambios_cpu == 3
    return "P1 corre 5 unidades seguidas (empate con P2 conserva P1); 3 cambios de CPU en total"

def t05():
    s = mk([(f"P{i}", 50, 0, 2) for i in range(1, 8)]); paso(s)
    assert s.cantidad_admitidos() == 5 and len(s.cola_nuevos) == 2
    h = correr(s); assert len(s.terminados) == 7
    return "Tras el 1er paso: 5 admitidos y 2 en Nuevos; terminan los 7 (sin bucle)"

def t06():
    s = mk([("P1", 400, 0, 3), ("P2", 100, 0, 2)]); paso(s)
    assert [p.id for p in s.cola_suspendidos] == ["P2"] and s.cola_suspendidos[0].estado == SUSPENDIDO
    return "P2 (100K) con 50K libres -> Listo y Suspendido, no Listo"

def t07():
    g = GestorMemoria(); P = {n: Proceso(n, t, 0, 1) for n, t in
        [("A", 100), ("B", 50), ("C", 150), ("D", 30), ("E", 70)]}
    for p in P.values(): g.asignar_best_fit(p)
    g.liberar(P["B"]); g.liberar(P["D"])   # huecos: 50K@200, 30K@400, 50K@500 (final)
    x = Proceso("X", 40, 0, 1); b = g.asignar_best_fit(x); assert b.inicio == 200, b   # empate 50/50 -> menor dir.
    y = Proceso("Y", 25, 0, 1); b = g.asignar_best_fit(y); assert b.inicio == 400 and b.tamano == 25, b
    assert not g.verificar()
    return "X(40K)->hueco de 50K (dirección menor); Y(25K)->hueco de 30K (el más chico)"

def t08():
    g = GestorMemoria(); P = [Proceso(n, 100, 0, 1) for n in "ABC"]
    for p in P: g.asignar_best_fit(p)
    g.liberar(P[0]); assert len([b for b in g.bloques if b.libre]) == 2
    g.liberar(P[2]); assert [b.tamano for b in g.bloques if b.libre] == [100, 250]
    g.liberar(P[1]); assert [(b.inicio, b.tamano) for b in g.bloques if b.libre] == [(100, 450)]
    assert not g.verificar()
    return "Liberar A, C, B -> un único bloque libre de 450K @100K; no fusiona los no contiguos"

def t09():
    s = mk([("P1", 200, 0, 2), ("P2", 150, 0, 3), ("P3", 250, 0, 6)]); paso(s)
    assert ids(s.cola_suspendidos) == ["P3"]
    paso(s)   # t=2: termina P1 -> libres 200 y 100 NO contiguos
    assert s.terminados[0].id == "P1" and ids(s.cola_suspendidos) == ["P3"]
    paso(s); paso(s); paso(s)   # t=5: termina P2 -> fusión total
    assert s.terminados[1].id == "P2" and s.cola_suspendidos == [] and s.actual.id == "P3"
    s2 = mk([("P1", 300, 0, 3), ("P2", 200, 0, 5), ("P3", 100, 0, 4), ("P4", 160, 0, 2)]); paso(s2)
    assert ids(s2.cola_suspendidos) == ["P2", "P4"]
    for _ in range(2): paso(s2)
    assert "P2" in ids(s2.cola_listos) + [s2.actual.id] and ids(s2.cola_suspendidos) == ["P4"]
    return "P3 sigue suspendido con libres no contiguos y pasa a Listo tras la fusión; P2 entra y P4 sigue suspendido"

def t10():
    s = mk([("P1", 100, 4, 2), ("P2", 80, 6, 3)])
    for _ in range(4):
        paso(s); assert s.ultima_unidad[2] is None
    assert s.reloj == 4 and all(p.tiempo_restante == p.tiempo_irrupcion for p in s.procesos)
    paso(s); assert s.ultima_unidad[2] == "P1"
    return "4 unidades inactivas (reloj 0->4), restantes intactos; luego P1 ejecuta"

def t11():
    s = mk([("P1", 100, 0, 2)]); paso(s); assert s.actual and not s.terminados
    paso(s); p = s.procesos[0]
    assert p.estado == TERMINADO and p.tiempo_finalizacion == 2 and s.actual is None
    assert s.memoria.total_libre() == 450 and p.particion_asignada is None
    return "P1 Terminado en t=2, CPU libre, 450K libres otra vez"

def t12():
    s = mk([("P1", 100, 0, 3), ("P2", 50, 1, 1), ("P3", 50, 2, 4)]); correr(s)
    e = {p.id: (p.tiempo_finalizacion, p.tiempo_retorno, p.tiempo_espera) for p in s.procesos}
    assert e == {"P1": (4, 4, 1), "P2": (2, 1, 0), "P3": (8, 6, 2)}, e
    st = s.estadisticas()
    assert abs(st["retorno_prom"] - 11 / 3) < 1e-9 and abs(st["espera_prom"] - 1.0) < 1e-9
    assert abs(st["rendimiento"] - 3 / 8) < 1e-9
    return "Manual: retornos 4,1,6 (prom 3.667); esperas 1,0,2 (prom 1.0); rendimiento 3/8"

def t13():
    d = tempfile.mkdtemp(); casos = {
        "campo ausente": "P1,100,0\n", "id repetido": "P1,100,0,2\nP1,50,1,2\n",
        "arribo negativo": "P1,100,-1,2\n", "irrupción 0": "P1,100,0,0\n",
        "no numérico": "P1,abc,0,2\n", "tamaño>450": "P1,451,0,2\n",
        "11 procesos": "".join(f"P{i},10,0,1\n" for i in range(11)), "vacío": "",
    }
    for nombre, txt in casos.items():
        ruta = os.path.join(d, "x.csv"); open(ruta, "w").write(txt)
        procs, errs = cargar_procesos(ruta); assert errs, nombre
    assert cargar_procesos(os.path.join(d, "noexiste.csv"))[1]
    ruta = os.path.join(d, "ok.csv"); open(ruta, "w").write("id,tamano,tiempo_arribo,tiempo_irrupcion\nP1,10,0,1\n")
    assert cargar_procesos(ruta)[1] == []
    return "9 archivos inválidos rechazados con mensaje; el válido con encabezado se acepta"

def t14():
    s = mk([("P1", 100, 0, 1), ("P2", 100, 5, 2)])
    paso(s); assert not s.terminado() and len(s.terminados) == 1   # Listos vacía, pero P2 sigue en Nuevos
    h = correr(s); assert s.reloj == 7 and s.terminado() and s.estadisticas()["rendimiento"] == 2 / 7
    return "No termina al vaciarse Listos en t=1; el informe sale en t=7 con rendimiento 2/7"


if __name__ == "__main__":
    ok = 0; pruebas = [v for k, v in sorted(globals().items()) if k.startswith("t") and k[1:].isdigit()]
    for f in pruebas:
        try:
            r = f(); print(f"[OK ] {f.__name__}: {r}"); ok += 1
        except Exception as e:
            print(f"[FALLA] {f.__name__}: {e!r}"); traceback.print_exc()
    print(f"\n{ok}/{len(pruebas)} pruebas aprobadas")
