### PySTank: An open-source Python SCADA tool for real-time tank level control of a Siemens S7-1200 PLC over Modbus TCP/IP

[![DOI](https://zenodo.org/badge/1160453236.svg)](https://doi.org/10.5281/zenodo.18904781)
-------------
#### Overview
-------------
The communication protocol implemented in PyStank is based on Modbus TCP/IP, an adaptation of the traditional industrial Modbus standard for operation over Ethernet networks using the TCP/IP stack.

This protocol follows a client-server model, where the client (typically a SCADA or HMI system) sends requests to servers (field devices such as PLCs, sensors, or actuators) via the standard port 502. Its simple structure, based on read/write functions of registers (coils, holding registers, input registers), ensures interoperability among devices from multiple manufacturers.

The proposed system is based on a closed-loop control strategy for a tank level process using industrial-grade devices. The PLC receives the analog signal from the ultrasonic level transmitter and, according to the defined setpoint, executes a PID control algorithm acting directly on a Variable Frequency Drive (VFD) to regulate pump speed. The overall logic of the level control system is shown in the flow chart (Figure 1).

<p align="center">
  <img src="https://github.com/elmergthub/pystank_an_open_source_python_scada_code_v00/blob/fc1446e5bd2977c0a202d9e8dd34f632161abc59/images/flow_chart_control.png?raw=true" width="40%" alt="Block diagram of the tank level control system">
  <br>
  <b>Figure 1.</b> Block diagram of the tank level control system.
</p>


-------------
#### Features

-------------
The software architecture is presented in Figure 2 to illustrate the main functional modules and their interrelationships. Interaction diagrams are also provided to offer a more detailed view of the design and the operational flow of each key functionality.
The primary role of the software is to operate as a communication bridge between the SCADA system (user interface) and the PLC. A schematic representation of the functional blocks FC, OB, FB, and DB used for process management is included, specifically for level PID control en la figura 03.

<p align="center">
  <img src="https://github.com/elmergthub/pystank_an_open_source_python_scada_code_v00/blob/8a8713daf093489fc005f0f54c53e45cbff7d0a1/images/System_architecture.png?raw=true" width="100%" alt="System Architecture Overview">
  <br>
  <b>Figure 2.</b> System Architecture Overview.
</p>


<p align="center">
  <img src="https://github.com/elmergthub/pystank_an_open_source_python_scada_code_v00/blob/8a8713daf093489fc005f0f54c53e45cbff7d0a1/images/Architecture-modbus.png?raw=true" width="100%" alt="PySTank Client–Server Configuration over Modbus TCP/IP">
  <br>
  <b>Figure 3.</b> PySTank Client–Server Configuration over Modbus TCP/IP.
</p>


-------------
The graphical interface is subsequently presented figura 04, enabling real-time data visualization and access to historical trends stored in a SQLite database. In addition, the interface includes a control panel for operating the level PID loop in manual or automatic mode, as well as for configuring its parameters. All functionalities are implemented through PyQt6 Signals and developed entirely in Python

<p align="center">
  <img src="https://github.com/elmergthub/pystank_an_open_source_python_scada_code_v00/blob/8a8713daf093489fc005f0f54c53e45cbff7d0a1/images/scada_main.png?raw=true" width="100%" alt="Main interface of the SCADA framework developed in PyQt6">
  <br>
  <b>Figure 3.</b> Main interface of the SCADA framework developed in PyQt6
</p>

#### Video Demonstration

A demonstration of the SCADA system for tank level PID control can be viewed here:

https://youtu.be/aXO-hsBcNxE?si=bIGZbm5S7Tx_OzEk

The video shows the graphical interface, real-time monitoring of the process variables (PV, SP, CV), and communication with the S7-1200 PLC using Modbus TCP/IP.


### System Requirements
#### Hardware

    PLC: Siemens S7-1200 (e.g., CPU 1214C DC/DC/DC, any firmware version).
    Host PC: Compatible with Python 3.13 or higher.
    Connectivity: Standard Ethernet Network (RJ45).

#### Software

    Python Runtime: Version 3.13.
    Python Libraries: Refer to requirements.txt or the dependencies listed in the source code.
    Engineering Software: TIA Portal (V16 or higher).
    Operating System: Windows 10 Professional (Tested/Verified).

### Installation

Clone the repository

`</>Basch`

	git clone https://github.com/elmergthub/pystank_an_open_source_python_scada_code_v00.git
	cd pystank_an_open_source_python_scada_code_v00
	pip install -r requirements.txt

#### PLC Configuration

To allow the Python script to communicate with the S7-1200 via Modbus TCP:

    Open TIA Portal and go to Device Configuration.
    In the PLC Properties, ensure Ethernet addresses are correctly set.
    Important: Under "Protection & Security," enable "Permit access with PUT/GET communication from remote partner".
    Download the hardware configuration and the Modbus server block (MB_SERVER) to the PLC.
-------------
## License
This project is licensed under the MIT License.
