"""Mide cuanto tarda una operacion, en milisegundos.

Lo usa la caja para registrar cuanto tarda facturar desde que el cajero pulsa el
boton, que es lo que el negocio mide.
"""

from __future__ import annotations

import time


class Cronometro:
    """Uso: `with Cronometro() as reloj: ...` y despues `reloj.milisegundos`."""

    def __init__(self) -> None:
        self._inicio: float | None = None
        self._fin: float | None = None

    def __enter__(self) -> "Cronometro":
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._fin = time.perf_counter()

    @property
    def milisegundos(self) -> float:
        """Lo transcurrido; si sigue en marcha, hasta ahora."""
        if self._inicio is None:
            return 0.0
        fin = self._fin if self._fin is not None else time.perf_counter()
        return (fin - self._inicio) * 1000
