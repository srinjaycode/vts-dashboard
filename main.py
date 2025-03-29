import sys
import numpy as np
import serial
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGridLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QDialog, QFrame, QComboBox, QSizePolicy, QStackedLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF, QPoint, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QDoubleValidator, QPalette, QPolygonF
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib as mpl

class ThemeManager:
    @staticmethod
    def apply_dark_theme(app):
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
        app.setPalette(palette)

        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px;
                min-width: 100px;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #333337;
                color: #E0E0E0;
                border: 1px solid #3F3F46;
                padding: 6px;
                min-height: 30px;
                font-size: 14px;
            }
            QComboBox {
                background-color: #333337;
                color: #E0E0E0;
                border: 1px solid #3F3F46;
                padding: 6px;
                min-height: 30px;
                font-size: 14px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #333337;
                color: #E0E0E0;
                selection-background-color: #0078D7;
                border: 1px solid #3F3F46;
            }
            QComboBox::drop-down {
                border: none;
            }
            QTableWidget {
                background-color: #252526;
                color: #E0E0E0;
                gridline-color: #3F3F46;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 8px;
                border: 1px solid #3F3F46;
                font-size: 14px;
            }
            QFrame {
                border: 1px solid #3F3F46;
                border-radius: 5px;
            }
        """)

    @staticmethod
    def apply_light_theme(app):
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        app.setPalette(palette)

        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px;
                min-width: 100px;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                padding: 6px;
                min-height: 30px;
                font-size: 14px;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                padding: 6px;
                min-height: 30px;
                font-size: 14px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #333333;
                selection-background-color: #0078D7;
                border: 1px solid #CCCCCC;
            }
            QComboBox::drop-down {
                border: none;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #333333;
                gridline-color: #CCCCCC;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 8px;
                border: 1px solid #CCCCCC;
                font-size: 14px;
            }
            QFrame {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
            }
        """)

class SerialReader(QObject):
    data_received = pyqtSignal(str)
    
    def __init__(self, port='COM1', baud_rate=9600):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.is_running = False
        self.ser = None
        
    def connect_serial(self, port, baud_rate):
        try:
            self.port = port
            self.baud_rate = baud_rate
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            return True
        except Exception as e:
            print(f"Serial connection error: {e}")
            return False
            
    def start_reading(self):
        self.is_running = True
        threading.Thread(target=self._read_serial, daemon=True).start()
        
    def stop_reading(self):
        self.is_running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            
    def _read_serial(self):
        while self.is_running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        self.data_received.emit(line)
            except Exception as e:
                print(f"Error reading serial: {e}")
                time.sleep(1)

class GraphWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telemetry Graphs")
        self.setGeometry(150, 150, 1000, 800)
        self.parent = parent
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.update_graphs()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_graphs)
        self.update_timer.start(500)

    def update_graphs(self):
        self.figure.clear()
        
        if self.parent.dark_mode:
            bg_color = '#2D2D30'
            text_color = '#E0E0E0'
            grid_color = '#3F3F46'
        else:
            bg_color = '#FFFFFF'
            text_color = '#333333'
            grid_color = '#CCCCCC'
            
        self.figure.set_facecolor(bg_color)
        
        timestamps = self.parent.timestamps
        motor_temps = self.parent.motor_temps
        battery_temps = self.parent.battery_temps
        energy_data = self.parent.energy_data
        
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        
        ax1.set_facecolor(bg_color)
        ax2.set_facecolor(bg_color)
        
        for ax in [ax1, ax2]:
            ax.spines['bottom'].set_color(text_color)
            ax.spines['top'].set_color(text_color) 
            ax.spines['right'].set_color(text_color)
            ax.spines['left'].set_color(text_color)
            ax.tick_params(axis='x', colors=text_color)
            ax.tick_params(axis='y', colors=text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            ax.grid(True, color=grid_color, linestyle='--', alpha=0.5)
        
        # Temperature plot
        ax1.plot(timestamps, motor_temps, color='#FF5555', linewidth=2, label='Motor Temp')
        ax1.plot(timestamps, battery_temps, color='#55AAFF', linewidth=2, label='Battery Temp')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Temperature (°C)')
        ax1.set_title('Temperature vs Time')
        legend1 = ax1.legend()
        frame1 = legend1.get_frame()
        frame1.set_facecolor(bg_color)
        frame1.set_edgecolor(text_color)
        for text in legend1.get_texts():
            text.set_color(text_color)
        
        # Energy plot
        ax2.plot(timestamps, energy_data, color='#00CC66', linewidth=2)
        ax2.fill_between(timestamps, energy_data, color='#00CC66', alpha=0.2)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Remaining Energy (Ah)')
        ax2.set_title('Remaining Energy vs Time')
        
        self.figure.tight_layout()
        self.canvas.draw()

class DecorativeTriangles(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.triangles = []
        self.generate_triangles()
        
    def generate_triangles(self):
        self.triangles = []
        for _ in range(40):  # number of triangles
            size = np.random.randint(35, 70)  # size range
            x = np.random.randint(0, self.width())
            y = np.random.randint(0, self.height())
            angle = np.random.randint(0, 360)
          
            color_choice = np.random.choice(['red', 'blue', 'yellow'])
            if color_choice == 'red':
                color = QColor(255, 70, 70)  
            elif color_choice == 'blue':
                color = QColor(70, 170, 255)  
            else:  # yellow
                color = QColor(255, 230, 100)  
            color.setAlpha(100)  # opacity
            self.triangles.append((x, y, size, angle, color))
    
    def resizeEvent(self, event):
        self.generate_triangles()
        super().resizeEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for x, y, size, angle, color in self.triangles:
            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            
            triangle = QPolygonF()
            triangle.append(QPointF(0, -size/2))
            triangle.append(QPointF(size/3, size/2))
            triangle.append(QPointF(-size/3, size/2))
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(triangle)
            painter.restore()

class TelemetryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTS Dashboard")
        self.setGeometry(100, 100, 1000, 800)
        
        self.dark_mode = True
        ThemeManager.apply_dark_theme(QApplication.instance())
        
        self.heat_time_seconds = 30 * 60  
        self.last_lap_time = self.heat_time_seconds
        self.lap_count = 0
        self.remaining_energy = 26  
        self.motor_temp = 25
        self.battery_temp = 25
        self.vibration = 20
        self.warning_active = False
        self.timestamps = []
        self.motor_temps = []
        self.battery_temps = []
        self.energy_data = []
        self.elapsed_time = 0  

        self.serial_reader = SerialReader()
        self.serial_reader.data_received.connect(self.process_serial_data)

        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.warning_timer = QTimer(self)
        self.warning_timer.timeout.connect(self.toggle_warning)
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.collect_data_point)
        
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        title_bar = QHBoxLayout()
        self.title_label = QLabel("⚡ VTS Dashboard")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        
        self.theme_button = QPushButton("🌙")
        self.theme_button.setFixedSize(40, 40)
        self.theme_button.setStyleSheet("border: none; background: transparent; font-size: 20px;")
        self.theme_button.clicked.connect(self.toggle_theme)
        
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()
        title_bar.addWidget(self.theme_button)
        main_layout.addLayout(title_bar)

        # Serial connection controls
        serial_frame = QFrame()
        serial_layout = QHBoxLayout(serial_frame)
        serial_layout.setContentsMargins(10, 10, 10, 10)
        
        port_label = QLabel("Port:")
        port_label.setStyleSheet("font-weight: bold;")
        self.port_combo = QComboBox()
        self.port_combo.addItems([f"COM{i}" for i in range(1, 11)])
        self.port_combo.setCurrentText("COM1")
        
        baud_label = QLabel("Baud:")
        baud_label.setStyleSheet("font-weight: bold;")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        
        self.connect_button = QPushButton("Connect Serial")
        self.connect_button.clicked.connect(self.connect_serial)
        self.connect_button.setStyleSheet("min-width: 120px;")
        
        serial_layout.addWidget(port_label)
        serial_layout.addWidget(self.port_combo)
        serial_layout.addWidget(baud_label)
        serial_layout.addWidget(self.baud_combo)
        serial_layout.addWidget(self.connect_button)
        main_layout.addWidget(serial_frame)

        # Timer display
        self.timer_label = QLabel(self.format_time(self.heat_time_seconds))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #FFDD00;")
        main_layout.addWidget(self.timer_label)

        # Temperature displays 
        temp_frame = QFrame()
        temp_layout = QHBoxLayout(temp_frame)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        temp_layout.setSpacing(20)
        
        self.motor_temp_label = QLabel("Motor: 25.0°C")
        self.motor_temp_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.battery_temp_label = QLabel("Battery: 25.0°C")
        self.battery_temp_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        temp_layout.addWidget(self.motor_temp_label)
        temp_layout.addWidget(self.battery_temp_label)
        main_layout.addWidget(temp_frame)

        # Other telemetry data
        telemetry_frame = QFrame()
        telemetry_layout = QGridLayout(telemetry_frame)
        telemetry_layout.setContentsMargins(10, 10, 10, 10)
        telemetry_layout.setSpacing(15)

        self.vibration_label = QLabel("Vibration Level: 20")
        self.vibration_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.remaining_energy_label = QLabel(f"Remaining Energy: {self.remaining_energy} Ah")
        self.remaining_energy_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.energy_input = QLineEdit()
        self.energy_input.setPlaceholderText("Enter Remaining Energy (Ah)")
        self.energy_input.setValidator(QDoubleValidator(0, 100, 2))
        self.energy_input.setStyleSheet("font-size: 16px;")
        
        self.warning_box = QFrame()
        self.warning_box.setFixedSize(40, 40)
        self.warning_box.setStyleSheet("border: 3px solid red; background: transparent;")
        
        self.lap_count_label = QLabel(f"Lap Count: {self.lap_count}")
        self.lap_count_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        telemetry_layout.addWidget(self.vibration_label, 0, 0)
        telemetry_layout.addWidget(self.remaining_energy_label, 0, 1)
        telemetry_layout.addWidget(self.energy_input, 1, 0)
        telemetry_layout.addWidget(self.warning_box, 1, 1, Qt.AlignmentFlag.AlignRight)
        telemetry_layout.addWidget(self.lap_count_label, 2, 0, 1, 2)
        
        main_layout.addWidget(telemetry_frame)

        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.start_button = QPushButton("Start Timer")
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setStyleSheet("background-color: #00A86B; min-width: 120px;")
        
        self.pause_button = QPushButton("Pause Timer")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setStyleSheet("background-color: #FF8C00; min-width: 120px;")
        
        self.lap_button = QPushButton("Record Lap")
        self.lap_button.clicked.connect(self.record_lap)
        self.lap_button.setStyleSheet("background-color: #0078D7; min-width: 120px;")
        
        self.pit_stop_button = QPushButton("Pit Stop")
        self.pit_stop_button.clicked.connect(self.pit_stop)
        self.pit_stop_button.setStyleSheet("background-color: #E74856; min-width: 120px;")
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.lap_button)
        buttons_layout.addWidget(self.pit_stop_button)
        main_layout.addLayout(buttons_layout)

        # Graphs button
        self.show_graphs_button = QPushButton("Show Graphs")
        self.show_graphs_button.clicked.connect(self.show_graphs)
        self.show_graphs_button.setStyleSheet("background-color: #8A2BE2; min-width: 120px;")
        main_layout.addWidget(self.show_graphs_button)

        # Lap time table
        self.lap_table = QTableWidget()
        self.lap_table.setColumnCount(4)
        self.lap_table.setHorizontalHeaderLabels(["Lap #", "Time Taken", "Energy Used", "Actions"])
        self.lap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lap_table.setMinimumHeight(200)
        main_layout.addWidget(self.lap_table)

        central_widget.setLayout(main_layout)
        
        self.triangle_overlay = DecorativeTriangles()
        self.triangle_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.stacked_layout.addWidget(central_widget)
        self.stacked_layout.addWidget(self.triangle_overlay)
        
        container = QWidget()
        container.setLayout(self.stacked_layout)
        self.setCentralWidget(container)
        
        # Timer to refresh triangles periodically
        self.triangle_timer = QTimer(self)
        self.triangle_timer.timeout.connect(self.refresh_triangles)
        self.triangle_timer.start(2000)  # refresh every 2 seconds

    def refresh_triangles(self):
        if hasattr(self, 'triangle_overlay'):
            self.triangle_overlay.generate_triangles()
            self.triangle_overlay.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'triangle_overlay'):
            self.triangle_overlay.setGeometry(self.rect())
            self.refresh_triangles()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.theme_button.setText("🌙")
            ThemeManager.apply_dark_theme(QApplication.instance())
            self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #FFDD00;")
        else:
            self.theme_button.setText("☀️")
            ThemeManager.apply_light_theme(QApplication.instance())
            self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #FF8C00;")
        self.update()

    def process_serial_data(self, data):
        try:
            if "MT:" in data:
                self.motor_temp = float(data.split("MT:")[1].strip())
                self.motor_temp_label.setText(f"Motor: {self.motor_temp:.1f}°C")
            
            elif "BT:" in data:
                self.battery_temp = float(data.split("BT:")[1].strip())
                self.battery_temp_label.setText(f"Battery: {self.battery_temp:.1f}°C")
                
            elif "V:" in data:
                self.vibration = float(data.split("V:")[1].strip())
                self.vibration_label.setText(f"Vibration Level: {self.vibration:.1f}")
            
            elif "W" in data:
                if not self.warning_active:
                    self.warning_active = True
                    self.warning_box.setStyleSheet("background-color: red; border: 3px solid red;")
                    self.warning_timer.start(500)
            
        except Exception as e:
            print(f"Error processing serial data: {e}")

    def connect_serial(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        
        if self.serial_reader.connect_serial(port, baud):
            self.connect_button.setText(f"Connected to {port}")
            self.connect_button.setStyleSheet("background-color: #00A86B; font-weight: bold;")
            self.serial_reader.start_reading()
            self.data_timer.start(5000) 
        else:
            self.connect_button.setText("Connection Failed")
            self.connect_button.setStyleSheet("background-color: #E74856; font-weight: bold;")

    def toggle_warning(self):
        if self.warning_active:
            current_style = self.warning_box.styleSheet()
            if "background-color: red" in current_style:
                self.warning_box.setStyleSheet("border: 2px solid red; background-color: transparent;")
            else:
                self.warning_box.setStyleSheet("background-color: red; border: 2px solid red;")

    def collect_data_point(self):
        if self.timer.isActive():
            self.elapsed_time += 5  
            
            self.timestamps.append(self.elapsed_time)
            self.motor_temps.append(self.motor_temp)
            self.battery_temps.append(self.battery_temp)
            self.energy_data.append(self.remaining_energy)
            
            if len(self.timestamps) > 120:
                self.timestamps = self.timestamps[-120:]
                self.motor_temps = self.motor_temps[-120:]
                self.battery_temps = self.battery_temps[-120:]
                self.energy_data = self.energy_data[-120:]

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def start_timer(self):
        if not self.timer.isActive():
            self.timer.start(1000)
            self.data_timer.start(5000)

    def pause_timer(self):
        if self.timer.isActive():
            self.timer.stop()

    def update_timer(self):
        if self.heat_time_seconds > 0:
            self.heat_time_seconds -= 1
            self.timer_label.setText(self.format_time(self.heat_time_seconds))

    def record_lap(self):
        try:
            new_energy = float(self.energy_input.text()) if self.energy_input.text() else self.remaining_energy
            energy_used = self.remaining_energy - new_energy
            self.remaining_energy = new_energy
            self.remaining_energy_label.setText(f"Remaining Energy: {self.remaining_energy:.2f} Ah")

            self.lap_count += 1
            time_taken = self.last_lap_time - self.heat_time_seconds
            self.last_lap_time = self.heat_time_seconds
            self.lap_count_label.setText(f"Lap Count: {self.lap_count}")

            row_position = self.lap_table.rowCount()
            self.lap_table.insertRow(row_position)
            self.lap_table.setItem(row_position, 0, QTableWidgetItem(str(self.lap_count)))
            self.lap_table.setItem(row_position, 1, QTableWidgetItem(self.format_time(time_taken)))
            self.lap_table.setItem(row_position, 2, QTableWidgetItem(f"{energy_used:.2f} Ah"))

            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #E74856;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    min-width: 60px;
                }
            """)
            delete_button.clicked.connect(lambda: self.lap_table.removeRow(row_position))
            self.lap_table.setCellWidget(row_position, 3, delete_button)
            
            # Clear the input field
            self.energy_input.clear()
            
        except ValueError:
            print("Invalid energy value entered")

    def pit_stop(self):
        if not hasattr(self, "in_pit_stop") or not self.in_pit_stop:
            # Entering pit stop
            self.in_pit_stop = True
            self.pit_start_time = self.heat_time_seconds

            row_position = self.lap_table.rowCount()
            self.lap_table.insertRow(row_position)
            self.lap_table.setItem(row_position, 0, QTableWidgetItem("--"))
            self.lap_table.setItem(row_position, 1, QTableWidgetItem("Entered Pit Stop"))
            self.lap_table.setItem(row_position, 2, QTableWidgetItem("--"))
            self.pit_stop_button.setText("Exit Pit Stop")
            self.pit_stop_button.setStyleSheet("background-color: #00A86B; font-weight: bold;")
        else:
            # Exiting pit stop
            self.in_pit_stop = False
            pit_time = self.pit_start_time - self.heat_time_seconds

            row_position = self.lap_table.rowCount()
            self.lap_table.insertRow(row_position)
            self.lap_table.setItem(row_position, 0, QTableWidgetItem("--"))
            self.lap_table.setItem(row_position, 1, QTableWidgetItem(f"Pit Stop Complete ({self.format_time(pit_time)})"))
            self.lap_table.setItem(row_position, 2, QTableWidgetItem("--"))
            self.pit_stop_button.setText("Pit Stop")
            self.pit_stop_button.setStyleSheet("background-color: #E74856; font-weight: bold;")

    def show_graphs(self):
        graph_window = GraphWindow(self)
        graph_window.exec()
        
    def closeEvent(self, event):
        self.serial_reader.stop_reading()
        self.timer.stop()
        self.warning_timer.stop()
        self.data_timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelemetryApp()
    window.show()
    sys.exit(app.exec())