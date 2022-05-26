import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from server import process_client_message, check_port


class TestServer(unittest.TestCase):
    dict_400 = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }
    dict_200 = {RESPONSE: 200}

    _time = 1650959264.002231

    def test_check(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: self._time, USER: {ACCOUNT_NAME: 'Guest'}}), self.dict_200)

    def test_action(self):
        self.assertEqual(process_client_message(
            {TIME: str(self._time), USER: {ACCOUNT_NAME: 'Guest'}}), self.dict_400)

    def test_wrong_action(self):
        self.assertEqual(process_client_message(
            {ACTION: 'Wrong', TIME: str(self._time), USER: {ACCOUNT_NAME: 'Guest'}}), self.dict_400)

    def test_empty_time(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.dict_400)

    def test_empty_user(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: str(self._time)}), self.dict_400)

    def test_unknown_user(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: self._time, USER: {ACCOUNT_NAME: 'Root'}}), self.dict_400)

    def test_port_ok(self):
        self.assertIn(check_port(5000), range(1024, 65535))

    def test_bad_port(self):
        self.assertNotIn(check_port(500), range(1024, 65535))


if __name__ == '__main__':
    unittest.main()
