import json
import os
import sys
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

DATA_FILE = os.path.join('data', 'servicios.json')
BACKUP_FILE = os.path.join('data', 'servicios.json.bak')

MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]


def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def guardar_datos(data):
    if os.path.exists(DATA_FILE):
        # Backup simple
        with open(DATA_FILE, 'rb') as fsrc, open(BACKUP_FILE, 'wb') as fdst:
            fdst.write(fsrc.read())
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pagos de Servicios e Impuestos')
        self.resize(1600, 600)
        self.servicios = cargar_datos()
        self.estilo_boton_generico = (
            "QPushButton {background-color: #2d2d2d; color: white; border: 1px solid #666; border-radius: 4px; padding: 5px;}"
            "QPushButton:hover {background-color: #444444;}"
            "QPushButton:pressed {background-color: #555555;}"
        )
        self.estilo_pagado = (
            "QPushButton {background-color: #2ecc71; color: black; border-radius: 4px; padding: 5px;}"
            "QPushButton:hover {background-color: #3eea85;}"
            "QPushButton:pressed {background-color: #1fa05a;}"
        )
        self.estilo_no_pagado = (
            "QPushButton {background-color: #555555; color: white; border-radius: 4px; padding: 5px;}"
            "QPushButton:hover {background-color: #777777;}"
            "QPushButton:pressed {background-color: #333333;}"
        )
        self.init_ui()

    def init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.table = QTableWidget(len(self.servicios), 4 + len(MESES))
        headers = ['Servicio', 'Empresa', 'Medio de pago', 'Ir a pagar'] + [m.capitalize() for m in MESES]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for row, servicio in enumerate(self.servicios):
            self.table.setItem(row, 0, QTableWidgetItem(servicio['nombre']))
            self.table.setItem(row, 1, QTableWidgetItem(servicio['empresa']))
            self.table.setItem(row, 2, QTableWidgetItem(servicio['metodo_pago']))

            # boton ir a pagar
            btn_pago = QPushButton('Ir a pagar')
            btn_pago.setStyleSheet(self.estilo_boton_generico)
            if servicio.get('url_pago'):
                btn_pago.clicked.connect(lambda checked, url=servicio['url_pago']: webbrowser.open(url))
            else:
                btn_pago.setEnabled(False)
            self.table.setCellWidget(row, 3, btn_pago)

            for i, mes in enumerate(MESES):
                estado = servicio['pagos'].get(mes, False)
                btn_estado = QPushButton()
                self.actualizar_boton_pago(btn_estado, estado)
                btn_estado.clicked.connect(self.make_marcar_handler(row, mes, btn_estado))
                self.table.setCellWidget(row, 4 + i, btn_estado)

        layout.addWidget(self.table)
        self.setCentralWidget(widget)
        self.aplicar_modo_oscuro()

    def actualizar_boton_pago(self, boton, estado):
        if estado:
            boton.setText('Pagado')
            boton.setStyleSheet(self.estilo_pagado)
        else:
            boton.setText('No pagué')
            boton.setStyleSheet(self.estilo_no_pagado)

    def make_marcar_handler(self, row, mes, button):
        def handler():
            servicio = self.servicios[row]
            nuevo_estado = not servicio['pagos'].get(mes, False)
            servicio['pagos'][mes] = nuevo_estado
            guardar_datos(self.servicios)
            self.actualizar_boton_pago(button, nuevo_estado)
            if nuevo_estado:
                QMessageBox.information(
                    self,
                    'Pago registrado',
                    f"¡Bien ahí, maestro! Ya pagaste {servicio['nombre']} de {mes}.")
        return handler

    def aplicar_modo_oscuro(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)


def main():
    app = QApplication(sys.argv)
    font = QFont('Segoe UI', 11)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
