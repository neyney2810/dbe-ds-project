import json
import multiprocessing
import socket
import time

from lib.logger import Logger
from lib.message import ChatMessage


class Client():
    def __init__(self, host, port, nickname):
        self.uuid = None

        self._host = host
        self._port = port
        self._nickname = nickname
        self._receive_msg = []

        self._sock = None
        self._logger = Logger()

    def _createSocket(self):
        address = (self._host, self._port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)
        print('Finding connection, {}:{}...'.format(self._host, self._port))
        return sock

    def _handleMessage(self):
        ''' Receiving message from the node server'''
        while True:
            data = ''
            data = self._sock.recv(1024).decode()
            '''Printing sms received from the server '''
            time.sleep(0.001)
            if data:
                message = json.loads(data)
                print("\033[A                             \033[A")
                self._logger.log_client_message(
                    "{}: {}".format(message['sender'],
                                    message['message']))
                print("Enter message: \n")

    def run(self):
        # Run chat room
        self._sock = self._createSocket()

        # First message
        # message = '{} has entered the chat'.format(self._nickname)
        # self.send_message(message)

        if self._sock:
            recv_io = multiprocessing.Process(target=self._handleMessage)
            recv_io.daemon = True
            recv_io.start()
            while True:
                try:
                    message = input("Enter message: \n")
                    req = ChatMessage(sender=self._nickname,
                                      message=message).toJSON()
                    self._logger.log_sys('Sending message: {}'.format(message))
                    self._sock.send(str.encode(req))
                except KeyboardInterrupt:
                    self.shutdown()
                    break
                except Exception as e:
                    self._logger.log_error(
                        'Error sending message: {}'.format(e))
                    self.shutdown()
                    break

    def shutdown(self):
        self._sock = None


def main():
    while True:
        server_ip = input('Enter server_ip: ')
        server_port = input('Enter server_port: ')
        nickname = 'client'
        nickname = input('Enter nickname: ')
        server_port = int(server_port)
        if len(server_ip.split('.')) < 4:
            continue
        break
    time.sleep(1)
    client = Client(server_ip, server_port, nickname)
    client.run()


if __name__ == '__main__':
    main()
