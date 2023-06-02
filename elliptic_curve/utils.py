import collections
import random
import hashlib
import base64

Coor = collections.namedtuple("Coor", ["x", "y"])


class EllipticCurve:
    def __init__(self, a: int, b: int, mod_p: int, base_point: Coor):
        self.a = a
        self.b = b
        self.mod_p = mod_p
        self.base_point = base_point

    def reduce_mod_p(self, x):
        return x % self.mod_p

    def reduce_inverse_mod_p(self, x):
        if not self.reduce_mod_p(x):
            return None
        # fermat corollary theorem
        return pow(x, self.mod_p - 2, self.mod_p)
        # return pow(x, -1, self.mod_p)

    def is_point_on_curve(self, P: Coor):
        Z = self.reduce_mod_p(P.y ** 2)
        R = self.reduce_mod_p((P.x ** 3) + self.a * P.x + self.b)
        return Z == R

    def point_addition(self, P: Coor, Q: Coor):
        if P is None:
            # if p is infinite return q
            return Q
        if Q is None:
            # if q is infinite return P
            return P

        if P.x == Q.x and P.y != Q.y:
            # infinite point
            return None

        if P == Q:
            # 3x^2 + a / 2y
            # (3x^2 + a) * 2y^-1
            u = self.reduce_mod_p((3 * P.x ** 2 + self.a) * self.reduce_inverse_mod_p(2 * P.y))
        else:
            # (y1 - y2) / (x1 - x2)
            # (y1 - y2) * (x1 - x2)^-1
            u = self.reduce_mod_p((P.y - Q.y) * self.reduce_inverse_mod_p(P.x - Q.x))

        # X = lambda^2  - x1 - x2
        # Y = -lambda*X - y1 + lambda*x1
        X = self.reduce_mod_p(u ** 2 - P.x - Q.x)
        Y = self.reduce_mod_p(u * (P.x - X) - P.y)

        return Coor(X, Y)

    def point_doubling(self, P: Coor):
        if P is None:
            return None

        u = self.reduce_mod_p((3 * P.x ** 2 + self.a) * self.reduce_inverse_mod_p(2 * P.y))
        X = self.reduce_mod_p(u ** 2 - 2 * P.x)
        Y = self.reduce_mod_p(u * (P.x - X) - P.y)

        return Coor(X, Y)

    def scalar_multiplication(self, k: int, P: Coor):
        k = self.reduce_mod_p(k)

        if not k or P is None:
            return None

        Q = None
        while k:
            if k & 1 != 0:
                Q = self.point_addition(Q, P)
            P = self.point_addition(P, P)

            k >>= 1
        return Q

    def generate_keys(self, private_key: int):
        public_key = self.scalar_multiplication(private_key, self.base_point)
        return private_key, public_key

    def generate_random_n(self):
        return random.randint(1, self.mod_p - 1)

    def encrypt(self, message: str, public_key: Coor, common_secret_encryption_point: Coor = None):
        if not common_secret_encryption_point:
            encryption_scalar_key = self.generate_random_n()
            common_secret_encryption_point = self.scalar_multiplication(encryption_scalar_key, self.base_point)
            secret_key = self.scalar_multiplication(encryption_scalar_key, public_key)
        else:
            secret_key = common_secret_encryption_point

        encryption_key = hashlib.sha256(str(secret_key[0]).encode()).digest()

        message_bytes = message.encode()

        # XOR encryption with the encryption key
        encrypted_message = bytearray()
        for i in range(len(message_bytes)):
            encrypted_byte = message_bytes[i] ^ encryption_key[i % len(encryption_key)]
            encrypted_message.append(encrypted_byte)

        base64_bytes = base64.b64encode(encrypted_message)
        return common_secret_encryption_point, str(base64_bytes, 'utf-8')

    def decrypt(self, ciphertext: str, private_key: int, common_secret_encryption_point: Coor):
        secret_key = self.scalar_multiplication(private_key, common_secret_encryption_point)
        encryption_key = hashlib.sha256(str(secret_key[0]).encode()).digest()
        ciphertext = base64.b64decode(ciphertext)
        # XOR decrypt with the encryption key
        decrypted_message = bytearray()
        for i in range(len(ciphertext)):
            decrypted_byte = ciphertext[i] ^ encryption_key[i % len(encryption_key)]
            decrypted_message.append(decrypted_byte)

        try:
            res = str(decrypted_message, 'utf-8')
        except:
            res = ''.join(format(x, '02x') for x in decrypted_message)
        return res

    @staticmethod
    def ones_complement(x: int):
        bin_x = bin(x)
        complement = 0
        for b in bin_x[2:]:
            complement = (complement << 1) + (int(b) ^ 1)
        return complement

