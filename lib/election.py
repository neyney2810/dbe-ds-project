# Defined a class to calculate the election results based on the input data.

import uuid

from lib.message import Message, MessageType


class Node:
    participant = False
    leader_id = None
    address = None

    def __init__(self, id=None, address=None, send=lambda msg, adr: print("Send: ", msg, adr)) -> None:
        if id is not None:
            self.id = id
        else:
            self.id = uuid.uuid4()
        self.sock_send = send
        self.next_node = None
        self.address = address

    def send(self, type, id):
        # send to next node
        elect_msg = Message(host=self.address.host, port=self.address.port, message=id,
                            type=type)
        self.sock_send(elect_msg, self.next_node.address)

    def set_next_node(self, next_node):
        self.next_node = next_node

    def is_leader(self):
        return self.leader_id == self.id

    def inititate_election(self):
        # Initiate the election process
        # send(self.id, 'ELECTION')
        self.send(MessageType.ELECTION_REQ, self.id)
        self.participant = True

    # Upon receiving a message ELECTION(j)
    def receive(self, id):
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

    def calculate(self):
        # Calculate the election results
        results = {}
        for candidate in self.data:
            results[candidate] = sum(self.data[candidate])
        return results

    def __str__(self):
        return "Election: {} Leader: {}".format(self.id, self.leader_id)


class LeaderNode(Node):
    def __init__(self, id=None, send=lambda type, id: print("Send: ", type, id)) -> None:
        super().__init__(id, send)
        self.leader_id = self.id

    def setup_ring(self, node_ids):
        # node_ids is of type list
        self.sorted_ids = sorted(node_ids)

    def get_ring(self):
        return self.sorted_ids

    def get_next_node_for(self, id):
        if self.leader_id == id:
            return self.sorted_ids[0]
        else:
            return self.sorted_ids[self.sorted_ids.index(id) + 1]
