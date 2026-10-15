"""Los tres RNF como pruebas automatizadas (versión reducida; la completa es verificar_rnf.py)."""
import verificar_rnf as v


def test_rnf01_modificabilidad_sin_tocar_el_motor():
    ok, detalle = v.rnf01()
    assert ok, detalle


def test_rnf02_claridad_de_errores_diez_de_diez():
    ok, detalle = v.rnf02()
    assert ok, detalle


def test_rnf03_confiabilidad_sin_excepciones_no_controladas():
    ok, detalle = v.rnf03(n_json=150, n_entradas=100)
    assert ok, detalle
