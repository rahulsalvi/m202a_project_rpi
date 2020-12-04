from ctypes import Structure, c_uint8, c_uint32

class CanMsg(Structure):
    _fields_ = [
            ("id", c_uint32),
            ("data", c_uint8 * 8)
            ]

class SerialMsg(Structure):
    _fields_ = [
            ("start_signal", c_uint32),
            ("seq_number", c_uint32),
            ("num_msgs", c_uint32),
            ("msgs", CanMsg * 4),
            ("crc32", c_uint32)
            ]
