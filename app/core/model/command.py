from enum import Enum


class Command(Enum):
    HELP = "__help"
    MENU = "__menu"
    POINT = "__point"
    LAST_SENT = "__last_sent"
    LAST_RECEIVED = "__last_received"
