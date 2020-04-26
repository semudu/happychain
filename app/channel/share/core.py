from bipwrapper.type.ctype import CType
from bipwrapper.type.poll_type import PollType

from app.common import database, bip
from app.common.cache import Cache, Keys
from app.common.constants.command import Command
from app.common.constants.globals import Globals
from app.common.constants.message import Message
from app.common.models.bip_request import BipRequest
from app.common.utils import get_yes_no_tuple, get_key_value_tuple


def initialize_share_a_content(sender, user_id, target_user_id):
    Cache.put(Keys.SHARE_A_CONTENT_BY_USER_ID % user_id, target_user_id)
    bip.single.send_text_message(sender, Message.SHARE_A_CONTENT)


def send_user_list(request):
    start_with = request.command
    user_id = database.get_user_id_by_msisdn(request.sender)

    if len(start_with) > 0:
        user_list = database.get_scope_users_by_user_id_and_like_name(user_id, request.command, 0, 7)
        size = len(user_list)
        if size > 0:
            if size > 1:
                send_ext_user_list(request.sender, user_id, start_with, 0, user_list)
            else:
                bip.single.send_poll_message(
                    request.sender,
                    Command.INITIALIZE_SHARE_A_CONTENT,
                    Message.SINGLE_TITLE % (start_with, user_list[0]["full_name"]),
                    Message.SHARE_SINGLE_USER_DESC,
                    Message.SHORT_LIST_IMAGE,
                    1,
                    PollType.SINGLE_CHOOSE,
                    get_yes_no_tuple(user_list[0]["id"]),
                    "OK")
        else:
            bip.single.send_text_message(request.sender, Message.NOT_FOUND % start_with)


def send_ext_user_list(msisdn, user_id, start_with, offset: int, user_list=None):
    if user_list is None:
        user_list = database.get_scope_users_by_user_id_and_like_name(user_id, start_with, offset, 7)

    if len(user_list) > 6:
        user_tuple = get_key_value_tuple(user_list[:5], "id", "full_name")
        user_tuple.append((Globals.OTHER_USERS, "Diğer"))
        poll_id = "%s%s%s%s%s" % (
            Command.INITIALIZE_SHARE_A_CONTENT, Globals.DELIMITER, start_with, Globals.DELIMITER, offset + 5)
    else:
        user_tuple = get_key_value_tuple(user_list, "id", "full_name")
        poll_id = Command.INITIALIZE_SHARE_A_CONTENT

    bip.single.send_poll_message(
        msisdn,
        poll_id,
        Message.SHORT_LIST_TITLE % start_with,
        Message.SHARE_START_TITLE,
        Message.SHORT_LIST_IMAGE,
        1,
        PollType.SINGLE_CHOOSE,
        user_tuple,
        "OK")


def share_content(request: BipRequest, user_id, share_user_id):
    if request.ctype in [CType.TEXT, CType.PHOTO, CType.VIDEO]:
        scope_id = database.get_scope_id_by_user_id(user_id)
        scope_users = database.get_scope_users_by_user_id_and_like_name(user_id)
        messages = database.get_share_message_list_by_scope_id(scope_id)

        for target_user in scope_users:
            target_user_id = target_user["id"]
            if target_user_id != user_id and target_user_id != share_user_id:
                if request.ctype == CType.TEXT:
                    pass
                    # TODO

    else:
        bip.single.send_text_message(request.sender, "Yazı, Fotoğraf ya da Video paylaşabilirsin.")

# TODO
