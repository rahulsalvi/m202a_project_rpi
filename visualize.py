import socket
import threading
import time
from ctypes import sizeof

from bokeh.plotting import figure, curdoc
from bokeh.client import push_session
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import row

from network_msgs import VehicleDataMsg
from database import DatabaseColumn

UDP_IP = "10.0.0.2"
UDP_PORT = 2718

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

fig = figure(plot_width=800, plot_height=400)
fig.xaxis.axis_label = "Time"
fig.yaxis.axis_label = "RPM"
data = ColumnDataSource(dict(timestamp=[], rpm=[]))
rpm_line = fig.line(source=data, x='timestamp', y='rpm')

def recv_thread_fn():
    d, _ = sock.recvfrom(sizeof(VehicleDataMsg)) # buffer size is 1024 bytes
    m = VehicleDataMsg.from_buffer_copy(d)
    print(m.timestamp, m.rpm)
    data.stream(dict(timestamp=[m.timestamp], rpm=[m.rpm]), 3600)

curdoc().add_root(row(fig))
curdoc().add_periodic_callback(recv_thread_fn, 1000)
