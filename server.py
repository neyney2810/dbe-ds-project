import threading
import socket
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv

import sys

from discovery import Discovery
from lib.election import Node


class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        super(Server, self).__init__()

        self.port = port

        # Auto setup server socket and host
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()
        self.host = host
        server_config = (host, port)
        self.server_socket.bind(server_config)

        self.server_socket.listen()

        # For automatic discovery of host
        self._discovery_thread = Discovery(
            self.host, port=self.port, broadcast_port=os.getenv('BROADCAST_PORT'), on_message=self.on_message)
        address = (self.host, self.port)
        self.discovered_nodes = set().add(address)

        # For ring and election
        self.election = Node()
        self.leader_address = ()  # Address of the leader host with port

    def run(self) -> None:
        print(self.get_election())
        self.get_network()
        self.start_listen_broadcast()
        self.thread_listen_msg()

    # ________chatting function _______________

    def thread_listen_msg(self):
        client_sock, client_address = self.server_socket.accept()
        print('Accepted connection from {}:{}'.format(
            client_address[0], client_address[1]))
        t = threading.Thread(target=self._msgHandler,
                             args=(client_sock, client_address), daemon=True)
        t.start()
        t.join()

    def _msgHandler(self, clientsocket, addr):
        while True:
            msg = clientsocket.recv(1024)
            # do some checks and if msg == someWeirdSignal: break:
            print(addr, ' >> ', msg)
            # Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
            clientsocket.send(msg)
        clientsocket.close()

    # ________broadcast listener _________________

    def start_listen_broadcast(self):
        self._discovery_thread.set_on_message(self.on_message)
        self._discovery_thread.start_listening()

    def on_message(self, message, address):
        print('On message message: {} from {}'.format(message, address))

    # _______basic replica communication_________________
    def send_message(self, message, address):
        pass

    # _______leader, worker and leader election_________________

    def get_network(self):
        self._discovery_thread.set_on_discovery(self.on_discovery)
        self._discovery_thread.send_discovery_message()

    def on_discovery(self, message):
        self.discovered_nodes.add((message.host, message.port))
        print('Received new node. Total {}'.format(self.discovered_nodes))

    def on_no_discovery(self):
        print('No nodes discovered. Raise myself as leader')
        self.election.leader(self.port)

    def get_election(self):
        return self.election


if __name__ == "__main__":
    load_dotenv()
    print(os.getenv('BROADCAST_PORT'))
    port = sys.argv[1] if len(sys.argv) > 1 else 3000

    try:
        port = int(port)
        Server_m = Server(port)
        Server_m.start()
    except TypeError:
        print("Invalid port number")
        sys.exit(1)
