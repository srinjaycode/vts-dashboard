import sys
import numpy as np
import serial
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QLineEdit,
                             QDialog, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# core serial data receiver from com port
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

# temp v time and remaining energy v time graph window
class GraphWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telemetry Graphs")
        self.setGeometry(150, 150, 800, 600)  
        self.parent = parent      
        layout = QVBoxLayout()
        self.temp_figure = Figure(figsize=(8, 3))
        self.temp_canvas = FigureCanvas(self.temp_figure)
        layout.addWidget(self.temp_canvas)  
        self.energy_figure = Figure(figsize=(8, 3))
        self.energy_canvas = FigureCanvas(self.energy_figure)
        layout.addWidget(self.energy_canvas)     
        self.setLayout(layout)
        self.update_graphs()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_graphs)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def update_graphs(self):
        if not self.parent:
            return
        timestamps = self.parent.timestamps
        motor_temps = self.parent.motor_temps
        battery_temps = self.parent.battery_temps
        energy_data = self.parent.energy_data
        
        if not timestamps:
            return
            
        # temperature plot
        self.temp_figure.clear()
        ax1 = self.temp_figure.add_subplot(111)
        ax1.plot(timestamps, motor_temps, 'r-', label='Motor Temp')
        ax1.plot(timestamps, battery_temps, 'b-', label='Battery Temp')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Temperature (°C)')
        ax1.set_title('Temperature vs Time')
        ax1.legend()
        ax1.grid(True)
        self.temp_figure.tight_layout()
        self.temp_canvas.draw()
        
        # energy plot
        self.energy_figure.clear()
        ax2 = self.energy_figure.add_subplot(111)
        ax2.plot(timestamps, energy_data, 'g-')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Remaining Energy (Ah)')
        ax2.set_title('Remaining Energy vs Time')
        ax2.grid(True)
        self.energy_figure.tight_layout()
        self.energy_canvas.draw()
        
    def closeEvent(self, event):
        self.update_timer.stop()
        event.accept()

