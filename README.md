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

## Compilación

Para generar una versión portable se recomienda crear un directorio con el ejecutable y la carpeta `data`.
Un ejemplo de comando es:

```bash
pyinstaller --noconsole main.py
```

Luego, comprime la carpeta `dist/main` junto con `data/` y distribuye ese archivo `.zip`. Así se incluyen todos los recursos necesarios para que la aplicación funcione sin instalar nada.

Los datos se almacenan en `data/servicios.json` y se realiza un backup automático `servicios.json.bak` al guardar.
