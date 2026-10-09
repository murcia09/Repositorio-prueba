# Facturación de punto de venta

Sistema de facturación electrónica para una tienda: el cajero arma el carrito, factura (se emite y se timbra ante el servicio de impuestos) y cobra. También maneja clientes, inventario, anulaciones, notas crédito, devoluciones, promociones, turnos de caja, compras a proveedores, puntos de fidelización, reportes y exportación contable.

Es un **proyecto de práctica** de la plataforma SDLC + Agentes: sirve para probar el bloque de desarrollo sobre un repositorio lo bastante grande como para que no quepa entero en el contexto de un agente.

## Estructura

```
facturacion/
├── api/              lo que usan las personas: la caja y las consultas
├── servicios/        reglas de negocio, una operación por módulo
├── documentos/       el XML que se timbra y el PDF que se entrega
├── integraciones/    servicio de impuestos, correo, contabilidad y catálogo
├── repositorios/     almacenamiento (en memoria; en producción, base de datos)
├── seguridad/        tokens Bearer y roles
├── utilidades/       dinero, fechas, validaciones y cronómetro
├── aplicacion.py     crea y conecta todos los servicios
├── config.py         configuración desde variables FACTURACION_*
├── errores.py        errores del dominio
└── modelos.py        clientes, productos, facturas, pagos y notas crédito
tests/                pruebas con pytest
```

## Cómo se prueba

```bash
pip install -r requirements.txt
python -m pytest -q
```

No necesita ningún servicio externo: el servicio de impuestos y el correo están simulados (`integraciones/`), con latencia y fallos configurables.

## Reglas que conviene conocer

- El dinero siempre es `Decimal`, redondeado a centavos línea por línea (`utilidades/dinero.py`).
- Una factura pasa por `borrador → emitida → timbrada → pagada`, o `anulada`. Solo se cobra una factura timbrada.
- El folio se asigna al emitir y nunca se repite ni se salta (`servicios/numeracion.py`).
- Toda operación queda en la auditoría (`servicios/auditoria.py`).
