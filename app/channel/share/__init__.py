from .core import *
from app.common import database, bip
from app.common.cache import Cache, Keys

from app.common.constants.command import Command
from app.common.constants.globals import Globals
from app.common.constants.message import Message
from app.common.models.bip_request import BipRequest
from app.common.utils import get_key_value_tuple


def __initialize_share_a_content(request):
    user_id = database.get_user_id_by_msisdn(request.sender)
    target_user_id = request.value()
    if target_user_id == Globals.NO:
        bip.single.send_text_message(request.sender, Message.SHARE_TRANSACTION_CANCELED)
    elif target_user_id == Globals.OTHER_USERS:  # User list next page
        send_ext_user_list(request.sender, user_id, request.extra_param(), int(request.extra_param(2)))
    else:
        initialize_share_a_content(request.sender, user_id, target_user_id)


def __share_owner_choice(request: BipRequest):
    user_id = database.get_user_id_by_msisdn(request.sender)
    target_user_id = request.value()
    if target_user_id != Globals.OTHER_USERS:
        initialize_share_a_content(request.sender, user_id, target_user_id)
    else:
        Cache.put(Keys.SHARE_OWNER_CHOICE_BY_USER_ID % user_id, True)
        bip.single.send_text_message(request.sender, Message.SHARE_SEARCH_USER)

    Cache.put(Keys.START_CACHED_TRANSACTION_BY_USER_ID % user_id, True)


def __start_share_transaction(request: BipRequest):
    user_id = database.get_user_id_by_msisdn(request.sender)
    most_sent_users = database.get_most_sent_4_user_by_user_id(user_id)
    most_sent_users_tuple = get_key_value_tuple(most_sent_users, "receiver_id", "full_name")
    bip.single.send_poll_message(
        request.sender,
        Command.SHARE_OWNER_CHOICE,
        Message.SHARE_START_TITLE,
        Message.SHARE_START_DESC,
        Message.SHARE_START_IMAGE,
        1,
        PollType.SINGLE_CHOOSE,
        [(user_id, "Kendim"),
         *most_sent_users_tuple,
         (Globals.OTHER_USERS, "Başka arkadaşım")],
        "OK")


command_map = {
    Command.SHARE_START: __start_share_transaction,
    Command.SHARE_OWNER_CHOICE: __share_owner_choice,
    Command.INITIALIZE_SHARE_A_CONTENT: __initialize_share_a_content
}
