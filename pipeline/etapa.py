"""Clase base para las etapas del pipeline."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .contexto import ContextoPipeline

Entrada = TypeVar("Entrada")
Salida = TypeVar("Salida")

#Clase base abstracta: toda etapa recibe una entrada y entrega una salida
class EtapaPipeline(ABC, Generic[Entrada, Salida]):
    """Interfaz genérica para etapas que transforman una entrada en una salida."""

    # Método obligatorio que cada etapa debe implementar 
    @abstractmethod
    def ejecutar(self, entrada: Entrada, contexto: ContextoPipeline) -> Salida:
        """Procesa una entrada de dominio usando la configuración de ejecución."""
        pass
