import json
from multiprocessing import Process
import multiprocessing
import os
import time
from dotenv import load_dotenv
from lib.address import Address
from lib.message import Message, MessageDecoder, MessageEncoder, MessageType
import socket

from lib.logger import Logger


class Discovery():
    BROADCAST_IP = '255.255.255.255'
    BROADCAST_PORT = 5972
    def on_discovery(x): return print(x)
    def on_finish_discovery(): return print('No nodes found in the network.')
    replica_address = None

    def __init__(self, host, port, broadcast_port):
        self._logger = Logger()
        self._stop_req = False
        self.host = host
        self.port = port
        self.BROADCAST_PORT = int(broadcast_port)
        self.setup_broadcast_socket()

    def set_on_message(self, on_message):
        self.on_message = on_message

    def set_replica_address(self, replica_address):
        self.replica_address = replica_address

    def run(self) -> None:
        self.listen()

    def setup_broadcast_socket(self):
        # Setup the socket for sending broadcast messages
        self.send_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.send_socket.setblocking(0)

        # Setup the socket for receiving broadcast messages
        self.recv_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.recv_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.recv_socket.bind(("", self.BROADCAST_PORT))

    # Will be called first time when node enter the network to collect information about other nodes and leader
    def send_discovery_message(self):
        message = Message(message=f"{self.replica_address if self.replica_address else ''}", host=self.host, port=self.port,
                          type=MessageType.DISCOVERY_REQ)
        message = MessageEncoder().encode(message)
        self._logger.log_broadcast(
            'Sending discovery message: {}'.format(message))

        # Broadcast message
        self.send_socket.sendto(
            str.encode(message), (self.BROADCAST_IP, self.BROADCAST_PORT))
        time.sleep(1)
        self.on_finish_discovery()

    def broadcast(self, message):
        # Broadcast the message to the network
        self.send_socket.settimeout(1)
        try:
            # Broadcast message
            self.send_socket.sendto(str.encode(
                message), (self.BROADCAST_IP, self.BROADCAST_PORT))
            while True:
                data, address = self.send_socket.recvfrom(1024)
                print('Broadcasted message: {}'.format(message))
                print(data)
        except socket.timeout:
            self._logger.log_broadcast(
                'Broadcast timed out')
        except Exception as e:
            self._logger.log_broadcast(
                'Error while broadcasting message: {}'.format(e))

    def listen(self):
        # Listen for incoming messages
        print('Listening for incoming messages from broadcast...')
        while True:
            data, address = self.recv_socket.recvfrom(1024)
            print('Received data from {}'.format(address))
            p = multiprocessing.Process(target=self.process_message,
                                        args=(data, address))
            p.start()
            p.join()

    def process_message(self, data, address):
        jsonStr = data.decode("utf-8")
        message = json.loads(json.loads(jsonStr), cls=MessageDecoder)
        if message.type == MessageType.DISCOVERY_REQ:
            if message.host != self.host or message.port != self.port:  # Ignore its own discovery request
                self._logger.log_broadcast('Discovery request from: {} {}'.format(
                    message.host, message.port))
                # Reply with its own address
                res = str(Address(host=self.replica_address.host,
                                  port=self.replica_address.port))
                reply = Message(host=self.host, port=self.port, message=res,
                                type=MessageType.DISCOVERY_RES)
                self._logger.log_broadcast(
                    'Sending discovery response to {}'.format(address))
                self.broadcast(MessageEncoder().encode(reply))
                # Add new node to the network
                self.on_discovery(message)
        elif message.type == MessageType.DISCOVERY_RES:
            self.on_discovery(message)
        elif message.type == MessageType.MESSAGE:
            self.on_message(message, address)

    def terminate(self):
        self._stop_req = True
        pass

    def start_listening(self):
        listen_thread = Process(target=self.listen)
        listen_thread.start()

    def start_send_discovery(self):
        discovery_thread = Process(
            target=self.send_discovery_message)
        discovery_thread.start()


if __name__ == '__main__':
    load_dotenv()
    discovery = Discovery("127.0.0.1", port=3004,
                          broadcast_port=os.getenv('BROADCAST_PORT'))
    discovery.send_discovery_message()
