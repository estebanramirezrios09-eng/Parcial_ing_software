"""Datos compartidos. Si el archivo oficial del docente usa otros IDs de opción,
basta con ajustar las constantes de este módulo."""
import copy
import json
import pathlib
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from transmision import Sesion, cargar_archivo  # noqa: E402

HISTORIA_PRINCIPAL = RAIZ / "historias" / "la_ultima_transmision.json"
HISTORIA_SEGUNDA = RAIZ / "historias" / "el_faro.json"

# IDs de opción de la historia principal (E1 -> E2 -> E3 -> finales)
REVISAR, INVESTIGAR, CONTINUAR = "revisar", "investigar", "continuar"
ACT_CODIGO, ACT_SIN_VERIFICAR, CORTAR = "activar_codigo", "activar_sin_verificar", "cortar"

# Recorridos hacia cada final
RUTAS_FINALES = {
    "E4": [REVISAR, INVESTIGAR, ACT_CODIGO],
    "E5": [REVISAR, CONTINUAR, ACT_SIN_VERIFICAR],
    "E6": [REVISAR, CONTINUAR, CORTAR],
}


@pytest.fixture
def datos():
    """Copia profunda del JSON real, lista para mutar en cada prueba."""
    with open(HISTORIA_PRINCIPAL, encoding="utf-8") as fh:
        return copy.deepcopy(json.load(fh))


@pytest.fixture
def historia():
    return cargar_archivo(str(HISTORIA_PRINCIPAL))


@pytest.fixture
def sesion(historia):
    return Sesion(historia)


def avanzar(sesion, *ids):
    for i in ids:
        sesion.elegir(i)
    return sesion
