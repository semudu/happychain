from bipwrapper import BipWrapper
from bipwrapper.type.button_type import ButtonType
from bipwrapper.type.poll_type import PollType
from bipwrapper.type.ctype import CType

from app.commons.constants.globals import *
from app.commons.constants.command import Command
from app.commons.constants.message import Message
from app.commons.log import get_logger
from app.commons.utils import *
from .database import Database
from config import APP, BIP

logger = get_logger(__name__)


class Channel:
    def __init__(self):
        self.db = Database()
        self.transfer_secret = APP.TRANSFER_SECRET
        self.bip_api = BipWrapper(BIP.ENVIRONMENT, BIP.USERNAME, BIP.PASSWORD)

    def __finish_transaction_message(self, msisdn, user_id, target_user, message, balance):
        self.bip_api.single.send_text_message(msisdn, Message.SENT_MESSAGE
                                              % (get_name_with_suffix(target_user["first_name"]),
                                                 message,
                                                 Globals.SEND_AMOUNT,
                                                 Globals.EARN_AMOUNT,
                                                 "{:.{}f}".format(balance, 2)))

        # TODO quick reply
        user = self.db.get_user_by_id(user_id)
        self.bip_api.single.send_text_message(target_user["msisdn"], Message.RECEIVED_MESSAGE % (
            user["full_name"], Globals.SEND_AMOUNT, message))

    def __send_free_message(self, msisdn, last_transaction, msg_type, message=""):
        if not message.strip():
            self.bip_api.single.send_text_message(msisdn, "Birşeyler yazabilirsin bence 😄")
        else:
            if msg_type == CType.TEXT:
                target_user = self.db.get_user_by_id(last_transaction["receiver_id"])
                balance = self.db.get_balance_by_user_id(last_transaction["sender_id"])
                self.db.update_free_message(last_transaction, msg_type, message)
                self.__finish_transaction_message(msisdn, last_transaction["sender_id"], target_user, message, balance)
            else:
                # TODO other messsage types
                self.bip_api.single.send_text_message(msisdn, "Şimdilik maalesef sadece yazı yollayabilirsin.")

    def __send_last_n(self, request, func):
        count = request.extra_param()
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        result = func(user_id, count)
        self.bip_api.single.send_text_message(request.sender, Message.LAST_SENT % count)
        for row in result:
            text = row["text"] + "\n\n" + row["full_name"] + "\n" + row["date"]
            self.bip_api.single.send_text_message(request.sender, text)

    def send_menu(self, request):
        user = self.db.get_user_by_msisdn(request.sender)
        if user["role"] == Role.SCOPE_ADMIN:
            pass
        else:
            self.bip_api.single.send_quickreply_message(request.sender, Command.MENU, [
                (Command.POINT, "💰 IMS Bakiyem", ButtonType.POST_BACK),
                (Command.LAST_SENT + Globals.DELIMITER + "5", "➡️ Son Yolladıklarım", ButtonType.POST_BACK),
                (Command.LAST_RECEIVED + Globals.DELIMITER + "5", "⬅️ Son gelenler", ButtonType.POST_BACK),
                (Command.HELP, "❓ Yardım", ButtonType.POST_BACK)
            ])

    def send_balance(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        balance = self.db.get_balance_by_user_id(user_id)
        total_send = self.db.get_total_sent_transaction(user_id)
        total_received = self.db.get_total_received_transaction(user_id)
        self.bip_api.single.send_text_message(request.sender, Message.BALANCE % (balance, total_send, total_received))

    def send_last_n_sent(self, request):
        self.__send_last_n(request, self.db.get_last_n_sent)

    def send_last_n_received(self, request):
        self.__send_last_n(request, self.db.get_last_n_received)

    def send_user_list(self, request):
        start_with = request.command
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        balance = self.db.get_balance_by_user_id(user_id)

        if balance >= Globals.SEND_AMOUNT:
            if len(start_with) > 0:
                user_list = self.db.get_scope_users_by_user_id_and_like_name(user_id, request.command)
                if len(user_list) > 0:
                    if len(user_list) > 1:
                        user_tuple = get_key_value_tuple(user_list, "id", "full_name")
                        self.bip_api.single.send_poll_message(
                            request.sender,
                            Command.MESSAGE_LIST,
                            Message.SHORT_LIST_TITLE % start_with,
                            Message.SHORT_LIST_DESC % Globals.SEND_AMOUNT,
                            Message.SHORT_LIST_IMAGE,
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
                            request.sender,
                            Command.MESSAGE_LIST,
                            Message.SINGLE_TITLE % (start_with, user_list[0]["full_name"]),
                            Message.SINGLE_DESC % Globals.SEND_AMOUNT,
                            Message.SHORT_LIST_IMAGE,
                            1,
                            PollType.SINGLE_CHOOSE,
                            yes_no_tuple,
                            "OK")
                else:
                    self.bip_api.single.send_text_message(request.sender, Message.NOT_FOUND % start_with)
        else:
            self.bip_api.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)

    def send_message_list(self, request):
        target_user_id = request.value()
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        message_list = self.db.get_message_list_by_user_id(target_user_id)
        if len(message_list) > 0:
            message_tuple = get_key_value_tuple(message_list, "id", "text")
            target_user = self.db.get_user_by_id(target_user_id)
            self.bip_api.single.send_poll_message(
                request.sender,
                "%s%s%s%s%s%s%s" % (
                    Command.FINISH_TRANSACTION, Globals.DELIMITER, str(target_user_id), Globals.DELIMITER, str(user_id),
                    self.transfer_secret, str(target_user_id)),
                Message.REASON_LIST_TITLE % (
                    get_name_with_suffix(target_user["first_name"]), Globals.SEND_AMOUNT),
                Message.REASON_LIST_DESC,
                Message.REASON_LIST_IMAGE,
                1,
                PollType.SINGLE_CHOOSE,
                message_tuple,
                "OK")

    def non_command(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        free_message_transaction = self.db.check_free_message(user_id)
        if free_message_transaction:
            self.__send_free_message(request.sender, free_message_transaction, request.ctype,
                                     request.context)
        else:
            self.send_user_list(request.sender, user_id, request.command)

    def send_message(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        if request.extra_param(2) == "%s%s%s" % (user_id, self.transfer_secret, request.extra_param()):
            target_user_id = request.extra_param()
            message_id = request.value()
            balance = self.db.get_balance_by_user_id(user_id)
            if balance >= Globals.SEND_AMOUNT:
                if not self.db.check_user_limit(user_id, target_user_id):
                    self.bip_api.single.send_text_message(request.sender,
                                                          Message.SAME_PERSON_LIMIT % Globals.SEND_SAME_PERSON_LIMIT)
                    return
                elif not self.db.check_team_limit(user_id, target_user_id):
                    self.bip_api.single.send_text_message(request.sender,
                                                          Message.SAME_TEAM_LIMIT % Globals.SEND_SAME_TEAM_LIMIT)
                    return
                else:
                    self.db.transfer_points(user_id, target_user_id, message_id)

                    target_user = self.db.get_user_by_id(target_user_id)
                    message = self.db.get_message_by_id(message_id)
                    balance = self.db.get_balance_by_user_id(user_id)

                    if message_id != -1:
                        self.__finish_transaction_message(request.sender, user_id, target_user, message, balance)
                    else:
                        self.bip_api.single.send_text_message(request.sender,
                                                              Message.FREE_MESSAGE % target_user["first_name"])

            else:
                self.bip_api.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)
        else:
            raise Exception("Transfer secret does not match!")

    def send_help_message(self, request):
        self.bip_api.single.send_text_message(request.sender, Message.HELP)
