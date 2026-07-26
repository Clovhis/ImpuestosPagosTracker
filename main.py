"""Impuestos Tracker 2026.

Tablero local para registrar pagos mensuales. Los datos siguen siendo el mismo
JSON portable de las versiones anteriores; esta versión solo moderniza la
experiencia y endurece el guardado para que sea más difícil perder cambios.
"""

import json
import os
import shutil
import sys
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


APP_DIR = os.path.dirname(os.path.abspath(__file__))


def resolver_rutas_datos():
    """Devuelve los archivos de datos y la plantilla incluida en el ejecutable.

    PyInstaller extrae los recursos de un ejecutable ``--onefile`` a una carpeta
    temporal (``_MEIPASS``). Esa carpeta desaparece al cerrar la app, por lo que
    nunca debe usarse para guardar datos del usuario. En el ejecutable se guarda
    junto a él; durante desarrollo se conserva la carpeta ``data`` del repo.
    """
    if getattr(sys, "frozen", False):
        resource_dir = getattr(sys, "_MEIPASS", APP_DIR)
        writable_dir = os.path.dirname(sys.executable)
    else:
        resource_dir = APP_DIR
        writable_dir = APP_DIR
    source = os.path.join(resource_dir, "data", "servicios.json")
    destination_dir = os.path.join(writable_dir, "data")
    destination = os.path.join(destination_dir, "servicios.json")
    return destination, os.path.join(destination_dir, "servicios.json.bak"), source


DATA_FILE, BACKUP_FILE, SEED_DATA_FILE = resolver_rutas_datos()

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_CORTOS = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
ICONS = {
    "Gas": "♨",
    "Luz": "ϟ",
    "Agua": "≈",
    "Cable / Internet / Celular": "◉",
    "Renta": "⌂",
    "Aseo y Limpieza": "✦",
}


def cargar_datos():
    """Carga y normaliza datos de instalaciones de versiones anteriores."""
    if not os.path.exists(DATA_FILE):
        # En el primer inicio del .exe, usa la plantilla incluida por PyInstaller.
        # Nunca pisa un archivo existente: las actualizaciones preservan tus pagos.
        if not os.path.exists(SEED_DATA_FILE):
            return []
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        shutil.copy2(SEED_DATA_FILE, DATA_FILE)
    with open(DATA_FILE, "r", encoding="utf-8") as archivo:
        servicios = json.load(archivo)
    for servicio in servicios:
        pagos = servicio.setdefault("pagos", {})
        for mes in MESES:
            pagos.setdefault(mes, False)
    return servicios


