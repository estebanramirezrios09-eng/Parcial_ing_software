"""U6: deshacer la última decisión (RF-19 a RF-22, solicitud de cambio de la hora 6)."""
import pytest

from conftest import (ACT_CODIGO, ACT_SIN_VERIFICAR, CONTINUAR, CORTAR, INVESTIGAR, REVISAR,
                      RUTAS_FINALES, avanzar)
from transmision import OpcionNoDisponible, SinRetroceso

INICIALES = {"conoce_origen": False, "confia_en_la_voz": False}


def _estado(s):
    return (s.escena.id, s.variables, s.historial)


def test_u6_ejemplo_del_anexo_investigar_deshacer_continuar(sesion):
    avanzar(sesion, REVISAR, INVESTIGAR)
    assert sesion.escena.id == "E3" and sesion.variables["conoce_origen"] is True
    sesion.deshacer()
    assert sesion.escena.id == "E2" and sesion.variables == INICIALES
    antes = _estado(sesion)
    with pytest.raises(SinRetroceso):          # un solo nivel
        sesion.deshacer()
    assert _estado(sesion) == antes
    sesion.elegir(CONTINUAR)
    assert {o.id for o in sesion.opciones_disponibles()} == {ACT_SIN_VERIFICAR, CORTAR}


@pytest.mark.parametrize(
    "ruta, escena_prev, vars_prev",
    [
        ([REVISAR], "E1", INICIALES),
        ([REVISAR, INVESTIGAR], "E2", INICIALES),
        ([REVISAR, CONTINUAR], "E2", INICIALES),
        ([REVISAR, INVESTIGAR, ACT_CODIGO], "E3", {"conoce_origen": True, "confia_en_la_voz": False}),
        ([REVISAR, CONTINUAR, ACT_SIN_VERIFICAR], "E3", INICIALES),
        ([REVISAR, CONTINUAR, CORTAR], "E3", INICIALES),
    ],
)
def test_u6_deshacer_restaura_escena_variables_e_historial(sesion, ruta, escena_prev, vars_prev):
    avanzar(sesion, *ruta)
    assert sesion.puede_deshacer
    sesion.deshacer()
    assert sesion.escena.id == escena_prev
    assert sesion.variables == vars_prev
    assert sesion.historial == [(e, o) for e, o in zip(["E1", "E2", "E3"], ruta[:-1])]
    assert not sesion.puede_deshacer           # consume la posibilidad de retroceder


@pytest.mark.parametrize("final", ["E4", "E5", "E6"])
def test_u6_se_puede_deshacer_desde_un_final_y_vuelve_a_e3(sesion, final):
    avanzar(sesion, *RUTAS_FINALES[final])
    assert sesion.es_final
    sesion.deshacer()
    assert sesion.escena.id == "E3" and not sesion.es_final


def test_u6_al_comenzar_no_hay_retroceso(sesion):
    assert not sesion.puede_deshacer
    antes = _estado(sesion)
    with pytest.raises(SinRetroceso):
        sesion.deshacer()
    assert _estado(sesion) == antes


@pytest.mark.parametrize("invalida", ["no_existe", "", None, 42, ACT_CODIGO])
def test_u6_entrada_invalida_conserva_el_historial_de_la_ultima_eleccion_valida(sesion, invalida):
    avanzar(sesion, REVISAR, CONTINUAR)        # en E3 sin origen: ACT_CODIGO no está habilitada
    antes = _estado(sesion)
    with pytest.raises(OpcionNoDisponible):
        sesion.elegir(invalida)
    assert _estado(sesion) == antes and sesion.puede_deshacer
    sesion.deshacer()                          # sigue deshaciendo CONTINUAR, no otra cosa
    assert sesion.escena.id == "E2" and sesion.historial == [("E1", REVISAR)]


def test_u6_una_nueva_eleccion_valida_vuelve_a_habilitar_el_retroceso(sesion):
    avanzar(sesion, REVISAR, INVESTIGAR)
    sesion.deshacer()
    assert not sesion.puede_deshacer
    sesion.elegir(CONTINUAR)
    assert sesion.puede_deshacer
    sesion.deshacer()
    assert sesion.escena.id == "E2" and sesion.variables == INICIALES


def test_u6_no_deja_estado_compartido_con_la_instantanea(sesion):
    avanzar(sesion, REVISAR, INVESTIGAR)
    sesion.deshacer()
    sesion.elegir(INVESTIGAR)
    assert sesion.variables["conoce_origen"] is True
    sesion.deshacer()
    assert sesion.variables == INICIALES
