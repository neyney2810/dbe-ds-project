import logging
import socket


class Client():
    def __init__(self, address, nickname):
        self.uuid = None

        self._primary = address
        self._sock = None
        self._nickname = nickname

        self.on_receive = None
        self.on_close = None
        self.on_history = None

        self._logger = logging.getLogger('client')

    def _createSocket(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(address)
        self._sock = sock
        return sock

    def send_message(self, message):
        self._sock.sendall(message.encode('UTF-8'))
        self._logger.debug('Sent message: {}'.format(message))

    def _handleMessage(self, data):
        if self.on_receive:
            self.on_receive(data.decode('UTF-8'))

    def run(self):
        self._sock = self._createSocket(self._primary)

        # First message
        message = 'Hello from {}'.format(self._nickname)
        self.send_message(message)

    def shutdown(self):
        self._sock = None
