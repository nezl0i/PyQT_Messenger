import sys
import os
import json
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from common.utils import get_message, send_message


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):

        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'Test_Guest'
        }
    }
    test_dict_recv_200 = {RESPONSE: 200}

    test_dict_recv_400 = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send)
        self.assertEqual(test_socket.encoded_message, test_socket.received_message)
        self.assertRaises(TypeError, send_message, test_socket, "bad dictionary")

    def test_get_message(self):
        test_sock_200 = TestSocket(self.test_dict_recv_200)
        test_sock_400 = TestSocket(self.test_dict_recv_400)
        self.assertEqual(get_message(test_sock_200), self.test_dict_recv_200)
        self.assertEqual(get_message(test_sock_400), self.test_dict_recv_400)


if __name__ == '__main__':
    unittest.main()
