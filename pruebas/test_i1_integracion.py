"""I1: lectura de archivos reales + motor + consola, de la carga a los finales (CA01, CA02, CA03)."""
import pytest

from conftest import (ACT_CODIGO, ACT_SIN_VERIFICAR, CONTINUAR, CORTAR, HISTORIA_PRINCIPAL, HISTORIA_SEGUNDA,
                      INVESTIGAR, RAIZ, REVISAR, RUTAS_FINALES, avanzar)
from transmision import HistoriaInvalida, OpcionNoDisponible, Sesion, SinRetroceso, cargar_archivo
from transmision.consola import ejecutar_ruta, jugar, main


@pytest.mark.parametrize("final", ["E4", "E5", "E6"])
def test_i1_los_tres_finales_son_alcanzables_desde_el_archivo(final):
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    avanzar(sesion, *RUTAS_FINALES[final])
    assert sesion.escena.id == final
    assert sesion.es_final
    assert sesion.opciones_disponibles() == []


def test_i1_ca01_revisar_e_investigar_lleva_a_e3_con_origen_conocido():
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    avanzar(sesion, REVISAR, INVESTIGAR)
    assert sesion.escena.id == "E3"
    assert sesion.variables["conoce_origen"] is True
    assert [o.texto for o in sesion.opciones_disponibles()] == ["Activar con código", "Cortar comunicación"]


def test_i1_ca02_activar_sin_verificar_y_rechazo_directo_del_id():
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    avanzar(sesion, REVISAR, CONTINUAR)
    with pytest.raises(OpcionNoDisponible):
        sesion.elegir(ACT_CODIGO)
    sesion.elegir(ACT_SIN_VERIFICAR)
    assert sesion.escena.id == "E5"


@pytest.mark.parametrize("final", ["E4", "E5", "E6"])
def test_i1_deshacer_desde_un_final_tras_cargar_y_recorrer_el_archivo(final):
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    avanzar(sesion, *RUTAS_FINALES[final])
    assert sesion.es_final
    sesion.deshacer()
    assert sesion.escena.id == "E3"
    assert sesion.variables["confia_en_la_voz"] is False
    with pytest.raises(SinRetroceso):
        sesion.deshacer()
    # E3 sigue ofreciendo las opciones que corresponden al estado restaurado
    esperadas = {"E4": {ACT_CODIGO, CORTAR}, "E5": {ACT_SIN_VERIFICAR, CORTAR}, "E6": {ACT_SIN_VERIFICAR, CORTAR}}
    assert {o.id for o in sesion.opciones_disponibles()} == esperadas[final]


def test_i1_consola_deshacer_en_ruta_e_interactivo():
    salida = []
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    assert ejecutar_ruta(sesion, [REVISAR, INVESTIGAR, "@deshacer", CONTINUAR, ACT_SIN_VERIFICAR], salida.append)
    assert "Activar sin verificar" in "\n".join(salida)
    # 'u' al comenzar: mensaje controlado; luego 1 (E2), 'u' deshace, 'q' sale
    respuestas = iter(["u", "1", "u", "q"])
    salida = []
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    jugar(sesion, leer=lambda _: next(respuestas), escribir=salida.append)
    texto = "\n".join(salida)
    assert "No se puede deshacer" in texto and "Última decisión deshecha" in texto
    assert sesion.escena.id == "E1"


def test_i1_ca03_archivo_con_destino_inexistente_se_rechaza():
    with pytest.raises(HistoriaInvalida) as info:
        cargar_archivo(str(RAIZ / "historias" / "invalidas" / "destino_inexistente.json"))
    assert "E99" in str(info.value)


def test_i1_segunda_historia_funciona_con_el_mismo_motor():
    sesion = Sesion(cargar_archivo(str(HISTORIA_SEGUNDA)))
    assert len(sesion.historia.escenas) >= 3
    avanzar(sesion, "tomar_llave")
    assert {o.id for o in sesion.opciones_disponibles()} == {"abrir_puerta", "esperar"}
    avanzar(sesion, "abrir_puerta")
    assert sesion.escena.id == "sala_luz" and sesion.es_final
    # Sin la llave, la puerta no se ofrece
    sesion.reiniciar()
    avanzar(sesion, "encender_linterna")
    assert {o.id for o in sesion.opciones_disponibles()} == {"esperar"}
    with pytest.raises(OpcionNoDisponible):
        sesion.elegir("abrir_puerta")


def test_i1_consola_ruta_reproducida_llega_al_final():
    salida = []
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    assert ejecutar_ruta(sesion, RUTAS_FINALES["E4"], salida.append) is True
    texto = "\n".join(salida)
    assert "Activar con código" in texto and "FIN DE LA HISTORIA" in texto


def test_i1_consola_interactiva_entrada_invalida_y_reinicio():
    respuestas = iter(["abc", "9", "1", "2", "1", "2", "s", "q"])
    salida = []
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))
    # 'abc' y '9' son inválidos; 1->E2, 2 (continuar)->E3 (conoce_origen False), 1->activar sin verificar->E5,
    # luego el menú pregunta si jugar de nuevo ('2' sobra y se ignora como respuesta no afirmativa)
    jugar(sesion, leer=lambda _: next(respuestas), escribir=salida.append)
    texto = "\n".join(salida)
    assert texto.count("Entrada no válida") == 2
    assert "=== E5 ===" in texto


def test_i1_consola_fin_de_entrada_no_produce_excepcion():
    sesion = Sesion(cargar_archivo(str(HISTORIA_PRINCIPAL)))

    def sin_entrada(_):
        raise EOFError

    salida = []
    jugar(sesion, leer=sin_entrada, escribir=salida.append)
    assert "Partida terminada." in "\n".join(salida)


def test_i1_main_codigos_de_salida(capsys):
    assert main([str(HISTORIA_PRINCIPAL), "--validar"]) == 0
    assert main([str(RAIZ / "historias" / "invalidas" / "destino_inexistente.json")]) == 2
    assert "E99" in capsys.readouterr().err
    assert main([str(HISTORIA_PRINCIPAL), "--ruta", ",".join(RUTAS_FINALES["E6"])]) == 0
    assert main([str(HISTORIA_PRINCIPAL), "--ruta", f"{REVISAR},{ACT_CODIGO}"]) == 1
    assert main([str(RAIZ / "no_existe.json")]) == 2
