import json

from app.services.utils import *
from .constants import Globals


class KeyValuePair:

    def __init__(self, id, value) -> None:
        self.id = id
        self.value = value

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, value):
        self.__id = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    def __repr__(self):
        return "<KeyValuePair id:%s value:%s/>" % (self.id, self.value)


class Content:
    '''

    Message
    {   'sender': '905332108311',
        'type': 'M',
        'msgid': 2419314,
        'sendtime': '29.03.2019 23:31:23.541 +0300',
        'content': 'sss',
        'txnid': 'UAab6Olf-89',
        'nickname': 'semudu',
        'ctype': 'T',
        'postback' : {
            'postbackid': 'qqq',
            'payload': 'asdas'
        },
        'poll': {
            'pollid': 'sss',
            'optionids': 'sss'
        }
    }

    Buzz
    {   'sender': '905332108311',
        'type': 'M',
        'msgid': 2419485,
        'sendtime': '30.03.2019 20:26:05.043 +0300',
        'txnid': '1vdvun90-77',
        'nickname': 'semudu',
        'ctype': 'Buzz'
    }

    '''

    def __init__(self, content_json):
        self.sender = content_json.get("sender")
        self.type = content_json.get("type")
        self.msgid = content_json.get("msgid")
        self.sendtime = content_json.get("sendtime")
        self.content = content_json.get("content")
        self.txnid = content_json.get("txnid")
        self.nickname = content_json.get("nickname")
        self.ctype = content_json.get("ctype")
        if "postback" in content_json:
            self.postback = content_json.get("postback")
        else:
            self.postback = None

        if "poll" in content_json:
            self.poll = content_json.get("poll")
        else:
            self.poll = None

    @property
    def sender(self):
        return self.__sender

    @sender.setter
    def sender(self, value):
        self.__sender = value[-10:]

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value):
        self.__type = value

    @property
    def msgid(self):
        return self.__msgid

    @msgid.setter
    def msgid(self, value):
        self.__msgid = value

    @property
    def sendtime(self):
        return self.__sendtime

    @sendtime.setter
    def sendtime(self, value):
        self.__sendtime = convert_to_date(value[:23])

    @property
    def content(self):
        return self.__content

    @content.setter
    def content(self, value):
        self.__content = value
        self.__commands = split_to_array(value, Globals.DELIMITER) if value else [""]

    @property
    def txnid(self):
        return self.__txnid

    @txnid.setter
    def txnid(self, value):
        self.__txnid = value

    @property
    def nickname(self):
        return self.__nickname

    @nickname.setter
    def nickname(self, value):
        self.__nickname = value

    @property
    def ctype(self):
        return self.__ctype

    @ctype.setter
    def ctype(self, value):
        self.__ctype = value.lower() if value else ""

    @property
    def postback(self):
        return self.__postback

    @postback.setter
    def postback(self, value):
        if value:
            self.__postback = KeyValuePair(value.get("postbackid"),
                                           split_to_array(value.get("payload").lower(), Globals.DELIMITER) if value.get(
                                               "payload") else [""])
        else:
            self.__postback = KeyValuePair(None, [None])

    @property
    def poll(self):
        return self.__poll

    @poll.setter
    def poll(self, value):
        if value:
            self.__poll = KeyValuePair(
                split_to_array(value.get("pollid"), Globals.DELIMITER) if value.get("pollid") else [""],
                value.get("optionids"))
        else:
            self.__poll = KeyValuePair([None], [None])

    @property
    def commands(self):
        return self.__commands

    @property
    def command(self):
        return self.__commands[0]

    @property
    def payload(self):
        return self.__postback.value[0]

    @property
    def payloads(self):
        return self.__postback.value

    @property
    def poll_id(self):
        return self.__poll.id[0]

    @property
    def poll_value(self):
        return self.__poll.value[0]

    @property
    def poll_ext(self):
        return self.__poll.id[1]

    @property
    def poll_secret(self):
        return self.__poll.id[2]

    @property
    def toJSON(self):
        return json.dumps(self, default=json_default,
                          sort_keys=True, indent=4)

    def __repr__(self):
        return "<Content sender:%s type:%s msgid:%s sendtime:%s content:%s txnid:%s nickname:%s ctype:%s postback:%s poll:%s />" % (
            self.sender, self.type, self.msgid, self.sendtime, self.content, self.txnid, self.nickname, self.ctype,
            self.postback, self.poll)
