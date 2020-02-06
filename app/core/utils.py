import binascii
import codecs
import hashlib
import os
import re
import datetime

import base58
import ecdsa
import unidecode
from ecdsa import SigningKey, VerifyingKey


def hash_password(password):
    """hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    """verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def get_keys():
    keys = {}
    sk = SigningKey.generate(curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256)
    prkey = sk.to_string()
    keys['private_key'] = codecs.encode(prkey, 'hex').decode("utf-8")

    vk = sk.get_verifying_key()
    pbkey = vk.to_string()
    keys['public_key'] = codecs.encode(pbkey, 'hex').decode("utf-8")

    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(hashlib.sha256(pbkey).digest())
    middle_man = ('\00').encode() + ripemd160.digest()
    checksum = hashlib.sha256(hashlib.sha256(middle_man).digest()).digest()[:4]
    binary_addr = middle_man + checksum
    keys['wallet_key'] = base58.b58encode(binary_addr).decode("utf-8")

    return keys


def get_sign(wallet_key, public_key, private_key):
    sk = SigningKey.from_string(private_key, curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256)
    vk = VerifyingKey.from_string(public_key, curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256)
    sig = sk.sign(wallet_key.encode())

    return codecs.encode(sig, 'hex').decode("utf-8")


def split_to_array(value, delimeter):
    return [unidecode.unidecode(x).lower() for x in re.split(delimeter, value)]


def convert_to_date(value, fmt='%d.%m.%Y %H:%M:%S.%f'):
    if isinstance(value, (datetime.date, datetime.datetime):
        return value
        
    return datetime.datetime.strptime(value, fmt)


def json_default(value):
    if isinstance(value, datetime):
        return "%s/%s/%s %s:%s:%s" % (value.day, value.month, value.year, value.hour, value.minute, value.second)
    else:
        return value.__dict__


def get_key_value_tuple(data: dict, key: str, value: str):
    result = []
    for row in data:
        result.append((row[key], row[value]))
    return result


def get_name_with_suffix(name) -> str:
    vowels = 'aıouAIOUeiöüEİÖÜ'

    if vowels.find(str(name[-1:])) != -1:
        if vowels.find(str(name[-1:])) < 9:
            return "%s'ya" % name
        else:
            return "%s'ye" % name
    else:
        if vowels.find(str(name[-2:1])) < 9:
            return "%s'a" % name
        else:
            return "%s'e" % name

    return name
