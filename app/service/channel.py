from collections import defaultdict

from bipwrapper import BipWrapper
from bipwrapper.type.button_type import ButtonType
from bipwrapper.type.poll_type import PollType
from bipwrapper.type.ctype import CType

from app.commons.models.bip_request import BipRequest
from app.commons.constants.globals import *
from app.commons.constants.command import Command
from app.commons.constants.message import Message
from app.commons.log import get_logger
from app.commons.utils import *
from app.commons.database import Database
from config import APP, BIP
from app.commons.cache import Cache, Keys
from app.commons.models.free_message import FreeMessage
from .service import Service

logger = get_logger(__name__)
service = Service()


class Channel:
    def __init__(self):
        self.db = Database()
        self.bip_api = BipWrapper(BIP.ENVIRONMENT, BIP.USERNAME, BIP.PASSWORD)
        self.map = {
            Command.MENU: self.send_menu,
            Command.HELP: self.send_help_message,
            Command.POINT: self.send_balance,
            Command.LAST_SENT: self.send_last_n_sent,
            Command.LAST_RECEIVED: self.send_last_n_received,
            Command.MESSAGE_LIST: self.send_message_list,
            Command.FINISH_TRANSACTION: self.send_message,
            Command.TRANSACTION_COUNT: self.send_transaction_count,
            Command.TOP_TEN: self.send_top_ten,
            Command.SEND_MESSAGE_ALL: self.start_send_all_transaction,
            Command.GET_TRANSACTION_REPORT: self.send_transaction_report,
            Command.ADD_USER: self.add_user,
            Command.REMOVE_USER: self.remove_user,
            Command.QUICK_REPLY: self.send_message_list
        }

    def run_command(self, request_json):
        request = BipRequest(request_json)
        task = defaultdict(lambda: self.non_command, self.map)
        task[request.command](request)

    def __finish_transaction_message(self, msisdn, user_id, target_user, message, balance):
        self.bip_api.single.send_text_message(msisdn, Message.SENT_MESSAGE
                                              % (get_name_with_suffix(target_user["first_name"]),
                                                 message,
                                                 Globals.SEND_AMOUNT,
                                                 Globals.EARN_AMOUNT,
                                                 "{:.{}f}".format(balance, 2)))

        user = self.db.get_user_by_id(user_id)

        if Cache.get(Keys.QUICK_REPLY_BY_USER_IDS % (user_id, target_user["id"])):
            self.bip_api.single.send_text_message(
                target_user["msisdn"],
                Message.QUICK_REPLY_TITLE % (
                    user["full_name"], Globals.SEND_AMOUNT, message))
            Cache.delete(Keys.QUICK_REPLY_BY_USER_IDS % (user_id, target_user["id"]))
        else:
            yes_no_tuple = [
                (user_id, "Tabiki! 😊"),
                (Globals.NO, "Sonra yollarım... 🙄 ")
            ]

            self.bip_api.single.send_poll_message(
                target_user["msisdn"],
                Command.QUICK_REPLY,
                Message.QUICK_REPLY_TITLE % (user["full_name"], Globals.SEND_AMOUNT, message),
                Message.QUICK_REPLY_DESC,
                Message.QUICK_REPLY_IMAGE,
                1,
                PollType.SINGLE_CHOOSE,
                yes_no_tuple,
                "OK")

            Cache.put(Keys.QUICK_REPLY_BY_USER_IDS % (target_user["id"], user_id,), True)

    def __send_free_message(self, msisdn, user_id, target_user_id, msg_type, message):
        if not message.strip():
            self.bip_api.single.send_text_message(msisdn, "Birşeyler yazabilirsin bence 😄")
        else:
            if msg_type == CType.TEXT:
                self.db.transfer_points(user_id, target_user_id, Globals.FREE_MSG_ID,
                                        FreeMessage(msg_type, message).get_json_str())

                target_user = self.db.get_user_by_id(target_user_id)
                balance = self.db.get_balance_by_user_id(user_id)

                self.__finish_transaction_message(msisdn, user_id, target_user, message, balance)
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
        if user["role"] in [Role.SCOPE_ADMIN, Role.SUPER_ADMIN] and request.ctype == CType.BUZZ:
            menu = [
                (Command.MENU, "Menü", ButtonType.POST_BACK),
                (Command.TRANSACTION_COUNT, "Gönderim Sayısı", ButtonType.POST_BACK),
                (Command.TOP_TEN, "İlk 10", ButtonType.POST_BACK),
                (Command.SEND_MESSAGE_ALL, "Toplu Mesaj", ButtonType.POST_BACK),
                (Command.GET_TRANSACTION_REPORT, "Rapor Al", ButtonType.POST_BACK)
            ]
        else:
            menu = [
                (Command.POINT, "💰 IMS Bakiyem", ButtonType.POST_BACK),
                (Command.LAST_SENT + Globals.DELIMITER + "5", "➡️ Son Yolladıklarım", ButtonType.POST_BACK),
                (Command.LAST_RECEIVED + Globals.DELIMITER + "5", "⬅️ Son gelenler", ButtonType.POST_BACK),
                (Command.HELP, "❓ Yardım", ButtonType.POST_BACK)
            ]

        self.bip_api.single.send_quickreply_message(request.sender, Command.MENU, menu)

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

    def __send_multi_user_list(self, msisdn, user_id, start_with, offset: int, user_list=None):
        if user_list is None:
            user_list = self.db.get_scope_users_by_user_id_and_like_name(user_id, start_with, offset, 7)

        if len(user_list) > 6:
            user_tuple = get_key_value_tuple(user_list[:5], "id", "full_name")
            user_tuple.append((Globals.OTHER_USERS, "Diğer"))
            poll_id = "%s%s%s%s%s" % (
                Command.MESSAGE_LIST, Globals.DELIMITER, start_with, Globals.DELIMITER, offset + 5)
        else:
            user_tuple = get_key_value_tuple(user_list, "id", "full_name")
            poll_id = Command.MESSAGE_LIST

        self.bip_api.single.send_poll_message(
            msisdn,
            poll_id,
            Message.SHORT_LIST_TITLE % start_with,
            Message.SHORT_LIST_DESC % Globals.SEND_AMOUNT,
            Message.SHORT_LIST_IMAGE,
            1,
            PollType.SINGLE_CHOOSE,
            user_tuple,
            "OK")

    def send_user_list(self, request):
        start_with = request.command
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        balance = self.db.get_balance_by_user_id(user_id)

        if balance >= Globals.SEND_AMOUNT:
            if len(start_with) > 0:
                user_list = self.db.get_scope_users_by_user_id_and_like_name(user_id, request.command, 0, 7)
                size = len(user_list)
                if size > 0:
                    if size > 1:
                        self.__send_multi_user_list(request.sender, user_id, start_with, 0, user_list)
                    else:
                        yes_no_tuple = [
                            (user_list[0]["id"], "Evet"),
                            (Globals.NO, "Hayır")
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
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        target_user_id = request.value()
        if target_user_id == Globals.NO:  # Quick reply no answer
            self.bip_api.single.send_text_message(request.sender, Message.QUICK_REPLY_NO)
            Cache.delete(Keys.QUICK_REPLY_BY_USER_IDS % (target_user_id, user_id))
        elif target_user_id == Globals.OTHER_USERS:  # User list next page
            self.__send_multi_user_list(request.sender, user_id, request.extra_param(), int(request.extra_param(2)))
        else:
            message_list = self.db.get_message_list_by_user_id(target_user_id)
            if len(message_list) > 0:
                message_tuple = get_key_value_tuple(message_list, "id", "text")
                target_user = self.db.get_user_by_id(target_user_id)
                self.bip_api.single.send_poll_message(
                    request.sender,
                    "%s%s%s%s%s%s%s" % (
                        Command.FINISH_TRANSACTION, Globals.DELIMITER, str(target_user_id), Globals.DELIMITER,
                        str(user_id),
                        APP.TRANSFER_SECRET, str(target_user_id)),
                    Message.REASON_LIST_TITLE % (
                        get_name_with_suffix(target_user["first_name"]), Globals.SEND_AMOUNT),
                    Message.REASON_LIST_DESC,
                    Message.REASON_LIST_IMAGE,
                    1,
                    PollType.SINGLE_CHOOSE,
                    message_tuple,
                    "OK")

    def non_command(self, request):
        user = self.db.get_user_by_msisdn(request.sender)
        free_msg_target_user_id = Cache.get(Keys.FREE_MSG_BY_USER_ID % user["id"])
        if free_msg_target_user_id:
            Cache.delete(Keys.FREE_MSG_BY_USER_ID % user["id"])
            self.__send_free_message(request.sender, user["id"], free_msg_target_user_id, request.ctype,
                                     request.content)
        else:
            if user["role"] in (Role.SCOPE_ADMIN, Role.SUPER_ADMIN):
                all_msg = Cache.get(Keys.ALL_MSG_BY_USER_ID % user["id"])
                if all_msg is True:
                    Cache.delete(Keys.ALL_MSG_BY_USER_ID % user["id"])
                    self.send_message_all(user, request.ctype, request.content)
                else:
                    self.send_user_list(request)
            else:
                self.send_user_list(request)

    def send_message(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        if request.extra_param(2) == "%s%s%s" % (user_id, APP.TRANSFER_SECRET, request.extra_param()):
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

                    target_user = self.db.get_user_by_id(target_user_id)

                    if message_id != Globals.FREE_MSG_ID:
                        self.db.transfer_points(user_id, target_user_id, message_id)
                        message = self.db.get_message_by_id(message_id)
                        balance = self.db.get_balance_by_user_id(user_id)

                        self.__finish_transaction_message(request.sender, user_id, target_user, message, balance)
                    else:
                        Cache.put(Keys.FREE_MSG_BY_USER_ID % user_id, target_user["id"])
                        self.bip_api.single.send_text_message(request.sender,
                                                              Message.FREE_MESSAGE % target_user["first_name"])

            else:
                self.bip_api.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)
        else:
            raise Exception("Transfer secret does not match!")

    def send_help_message(self, request):
        self.bip_api.single.send_text_message(request.sender, Message.HELP)

    def send_transaction_count(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        scope_id = self.db.get_scope_id_by_user_id(user_id)
        count = self.db.get_transaction_count_by_scope(scope_id)
        self.bip_api.single.send_text_message(request.sender, count)

    def send_top_ten(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        scope_id = self.db.get_scope_id_by_user_id(user_id)
        users = self.db.get_top_ten_user_by_scope(scope_id)
        msg = "%s\n\nToplam Yolladığı: %s\nToplam Aldığı: %s\nGenel Toplam: %s"
        for user in users:
            self.bip_api.single.send_text_message(request.sender, msg % (
                user["full_name"], user["total_sent"], user["total_received"], user["total"]))

    def start_send_all_transaction(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        Cache.put(Keys.ALL_MSG_BY_USER_ID % user_id, True)
        self.bip_api.single.send_text_message(request.sender,
                                              "Yazacağın ilk mesaj sorumluluğundaki tüm kullanıcılara gönderilecek.")

    def send_message_all(self, user, ctype, content):
        if len(content) > 5:
            receivers = list(map(lambda receiver: receiver["msisdn"],
                                 self.db.get_scope_users_by_user_id_and_like_name(user["id"])))
            if ctype == CType.TEXT:
                self.bip_api.multi.send_text_message(receivers, content)

            self.bip_api.single.send_text_message(user["msisdn"], "Mesajın tüm kullanıcılara gönderildi.")
        else:
            self.bip_api.single.send_text_message(user["msisdn"], "Toplu mesaj iptal edildi.")

    def send_transaction_report(self, request):
        user_id = self.db.get_user_id_by_msisdn(request.sender)
        scope = self.db.get_scope_by_user_id(user_id)
        file_info = service.get_report_file_info(scope["id"], scope["name"])
        self.bip_api.single.send_document(request.sender, file_info["name"], file_info["url"])

    def add_user(self, request):
        # TODO
        pass

    def remove_user(self, request):
        # TODO
        pass
