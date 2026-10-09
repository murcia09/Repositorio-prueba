"""Folios consecutivos por serie.

La numeracion de las facturas la autoriza el fisco por rangos: un folio no se puede
repetir ni saltar. Por eso el folio se asigna en el ultimo momento de la emision, y
con un candado, para que dos cajas no reciban el mismo.
"""

from __future__ import annotations

import threading


class GeneradorFolios:
    def __init__(self, serie: str, inicial: int = 1) -> None:
        if inicial < 1:
            raise ValueError("El primer folio debe ser 1 o mayor.")
        self.serie = serie
        self._siguiente = inicial
        self._ultimo: int | None = None
        self._candado = threading.Lock()

    def siguiente(self) -> int:
        with self._candado:
            folio = self._siguiente
            self._siguiente += 1
            self._ultimo = folio
            return folio

    @property
    def ultimo_asignado(self) -> int | None:
        """El ultimo folio entregado, o None si todavia no se entrego ninguno."""
        return self._ultimo
