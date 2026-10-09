"""Autenticacion con tokens Bearer emitidos por el proveedor de identidad.

En produccion el token lo emite el proveedor OAuth2/OIDC y se valida su firma.
Aqui se simula con un registro de tokens emitidos, suficiente para probar los
permisos de cada rol.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from facturacion.errores import PermisoDenegado, TokenInvalido

ROLES = ("cajero", "supervisor", "contador")


@dataclass(frozen=True)
class Usuario:
    id: str
    nombre: str
    roles: frozenset[str]

    def tiene_rol(self, rol: str) -> bool:
        return rol in self.roles


class Autenticador:
    def __init__(self) -> None:
        self._tokens: dict[str, Usuario] = {}

    def emitir_token(self, usuario: Usuario) -> str:
        desconocidos = set(usuario.roles) - set(ROLES)
        if desconocidos:
            raise PermisoDenegado(f"Roles desconocidos: {sorted(desconocidos)}.")
        token = secrets.token_urlsafe(24)
        self._tokens[token] = usuario
        return token

    def validar(self, cabecera: str | None) -> Usuario:
        """Recibe la cabecera `Authorization` completa: `Bearer <token>`."""
        esquema, _, token = (cabecera or "").partition(" ")
        if esquema.lower() != "bearer" or not token:
            raise TokenInvalido("Se esperaba una cabecera 'Bearer <token>'.")
        usuario = self._tokens.get(token)
        if usuario is None:
            raise TokenInvalido("El token no es valido o ya expiro.")
        return usuario

    def revocar(self, token: str) -> None:
        self._tokens.pop(token, None)


def exigir_rol(usuario: Usuario, *roles: str) -> None:
    """Levanta PermisoDenegado si el usuario no tiene ninguno de los roles."""
    if not any(usuario.tiene_rol(rol) for rol in roles):
        raise PermisoDenegado(
            f"{usuario.nombre} no tiene permiso: hace falta el rol {' o '.join(roles)}."
        )
