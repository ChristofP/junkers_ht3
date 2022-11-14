"""Heatronic 3 driver"""
import logging
import socket
import threading
import time

_LOGGER = logging.getLogger(__name__)

crc_table = [
    0x00,
    0x02,
    0x04,
    0x06,
    0x08,
    0x0A,
    0x0C,
    0x0E,
    0x10,
    0x12,
    0x14,
    0x16,
    0x18,
    0x1A,
    0x1C,
    0x1E,
    0x20,
    0x22,
    0x24,
    0x26,
    0x28,
    0x2A,
    0x2C,
    0x2E,
    0x30,
    0x32,
    0x34,
    0x36,
    0x38,
    0x3A,
    0x3C,
    0x3E,
    0x40,
    0x42,
    0x44,
    0x46,
    0x48,
    0x4A,
    0x4C,
    0x4E,
    0x50,
    0x52,
    0x54,
    0x56,
    0x58,
    0x5A,
    0x5C,
    0x5E,
    0x60,
    0x62,
    0x64,
    0x66,
    0x68,
    0x6A,
    0x6C,
    0x6E,
    0x70,
    0x72,
    0x74,
    0x76,
    0x78,
    0x7A,
    0x7C,
    0x7E,
    0x80,
    0x82,
    0x84,
    0x86,
    0x88,
    0x8A,
    0x8C,
    0x8E,
    0x90,
    0x92,
    0x94,
    0x96,
    0x98,
    0x9A,
    0x9C,
    0x9E,
    0xA0,
    0xA2,
    0xA4,
    0xA6,
    0xA8,
    0xAA,
    0xAC,
    0xAE,
    0xB0,
    0xB2,
    0xB4,
    0xB6,
    0xB8,
    0xBA,
    0xBC,
    0xBE,
    0xC0,
    0xC2,
    0xC4,
    0xC6,
    0xC8,
    0xCA,
    0xCC,
    0xCE,
    0xD0,
    0xD2,
    0xD4,
    0xD6,
    0xD8,
    0xDA,
    0xDC,
    0xDE,
    0xE0,
    0xE2,
    0xE4,
    0xE6,
    0xE8,
    0xEA,
    0xEC,
    0xEE,
    0xF0,
    0xF2,
    0xF4,
    0xF6,
    0xF8,
    0xFA,
    0xFC,
    0xFE,
    0x19,
    0x1B,
    0x1D,
    0x1F,
    0x11,
    0x13,
    0x15,
    0x17,
    0x09,
    0x0B,
    0x0D,
    0x0F,
    0x01,
    0x03,
    0x05,
    0x07,
    0x39,
    0x3B,
    0x3D,
    0x3F,
    0x31,
    0x33,
    0x35,
    0x37,
    0x29,
    0x2B,
    0x2D,
    0x2F,
    0x21,
    0x23,
    0x25,
    0x27,
    0x59,
    0x5B,
    0x5D,
    0x5F,
    0x51,
    0x53,
    0x55,
    0x57,
    0x49,
    0x4B,
    0x4D,
    0x4F,
    0x41,
    0x43,
    0x45,
    0x47,
    0x79,
    0x7B,
    0x7D,
    0x7F,
    0x71,
    0x73,
    0x75,
    0x77,
    0x69,
    0x6B,
    0x6D,
    0x6F,
    0x61,
    0x63,
    0x65,
    0x67,
    0x99,
    0x9B,
    0x9D,
    0x9F,
    0x91,
    0x93,
    0x95,
    0x97,
    0x89,
    0x8B,
    0x8D,
    0x8F,
    0x81,
    0x83,
    0x85,
    0x87,
    0xB9,
    0xBB,
    0xBD,
    0xBF,
    0xB1,
    0xB3,
    0xB5,
    0xB7,
    0xA9,
    0xAB,
    0xAD,
    0xAF,
    0xA1,
    0xA3,
    0xA5,
    0xA7,
    0xD9,
    0xDB,
    0xDD,
    0xDF,
    0xD1,
    0xD3,
    0xD5,
    0xD7,
    0xC9,
    0xCB,
    0xCD,
    0xCF,
    0xC1,
    0xC3,
    0xC5,
    0xC7,
    0xF9,
    0xFB,
    0xFD,
    0xFF,
    0xF1,
    0xF3,
    0xF5,
    0xF7,
    0xE9,
    0xEB,
    0xED,
    0xEF,
    0xE1,
    0xE3,
    0xE5,
    0xE7,
]


