from app.common import database
from app.common.constants.globals import Globals
from app.common.cache import Cache, Keys
from app.common.constants.command import get_command_map
from app.common.models.bip_request import BipRequest

from .ims.core import send_free_message, send_message_all, send_user_list as ims_user_list
from .share.core import share_content, send_user_list as share_user_list
from .ims import command_map as ims_commands
from .share import command_map as share_commands


def __exist_cached_transaction(request, user):
    user_id = user["id"]
    exist_cached_transaction = Cache.get(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user_id)
    if exist_cached_transaction is True:
        Cache.delete(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user_id)

        free_message_user_id = Cache.get(Keys.FREE_MSG_BY_USER_ID % user_id)
        if free_message_user_id:
            send_free_message(request.sender, user_id, free_message_user_id, request.ctype,
                              request.content)
            return True

        all_msg = Cache.get(Keys.ALL_MSG_BY_USER_ID % user_id)
        if all_msg is True:
            Cache.delete(Keys.ALL_MSG_BY_USER_ID % user_id)
            send_message_all(user, request.ctype, request.content)
            return True

        target_user_id = Cache.get(Keys.SHARE_OWNER_CHOICE_BY_USER_ID % user_id)
        if target_user_id != Globals.OTHER_USERS:
            share_content(request, user_id, target_user_id)
            return True
        else:
            Cache.put(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user_id, True)

    return False


def __non_command(request):
    user = database.get_user_by_msisdn(request.sender)
    if not __exist_cached_transaction(request, user):
        ims_user_list(request)


__command_map = get_command_map(__non_command, {
    **ims_commands,
    **share_commands})


def run_bip_command(request_json):
    request = BipRequest(request_json)
    __command_map[request.command](request)
