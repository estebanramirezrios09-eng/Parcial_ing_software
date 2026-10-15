"""U4: errores de contenido -> rechazo controlado, con causa y campo/ID en el mensaje (RF-10 a RF-13).

Cubre las nueve categorías exigidas: ilegible/estructura, campo ausente, inicio inexistente,
escena duplicada, opción duplicada, destino inexistente, variable no declarada, valor no booleano
y cantidad de opciones incompatible con 'final'."""
import json

import pytest

from transmision import HistoriaInvalida, cargar_archivo, cargar_desde_texto
from transmision import diagnostico as d


def _e(datos, sid):
    return next(e for e in datos["escenas"] if e["id"] == sid)


def _o(datos, sid, oid):
    return next(o for o in _e(datos, sid)["opciones"] if o["id"] == oid)


def _pop(obj, clave):
    """Elimina una clave y devuelve None (las mutaciones solo devuelven valor si reemplazan la raíz)."""
    obj.pop(clave)


def _upd(obj, **kw):
    obj.update(**kw)


def _quitar(clave):
    return lambda dt: _pop(dt, clave)


CASOS = [
    # (id, mutación, código esperado, fragmento que debe aparecer en el mensaje)
    ("raiz_no_objeto", lambda dt: [dt], d.E_ESTRUCTURA, "raíz"),
    ("escenas_no_lista", lambda dt: _upd(dt, escenas={"E1": 1}), d.E_ESTRUCTURA, "escenas"),
    ("escena_no_objeto", lambda dt: dt["escenas"].append("texto suelto"), d.E_ESTRUCTURA, "posición 6"),
    ("falta_titulo", _quitar("titulo"), d.E_CAMPO_AUSENTE, "titulo"),
    ("falta_inicio", _quitar("inicio"), d.E_CAMPO_AUSENTE, "inicio"),
    ("falta_variables", _quitar("variables"), d.E_CAMPO_AUSENTE, "variables"),
    ("falta_escenas", _quitar("escenas"), d.E_CAMPO_AUSENTE, "escenas"),
    ("escena_sin_texto", lambda dt: _pop(_e(dt, "E2"), "texto"), d.E_CAMPO_AUSENTE, "E2"),
    ("escena_sin_final", lambda dt: _pop(_e(dt, "E4"), "final"), d.E_CAMPO_AUSENTE, "E4"),
    ("opcion_sin_destino", lambda dt: _pop(_o(dt, "E2", "investigar"), "destino"), d.E_CAMPO_AUSENTE, "investigar"),
    ("opcion_sin_efectos", lambda dt: _pop(_o(dt, "E1", "revisar"), "efectos"), d.E_CAMPO_AUSENTE, "revisar"),
    ("inicio_inexistente", lambda dt: dt.update(inicio="E0"), d.E_INICIO, "E0"),
    ("escena_duplicada", lambda dt: _e(dt, "E6").update(id="E5"), d.E_ESCENA_DUP, "E5"),
    ("opcion_duplicada", lambda dt: _o(dt, "E2", "continuar").update(id="investigar"), d.E_OPCION_DUP, "investigar"),
    ("destino_inexistente_E99", lambda dt: _o(dt, "E1", "revisar").update(destino="E99"), d.E_DESTINO, "E99"),
    ("condicion_variable_no_declarada",
     lambda dt: _o(dt, "E3", "cortar")["condiciones"].update(fantasma=True), d.E_VARIABLE, "fantasma"),
    ("efecto_variable_no_declarada",
     lambda dt: _o(dt, "E2", "continuar")["efectos"].update(otra=True), d.E_VARIABLE, "otra"),
    ("condicion_no_booleana",
     lambda dt: _o(dt, "E3", "activar_codigo")["condiciones"].update(conoce_origen="si"), d.E_NO_BOOL, "conoce_origen"),
    ("efecto_no_booleano",
     lambda dt: _o(dt, "E2", "investigar")["efectos"].update(conoce_origen=1), d.E_NO_BOOL, "conoce_origen"),
    ("variable_inicial_no_booleana",
     lambda dt: dt["variables"].update(conoce_origen="no"), d.E_NO_BOOL, "conoce_origen"),
    ("final_con_opciones",
     lambda dt: _e(dt, "E4")["opciones"].append(dict(_o(dt, "E1", "revisar"), id="extra")),
     d.E_FINAL_OPCIONES, "E4"),
    ("no_final_sin_opciones", lambda dt: _e(dt, "E2").update(opciones=[]), d.E_FINAL_OPCIONES, "E2"),
]


@pytest.mark.parametrize("mutar, codigo, fragmento", [c[1:] for c in CASOS], ids=[c[0] for c in CASOS])
def test_u4_error_de_contenido_produce_rechazo_controlado(datos, mutar, codigo, fragmento):
    resultado = mutar(datos)
    contenido = datos if resultado is None else resultado
    with pytest.raises(HistoriaInvalida) as info:
        cargar_desde_texto(json.dumps(contenido), "caso.json")
    codigos = [x.codigo for x in info.value.diagnosticos]
    assert codigo in codigos
    mensaje = next(str(x) for x in info.value.diagnosticos if x.codigo == codigo)
    assert fragmento in mensaje, f"el mensaje no menciona '{fragmento}': {mensaje}"


@pytest.mark.parametrize(
    "texto",
    ["", "{no es json", '{"titulo": "x",', "[1, 2", "\x00\x01", "null y mas"],
    ids=["vacio", "llave_sin_cerrar", "coma_final", "lista_truncada", "binario", "basura"],
)
def test_u4_archivo_ilegible(texto):
    with pytest.raises(HistoriaInvalida) as info:
        cargar_desde_texto(texto, "roto.json")
    assert info.value.diagnosticos[0].codigo == d.E_ILEGIBLE
    assert "JSON" in str(info.value)


def test_u4_archivo_inexistente_y_codificacion(tmp_path):
    with pytest.raises(HistoriaInvalida) as info:
        cargar_archivo(str(tmp_path / "nada.json"))
    assert info.value.diagnosticos[0].codigo == d.E_ILEGIBLE
    assert "nada.json" in str(info.value)

    binario = tmp_path / "latin.json"
    binario.write_bytes('{"titulo": "á"}'.encode("latin-1"))
    with pytest.raises(HistoriaInvalida) as info:
        cargar_archivo(str(binario))
    assert info.value.diagnosticos[0].codigo == d.E_ILEGIBLE
    assert "UTF-8" in str(info.value)


def test_u4_ca03_destino_inexistente_no_abre_sesion(datos, tmp_path):
    from transmision import Sesion
    datos["escenas"][0]["opciones"][0]["destino"] = "E99"
    ruta = tmp_path / "copia.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    sesion = None
    with pytest.raises(HistoriaInvalida) as info:
        sesion = Sesion(cargar_archivo(str(ruta)))
    assert sesion is None
    assert "E99" in str(info.value) and "revisar" in str(info.value)


def test_u4_acumula_varios_errores(datos):
    _o(datos, "E1", "revisar")["destino"] = "E99"
    datos["inicio"] = "E0"
    with pytest.raises(HistoriaInvalida) as info:
        cargar_desde_texto(json.dumps(datos))
    assert {x.codigo for x in info.value.diagnosticos} == {d.E_DESTINO, d.E_INICIO}


def test_u4_historia_valida_no_produce_diagnosticos(datos):
    from transmision.validador import validar
    assert validar(datos) == []
