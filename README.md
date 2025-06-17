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

## Compilación a EXE

```bash
pyinstaller --onefile --noconsole main.py
```

Los datos se almacenan en `data/servicios.json` y se realiza un backup automático `servicios.json.bak` al guardar.
