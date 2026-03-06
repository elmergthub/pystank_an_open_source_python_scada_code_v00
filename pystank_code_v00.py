############################-----------------------------------PLC TCP IP_PLC------------------------------------------#########################################

import sys
import threading
import time
import struct
from pymodbus.client import ModbusTcpClient


############################-------------------------------------GRAPH---------------------------------------------#########################################
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import signal



############################-----------------------------------USER INTERFACE--------------------------------------##########################################

import sys
import random
from collections import deque

#-------------------------------------------------------- PyQt6 widgets and tools-------------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,QCheckBox,QDateTimeEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget, QLineEdit, QGroupBox, QGridLayout, QSizePolicy, QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QMainWindow, QFileDialog
)
from PyQt6.QtCore import QTimer, Qt, QPoint, QDateTime
from PyQt6.QtGui import QPixmap, QColor, QPainter, QDoubleValidator, QFont, QPen, QPolygon, QBrush, QIcon



#-----------------------------------------------------------plotting module-------------------------------------------------------------------------------------
import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from pyqtgraph import AxisItem
from openpyxl import Workbook

###########################------------------------------------Data Base--------------------------------------------#########################################

data_base_global = "signals_to_plc.db"

def create_global_database():
    conection = sqlite3.connect(data_base_global)
    c = conection.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS data (
            timestamp REAL,
            pv REAL,
            sv REAL,
            cv REAL
        )
    ''')
    conection.commit()
    conection.close()

def insert_global_data(pv, sv, cv):
    conection = sqlite3.connect(data_base_global)
    c = conection.cursor()
    c.execute("INSERT INTO data VALUES (?, ?, ?, ?)", (time.time(), pv, sv, cv))
    conection.commit()
    conection.close()

def query_global_data(ts_start, ts_end):
    conection = sqlite3.connect(data_base_global)
    c = conection.cursor()
    c.execute("SELECT timestamp, pv, sv, cv FROM data WHERE timestamp BETWEEN ? AND ?", (ts_start, ts_end))
    rows = c.fetchall()
    conection.close()
    return rows

############################--------------------------Convert timestamps to datetime and format ------------------------##########################################

class TimeAxisItem(AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)  

    def tickStrings(self, values, scale, spacing):
        # Convertir timestamps a datetime y formatear
        return [datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S") for value in values]

############################-----------------------------------SIMULACION DATE------------------------------------------#########################################

# Kd, Kp, Ki, Kv, A = 0, 0.4, 0.04, 2.22e-3, 1
# num = [Kd, Kp, Ki]
# den = [Kd + A, Kp + Kv, Ki]
# system = signal.TransferFunction(num, den)



#-----------------------------------------------------------X-axis with dates-------------------------------------------------------------------------------------
class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(v).strftime("%H:%M:%S") for v in values]

############################-----------------------------------PLC TCP IP_PLC------------------------------------------###############################################
#----------------------------------------------------------Configuration MODBUS-----------------------------------------------------------------------------------
IP_PLC = '192.168.0.20'
PORT_PLC = 502

address_float_read = 2
address_float_write = 2

count_float = 16
n_registers_float = 2

address_word_read = 0 
count_word = 1

address_word_write = 1
count_word_write = 1
global flag_word_write_read
flag_word_write_read = True
flag_float_write_read = True


#----------------------------------------------------------Process control variables---------------------------------------------------------------------------------
global_send_MB = False
global_pause_MB = threading.Event()
lock = threading.Lock()

mode_send_float = False
mode_send_bool = False



#--------------------------------------------------------------float to write-----------------------------------------------------------------------------------
float_w_0  = 0.0 #PID SV
float_w_1  = 0.0 #PID KP
float_w_2  = 0.0 #PID TI
float_w_3  = 0.0 #PID TD
float_w_4  = 0.0 #VDF HZ 
float_w_5  = 0.0
float_w_6  = 0.0
float_w_7  = 0.0
float_w_8  = 0.0
float_w_9  = 0.0
float_w_10 = 0.0
float_w_11 = 0.0
float_w_12 = 0.0
float_w_13 = 0.0
float_w_14 = 0.0
float_w_15 = 0.0


f_float_write = [float_w_0, float_w_1, float_w_2,float_w_3, float_w_4, float_w_5,float_w_6, float_w_7, float_w_8, 
                                float_w_9, float_w_10, float_w_11,float_w_12, float_w_13, float_w_14,float_w_15]


#--------------------------------------------------------------bool to write-----------------------------------------------------------------------------------
bool_w_0 = False
bool_w_1 = False
bool_w_2 = False
bool_w_3 = False
bool_w_4 = False
bool_w_5 = False
bool_w_6 = False
bool_w_7 = False
bool_w_8 = False
bool_w_9 = False
bool_w_10 = False
bool_w_11 = False
bool_w_12 = False
bool_w_13 = False
bool_w_14 = False
bool_w_15 = False

f_bool_write = [bool_w_0, bool_w_1, bool_w_2, bool_w_3, bool_w_4, bool_w_5, bool_w_6, bool_w_7,
                                    bool_w_8, bool_w_9, bool_w_10, bool_w_11, bool_w_12, bool_w_13, bool_w_14, bool_w_15]





#--------------------------------------------------------------bool to read-----------------------------------------------------------------------------------
bool_r_0 = False 
bool_r_1 = False 
bool_r_2 = False 
bool_r_3 = False 
bool_r_4 = False
bool_r_5 = False
bool_r_6 = False
bool_r_7 = False
bool_r_8 = False
bool_r_9 = False
bool_r_10 = False
bool_r_11 = False
bool_r_12 = False
bool_r_13 = False
bool_r_14 = False
bool_r_15 = False

#--------------------------------------------------------------float to read-----------------------------------------------------------------------------------
float_r_0 = 0.0 #PID SV
float_r_1 = 0.0 #PID KP
float_r_2 = 0.0 #PID TI
float_r_3 = 0.0 #PID TD
float_r_4 = 0.0 #VDF HZ 
float_r_5 = 0.0
float_r_6 = 0.0
float_r_7 = 0.0
float_r_8 = 0.0 #PID PV M 
float_r_9 = 0.0 #PID CV HZ 
float_r_10 = 0.0 #FLOW
float_r_11 = 0.0
float_r_12 = 0.0
float_r_13 = 0.0
float_r_14 = 0.0
float_r_15 = 0.0


#--------------------------------------------------------------values to PID-----------------------------------------------------------------------------------
pv_pid = 0.0 #Lectura 
sv_pid = 0.0 #Escritura 
kp_pid = 0.0 #Escritura 
ti_pid = 0.0 #Escritura 
td_pid = 0.0 #Escritura 



#---------------------------------------------------------Modbus read/write functions---------------------------------------------------------------------------
def read_global_data():
    global global_send_MB
    while True:
        if global_pause_MB.is_set():
            time.sleep(1)
            continue

        try:
            with ModbusTcpClient(IP_PLC, port=PORT_PLC) as client:
                if not client.connect():
                    print("Failed to connect for reading MODBUS")
                    time.sleep(2)
                    continue
                
                global float_r_0, float_r_1, float_r_2, float_r_3, float_r_4, float_r_5, float_r_6, float_r_7
                global float_r_8, float_r_9, float_r_10, float_r_11, float_r_12, float_r_13, float_r_14, float_r_15
                global f_float_read, f_bool_read, f_bool_read_write, f_bool_write,f_float_write
                global flag_word_write_read, flag_float_write_read


                f_n_register = n_registers_float * count_float
                tcp_read_float = client.read_holding_registers(address=address_float_read, count=f_n_register, slave=1)
                if not tcp_read_float.isError():
                    tcp_register_r = tcp_read_float.registers
                    f_float_read = []
                    for i in range(0, f_n_register, 2):
                        pair = tcp_register_r[i:i+2]
                        bytes_dato = struct.pack('>HH', pair[0], pair[1])
                        value = struct.unpack('>f', bytes_dato)[0]
                        f_float_read.append(value)

                    if len(f_float_read) >= 16:

                        (float_r_0, float_r_1, float_r_2, float_r_3, float_r_4, float_r_5, float_r_6, float_r_7,
                        float_r_8, float_r_9, float_r_10, float_r_11, float_r_12, float_r_13, float_r_14, float_r_15) = f_float_read[:16]

                    for i, val in enumerate(f_float_read):
                        print(f"FLOAT {i+1}: {val}")

                    if flag_float_write_read == True:
                        f_float_write = f_float_read
                        flag_float_write_read = False
                else:
                    print("Error reading float values")


                tcp_read_word = client.read_holding_registers(address=address_word_read, count=count_word, slave=1)
                if not tcp_read_word.isError():
                    val_bool_r = tcp_read_word.registers[0]
                    f_bool_read = [(val_bool_r >> i) & 1 for i in range(16)]
                    
                    # Individual assignment to bool variables
                    global bool_r_0, bool_r_1, bool_r_2, bool_r_3, bool_r_4, bool_r_5, bool_r_6, bool_r_7
                    global bool_r_8, bool_r_9, bool_r_10, bool_r_11, bool_r_12, bool_r_13, bool_r_14, bool_r_15
                    bool_r_0  = bool(f_bool_read[0])
                    bool_r_1  = bool(f_bool_read[1])
                    bool_r_2  = bool(f_bool_read[2])
                    bool_r_3  = bool(f_bool_read[3])
                    bool_r_4  = bool(f_bool_read[4])
                    bool_r_5  = bool(f_bool_read[5])
                    bool_r_6  = bool(f_bool_read[6])
                    bool_r_7  = bool(f_bool_read[7])
                    bool_r_8  = bool(f_bool_read[8])
                    bool_r_9  = bool(f_bool_read[9])
                    bool_r_10 = bool(f_bool_read[10])
                    bool_r_11 = bool(f_bool_read[11])
                    bool_r_12 = bool(f_bool_read[12])
                    bool_r_13 = bool(f_bool_read[13])
                    bool_r_14 = bool(f_bool_read[14])
                    bool_r_15 = bool(f_bool_read[15])

                    # results
                    for i in range(16):
                        print(f"Salida_{i}: {eval(f'bool_r_{i}')}")
                else:
                    print("Error reading bool values")
                

                if flag_word_write_read == True:

                    
                    tcp_read_write_word = client.read_holding_registers(address=address_word_write, count=count_word_write, slave=1) 
                    if not tcp_read_write_word.isError():
                        val_bool_r = tcp_read_write_word.registers[0]
                        f_bool_read_write = [(val_bool_r >> i) & 1 for i in range(16)]
                        
                        f_bool_write = f_bool_read_write

                        flag_word_write_read = False
                        
                    else:
                        print("Error WORD read/write")

                

            time.sleep(1)

        except Exception as e:
            print(f"Read exception: {e}")
            time.sleep(4)

def write_global_data():

    global global_send_MB, f_float_write, f_bool_write
    global mode_send_float, mode_send_bool 

    while True:
        if not global_send_MB:
            time.sleep(0.01) # 0.1 seg 
            continue

        try:
            global_pause_MB.set()
            with ModbusTcpClient(IP_PLC, port=PORT_PLC) as client:
                if not client.connect():
                    print("Failed to connect for writing.")
                    time.sleep(2)
                    continue
                if mode_send_float == True:
                    registros_w = []
                    with lock:
                        for val in f_float_write:
                            bytes_float = struct.pack('>f', val)
                            hi, lo = struct.unpack('>HH', bytes_float)
                            registros_w.extend([hi, lo])

                    wr = client.write_registers(address=address_float_write, values=registros_w, slave=1)
                    if not wr.isError():
                        print("float values written successfully")
                    else:
                        print("Error writing float values.")
                
                if mode_send_bool == True:
                    bits = f_bool_write
                    word_send = 0
                    for i, bit in enumerate(bits):
                        if bit:
                            word_send |= (1 << i)

                    wr_bool = client.write_register(address=address_word_write, value=word_send, slave=1)
                    if not wr_bool.isError():
                        print("word values written successfully")
                    else:
                        print("Error writing word values.")

            global_send_MB = False
            mode_send_float = False
            mode_send_bool = False
            time.sleep(1)

        except Exception as e:
            print(f"Write exception: {e}")

        finally:
            global_pause_MB.clear()






#---------------------------------------------------------Custom tank visualization widget---------------------------------------------------------------------------
class i_level_tank(QFrame):
    def __init__(self, width=30, height=120, parent = None):
        super().__init__(parent)
        self.setFixedSize(width, height)  
        self.level = 0  # Initial tank level
        self.color = QColor("gray")  
        self.setStyleSheet("background-color: white;")  

    def setNivel(self, porcentaje, color):
        self.level = max(0, min(100, porcentaje))  # Scaled so that the level is between 0 and 100
        self.color = QColor(color)  
        self.update()  # Refresh the widget

    def paintEvent(self, event):
        painter = QPainter(self)  
        painter.setPen(Qt.GlobalColor.black)  
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)  

        fill_height = int(self.height() * self.level / 100)  # Height scaled according to the level
        fill_rect = self.rect().adjusted(1, self.height() - fill_height + 1, -1, -1)  
        painter.fillRect(fill_rect, self.color)  




#------------------------------------------------------------------flow arrows----------------------------------------------------------------------------------
class flow_widget(QWidget):
    def __init__(self, direction="right", start_offset=10, length=150, 
                head_length=15, head_width=8, line_width=2, color=Qt.GlobalColor.blue, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.start_offset = start_offset
        self.length = length
        self.head_length = head_length
        self.head_width = head_width
        self.line_width = line_width
        self.color = color
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent;")
        
        if direction in ["right", "left"]:
            self.setFixedSize(length + head_length + start_offset + 10, max(head_width * 2 + 20, 50))
        else:  # "up", "down"
            self.setFixedSize(max(head_width * 2 + 20, 50), length + head_length + start_offset + 10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(self.color, self.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.color))

        w, h = self.width(), self.height()
        hl = self.head_length
        hw = self.head_width

        # right-pointing flow arrow
        if self.direction == "right":
            start = QPoint(self.start_offset, h // 2)
            end = QPoint(start.x() + self.length - hl, h // 2)
            f_point = QPoint(end.x() + hl, end.y())
            base_left = QPoint(end.x(), end.y() - hw)
            base_right = QPoint(end.x(), end.y() + hw)

        # left-pointing flow arrow
        elif self.direction == "left":
            start = QPoint(w - self.start_offset, h // 2)
            end = QPoint(start.x() - self.length + hl, h // 2)
            f_point = QPoint(end.x() - hl, end.y())
            base_left = QPoint(end.x(), end.y() - hw)
            base_right = QPoint(end.x(), end.y() + hw)

        # up-pointing flow arrow
        elif self.direction == "up":
            start = QPoint(w // 2, h - self.start_offset)
            end = QPoint(w // 2, start.y() - self.length + hl)
            f_point = QPoint(end.x(), end.y() - hl)
            base_left = QPoint(end.x() - hw, end.y())
            base_right = QPoint(end.x() + hw, end.y())

        # down-pointing flow arrow
        elif self.direction == "down":
            start = QPoint(w // 2, self.start_offset)
            end = QPoint(w // 2, start.y() + self.length - hl)
            f_point = QPoint(end.x(), end.y() + hl)
            base_left = QPoint(end.x() - hw, end.y())
            base_right = QPoint(end.x() + hw, end.y())

        # arrowhead
        painter.drawLine(start, end)
        arrow_head = QPolygon([f_point, base_left, base_right])
        painter.drawPolygon(arrow_head)


class flow_electric(QWidget):
    def __init__(self, direction="right", start_offset=10, length=150, 
                head_length=15, head_width=8, line_width=2, color=Qt.GlobalColor.red, 
                dash_pattern=[5, 3], parent=None):
        super().__init__(parent)
        self.direction = direction
        self.start_offset = start_offset
        self.length = length
        self.head_length = head_length
        self.head_width = head_width
        self.line_width = line_width
        self.color = color
        self.dash_pattern = dash_pattern 
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent;")
        
        if direction in ["right", "left"]:
            self.setFixedSize(length + head_length + start_offset + 10, max(head_width * 2 + 20, 50))
        else:  # "up", "down"
            self.setFixedSize(max(head_width * 2 + 20, 50), length + head_length + start_offset + 10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Set dashed pen style
        pen = QPen(self.color, self.line_width)
        pen.setDashPattern(self.dash_pattern)  
        pen.setCapStyle(Qt.PenCapStyle.FlatCap) 
        painter.setPen(pen)
        painter.setBrush(QBrush(self.color))

        w, h = self.width(), self.height()
        hl = self.head_length
        hw = self.head_width

        # e_right-pointing flow arrow
        if self.direction == "right":
            start = QPoint(self.start_offset, h // 2)
            end = QPoint(start.x() + self.length - hl, h // 2)
            f_point = QPoint(end.x() + hl, end.y())
            base_left = QPoint(end.x(), end.y() - hw)
            base_right = QPoint(end.x(), end.y() + hw)

        # e_left-pointing flow arrow
        elif self.direction == "left":
            start = QPoint(w - self.start_offset, h // 2)
            end = QPoint(start.x() - self.length + hl, h // 2)
            f_point = QPoint(end.x() - hl, end.y())
            base_left = QPoint(end.x(), end.y() - hw)
            base_right = QPoint(end.x(), end.y() + hw)

        # e_up-pointing flow arrow
        elif self.direction == "up":
            start = QPoint(w // 2, h - self.start_offset)
            end = QPoint(w // 2, start.y() - self.length + hl)
            f_point = QPoint(end.x(), end.y() - hl)
            base_left = QPoint(end.x() - hw, end.y())
            base_right = QPoint(end.x() + hw, end.y())

        # e_down-pointing flow arrow
        elif self.direction == "down":
            start = QPoint(w // 2, self.start_offset)
            end = QPoint(w // 2, start.y() + self.length - hl)
            f_point = QPoint(end.x(), end.y() + hl)
            base_left = QPoint(end.x() - hw, end.y())
            base_right = QPoint(end.x() + hw, end.y())

        # e_arrowhead
        painter.drawLine(start, end)
        arrow_head = QPolygon([f_point, base_left, base_right])
        painter.drawPolygon(arrow_head)



############################-------------------------------------Main system screen------------------------------------------------############################
class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(900, 600)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.parameters_window = []

        main_layout = QVBoxLayout(self)
        
        # Sensor reading timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_sensors)
        self.timer.start(1000)

        main_container_top = QHBoxLayout()

        # Pump window 
        pump_window = QFrame()
        pump_window.setMinimumSize(150, 200)  
        pump_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Image 1 (PLC)
        self.label_imagen1 = QLabel(pump_window)
        self.label_imagen1.setObjectName("PLC_Principal")
        self.label_imagen1.setPixmap(QPixmap("images/PLC_LC.png").scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio))
        self.label_imagen1.setGeometry(250, 20, 90, 90)  

        self.tag_imagen1 = QLabel("      PLC \n \n  LC\n 101", pump_window)
        self.tag_imagen1.setGeometry(280, 0, 75, 100) 
        self.tag_imagen1.setStyleSheet("font-weight: bold;")
        

        # Image 1.1 (VDF)
        self.image_vdf = QLabel(pump_window)
        self.image_vdf.setPixmap(QPixmap("images/FIC.png").scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_vdf.setGeometry(250, 125, 120, 90)  
        self.tag_imagen2 = QLabel("      VDF \n \n FIC \n 101", pump_window)
        self.tag_imagen2.setGeometry(280, 102, 75, 100)  
        self.tag_imagen2.setStyleSheet("font-weight: bold;")

        # Image conector input
        self.image_input_s1 = QLabel(pump_window)
        self.image_input_s1.setPixmap(QPixmap("images/conector_input.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_input_s1.setGeometry(0, 213, 150, 150) 
        self.tag_image_input_s1 = QLabel("103 | TK-003", pump_window)
        self.tag_image_input_s1.setGeometry(10, 238, 75, 100)  
        self.tag_image_input_s1.setStyleSheet("font-weight: bold;")

        # Image 2 (Pump)
        self.label_pump = QLabel(pump_window)
        self.state_pump = True
        self.label_pump.setPixmap(QPixmap("images/pump.png").scaled(80,120, Qt.AspectRatioMode.KeepAspectRatio))
        self.label_pump.setGeometry(250, 185, 100, 200)  
        self.tag_imagen3 = QLabel("PUMP | P-001", pump_window)
        self.tag_imagen3.setGeometry(250, 320, 100, 20) 
        self.tag_imagen3.setStyleSheet("font-weight: bold;")
        
        self.label_pump.mousePressEvent = lambda event: self.show_parameters_pump(self.label_pump, "Pump Parameters")

        # Image VALVE CHECK
        self.image_check = QLabel(pump_window)
        self.image_check.setPixmap(QPixmap("images/check.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_check.setGeometry(345, 245, 40, 40)  

        # Image VALVE manual
        self.image_valve_1 = QLabel(pump_window)
        self.image_valve_1.setPixmap(QPixmap("images/valve.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_valve_1.setGeometry(410, 246, 40, 40)  

        # Pump frequency
        self.value_pump = QLabel("0.0 Hz", pump_window)
        self.value_pump .setGeometry(330, 140, 100, 30)  
        self.value_pump .setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_pump .setStyleSheet("background-color: white; border: 1px solid black; color: black;")
        

        main_container_top.addWidget(pump_window, 1)
        
        

        
        # Timer to toggle pump state
        self.state_pump = QTimer()
        self.state_pump.timeout.connect(self.toggle_pump_image)
        self.state_pump.start(100)  # Cambia cada 1000 ms (1 segundo)



        # Flowmeter window
        flowmeter_window = QFrame()
        flowmeter_window.setMinimumSize(150, 200)
        flowmeter_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        label_flowmeter = QLabel(flowmeter_window)
        label_flowmeter.setPixmap(QPixmap("images/flow_meter.png").scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio))
        label_flowmeter.setGeometry(200, 40, 130, 130)
        label_flowmeter.mousePressEvent = lambda event: self.show_parameters_tank(label_flowmeter, "Flowmeter Parameters")
        self.tag_imagen_ft = QLabel("Flowmeter \n \n   FT \n   100",flowmeter_window)
        self.tag_imagen_ft.setStyleSheet("font-weight: bold;")
        self.tag_imagen_ft.setGeometry(250, 10, 150, 100) 

        # Image CV 100
        self.image_CV_100 = QLabel(flowmeter_window)
        self.image_CV_100.setPixmap(QPixmap("images/cv_valve.png").scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_CV_100.setGeometry(75, 27, 140, 140)  
        self.tag_CV_100 = QLabel("Servo Valve \n \n   CV \n   100",flowmeter_window)
        self.tag_CV_100.setGeometry(150, 0, 100, 100)
        self.tag_CV_100.setStyleSheet("font-weight: bold;")

        # Image PT 100
        self.image_PT_100 = QLabel(flowmeter_window)
        self.image_PT_100.setPixmap(QPixmap("images/LT.png").scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_PT_100.setGeometry(40, 230, 70, 70)  
        self.tag_PT_100 = QLabel("Pressure Transmitter \n \n   PT \n   100",flowmeter_window)
        self.tag_PT_100.setGeometry(60, 200, 120, 100)
        self.tag_PT_100.setStyleSheet("font-weight: bold;")

        self.image_GP_100 = QLabel(flowmeter_window)
        self.image_GP_100.setPixmap(QPixmap("images/LT.png").scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_GP_100.setGeometry(40, 160, 70, 70)
        self.tag_GP_100 = QLabel("Pressure Gauge \n \n   PG \n   100",flowmeter_window)
        self.tag_GP_100.setGeometry(60, 130, 120, 100)
        self.tag_GP_100.setStyleSheet("font-weight: bold;")


        # Image VALVE manual 2
        self.image_valve_2 = QLabel(flowmeter_window)
        self.image_valve_2.setPixmap(QPixmap("images/valve.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_valve_2.setGeometry(50, 303, 40, 40)  

        # Image VALVE manual 3
        self.image_valve_3 = QLabel(flowmeter_window)
        self.image_valve_3.setPixmap(QPixmap("images/valve_v.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_valve_3.setGeometry(193, 200, 40, 40)  

        # Image conector output
        self.image_input_s1 = QLabel(flowmeter_window)
        self.image_input_s1.setPixmap(QPixmap("images/conector_output.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_input_s1.setGeometry(170, 248, 150, 150)  
        self.tag_image_input_s1 = QLabel("103 | TK-003", flowmeter_window)
        self.tag_image_input_s1.setGeometry(190, 273, 75, 100)  
        self.tag_image_input_s1.setStyleSheet("font-weight: bold;")

        # Image conector output 2
        self.image_output_s2 = QLabel(flowmeter_window)
        self.image_output_s2.setPixmap(QPixmap("images/conector_output.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_output_s2.setGeometry(270, 200, 150, 150)  
        self.tag_image_output_s2 = QLabel("102 | TK-002", flowmeter_window)
        self.tag_image_output_s2.setGeometry(280, 225, 75, 100)  
        self.tag_image_output_s2.setStyleSheet("font-weight: bold;")

        # Flow rate
        self.rate_flow = QLabel("0.0", flowmeter_window)
        self.rate_flow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rate_flow.setGeometry(300, 60, 100, 30)
        self.rate_flow.setStyleSheet("background-color: white; border: 1px solid black;color: black;")
        

        main_container_top.addWidget(flowmeter_window,1)




        # Tank window
        tank_window = QFrame()
        tank_window.setMinimumSize(300, 200)
        tank_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Level Sensor Image
        self.label_sensor_level = QLabel(tank_window)
        self.label_sensor_level.setPixmap(QPixmap("images/LT.png").scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio))
        self.label_sensor_level.setGeometry(115, 110, 70, 70)  

        self.imagen_fondo = QLabel(tank_window)
        self.imagen_fondo.setPixmap(QPixmap("images/tk-001.png").scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.imagen_fondo.setGeometry(-00, 130, 250, 250)
        
        self.imagen_fondo.mousePressEvent = lambda event: self.show_parameters_tank(self.imagen_fondo, "Parameters - Tank")
        
        self.tag_imagen6 = QLabel("Tank | TK-001",tank_window)
        self.tag_imagen6.setGeometry(90, 335, 150, 20) 
        self.tag_imagen6.setStyleSheet("font-weight: bold;")

        self.value_tank = QLabel("0.0", tank_window)
        self.value_tank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_tank.setGeometry(185, 120, 100, 30)
        self.value_tank.setStyleSheet("background-color: white; border: 1px solid black;color: black;")
        self.tag_imagen5 = QLabel("     Level Transmitter \n \n LT \n 101",tank_window)
        self.tag_imagen5.setStyleSheet("font-weight: bold;")
        self.tag_imagen5.setGeometry(140, 75, 150, 100) 



        # Image 1.1 (VDF)
        self.image_CV_102 = QLabel(tank_window)
        self.image_CV_102.setPixmap(QPixmap("images/cv_valve.png").scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_CV_102.setGeometry(190, 210, 140, 140)  
        self.tag_image_CV_102 = QLabel("Servo Valve \n \n   CV \n   102", tank_window)
        self.tag_image_CV_102.setStyleSheet("font-weight: bold;")
        self.tag_image_CV_102.setGeometry(265, 185, 120, 100)  

        # Image output 3
        self.image_output_s3 = QLabel(tank_window)
        self.image_output_s3.setPixmap(QPixmap("images/conector_output.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        self.image_output_s3.setGeometry(290, 250, 150, 150)  
        self.tag_image_output_s3 = QLabel("102 | TK-002", tank_window)
        self.tag_image_output_s3.setGeometry(300, 275, 75, 100)  
        self.tag_image_output_s3.setStyleSheet("font-weight: bold;")


        self.level_tank = i_level_tank(parent=tank_window)
        self.level_tank.move(135, 210)
        main_container_top.addWidget(tank_window,1)


        # PID window
        pid_window = pidwindow()
        pid_window.setMaximumSize(250, 300)
        pid_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pid_window.setFrameShape(QFrame.Shape.Box)
        pid_window.setFrameShadow(QFrame.Shadow.Raised)
        pid_window.setLineWidth(2)

        pid_content = QVBoxLayout(pid_window)
        pid_content.setContentsMargins(10, 10, 10, 10)
        pid_content.setSpacing(15)
        pid_content.setAlignment(Qt.AlignmentFlag.AlignTop)

        pid_title = QLabel("PID parameters")
        pid_title.setFont(QFont("Arial", 14))
        pid_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pid_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pid_content.addWidget(pid_title)

        # PID parameters window
        valor_style = "background-color: white; border: 1px solid gray; padding: 2px 6px;"
        layout_parameters_pid = QGridLayout()
        layout_parameters_pid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_parameters_pid.setHorizontalSpacing(10)

        def pid_create_parameter(pid_name, pid_value, pid_unit):
            pid_name_label = QLabel(pid_name)
            pid_name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            pid_name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            pid_value_label = QLabel(pid_value)
            pid_value_label.setMinimumWidth(60)
            pid_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_value_label.setStyleSheet("background-color: white; border: 1px solid black;color: black;")
            pid_value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            pid_unit_label = QLabel(pid_unit)
            pid_unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            pid_unit_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            return pid_name_label, pid_value_label, pid_unit_label

        pid_name1_label, self.pid_value1_label, pid_unit1_label = pid_create_parameter("SP:", "0.00", "cm")
        pid_name2_label, self.pid_value2_label, pid_unit2_label = pid_create_parameter("PV:", "0.00", "cm")

        self.value_sv_level = self.pid_value1_label
        self.value_pv_level = self.pid_value2_label

        

        layout_parameters_pid.addWidget(pid_name1_label, 0, 0)
        layout_parameters_pid.addWidget(self.pid_value1_label, 0, 1)
        layout_parameters_pid.addWidget(pid_unit1_label, 0, 2)

        layout_parameters_pid.addWidget(pid_name2_label, 1, 0)
        layout_parameters_pid.addWidget(self.pid_value2_label, 1, 1)
        layout_parameters_pid.addWidget(pid_unit2_label, 1, 2)

        pid_content.addLayout(layout_parameters_pid)

        # AUTO MODE 
        self.automatic_button = QPushButton("Automatic")
        self.manual_start_button = QPushButton("START")
        self.manual_stop_button = QPushButton("STOP")

        for b in (self.automatic_button, self.manual_start_button, self.manual_stop_button):
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setMinimumHeight(20)
            b.setMaximumWidth(200)    

        
        self.automatic_button.setStyleSheet("background-color: none;")

        self.manual_start_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;  /* Azul */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)

        self.manual_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;  /* Rojo */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)




        frame_auto = QFrame()
        frame_auto.setFrameShape(QFrame.Shape.Box)
        frame_auto.setLineWidth(1)

        layout_auto = QVBoxLayout(frame_auto)
        layout_auto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_auto.setContentsMargins(5, 5, 5, 5)
        layout_auto.setSpacing(10)

        layout_auto.addWidget(self.automatic_button)
        layout_auto.addWidget(self.manual_start_button)
        layout_auto.addWidget(self.manual_stop_button)
        layout_auto.addStretch(1)

        pid_content.addWidget(frame_auto)

        # MANUAL MODE
        self.maual_button = QPushButton("Manual")
        self.maual_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.maual_button.setMinimumHeight(20)
        self.maual_button.setMaximumWidth(200)

        frame_manual = QFrame()
        frame_manual.setFrameShape(QFrame.Shape.Box)
        frame_manual.setLineWidth(1)

        layout_manual = QVBoxLayout(frame_manual)
        layout_manual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_manual.setContentsMargins(5, 5, 5, 5)
        layout_manual.addStretch(1)
        layout_manual.addWidget(self.maual_button)
        layout_manual.addStretch(1)

        pid_content.addWidget(frame_manual)

        # Activation logic
        self.automatic_button.setStyleSheet("background-color: none;") ##2196F3 
        self.maual_button.setStyleSheet("background-color: none;")
        self.manual_start_button.setEnabled(False)
        self.manual_stop_button.setEnabled(False)
        self.automatic_mode = False
        self.manual_mode = False

        def activate_automatic():

            global e_close_window

            self.automatic_mode = True
            self.manual_mode = False
            e_close_window = True
            self.automatic_button.setStyleSheet("""background-color:  #04fa04; font-weight: bold; color: black;""")
            self.maual_button.setStyleSheet("background-color: none;")
            self.manual_start_button.setEnabled(True)
            self.manual_stop_button.setEnabled(True)
            

        def activate_manual():

            
            self.automatic_mode = False
            self.manual_mode = True
            self.automatic_button.setStyleSheet("background-color: none;")
            self.maual_button.setStyleSheet("""background-color:  #04fa04; font-weight: bold; color: black;""")
            self.manual_start_button.setEnabled(False)
            self.manual_stop_button.setEnabled(False)

        self.automatic_button.clicked.connect(activate_automatic)
        self.automatic_button.clicked.connect(self.plc_auto_mode)
        self.automatic_button.clicked.connect(self.process_manual_auto_mode_send)

        self.maual_button.clicked.connect(activate_manual)
        self.maual_button.clicked.connect(self.plc_manual_mode)
        self.maual_button.clicked.connect(self.process_manual_auto_mode_send)


        main_container_top.addWidget(pid_window, 1)
        main_layout.addLayout(main_container_top)


        #------------------------------------------------------------------PID-TF Simulation WindoW-------------------------------------------------------------------------
        self.pid_s_parameters = {}

        simulation_window = QFrame()
        simulation_window.setMaximumSize(250, 300)
        simulation_window.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        simulation_window.setFrameShape(QFrame.Shape.Box)
        simulation_window.setFrameShadow(QFrame.Shadow.Raised)
        simulation_window.setLineWidth(2)

        simulation_content = QVBoxLayout(simulation_window)
        simulation_content.setContentsMargins(10, 10, 10, 10)
        simulation_content.setSpacing(10)
        simulation_content.setAlignment(Qt.AlignmentFlag.AlignCenter)  



        # Title
        simulation_title = QLabel("Experimental/Simulated")
        simulation_title.setFont(QFont("Arial", 14))
        
        simulation_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        simulation_content.addWidget(simulation_title, alignment=Qt.AlignmentFlag.AlignCenter)
        simulation_content.addStretch(1)

        # PID simulation parameter inputs
        for pid_name, pid_s_unit in zip(['Kd', 'Kp', 'Ki', 'Kv', 'A'],
                                ['s', '-', '1/s', 'm³/s·m', 'm²']):
            m_line = QHBoxLayout()
            m_line.setAlignment(Qt.AlignmentFlag.AlignCenter)  

            pid_s_label = QLabel(pid_name + ":")
            pid_s_label.setFixedWidth(30)

            pid_s_input = QLineEdit()
            pid_s_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_s_input.setPlaceholderText("0.0")
            pid_s_input.setFixedWidth(70)

            pid_s_label_unit = QLabel(pid_s_unit)
            pid_s_label_unit.setFixedWidth(50)

            m_line.addWidget(pid_s_label)
            m_line.addWidget(pid_s_input)
            m_line.addWidget(pid_s_label_unit)

            simulation_content.addLayout(m_line)

            self.pid_s_parameters[pid_name] = pid_s_input


            


        # Graph button
        simulate_button = QPushButton("Start Simulation")
        simulate_button.setStyleSheet("""background-color:  #04fa04; font-weight: bold; color: black;""") ##2196F3
        
        simulate_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        simulate_button.setMinimumHeight(20)
        simulate_button.setMinimumWidth(200)

        
        simulate_button.clicked.connect(self.start_pid_simulation)

        # Compare button
        compare_button = QPushButton("Start Compare")
        compare_button.setStyleSheet("""background-color:  #04fa04; font-weight: bold; color: black;""") ##2196F3
        
        compare_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        compare_button.setMinimumHeight(20)
        compare_button.setMinimumWidth(200)

        
        compare_button.clicked.connect(self.start_comparison)




        simulation_content.addStretch(1)

        simulation_content.addWidget(simulate_button, alignment=Qt.AlignmentFlag.AlignCenter)
        simulation_content.addWidget(compare_button, alignment=Qt.AlignmentFlag.AlignCenter)
        simulation_content.addStretch(1)
        main_container_top.addWidget(simulation_window, 1)
        


        self.a_flow_1 = flow_widget(
            direction="right", 
            start_offset=10, 
            length=100, 
            head_length=20,    
            head_width=6,      
            line_width=2,      
            color=Qt.GlobalColor.blue,
            parent=self 
        )
        self.a_flow_1.move(150, 270)
        self.a_flow_1.lower()


        self.a_flow_2 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=20, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  
            parent=self
        )
        self.a_flow_2.move(315, 250)
        self.a_flow_2.lower()

        self.a_flow_2_1 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=105, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  
            parent=self
        )
        self.a_flow_2_1.move(375, 250)
        self.a_flow_2_1.lower()


        self.a_flow_3 = flow_widget(
            direction="up", 
            start_offset=20, 
            length=55, 
            head_length=1,    
            head_width=1,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  
            parent=self
        )
        self.a_flow_3.move(383, 265)
        self.a_flow_3.lower()

        self.a_flow_3_0 = flow_widget(
            direction="up", 
            start_offset=20, 
            length=130, 
            head_length=1,    
            head_width=1,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_3_0.move(650, 140)
        self.a_flow_3_0.lower()

        self.a_flow_3_1 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=250, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_3_1.move(388, 307)
        self.a_flow_3_1.lower()

        self.a_flow_3_2 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=20, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_3_2.move(480, 250)
        self.a_flow_3_2.lower()



        self.a_flow_3_2 = flow_widget( # input tank
            direction="right", 
            start_offset=20, 
            length=520, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  
            parent=self
        )
        self.a_flow_3_2.move(480, 125)
        self.a_flow_3_2.lower()

        self.a_flow_3_3 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=100, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_3_3.move(655, 258)
        self.a_flow_3_3.lower()

        self.a_flow_3_4 = flow_widget(
            direction="up", 
            start_offset=20, 
            length=124, 
            head_length=1,    
            head_width=1,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_3_4.move(475, 140)
        self.a_flow_3_4.lower()

        self.a_flow_3_5 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=20, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # GAUGUE P
            parent=self
        )
        self.a_flow_3_5.move(480, 180)
        self.a_flow_3_5.lower()

        self.a_flow_5 = flow_widget(
            direction="down", 
            start_offset=20, 
            length=60, 
            head_length=20,    
            head_width=6,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # input tank 
            parent=self
        )
        self.a_flow_5.move(995, 130)
        self.a_flow_5.lower()


        self.a_flow_6 = flow_widget(
            direction="right", 
            start_offset=20, 
            length=150, 
            head_length=0,    
            head_width=0,      
            line_width=2,      
            color=Qt.GlobalColor.blue,  # Color diferente
            parent=self
        )
        self.a_flow_6.move(1050, 308)
        self.a_flow_6.lower()



        self.a_flow_r_1 = flow_electric(
            direction="up",
            start_offset=20,
            length=250,
            head_length=0,
            head_width=0,
            line_width=2,
            color=Qt.GlobalColor.red,
            dash_pattern=[5, 3],  
            parent=self
        )
        self.a_flow_r_1.move(277, 10)
        self.a_flow_r_1.lower()

        self.a_flow_r_2 = flow_electric(
            direction="right",
            start_offset=20,
            length=770,
            head_length=0,
            head_width=0,
            line_width=2,
            color=Qt.GlobalColor.red,
            dash_pattern=[5, 3],  
            parent=self
        )
        self.a_flow_r_2.move(281, -10)
        self.a_flow_r_2.lower()

        self.a_flow_r_3 = flow_electric(
            direction="down",
            start_offset=20,
            length=110,
            head_length=0,
            head_width=0,
            line_width=2,
            color=Qt.GlobalColor.red,
            dash_pattern=[5, 3],  
            parent=self
        )
        self.a_flow_r_3.move(1050, -0)
        self.a_flow_r_3.lower()











        #------------------------------------------------------------------scada graph-------------------------------------------------------------------------
        
        self.scada_graph = g_pid_graph()
        main_layout.addWidget(self.scada_graph)



    def plc_auto_mode(self):
            self.plc_auto_manual_mode = True

    def plc_manual_mode(self):
            self.plc_auto_manual_mode = False

    def process_manual_auto_mode_send(self):

        global global_send_MB, mode_send_bool
        global f_bool_write
                
        try:  
            f_bool_write[1] = self.plc_auto_manual_mode
            global_send_MB = True
            mode_send_bool = True
                    
                    
        except ValueError:
            QMessageBox.warning(self, "Error", "All fields must be valid numbers.")  


#--------------------------------------------------------------Alternating pump status images---------------------------------------------------------------------------------
    def toggle_pump_image(self):  #self.)
        global bool_r_0 
        if bool_r_0 == True:
            self.label_pump.setPixmap(QPixmap("images/pump-pid-x.png").scaled(80, 120, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.label_pump.setPixmap(QPixmap("images/pump-pid-x.png").scaled(80, 120, Qt.AspectRatioMode.KeepAspectRatio))

    def read_sensors(self):

        global float_r_0 #PID SV 
        global float_r_3 ##VDF HZ MANUAL
        global float_r_8 #PID PV LEVEL
        global float_r_9 #PID CV HZ 
        global float_r_10 #FLOW
        global plc_in_pid_sv_level
        global plc_in_pid_pv_level
        global plc_in_pid_cv_hz

        plc_in_pid_sv_level = float_r_0
        plc_in_vdf_hz_manual = float_r_3
        plc_in_pid_pv_level = float_r_8
        plc_in_pid_cv_hz = float_r_9
        plc_in_flujo = float_r_10

        # Level-based color
        if plc_in_pid_pv_level < 80:
            color = "blue"
        
        else:
            color = "red"


        self.value_sv_level.setText(f"{plc_in_pid_sv_level:.1f}")
        self.value_pv_level.setText(f"{plc_in_pid_pv_level:.1f}")
        self.level_tank.setNivel(plc_in_pid_pv_level, color)
        self.value_tank.setText(f"{plc_in_pid_pv_level:.1f} cm")
        self.value_pump.setText(f"{plc_in_pid_cv_hz:.1f} Hz")  
        self.rate_flow.setText(f"{plc_in_flujo:.1f} m3/h")   
    
    def start_pid_simulation(self):
            try:
                # Extract text values, use "0" if empty, and convert to float
                Kd = float(self.pid_s_parameters['Kd'].text().strip() or "0")
                Kp = float(self.pid_s_parameters['Kp'].text().strip() or "0")
                Ki = float(self.pid_s_parameters['Ki'].text().strip() or "0")
                Kv = float(self.pid_s_parameters['Kv'].text().strip() or "0")
                A  = float(self.pid_s_parameters['A'].text().strip() or "0")


                # Transfer function equation in the Laplace domain
                num = [Kd, Kp, Ki]
                den = [Kd + A, Kp + Kv, Ki]
                system = signal.TransferFunction(num, den)

                # Simulate step response
                t_sim = np.linspace(0, 60, 61)
                _, y_sim = signal.step(system, T=t_sim)


                self.s_graph_window = simulation_trend(t_sim, y_sim)
                self.s_graph_window.show()  

            except ValueError:
                print("Error simulation: the fields must contain valid numeric values.")


    #--------------------------------------------------------------start comparison------------------------------------------------------------------------------------

    def start_comparison(self):
            try:
                
                self.launch_comparison_window = comparison_graph(self)
                self.launch_comparison_window.show()  

            except ValueError:
                print("Error comparison: the fields must contain valid numeric values.")




    #------------------------------------------------------------Parameters for each image window----------------------------------------------------------------------

    def show_parameters_tank(self, widget, title):
        window = QWidget()
        window.setWindowTitle(title)
        window.setWindowIcon(QIcon("images/tanque.png"))
        window.setFixedSize(350, 150)
        layout = QVBoxLayout(window)
        label = QLabel(f"Parameters: {title}")
        label.setWordWrap(True)
        layout.addWidget(label)

        global_pos = widget.mapToGlobal(widget.rect().topRight())
        window.move(global_pos.x() + 10, global_pos.y())

        self.parameters_window.append(window)
        window.show()

    # -------------------------------------------------------------------Input Hz - frequency inverter - Manual ----------------------------------------------------------------------
    def show_parameters_pump(self, widget, title):

        pump_parameters_window = QWidget()
        pump_parameters_window.setWindowTitle(title)
        pump_parameters_window.setWindowIcon(QIcon("images/tanque.png"))
        pump_parameters_window.setFixedSize(350, 150) 
        layout = QVBoxLayout(pump_parameters_window)

        

        # Input Hz - frequency inverter

        global float_r_4
        layout_frecuency = QHBoxLayout()
        und_Hz = QLabel("Frecuency (Hz):")
        self.edit_frecuency = QLineEdit(f"{float_r_4:.2f}")

        self.edit_frecuency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_frecuency.addWidget(und_Hz)
        layout_frecuency.addWidget(self.edit_frecuency)
        layout.addLayout(layout_frecuency)





        # Buttons Start-Stop
        layout_button = QHBoxLayout()
        self.manual_start_button = QPushButton("Start")
        self.manual_start_button.setStyleSheet("""
            QPushButton {
                background-color: "#04fa04";  /* Azul */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: '#7f7f7f';
            }
        """)
        self.manual_stop_button = QPushButton("Stop")
        self.manual_stop_button.setStyleSheet("""
            QPushButton {
                background-color: '#d62728';  /* Azul */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: '#7f7f7f';
            }
        """)
        layout_button.addWidget(self.manual_start_button)
        layout_button.addWidget(self.manual_stop_button)
        layout.addLayout(layout_button)

        # Condition: enable only if automatic_mode is False
        
        if self.manual_mode:
            manual_mode_enabled = True
        else:
            manual_mode_enabled = False

        self.edit_frecuency.setEnabled(manual_mode_enabled)
        self.manual_start_button.setEnabled(manual_mode_enabled)
        self.manual_stop_button.setEnabled(manual_mode_enabled)
        self.manual_start_button.clicked.connect(self.start_motor)
        self.manual_stop_button.clicked.connect(self.stop_motor)
        self.manual_start_button.clicked.connect(self.process_manual_hz_send)    
        self.manual_stop_button.clicked.connect(self.process_manual_hz_send) 
        
        # Window location
        global_pos = widget.mapToGlobal(widget.rect().topRight())
        pump_parameters_window.move(global_pos.x() + 10, global_pos.y())

        
        if self.manual_mode: 
            self.parameters_window.append(pump_parameters_window)
            pump_parameters_window.show()
        else:
            QTimer.singleShot(100,pump_parameters_window.close) 

    def start_motor(self):
        self.pump_motor = True

    def stop_motor(self):
        self.pump_motor = False
    
        
        


    def process_manual_hz_send(self):

            global global_send_MB, mode_send_float, mode_send_bool
            global f_float_write, f_bool_write
            
            try:
                f_float_write[4] = float(self.edit_frecuency.text())    
                f_bool_write[0] = self.pump_motor
                global_send_MB = True
                mode_send_float = True
                mode_send_bool = True
                print("Pump started")
                
                
            except ValueError:
                QMessageBox.warning(self, "Error", "Pump failed to start")


#------------------------------------------------------------------------Real-time data from PID------------------------------------------------------------------------------
class real_time_pid_data:
    def __init__(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate)
        self.timer.start(1000)

    def generate(self):

        
        global plc_in_pid_pv_level, plc_in_pid_sv_level, plc_in_pid_cv_hz

        pv = plc_in_pid_pv_level
        sv = plc_in_pid_sv_level
        cv = plc_in_pid_cv_hz
        insert_global_data(pv, sv, cv)


#------------------------------------------------------------------------PID parameters window--------------------------------------------------------------------------------
class pidwindow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialogo = pid_parameters_window(self)
            dialogo.exec()


    

class pid_parameters_window(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PID parameters")
        self.setFixedSize(250, 230)

        

        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        
        #global f_float_read 

        self.edit_sv = QLineEdit(f"{float_r_0:.2f}")
        self.edit_kp = QLineEdit(f"{float_r_1:.2f}")
        self.edit_ti = QLineEdit(f"{float_r_2:.2f}")
        self.edit_td = QLineEdit(f"{float_r_3:.2f}")

        for edit in (self.edit_sv, self.edit_kp, self.edit_ti, self.edit_td):
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addRow("SP:", self.edit_sv)
        layout.addRow("Kp:", self.edit_kp)
        layout.addRow("Ti:", self.edit_ti)
        layout.addRow("Td:", self.edit_td)

        # Buttons
        self.pid_button = QDialogButtonBox()
        self.pid_button_send = self.pid_button.addButton("Send", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = self.pid_button.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)

        self.pid_button_send.clicked.connect(self.pid_send_process)
        self.cancel_button.clicked.connect(self.reject)

        layout.addRow(self.pid_button)
        self.setLayout(layout)

    
    
    def pid_send_process(self):
        
        
        global global_send_MB,mode_send_float
        global f_float_write
        

        try:
            f_float_write[0] = float(self.edit_sv.text())
            f_float_write[1] = float(self.edit_kp.text())
            f_float_write[2] = float(self.edit_ti.text())
            f_float_write[3] = float(self.edit_td.text())

            global_send_MB = True
            mode_send_float = True
            
            QMessageBox.information(self, "Parameters", "Parameters assigned successfully")

        except ValueError:
            QMessageBox.warning(self, "Error", "All fields must be valid numbers")




#########################-------------------------------------------------Simulation Window------------------------------------------------################################

class simulation_trend(QDialog):
    def __init__(self, t_sim, y_sim, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulation - Tank Response")
        self.setWindowIcon(QIcon("images/tanque.png")) 
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.resize(1000, 500)

        self.t_sim = t_sim
        self.y_sim = y_sim

        layout = QVBoxLayout(self)


        # Excel export button
        self.export_button = QPushButton("Export to Excel")
        self.export_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.export_button.setMinimumHeight(20)
        self.export_button.setMaximumWidth(200)
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)



        # Custom time axis
        axis = TimeAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(background='k', axisItems={'bottom': axis}) 
        layout.addWidget(self.plot_widget)

        self.plot_widget.setTitle("<span style='color:white; font-size:15pt;'>Tank Level - Step</span>")
        self.plot_widget.setLabel('left', 'Tank Level')
        self.plot_widget.setLabel('bottom', 'System Time')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='cyan', width=2))
        self.plot_widget.setYRange(0, max(self.y_sim) * 1.2)

        # Data initialization
        self.x_data = []
        self.y_data = []
        self.index = 0
        self.start_time = time.time()

        # Timer to update graph
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        if self.index < len(self.t_sim):
            current_timestamp = self.start_time + self.t_sim[self.index]
            self.x_data.append(current_timestamp)
            self.y_data.append(self.y_sim[self.index])
            self.curve.setData(self.x_data, self.y_data)
            self.plot_widget.setXRange(self.x_data[0], self.x_data[-1])
            self.index += 1
        else:
            self.timer.stop()
            print("Simulation completed.")

    def export_to_excel(self):
        try:
            suggested_name = datetime.now().strftime("simulation_level_%Y-%m-%d_%H-%M-%S.xlsx")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel file",
                suggested_name,
                "Excel files (*.xlsx)"
            )
            if file_path:
                timestamps = [datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") for ts in self.x_data]
                df = pd.DataFrame({'DateTime': timestamps, 'Level': self.y_data})
                df.to_excel(file_path, index=False)
                print(f"File exported successfully: {file_path}")
            else:
                print("Export canceled.")
        except ImportError:
            print("Error_Simulation_W: package 'openpyxl'")
        except Exception as e:
            print(f"Error_Simulation_W: {e}")




#########################-------------------------------------------------Comparison Graph Window------------------------------------------------################################

class comparison_graph(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Graphic from Excel")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setGeometry(200, 200, 1200, 800)

        self.df_original = pd.DataFrame()
        self.current_df = pd.DataFrame()

        # Widgets
        self.graphWidget = pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.button_load = QPushButton("📂 Load Excel")
        self.button_export = QPushButton("📤 Export Excel")
        self.button_plot_range = QPushButton("📈 Graph Range")

        # Configure date/time editors
        self.startDateEdit = QDateTimeEdit()
        self.endDateEdit = QDateTimeEdit()
        for editor in (self.startDateEdit, self.endDateEdit):
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setCalendarPopup(True)
            editor.setTimeSpec(Qt.TimeSpec.LocalTime)
            editor.setMinimumWidth(150)

        # Top layout (controls)
        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.button_load)
        controlLayout.addWidget(QLabel("Start:"))
        controlLayout.addWidget(self.startDateEdit)
        controlLayout.addWidget(QLabel("End:"))
        controlLayout.addWidget(self.endDateEdit)
        controlLayout.addWidget(self.button_plot_range)
        controlLayout.addWidget(self.button_export)

        # General layout
        layout = QVBoxLayout()
        layout.addLayout(controlLayout)
        layout.addWidget(self.graphWidget)

        self.setLayout(layout)

        # Events
        self.button_load.clicked.connect(self.load_excel)
        self.button_plot_range.clicked.connect(self.plot_range)
        self.button_export.clicked.connect(self.export_filtered_data)

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel file", "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            try:
                # Read file
                df = pd.read_excel(file_path)
                
                # Remove rows with missing values
                df = df.dropna()
                
                # Convert first column to datetime
                time_col = df.columns[0]
                df[time_col] = pd.to_datetime(df[time_col])
                
                # Order by time
                df = df.sort_values(by=time_col)
                
                # Store data
                self.df_original = df
                self.current_df = df.copy()
                
                # Set initial ranges
                min_time = df[time_col].min()
                max_time = df[time_col].max()
                
                self.startDateEdit.setDateTime(QDateTime(min_time))
                self.endDateEdit.setDateTime(QDateTime(max_time))
                
                # Graph all data
                self.plot_data(df)
                
            except Exception as e:
                print("Error loading file:", e)
                self.show_error_message(f"Error loading file:\n{str(e)}")

    def plot_data(self, df):
        self.graphWidget.clear()
        self.graphWidget.addLegend()

        if df.empty:
            return
            
        # Get time column
        time_col = df.columns[0]
        time_data = df[time_col]
        
        # Convert to timestamp (seconds since epoch)
        x = time_data.astype('int64') // 10**9
        
        # Plot series colors
        num_series = len(df.columns) - 1
        colors = [
            "#fbff00", "#08fc00", "#fa0404", '#d62728', 
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            "#f3f30b", "#0dd4eb"
        ]
        
        # Plot series
        for i, col in enumerate(df.columns[1:]):
            color = colors[i % len(colors)]
            self.graphWidget.plot(
                x=x, 
                y=df[col],
                pen=pg.mkPen(color=color, width=2),
                name=col,
                symbol='o',
                symbolSize=0,
                symbolBrush=color
            )
        
        # Configure labels and grid
        self.graphWidget.setLabel('bottom', 'Tiempo')
        self.graphWidget.setLabel('left', 'Valor')
        self.graphWidget.showGrid(x=True, y=True)
        
        # Set X-axis range based on data
        min_x = x.min()
        max_x = x.max()
        self.graphWidget.setXRange(min_x, max_x, padding=0.05)
        
        # Store current data
        self.current_df = df

    # Plot selected range
    def plot_range(self):
        if self.df_original.empty:
            return

        start_dt = self.startDateEdit.dateTime().toPyDateTime()
        end_dt = self.endDateEdit.dateTime().toPyDateTime()
        
        time_col = self.df_original.columns[0]
        mask = (
            (self.df_original[time_col] >= start_dt) & 
            (self.df_original[time_col] <= end_dt)
        )
        df_filtered = self.df_original.loc[mask]
        
        if not df_filtered.empty:
            self.plot_data(df_filtered)
        else:
            self.show_warning_message("No data available in the selected range")

    # Save data
    def export_filtered_data(self):
        if self.current_df.empty:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Data", "", 
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.current_df.to_csv(file_path, index=False)
                else:
                    self.current_df.to_excel(file_path, index=False)
                
                self.show_info_message(f"Datos exportados exitosamente a:\n{file_path}")
            except Exception as e:
                self.show_error_message(f"Error al exportar:\n{str(e)}")

    def show_error_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.exec()

    def show_warning_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(message)
        msg.setWindowTitle("Warning")
        msg.exec()

    def show_info_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle("Information")
        msg.exec()


#--------------------------------------------------Real-Time PID Monitoring Overview Graph (PV, SP, CV)-----------------------------------------------------------------

class g_pid_graph(QWidget):
    def __init__(self):
        super().__init__()
        self.paused = False
        self.user_moved_cursor = False
        
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': DateAxisItem()})
        self.plot_widget.setTitle('<span style="color:white; font-size:14pt;">REAL-TIME LEVEL CONTROL SYSTEM</span>')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.plot_widget.setLabel("left", "Value")
        self.plot_widget.setLabel("bottom", "Date and Time")

        self.curve_pv = self.plot_widget.plot(pen=pg.mkPen("y", width=2), name="PV")
        self.curve_sp = self.plot_widget.plot(pen=pg.mkPen("g", width=2), name="SP")
        self.curve_out = self.plot_widget.plot(pen=pg.mkPen("r", width=2), name="CV")

        self.v_line = pg.InfiniteLine(angle=90, movable=True, pen=pg.mkPen('c', width=1))
        self.v_line.sigPositionChanged.connect(self.on_user_cursor_move)
        self.plot_widget.addItem(self.v_line)
        self.v_line.setVisible(True)

        self.value_label = QLabel("Cursor: ")

        self.real_time_check = QCheckBox("Show Real Time (last 60s)")
        self.range_check = QCheckBox("Show by Time Range")
        self.real_time_check.setChecked(True)

        self.real_time_check.stateChanged.connect(self.on_mode_change)
        self.range_check.stateChanged.connect(self.on_mode_change)

        self.start_time_edit = QDateTimeEdit()
        self.end_time_edit = QDateTimeEdit()
        for widget in [self.start_time_edit, self.end_time_edit]:
            widget.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
            widget.setCalendarPopup(True)

        now = QDateTime.currentDateTime()
        self.start_time_edit.setDateTime(now.addSecs(-300))
        self.end_time_edit.setDateTime(now)

        self.start_time_edit.dateTimeChanged.connect(self.update_plot)
        self.end_time_edit.dateTimeChanged.connect(self.update_plot)

        self.pause_button = QPushButton("⏸ Pause Viewing")
        self.pause_button.clicked.connect(self.toggle_pause)

        self.export_button = QPushButton("📤 Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)

        # Layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.real_time_check)
        controls_layout.addWidget(self.range_check)
        controls_layout.addWidget(QLabel("Start:"))
        controls_layout.addWidget(self.start_time_edit)
        controls_layout.addWidget(QLabel("End:"))
        controls_layout.addWidget(self.end_time_edit)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.addLayout(controls_layout)
        layout.addWidget(self.value_label)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)

        self.timestamps = []
        self.pv = []
        self.sv = []
        self.cv = []

        self.update_plot()
    
    # Graph display mode: real-time / history
    def on_mode_change(self):
        sender = self.sender()
        if sender == self.real_time_check and self.real_time_check.isChecked():
            self.range_check.setChecked(False)
        elif sender == self.range_check and self.range_check.isChecked():
            self.real_time_check.setChecked(False)
        self.user_moved_cursor = False
        self.update_plot()

    # Resume/Pause visualization
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.setText("▶ Resume visualization" if self.paused else "⏸ Pause visualization")

    # Time range to be displayed on the graph
    def update_plot(self):
        if self.paused:
            return

        now = time.time()

        if self.real_time_check.isChecked():
            ts_start = now - 60
            ts_end = now
        elif self.range_check.isChecked():
            ts_start = self.start_time_edit.dateTime().toSecsSinceEpoch()
            ts_end = self.end_time_edit.dateTime().toSecsSinceEpoch()
            if ts_end <= ts_start:
                return
        else:
            return

        rows = query_global_data(ts_start, ts_end)
        if not rows:
            self.curve_pv.clear()
            self.curve_sp.clear()
            self.curve_out.clear()
            return

        self.timestamps, self.pv, self.sv, self.cv = zip(*rows)

        self.curve_pv.setData(self.timestamps, self.pv)
        self.curve_sp.setData(self.timestamps, self.sv)
        self.curve_out.setData(self.timestamps, self.cv)

        self.plot_widget.setXRange(self.timestamps[0], self.timestamps[-1])
        self.v_line.setBounds((self.timestamps[0], self.timestamps[-1]))

        if not self.user_moved_cursor:
            mid_time = (self.timestamps[0] + self.timestamps[-1]) / 2
            self.v_line.setPos(mid_time)

        self.on_cursor_move()


    def on_user_cursor_move(self):
        self.user_moved_cursor = True
        self.on_cursor_move()

    def on_cursor_move(self):
        if not self.timestamps:
            return
        cursor_ts = self.v_line.value()
        idx = min(range(len(self.timestamps)), key=lambda i: abs(self.timestamps[i] - cursor_ts))
        ts_str = datetime.fromtimestamp(self.timestamps[idx]).strftime("%d/%m/%Y %H:%M:%S")
        pv_val = self.pv[idx]
        sp_val = self.sv[idx]
        out_val = self.cv[idx]
        self.value_label.setText(
            f"Cursor: {ts_str} | PV: {pv_val:.2f} | SP: {sp_val:.2f} | CV: {out_val:.2f}"
        )

    # Export to excel
    def export_to_excel(self):
        if self.real_time_check.isChecked():
            now = time.time()
            ts_start = now - 60
            ts_end = now
        elif self.range_check.isChecked():
            ts_start = self.start_time_edit.dateTime().toSecsSinceEpoch()
            ts_end = self.end_time_edit.dateTime().toSecsSinceEpoch()
        else:
            return

        data = query_global_data(ts_start, ts_end)
        if not data:
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar como Excel", "", "Excel Files (*.xlsx)")
        if not filepath:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Data"
        ws.append(["DateTime", "PV", "SP", "CV"])

        for row in data:
            ts = datetime.fromtimestamp(row[0]).strftime("%d/%m/%Y %H:%M:%S")
            ws.append([ts, row[1], row[2], row[3]])

        wb.save(filepath)



#-------------------------------------------------------------Parameters screen or manual mode / 1-------------------------------------------------------------------------------
class parameters_manual_screen_1(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reserve 1")

        main_layout = QGridLayout()
        self.m_inputs = {}

        group_data = [
            {"id": "temperature", "title": "Temperature Sensor", "placeholder": "°C"},
            {"id": "pressure", "title": "Pressure Sensor", "placeholder": "bar"},
            {"id": "level", "title": "Level Sensor", "placeholder": "%"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
        ]

        number_rows = 2
        number_columns = 4
        group_width = 400
        group_height = 180

        for index, m_group in enumerate(group_data):
            grupo_id = m_group["id"]
            title = m_group["title"]
            texto_placeholder = m_group["placeholder"]

            box = QGroupBox()
            layout_group = QVBoxLayout()

            pid_s_label = QLabel(title)
            pid_s_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_s_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout_group.addWidget(pid_s_label)

            pid_s_input = QLineEdit()
            pid_s_input.setPlaceholderText(texto_placeholder)
            pid_s_input.setValidator(QDoubleValidator())
            pid_s_input.setFixedHeight(30)
            layout_group.addWidget(pid_s_input)
            self.m_inputs[grupo_id] = pid_s_input

            accept_button = QPushButton("Accept")
            cancel_button = QPushButton("Cancel")
            accept_button.setFixedWidth(90)
            cancel_button.setFixedWidth(90)

            accept_button.clicked.connect(lambda _, gid=grupo_id: self.accept_button(gid))
            cancel_button.clicked.connect(lambda _, gid=grupo_id: self.cancel_button(gid))

            layout_button = QHBoxLayout()
            layout_button.addStretch()
            layout_button.addWidget(accept_button)
            layout_button.addSpacing(10)
            layout_button.addWidget(cancel_button)
            layout_button.addStretch()

            layout_group.addLayout(layout_button)
            box.setLayout(layout_group)
            box.setFixedSize(group_width, group_height)

            m_line = index // number_columns
            m_column = index % number_columns
            main_layout.addWidget(box, m_line, m_column)

        self.setLayout(main_layout)

    def accept_button(self, grupo_id):
        value = self.m_inputs[grupo_id].text()
        print(f"[{grupo_id}] ACCEPTED. Entered value: {value}")

    def cancel_button(self, grupo_id):
        print(f"[{grupo_id}] CANCEL")








#-------------------------------------------------------------Parameters screen or manual mode / 2------------------------------------------------------------------------------
class parameters_manual_screen_2(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reserve 2")

        main_layout = QGridLayout()
        self.m_inputs = {}

        group_data = [
            {"id": "temperature", "title": "Temperature Sensor", "placeholder": "°C"},
            {"id": "pressure", "title": "Pressure Sensor", "placeholder": "bar"},
            {"id": "level", "title": "Level Sensor", "placeholder": "%"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
            {"id": "flow", "title": "Flow Sensor", "placeholder": "L/s"},
        ]

        number_rows = 2
        number_columns = 4
        group_width = 400
        group_height = 180

        for index, m_group in enumerate(group_data):
            grupo_id = m_group["id"]
            title = m_group["title"]
            texto_placeholder = m_group["placeholder"]

            box = QGroupBox()
            layout_group = QVBoxLayout()

            pid_s_label = QLabel(title)
            pid_s_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_s_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout_group.addWidget(pid_s_label)

            pid_s_input = QLineEdit()
            pid_s_input.setPlaceholderText(texto_placeholder)
            pid_s_input.setValidator(QDoubleValidator())
            pid_s_input.setFixedHeight(30)
            layout_group.addWidget(pid_s_input)
            self.m_inputs[grupo_id] = pid_s_input

            accept_button = QPushButton("Accept")
            cancel_button = QPushButton("Cancel")
            accept_button.setFixedWidth(90)
            cancel_button.setFixedWidth(90)

            accept_button.clicked.connect(lambda _, gid=grupo_id: self.accept_button(gid))
            cancel_button.clicked.connect(lambda _, gid=grupo_id: self.cancel_button(gid))

            layout_button = QHBoxLayout()
            layout_button.addStretch()
            layout_button.addWidget(accept_button)
            layout_button.addSpacing(10)
            layout_button.addWidget(cancel_button)
            layout_button.addStretch()

            layout_group.addLayout(layout_button)
            box.setLayout(layout_group)
            box.setFixedSize(group_width, group_height)

            m_line = index // number_columns
            m_column = index % number_columns
            main_layout.addWidget(box, m_line, m_column)

        self.setLayout(main_layout)

    def accept_button(self, grupo_id):
        value = self.m_inputs[grupo_id].text()
        print(f"[{grupo_id}] ACCEPTED. Entered value: {value}")

    def cancel_button(self, grupo_id):
        print(f"[{grupo_id}] CANCEL")










#-------------------------------------------------------------Main Screen - Home - General Container--------------------------------------------------------------------------
class main_screen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA")
        self.setWindowIcon(QIcon("images/tank.png")) 
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        main_layout = QVBoxLayout()

        nav_layout = QHBoxLayout() # Navigation bar
        self.home_button = QPushButton("\ud83c\udfe0 Home")
        self.home_button.setFixedHeight(40)  
        self.home_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  
        
        
        self.maual_button = QPushButton("\u2699 Manual")
        self.maual_button.setFixedHeight(40)  
        self.maual_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  



        self.parameter_button = QPushButton("\u2699 Parameters")
        self.parameter_button.setFixedHeight(40)  
        self.parameter_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)   

        nav_layout.addWidget(self.home_button)
        nav_layout.addWidget(self.maual_button)
        nav_layout.addWidget(self.parameter_button)
        
        main_layout.addLayout(nav_layout) 

        # Screens container
        self.stack = QStackedWidget()
        # Screen 1
        self.home_screen = HomeScreen()
        # Screen 2
        self.manual_screen = parameters_manual_screen_1()
        # Screen 3
        self.parametros_screen = parameters_manual_screen_2() 

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.manual_screen)
        self.stack.addWidget(self.parametros_screen)

        main_layout.addWidget(self.stack) 
        self.setLayout(main_layout)

        # Navigation buttons between screens
        self.home_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_screen))
        self.maual_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.manual_screen))
        self.parameter_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.parametros_screen))



###########################---------------------------------------PLC - data read and write threads ---------------------------------#########################################


# Launch read/write threads
threading.Thread(target=read_global_data, daemon=True).start()
threading.Thread(target=write_global_data, daemon=True).start()



############################--------------------------------- Program execution – Starts the GUI event loop---------------------------#########################################
if __name__ == "__main__":
    
    create_global_database()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    windowComparador = comparison_graph() 
    window = main_screen()
    
    simulator = real_time_pid_data()
    window.show()
    sys.exit(app.exec())



