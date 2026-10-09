import pytest

from facturacion.errores import ClienteInvalido, TokenInvalido
from facturacion.modelos import Cliente
from facturacion.seguridad.autenticacion import Autenticador, Usuario
from facturacion.utilidades.validaciones import digito_verificacion, validar_correo, validar_nit


def test_nit_con_y_sin_digito_de_verificacion():
    assert digito_verificacion("900123456") == 8
    assert validar_nit("900123456-8")
    assert not validar_nit("900123456-1")
    assert validar_nit("900.123.456")
    assert not validar_nit("12AB")


def test_correo():
    assert validar_correo("ana@example.com")
    assert not validar_correo("ana@")


def test_registrar_rechaza_datos_invalidos(app):
    with pytest.raises(ClienteInvalido, match="NIT"):
        app.clientes.registrar(Cliente("c9", "Mal NIT", "123"))
    with pytest.raises(ClienteInvalido, match="Ya existe"):
        app.clientes.registrar(Cliente("c1", "Repetido", "1032456789"))


def test_buscar_por_nit_y_actualizar_correo(app):
    assert app.clientes.buscar_por_nit("900123456-8").id == "c2"
    assert app.clientes.actualizar_correo("c2", "compras@andina.example").correo == "compras@andina.example"


def test_token_bearer():
    auth = Autenticador()
    usuario = Usuario("u1", "Carlos", frozenset({"cajero"}))
    token = auth.emitir_token(usuario)
    assert auth.validar(f"Bearer {token}") == usuario
    auth.revocar(token)
    with pytest.raises(TokenInvalido):
        auth.validar(f"Bearer {token}")
    with pytest.raises(TokenInvalido):
        auth.validar("Basic abc")
