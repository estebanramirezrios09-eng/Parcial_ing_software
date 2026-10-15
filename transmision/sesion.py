"""Sesión de juego: estado de una partida (RF-05 a RF-08, RF-14, RF-15, RF-19)."""
from typing import Dict, List, Optional, Tuple

from .modelos import Escena, Historia, Opcion
from .reglas import aplicar_efectos, opcion_habilitada


class OpcionNoDisponible(Exception):
    """La opción pedida no existe o no está habilitada. El estado no cambia."""


class SinRetroceso(Exception):
    """No hay una elección que deshacer (RF-19). El estado no cambia."""


class Sesion:
    def __init__(self, historia: Historia):
        self._historia = historia
        self.reiniciar()

    # --- consulta -------------------------------------------------------
    @property
    def historia(self) -> Historia:
        return self._historia

    @property
    def escena(self) -> Escena:
        return self._historia.escena(self._escena_id)

    @property
    def variables(self) -> Dict[str, bool]:
        return dict(self._variables)

    @property
    def historial(self) -> List[Tuple[str, str]]:
        """Pares (escena, opción) elegidos en esta partida."""
        return list(self._historial)

    @property
    def puede_deshacer(self) -> bool:
        """Hay una última elección válida que deshacer (un solo nivel, RF-19)."""
        return self._previo is not None

    @property
    def es_final(self) -> bool:
        return self.escena.final

    def opciones_disponibles(self) -> List[Opcion]:
        return [o for o in self.escena.opciones if opcion_habilitada(o, self._variables)]

    @property
    def bloqueada(self) -> bool:
        """Escena no final sin ninguna opción habilitada (RF-14)."""
        return not self.es_final and not self.opciones_disponibles()

    # --- acciones -------------------------------------------------------
    def elegir(self, opcion_id: str) -> Escena:
        """Aplica efectos y avanza. Si algo falla, no modifica el estado."""
        if self.es_final:
            raise OpcionNoDisponible(f"La escena '{self.escena.id}' es un final: no admite elecciones.")
        opcion = next((o for o in self.escena.opciones if o.id == opcion_id), None) \
            if isinstance(opcion_id, str) else None
        if opcion is None:
            raise OpcionNoDisponible(f"La opción {opcion_id!r} no existe en la escena '{self.escena.id}'.")
        if not opcion_habilitada(opcion, self._variables):
            raise OpcionNoDisponible(
                f"La opción '{opcion.id}' no está disponible con el estado actual de la partida.")
        nuevas = aplicar_efectos(self._variables, opcion.efectos)
        # Instantánea previa a la elección válida: solo se guarda cuando todo salió bien (RF-19)
        self._previo = (self._escena_id, dict(self._variables), list(self._historial))
        self._historial.append((self._escena_id, opcion.id))
        self._variables = nuevas
        self._escena_id = opcion.destino
        return self.escena

    def deshacer(self) -> Escena:
        """Restaura escena, variables e historial previos a la última elección válida (RF-19).

        Un solo nivel: tras deshacer no hay otro retroceso hasta una nueva elección válida.
        Si no hay nada que deshacer, lanza SinRetroceso sin modificar el estado."""
        if self._previo is None:
            raise SinRetroceso("No hay ninguna elección que deshacer.")
        self._escena_id, self._variables, self._historial = self._previo
        self._previo = None
        return self.escena

    def reiniciar(self) -> None:
        """Nueva partida: escena y variables iniciales, sin rastro de la anterior (RF-15)."""
        self._escena_id = self._historia.inicio
        self._variables = dict(self._historia.variables)
        self._historial = []
        self._previo: Optional[Tuple[str, Dict[str, bool], List[Tuple[str, str]]]] = None
