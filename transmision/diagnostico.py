"""Diagnósticos de validación: cada error de contenido tiene código, causa y campo."""
from dataclasses import dataclass
from typing import Optional

E_ILEGIBLE = "E_ILEGIBLE"            # archivo ilegible o no es JSON
E_ESTRUCTURA = "E_ESTRUCTURA"        # tipo de dato incorrecto
E_CAMPO_AUSENTE = "E_CAMPO_AUSENTE"  # campo obligatorio ausente
E_INICIO = "E_INICIO"                # escena inicial inexistente
E_ESCENA_DUP = "E_ESCENA_DUP"        # ID de escena repetido
E_OPCION_DUP = "E_OPCION_DUP"        # ID de opción repetido dentro de su escena
E_DESTINO = "E_DESTINO"              # destino inexistente
E_VARIABLE = "E_VARIABLE"            # variable no declarada
E_NO_BOOL = "E_NO_BOOL"              # valor no booleano
E_FINAL_OPCIONES = "E_FINAL_OPCIONES"  # cantidad de opciones incompatible con 'final'

CODIGOS = (
    E_ILEGIBLE, E_ESTRUCTURA, E_CAMPO_AUSENTE, E_INICIO, E_ESCENA_DUP,
    E_OPCION_DUP, E_DESTINO, E_VARIABLE, E_NO_BOOL, E_FINAL_OPCIONES,
)


@dataclass(frozen=True)
class Diagnostico:
    codigo: str
    mensaje: str
    campo: Optional[str] = None

    def __str__(self) -> str:
        ubicacion = f" (campo: {self.campo})" if self.campo else ""
        return f"[{self.codigo}] {self.mensaje}{ubicacion}"
