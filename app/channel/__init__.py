from app.common.service import database
from app.common.constants.globals import Role
from app.common.cache import Cache, Keys
from app.common.constants.command import get_command_map

from .base.__core__ import send_free_message, send_message_all, send_user_list
from .base import command_map as base_commands
from ..common.models.bip_request import BipRequest


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


__command_map = get_command_map(__non_command, {**base_commands})


def run_bip_command(request_json):
    request = BipRequest(request_json)
    __command_map[request.command](request)
