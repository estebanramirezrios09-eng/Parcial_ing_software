"""Validación del contenido (RF-10 a RF-13). Opera sobre el dato crudo (dict/list)
y acumula todos los diagnósticos en lugar de detenerse en el primero."""
from typing import Any, Dict, List, Set

from .diagnostico import (
    Diagnostico, E_CAMPO_AUSENTE, E_DESTINO, E_ESCENA_DUP, E_ESTRUCTURA,
    E_FINAL_OPCIONES, E_INICIO, E_NO_BOOL, E_OPCION_DUP, E_VARIABLE,
)
from .modelos import Escena, Historia, Opcion

CAMPOS_HISTORIA = (
    ("titulo", str, "un texto"),
    ("inicio", str, "un texto (ID de escena)"),
    ("variables", dict, "un mapa de booleanos"),
    ("escenas", list, "una lista de escenas"),
)
CAMPOS_ESCENA = (
    ("id", str, "un texto"),
    ("texto", str, "un texto"),
    ("final", bool, "un booleano"),
    ("opciones", list, "una lista"),
)
CAMPOS_OPCION = (
    ("id", str, "un texto"),
    ("texto", str, "un texto"),
    ("destino", str, "un texto (ID de escena)"),
    ("condiciones", dict, "un mapa de igualdades"),
    ("efectos", dict, "un mapa de asignaciones"),
)


def validar(datos: Any) -> List[Diagnostico]:
    """Devuelve la lista de problemas del contenido; vacía si es válido."""
    diag: List[Diagnostico] = []

    def add(codigo: str, mensaje: str, campo: str = None) -> None:
        diag.append(Diagnostico(codigo, mensaje, campo))

    if not isinstance(datos, dict):
        add(E_ESTRUCTURA, "La raíz del archivo debe ser un objeto con titulo, inicio, variables y escenas.", "(raíz)")
        return diag

    _revisar_campos(datos, CAMPOS_HISTORIA, "la historia", "", add)

    declaradas: Set[str] = set()
    if isinstance(datos.get("variables"), dict):
        for nombre, valor in datos["variables"].items():
            declaradas.add(nombre)
            if not isinstance(valor, bool):
                add(E_NO_BOOL, f"La variable '{nombre}' debe valer true o false y vale {valor!r}.",
                    f"variables.{nombre}")

    escenas = datos.get("escenas") if isinstance(datos.get("escenas"), list) else None
    ids_escena: Set[str] = set()
    if escenas is not None:
        for i, esc in enumerate(escenas):
            if isinstance(esc, dict) and isinstance(esc.get("id"), str):
                if esc["id"] in ids_escena:
                    add(E_ESCENA_DUP, f"El ID de escena '{esc['id']}' está repetido.", f"escenas[{i}].id")
                ids_escena.add(esc["id"])
        for i, esc in enumerate(escenas):
            _validar_escena(i, esc, ids_escena, declaradas, add)

    if isinstance(datos.get("inicio"), str) and escenas is not None and datos["inicio"] not in ids_escena:
        add(E_INICIO, f"La escena inicial '{datos['inicio']}' no existe entre las escenas.", "inicio")
    return diag


def _revisar_campos(obj: Dict[str, Any], campos, que: str, prefijo: str, add) -> None:
    for campo, tipo, nombre_tipo in campos:
        ruta = f"{prefijo}{campo}"
        if campo not in obj:
            add(E_CAMPO_AUSENTE, f"Falta el campo obligatorio '{campo}' de {que}.", ruta)
        elif not isinstance(obj[campo], tipo):
            add(E_ESTRUCTURA, f"El campo '{campo}' de {que} debe ser {nombre_tipo}.", ruta)


def _validar_escena(i: int, esc: Any, ids_escena: Set[str], declaradas: Set[str], add) -> None:
    if not isinstance(esc, dict):
        add(E_ESTRUCTURA, f"La escena en la posición {i} debe ser un objeto.", f"escenas[{i}]")
        return
    etiqueta = f"la escena '{esc['id']}'" if isinstance(esc.get("id"), str) else f"la escena en la posición {i}"
    ref = esc["id"] if isinstance(esc.get("id"), str) else str(i)
    _revisar_campos(esc, CAMPOS_ESCENA, etiqueta, f"escenas[{ref}].", add)

    opciones = esc.get("opciones")
    if isinstance(opciones, list) and isinstance(esc.get("final"), bool):
        if esc["final"] and len(opciones) > 0:
            add(E_FINAL_OPCIONES, f"La escena final '{ref}' debe tener cero opciones y tiene {len(opciones)}.",
                f"escenas[{ref}].opciones")
        if not esc["final"] and len(opciones) == 0:
            add(E_FINAL_OPCIONES, f"La escena no final '{ref}' debe tener al menos una opción y no tiene ninguna.",
                f"escenas[{ref}].opciones")

    if not isinstance(opciones, list):
        return
    vistos: Set[str] = set()
    for j, op in enumerate(opciones):
        if not isinstance(op, dict):
            add(E_ESTRUCTURA, f"La opción en la posición {j} de {etiqueta} debe ser un objeto.",
                f"escenas[{ref}].opciones[{j}]")
            continue
        op_ref = op["id"] if isinstance(op.get("id"), str) else str(j)
        prefijo = f"escenas[{ref}].opciones[{op_ref}]."
        et_op = f"la opción '{op_ref}' de {etiqueta}" if isinstance(op.get("id"), str) \
            else f"la opción en la posición {j} de {etiqueta}"
        _revisar_campos(op, CAMPOS_OPCION, et_op, prefijo, add)
        if isinstance(op.get("id"), str):
            if op["id"] in vistos:
                add(E_OPCION_DUP, f"El ID de opción '{op['id']}' está repetido en {etiqueta}.", prefijo + "id")
            vistos.add(op["id"])
        if isinstance(op.get("destino"), str) and op["destino"] not in ids_escena:
            add(E_DESTINO, f"{et_op[0].upper() + et_op[1:]} apunta a un destino inexistente: '{op['destino']}'.",
                prefijo + "destino")
        for mapa in ("condiciones", "efectos"):
            _validar_mapa(op.get(mapa), mapa, et_op, prefijo, declaradas, add)


def _validar_mapa(mapa: Any, nombre: str, et_op: str, prefijo: str, declaradas: Set[str], add) -> None:
    if not isinstance(mapa, dict):
        return
    for variable, valor in mapa.items():
        if variable not in declaradas:
            add(E_VARIABLE, f"En {nombre} de {et_op} se usa la variable no declarada '{variable}'.",
                f"{prefijo}{nombre}.{variable}")
        if not isinstance(valor, bool):
            add(E_NO_BOOL, f"En {nombre} de {et_op}, la variable '{variable}' debe valer true o false y vale {valor!r}.",
                f"{prefijo}{nombre}.{variable}")


def construir_historia(datos: Dict[str, Any]) -> Historia:
    """Construye el modelo de dominio. Precondición: validar(datos) == []."""
    escenas = {}
    for e in datos["escenas"]:
        opciones = tuple(
            Opcion(o["id"], o["texto"], o["destino"], dict(o["condiciones"]), dict(o["efectos"]))
            for o in e["opciones"]
        )
        escenas[e["id"]] = Escena(e["id"], e["texto"], e["final"], opciones)
    return Historia(datos["titulo"], datos["inicio"], dict(datos["variables"]), escenas)
