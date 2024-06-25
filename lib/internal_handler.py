import json
from multiprocessing import Process
import os
import socket
import time

from lib.address import Address
from lib.election import Node, RingMember
from lib.message import Message, MessageDecoder, MessageEncoder, MessageType
from lib.logger import Logger


# Handling message between replica nodes of server
class InternalMessageHandler(Process):
    def __init__(self, server_address):
        super(InternalMessageHandler, self).__init__()
        self._logger = Logger()

        server_address = server_address
        self.host = socket.gethostbyname(socket.gethostname())
        self.status = 'up'
        self.last_heartbeat = time.time()

        if (os.getenv('REPLICA_PORT') and os.getenv('REPLICA_PORT').isdigit()):
            self.port = int(os.getenv('REPLICA_PORT'))

        self.sock = None
        while self.sock is None:
            try:
                self._create_socket(self.port)
            except OSError:
                self.port += 1
        replica_address = Address(self.host, self.port)

        # Once open socket successfully, start ring setup and election
        self.nodes = list()
        node_address = Node(address=server_address,
                            replica_address=replica_address)
        self.nodes.append(node_address)
        self.election = RingMember(address=server_address, replica_address=Address(
            self.host, self.port), send=self.send_message, nodes=list(self.nodes))

        print("Finished init InternalMessageHandler with nodes", self.nodes)

    def run(self):
        # Start listening for messages
        self.listen_message()

    def _create_socket(self, port):
        self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        conf = ("", port)
        self.sock.bind(conf)

    def listen_message(self):
        self.sock.listen()
        while True:
            data, address = self.sock.recvfrom(1024)
            jsonStr = data.decode("utf-8")
            message = json.loads(json.loads(jsonStr), cls=MessageDecoder)
            self._logger.log_replica(
                'Received replica message: {} from {}'.format(message, address))
            process = Process(target=self.process_message,
                              args=(message, address), daemon=True)
            process.start()
            process.join()

    def process_message(self, message, client_address):
        self._logger.log_replica('Processing replica message: {} from {}'.format(
            message, client_address))
        if message.type == 'ELECTION_REQUEST':
            self.election.receive_election(message.message)
        # elif message.type == 'ELECTION_RESPONSE':
        #     self.election.receive_election_response(message.message)
        # elif message.type == 'LEADER_REQUEST':
        #     self.election.receive_leader(message.message)
        # elif message.type == 'LEADER_RESPONSE':
        #     self.election.receive_leader_response(message.message)
        elif message.type == MessageType.PING_REQ:
            res = Message(host=self.host, port=self.port, message=id,
                          type=type)
            self.sock.sendto(MessageEncoder().encode(res), client_address)
            self._logger.log_replica(
                'Sending replica message: {} to {}'.format(res, client_address))
        elif message.type == MessageType.PING_RES:
            node_id = str(client_address[0]) + ':' + str(client_address[1])
            self.election.receive_heartbeat(node_id)

    def send_message(self, message, address):
        self.sock.settimeout(5)
        try:
            self._logger.log_replica(
                'Sending replica message: {} to {}'.format(message, address))
            data, res_adr = self.sock.sendto(str.encode(
                message), (address.host, message.port))
            self._logger.log_replica("Response", data, res_adr)
        except socket.timeout:
            self._logger.log_replica('Replica message timed out.')

    def add_node(self, node):
        # New node: broadcast to all nodes to ask leader
        # if receive no response, initiate election

        if node in self.nodes:
            return  # Node already exists, no need to add again
        self.nodes.append(node)
        self.election.nodes = list(self.nodes)
        self.election.form_ring()
        self._logger.log_replica('Current nodes: {}'.format(self.get_nodes()))

    def remove_node(self, node):
        self.nodes.remove(node)
        self.election.set_nodes(list(self.nodes))

    def query_next_node_for_leader(self):
        # If alone become leader
        if len(self.election.nodes) <= 1:
            self.election.raise_leader()
        else:
            next_node = self.election.get_next_node()
            print('Querying next node for leader: {}'.format(next_node))
        pass

    def get_nodes(self):
        return self.nodes

    def __str__(self):
        return f'{self.name} ({self.address})'

    def __repr__(self):
        return self.__str__()

    def is_up(self):
        return self.status == 'up'

    def is_down(self):
        return self.status == 'down'

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def down(self):
        self.status = 'down'

    def up(self):
        self.status = 'up'

    def to_dict(self):
        return {
            'name': self.name,
            'address': self.address,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat
        }

    @ staticmethod
    def from_dict(replica_dict):
        replica = InternalMessageHandler(
            replica_dict['name'], replica_dict['address'])
        replica.status = replica_dict['status']
        replica.last_heartbeat = replica_dict['last_heartbeat']
        return replica
