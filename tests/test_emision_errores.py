import pytest

from facturacion.emision import emitir


def test_emitir_con_objeto_no_diccionario_lanza_typeerror():
    with pytest.raises(TypeError, match="venta debe ser un diccionario"):
        emitir(None)


@pytest.mark.parametrize("venta", [{}, {"otro": "valor"}])
def test_emitir_sin_venta_id_lanza_keyerror(venta):
    with pytest.raises(KeyError):
        emitir(venta)


@pytest.mark.parametrize(
    "venta_id",
    ["", "   ", 0, None],
)
def test_emitir_con_venta_id_invalido_lanza_valueerror(venta_id):
    with pytest.raises(ValueError, match="venta_id debe ser una cadena no vacía"):
        emitir({"venta_id": venta_id})
