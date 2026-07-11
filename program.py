import sys
import json
import yaml
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import threading
import argparse
from pathlib import Path

# PyQt6 imports
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QPushButton, QLabel, QFileDialog,
        QTextEdit, QMessageBox, QProgressBar, QComboBox,
        QFrame, QStatusBar
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QPalette
    HAS_UI = True
except ImportError:
    HAS_UI = False


# ============================================================
# Task2: Wczytywanie z pliku JSON
# ============================================================
def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Błąd składni pliku JSON: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Plik nie istnieje: {filepath}")


# ============================================================
# Task3: Zapis do pliku JSON
# ============================================================
def save_json(data, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Błąd zapisu pliku JSON: {e}")


# ============================================================
# Task4: Wczytywanie z pliku YAML
# ============================================================
def load_yaml(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError("Plik YAML jest pusty lub nieprawidłowy")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Błąd składni pliku YAML: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Plik nie istnieje: {filepath}")


# ============================================================
# Task5: Zapis do pliku YAML
# ============================================================
def save_yaml(data, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        raise IOError(f"Błąd zapisu pliku YAML: {e}")


# ============================================================
# Task6: Wczytywanie z pliku XML
# ============================================================
def xml_to_dict(element):
    result = {}
    if element.attrib:
        result['@attributes'] = element.attrib
    children = list(element)
    if children:
        child_dict = {}
        for child in children:
            child_data = xml_to_dict(child)
            if child.tag in child_dict:
                if not isinstance(child_dict[child.tag], list):
                    child_dict[child.tag] = [child_dict[child.tag]]
                child_dict[child.tag].append(child_data)
            else:
                child_dict[child.tag] = child_data
        result.update(child_dict)
    else:
        if element.text and element.text.strip():
            result = element.text.strip()
    return result


def load_xml(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        return {root.tag: xml_to_dict(root)}
    except ET.ParseError as e:
        raise ValueError(f"Błąd składni pliku XML: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Plik nie istnieje: {filepath}")


# ============================================================
# Task7: Zapis do pliku XML
# ============================================================
def dict_to_xml(data, root_name="root"):
    def build_element(parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '@attributes':
                    continue
                child = ET.SubElement(parent, str(key))
                if isinstance(data, dict) and '@attributes' in data:
                    for attr_key, attr_val in data['@attributes'].items():
                        parent.set(attr_key, attr_val)
                build_element(child, value)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, "item")
                build_element(child, item)
        else:
            parent.text = str(data)

    root = ET.Element(root_name)
    build_element(root, data)
    return root


def save_xml(data, filepath):
    try:
        if isinstance(data, dict) and len(data) == 1:
            root_name = list(data.keys())[0]
            root_data = data[root_name]
        else:
            root_name = "root"
            root_data = data

        root = dict_to_xml(root_data, root_name)
        xml_str = ET.tostring(root, encoding='unicode')
        pretty_xml = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="    ")
        lines = pretty_xml.split('\n')
        pretty_xml = '\n'.join(lines[1:])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(pretty_xml)
    except Exception as e:
        raise IOError(f"Błąd zapisu pliku XML: {e}")


# ============================================================
# Helpers
# ============================================================
def get_extension(filepath):
    ext = Path(filepath).suffix.lower()
    if ext in ['.yaml', '.yml']:
        return 'yaml'
    elif ext == '.json':
        return 'json'
    elif ext == '.xml':
        return 'xml'
    else:
        raise ValueError(f"Nieobsługiwany format pliku: {ext}")


def load_file(filepath):
    fmt = get_extension(filepath)
    if fmt == 'json':
        return load_json(filepath)
    elif fmt == 'yaml':
        return load_yaml(filepath)
    elif fmt == 'xml':
        return load_xml(filepath)


def save_file(data, filepath):
    fmt = get_extension(filepath)
    if fmt == 'json':
        save_json(data, filepath)
    elif fmt == 'yaml':
        save_yaml(data, filepath)
    elif fmt == 'xml':
        save_xml(data, filepath)


# ============================================================
# Task1: Parsowanie argumentów
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description='Konwerter formatów danych (JSON, YAML, XML)',
        usage='program.exe pathFile1.x pathFile2.y'
    )
    parser.add_argument('input', nargs='?', help='Plik wejściowy (.json, .yaml, .yml, .xml)')
    parser.add_argument('output', nargs='?', help='Plik wyjściowy (.json, .yaml, .yml, .xml)')
    return parser.parse_args()


def run_cli(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Błąd: Plik wejściowy '{input_path}' nie istnieje.")
        sys.exit(1)

    try:
        print(f"Wczytywanie: {input_path}")
        data = load_file(input_path)
        print(f"Zapisywanie: {output_path}")
        save_file(data, output_path)
        print(f"Konwersja zakończona pomyślnie: {input_path} -> {output_path}")
    except (ValueError, IOError, FileNotFoundError) as e:
        print(f"Błąd: {e}")
        sys.exit(1)


# ============================================================
# Task9: Asynchroniczny worker dla UI
# ============================================================
class ConversionWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            data = load_file(self.input_path)
            save_file(data, self.output_path)
            self.finished.emit(True, f"Konwersja zakończona: {self.input_path} → {self.output_path}")
        except Exception as e:
            self.finished.emit(False, str(e))


# ============================================================
# Task8: UI w PyQt6
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Konwerter formatów danych - Szymon Wypler 60822")
        self.setMinimumSize(700, 500)
        self.worker = None
        self.input_path = ""
        self.output_path = ""
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tytuł
        title = QLabel("Konwerter formatów: JSON / YAML / XML")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        # Plik wejściowy
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Brak wybranego pliku wejściowego")
        self.input_label.setWordWrap(True)
        btn_input = QPushButton("Wybierz plik wejściowy")
        btn_input.setFixedWidth(200)
        btn_input.clicked.connect(self.choose_input)
        input_layout.addWidget(btn_input)
        input_layout.addWidget(self.input_label)
        layout.addLayout(input_layout)

        # Plik wyjściowy
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Brak wybranego pliku wyjściowego")
        self.output_label.setWordWrap(True)
        btn_output = QPushButton("Wybierz plik wyjściowy")
        btn_output.setFixedWidth(200)
        btn_output.clicked.connect(self.choose_output)
        output_layout.addWidget(btn_output)
        output_layout.addWidget(self.output_label)
        layout.addLayout(output_layout)

        # Przycisk konwersji
        self.btn_convert = QPushButton("Konwertuj")
        self.btn_convert.setFixedHeight(45)
        self.btn_convert.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_convert.clicked.connect(self.convert)
        layout.addWidget(self.btn_convert)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Log
        log_label = QLabel("Log:")
        layout.addWidget(log_label)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Gotowy")

    def choose_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik wejściowy", "",
            "Pliki danych (*.json *.yaml *.yml *.xml)"
        )
        if path:
            self.input_path = path
            self.input_label.setText(path)
            self.log.append(f"Wybrano plik wejściowy: {path}")

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Wybierz plik wyjściowy", "",
            "JSON (*.json);;YAML (*.yaml);;XML (*.xml)"
        )
        if path:
            self.output_path = path
            self.output_label.setText(path)
            self.log.append(f"Wybrano plik wyjściowy: {path}")

    def convert(self):
        if not self.input_path:
            QMessageBox.warning(self, "Błąd", "Nie wybrano pliku wejściowego!")
            return
        if not self.output_path:
            QMessageBox.warning(self, "Błąd", "Nie wybrano pliku wyjściowego!")
            return
        if not os.path.exists(self.input_path):
            QMessageBox.critical(self, "Błąd", f"Plik wejściowy nie istnieje:\n{self.input_path}")
            return

        self.btn_convert.setEnabled(False)
        self.progress.setVisible(True)
        self.status.showMessage("Konwertowanie...")
        self.log.append(f"Konwertowanie: {self.input_path} → {self.output_path}")

        # Task9: asynchroniczne wykonanie
        self.worker = ConversionWorker(self.input_path, self.output_path)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        self.btn_convert.setEnabled(True)
        self.progress.setVisible(False)
        if success:
            self.status.showMessage("Gotowy")
            self.log.append(f"✓ {message}")
            QMessageBox.information(self, "Sukces", message)
        else:
            self.status.showMessage("Błąd")
            self.log.append(f"✗ Błąd: {message}")
            QMessageBox.critical(self, "Błąd konwersji", message)


# ============================================================
# Punkt wejścia
# ============================================================
def main():
    args = parse_args()

    if args.input and args.output:
        # Tryb CLI
        run_cli(args.input, args.output)
    else:
        # Tryb UI
        if not HAS_UI:
            print("Błąd: PyQt6 nie jest zainstalowane. Zainstaluj: pip install PyQt6")
            print("Użycie CLI: program.exe plik_wejściowy.json plik_wyjściowy.yaml")
            sys.exit(1)
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
