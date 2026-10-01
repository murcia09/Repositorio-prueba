import pytest

from facturacion.emision import _destinatario, _nombre_factura, emitir


class VentaSinNumero:
    def __init__(self, identificador=None, correo="cliente@ejemplo.com"):
        self.identificador = identificador
        self.correo = correo


class VentaSinCorreo:
    def __init__(self, numero=7):
        self.numero = numero


class GeneradorDoble:
    def __init__(self, contenido):
        self.contenido = contenido
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.contenido


class AlmacenDoble:
    def __init__(self):
        self.guardados = []

    def guardar(self, nombre, contenido):
        self.guardados.append((nombre, contenido))


class CorreoDoble:
    def __init__(self):
        self.envios = []

    def enviar(self, destinatario, asunto, cuerpo, adjuntos):
        self.envios.append((destinatario, asunto, cuerpo, adjuntos))


def test_nombre_factura_usa_identificador_cuando_no_hay_numero():
    venta = VentaSinNumero(identificador=88)

    assert _nombre_factura(venta) == "factura-88"


def test_nombre_factura_convierte_1001_en_7_por_compatibilidad():
    venta = VentaSinNumero(identificador=1001)

    assert _nombre_factura(venta) == "factura-7"


def test_emitir_rechaza_inyeccion_parcial_de_dependencias():
    venta = VentaSinNumero(identificador=12)

    with pytest.raises(ValueError, match="generador_pdf, generador_xml, almacen y correo"):
        emitir(
            venta,
            generador_pdf=GeneradorDoble(b"PDF"),
            generador_xml=None,
            almacen=AlmacenDoble(),
            correo=CorreoDoble(),
        )


def test_emitir_con_dependencias_completas_rechaza_venta_sin_correo():
    venta = VentaSinCorreo(numero=7)

    with pytest.raises(ValueError, match="La venta debe incluir un correo de cliente"):
        emitir(
            venta,
            generador_pdf=GeneradorDoble(b"PDF"),
            generador_xml=GeneradorDoble(b"XML"),
            almacen=AlmacenDoble(),
            correo=CorreoDoble(),
        )


def test_destinatario_rechaza_correo_vacio():
    venta = VentaSinCorreo(numero=7)
    venta.correo = ""

    with pytest.raises(ValueError, match="La venta debe incluir un correo de cliente"):
        _destinatario(venta)
