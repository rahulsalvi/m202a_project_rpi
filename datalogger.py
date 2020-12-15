from ctypes import sizeof, addressof
import threading
import time
import sqlite3
import socket
import serial

from crccheck.crc import Crc32Mpeg2

from serial_msgs import SerialMsg
from aemnet_msgs import msg_00, msg_03, msg_04
from network_msgs import VehicleDataMsg
from database import DatabaseColumn

columns = [0.0] * int(DatabaseColumn.NUM_VALUES)
columns[DatabaseColumn.TIMESTAMP] = 0
columns[DatabaseColumn.SEQ_NUM] = 0
columns_lock = threading.Lock()

def process_msg_00(data):
    d = msg_00.from_address(addressof(data))
    columns[DatabaseColumn.RPM] = d.get_rpm()
    columns[DatabaseColumn.THROTTLE] = d.get_throttle()
    columns[DatabaseColumn.INTAKE_TEMP] = d.get_intake_temp()
    columns[DatabaseColumn.COOLANT_TEMP] = d.get_coolant_temp()

def process_msg_03(data):
    d = msg_03.from_address(addressof(data))
    columns[DatabaseColumn.AFR1] = d.get_afr1()
    columns[DatabaseColumn.AFR2] = d.get_afr2()
    columns[DatabaseColumn.VEHICLE_SPEED] = d.get_vehicle_speed()
    columns[DatabaseColumn.GEAR] = d.get_gear()
    columns[DatabaseColumn.BATTERY_VOLTAGE] = d.get_battery_voltage()

def process_msg_04(data):
    d = msg_04.from_address(addressof(data))
    columns[DatabaseColumn.MANIFOLD_PRESSURE] = d.get_manifold_pressure()
    columns[DatabaseColumn.FUEL_PRESSURE] = d.get_fuel_pressure()

msg_processing_fns = {0x1f0a000: process_msg_00, 0x1f0a003: process_msg_03, 0x1f0a004: process_msg_04}

port = serial.Serial("/dev/serial0", baudrate=115200)
# feedface in reverse
start_signal = bytes.fromhex("cefaedfe")

def wait_for_start_signal():
    while True:
        if port.read(1)[0] == start_signal[0]:
            if port.read(1)[0] == start_signal[1]:
                if port.read(1)[0] == start_signal[2]:
                    if port.read(1)[0] == start_signal[3]:
                        break
                else:
                    continue
            else:
                continue
        else:
            continue


def read_msg():
    while True:
        wait_for_start_signal()
        data = port.read(size=(sizeof(SerialMsg) - 4))
        msg_bytes = start_signal + data
        crc = Crc32Mpeg2.calc(msg_bytes[:SerialMsg.crc32.offset])
        msg = SerialMsg.from_buffer_copy(msg_bytes)
        if crc == msg.crc32:
            return msg

def serial_thread_fn():
    while True:
        m = read_msg()
        columns_lock.acquire()
        for i in range(m.num_msgs):
            msg_id = m.msgs[i].id
            fn = msg_processing_fns.get(msg_id)
            if fn is not None:
                msg_data = m.msgs[i].data
                fn(msg_data)
        columns_lock.release()
        time.sleep(0.005)

def create_db_connection():
    file_time = time.strftime("%Y-%m-%d_%H-%M.db")
    conn = sqlite3.connect(file_time)
    return conn

def db_thread_fn():
    conn = create_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE data
                 (timestamp bigint,
                  sequence_number bigint,
                  rpm float,
                  throttle float,
                  intake_temp float,
                  coolant_temp float,
                  afr1 float,
                  afr2 float,
                  vehicle_speed float,
                  gear float,
                  battery_voltage float,
                  manifold_pressure float,
                  fuel_pressure float)''')
    conn.commit()
    seq_num = 0
    while True:
        columns_lock.acquire()
        columns[DatabaseColumn.TIMESTAMP] = int(time.time() * 1000)
        columns[DatabaseColumn.SEQ_NUM] = seq_num
        c.execute("INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(columns))
        columns_lock.release()
        conn.commit()
        seq_num = seq_num + 1
        time.sleep(0.5)

def data_network_send_thread_fn(sock):
    udp_ip = "10.0.0.2"
    udp_port = 2718
    while True:
        m = VehicleDataMsg()
        columns_lock.acquire()
        m.timestamp = columns[DatabaseColumn.TIMESTAMP]
        m.seq_number = columns[DatabaseColumn.SEQ_NUM]
        m.rpm = columns[DatabaseColumn.RPM]
        m.throttle = columns[DatabaseColumn.THROTTLE]
        m.intake_temp = columns[DatabaseColumn.INTAKE_TEMP]
        m.coolant_temp = columns[DatabaseColumn.COOLANT_TEMP]
        m.afr1 = columns[DatabaseColumn.AFR1]
        m.afr2 = columns[DatabaseColumn.AFR2]
        m.vehicle_speed = columns[DatabaseColumn.VEHICLE_SPEED]
        m.gear = columns[DatabaseColumn.GEAR]
        m.battery_voltage = columns[DatabaseColumn.BATTERY_VOLTAGE]
        m.manifold_pressure = columns[DatabaseColumn.MANIFOLD_PRESSURE]
        m.fuel_pressure = columns[DatabaseColumn.FUEL_PRESSURE]
        columns_lock.release()
        sock.sendto(bytes(m), (udp_ip, udp_port))
        time.sleep(1.0)

def main():
    serial_thread = threading.Thread(target=serial_thread_fn, daemon=True)
    serial_thread.start()
    database_thread = threading.Thread(target=db_thread_fn, daemon=True)
    database_thread.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_network_send_thread = threading.Thread(target=data_network_send_thread_fn, args=(sock,), daemon=True)
    data_network_send_thread.start()

    try:
        while True:
            print(columns[DatabaseColumn.RPM])
            time.sleep(0.5)
    except KeyboardInterrupt:
        sock.close()
        print("Exiting")

if __name__ == "__main__":
    main()
