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
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QMessageBox,
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

        self.table = QTableWidget(len(self.servicios), 5 + len(MESES))
        headers = ['Servicio', 'Empresa', 'Cómo se paga', 'Con qué pago', 'Ir a pagar'] + [m.capitalize() for m in MESES]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for row, servicio in enumerate(self.servicios):
            self.table.setItem(row, 0, QTableWidgetItem(servicio['nombre']))
            self.table.setItem(row, 1, QTableWidgetItem(servicio['empresa']))
            self.table.setItem(row, 2, QTableWidgetItem(servicio.get('como_pagar', '')))
            self.table.setItem(row, 3, QTableWidgetItem(servicio.get('con_que_pago', '')))

            # boton ir a pagar
            btn_pago = QPushButton('Ir a pagar')
            btn_pago.setStyleSheet(self.estilo_boton_generico)
            if servicio.get('url_pago'):
                btn_pago.clicked.connect(lambda checked, url=servicio['url_pago']: webbrowser.open(url))
            else:
                btn_pago.setEnabled(False)
            self.table.setCellWidget(row, 4, btn_pago)

            for i, mes in enumerate(MESES):
                estado = servicio['pagos'].get(mes, False)
                btn_estado = QPushButton()
                self.actualizar_boton_pago(btn_estado, estado)
                btn_estado.clicked.connect(self.make_marcar_handler(row, mes, btn_estado))
                self.table.setCellWidget(row, 5 + i, btn_estado)

        layout.addWidget(self.table)
        self.agregar_info_arba(layout)

        reset_btn = QPushButton('Reset año')
        reset_btn.setStyleSheet(
            "QPushButton {background-color: red; color: white; border-radius: 4px; padding: 5px;}"
            "QPushButton:hover {background-color: #ff5555;}"
            "QPushButton:pressed {background-color: #aa0000;}"
        )
        reset_btn.clicked.connect(self.reset_anio)
        layout.addWidget(reset_btn, alignment=Qt.AlignRight)

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
            # pequeña animación o feedback visual podría agregarse aquí
        return handler

    def copiar_al_portapapeles(self, texto):
        QApplication.clipboard().setText(texto)

    def agregar_info_arba(self, layout):
        info = [
            ("Partida - Leo/Naty:", "047 - 098287"),
            ("Partida - Reina:", "110 - 004573"),
            ("Partida - Graciela:", "110 - 056763"),
            ("Partida - Silvana:", "097 - 082018"),
        ]
        layout.addWidget(QLabel("ARBA"))
        info_widget = QWidget()
        grid = QGridLayout(info_widget)
        for row, (label_text, numero) in enumerate(info):
            grid.addWidget(QLabel(label_text), row, 0)
            btn = QPushButton(numero)
            btn.setStyleSheet(self.estilo_boton_generico)
            solo_numero = numero.split('-')[-1].strip()
            btn.clicked.connect(lambda checked, n=solo_numero: self.copiar_al_portapapeles(n))
            grid.addWidget(btn, row, 1)
        layout.addWidget(info_widget)

    def reset_anio(self):
        reply = QMessageBox.question(
            self,
            'Confirmar reset',
            '¿Seguro que deseas resetear todos los pagos del año?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for row, servicio in enumerate(self.servicios):
                for mes in MESES:
                    servicio['pagos'][mes] = False
                for i, _ in enumerate(MESES):
                    btn = self.table.cellWidget(row, 5 + i)
                    if btn:
                        self.actualizar_boton_pago(btn, False)
            guardar_datos(self.servicios)

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
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
