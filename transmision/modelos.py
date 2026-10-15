"""Modelo de dominio: una historia es un grafo de escenas con opciones."""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Opcion:
    id: str
    texto: str
    destino: str
    condiciones: Dict[str, bool]
    efectos: Dict[str, bool]


@dataclass(frozen=True)
class Escena:
    id: str
    texto: str
    final: bool
    opciones: Tuple[Opcion, ...]


@dataclass(frozen=True)
class Historia:
    titulo: str
    inicio: str
    variables: Dict[str, bool]
    escenas: Dict[str, Escena]

    def escena(self, escena_id: str) -> Escena:
        return self.escenas[escena_id]
