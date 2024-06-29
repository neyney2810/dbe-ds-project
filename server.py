import json
from multiprocessing.shared_memory import ShareableList
from multiprocessing import Manager, Process
import socket
import os
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
class Server():
    def __init__(self, host, port):
        super(Server, self).__init__()

        self.host = host
        self.port = port
        server_config = (host, port)

        # Sharable list
        nr_replicas = int(os.getenv('MAX_REPLICA') or 3)
        self._replica_list = ShareableList(
            [" " * 256] * nr_replicas, name="replica_list"+str(port))
        self._leader_id = ShareableList(
            [" " * 256], name="leader_id"+str(port))

        # Logger
        self._logger = Logger()

        # Auto setup server socket and host
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(server_config)
        self.server_socket.listen()

        # For ring and election
        self._internal_msg_handler = InternalMessageHandler(server_address=Address(
            host=self.host, port=self.port))
        replica_address = Address(
            self._internal_msg_handler.host, self._internal_msg_handler.port)

        # For automatic discovery of host
        self._discovery_thread = Discovery(
            self.host, port=self.port, broadcast_port=os.getenv('BROADCAST_PORT'))
        self._discovery_thread.on_discovery = self.on_discovery
        self._discovery_thread.on_finish_discovery = self.on_finish_discovery
        self._discovery_thread.set_replica_address(replica_address)
        self._discovery_thread.set_on_message(self.on_message)

    def run(self):
        # Get network
        dis_send_p = Process(
            target=self._discovery_thread.send_discovery_message)

        # Broadcast listener
        dis_start = Process(
            target=self._discovery_thread.start_listening)

        # Start replica
        p = Process(
            target=self._internal_msg_handler.listen_message)

        # Chatting function
        t = Process(target=self.process_listen_client)

        dis_send_p.start()
        dis_start.start()
        p.start()
        t.start()

    # ________chatting function _______________

    def process_listen_client(self):
        self._logger.log_client('Server started listening on {}:{}'.format(
            self.host, self.port))
        conn, addr = self.server_socket.accept()
        with conn:
            while True:
                data = conn.recv(1024)
                self._logger.log_client('Accepted connection from {}:{}'.format(
                    addr[0], addr[1]))
                t = Process(target=self._msgHandler,
                            args=(data, conn, addr))
                t.start()
                t.join()

    def _msgHandler(self, data, conn, addr):
        msg = json.loads(data.decode())
        # do some checks and if msg == someWeirdSignal: break:
        print(addr, ' >> ', msg)
        # Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
        conn.sendall(str.encode("OK"), addr)

    # ________broadcast listener _________________

    def on_message(self, message, address):
        print('On message message: {} from {}'.format(message, address))

    # _______leader, worker and leader election_________________
    def get_network(self):
        self._discovery_thread.start_send_discovery()

    def on_discovery(self, message):
        replica_adr_str = message.message
        replica_adr = Address.from_string(replica_adr_str)
        self._internal_msg_handler.add_node(Node(address=Address(
            host=message.host, port=message.port), replica_address=replica_adr))
        self._logger.log_broadcast('Received new server node. Total number: {}'.format(
            [node.address for node in self._internal_msg_handler.election.get_ring()]))
        self._internal_msg_handler.election.form_ring()

    def on_finish_discovery(self):
        self._logger.log_sys('Finished discovery. Start form ring')
        self._logger.log_sys(self._internal_msg_handler.election.get_ring())
        # Start form ring
        if len(self._internal_msg_handler.election.get_ring()) <= 1:
            self._internal_msg_handler.election.raise_leader()
        else:
            self._internal_msg_handler.election.join_ring()
        self._internal_msg_handler.election.start_p_send_heartbeat()


def set_leader_id(d, port, leader_id):
    d['leader_id'+str(port)] = leader_id
    print(Manager().dict().get('leader_id'+str(port)))


if __name__ == "__main__":
    load_dotenv()
    port = sys.argv[1] if len(sys.argv) > 1 else 3000

    try:
        host = socket.gethostbyname(socket.gethostname())
        port = int(port)
        server = Server(host, port)
        server.run()

    except TypeError as e:
        print("Type Error", e)
        print("Invalid port number")
        sys.exit(1)
