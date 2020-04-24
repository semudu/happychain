from bipwrapper.type.button_type import ButtonType
from app.commons.constants.globals import *
from app.commons.log import get_logger
from config import APP
from app.commons.service import get_report_file_info
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
        send_multi_user_list(request.sender, user_id, request.extra_param(), int(request.extra_param(2)))
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


def __non_command(request):
    user = database.get_user_by_msisdn(request.sender)
    free_msg_target_user_id = Cache.get(Keys.FREE_MSG_BY_USER_ID % user["id"])
    if free_msg_target_user_id:
        Cache.delete(Keys.FREE_MSG_BY_USER_ID % user["id"])
        send_free_message(request.sender, user["id"], free_msg_target_user_id, request.ctype,
                          request.content)
    else:
        if user["role"] in (Role.SCOPE_ADMIN, Role.SUPER_ADMIN):
            all_msg = Cache.get(Keys.ALL_MSG_BY_USER_ID % user["id"])
            if all_msg is True:
                Cache.delete(Keys.ALL_MSG_BY_USER_ID % user["id"])
                send_message_all(user, request.ctype, request.content)
            else:
                send_user_list(request)
        else:
            send_user_list(request)


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

                target_user = database.get_user_by_id(target_user_id)

                if message_id != Globals.FREE_MSG_ID:
                    database.transfer_points(user_id, target_user_id, message_id)
                    message = database.get_message_by_id(message_id)
                    balance = database.get_balance_by_user_id(user_id)

                    finish_transaction_message(request.sender, user_id, target_user, message, balance)
                else:
                    Cache.put(Keys.FREE_MSG_BY_USER_ID % user_id, target_user["id"])
                    bip.single.send_text_message(request.sender,
                                                 Message.FREE_MESSAGE % target_user["first_name"])

        else:
            bip.single.send_text_message(request.sender, Message.INSUFFICIENT_FUNDS)
    else:
        raise Exception("Transfer secret does not match!")


def __send_help_message(request):
    bip.single.send_text_message(request.sender, Message.HELP)


def __send_transaction_count(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    scope_id = database.get_scope_id_by_user_id(user_id)
    count = database.get_transaction_count_by_scope(scope_id)
    bip.single.send_text_message(request.sender, count)


def __send_top_ten(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    scope_id = database.get_scope_id_by_user_id(user_id)
    users = database.get_top_ten_user_by_scope(scope_id)
    msg = "%s\n\nToplam Yolladığı: %s\nToplam Aldığı: %s\nGenel Toplam: %s"
    for user in users:
        bip.single.send_text_message(request.sender, msg % (
            user["full_name"], user["total_sent"], user["total_received"], user["total"]))


def __start_send_all_transaction(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    Cache.put(Keys.ALL_MSG_BY_USER_ID % user_id, True)
    bip.single.send_text_message(request.sender,
                                 "Yazacağın ilk mesaj sorumluluğundaki tüm kullanıcılara gönderilecek.")


def __send_transaction_report(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    scope = database.get_scope_by_user_id(user_id)
    file_info = get_report_file_info(scope["id"], scope["name"])
    bip.single.send_document(request.sender, file_info["name"], file_info["url"])


def __add_user(request):
    # TODO
    pass


def __remove_user(request):
    # TODO
    pass


command_map = {
    Command.MENU: __send_menu,
    Command.HELP: __send_help_message,
    Command.POINT: __send_balance,
    Command.LAST_SENT: __send_last_n_sent,
    Command.LAST_RECEIVED: __send_last_n_received,
    Command.MESSAGE_LIST: __send_message_list,
    Command.FINISH_TRANSACTION: __send_message,
    Command.TRANSACTION_COUNT: __send_transaction_count,
    Command.TOP_TEN: __send_top_ten,
    Command.SEND_MESSAGE_ALL: __start_send_all_transaction,
    Command.GET_TRANSACTION_REPORT: __send_transaction_report,
    Command.ADD_USER: __add_user,
    Command.REMOVE_USER: __remove_user,
    Command.QUICK_REPLY: __send_message_list
}
