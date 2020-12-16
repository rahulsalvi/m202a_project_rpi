from ctypes import sizeof, addressof
import threading
import time
import sqlite3
import socket
import select

import serial
from crccheck.crc import Crc32Mpeg2

from serial_msgs import SerialMsg
from aemnet_msgs import msg_00, msg_03, msg_04
from network_msgs import VehicleDataMsg, HeartbeatMsg
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

file_time = time.strftime("%Y-%m-%d_%H-%M.db")
def create_db_connection():
    global file_time
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

SEND_UDP_IP = "10.0.0.2"
SEND_UDP_PORT = 2718
def data_network_send_thread_fn(sock):
    while True:
        m = VehicleDataMsg()
        columns_lock.acquire()
        m.from_list(columns)
        columns_lock.release()
        sock.sendto(bytes(m), (SEND_UDP_IP, SEND_UDP_PORT))
        time.sleep(1.0)

client_connected = False
client_connected_lock = threading.Lock()
missing_ranges = []
missing_ranges_lock = threading.Lock()

def heartbeat_recv_thread_fn(sock):
    global client_connected
    global missing_ranges
    sock.setblocking(0)
    missed_acks = 0
    last_received_ack = 0
    while True:
        ready,_,_ = select.select([sock], [], [], 1)
        if len(ready) == 0:
            missed_acks += 1
        else:
            d, _ = sock.recvfrom(sizeof(HeartbeatMsg))
            m = HeartbeatMsg.from_buffer_copy(d)
            if m.ack_num - last_received_ack > 6:
                missing_range = [last_received_ack, m.ack_num-1]
                missing_ranges_lock.acquire()
                missing_ranges.append(missing_range)
                missing_ranges_lock.release()
            last_received_ack = m.ack_num
            missed_acks = 0
        client_connected_lock.acquire()
        client_connected = (missed_acks < 2)
        client_connected_lock.release()
        print("Client connected:", missed_acks < 2)

def catchup(sock, datapoints):
    groups = []
    for i in range(0, len(datapoints), 8):
        groups.append(datapoints[i:i+7])
    for i in [0, 4, 8, 2, 6]:
        for group in groups:
            if len(group) > i:
                m = VehicleDataMsg()
                m.from_list(group[i])
                sock.sendto(bytes(m), (SEND_UDP_IP, SEND_UDP_PORT))
                time.sleep(0.2)

def client_catchup_thread_fn(sock):
    global client_connected
    global missing_ranges
    conn = create_db_connection()
    c = conn.cursor()
    while True:
        client_connected_lock.acquire()
        connected = client_connected
        client_connected_lock.release()
        missing_ranges_lock.acquire()
        mr = missing_ranges
        missing_ranges_lock.release()
        if connected and len(mr) > 0:
            r = mr.pop()
            c.execute("SELECT * from data WHERE sequence_number >= ? AND sequence_number <= ?", tuple(r))
            datapoints = c.fetchall()
            catchup(sock, datapoints)
        time.sleep(1.0)

# useful for testing without anything hooked up
def set_rpm_thread_fn():
    counter = 0
    while True:
        columns_lock.acquire()
        columns[DatabaseColumn.RPM] = (counter * 30.0)
        columns_lock.release()
        counter += 1
        if counter > 400:
            counter = 0
        time.sleep(0.050)

def main():
    serial_thread = threading.Thread(target=serial_thread_fn, daemon=True)
    serial_thread.start()
    database_thread = threading.Thread(target=db_thread_fn, daemon=True)
    database_thread.start()

    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_network_send_thread = threading.Thread(target=data_network_send_thread_fn, args=(send_sock,), daemon=True)
    data_network_send_thread.start()

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(("10.0.0.186", 2719))
    heartbeat_recv_thread = threading.Thread(target=heartbeat_recv_thread_fn, args=(recv_sock,), daemon=True)
    heartbeat_recv_thread.start()

    catchup_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_catchup_thread = threading.Thread(target=client_catchup_thread_fn, args=(catchup_sock,), daemon=True)
    client_catchup_thread.start()

    set_rpm_thread = threading.Thread(target=set_rpm_thread_fn, daemon=True)
    set_rpm_thread.start()

    try:
        while True:
            print("RPM:", int(columns[DatabaseColumn.RPM]))
            time.sleep(1.0)
    except KeyboardInterrupt:
        send_sock.close()
        recv_sock.close()
        catchup_sock.close()
        port.close()
        print("Exiting")

if __name__ == "__main__":
    main()
