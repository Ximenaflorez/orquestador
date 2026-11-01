"""Comandos del ciclo mensual."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orquestador.config import cargar_ajustes, cargar_entorno, proyecto_raiz
from orquestador.grafo import ejecutar
from orquestador.ingesta import mes_del_nombre, EntradaInvalida


def main(argv: list[str] | None = None) -> int:
    cargar_entorno()
    parser = argparse.ArgumentParser(prog="orquestador")
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    correr = subcomandos.add_parser("correr")
    correr.add_argument("--mes")
    correr.add_argument("--archivo")
    consultar = subcomandos.add_parser("consultar")
    consultar.add_argument("--puerto", type=int, default=8765)
    consultar.add_argument("--sin-navegador", action="store_true")
    argumentos = parser.parse_args(argv)
    if argumentos.comando == "correr":
        return _correr(argumentos.mes, argumentos.archivo)
    if argumentos.comando == "consultar":
        from orquestador.vista import servir

        return servir(proyecto_raiz(), argumentos.puerto, abrir=not argumentos.sin_navegador)
    return 1


def _correr(mes: str | None, archivo: str | None) -> int:
    raiz = proyecto_raiz()
    try:
        ruta, mes_resuelto = _resolver(raiz, mes, archivo)
    except EntradaInvalida as exc:
        print(exc.motivo, file=sys.stderr)
        return 2
    try:
        _corrida, codigo = ejecutar(ruta, mes_resuelto, raiz, cargar_ajustes())
    except Exception:
        print("Error inesperado de ejecución", file=sys.stderr)
        return 1
    return codigo


def _resolver(raiz: Path, mes: str | None, archivo: str | None) -> tuple[Path, str]:
    if archivo:
        ruta = Path(archivo)
        if not ruta.is_absolute():
            ruta = raiz / ruta
        mes_archivo = mes_del_nombre(ruta)
        if mes and mes != mes_archivo:
            raise EntradaInvalida("El mes indicado y el nombre del archivo no coinciden.")
        return ruta, mes_archivo
    if not mes:
        raise EntradaInvalida("Indica --mes o deja el archivo del mes en datos/meses.")
    ruta = raiz / "datos" / "meses" / f"feedback_response_{mes}.xlsx"
    return ruta, mes
