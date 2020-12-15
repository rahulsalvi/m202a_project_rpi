import socket
import threading
import time
from functools import partial
from ctypes import sizeof

from bokeh.plotting import figure, curdoc
from bokeh.models import CheckboxGroup
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import column

from network_msgs import VehicleDataMsg, HeartbeatMsg

RECV_UDP_IP = "10.0.0.2"
RECV_UDP_PORT = 2718

SEND_UDP_IP = "10.0.0.186"
SEND_UDP_PORT = 2719

doc = curdoc()

recv_sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
recv_sock.bind((RECV_UDP_IP, RECV_UDP_PORT))

send_sock = socket.socket(socket.AF_INET, # Internet
                          socket.SOCK_DGRAM) # UDP


fig = figure(plot_width=800, plot_height=400, x_range=(0,60), y_range=(0,13000))
fig.xaxis.axis_label = "Time"
fig.yaxis.axis_label = "RPM"
data = ColumnDataSource(dict(timestamp=[], rpm=[]))
rpm_line = fig.circle(source=data, x='timestamp', y='rpm')

first_time = 0
got_first_time = False

def update(m):
    global first_time
    global got_first_time
    global fig
    # convert to seconds
    ts = m.timestamp / 1000.0
    if not got_first_time:
        first_time = ts
        got_first_time = True
    ts = ts - first_time
    if abs(fig.x_range.end - ts) < 3:
        fig.x_range.start = ts - 55
        fig.x_range.end = ts + 5
    data.stream(dict(timestamp=[ts], rpm=[m.rpm]), 3600)

connected = False
most_recent_seq_num = 0

def recv_thread_fn():
    global connected
    global most_recent_seq_num
    while True:
        d, _ = recv_sock.recvfrom(sizeof(VehicleDataMsg)) # buffer size is 1024 bytes
        m = VehicleDataMsg.from_buffer_copy(d)
        if connected:
            if m.seq_number > most_recent_seq_num:
                most_recent_seq_num = m.seq_number
            doc.add_next_tick_callback(partial(update, m=m))

def send_thread_fn():
    global connected
    global most_recent_seq_num
    m = HeartbeatMsg()
    while True:
        if connected:
            m.ack_num = most_recent_seq_num
            send_sock.sendto(bytes(m), (SEND_UDP_IP, SEND_UDP_PORT))
        time.sleep(1.0)


def connected_checkbox_on_click(new):
    global connected
    connected = not bool(new[0])

connected_checkbox = CheckboxGroup(labels=["Connected"], active=[1])
connected_checkbox.on_click(connected_checkbox_on_click)

doc.add_root(column(fig, connected_checkbox))

recv_thread = threading.Thread(target=recv_thread_fn, daemon=True)
recv_thread.start()

send_thread = threading.Thread(target=send_thread_fn, daemon=True)
send_thread.start()
