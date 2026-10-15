"""U1: las condiciones cumplidas y no cumplidas habilitan únicamente las opciones correspondientes."""
import pytest

from conftest import ACT_CODIGO, ACT_SIN_VERIFICAR, CONTINUAR, CORTAR, INVESTIGAR, REVISAR, avanzar
from transmision.reglas import condiciones_cumplidas


@pytest.mark.parametrize(
    "condiciones, variables, esperado",
    [
        ({}, {"a": False}, True),                              # mapa vacío habilita
        ({"a": True}, {"a": True}, True),
        ({"a": True}, {"a": False}, False),
        ({"a": False}, {"a": False}, True),
        ({"a": True, "b": False}, {"a": True, "b": False}, True),
        ({"a": True, "b": False}, {"a": True, "b": True}, False),  # todas deben cumplirse
    ],
)
def test_u1_regla_pura(condiciones, variables, esperado):
    assert condiciones_cumplidas(condiciones, variables) is esperado


@pytest.mark.parametrize(
    "ruta, esperadas",
    [
        # Sabe el origen -> ve 'activar con código' y 'cortar'; no ve 'activar sin verificar'
        ([REVISAR, INVESTIGAR], {ACT_CODIGO, CORTAR}),
        # No sabe el origen -> ve 'activar sin verificar' y 'cortar'; no ve 'activar con código'
        ([REVISAR, CONTINUAR], {ACT_SIN_VERIFICAR, CORTAR}),
    ],
)
def test_u1_e3_muestra_exactamente_dos_opciones(sesion, ruta, esperadas):
    avanzar(sesion, *ruta)
    ids = [o.id for o in sesion.opciones_disponibles()]
    assert sesion.escena.id == "E3"
    assert len(ids) == 2
    assert set(ids) == esperadas


def test_u1_opcion_sin_condiciones_siempre_visible(sesion):
    assert [o.id for o in sesion.opciones_disponibles()] == [REVISAR]
