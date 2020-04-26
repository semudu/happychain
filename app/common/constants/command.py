from collections import defaultdict


class Command:
    # == BASE CHANNEL == #
    HELP = "__help"
    MENU = "__menu"
    POINT = "__point"
    LAST_SENT = "__last_sent"
    LAST_RECEIVED = "__last_received"
    MESSAGE_LIST = "__message_list"
    FINISH_TRANSACTION = "__finish_transaction"
    QUICK_REPLY = "__quick_reply"

    # == ADMIN COMMANDS == #
    TRANSACTION_COUNT = "__transaction_count"
    TOP_TEN = "__top_ten"
    SEND_MESSAGE_ALL = "__send_message_all"
    GET_TRANSACTION_REPORT = "__get_transaction_report"
    ADD_USER = "__add_user"
    REMOVE_USER = "__remove_user"

    # == SHARE CHANNEL == #
    SHARE_START = "__share_start"
    SHARE_OWNER_CHOICE = "__share_owner_choise"
    INITIALIZE_SHARE_A_CONTENT = "__initialize_share_a_content"


EXTRA_COMMANDS = {
    # == BASE CHANNEL == #
    Command.HELP: ["!!", "!y", "!yardım", "!yardim"],
    Command.MENU: ["!m", "!menu", "!menü"],
    Command.POINT: ["!puan", "!bakiye"],
    Command.GET_TRANSACTION_REPORT: ["!rapor"],
    # == SHARE CHANNEL == #
    Command.SHARE_START: ["!p", "!paylaş", "!paylas"]
}


def __merge_commands(command: str):
    return (EXTRA_COMMANDS[command] + [command]) if command in EXTRA_COMMANDS else [command]


def __get_extended_command_map(command_map: dict) -> dict:
    extended_command_map = {}
    for command, function in command_map.items():
        commands = __merge_commands(command)
        extended_command_map.update(dict.fromkeys(commands, function))
        extended_command_map.update(
            dict.fromkeys([key.translate({ord(u'ı'): u'I', ord(u'i'): u'İ'}).upper() for key in commands],
                          function))
    return extended_command_map


def get_command_map(default_function, command_map):
    return defaultdict(lambda: default_function, __get_extended_command_map(command_map))
