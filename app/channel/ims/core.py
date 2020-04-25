from app.common import bip, database
from app.common.utils import *
from app.common.constants.message import Message
from app.common.constants.globals import Globals, Role
from app.common.constants.command import Command
from bipwrapper.type.poll_type import PollType
from app.common.cache import Cache, Keys
from bipwrapper.type.ctype import CType
from app.common.models.free_message import FreeMessage


def send_message_all(user, ctype, content):
    if user["role"] in (Role.SCOPE_ADMIN, Role.SUPER_ADMIN):
        if len(content) > 5:
            receivers = list(map(lambda receiver: receiver["msisdn"],
                                 database.get_scope_users_by_user_id_and_like_name(user["id"])))
            if ctype == CType.TEXT:
                bip.multi.send_text_message(receivers, content)

            bip.single.send_text_message(user["msisdn"], "Mesajın tüm kullanıcılara gönderildi.")
        else:
            bip.single.send_text_message(user["msisdn"], "Toplu mesaj iptal edildi.")


def send_user_list(request):
    start_with = request.command
    user_id = database.get_user_id_by_msisdn(request.sender)
    balance = database.get_balance_by_user_id(user_id)

    if balance >= Globals.SEND_AMOUNT:
        if len(start_with) > 0:
            user_list = database.get_scope_users_by_user_id_and_like_name(user_id, request.command, 0, 7)
            size = len(user_list)
            if size > 0:
                if size > 1:
                    send_ext_user_list(request.sender, user_id, start_with, 0, user_list)
                else:
                    bip.single.send_poll_message(
                        request.sender,
                        Command.MESSAGE_LIST,
                        Message.SINGLE_TITLE % (start_with, user_list[0]["full_name"]),
                        Message.SINGLE_DESC % Globals.SEND_AMOUNT,
                        Message.SHORT_LIST_IMAGE,
                        1,
                        PollType.SINGLE_CHOOSE,
                        get_yes_no_tuple(user_list[0]["id"]),
                        "OK")
            else:
                bip.single.send_text_message(request.sender, Message.NOT_FOUND % start_with)
    else:
        bip.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)


def send_ext_user_list(msisdn, user_id, start_with, offset: int, user_list=None):
    if user_list is None:
        user_list = database.get_scope_users_by_user_id_and_like_name(user_id, start_with, offset, 7)

    if len(user_list) > 6:
        user_tuple = get_key_value_tuple(user_list[:5], "id", "full_name")
        user_tuple.append((Globals.OTHER_USERS, "Diğer"))
        poll_id = "%s%s%s%s%s" % (
            Command.MESSAGE_LIST, Globals.DELIMITER, start_with, Globals.DELIMITER, offset + 5)
    else:
        user_tuple = get_key_value_tuple(user_list, "id", "full_name")
        poll_id = Command.MESSAGE_LIST

    bip.single.send_poll_message(
        msisdn,
        poll_id,
        Message.SHORT_LIST_TITLE % start_with,
        Message.SHORT_LIST_DESC % Globals.SEND_AMOUNT,
        Message.SHORT_LIST_IMAGE,
        1,
        PollType.SINGLE_CHOOSE,
        user_tuple,
        "OK")


def send_free_message(msisdn, user_id, target_user_id, msg_type, message):
    if not message.strip():
        bip.single.send_text_message(msisdn, "Birşeyler yazabilirsin bence 😄")
    else:
        Cache.delete(Keys.FREE_MSG_BY_USER_ID % user_id)
        if msg_type == CType.TEXT:
            database.transfer_points(user_id, target_user_id, Globals.FREE_MSG_ID,
                                     FreeMessage(msg_type, message).get_json_str())

            target_user = database.get_user_by_id(target_user_id)
            balance = database.get_balance_by_user_id(user_id)

            finish_transaction_message(msisdn, user_id, target_user, message, balance)
        else:
            # TODO other messsage types
            bip.single.send_text_message(msisdn, "Şimdilik maalesef sadece yazı yollayabilirsin.")


def send_last_n(request, func):
    count = request.extra_param()
    user_id = database.get_user_id_by_msisdn(request.sender)
    result = func(user_id, count)
    bip.single.send_text_message(request.sender, Message.LAST_SENT % count)
    for row in result:
        text = row["text"] + "\n\n" + row["full_name"] + "\n" + row["date"]
        bip.single.send_text_message(request.sender, text)


def finish_transaction_message(msisdn, user_id, target_user, message, balance):
    bip.single.send_text_message(msisdn, Message.SENT_MESSAGE
                                 % (get_name_with_suffix(target_user["first_name"]),
                                    message,
                                    Globals.SEND_AMOUNT,
                                    Globals.EARN_AMOUNT,
                                    "{:.{}f}".format(balance, 2)))

    user = database.get_user_by_id(user_id)

    if Cache.get(Keys.QUICK_REPLY_BY_USER_IDS % (user_id, target_user["id"])):
        bip.single.send_text_message(
            target_user["msisdn"],
            Message.QUICK_REPLY_TITLE % (
                user["full_name"], Globals.SEND_AMOUNT, message))
        Cache.delete(Keys.QUICK_REPLY_BY_USER_IDS % (user_id, target_user["id"]))
    else:
        yes_no_tuple = [
            (user_id, "Tabiki! 😊"),
            (Globals.NO, "Sonra yollarım... 🙄 ")
        ]

        bip.single.send_poll_message(
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
