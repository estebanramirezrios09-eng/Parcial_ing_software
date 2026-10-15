"""Verificación local y reproducible de los tres RNF. Uso:  python pruebas/verificar_rnf.py

RNF-01 Modificabilidad del contenido
RNF-02 Claridad de los errores
RNF-03 Confiabilidad ante entradas inválidas
Escribe el resultado en resultados/rnf.txt y termina con código 1 si algún RNF falla."""
import ast
import copy
import hashlib
import json
import pathlib
import random
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from transmision import HistoriaInvalida, OpcionNoDisponible, Sesion, cargar_archivo, cargar_desde_texto  # noqa: E402
from transmision import diagnostico as d  # noqa: E402
from transmision.consola import jugar  # noqa: E402

PRINCIPAL = RAIZ / "historias" / "la_ultima_transmision.json"
SEGUNDA = RAIZ / "historias" / "el_faro.json"
SEMILLA = 20261014


# ------------------------------------------------------------------ RNF-01
def hash_codigo():
    return {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((RAIZ / "transmision").glob("*.py"))}


def textos_ejecutables(ruta):
    """Literales de texto y nombres que usa el código, sin docstrings ni comentarios."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(getattr(cuerpo[0], "value", None), ast.Constant) \
                    and isinstance(cuerpo[0].value.value, str):
                docstrings.add(id(cuerpo[0].value))
    textos = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docstrings:
            textos.append(nodo.value)
        elif isinstance(nodo, ast.Name):
            textos.append(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            textos.append(nodo.attr)
        elif isinstance(nodo, (ast.arg,)):
            textos.append(nodo.arg)
        elif isinstance(nodo, ast.keyword) and nodo.arg:
            textos.append(nodo.arg)
    return textos


def rnf01():
    """Criterios: (a) 0 archivos .py modificados al cargar y jugar la segunda historia;
    (b) 0 apariciones de IDs o variables de las historias en los literales y nombres que ejecuta
    el código del motor (análisis con ast; se ignoran docstrings y comentarios);
    (c) la segunda historia (>=3 escenas) se juega hasta un final."""
    antes = hash_codigo()
    sesion = Sesion(cargar_archivo(str(SEGUNDA)))
    n_escenas = len(sesion.historia.escenas)
    sesion.elegir("tomar_llave")
    sesion.elegir("abrir_puerta")
    llego = sesion.es_final
    modificados = [k for k, v in hash_codigo().items() if antes.get(k) != v]

    identificadores = set()
    for ruta in (PRINCIPAL, SEGUNDA):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        identificadores |= set(datos["variables"])
        for esc in datos["escenas"]:
            identificadores.add(esc["id"])
            identificadores |= {o["id"] for o in esc["opciones"]}
    apariciones = []
    for p in sorted((RAIZ / "transmision").glob("*.py")):
        textos = textos_ejecutables(p)
        for ident in sorted(identificadores):
            patron = rf"(?<![A-Za-z0-9_]){re.escape(ident)}(?![A-Za-z0-9_])"
            if any(re.search(patron, t) for t in textos):
                apariciones.append(f"{p.name}:{ident}")
    ok = not modificados and not apariciones and n_escenas >= 3 and llego
    detalle = [
        f"Archivos .py del motor modificados al usar la 2.ª historia: {len(modificados)} (meta: 0)",
        f"IDs de escena/opción/variable de las historias hallados en literales/nombres de transmision/*.py: {len(apariciones)} (meta: 0)"
        + (f" -> {apariciones}" if apariciones else ""),
        f"Escenas de la 2.ª historia: {n_escenas} (meta: >= 3); llegó a un final: {llego}",
    ]
    return ok, detalle


# ------------------------------------------------------------------ RNF-02
def _casos_error():
    base = json.loads(PRINCIPAL.read_text(encoding="utf-8"))

    def con(fn):
        dt = copy.deepcopy(base)
        fn(dt)
        return json.dumps(dt)

    def esc(dt, i):
        return next(e for e in dt["escenas"] if e["id"] == i)

    def op(dt, i, o):
        return next(x for x in esc(dt, i)["opciones"] if x["id"] == o)

    return [
        (d.E_ILEGIBLE, "línea", "{no es json"),
        (d.E_ESTRUCTURA, "escenas", con(lambda x: x.update(escenas=5))),
        (d.E_CAMPO_AUSENTE, "titulo", con(lambda x: x.pop("titulo"))),
        (d.E_INICIO, "E0", con(lambda x: x.update(inicio="E0"))),
        (d.E_ESCENA_DUP, "E5", con(lambda x: esc(x, "E6").update(id="E5"))),
        (d.E_OPCION_DUP, "investigar", con(lambda x: op(x, "E2", "continuar").update(id="investigar"))),
        (d.E_DESTINO, "E99", con(lambda x: op(x, "E1", "revisar").update(destino="E99"))),
        (d.E_VARIABLE, "fantasma", con(lambda x: op(x, "E3", "cortar")["condiciones"].update(fantasma=True))),
        (d.E_NO_BOOL, "conoce_origen", con(lambda x: op(x, "E2", "investigar")["efectos"].update(conoce_origen=1))),
        (d.E_FINAL_OPCIONES, "E2", con(lambda x: esc(x, "E2").update(opciones=[]))),
    ]


def rnf02():
    """Criterio: 10/10 variantes de error producen un mensaje con la causa (código) y el
    campo o ID involucrado, sin lanzar excepciones distintas de HistoriaInvalida."""
    filas, aciertos = [], 0
    for codigo, esperado, texto in _casos_error():
        try:
            cargar_desde_texto(texto, "variante.json")
            res = "NO RECHAZADO"
        except HistoriaInvalida as exc:
            msgs = [str(x) for x in exc.diagnosticos if x.codigo == codigo]
            ok = bool(msgs) and esperado in msgs[0]
            res = "OK   " if ok else "FALLA"
            aciertos += ok
            filas.append(f"{res} {codigo:<17} contiene '{esperado}': {msgs[0] if msgs else exc.diagnosticos}")
            continue
        filas.append(f"{res} {codigo}")
    total = len(_casos_error())
    return aciertos == total, [f"Variantes con mensaje correcto: {aciertos}/{total} (meta: {total}/{total})"] + filas


# ------------------------------------------------------------------ RNF-03
def _mutar(valor, rng):
    return rng.choice([None, 1, 3.5, "E99", "", [], {}, True, False, {"x": 1}, [1, 2], "\x00"])


def _rutas(nodo, ruta=()):
    yield ruta
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            yield from _rutas(v, ruta + (k,))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from _rutas(v, ruta + (i,))


def rnf03(n_json=500, n_entradas=500):
    """Criterio: 0 excepciones no controladas en n_json contenidos mutados al azar y n_entradas
    entradas aleatorias de teclado/identificadores (semilla fija)."""
    rng = random.Random(SEMILLA)
    base = json.loads(PRINCIPAL.read_text(encoding="utf-8"))
    no_controladas, rechazadas, aceptadas = [], 0, 0
    for i in range(n_json):
        dt = copy.deepcopy(base)
        for _ in range(rng.randint(1, 3)):
            rutas = [r for r in _rutas(dt) if r]
            r = rng.choice(rutas)
            padre = dt
            for k in r[:-1]:
                padre = padre[k]
            if rng.random() < 0.3 and isinstance(padre, dict):
                padre.pop(r[-1], None)
            else:
                padre[r[-1]] = _mutar(padre[r[-1]], rng)
        texto = json.dumps(dt)
        if rng.random() < 0.1:
            texto = texto[: rng.randint(0, len(texto))]
        try:
            h = cargar_desde_texto(texto, f"mutante{i}")
            aceptadas += 1
            Sesion(h)  # si se acepta, debe poder abrirse una sesión
        except HistoriaInvalida:
            rechazadas += 1
        except Exception as exc:  # noqa: BLE001
            no_controladas.append(f"json#{i}: {type(exc).__name__}: {exc}")

    # entradas aleatorias al motor y a la consola
    alfabeto = ["", " ", "0", "1", "2", "3", "-1", "99", "abc", "revisar", "investigar", "activar_codigo",
                "cortar", "r", "q", "s", "n", "'; DROP", "\t", "é", "💥", "1.5", "None"]
    for i in range(n_entradas):
        sesion = Sesion(cargar_archivo(str(PRINCIPAL)))
        for _ in range(rng.randint(1, 8)):
            try:
                sesion.elegir(rng.choice(alfabeto))
            except OpcionNoDisponible:
                pass
            except Exception as exc:  # noqa: BLE001
                no_controladas.append(f"motor#{i}: {type(exc).__name__}: {exc}")
        guion = iter(rng.choice(alfabeto) for _ in range(30))

        def leer(_):
            try:
                return next(guion)
            except StopIteration:
                raise EOFError from None

        try:
            jugar(Sesion(cargar_archivo(str(PRINCIPAL))), leer=leer, escribir=lambda _: None)
        except Exception as exc:  # noqa: BLE001
            no_controladas.append(f"consola#{i}: {type(exc).__name__}: {exc}")
    detalle = [
        f"Contenidos mutados: {n_json} (rechazados {rechazadas}, aceptados {aceptadas}); "
        f"entradas aleatorias al motor y la consola: {n_entradas} partidas; semilla {SEMILLA}",
        f"Excepciones no controladas: {len(no_controladas)} (meta: 0)",
    ] + no_controladas[:10]
    return not no_controladas, detalle


def main():
    resultados = [
        ("RNF-01 Modificabilidad del contenido", rnf01()),
        ("RNF-02 Claridad de los errores", rnf02()),
        ("RNF-03 Confiabilidad ante entradas inválidas", rnf03()),
    ]
    lineas = ["VERIFICACIÓN DE REQUISITOS NO FUNCIONALES", "=" * 42]
    todo_ok = True
    for nombre, (ok, detalle) in resultados:
        todo_ok &= ok
        lineas.append(f"\n{nombre}: {'CUMPLE' if ok else 'NO CUMPLE'}")
        lineas += [f"  {x}" for x in detalle]
    lineas.append(f"\nRESULTADO GLOBAL: {'3/3 RNF cumplen' if todo_ok else 'HAY RNF QUE NO CUMPLEN'}")
    texto = "\n".join(lineas)
    print(texto)
    (RAIZ / "resultados").mkdir(exist_ok=True)
    (RAIZ / "resultados" / "rnf.txt").write_text(texto + "\n", encoding="utf-8")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
