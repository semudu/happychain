from app.common import database, bip
from app.common.cache import Cache, Keys
from app.common.constants.command import Command
from app.common.constants.globals import Role
from app.common.service import get_report_file_info


def __send_transaction_count(request):
    user = database.get_user_by_msisdn(request.sender)
    if user["role"] in [Role.SCOPE_ADMIN, Role.SUPER_ADMIN]:
        scope_id = database.get_scope_id_by_user_id(user["id"])
        count = database.get_transaction_count_by_scope(scope_id)
        bip.single.send_text_message(request.sender, count)


def __send_top_ten(request):
    user = database.get_user_by_msisdn(request.sender)
    if user["role"] in [Role.SCOPE_ADMIN, Role.SUPER_ADMIN]:
        scope_id = database.get_scope_id_by_user_id(user["id"])
        top_user_list = database.get_top_ten_user_by_scope(scope_id)
        msg = "%s\n\nToplam Yolladığı: %s\nToplam Aldığı: %s\nGenel Toplam: %s"
        for top_user in top_user_list:
            bip.single.send_text_message(request.sender, msg % (
                top_user["full_name"], top_user["total_sent"], top_user["total_received"], top_user["total"]))


def __start_send_all_transaction(request):
    user = database.get_user_by_msisdn(request.sender)
    if user["role"] in [Role.SCOPE_ADMIN, Role.SUPER_ADMIN]:
        Cache.put(Keys.ALL_MSG_BY_USER_ID % user["id"], True)
        Cache.put(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user["id"], True)
        bip.single.send_text_message(request.sender,
                                     "Yazacağın ilk mesaj sorumluluğundaki tüm kullanıcılara gönderilecek.")


def __send_transaction_report(request):
    user = database.get_user_by_msisdn(request.sender)
    if user["role"] in [Role.SCOPE_ADMIN, Role.SUPER_ADMIN]:
        scope = database.get_scope_by_user_id(user["id"])
        file_info = get_report_file_info(scope["id"], scope["name"])
        bip.single.send_document(request.sender, file_info["name"], file_info["url"])


def __add_user(request):
    # TODO
    pass


def __remove_user(request):
    # TODO
    pass


command_map = {
    Command.TRANSACTION_COUNT: __send_transaction_count,
    Command.TOP_TEN: __send_top_ten,
    Command.SEND_MESSAGE_ALL: __start_send_all_transaction,
    Command.GET_TRANSACTION_REPORT: __send_transaction_report,
    Command.ADD_USER: __add_user,
    Command.REMOVE_USER: __remove_user,
}
