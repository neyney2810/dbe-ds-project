from enum import Enum
import json


class MessageType(str, Enum):
    MESSAGE = "MESSAGE"
    DISCOVERY_REQ = "DISCOVERY_REQUEST"
    DISCOVERY_RES = "DISCOVERY_RESPONSE"
    ELECTION_REQ = "ELECTION_REQUEST"  # initiate election
    ELECTION_RES = "ELECTION_RESPONSE"
    LEADER_REQ = "LEADER_REQUEST"  # vote for leader with id
    LEADER_RES = "LEADER_RESPONSE"
    PING_REQ = "PING_REQUEST"
    PING_RES = "PING_RESPONSE"
    GET_LEADER = "GET_LEADER"  # new to ring? get leader
    RES_LEADER = "LEADER"
    REMOVE_NODE = "REMOVE_NODE"
    REMOVE_NODE_RES = "REMOVE_NODE_RESPONSE"

    def toJSON(self):
        return self.name


class Message(object):
    type = MessageType.MESSAGE
    message = None
    host = ''
    port = ''

    def __init__(self, message, type, host='', port=''):
        self.message = message
        self.type = type
        self.host = host
        self.port = port

    def __str__(self):
        return 'Message: {} Type: {} Host: {} Port: {}'.format(self.message, self.type, self.host, self.port)

    def toJSON(self):
        return json.dumps({
            'message': self.message,
            'type': self.type,
            'host': self.host,
            'port': self.port
        })


class MessageEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Message):
            return o.toJSON()
        return super().default(o)


class MessageDecoder(json.JSONDecoder):
    def decode(self, s):
        data = json.loads(s)
        return Message(data['message'], data['type'], data['host'], data['port'])


class ChatMessageType(str, Enum):
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    MESSAGE = "MESSAGE"

    def toJSON(self):
        return self.name


class ChatMessage:
    def __init__(self, sender: str, message: str):
        self.sender = sender
        self.message = message

    def __str__(self):
        return 'Message: {} Sender: {}'.format(self.message, self.sender)

    def toJSON(self):
        return json.dumps({
            'message': self.message,
            'sender': self.sender
        })

    @staticmethod
    def fromJSON(data: str):
        data = json.loads(data)
        return ChatMessage(data['message'], data['sender'])