# main telemetry dashboard
class TelemetryApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VTS Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)  # fixed size

        # timer stuff
        self.heat_time_seconds = 30 * 60  
        self.last_lap_time = self.heat_time_seconds
        self.lap_count = 0
        self.remaining_energy = 26  
        
        # telemetry data 
        self.motor_temp = 0
        self.battery_temp = 0
        self.vibration = 0
        self.warning_active = False

        # storing temp, energy, time for the graphs
        self.timestamps = []
        self.motor_temps = []
        self.battery_temps = []
        self.energy_data = []
        self.elapsed_time = 0  

        self.serial_reader = SerialReader()
        self.serial_reader.data_received.connect(self.process_serial_data)

        self.init_ui()
        
        # timer for heats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # timer for warning box
        self.warning_timer = QTimer(self)
        self.warning_timer.timeout.connect(self.toggle_warning)
        
        # timer for collecting data points (every 5 sec)
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.collect_data_point)

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Title
        self.title_label = QLabel("⚡ VTS Dashboard", alignment=Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(self.title_label)

        serial_layout = QHBoxLayout()
        
        # port selection 
        port_label = QLabel("Port:")
        port_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.port_combo = QComboBox()
        self.port_combo.addItems([f"COM{i}" for i in range(1, 11)])
        self.port_combo.setCurrentText("COM1")
        
        # baud rate selection 
        baud_label = QLabel("Baud:")
        baud_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        
        # serial connect button
        self.connect_button = QPushButton("Connect Serial")
        self.connect_button.clicked.connect(self.connect_serial)
        self.connect_button.setStyleSheet("background-color: teal; color: white; font-size: 14px; font-weight: bold; padding: 6px;")
        
        serial_layout.addWidget(port_label)
        serial_layout.addWidget(self.port_combo)
        serial_layout.addWidget(baud_label)
        serial_layout.addWidget(self.baud_combo)
        serial_layout.addWidget(self.connect_button)
        
        main_layout.addLayout(serial_layout)

        self.timer_label = QLabel(self.format_time(self.heat_time_seconds), alignment=Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 48px; font-weight: bold; color: yellow;")
        main_layout.addWidget(self.timer_label)

        grid_layout = QGridLayout()

        # telemetry data
        self.motor_temp_label = QLabel("Motor Temp: -- °C")
        self.battery_temp_label = QLabel("Battery Temp: -- °C")
        self.vibration_label = QLabel("Vibration Level: --")
        self.remaining_energy_label = QLabel(f"Remaining Energy: {self.remaining_energy} Ah")
        self.lap_count_label = QLabel(f"Lap Count: {self.lap_count}")

        # warning box
        self.warning_box = QFrame()
        self.warning_box.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.warning_box.setLineWidth(2)
        self.warning_box.setMidLineWidth(2)
        self.warning_box.setFixedSize(30, 30)
        self.warning_box.setStyleSheet("border: 2px solid red;")

        # remaining energy text input
        self.energy_input = QLineEdit()
        self.energy_input.setPlaceholderText("Enter Remaining Energy (Ah)")
        self.energy_input.setStyleSheet("font-size: 14px; padding: 5px;")

      
        labels = [self.motor_temp_label, self.battery_temp_label, self.vibration_label, 
                  self.remaining_energy_label, self.lap_count_label]
        for lbl in labels:
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")

        grid_layout.addWidget(self.motor_temp_label, 0, 0)
        grid_layout.addWidget(self.battery_temp_label, 0, 1)
        grid_layout.addWidget(self.vibration_label, 1, 0)
        grid_layout.addWidget(self.remaining_energy_label, 1, 1)
        grid_layout.addWidget(self.energy_input, 2, 0, 1, 1)
        grid_layout.addWidget(self.warning_box, 2, 1, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.lap_count_label, 3, 0, 1, 2)

        main_layout.addLayout(grid_layout)

        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Timer")
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 16px; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause Timer")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setStyleSheet("background-color: orange; color: white; font-size: 16px; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.pause_button)

        self.lap_button = QPushButton("Record Lap")
        self.lap_button.clicked.connect(self.record_lap)
        self.lap_button.setStyleSheet("background-color: blue; color: white; font-size: 16px; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.lap_button)

        self.pit_stop_button = QPushButton("Pit Stop")
        self.pit_stop_button.clicked.connect(self.pit_stop)
        self.pit_stop_button.setStyleSheet("background-color: red; color: white; font-size: 16px; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.pit_stop_button)

        main_layout.addLayout(buttons_layout)

        self.show_graphs_button = QPushButton("Show Graphs")
        self.show_graphs_button.clicked.connect(self.show_graphs)
        self.show_graphs_button.setStyleSheet("background-color: purple; color: white; font-size: 16px; font-weight: bold; padding: 8px; margin-top: 10px;")
        main_layout.addWidget(self.show_graphs_button)

        # lap time table
        self.lap_table = QTableWidget()
        self.lap_table.setColumnCount(4)
        self.lap_table.setHorizontalHeaderLabels(["Lap #", "Time Taken", "Energy Used", ""])
        self.lap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lap_table.setStyleSheet("font-size: 14px;")

        # scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.lap_table)
        main_layout.addWidget(scroll_area)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def connect_serial(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        
        if self.serial_reader.connect_serial(port, baud):
            self.connect_button.setText(f"Connected to {port}")
            self.connect_button.setStyleSheet("background-color: green; color: white; font-size: 14px; font-weight: bold; padding: 6px;")
            self.serial_reader.start_reading()
            self.data_timer.start(5000) 
        else:
            self.connect_button.setText("Connection Failed")
            self.connect_button.setStyleSheet("background-color: darkred; color: white; font-size: 14px; font-weight: bold; padding: 6px;")

    def process_serial_data(self, data):
        try:
            if "MT:" in data:
                self.motor_temp = float(data.split("MT:")[1].strip())
                self.motor_temp_label.setText(f"Motor Temp: {self.motor_temp} °C")
            
            elif "BT:" in data:
                self.battery_temp = float(data.split("BT:")[1].strip())
                self.battery_temp_label.setText(f"Battery Temp: {self.battery_temp} °C")
            elif "V:" in data:
                self.vibration = float(data.split("V:")[1].strip())
                self.vibration_label.setText(f"Vibration Level: {self.vibration}")
            
            elif "W" in data:
                if not self.warning_active:
                    self.warning_active = True
                    self.warning_box.setStyleSheet("background-color: red; border: 2px solid red;")
                    self.warning_timer.start(500)  # Blink every 500ms
            
        except Exception as e:
            print(f"Error processing serial data: {e}")

    def toggle_warning(self):
        if self.warning_active:
            current_style = self.warning_box.styleSheet()
            if "background-color: red" in current_style:
                self.warning_box.setStyleSheet("border: 2px solid red;")
            else:
                self.warning_box.setStyleSheet("background-color: red; border: 2px solid red;")

    def collect_data_point(self):
        # only collect if timer is running (meaning we're in a heat)
        if self.timer.isActive():
            self.elapsed_time += 5  
            
            self.timestamps.append(self.elapsed_time)
            self.motor_temps.append(self.motor_temp)
            self.battery_temps.append(self.battery_temp)
            self.energy_data.append(self.remaining_energy)
            
            # keep only the last 120 data points (10 minutes worth at 5s interval)
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
        new_energy = float(self.energy_input.text()) if self.energy_input.text() else self.remaining_energy
        energy_used = self.remaining_energy - new_energy
        self.remaining_energy = new_energy
        self.remaining_energy_label.setText(f"Remaining Energy: {self.remaining_energy} Ah")

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
        delete_button.setStyleSheet("background-color: red; color: white; font-size: 12px; font-weight: bold;")
        
        delete_button.clicked.connect(lambda: self.lap_table.removeRow(row_position))
        
        self.lap_table.setCellWidget(row_position, 3, delete_button)

    def pit_stop(self):
        if not hasattr(self, "in_pit_stop") or not self.in_pit_stop:
            # entering pit stop
            self.in_pit_stop = True
            self.pit_start_time = self.heat_time_seconds

            row_position = self.lap_table.rowCount()
            self.lap_table.insertRow(row_position)
            self.lap_table.setItem(row_position, 0, QTableWidgetItem("--"))
            self.lap_table.setItem(row_position, 1, QTableWidgetItem("Entered Pit Stop"))
            self.lap_table.setItem(row_position, 2, QTableWidgetItem("--"))
            self.pit_stop_button.setText("Exit Pit Stop")
        else:
            # exiting pit stop
            self.in_pit_stop = False
            pit_time = self.pit_start_time - self.heat_time_seconds

            row_position = self.lap_table.rowCount()
            self.lap_table.insertRow(row_position)
            self.lap_table.setItem(row_position, 0, QTableWidgetItem("--"))
            self.lap_table.setItem(row_position, 1, QTableWidgetItem(f"Pit Stop Complete ({self.format_time(pit_time)})"))
            self.lap_table.setItem(row_position, 2, QTableWidgetItem("--"))

            self.pit_stop_button.setText("Pit Stop")

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