"""Motor de historias interactivas «La última transmisión».

Paquete organizado en capas (ver docs/informe.pdf, sección Arquitectura):

- modelos / reglas      -> dominio (sin entrada/salida)
- diagnostico / validador / cargador -> contenido (lectura y validación)
- sesion                -> estado de una partida
- consola               -> interfaz de usuario
"""
from .cargador import HistoriaInvalida, cargar_archivo, cargar_desde_texto
from .modelos import Escena, Historia, Opcion
from .sesion import OpcionNoDisponible, Sesion, SinRetroceso

__version__ = "1.1.0"

__all__ = [
    "Escena",
    "Historia",
    "HistoriaInvalida",
    "Opcion",
    "OpcionNoDisponible",
    "Sesion",
    "SinRetroceso",
    "cargar_archivo",
    "cargar_desde_texto",
]
