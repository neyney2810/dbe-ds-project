# Test message class

import unittest
from lib.message import Message, MessageType


class TestMessage(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def test_message(self):
        message = Message('Hello', MessageType.MESSAGE)
        self.assertEqual(message.message, 'Hello')
        self.assertEqual(message.type, MessageType.MESSAGE)

    def test_message_to_json(self):
        message = Message('Hello', MessageType.MESSAGE)
        self.assertEqual(message.toJSON(), {
                         'message': 'Hello', 'type': MessageType.MESSAGE})

    def test_message_as_tuple(self):
        message = Message(("hello", "world"), MessageType.MESSAGE)
        print(message.toJSON())
        self.assertEqual(message.toJSON(), {'message': (
            'hello', 'world'), 'type': MessageType.MESSAGE})
