import json


class Address:
    def __init__(self, host: str = "", port: int = None):
        self.host = host
        self.port = port

    def __eq__(self, other):
        return self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash((self.host, self.port))

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return iter((self.host, self.port))

    def __getitem__(self, index):
        if index == 0:
            return self.host
        elif index == 1:
            return self.port
        else:
            raise IndexError

    def __len__(self):
        return 2

    def toJSON(self):
        return json.dumps({
            'host': self.host,
            'port': self.port
        })

    def fromJSON(address: str):
        data = json.loads(address)
        return Address(data['host'], data['port'])

    @staticmethod
    def from_string(address: str):
        host, port = address.split(':')
        return Address(host, int(port))
