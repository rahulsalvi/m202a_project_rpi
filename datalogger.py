from ctypes import sizeof, addressof
import threading
import serial
from serial_msgs import SerialMsg
from crccheck.crc import Crc32Mpeg2
from aemnet_msgs import msg_00, msg_03, msg_04

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

def main():
    while True:
        m = read_msg()
        print(m.seq_number)
        print(m.num_msgs)
        for i in range(m.num_msgs):
            ID = m.msgs[i].id
            print(hex(ID))
            if ID == 0x1f0a000:
                d = msg_00.from_address(addressof(m.msgs[i].data))
                print(d.get_rpm(), d.get_throttle(), d.get_intake_temp(), d.get_coolant_temp())
            elif ID == 0x1f0a003:
                d = msg_03.from_address(addressof(m.msgs[i].data))
                print(d.get_afr1(), d.get_afr2(), d.get_vehicle_speed(), d.get_gear(), d.get_ign_timing(), d.get_battery_voltage())
            elif ID == 0x1f0a004:
                d = msg_04.from_address(addressof(m.msgs[i].data))
                print(d.get_manifold_pressure(), d.get_ve(), d.get_fuel_pressure(), d.get_oil_pressure(), d.get_afr_target())

if __name__ == "__main__":
    main()
