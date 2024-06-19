import socket


class Discovery(object):
    BROADCAST_IP = '192.168.0.255'

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_service(self):
        return 'http://{}:{}'.format(self.host, self.port)

    def broadcast(self, message):
        # Broadcast the message to the network
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Broadcast message
        broadcast_socket.sendto(str.encode(
            message), (self.BROADCAST_IP, self.port))

    def listen(self):
        # Listen for incoming messages
        # Create a UDP socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind((self.host, self.port))
        # Listen for incoming messages
        while True:
            data, address = listen_socket.recvfrom(1024)
            print('Received message from {}:{}'.format(address[0], address[1]))
            print('Message: {}'.format(data.decode()))


def main():
    # Broadcast address and port
    BROADCAST_PORT = 5000

    # Local address and port
    LOCAL_HOST = socket.gethostname()
    LOCAL_IP = socket.gethostbyname(LOCAL_HOST)

    # Create a discovery object
    discovery = Discovery(LOCAL_IP, BROADCAST_PORT)
    message = LOCAL_IP + ' is up and running'
    discovery.broadcast(message)


if __name__ == '__main__':
    main()
