# -*- coding: utf-8 -*-
from .context import tkgtri
from tkgtri import ServerHelper
import unittest
import uuid


class ServerTestSuite(unittest.TestCase):

    def test_create_get_salt(self):
        u = str(uuid.uuid4())
        s = "ABC/XYZ"
        t = "TKG_666"
        ser = ServerHelper()
        self.assertEqual(True, ser.check_secret(ser.get_secret((u, s, t)), (u, s, t)))


if __name__ == '__main__':
    unittest.main()
