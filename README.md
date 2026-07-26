# Impuestos Tracker · 2026

Aplicación de escritorio para Windows 11 que permite llevar un registro local
de servicios e impuestos pagados, mes a mes.

La edición 2026 transforma la tabla tradicional en un tablero oscuro de alto
contraste: progreso anual, foco en el mes actual, tarjetas por servicio,
confirmación sonora opcional y accesos rápidos a partidas de ARBA.

## Ejecutar

Requiere Python 3.9 o superior.

```bash
pip install -r requirements.txt
python main.py
```

## Datos y seguridad

- Los datos permanecen en `data/servicios.json` junto al ejecutable de Windows.
  El primer inicio crea ese archivo desde la plantilla incluida; las
  actualizaciones posteriores nunca sobrescriben tus pagos.
- Cada cambio se guarda en el momento.
- Antes de guardar se crea `data/servicios.json.bak`.
- El archivo se reemplaza de manera atómica para evitar archivos JSON truncados.

La app no necesita conexión para funcionar; solo se abre el navegador al usar
un enlace de pago configurado.
