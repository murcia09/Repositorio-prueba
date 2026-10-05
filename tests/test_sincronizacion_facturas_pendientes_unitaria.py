import pytest

from facturacion.emision import sincronizar_facturas_pendientes


def test_sincronizar_facturas_pendientes_incluye_id_remoto_y_respeta_el_orden_de_llamadas():
    facturas = [
        {"id": "FAC-001", "cliente": "CLIENTE-1"},
        {"id": "FAC-002", "cliente": "CLIENTE-2"},
    ]
    llamadas = []

    def sincronizador(factura):
        llamadas.append(factura)
        return f"remota-{factura['id']}"

    resultado = sincronizar_facturas_pendientes(facturas, sincronizador=sincronizador)

    assert llamadas == facturas
    assert resultado == {
        "total_procesadas": 2,
        "procesadas_correctamente": [
            {"id": "FAC-001", "cliente": "CLIENTE-1", "id_remoto": "remota-FAC-001"},
            {"id": "FAC-002", "cliente": "CLIENTE-2", "id_remoto": "remota-FAC-002"},
        ],
        "fallidas": [],
    }


def test_sincronizar_facturas_pendientes_con_lista_vacia_no_llama_al_colaborador():
    llamadas = []

    def sincronizador(factura):
        llamadas.append(factura)
        raise AssertionError("no debería llamarse cuando la cola está vacía")

    resultado = sincronizar_facturas_pendientes([], sincronizador=sincronizador)

    assert llamadas == []
    assert resultado == {
        "total_procesadas": 0,
        "procesadas_correctamente": [],
        "fallidas": [],
    }


def test_sincronizar_facturas_pendientes_registra_fallos_sin_interrumpir_el_resto():
    facturas = [
        {"id": "FAC-OK", "cliente": "CLIENTE-1"},
        {"id": "FAC-ERR", "cliente": "CLIENTE-2"},
        {"id": "FAC-OK-2", "cliente": "CLIENTE-3"},
    ]
    llamadas = []

    def sincronizador(factura):
        llamadas.append(factura["id"])
        if factura["id"] == "FAC-ERR":
            raise RuntimeError("servicio no disponible")
        return f"remota-{factura['id']}"

    resultado = sincronizar_facturas_pendientes(facturas, sincronizador=sincronizador)

    assert llamadas == ["FAC-OK", "FAC-ERR", "FAC-OK-2"]
    assert resultado["total_procesadas"] == 3
    assert resultado["procesadas_correctamente"] == [
        {"id": "FAC-OK", "cliente": "CLIENTE-1", "id_remoto": "remota-FAC-OK"},
        {"id": "FAC-OK-2", "cliente": "CLIENTE-3", "id_remoto": "remota-FAC-OK-2"},
    ]
    assert len(resultado["fallidas"]) == 1
    assert resultado["fallidas"][0]["factura"] == {"id": "FAC-ERR", "cliente": "CLIENTE-2"}
    assert "servicio no disponible" in resultado["fallidas"][0]["error"]


def test_sincronizar_facturas_pendientes_rechaza_una_entrada_que_no_es_lista():
    with pytest.raises(TypeError, match="facturas_pendientes debe ser una lista"):
        sincronizar_facturas_pendientes({"id": "FAC-001"}, sincronizador=lambda _f: "x")
