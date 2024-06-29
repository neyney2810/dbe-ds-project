# Defined a class to calculate the election results based on the input data.

import json
from multiprocessing import Manager, Process
from multiprocessing.shared_memory import ShareableList
import time

from lib.address import Address
from lib.logger import Logger
from lib.message import Message, MessageEncoder, MessageType


class Node:
    # Address is the primary address of the node which is used for client communication
    address = Address()
    # replica address for internode communication, normally get the same host with address but different port
    replica_address = Address()

    def __init__(self, address=Address(), replica_address=Address()) -> None:
        self.address = address
        self.replica_address = replica_address
        self.id = self.toJSON()

    def __str__(self):
        return "[Address: {}, Replica Address: {}]".format(self.address, self.replica_address)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.address == other.address

    def __iter__(self):
        return iter(self.address)

    def __len__(self):
        return len(self.address)

    def toJSON(self):
        return json.dumps({
            'address': self.address.toJSON(),
            'replica_address': self.replica_address.toJSON()
        })

    @staticmethod
    def fromJSON(address: str):
        data = json.loads(address)
        return Node(Address.fromJSON(data['address']), Address.fromJSON(data['replica_address']))


class RingMember(Node):
    participant = False
    nodes = []  # List of nodes address in the ring

    def __init__(self, address=Address(), send=lambda msg, adr: None, replica_address=Address()) -> None:
        super().__init__(address, replica_address)
        self.next_node_alive = True
        self.sock_send = send
        self.address = address
        self.replica_address = replica_address
        self.nodes = ShareableList(name="replica_list"+str(address.port))
        self.leader_id = ShareableList(name="leader_id"+str(address.port))
        self._logger = Logger()
        self.is_sending_heartbeat = False

    def send_next_node(self, type, id):
        # send to next node
        next_node = self.get_next_node()
        if next_node is not None:
            elect_msg = Message(host=self.address.host, port=self.address.port, message=id,
                                type=type)
            return self.sock_send(MessageEncoder().encode(
                elect_msg), next_node.replica_address)
        return None

    def send_leader(self, type, id):
        # send to leader node
        print('Sending LEADER to {}'.format(self.leader_id[0]))
        # if next_node is not None:
        #     elect_msg = Message(host=self.address.host, port=self.address.port, message=id,
        #                         type=type)
        #     self.sock_send(MessageEncoder().encode(
        #         elect_msg), self.replica_address)

    # Ring formation
    def form_ring(self):
        sorted_list = sorted(
            [node for node in self.nodes if not node.startswith(' ')])
        for i in range(len(sorted_list)):
            if (i + 1) <= len(sorted_list):
                self.nodes[i] = sorted_list[i]
            else:
                self.nodes[i] = " "
        ns = [Node.fromJSON(node).address for node in sorted_list]
        print('Ring formed: {}'.format(ns))

    def get_next_node(self):
        node_list = sorted(
            [node for node in self.nodes if not node.startswith(' ')])\

        if len(node_list) == 0 or len(node_list) == 1:
            return None
        json_node = Node(address=self.address,
                         replica_address=self.replica_address).toJSON()
        current_index = node_list.index(json_node)
        if current_index + 1 < len(node_list):
            n = Node.fromJSON(node_list[current_index + 1])
            self._logger.log_replica('Next node is {}:{}'.format(
                n.address.host, n.address.port))
            return n
        n = Node.fromJSON(node_list[0])
        self._logger.log_replica('Next node is {}:{}'.format(
            n.address.host, n.address.port))
        return n

    def join_ring(self):
        # Query neighbor for the current leader
        leader_id = self.send_next_node(MessageType.GET_LEADER, "")
        self.leader_id[0] = json.dumps(leader_id)
        self._logger.log_replica('Leader is {}'.format(self.leader_id[0]))

    def get_ring(self):
        node_list = [Node.fromJSON(node)
                     for node in self.nodes if not node.startswith(' ')]
        return node_list

    def is_leader(self):
        return self.leader_id[0] == self.id

    def inititate_election(self):
        # Initiate the election process
        # If ring has only 1 member, then it is the leader
        if len(self.nodes) == 1:
            self.raise_leader()
        else:
            # send(self.id, 'ELECTION')
            self.send_next_node(MessageType.ELECTION_REQ, self.id)
            self.participant = True

    # Upon receiving a message ELECTION(j)
    def receive_election(self, id):
        # if (j > my_id) then send(ELECTION, j);
        if id > self.id:
            # send(id, 'ELECTION')
            self.send_next_node(MessageType.ELECTION_REQ, id)
            # else if (my_id = j) then send(LEADER(my_id));
            print('Sending ELECTION to {}'.format(id))
        elif id == self.id:
            # send(id, 'LEADER')
            self.send_next_node(MessageType.LEADER_REQ, id)
            self.leader_id[0] = self.id

        # if ((my_id > j) ^ (¬participant)) then send ELECTION(my_id));
        if self.id > id and not self.participant:
            # send(self.id, 'ELECTION')
            self.inititate_election()
        self.participant = True

    # Upon receiving a message LEADER(j):
    def receive_leader(self, leader_id):
        self.leader_id[0] = leader_id
        if self.id != leader_id:
            # send(LEADER, j)
            self.send_next_node(MessageType.LEADER_REQ, leader_id)
        pass

    def raise_leader(self):
        self.leader_id[0] = self.id
        print('I am the leader', self.leader_id[0])
        pass

    def start_p_send_heartbeat(self):
        print('Starting heartbeat')
        self.send_heartbeat_p = Process(target=self.send_heartbeat)
        self.send_heartbeat_p.start()

    def send_heartbeat(self):
        while True:
            time.sleep(10)  # Heartbeat interval
            next_node = self.get_next_node()
            if next_node is not None:
                message = self.send_next_node(MessageType.PING_REQ, self.id)
                if message is None:
                    print('Node is dead')
                    # remove nodes from the list
                    self.remove_node(next_node)
                    # refresh the ring
                    self.form_ring()
                    # broadcast removal of node
                    self.send_remove_node(next_node)
                    if (next_node.toJSON() == self.leader_id[0]):
                        # start the election process
                        self.inititate_election()

    def send_remove_node(self, node):
        self.send_next_node(MessageType.REMOVE_NODE, node.toJSON())
        pass

    def receive_heartbeat(self, node_id):
        print(f"Received heartbeat from next node")

    def set_nodes(self, nodes):
        self.nodes = nodes

    def remove_node(self, node):
        # Remove node from the list
        node_json = node.toJSON()
        for i in range(len(self.nodes)):
            if self.nodes[i] == node_json:
                self.nodes[i] = " "
                break
        print('Node removed from the list')

    def __str__(self):
        return "Election: {} Leader: {}".format(self.id, self.leader_id)
