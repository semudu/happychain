import logging

from bipwrapper.api import Api
from bipwrapper.type import *

from .blockchain import Blockchain
from .database import Database
from .model.costants import *
from .utils import *

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Bip:
    def __init__(self, config):
        self.db = Database(config)
        self.blockchain = Blockchain(config)
        self.api = Api(config.BIP_URL, config.BIP_USERNAME, config.BIP_PASSWORD)

    def __send_menu__(self, receiver):
        self.api.one.send_quickreply_message(receiver, Poll.MENU, [
            (Command.POINT, "💰 IMS Bakiyem", ButtonType.POST_BACK),
            (Command.LAST_SENT + "-5", "➡️ Son Yolladıklarım", ButtonType.POST_BACK),
            (Command.LAST_RECEIVED + "-5", "⬅️ Son gelenler", ButtonType.POST_BACK),
            (Command.HELP, "❓ Yardım", ButtonType.POST_BACK)
        ])

    def __send_balance__(self, receiver, user_id):
        balance = self.blockchain.get_balance(user_id)
        total_send = self.db.get_total_sent_transaction(user_id)
        total_received = self.db.get_total_received_transaction(user_id)
        self.api.one.send_text_message(receiver, Message.BALANCE % (balance, total_send, total_received))

    def __send_lastn_sent(self, receiver, user_id, count):
        text = Message.LAST_SENT % count
        result = self.db.get_lastn_sent(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.api.one.send_text_message(receiver, text)

    def __send_lastn_received(self, receiver, user_id, count):
        text = Message.LAST_RECEIVED % count
        result = self.db.get_lastn_received(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.api.one.send_text_message(receiver, text)

    def __send_user_list(self, receiver, user_id, start_with):
        if len(start_with) > 0:
            scope_id = self.db.get_user_scope_id(user_id)
            user_list = self.db.get_users_by_scope(scope_id, start_with)
            if len(user_list) > 0:
                if len(user_list) > 1:
                    user_tuple = get_key_value_tuple(user_list, "id", "full_name")
                    self.api.one.send_poll_message(
                        receiver,
                        Poll.SHORT_LIST,
                        Message.SHORT_LIST_TITLE % start_with,
                        Message.SHORT_LIST_DESC % Globals.SEND_AMOUNT,
                        Image.SHORT_LIST_URL,
                        1,
                        PollType.SINGLE_CHOOSE,
                        user_tuple,
                        "OK")
                else:
                    user_tuple = [
                        (user_list[0]["id"], "Evet"),
                        (-1, "Hayır")
                    ]
                    self.api.one.send_poll_message(
                        receiver,
                        Poll.SHORT_LIST,
                        Message.SINGLE_TITLE % (start_with, user_list[0]["full_name"]),
                        Message.SINGLE_DESC % Globals.SEND_AMOUNT,
                        Image.SHORT_LIST_URL,
                        1,
                        PollType.SINGLE_CHOOSE,
                        user_tuple,
                        "OK")
            else:
                self.api.one.send_text_message(receiver, Message.NOT_FOUND % start_with)

    def __send_reason_list(self, receiver, user_id, target_user_id):
        scope_id = self.db.get_user_scope_id(user_id)
        reason_list = self.db.get_reasons_by_scope(scope_id)
        if len(reason_list) > 0:
            reason_tuple = get_key_value_tuple(reason_list, "id", "text")
            target_user = self.db.get_user_by_id(target_user_id)
            self.api.one.send_poll_message(
                receiver,
                Poll.REASON_LIST,
                Message.REASON_LIST_TITLE % (get_name_with_suffix(target_user["first_name"]), Globals.SEND_AMOUNT),
                Message.REASON_LIST_DESC,
                Image.REASON_LIST_URL,
                1,
                PollType.SINGLE_CHOOSE,
                reason_tuple,
                "OK")

    def process_request(self, msg):
        if msg.sender:
            user_id = self.db.get_user_id_by_msisdn(msg.sender)
            if user_id:
                if msg.command == Command.HELP or msg.payload == Command.HELP:
                    self.api.one.send_text_message(msg.sender, Message.HELP)

                elif msg.command == Command.MENU:
                    self.__send_menu__(msg.sender)

                elif msg.command == Command.POINT:
                    self.__send_balance__(msg.sender, user_id)

                elif msg.command == Command.LAST_SENT:
                    self.__send_lastn_sent(msg.sender, user_id, msg.next_command())

                elif msg.command == Command.LAST_RECEIVED:
                    self.__send_lastn_received(msg.sender, user_id, msg.next_command())

                elif msg.ctype == "buzz":
                    # send menu to user
                    self.__send_menu__(msg.sender)

                elif msg.ctype == "poll" and msg.poll.id == Poll.SHORT_LIST:
                    # send reason list to user
                    self.__send_reason_list(msg.sender, user_id, msg.poll.value[0])
                    pass

                elif msg.ctype == "poll" and msg.poll.id == Poll.REASON_LIST:
                    # TODO hizlicevap
                    pass

                else:
                    # send name list to user
                    self.__send_user_list(msg.sender, user_id, msg.command)
