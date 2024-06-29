import logging
import multiprocessing
import socket
import time

from lib.message import ChatMessage, Message, MessageEncoder, MessageType


class Client():
    def __init__(self, host, port, nickname):
        self.uuid = None

        self._host = host
        self._port = port
        self._nickname = nickname
        self._receive_msg = []

        self._sock = None
        self._logger = logging.getLogger('client')

    def _createSocket(self):
        address = (self._host, self._port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)
        print('Finding connection')
        return sock

    def _handleMessage(self):
        ''' Receiving message from the node server'''
        while True:
            data = ''
            data = self._sock.recv(1024).decode()
            '''Printing sms received from the server '''
            time.sleep(0.001)
            print(data)

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
                message = input("Enter message:")
                req = ChatMessage(sender=self._nickname,
                                  message=message).toJSON()
                self._logger.debug('Sending message: {}'.format(message))
                res = self._sock.send(str.encode(req))
                print('Sent: {}'.format(res))
                if res:
                    print('{}: {}'.format(self._nickname, message))
                continue

    def shutdown(self):
        self._sock = None


def main():
    while True:
        # server_ip = input('Enter server_ip: ')
        # nickname = input('Enter nickname: ')
        server_ip = '127.0.0.1'
        nickname = 'client'
        server_port = 3000
        if len(server_ip.split('.')) < 4:
            continue
        break
    time.sleep(1)
    client = Client(server_ip, server_port, nickname)
    client.run()


if __name__ == '__main__':
    main()
