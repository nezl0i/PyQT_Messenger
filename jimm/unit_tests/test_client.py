import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import create_presence, process_ans


class TestClass(unittest.TestCase):
    def test_presense(self):
        test = create_presence()
        _time = 1650959264.002231
        test[TIME] = _time
        self.assertEqual(test, {ACTION: PRESENCE, TIME: _time, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_200(self):
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')

    def test_400(self):
        self.assertEqual(process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError, process_ans, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
