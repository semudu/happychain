from bipwrapper.model.request import Request
from bipwrapper.type.ctype import CType
from app.commons.utils import split_to_array
from app.commons.constants.globals import Globals
from app.commons.constants.command import Command


class BipRequest(Request):
    def __init__(self, request_json):
        request_json["sender"] = request_json["sender"][-10:]
        super().__init__(request_json)

        self.__command = None
        self.__extras = None
        self.__values = None

        if self.ctype == CType.TEXT:
            ctx_arr = split_to_array(self.context, Globals.DELIMITER)
            self.__command = ctx_arr[0]
            self.__extras = ctx_arr[1:]
        elif self.ctype == CType.POLL:
            ctx_arr = split_to_array(self.poll.poll_id, Globals.DELIMITER)
            self.__command = ctx_arr[0]
            self.__extras = ctx_arr[1:]
            self.__values = self.poll.values
        elif self.ctype == CType.POSTBACK:
            ctx_arr = split_to_array(self.postback.value, Globals.DELIMITER)
            self.__command = ctx_arr[0]
            self.__extras = ctx_arr[1:]
        elif self.ctype == CType.BUZZ:
            self.__command = Command.MENU

    @property
    def command(self):
        return self.__command

    def value(self, order=1):
        if len(self.__values) >= order:
            return self.__values[order - 1]
        return None

    def extra_param(self, order=1):
        if len(self.__extras) >= order:
            return self.__extras[order - 1]
        return None
