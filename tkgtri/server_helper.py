from datetime import datetime
import hashlib


class ServerHelper(object):
    def __init__(self):
        pass

    @staticmethod
    def get_secret(args: list):
            m = hashlib.md5()
            message = "".join(args)
            m.update(message.encode())
            return m.hexdigest()

    def check_secret(self, secret, args):
        hash = self.get_secret(args)
        return True if hash == secret else False

