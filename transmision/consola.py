"""Interfaz de consola (RF-04, RF-09, RF-14, RF-15, RF-19). No contiene reglas del juego."""
import argparse
import sys
from typing import Callable, List, Optional

from .cargador import HistoriaInvalida, cargar_archivo
from .sesion import OpcionNoDisponible, Sesion, SinRetroceso

ORDEN_DESHACER = "@deshacer"   # token reservado para reproducir un retroceso con --ruta
HISTORIA_POR_DEFECTO = "historias/la_ultima_transmision.json"


def mostrar_escena(sesion: Sesion, escribir: Callable[[str], None]) -> None:
    escena = sesion.escena
    escribir("")
    escribir(f"=== {escena.id} ===")
    escribir(escena.texto)
    if sesion.es_final:
        escribir("--- FIN DE LA HISTORIA ---")
    elif sesion.bloqueada:
        escribir("[Bloqueo] Ninguna opción está disponible en esta escena. "
                 "Revise las condiciones del contenido o reinicie la partida.")
    else:
        for n, opcion in enumerate(sesion.opciones_disponibles(), start=1):
            escribir(f"  {n}) {opcion.texto}")


def _resolver(sesion: Sesion, respuesta: str) -> str:
    """Traduce un número de la lista visible a un ID de opción; si no, devuelve lo escrito."""
    respuesta = respuesta.strip()
    visibles = sesion.opciones_disponibles()
    if respuesta.isdigit() and 1 <= int(respuesta) <= len(visibles):
        return visibles[int(respuesta) - 1].id
    return respuesta


def _deshacer(sesion: Sesion, escribir: Callable[[str], None]) -> bool:
    try:
        sesion.deshacer()
    except SinRetroceso as exc:
        escribir(f"No se puede deshacer: {exc}")
        return False
    escribir("\n(Última decisión deshecha)")
    return True


def jugar(sesion: Sesion, leer: Callable[[str], str] = input,
          escribir: Callable[[str], None] = print) -> None:
    """Bucle de partida. Termina con 'q', al final del flujo o por fin de entrada."""
    try:
        while True:
            mostrar_escena(sesion, escribir)
            if sesion.es_final or sesion.bloqueada:
                resp = leer("¿Jugar de nuevo? [s/n] ('u' deshace la última decisión): ").strip().lower()
                if resp == "u":
                    _deshacer(sesion, escribir)
                    continue
                if resp in ("s", "si", "sí"):
                    sesion.reiniciar()
                    escribir("\n(Nueva partida)")
                    continue
                return
            resp = leer("Elija una opción (número), 'u' deshace, 'r' reinicia, 'q' sale: ").strip()
            if resp.lower() == "q":
                return
            if resp.lower() == "u":
                _deshacer(sesion, escribir)
                continue
            if resp.lower() == "r":
                sesion.reiniciar()
                escribir("\n(Partida reiniciada)")
                continue
            try:
                sesion.elegir(_resolver(sesion, resp))
            except OpcionNoDisponible as exc:
                escribir(f"Entrada no válida: {exc}")
    except (EOFError, KeyboardInterrupt):
        escribir("\nPartida terminada.")


def ejecutar_ruta(sesion: Sesion, ids: List[str], escribir: Callable[[str], None] = print) -> bool:
    """Reproduce una secuencia de IDs de opción (para demostraciones). True si llega a un final."""
    mostrar_escena(sesion, escribir)
    for opcion_id in ids:
        if opcion_id == ORDEN_DESHACER:
            if not _deshacer(sesion, escribir):
                return False
            mostrar_escena(sesion, escribir)
            continue
        try:
            sesion.elegir(opcion_id)
        except OpcionNoDisponible as exc:
            escribir(f"Ruta interrumpida: {exc}")
            return False
        escribir(f"\n> Elegida: {opcion_id}")
        mostrar_escena(sesion, escribir)
    return sesion.es_final


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="transmision", description="Motor de historias interactivas.")
    parser.add_argument("historia", nargs="?", default=HISTORIA_POR_DEFECTO, help="archivo JSON de la historia")
    parser.add_argument("--validar", action="store_true", help="solo validar el archivo y salir")
    parser.add_argument("--ruta", help="IDs de opciones separados por comas para reproducir un recorrido; "
                                    "@deshacer retrocede la última decisión")
    args = parser.parse_args(argv)

    try:
        historia = cargar_archivo(args.historia)
    except HistoriaInvalida as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.validar:
        print(f"OK: '{args.historia}' es válida ({len(historia.escenas)} escenas).")
        return 0

    sesion = Sesion(historia)
    print(f"*** {historia.titulo} ***")
    if args.ruta:
        llego = ejecutar_ruta(sesion, [p.strip() for p in args.ruta.split(",") if p.strip()])
        return 0 if llego else 1
    jugar(sesion)
    return 0


if __name__ == "__main__":
    sys.exit(main())
