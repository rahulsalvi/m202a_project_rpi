import socket
from ctypes import sizeof
from network_msgs import VehicleDataMsg

UDP_IP = "10.0.0.2"
UDP_PORT = 2718

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(sizeof(VehicleDataMsg)) # buffer size is 1024 bytes
    m = VehicleDataMsg.from_buffer_copy(data)
    print(m.rpm)
