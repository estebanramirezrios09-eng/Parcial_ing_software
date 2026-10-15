"""Lectura de archivos de historia (RF-01, RF-09). Única capa que toca el disco."""
import json
from typing import List

from .diagnostico import Diagnostico, E_ILEGIBLE
from .modelos import Historia
from .validador import construir_historia, validar


class HistoriaInvalida(Exception):
    """El contenido no es jugable. Lleva todos los diagnósticos encontrados."""

    def __init__(self, diagnosticos: List[Diagnostico], origen: str = "<texto>"):
        self.diagnosticos = list(diagnosticos)
        self.origen = origen
        super().__init__(str(self))

    def __str__(self) -> str:
        lineas = [f"La historia '{self.origen}' no es válida ({len(self.diagnosticos)} problema(s)):"]
        lineas += [f"  - {d}" for d in self.diagnosticos]
        return "\n".join(lineas)


def cargar_desde_texto(texto: str, origen: str = "<texto>") -> Historia:
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, RecursionError) as exc:
        detalle = f"línea {exc.lineno}, columna {exc.colno}: {exc.msg}" if isinstance(exc, json.JSONDecodeError) \
            else "estructura demasiado anidada"
        raise HistoriaInvalida(
            [Diagnostico(E_ILEGIBLE, f"El contenido no es JSON válido ({detalle}).", origen)], origen
        ) from None
    problemas = validar(datos)
    if problemas:
        raise HistoriaInvalida(problemas, origen)
    return construir_historia(datos)


def cargar_archivo(ruta: str) -> Historia:
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            texto = fh.read()
    except FileNotFoundError:
        raise HistoriaInvalida([Diagnostico(E_ILEGIBLE, f"No existe el archivo '{ruta}'.", str(ruta))], str(ruta)) from None
    except UnicodeDecodeError:
        raise HistoriaInvalida(
            [Diagnostico(E_ILEGIBLE, f"El archivo '{ruta}' no está codificado en UTF-8.", str(ruta))], str(ruta)
        ) from None
    except OSError as exc:
        raise HistoriaInvalida(
            [Diagnostico(E_ILEGIBLE, f"No se pudo leer el archivo '{ruta}': {exc.strerror}.", str(ruta))], str(ruta)
        ) from None
    return cargar_desde_texto(texto, str(ruta))
