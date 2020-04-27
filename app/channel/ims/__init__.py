from bipwrapper.type.button_type import ButtonType
from app.common.log import get_logger
from config import APP
from .core import *

logger = get_logger(__name__)


def __send_menu(request):
    user = database.get_user_by_msisdn(request.sender)
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

    bip.single.send_quickreply_message(request.sender, Command.MENU, menu)


def __send_balance(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    balance = database.get_balance_by_user_id(user_id)
    total_send = database.get_total_sent_transaction(user_id)
    total_received = database.get_total_received_transaction(user_id)
    bip.single.send_text_message(request.sender, Message.BALANCE % (balance, total_send, total_received))


def __send_last_n_sent(request):
    send_last_n(request, database.get_last_n_sent)


def __send_last_n_received(request):
    send_last_n(request, database.get_last_n_received)


def __send_message_list(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    target_user_id = request.value()
    if target_user_id == Globals.NO:  # Quick reply no answer
        bip.single.send_text_message(request.sender, Message.QUICK_REPLY_NO)
        Cache.delete(Keys.QUICK_REPLY_BY_USER_IDS % (target_user_id, user_id))
    elif target_user_id == Globals.OTHER_USERS:  # User list next page
        send_ext_user_list(request.sender, user_id, request.extra_param(), int(request.extra_param(2)))
    else:
        message_list = database.get_message_list_by_user_id(target_user_id)
        if len(message_list) > 0:
            message_tuple = get_key_value_tuple(message_list, "id", "text")
            target_user = database.get_user_by_id(target_user_id)
            bip.single.send_poll_message(
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


def __send_message(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    if request.extra_param(2) == "%s%s%s" % (user_id, APP.TRANSFER_SECRET, request.extra_param()):
        target_user_id = request.extra_param()
        message_id = request.value()
        balance = database.get_balance_by_user_id(user_id)
        if balance >= Globals.SEND_AMOUNT:
            if not database.check_user_limit(user_id, target_user_id):
                bip.single.send_text_message(request.sender,
                                             Message.SAME_PERSON_LIMIT % Globals.SEND_SAME_PERSON_LIMIT)
                return
            elif not database.check_team_limit(user_id, target_user_id):
                bip.single.send_text_message(request.sender,
                                             Message.SAME_TEAM_LIMIT % Globals.SEND_SAME_TEAM_LIMIT)
                return
            else:
                if message_id == Globals.FREE_MSG_ID:
                    target_user = database.get_user_by_id(target_user_id)
                    Cache.put(Keys.FREE_MSG_BY_USER_ID % user_id, target_user_id)
                    Cache.put(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user_id, True)
                    bip.single.send_text_message(request.sender,
                                                 Message.FREE_MESSAGE % target_user["first_name"])
                else:
                    finish_transaction_message(request.sender, user_id, target_user_id, message_id, balance)

        else:
            bip.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)
    else:
        raise Exception("Transfer secret does not match!")


def __send_help_message(request):
    bip.single.send_text_message(request.sender, Message.HELP)


command_map = {
    Command.MENU: __send_menu,
    Command.HELP: __send_help_message,
    Command.POINT: __send_balance,
    Command.LAST_SENT: __send_last_n_sent,
    Command.LAST_RECEIVED: __send_last_n_received,
    Command.MESSAGE_LIST: __send_message_list,
    Command.FINISH_TRANSACTION: __send_message,
    Command.QUICK_REPLY: __send_message_list
}
