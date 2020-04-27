import binascii
import datetime
import hashlib
import os
import re

from app.common.constants.globals import Globals


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


def split_to_array(value, delimeter):
    return [x.translate({ord(u'I'): u'ı', ord(u'İ'): u'i'}).lower() for x in re.split(delimeter, value)]


def capitalize_each_word(value):
    return value.translate({ord(u'I'): u'ı', ord(u'İ'): u'i'}).title()


def convert_to_date(value, fmt='%d.%m.%Y %H:%M:%S.%f'):
    if isinstance(value, (datetime.date, datetime.datetime)):
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
    name = capitalize_each_word(name)

    if vowels.find(str(name[-1:])) != -1:
        if vowels.find(str(name[-1:])) < 9:
            return "%s'ya" % name
        else:
            return "%s'ye" % name
    else:
        if vowels.find(str(name[-2:-1])) < 9:
            return "%s'a" % name
        else:
            return "%s'e" % name


def get_de_da_suffix(name) -> str:
    vowels = 'aıouAIOUeiöüEİÖÜ'
    name = capitalize_each_word(name)

    if vowels.find(str(name[-1:])) != -1:
        if vowels.find(str(name[-1:])) < 9:
            return "%s da" % name
        else:
            return "%s de" % name
    else:
        if vowels.find(str(name[-2:-1])) < 9:
            return "%s da" % name
        else:
            return "%s de" % name


def get_name_with_own_suffix(name) -> str:
    vowels = 'aıouAIOUeiöüEİÖÜ'
    name = capitalize_each_word(name)

    if vowels.find(str(name[-1:])) != -1:
        if vowels.find(str(name[-1:])) < 9:
            return "%s' nın" % name
        else:
            return "%s' nin" % name
    else:
        if vowels.find(str(name[-2:-1])) < 9:
            return "%s' ın" % name
        else:
            return "%s' in" % name


def is_after_minutes(date, minutes):
    return (datetime.datetime.now() - datetime.timedelta(minutes=minutes)) > date


def now(fmt="%d.%m.%Y %H:%M:%S.%f"):
    return datetime.datetime.now().strftime(fmt)


def get_yes_no_tuple(yes_id):
    return [
        (yes_id, "Evet"),
        (Globals.NO, "Hayır")
    ]
