import logging

from bipwrapper.api import Api
from bipwrapper.type import *
from mysql.connector import Error

# from .blockchain import Blockchain
from .database import Database
from .utils import *

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Service:
    def __init__(self, config):
        self.db = Database(config)
        # self.blockchain = Blockchain(config)
        self.transfer_secret = config.TRANSFER_SECRET
        self.bip_api = Api(config.BIP_URL, config.BIP_USERNAME, config.BIP_PASSWORD)

    def __send_menu__(self, msisdn):
        self.bip_api.single.send_quickreply_message(msisdn, Poll.MENU, [
            (Command.POINT, "💰 IMS Bakiyem", ButtonType.POST_BACK),
            (Command.LAST_SENT + Globals.DELIMITER + "5", "➡️ Son Yolladıklarım", ButtonType.POST_BACK),
            (Command.LAST_RECEIVED + Globals.DELIMITER + "5", "⬅️ Son gelenler", ButtonType.POST_BACK),
            (Command.HELP, "❓ Yardım", ButtonType.POST_BACK)
        ])

    def __send_balance__(self, msisdn, user_id):
        # balance = self.blockchain.get_balance(user_id)
        balance = self.db.get_balance(user_id)
        total_send = self.db.get_total_sent_transaction(user_id)
        total_received = self.db.get_total_received_transaction(user_id)
        self.bip_api.single.send_text_message(msisdn, Message.BALANCE % (balance, total_send, total_received))

    def __send_lastn_sent(self, msisdn, user_id, count):
        text = Message.LAST_SENT % count
        result = self.db.get_lastn_sent(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.bip_api.single.send_text_message(msisdn, text)

    def __send_lastn_received(self, msisdn, user_id, count):
        text = Message.LAST_RECEIVED % count
        result = self.db.get_lastn_received(user_id, count)
        for row in result:
            text += row["full_name"] + "\n" + row["text"] + "\n" + row["date"]
        self.bip_api.single.send_text_message(msisdn, text)

    def __send_user_list(self, msisdn, user_id, start_with):
        balance = self.db.get_balance(user_id)
        logging.debug("balance: %s" % balance)
        if balance >= Globals.SEND_AMOUNT:
            if len(start_with) > 0:
                user_list = self.db.get_users_by_scope(user_id, start_with)
                if len(user_list) > 0:
                    if len(user_list) > 1:
                        user_tuple = get_key_value_tuple(user_list, "id", "full_name")
                        self.bip_api.single.send_poll_message(
                            msisdn,
                            Poll.SHORT_LIST,
                            Message.SHORT_LIST_TITLE % start_with,
                            Message.SHORT_LIST_DESC % Globals.SEND_AMOUNT,
                            Image.SHORT_LIST_URL,
                            1,
                            PollType.SINGLE_CHOOSE,
                            user_tuple,
                            "OK")
                    else:
                        yes_no_tuple = [
                            (user_list[0]["id"], "Evet"),
                            (-1, "Hayır")
                        ]
                        self.bip_api.single.send_poll_message(
                            msisdn,
                            Poll.SHORT_LIST,
                            Message.SINGLE_TITLE % (start_with, user_list[0]["full_name"]),
                            Message.SINGLE_DESC % Globals.SEND_AMOUNT,
                            Image.SHORT_LIST_URL,
                            1,
                            PollType.SINGLE_CHOOSE,
                            yes_no_tuple,
                            "OK")
                else:
                    self.bip_api.single.send_text_message(msisdn, Message.NOT_FOUND % start_with)
        else:
            self.bip_api.single.send_text_message(msisdn, Message.INSUFFICIENT_FUNDS)

    def __send_reason_list(self, msisdn, user_id, target_user_id):
        scope_id = self.db.get_user_scope_id(user_id)
        reason_list = self.db.get_reasons_by_scope(scope_id)
        if len(reason_list) > 0:
            reason_tuple = get_key_value_tuple(reason_list, "id", "text")
            target_user = self.db.get_user_by_id(target_user_id)

            self.bip_api.single.send_poll_message(
                msisdn,
                "%s%s%s%s%s%s%s" % (
                    Poll.REASON_LIST, Globals.DELIMITER, str(target_user_id), Globals.DELIMITER, str(user_id),
                    self.transfer_secret, str(target_user_id)),
                Message.REASON_LIST_TITLE % (
                    get_name_with_suffix(target_user["first_name"]), Globals.SEND_AMOUNT),
                Message.REASON_LIST_DESC,
                Image.REASON_LIST_URL,
                1,
                PollType.SINGLE_CHOOSE,
                reason_tuple,
                "OK")

    def __send_a_reason(self, msisdn, user_id, target_user_id, reason_id):
        balance = self.db.get_balance(user_id)
        if balance >= Globals.SEND_AMOUNT:
            if not self.db.check_user_limit(user_id, target_user_id):
                self.bip_api.single.send_text_message(msisdn,
                                                      Message.SAME_PERSON_LIMIT % Globals.SEND_SAME_PERSON_LIMIT)
                return
            elif not self.db.check_team_limit(user_id, target_user_id):
                self.bip_api.single.send_text_message(msisdn, Message.SAME_TEAM_LIMIT % Globals.SEND_SAME_TEAM_LIMIT)
                return
            else:
                self.db.transfer_points(user_id, target_user_id, reason_id)

                target_user = self.db.get_user_by_id(target_user_id)
                reason = self.db.get_reason_by_id(reason_id)
                balance = self.db.get_balance(user_id)

                self.bip_api.single.send_text_message(msisdn, Message.SENT_MESSAGE
                                                      % (get_name_with_suffix(target_user["first_name"]),
                                                         reason,
                                                         Globals.SEND_AMOUNT,
                                                         Globals.EARN_AMOUNT,
                                                         "{:.{}f}".format(balance, 2)))

                # TODO
                target_user = self.db.get_user_by_id(target_user_id)
                self.bip_api.single.send_text_message(target_user["msisdn"], "")

        else:
            self.bip_api.single.send_text_message(msisdn, Message.INSUFFICIENT_FUNDS)

    def import_user_array(self, user_array):
        teams = {}
        succeed = []
        failed = []

        for i in range(1, len(user_array)):
            user_fields = user_array[i]
            team_name = user_fields[5]
            if team_name not in teams:
                team_id = self.db.get_team_id_by_name(team_name)
                if team_id is not None:
                    teams[team_name] = team_id

            if team_name in teams:
                try:
                    self.db.add_user(user_fields[0], user_fields[1], user_fields[2], user_fields[3], user_fields[4],
                                     Globals.DEFAULT_PASSWD, teams[team_name])
                    succeed.append(user_fields[0])
                except Error as e:
                    failed.append({"msisdn": user_fields[0], "description": str(e)})
            else:
                failed.append({"msisdn": user_fields[0], "description": "team[%s] is not found" % team_name})

        return {
            "succeed": succeed,
            "failed": failed
        }

    def process_bip_request(self, msg):
        if msg.sender:
            user_id = self.db.get_user_id_by_msisdn(msg.sender)
            if user_id:
                if msg.command == Command.HELP or msg.payload == Command.HELP:
                    self.bip_api.single.send_text_message(msg.sender, Message.HELP)

                elif msg.command == Command.MENU:
                    self.__send_menu__(msg.sender)

                elif msg.command == Command.POINT or msg.payload == Command.POINT:
                    self.__send_balance__(msg.sender, user_id)

                elif msg.command == Command.LAST_SENT or msg.payload == Command.LAST_SENT:
                    self.__send_lastn_sent(msg.sender, user_id, msg.next_command())

                elif msg.command == Command.LAST_RECEIVED or msg.payload == Command.LAST_RECEIVED:
                    self.__send_lastn_received(msg.sender, user_id, msg.next_command())

                elif msg.ctype == CType.BUZZ:
                    # send menu to user
                    self.__send_menu__(msg.sender)

                elif msg.ctype == CType.POLL and msg.poll_id == Poll.SHORT_LIST:
                    # send reason list to user
                    self.__send_reason_list(msg.sender, user_id, msg.poll_value)

                elif msg.ctype == CType.POLL and msg.poll_id == Poll.REASON_LIST:
                    if msg.poll_secret == "%s%s%s" % (user_id, self.transfer_secret, msg.poll_ext):
                        self.__send_a_reason(msg.sender, user_id, msg.poll_ext, msg.poll_value)
                    else:
                        raise Exception("Transfer secret does not match!")

                else:
                    # send name list to user
                    self.__send_user_list(msg.sender, user_id, msg.command)
