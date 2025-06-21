# ImpuestosPagosTracker

Aplicación de escritorio en Python para llevar el control mensual de tus servicios e impuestos.

## Requisitos

- Python 3.9+
- Dependencias en `requirements.txt`

Instalación de dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Empaquetado

La aplicación se distribuye en un archivo `.zip` que contiene todo el código y la carpeta `data`.
Solo necesitas descomprimir ese archivo y ejecutar `python main.py` dentro de la carpeta resultante.
El empaquetado se genera automáticamente mediante GitHub Actions.

Los datos se almacenan en `data/servicios.json` y se realiza un backup automático `servicios.json.bak` al guardar.
