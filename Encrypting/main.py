import json
import os
import hashlib
import logging
import datetime

'''
from cryptography.fernet import Fernet
key = b'pRmgMa8T0INjEAfksaq2aafzoZXEuwKI7wDe4c1F8AY='
cipher_suite = Fernet(key)
ciphered_text = cipher_suite.encrypt(b"SuperSecretPassword")   #required to be bytes
print(ciphered_text.decode("utf-8"))
unciphered_text = (cipher_suite.decrypt(ciphered_text))
print(unciphered_text.decode("utf-8"))

test = "CIAO".encode('utf-8')

print(test)
'''


def generate_message_hash(message, time=None, secret_key=None, hash_algorithm=None, hash_timeout=None):

    SECRET_KEY      =    os.getenv("SECRET_KEY",                default=None)                       if secret_key       is None else secret_key
    HASH_ALGORITHM  =    os.getenv("HASH_ALGORITHM",            default='sha1')                     if hash_algorithm   is None else hash_algorithm

    if SECRET_KEY is None:
        logging.getLogger().critical('MISSING SECRET_KEY ENV VARIABLE')
        return False, None
    
    message_to_hash = json.dumps(message, sort_keys=True) + SECRET_KEY
    # print('message_to_hash', message_to_hash.encode('utf-8'))

    hash_object = hashlib.new(HASH_ALGORITHM)
    hash_object.update(message_to_hash.encode('utf-8'))
    hash_str = hash_object.hexdigest()
    message_encoded = hash_str.encode('utf-8')
    message_decoded = message_encoded.decode('utf-8')

    return message_encoded, message_decoded




if __name__ == "__main__":
    test = generate_message_hash("CIAO", 10, "ASDFDSAASDF", "sha512_256", 100 )
    print(test)