class Ht3Driver(threading.Thread):
    """Heatronic 3 driver"""

    def __init__(self, address, port=8088):
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop_thread = threading.Event()
        self._lock = threading.Lock()

        self._address = address
        self._port = int(port)
        self._socket = None
        self._devicetype = "RX"
        self._flag_writing_sequence = 0
        self._buffer = ""
        self._client_id = 0
        self._stop = False

        self._connected = False

        self.dict = {}
        self.callback = None

        _LOGGER.info("HT3 cht_socket_client init")

        # self.connect()

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
            _LOGGER.info("Client-ID:%s; socket closed", self._client_id)

    def set_callback(self, function):
        """Function to be called when data is changed."""
        self.callback = function

    def connected(self):
        """Check if driver is connected"""
        return self._connected

    def clientID(self):
        """get Client ID"""
        return self._client_id

    def stop(self):
        """Stop the interface connection"""
        self._stop = True
        # self._stop_thread.set()

        if self._socket is not None:
            with self._lock:  # Receive thread might use the socket
                self._connected = False
                self._socket.close()
                self._socket = None
                _LOGGER.info("Client-ID:%s; socket closed", self._client_id)

    def restart(self):
        """Restart the interface connection"""
        self._stop = False

    def _write(self, data):
        """write data to connected socket. It will block
        until all data is written.
        """
        if self._socket is None:
            _LOGGER.critical(
                "Client-ID:%s; cht_socket_client._write(); socket not initialised",
                self._client_id,
            )

        try:
            self._socket.sendall(bytes(data))
        except:
            self._connected = False
            self._socket.close()
            self._socket = None
            _LOGGER.critical(
                "Client-ID:%s; cht_socket_client._write(); error on socket.sendall",
                self._client_id,
            )
            raise

    def _read(self):
        data = self._socket.recv(1024)
        # print (data)
        # print (data.hex())
        return data.hex()

    def _substr(self, string, start, end):
        return string[start : start + end]

    def _set_value(self, name, value):
        if name in self.dict:
            old_value = self.dict[name]
            if value != old_value:
                self.dict[name] = value
                if self.callback:
                    self.callback(name, value)
        else:
            self.dict[name] = value
            if self.callback:
                self.callback(name, value)

    def connect(self):
        """connect to HT3 gateway"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self._address, self._port))
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            _LOGGER.info(
                "Connected to server:'%s';port:'%d'", self._address, self._port
            )
        except (socket.error, socket.timeout, ValueError):
            _LOGGER.critical(
                "HT3 cht_socket_client.connect();error:can't connect to socket %s:%s",
                self._address,
                self._port,
            )
            self._connected = False
            self._socket = None
            # raise
            return False

        # send registration to proxy-server and receive client-related informations from server
        try:
            # send devicetype to server
            devicetype = bytearray(self._devicetype.encode("utf-8"))
            self._write(devicetype)

            # read answer from server (client-ID) and store it
            self._client_id = self._socket.recv(10).decode("utf-8")
            ## only for test## print("client got ID:{0}".format(self._client_id))
        except (socket.error, socket.timeout, ValueError):
            self._socket.close()
            self._socket = None
            _LOGGER.critical(
                "HT3 cht_socket_client.connect();error:can't register to master"
            )
            self._connected = False
            return False
            # raise

        # successfully connected to server
        _LOGGER.info(
            "Client-ID:%s; registered with devicetype:'%s'",
            self._client_id,
            self._devicetype,
        )
        self._connected = True

        return True

    def run(self):
        # @ToDo: add connection lost + reconnect
        # @ToDo: search for start-tag '#' and 'H','R'

        _LOGGER.info("Client-ID:%s; cht_socket_client run", self._client_id)

        def handle_messages(data):
            self._buffer += data
            if len(self._buffer) > 0:
                if self._buffer.find("88000200") >= 0:  # heater
                    pos = self._buffer.find("88002000")
                    length = 62
                    _data = self._substr(self._buffer, pos, length)
                    if len(_data) >= length:
                        print(_data)
                elif self._buffer.find("88001800") >= 0:  # heater
                    pos = self._buffer.find("88001800")
                    length = 62
                    _data = self._substr(self._buffer, pos, length)
                    if len(_data) >= length:
                        self._decode_msg_ch1(_data, length)
                        self._buffer = ""
                elif (
                    self._buffer.find("9000ff00") >= 0
                ):  # controller data (FW1xy / FW2xy)
                    pos = self._buffer.find("9000ff00")
                    length = 28
                    _data = self._substr(self._buffer, pos, length)
                    if len(_data) >= length:
                        self._decode_msg_hc(_data, length)
                        self._buffer = ""
                elif self._buffer.find("88003400") >= 0:  # domestic hot water data
                    pos = self._buffer.find("88003400")
                    length = 46
                    _data = self._substr(self._buffer, pos, length)
                    if len(_data) >= length:
                        self._decode_msg_dhw(_data, length)
                        self._buffer = ""
                elif self._buffer.find("90000600") >= 0:  # date / time data
                    pos = self._buffer.find("90000600")
                    length = 28
                    _data = self._substr(self._buffer, pos, length)
                    if len(_data) >= length:
                        self._decode_msg_dt(_data, length)
                        self._buffer = ""
                elif self._buffer.find("#HR") >= 0:
                    print(self._buffer[self._buffer.find("#HR") :])
                # else:
                #    print(self._buffer)

        while not self._stop_thread.isSet():
            if not self._stop:
                if not self._connected:
                    time.sleep(10)
                    self.connect()
                else:
                    try:
                        with self._lock:
                            data = self._read()
                        handle_messages(data)
                    except (socket.timeout, ValueError):  # No data
                        _LOGGER.critical(
                            "Client-ID:%s; cht_socket_client.run(); error on socket.recv",
                            self._client_id,
                        )
                        self._connected = False
                        self._socket.close()
                        self._socket = None

        _LOGGER.info("Client-ID:%s; cht_socket_client stopped", self._client_id)

    def write_hc_trequested(self, trequested):
        # do not write if flag is set
        if self._flag_writing_sequence == 1:
            return False
        self._flag_writing_sequence = 1

        trequested_4htbus = int(trequested * 2)

        ## send 1. netcom-bytes to 'ht_pitiny' | 'ht_piduino' (ht_transceiver)
        #   header=  '#',   <length>  ,'!' ,'S' ,0x11
        #   header= 0x23,(len(data)+3),0x21,0x53,0x11
        #   data  = 0x10,0xff,0x11,0x00,0x65,tsoll
        #   block=header+data
        header = [0x23, 0x09, 0x21, 0x53, 0x11]
        data = [0x10, 0xFF, 0x11, 0x00, 0x65, trequested_4htbus]
        block = header + data
        self._write(block)

        time.sleep(1)

        ## send 2. netcom-bytes to 'ht_pitiny' | 'ht_piduino' (ht_transceiver)
        #   header= 0x23,(len(data)+3),0x21,0x53,0x11
        #   data  = 0x10,0xff,0x07,0x00,0x79,tsoll
        #   block=header+data
        header = [0x23, 0x09, 0x21, 0x53, 0x11]
        data = [0x10, 0xFF, 0x07, 0x00, 0x79, trequested_4htbus]
        block = header + data
        self._write(block)

        self._flag_writing_sequence = 0

        _LOGGER.info(
            "Client-ID:%s; writeHC_Trequested:'%d'", self._client_id, trequested
        )
        _LOGGER.info(
            "Client-ID:%s; trequested_4htbus:'%d'", self._client_id, trequested_4htbus
        )

        return True

    def write_hc_mode(self, mode_requested):
        # do not write if flag is set
        if self._flag_writing_sequence == 1:
            return False

        self._flag_writing_sequence = 1

        ## send 1. netcom-bytes to 'ht_pitiny' | 'ht_piduino' (ht_transceiver)
        #   header=  '#',   <length>  ,'!' ,'S' ,0x11
        #   header= 0x23,(len(data)+3),0x21,0x53,0x11
        #   data  = 0x10,0xff,0x0e,0x00,0x65,mode_requested
        #   block=header+data
        header = [0x23, 0x09, 0x21, 0x53, 0x11]
        data = [0x10, 0xFF, 0x0E, 0x00, 0x65, mode_requested]
        block = header + data
        self._write(block)

        time.sleep(1)

        ## send 2. netcom-bytes to 'ht_pitiny' | 'ht_piduino' (ht_transceiver)
        #   header= 0x23,(len(data)+3),0x21,0x53,0x11
        #   data  = 0x10,0xff,0x04,0x00,0x79,mode_requested
        #   block=header+data
        header = [0x23, 0x09, 0x21, 0x53, 0x11]
        data = [0x10, 0xFF, 0x04, 0x00, 0x79, mode_requested]
        block = header + data
        self._write(block)

        self._flag_writing_sequence = 0

        _LOGGER.info("Client-ID:%s; writeHC_mode:'%d'", self._client_id, mode_requested)

        return True

    def _decode_msg_ch1(self, string, length):
        if self.crc_check(string, length):
            self._set_value("ch_Tflow_desired", int(self._substr(string, 4 * 2, 2), 16))
            self._set_value(
                "ch_Tflow_measured", int(self._substr(string, 5 * 2, 4), 16) / 10
            )
            # self.ch_Treturn          = int(self._substr(string,17*2,4), 16)/10
            self._set_value("ch_Tmixer", int(self._substr(string, 13 * 2, 4), 16) / 10)
            self._set_value("ch_burner_power", int(self._substr(string, 8 * 2, 2), 16))
            self._set_value(
                "ch_burner_operation",
                1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x08) else 0,
            )
            self._set_value(
                "ch_pump_heating",
                1 if (int(self._substr(string, 11 * 2, 2), 16) & 0x20) else 0,
            )
            self._set_value(
                "ch_pump_cylinder",
                1 if (int(self._substr(string, 11 * 2, 2), 16) & 0x40) else 0,
            )
            self._set_value(
                "ch_pump_circulation",
                1 if (int(self._substr(string, 11 * 2, 2), 16) & 0x80) else 0,
            )
            self._set_value(
                "ch_burner_fan",
                1 if (int(self._substr(string, 11 * 2, 2), 16) & 0x01) else 0,
            )
            self._set_value("ch_mode", (int(self._substr(string, 9 * 2, 2), 16) & 0x03))
            self._set_value("ch_code", int(self._substr(string, 24 * 2, 4), 16))
            self._set_value("ch_22_num", int(self._substr(string, 22 * 2, 2), 16))
            self._set_value("ch_23_num", int(self._substr(string, 23 * 2, 2), 16))
            # self.ch_22_char          = (ch_22_num == 0) ? "0" : chr(ch_22_num)
            # self.ch_23_char          = (ch_23_num == 0) ? "0" : chr(ch_23_num)
            # self.ch_error            = ch_22_char . ch_23_char
            # print(self.ch_Tflow_measured)

    def _decode_msg_hc(self, string, length):
        # prefix = "hc1_"

        if self.crc_check(string, length):
            # Messages of length 11 Bytes are unknown -> no handling
            if length == 11:
                return 1

            # hc_type = int(self._substr(string, 5 * 2, 2), 16)

            # if hc_type == 111:
            #     prefix = "hc1_"
            # elif hc_type == 112:
            #     prefix = "hc2_"
            # elif hc_type == 114:
            #     prefix = "hc3_"
            # elif hc_type == 116:
            #     prefix = "hc4_"
            # elif hc_type == 211:
            #     return 1

            if length != 9:
                self._set_value(
                    "hc_Tdesired", int(self._substr(string, 8 * 2, 4), 16) / 10
                )
                self._set_value(
                    "hc_Tmeasured", int(self._substr(string, 10 * 2, 4), 16) / 10
                )

            self._set_value("hc_mode", int(self._substr(string, 6 * 2, 2), 16))
            self._set_value("hc_auto", int(self._substr(string, 7 * 2, 2), 16))

            # print("{0}: {1} - {2}".format(prefix, self.hc_Tdesired, self.hc_Tmeasured))

    def _decode_msg_dhw(self, string, length):
        if self.crc_check(string, length):
            self._set_value("dhw_Tdesired", int(self._substr(string, 4 * 2, 2), 16))
            self._set_value(
                "dhw_Tmeasured", int(self._substr(string, 5 * 2, 4), 16) / 10
            )
            self._set_value(
                "dhw_Tcylinder", int(self._substr(string, 7 * 2, 4), 16) / 10
            )
            self._set_value("ch_runtime_dhw", int(self._substr(string, 14 * 2, 6), 16))
            self._set_value("ch_starts_dhw", int(self._substr(string, 17 * 2, 6), 16))
            self._set_value(
                "dhw_charge_once",
                1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x02) else 0,
            )
            self._set_value(
                "dhw_thermal_desinfection",
                1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x04) else 0,
            )
            self._set_value(
                "dhw_generating",
                1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x08) else 0,
            )
            self._set_value(
                "dhw_boost_charge",
                1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x10) else 0,
            )
            self._set_value(
                "dhw_Tok", 1 if (int(self._substr(string, 9 * 2, 2), 16) & 0x20) else 0
            )

            # print("DHW: {} {} {} {} {} {} {}".format(self.dhw_Tdesired, self.dhw_Tmeasured, self.ch_runtime_dhw, self.dhw_charge_once, self.dhw_generating, self.dhw_boost_charge, self.dhw_Tok))

    def _decode_msg_dt(self, string, length):
        if self.crc_check(string, length):
            year = 2000 + int(self._substr(string, 4 * 2, 2), 16)
            month = int(self._substr(string, 5 * 2, 2), 16)
            day = int(self._substr(string, 7 * 2, 2), 16)
            hours = int(self._substr(string, 6 * 2, 2), 16)
            minute = int(self._substr(string, 8 * 2, 2), 16)
            sec = int(self._substr(string, 9 * 2, 2), 16)
            # dow = int(self._substr(string, 10 * 2, 2), 16)
            # dst = "dst" if (int(self._substr(string, 11 * 2, 2), 16) & 0x01) else ""

            self._set_value(
                "ht3_time",
                "{:4d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    year, month, day, hours, minute, sec
                ),
            )
            # print("{:4d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(self.year, self.month, self.day, self.hours, self.min, self.sec))

    def crc_check(self, buffer, length):
        """calculate CRC checksum"""
        if length < 6:
            return False

        length >>= 1
        crc = 0

        try:
            for i in range(0, length - 2):
                crc = crc_table[crc]
                crc ^= int(self._substr(buffer, i * 2, 2), 16)

            return crc == int(self._substr(buffer, length * 2 - 4, 2), 16)

        except (IndexError):
            # print("crc_check();Error;{0}", e.args[0])
            return False

    def crc_get(self, string):
        """get CRC"""
        crc = 0
        length = int(len(string) / 2)

        for i in range(length - 3):
            crc = int(crc_table[crc])
            crc ^= int(self._substr(string, i * 2, 2), 16)

        # print (hex(crc), " ", self._substr(string, length*2-4, 2))
