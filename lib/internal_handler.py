import json
from multiprocessing import Process
import os
import socket
import time

from lib.address import Address
from lib.election import Node, RingMember
from lib.message import Message, MessageDecoder, MessageEncoder, MessageType
from lib.logger import Logger
from multiprocessing.shared_memory import ShareableList


class InternalMessageHandler():
    def __init__(self, server_address):
        super().__init__()
        self._logger = Logger()

        self.server_address = server_address
        server_address = server_address
        self.host = server_address.host
        self.status = 'up'
        self.last_heartbeat = time.time()

        if (os.getenv('REPLICA_PORT') and os.getenv('REPLICA_PORT').isdigit()):
            self.port = int(os.getenv('REPLICA_PORT'))

        self.sock = None
        while self.sock is None:
            try:
                self._create_socket(self.port)
            except OSError:
                self.sock = None
                self.port += 1
        replica_address = Address(self.host, self.port)

        self.nodes = ShareableList(
            name="replica_list"+str(server_address.port))
        node_address = Node(address=server_address,
                            replica_address=replica_address)
        self.nodes[0] = node_address.toJSON()
        self.election = RingMember(address=server_address, replica_address=Address(
            self.host, self.port), send=self.send_message)

    def _create_socket(self, port):
        self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", port))

    def listen_message(self):
        self._logger.log_replica('Listening for replica messages on {}:{}...'.format(
            self.host, self.port))
        while True:
            data, address = self.sock.recvfrom(1024)
            self._logger.log_replica('Connected by {}'.format(address))
            jsonStr = data.decode("utf-8")
            message = json.loads(json.loads(jsonStr), cls=MessageDecoder)
            t = Process(target=self.process_message,
                        args=(message, address))
            t.start()
            t.join()

    def process_message(self, message, client_address):
        message_type = message.type
        switcher = {
            MessageType.GET_LEADER: self.process_get_leader,
            MessageType.PING_REQ: self.process_ping_req,
            MessageType.PING_RES: self.process_ping_res,
            MessageType.ELECTION_REQ: self.process_election_req,
            MessageType.LEADER_REQ: self.process_leader_req,
            MessageType.REMOVE_NODE: self.process_remove_node,
            MessageType.MESSAGE: self.process_message
        }
        # Get the function to handle the message type
        handler = switcher.get(message_type, self.process_default)
        # Call the handler function with the message and client address
        handler(message, client_address)

    def process_get_leader(self, message, client_address):
        leader_id = ShareableList(
            name="leader_id"+str(self.server_address.port))[0]
        self._logger.log_replica('Leader id: {}'.format(leader_id))
        leader_id = leader_id.strip() if leader_id else ""
        self.sock.sendto(
            str.encode(leader_id), client_address)

    def process_ping_req(self, message, client_address):
        res = Message(host=self.host, port=self.port, message="",
                      type=MessageType.PING_RES)
        res = MessageEncoder().encode(res)
        self._logger.log_replica(
            'PING RESPONSE to {}'.format(client_address))
        self.sock.sendto(
            str.encode(res), client_address)

    def process_ping_res(self, message, client_address):
        node_id = str(client_address[0]) + ':' + str(client_address[1])
        self.election.receive_heartbeat(node_id)

    def process_election_req(self, message, client_address):
        self.election.receive_election(message.message)

    def process_leader_req(self, message, client_address):
        self.election.receive_leader(message.message)

    def process_remove_node(self, message, client_address):
        node = Node.fromJSON(message.message)
        self.remove_node(message.message)
        self.election.form_ring()
        self.election.send_remove_node(node)
        res = Message(host=self.host, port=self.port,
                      message="", type=MessageType.REMOVE_NODE_RES)
        self.sock.sendto(
            str.encode(MessageEncoder().encode(res)), client_address)

    def process_default(self, message, client_address):
        self.election.receive_election(message.message)

    def send_message(self, message, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        try:
            self._logger.log_replica("Sending message to {}".format(address))
            sock.sendto(
                str.encode(message), (address.host, address.port))
            data, addr = sock.recvfrom(1024)
            message = json.loads(data.decode("utf-8"))
            self._logger.log_replica(
                'Received response: {}'.format(message))
            return message
        except socket.timeout:
            self._logger.log_replica('Replica message timed out.')
            return None

    def add_node(self, node):
        # New node: broadcast to all nodes to ask leader
        # if receive no response, initiate election
        node_json = node.toJSON()
        if node_json in self.nodes:
            return  # Node already exists, no need to add again
        # interate throught the array and add the node to the position that is not 0
        for i in range(len(self.nodes)):
            # Check if the element at position i is space string
            if self.nodes[i].startswith(' '):
                self.nodes[i] = node_json
                break

    def remove_node(self, node):
        node_json = node.toJSON()
        # Remove node from the list
        for i in range(len(self.nodes)):
            if self.nodes[i] == node_json:
                self.nodes[i] = " "
                break

    def query_next_node_for_leader(self):
        list = [node for node in self.nodes if not node.startswith(' ')]
        self._logger.log_replica(
            'Querying next node for leader: {}'.format(list))
        # If alone become leader
        if len(self.nodes) <= 1:
            return None
        else:
            next_node = self.election.get_next_node()
            print('Querying next node for leader: {}'.format(next_node))
        pass

    def get_ring(self):
        return [node for node in self.nodes if not node.startswith(' ')]

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