def guardar_datos(data):
    """Crea un backup y reemplaza el archivo de forma atómica."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as origen, open(BACKUP_FILE, "wb") as destino:
            destino.write(origen.read())
    temporal = f"{DATA_FILE}.tmp"
    with open(temporal, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)
    os.replace(temporal, DATA_FILE)


class ProgressRing(QWidget):
    """Indicador de progreso anual, pintado sin depender de assets externos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setFixedSize(104, 104)

    def set_value(self, value):
        self.value = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        pen = QPen(QColor("#29354A"), 9, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        pen.setColor(QColor("#6EE7B7"))
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -int(360 * 16 * self.value / 100))
        painter.setPen(QColor("#F7F8FC"))
        painter.setFont(QFont("Segoe UI", 17, QFont.DemiBold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%")


class Toast(QLabel):
    """Mensaje breve, discreto y no bloqueante para confirmaciones."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.setVisible(False)

    def show_message(self, message):
        self.setText(message)
        self.adjustSize()
        self.move(self.parent().width() - self.width() - 30, 28)
        self.show()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2400, self.hide)


class MonthButton(QPushButton):
    """Botón compacto y explícito: símbolo + texto, no solo color."""

    toggled_payment = Signal(str, bool)

    def __init__(self, month, active_month, paid, parent=None):
        super().__init__(parent)
        self.month = month
        self.active_month = active_month
        self.paid = paid
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(QSize(55, 48))
        self.clicked.connect(self.toggle)
        self.refresh()

    def toggle(self):
        self.paid = not self.paid
        self.refresh()
        self.toggled_payment.emit(self.month, self.paid)

    def refresh(self):
        label = MESES_CORTOS[MESES.index(self.month)]
        if self.paid:
            self.setText(f"✓\n{label}")
            background, border, foreground = "#164F47", "#48D3A7", "#D9FFF1"
            status = "Pagado"
        elif self.month == self.active_month:
            self.setText(f"•\n{label}")
            background, border, foreground = "#352B68", "#9B8CFF", "#F2F0FF"
            status = "Pendiente este mes"
        else:
            self.setText(label)
            background, border, foreground = "#1A2332", "#2B3A50", "#98A7BD"
            status = "Pendiente"
        self.setToolTip(f"{self.month.capitalize()}: {status}. Hacé clic para cambiarlo.")
        self.setStyleSheet(
            "QPushButton {"
            f"background: {background}; color: {foreground}; border: 1px solid {border};"
            "border-radius: 12px; font-size: 10px; font-weight: 700; padding: 2px;"
            "} QPushButton:hover { border: 2px solid #E7E2FF; }"
            "QPushButton:focus { border: 2px solid #FFFFFF; }"
            "QPushButton:pressed { background: #5B4DB1; }"
        )


class ServiceCard(QFrame):
    changed = Signal()

    def __init__(self, service, current_month, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_month = current_month
        self.month_buttons = {}
        self.setObjectName("serviceCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.build()

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        icon = QLabel(ICONS.get(self.service["nombre"], "●"))
        icon.setObjectName("serviceIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(42, 42)
        header.addWidget(icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel(self.service["nombre"])
        title.setObjectName("serviceTitle")
        company = QLabel(self.service.get("empresa", ""))
        company.setObjectName("serviceCompany")
        title_box.addWidget(title)
        title_box.addWidget(company)
        header.addLayout(title_box)
        header.addStretch()

        self.counter = QLabel()
        self.counter.setObjectName("serviceCounter")
        header.addWidget(self.counter)

        pay = QPushButton("Abrir pago")
        pay.setObjectName("payButton")
        pay.setCursor(Qt.PointingHandCursor)
        pay.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        pay.setEnabled(bool(self.service.get("url_pago")))
        pay.setToolTip("Abrir la página de pago" if pay.isEnabled() else "No hay un enlace de pago configurado")
        if pay.isEnabled():
            pay.clicked.connect(lambda: webbrowser.open(self.service["url_pago"]))
        header.addWidget(pay)
        layout.addLayout(header)

        details = QLabel(
            f"<b>Cómo se paga</b>  {self.service.get('como_pagar', 'Sin detalle')}"
            f"<span style='color:#43536c'>   ·   </span>"
            f"<b>Medio</b>  {self.service.get('con_que_pago', 'Sin detalle')}"
        )
        details.setObjectName("serviceDetails")
        details.setWordWrap(True)
        layout.addWidget(details)

        months = QHBoxLayout()
        months.setSpacing(7)
        for month in MESES:
            button = MonthButton(month, self.current_month, self.service["pagos"].get(month, False))
            button.toggled_payment.connect(self.on_month_toggled)
            self.month_buttons[month] = button
            months.addWidget(button)
        months.addStretch()
        layout.addLayout(months)
        self.refresh_counter()

    def on_month_toggled(self, month, paid):
        self.service["pagos"][month] = paid
        self.refresh_counter()
        self.changed.emit()

    def refresh_counter(self):
        paid = sum(self.service["pagos"].values())
        self.counter.setText(f"{paid} de 12 pagados")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.servicios = cargar_datos()
        self.current_month = MESES[datetime.now().month - 1]
        self.sound_on = True
        self.setWindowTitle("Impuestos Tracker · 2026")
        self.setMinimumSize(1060, 720)
        self.resize(1440, 900)
        self.apply_theme()
        self.build()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0B0F16; color: #F7F8FC; font-family: 'Segoe UI'; }
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: #0B0F16; }
            QScrollBar:vertical { background: transparent; width: 10px; margin: 6px; }
            QScrollBar::handle:vertical { background: #344157; min-height: 40px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QLabel#eyebrow { color: #9B8CFF; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel#pageTitle { font-size: 30px; font-weight: 700; letter-spacing: -0.5px; }
            QLabel#pageSubtitle { color: #96A3B7; font-size: 14px; }
            QFrame#summaryCard, QFrame#serviceCard, QFrame#arbaCard { background: #121824; border: 1px solid #243148; border-radius: 20px; }
            QLabel#statValue { font-size: 28px; font-weight: 700; }
            QLabel#statLabel, QLabel#serviceCompany { color: #96A3B7; font-size: 12px; }
            QLabel#statDetail { color: #6EE7B7; font-size: 12px; font-weight: 600; }
            QLabel#sectionTitle { font-size: 18px; font-weight: 700; }
            QLabel#sectionHint { color: #96A3B7; font-size: 13px; }
            QLabel#serviceIcon { background: #26204A; color: #C4BBFF; border-radius: 14px; font-size: 21px; font-weight: 700; }
            QLabel#serviceTitle { font-size: 17px; font-weight: 700; }
            QLabel#serviceCounter { background: #1B2638; color: #B9C6D9; border-radius: 11px; padding: 6px 10px; font-size: 11px; font-weight: 600; }
            QLabel#serviceDetails { color: #AEB9C9; font-size: 12px; padding: 9px 11px; background: #0E141F; border-radius: 10px; }
            QPushButton#payButton { background: #7868E6; color: white; border: none; border-radius: 11px; padding: 9px 13px; font-weight: 700; }
            QPushButton#payButton:hover { background: #9385F4; } QPushButton#payButton:disabled { background: #222C3D; color: #66758C; }
            QPushButton#quietButton, QToolButton#soundButton { background: #1A2332; color: #DCE4F2; border: 1px solid #30405A; border-radius: 11px; padding: 9px 12px; font-weight: 600; }
            QPushButton#quietButton:hover, QToolButton#soundButton:hover { background: #26334A; border-color: #A99EFF; }
            QPushButton#dangerButton { background: transparent; color: #F3A0A9; border: 1px solid #713944; border-radius: 10px; padding: 9px 13px; font-weight: 600; }
            QPushButton#dangerButton:hover { background: #3A1D27; }
            QLabel#toast { background: #E5FFF3; color: #153D31; border-radius: 12px; padding: 10px 14px; font-weight: 700; }
        """)

    def build(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(32, 26, 32, 28)
        root.setSpacing(20)

        root.addLayout(self.build_header())
        root.addLayout(self.build_summary())

        section = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("Tu calendario de pagos")
        title.setObjectName("sectionTitle")
        hint = QLabel("Marcá cada mes al pagar. Los cambios se guardan al instante en tu PC.")
        hint.setObjectName("sectionHint")
        title_block.addWidget(title)
        title_block.addWidget(hint)
        section.addLayout(title_block)
        section.addStretch()
        reset = QPushButton("Reiniciar el año")
        reset.setObjectName("dangerButton")
        reset.setCursor(Qt.PointingHandCursor)
        reset.clicked.connect(self.reset_year)
        section.addWidget(reset)
        root.addLayout(section)

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        for service in self.servicios:
            card = ServiceCard(service, self.current_month)
            card.changed.connect(self.on_payment_changed)
            self.cards_layout.addWidget(card)
        root.addLayout(self.cards_layout)
        root.addWidget(self.build_arba_card())
        root.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)
        self.toast = Toast(self)
        self.refresh_dashboard()

    def build_header(self):
        layout = QHBoxLayout()
        copy = QVBoxLayout()
        copy.setSpacing(3)
        eyebrow = QLabel("FINANZAS DEL HOGAR · 2026")
        eyebrow.setObjectName("eyebrow")
        heading = QLabel("Impuestos, bajo control.")
        heading.setObjectName("pageTitle")
        date = datetime.now().strftime("%d/%m/%Y")
        subtitle = QLabel(f"Hoy es {date}. El foco está en {self.current_month.capitalize()}.")
        subtitle.setObjectName("pageSubtitle")
        copy.addWidget(eyebrow)
        copy.addWidget(heading)
        copy.addWidget(subtitle)
        layout.addLayout(copy)
        layout.addStretch()
        self.sound_button = QToolButton()
        self.sound_button.setObjectName("soundButton")
        self.sound_button.setCursor(Qt.PointingHandCursor)
        self.sound_button.clicked.connect(self.toggle_sound)
        self.update_sound_button()
        layout.addWidget(self.sound_button)
        return layout

    def build_summary(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        completion = QFrame()
        completion.setObjectName("summaryCard")
        completion_layout = QHBoxLayout(completion)
        completion_layout.setContentsMargins(18, 14, 18, 14)
        self.progress_ring = ProgressRing()
        completion_layout.addWidget(self.progress_ring)
        summary_text = QVBoxLayout()
        annual = QLabel("PROGRESO ANUAL")
        annual.setObjectName("eyebrow")
        self.annual_value = QLabel()
        self.annual_value.setObjectName("statValue")
        self.annual_detail = QLabel()
        self.annual_detail.setObjectName("statDetail")
        summary_text.addWidget(annual)
        summary_text.addWidget(self.annual_value)
        summary_text.addWidget(self.annual_detail)
        summary_text.addStretch()
        completion_layout.addLayout(summary_text)
        layout.addWidget(completion, 2)

        self.month_stat = self.summary_stat("ESTE MES", "", "")
        self.pending_stat = self.summary_stat("POR HACER", "", "")
        layout.addWidget(self.month_stat, 1)
        layout.addWidget(self.pending_stat, 1)
        return layout

    def summary_stat(self, label, value, detail):
        card = QFrame()
        card.setObjectName("summaryCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        label_widget = QLabel(label)
        label_widget.setObjectName("eyebrow")
        value_widget = QLabel(value)
        value_widget.setObjectName("statValue")
        detail_widget = QLabel(detail)
        detail_widget.setObjectName("statLabel")
        card_layout.addWidget(label_widget)
        card_layout.addWidget(value_widget)
        card_layout.addWidget(detail_widget)
        card.value_widget = value_widget
        card.detail_widget = detail_widget
        return card

    def build_arba_card(self):
        card = QFrame()
        card.setObjectName("arbaCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        title = QLabel("Datos rápidos · ARBA")
        title.setObjectName("sectionTitle")
        description = QLabel("Copiá una partida con un clic para pegarla en el portal de pago.")
        description.setObjectName("sectionHint")
        layout.addWidget(title)
        layout.addWidget(description)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        data = [
            ("Partida · Leo / Naty", "047 - 098287"),
            ("Partida · Reina", "110 - 004573"),
            ("Partida · Graciela", "110 - 056763"),
            ("Partida · Silvana", "097 - 082018"),
        ]
        for row, (label, number) in enumerate(data):
            key = QLabel(label)
            key.setObjectName("serviceCompany")
            button = QPushButton(number)
            button.setObjectName("quietButton")
            button.setCursor(Qt.PointingHandCursor)
            only_number = number.split("-")[-1].strip()
            button.clicked.connect(lambda checked=False, text=only_number, name=label: self.copy_reference(text, name))
            grid.addWidget(key, row, 0)
            grid.addWidget(button, row, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return card

    def refresh_dashboard(self):
        total_slots = len(self.servicios) * len(MESES)
        paid_total = sum(sum(service["pagos"].values()) for service in self.servicios)
        paid_current = sum(service["pagos"].get(self.current_month, False) for service in self.servicios)
        pending_current = len(self.servicios) - paid_current
        percentage = round(100 * paid_total / total_slots) if total_slots else 0
        self.progress_ring.set_value(percentage)
        self.annual_value.setText(f"{paid_total} de {total_slots}")
        self.annual_detail.setText(f"{percentage}% del año registrado")
        self.month_stat.value_widget.setText(f"{paid_current} / {len(self.servicios)}")
        self.month_stat.detail_widget.setText(f"pagos de {self.current_month.capitalize()}")
        self.pending_stat.value_widget.setText(str(pending_current))
        self.pending_stat.detail_widget.setText("servicios pendientes este mes")

    def on_payment_changed(self):
        try:
            guardar_datos(self.servicios)
        except OSError as error:
            QMessageBox.critical(
                self,
                "No se pudo guardar",
                f"No se pudo actualizar el archivo de datos.\n\n{error}",
            )
            return
        self.refresh_dashboard()
        self.play_feedback(success=True)
        self.toast.show_message("✓ Pago actualizado y guardado")

    def copy_reference(self, text, name):
        QApplication.clipboard().setText(text)
        self.play_feedback(success=False)
        self.toast.show_message(f"✓ {name}: partida copiada")

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.update_sound_button()
        if self.sound_on:
            self.play_feedback(success=False)
        self.toast.show_message("Sonido activado" if self.sound_on else "Sonido desactivado")

    def update_sound_button(self):
        self.sound_button.setText("Sonido: sí" if self.sound_on else "Sonido: no")
        self.sound_button.setToolTip("Activar o desactivar los sonidos de confirmación")

    def play_feedback(self, success):
        """Usa sonidos de sistema: nada que descargar y funciona en Windows 11."""
        if not self.sound_on or sys.platform != "win32":
            return
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK if success else winsound.MB_ICONASTERISK)
        except (ImportError, RuntimeError):
            pass

    def reset_year(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Reiniciar el año")
        dialog.setIcon(QMessageBox.Warning)
        dialog.setText("¿Reiniciar todos los pagos de 2026?")
        dialog.setInformativeText("Se conservarán los servicios y sus datos de pago. Se creará un backup antes de guardar.")
        dialog.setStandardButtons(QMessageBox.Cancel | QMessageBox.Reset)
        dialog.setDefaultButton(QMessageBox.Cancel)
        if dialog.exec() != QMessageBox.Reset:
            return
        for service in self.servicios:
            for month in MESES:
                service["pagos"][month] = False
        guardar_datos(self.servicios)
        for index in range(self.cards_layout.count()):
            card = self.cards_layout.itemAt(index).widget()
            if isinstance(card, ServiceCard):
                for button in card.month_buttons.values():
                    button.paid = False
                    button.refresh()
                card.refresh_counter()
        self.refresh_dashboard()
        self.play_feedback(success=False)
        self.toast.show_message("El año quedó listo para empezar de nuevo")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Impuestos Tracker")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
