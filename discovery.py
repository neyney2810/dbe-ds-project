import json
import os
from dotenv import load_dotenv
from lib.message import Message, MessageDecoder, MessageEncoder, MessageType
import socket
from threading import Thread


class Discovery():
    BROADCAST_IP = '255.255.255.255'
    BROADCAST_PORT = 5972

    def __init__(self, host, port, broadcast_port, on_message=lambda x, a: print(x, a), on_discovery=lambda x: print(x), on_no_discovery=lambda: print('No nodes found in the network.')):
        self._stop_req = False
        self.host = host
        self.port = port
        self.BROADCAST_PORT = int(broadcast_port)
        self.on_message = on_message
        self.on_discovery = on_discovery
        self.on_no_discovery = on_no_discovery
        self.setup_broadcast_socket()

    def set_on_message(self, on_message):
        self.on_message = on_message

    def set_on_discovery(self, on_discovery):
        self.on_discovery = on_discovery

    def run(self) -> None:
        self.listen()

    def setup_broadcast_socket(self):
        # Setup the socket for sending broadcast messages
        self.send_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Setup the socket for receiving broadcast messages
        self.recv_socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.recv_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.recv_socket.bind(("", self.BROADCAST_PORT))

    def send_discovery_message(self):
        ip = socket.gethostbyname(socket.gethostname())
        message = Message(message="", host=ip, port=self.BROADCAST_PORT,
                          type=MessageType.DISCOVERY_REQ)
        print('Sending discovery message: {}'.format(message))
        data = self.broadcast(MessageEncoder().encode(message))
        if data is not None:
            jsonStr = data.decode("utf-8")
            message = json.loads(json.loads(jsonStr), cls=MessageDecoder)
            if (message.type == MessageType.DISCOVERY_RES):
                print('Received discovery response: {}'.format(message))
                self.on_discovery(message)
        else:
            self.on_no_discovery()

    def broadcast(self, message):
        # Broadcast the message to the network
        self.send_socket.settimeout(10)

        try:
            # Broadcast message
            self.send_socket.sendto(str.encode(
                message), (self.BROADCAST_IP, self.BROADCAST_PORT))
            data, address = self.send_socket.recvfrom(1024)
            return data
        except socket.timeout:
            print('Broadcast timed out. Node is alone in the network.')
            return None

    def listen(self):
        print('Listening for incoming messages...')
        # Listen for incoming messages
        while True:
            data, address = self.recv_socket.recvfrom(1024)
            print('Received message from {}:{}'.format(address[0], address[1]))
            jsonStr = data.decode("utf-8")
            message = json.loads(json.loads(jsonStr), cls=MessageDecoder)
            if message.type == MessageType.DISCOVERY_REQ:
                # Reply with its own address
                reply = Message(host=self.host, port=self.port, message="",
                                type=MessageType.DISCOVERY_RES)
                self.recv_socket.sendto(str.encode(
                    MessageEncoder().encode(reply)), address)
            elif message.type == MessageType.DISCOVERY_RES:
                self.on_discovery(message)
            elif message.type == MessageType.MESSAGE:
                self.on_message(message, address)

    def terminate(self):
        self._stop_req = True
        pass

    def start_listening(self):
        listener_thread = Thread(
            target=self.listen)
        listener_thread.daemon = True
        listener_thread.start()
        listener_thread.join()

    def start_send_discovery(self):
        discovery_thread = Thread(
            target=self.send_discovery_message)
        discovery_thread.daemon = True
        discovery_thread.start()
        discovery_thread.join()


if __name__ == '__main__':
    load_dotenv()
    discovery = Discovery("127.0.0.1", port=3004,
                          broadcast_port=os.getenv('BROADCAST_PORT'))
    discovery.send_discovery_message()
