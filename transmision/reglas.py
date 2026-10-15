"""Reglas puras del juego (RF-06, RF-08). No dependen de ninguna historia concreta."""
from typing import Dict, Mapping

from .modelos import Opcion


def condiciones_cumplidas(condiciones: Mapping[str, bool], variables: Mapping[str, bool]) -> bool:
    """Todas las igualdades deben cumplirse; un mapa vacío habilita la opción."""
    return all(variables.get(nombre) == valor for nombre, valor in condiciones.items())


def opcion_habilitada(opcion: Opcion, variables: Mapping[str, bool]) -> bool:
    return condiciones_cumplidas(opcion.condiciones, variables)


def aplicar_efectos(variables: Mapping[str, bool], efectos: Mapping[str, bool]) -> Dict[str, bool]:
    """Devuelve una copia nueva con los efectos aplicados; no modifica la original."""
    nuevas = dict(variables)
    nuevas.update(efectos)
    return nuevas
