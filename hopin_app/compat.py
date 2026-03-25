import base64
import json
import os

import http_ece
import six
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from requests.structures import CaseInsensitiveDict


def patch_pywebpush_for_cryptography_46():
    try:
        from pywebpush import WebPusher
    except Exception:
        return

    if getattr(WebPusher.encode, "_hopin_patched", False):
        return

    def encode(self, data, content_encoding="aes128gcm"):
        if not data:
            return
        if not self.auth_key or not self.receiver_key:
            raise self.WebPushException("No keys specified in subscription info")

        salt = None
        if content_encoding not in self.valid_encodings:
            raise self.WebPushException(
                "Invalid content encoding specified. Select from " +
                json.dumps(self.valid_encodings)
            )

        if content_encoding == "aesgcm":
            salt = os.urandom(16)

        # cryptography>=46 requires an EllipticCurve instance, not the class.
        server_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        crypto_key = server_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        if isinstance(data, six.string_types):
            data = bytes(data.encode("utf8"))

        if content_encoding == "aes128gcm":
            encrypted = http_ece.encrypt(
                data,
                salt=salt,
                private_key=server_key,
                dh=self.receiver_key,
                auth_secret=self.auth_key,
                version=content_encoding,
            )
            reply = CaseInsensitiveDict({"body": encrypted})
        else:
            crypto_key = base64.urlsafe_b64encode(crypto_key).strip(b"=")
            encrypted = http_ece.encrypt(
                data,
                salt=salt,
                private_key=server_key,
                keyid=crypto_key.decode(),
                dh=self.receiver_key,
                auth_secret=self.auth_key,
                version=content_encoding,
            )
            reply = CaseInsensitiveDict({
                "crypto_key": crypto_key,
                "body": encrypted,
            })
            if salt:
                reply["salt"] = base64.urlsafe_b64encode(salt).strip(b"=")

        return reply

    from pywebpush import WebPushException

    WebPusher.WebPushException = WebPushException
    encode._hopin_patched = True
    WebPusher.encode = encode
