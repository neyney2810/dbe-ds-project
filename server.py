import multiprocessing
import socket
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv

import sys

from lib.discovery import Discovery
from lib.address import Address
from lib.election import Node
from lib.internal_handler import InternalMessageHandler
from lib.logger import Logger


# Starting point, listening to client messages
# Starting point of network discovery
# Starting point of node and election process
class Server(multiprocessing.Process):
    def __init__(self, port):
        super(Server, self).__init__()

        host = socket.gethostbyname(socket.gethostname())
        self.host = host
        self.port = port
        server_config = (host, port)

        # Logger
        self._logger = Logger()

        # Auto setup server socket and host
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(server_config)
        self.server_socket.listen()

        # For ring and election
        self._internal_msg_handler = InternalMessageHandler(
            server_address=Address(self.host, self.port))
        replica_address = Address(
            self._internal_msg_handler.host, self._internal_msg_handler.port)

        # For automatic discovery of host
        self._discovery_thread = Discovery(
            self.host, port=self.port, broadcast_port=os.getenv('BROADCAST_PORT'))
        self._discovery_thread.set_replica_address(replica_address)

    def run(self):
        self.get_network()
        self.start_listen_broadcast()
        self.thread_listen_msg()
        pass

        # ________chatting function _______________

    def thread_listen_msg(self):
        client_sock, client_address = self.server_socket.accept()
        self._logger.log('Accepted connection from {}:{}'.format(
            client_address[0], client_address[1]))
        t = multiprocessing.Process(target=self._msgHandler,
                                    args=(client_sock, client_address), daemon=True)
        t.start()

    def _msgHandler(self, clientsocket, addr):
        while True:
            msg = clientsocket.recv(1024)
            # do some checks and if msg == someWeirdSignal: break:
            print(addr, ' >> ', msg)
            # Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
            clientsocket.send(msg)

    # ________broadcast listener _________________

    def start_listen_broadcast(self):
        self._discovery_thread.set_on_message(self.on_message)
        self._discovery_thread.start_listening()

    def on_message(self, message, address):
        print('On message message: {} from {}'.format(message, address))

    # _______basic replica communication_________________
    def start_replica(self):
        pass

    # _______leader, worker and leader election_________________
    def get_network(self):
        self._discovery_thread.set_on_discovery(self.on_discovery)
        self._discovery_thread.set_on_finish_discovery(
            self.on_finish_discovery)
        self._discovery_thread.start_send_discovery()

    def on_discovery(self, message):
        replica_adr_str = message.message
        replica_adr = Address.from_string(replica_adr_str)
        self._internal_msg_handler.add_node(Node(address=Address(
            host=message.host, port=message.port), replica_address=replica_adr))
        self._logger.log_broadcast('Received new server node. Total {}'.format(
            self._internal_msg_handler.get_nodes()))
        print("\n")

    def on_finish_discovery(self):
        print('Finished discovery. Start form ring')
        # Start form ring
        print("Form ring", self._internal_msg_handler.nodes,
              self._internal_msg_handler.election.nodes)
        self._internal_msg_handler.election.form_ring()
        # Start get leader, if alone then become leader
        self._internal_msg_handler.query_next_node_for_leader()


if __name__ == "__main__":
    load_dotenv()
    port = sys.argv[1] if len(sys.argv) > 1 else 3000

    try:
        port = int(port)
        Server_m = Server(port)
        Server_m.start()
    except TypeError as e:
        print("Type Error", e)
        print("Invalid port number")
        sys.exit(1)
