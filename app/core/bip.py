import logging

from bipwrapper.api import Api
from bipwrapper.type import *

from .blockchain import Blockchain
from .database import Database
from .model.command import Command
from .model.message import Message


class Bip:
    def __init__(self, config):
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        self.db = Database(config)
        self.blockchain = Blockchain(config)
        self.api = Api(config.api_URL, config.api_USERNAME, config.api_PASSWORD)

    def __send_menu__(self, receiver):
        self.api.one.send_quickreply_message(receiver, "quickmenu", [
            (Command.POINT, "💰 IMS Bakiyem", ButtonType.POST_BACK),
            (Command.LAST_SENT + "-5", "➡️ Son Yolladıklarım", ButtonType.POST_BACK),
            (Command.LAST_RECEIVED + "-5", "⬅️ Son gelenler", ButtonType.POST_BACK),
            (Command.HELP, "❓ Yardım", ButtonType.POST_BACK)
        ])

    def __send_balance__(self, receiver, user_id):
        balance = self.blockchain.get_balance(user_id)
        total_send = self.db.get_total_sent_transaction(user_id)
        total_received = self.db.get_total_received_transaction(user_id)
        self.api.one.send_text_message(receiver, Message.BIP_BALANCE % (balance, total_send, total_received))

    def __send_lastn_sent(self, receiver, user_id, count):
        text = Message.BIP_LAST_SENT % count
        result = self.db.get_lastn_sent(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.api.one.send_text_message(receiver, text)

    def __send_lastn_received(self, receiver, user_id, count):
        text = Message.BIP_LAST_RECEIVED % count
        result = self.db.get_lastn_received(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.api.one.send_text_message(receiver, text)

    def __send_user_list(self, receiver, name):
        user_list = self.db.get_users(name)

    def process_request(self, msg):
        user_id = self.db.get_user_id_by_msisdn(msg.sender)
        if msg.command == Command.HELP or msg.payload == Command.HELP:
            self.api.one.send_text_message(msg.sender, Message.BIP_HELP)

        elif msg.command == Command.MENU:
            self.__send_menu__(msg.sender)

        elif msg.command == Command.POINT:
            self.__send_balance__(msg.sender, user_id)

        elif msg.command == Command.LAST_SENT:
            self.__send_lastn_sent(msg.sender, user_id, msg.next_command())

        elif msg.command == Command.LAST_RECEIVED:
            self.__send_lastn_received(msg.sender, user_id, msg.next_command())

        elif msg.ctype == "buzz":
            self.__send_menu__(msg.sender)

        elif msg.ctype == "poll" and msg.pollid == "receiver_list":
            # TODO hizlianket
            pass

        elif msg.ctype == "poll" and msg.pollid == "quick_reply":
            # TODO hizlicevap
            pass

        elif msg.ctype == "poll" and msg.pollid == "reason_options":
            # TODO reasonList
            pass

        else:
            # TODO liste
            pass
