import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class StreamEngine:
    def __init__(self, key: bytes, nonce: bytes):
        self.algorithm = algorithms.AES(key)
        self.mode = modes.CTR(nonce)
        self.cipher = Cipher(self.algorithm, self.mode, backend=default_backend())

    def encryptor(self):
        return self.cipher.encryptor()

    def decryptor(self):
        return self.cipher.decryptor()


def generate_key():
    return os.urandom(32)


def generate_nonce():
    return os.urandom(16)
