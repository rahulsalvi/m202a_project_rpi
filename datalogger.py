from ctypes import sizeof
import serial
from serial_msgs import SerialMsg
from crccheck.crc import Crc32Mpeg2

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
    wait_for_start_signal()
    data = port.read(size=(sizeof(SerialMsg) - 4))
    msg_bytes = start_signal + data
    crc = Crc32Mpeg2.calc(msg_bytes[:SerialMsg.crc32.offset])
    msg = SerialMsg.from_buffer_copy(msg_bytes)
    if crc == msg.crc32:
        return msg
    return None

while True:
    m = read_msg()
    if m is not None:
        print(m.seq_number)
        print(m.num_msgs)
        for i in range(m.num_msgs):
            print(hex(m.msgs[i].id))
    else:
        print("CRC ERROR")
