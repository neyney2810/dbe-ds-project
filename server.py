import json
from multiprocessing.shared_memory import ShareableList
from multiprocessing import Lock, Manager, Process
from multiprocessing.sharedctypes import Value, Array
import signal
import socket
import os
from dotenv import load_dotenv
import sys

from lib.clock import VectorClock
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

        # Auto setup server socket and host
        socket_created = False
        while not socket_created:
            try:
                self.server_socket = self._create_server_socket(
                    self.host, self.port)
                socket_created = True
            except OSError:
                self.port += 1

        # Sharable list
        nr_replicas = int(os.getenv('MAX_REPLICA') or 3)
        self._create_shared_memory(nr_replicas)

        # Logger
        self._logger = Logger()

        # For ring and election
        self._internal_msg_handler = InternalMessageHandler(server_address=Address(
            host=self.host, port=self.port))
        replica_address = Address(
            self._internal_msg_handler.host, self._internal_msg_handler.port)
        self.id = self._internal_msg_handler.election.id

        # For automatic discovery of host
        self._discovery_thread = Discovery(
            self.host, port=self.port, broadcast_port=os.getenv('BROADCAST_PORT'))
        self._discovery_thread.on_discovery = self.on_discovery
        self._discovery_thread.on_finish_discovery = self.on_finish_discovery
        self._discovery_thread.set_replica_address(replica_address)
        self._discovery_thread.set_on_message(self.on_message)

        # Global vectorclock
        self._client_list = []

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

    def _create_server_socket(self, host, port):
        server_config = (host, port)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(server_config)
        server_socket.listen()
        return server_socket

    def process_listen_client(self):
        self._logger.log_client('Server started listening on {}:{}'.format(
            self.host, self.port))
        self._vector_clock = VectorClock(self.id)
        while True:
            client_soc, address = self.server_socket.accept()
            print('Connected by {}:{}'.format(address[0], address[1]))
            if client_soc not in self._client_list:
                self._client_list.append(client_soc)
            t = Process(target=self._msgHandler,
                        args=(client_soc, address, self._vector_clock))
            t.start()

    def _msgHandler(self, client_sock, addr, vector_clock: VectorClock):
        while True:
            data = client_sock.recv(1024)
            if len(data) == 0:
                break
            print(addr, ' >> ', data)
            vector_clock.increment(self.id)
            message = json.loads(data.decode())
            self.broadcast_client_message(message, client_sock)

    def broadcast_client_message(self, message, sock):
        for client in self._client_list:
            try:
                client.send(str.encode(json.dumps(message)))
            except BrokenPipeError:
                self._client_list.remove(client)
                print('Client disconnected')

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

    def _create_shared_memory(self, nr_replicas):
        try:
            port = self.port
            self._replica_list = ShareableList(
                [" " * 256] * nr_replicas, name="replica_list"+str(port))
            self._leader_id = ShareableList(
                [" " * 256], name="leader_id"+str(port))
        except FileNotFoundError as e:
            ShareableList(name="replica_list"+str(port)).shm.close()
            ShareableList(name="replica_list"+str(port)).shm.unlink()
            ShareableList(name="leader_id"+str(port)).shm.close()
            ShareableList(name="leader_id"+str(port)).shm.unlink()
            self._replica_list = ShareableList(
                [" " * 256] * nr_replicas, name="replica_list"+str(port))
            self._leader_id = ShareableList(
                [" " * 256], name="leader_id"+str(port))

    def shutdown(self):
        self._discovery_thread.terminate()
        self._leader_id.shm.close()
        self._leader_id.shm.unlink()
        self._replica_list.shm.close()
        self._replica_list.shm.unlink()
        self._internal_msg_handler.terminate()
        self.server_socket.close()
        self._discovery_thread.terminate()
        self._logger.log_sys('Server shutdown')


def set_leader_id(d, port, leader_id):
    d['leader_id'+str(port)] = leader_id
    print(Manager().dict().get('leader_id'+str(port)))


if __name__ == "__main__":
    load_dotenv()
    port = sys.argv[1] if len(sys.argv) > 1 else 3000
    os.system('cls||clear')

    try:
        host = socket.gethostbyname(socket.gethostname())
        port = int(port)
        server = Server(host, port)

        signal.signal(signal.SIGINT, lambda s, f: server.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: server.shutdown())

        server.run()

    except TypeError as e:
        print("Type Error", e)
        print("Invalid port number")
        sys.exit(1)
