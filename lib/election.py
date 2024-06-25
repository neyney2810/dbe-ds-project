# Defined a class to calculate the election results based on the input data.

import time

from lib.address import Address
from lib.message import Message, MessageType


class Node:
    # Address is the primary address of the node which is used for client communication
    address = Address()
    # replica address for internode communication, normally get the same host with address but different port
    replica_address = Address()

    def __init__(self, address=Address(), replica_address=Address()) -> None:
        self.address = address
        self.replica_address = replica_address
        self.id = str(address.host) + ":" + str(address.port)

    def __str__(self):
        return "[Address: {}, Replica Address: {}]".format(self.address, self.replica_address)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.address == other.address

    def __hash__(self):
        return hash(self.address)

    def __iter__(self):
        return iter(self.address)

    def __getitem__(self, index):
        return self.address[index]

    def __len__(self):
        return len(self.address)


class RingMember(Node):
    participant = False
    leader_id = None
    nodes = []  # List of nodes address in the ring

    def __init__(self, address=Address(), send=lambda msg, adr: None, replica_address=Address(), nodes=[]) -> None:
        super().__init__(address, replica_address)
        self.alive = True
        self.sock_send = send
        self.address = address
        self.replica_address = replica_address
        self.nodes = nodes

    def send(self, type, id):
        # send to next node
        next_node = self.get_next_node()
        if next_node is not None:
            elect_msg = Message(host=self.address.host, port=self.address.port, message=id,
                                type=type)
            self.sock_send(elect_msg, self.replica_address)

    # Ring formation
    def form_ring(self):
        print("Form ring", [node for node in self.nodes])
        self.nodes = sorted([node.id for node in self.nodes])
        print("Sorted ring", self.nodes)
        return self.nodes

    def get_next_node(self):
        if len(self.nodes) == 0 or len(self.nodes) == 1:
            return None
        current_index = self.nodes.index(self.id)
        if current_index + 1 < len(self.nodes):
            return self.nodes[current_index + 1]
        return self.nodes[0]

    def join_ring(self):
        # Query neighbor for the current leader
        self.send(MessageType.GET_LEADER, "")

    def is_leader(self):
        return self.leader_id == self.id

    def inititate_election(self):
        # Initiate the election process
        # send(self.id, 'ELECTION')
        self.send(MessageType.ELECTION_REQ, self.id)
        self.participant = True

    # Upon receiving a message ELECTION(j)
    def receive_election(self, id):
        # if (j > my_id) then send(ELECTION, j);
        if id > self.id:
            # send(id, 'ELECTION')
            self.send(MessageType.ELECTION_REQ, id)
            # else if (my_id = j) then send(LEADER(my_id));
            print('Sending ELECTION to {}'.format(id))
        elif id == self.id:
            # send(id, 'LEADER')
            self.send(MessageType.LEADER_REQ, id)
            self.leader_id = self.id
        # if ((my_id > j) ^ (¬participant)) then send(ELECTION(my_id));
        elif self.id > id and not self.participant:
            # send(self.id, 'ELECTION')
            self.inititate_election()
        self.participant = True

    # Upon receiving a message LEADER(j):
    def leader(self, leader_id):
        self.leader_id = leader_id
        if self.id != leader_id:
            # send(LEADER, j)
            self.send(MessageType.LEADER_REQ, leader_id)

    def raise_leader(self):
        # send(LEADER, my_id)
        self.send(MessageType.LEADER_REQ, self.id)
        print('I am the leader')

    def send_heartbeat(self):
        while self.alive:
            time.sleep(10)  # Heartbeat interval
            print(f"Node {self.node_id} sending heartbeat")
            if self.get_next_node() is not None:
                self.send(MessageType.PING_REQ, self.id)

    def receive_heartbeat(self, node_id):
        print(f"Node {self.node_id} received heartbeat from Node {node_id}")

    def set_nodes(self, nodes):
        self.nodes = nodes

    def __str__(self):
        return "Election: {} Leader: {}".format(self.id, self.leader_id)
