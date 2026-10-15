"""U2, U3, U5 y bloqueo de partida (RF-14)."""
import pytest

from conftest import (ACT_CODIGO, ACT_SIN_VERIFICAR, CONTINUAR, CORTAR, INVESTIGAR, REVISAR,
                      RUTAS_FINALES, avanzar)
from transmision import OpcionNoDisponible, Sesion, SinRetroceso, cargar_desde_texto


# ---------------------------------------------------------------- U2
@pytest.mark.parametrize(
    "ruta, escena_esperada, variables_esperadas",
    [
        ([REVISAR], "E2", {"conoce_origen": False, "confia_en_la_voz": False}),
        ([REVISAR, INVESTIGAR], "E3", {"conoce_origen": True, "confia_en_la_voz": False}),
        ([REVISAR, CONTINUAR], "E3", {"conoce_origen": False, "confia_en_la_voz": False}),
        ([REVISAR, INVESTIGAR, ACT_CODIGO], "E4", {"conoce_origen": True, "confia_en_la_voz": True}),
        ([REVISAR, CONTINUAR, ACT_SIN_VERIFICAR], "E5", {"conoce_origen": False, "confia_en_la_voz": True}),
        ([REVISAR, CONTINUAR, CORTAR], "E6", {"conoce_origen": False, "confia_en_la_voz": False}),
        ([REVISAR, INVESTIGAR, CORTAR], "E6", {"conoce_origen": True, "confia_en_la_voz": False}),
    ],
)
def test_u2_eleccion_valida_aplica_efectos_y_avanza(sesion, ruta, escena_esperada, variables_esperadas):
    avanzar(sesion, *ruta)
    assert sesion.escena.id == escena_esperada
    assert sesion.variables == variables_esperadas


def test_u2_elegir_devuelve_la_nueva_escena_y_registra_historial(sesion):
    nueva = sesion.elegir(REVISAR)
    assert nueva.id == "E2"
    assert sesion.historial == [("E1", REVISAR)]


# ---------------------------------------------------------------- U3
@pytest.mark.parametrize(
    "ruta_previa, opcion_invalida",
    [
        ([], "no_existe"),                       # opción inexistente
        ([], ""),                                # cadena vacía
        ([], None),                              # tipo incorrecto
        ([], 42),                                # tipo incorrecto
        ([], ACT_CODIGO),                        # existe en otra escena
        ([REVISAR, CONTINUAR], ACT_CODIGO),      # existe en la escena pero no está habilitada (CA02)
        ([REVISAR, INVESTIGAR], ACT_SIN_VERIFICAR),
        (RUTAS_FINALES["E4"], REVISAR),          # escena final
    ],
)
def test_u3_opcion_invalida_deja_estado_intacto(sesion, ruta_previa, opcion_invalida):
    avanzar(sesion, *ruta_previa)
    antes = (sesion.escena.id, sesion.variables, sesion.historial)
    with pytest.raises(OpcionNoDisponible):
        sesion.elegir(opcion_invalida)
    assert (sesion.escena.id, sesion.variables, sesion.historial) == antes


def test_u3_ca02_activar_con_codigo_rechazado_si_no_conoce_origen(sesion):
    avanzar(sesion, REVISAR, CONTINUAR)
    with pytest.raises(OpcionNoDisponible, match=ACT_CODIGO):
        sesion.elegir(ACT_CODIGO)
    assert sesion.escena.id == "E3"
    sesion.elegir(ACT_SIN_VERIFICAR)
    assert sesion.escena.id == "E5"


# ---------------------------------------------------------------- U5
@pytest.mark.parametrize("final", ["E4", "E5", "E6"])
def test_u5_reiniciar_restaura_escena_y_variables(sesion, historia, final):
    avanzar(sesion, *RUTAS_FINALES[final])
    assert sesion.es_final
    sesion.reiniciar()
    assert sesion.escena.id == historia.inicio
    assert sesion.variables == historia.variables
    assert sesion.historial == []


@pytest.mark.parametrize("ruta", [[REVISAR], [REVISAR, INVESTIGAR], RUTAS_FINALES["E4"]])
def test_u5_reiniciar_elimina_el_historial_de_retroceso(sesion, ruta):
    avanzar(sesion, *ruta)
    assert sesion.puede_deshacer
    sesion.reiniciar()
    assert not sesion.puede_deshacer
    with pytest.raises(SinRetroceso):
        sesion.deshacer()
    assert sesion.escena.id == "E1"


def test_u5_efectos_no_contaminan_la_historia_ni_la_partida_siguiente(sesion, historia):
    avanzar(sesion, REVISAR, INVESTIGAR)
    sesion.reiniciar()
    assert historia.variables == {"conoce_origen": False, "confia_en_la_voz": False}
    avanzar(sesion, REVISAR, CONTINUAR)
    # Si el estado anterior se hubiera conservado, 'activar con código' estaría habilitada
    assert {o.id for o in sesion.opciones_disponibles()} == {ACT_SIN_VERIFICAR, CORTAR}


# ------------------------------------------------------- bloqueo (RF-14)
JSON_BLOQUEO = """
{"titulo": "Bloqueo", "inicio": "A", "variables": {"x": false},
 "escenas": [
   {"id": "A", "texto": "Sin salida", "final": false,
    "opciones": [{"id": "o", "texto": "Imposible", "destino": "B",
                  "condiciones": {"x": true}, "efectos": {}}]},
   {"id": "B", "texto": "Fin", "final": true, "opciones": []}]}
"""


def test_bloqueo_se_detecta_y_se_puede_reiniciar():
    sesion = Sesion(cargar_desde_texto(JSON_BLOQUEO))
    assert sesion.bloqueada is True
    assert sesion.opciones_disponibles() == []
    with pytest.raises(OpcionNoDisponible):
        sesion.elegir("o")
    sesion.reiniciar()
    assert sesion.escena.id == "A"


def test_escena_final_no_se_considera_bloqueada(sesion):
    avanzar(sesion, *RUTAS_FINALES["E6"])
    assert sesion.es_final and not sesion.bloqueada
